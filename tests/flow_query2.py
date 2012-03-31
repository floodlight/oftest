"""
Flow query test case.

Attempts to fill switch to capacity with randomized flows, and ensure that they all are read back correctly.
"""
import math

import logging

import unittest
import random

import oftest.controller  as controller
import oftest.cstruct     as ofp
import oftest.message     as message
import oftest.dataplane   as dataplane
import oftest.action      as action
import oftest.action_list as action_list
import oftest.parse       as parse
import pktact
import basic

from testutils import *
from time import sleep

#@var port_map Local copy of the configuration map from OF port
# numbers to OS interfaces
pa_port_map = None
#@var pa_logger Local logger object
pa_logger = None
#@var pa_config Local copy of global configuration data
pa_config = None

def test_set_init(config):
    """
    Set up function for packet action test classes

    @param config The configuration dictionary; see oft
    """

    basic.test_set_init(config)

    global pa_port_map
    global pa_logger
    global pa_config

    pa_logger = logging.getLogger("pkt_act")
    pa_logger.info("Initializing test set")
    pa_port_map = config["port_map"]
    pa_config = config


def shuffle(list):
    n = len(list)
    lim = n * n
    i = 0
    while i < lim:
        a = random.randint(0, n - 1)
        b = random.randint(0, n - 1)
        temp = list[a]
        list[a] = list[b]
        list[b] = temp
        i = i + 1
    return list


def rand_pick(list):
    return list[random.randint(0, len(list) - 1)]

def rand_dl_addr():
    return [random.randint(0, 255) & ~1,
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
            ]

def rand_nw_addr():
    return random.randint(0, (1 << 32) - 1)


class flow_info:
    # Members:
    # priorities - list of flow priorities
    # dl_addrs   - list of MAC addresses
    # vlans      - list of VLAN ids
    # ethertypes - list of Ethertypes
    # ip_addrs   - list of IP addresses
    # ip_tos     - list of IP TOS values
    # ip_protos  - list of IP protocols
    # l4_ports   - list of L4 ports

    def __init__(self):
        priorities = []
        dl_addrs   = []
        vlans      = []
        ethertypes = []
        ip_addrs   = []
        ip_tos     = []
        ip_protos  = []
        l4_ports   = []

    def rand(self, n):
        self.priorities = []
        i = 0
        while i < n:
            self.priorities.append(random.randint(1, 65534))
            i = i + 1
    
        self.dl_addrs = []
        i = 0
        while i < n:
            self.dl_addrs.append(rand_dl_addr())
            i = i + 1
    
        self.vlans = []
        i = 0
        while i < n:
            self.vlans.append(random.randint(1, 4094))
            i = i + 1
    
        self.ethertypes = []
        i = 0
        while i < n:
            self.ethertypes.append(random.randint(0, (1 << 16) - 1))
            i = i + 1
    
        self.ip_addrs = []
        i = 0
        while i < n:
            self.ip_addrs.append(rand_nw_addr())
            i = i + 1
    
        self.ip_tos = []
        i = 0
        while i < n:
            self.ip_tos.append(random.randint(0, (1 << 8) - 1) & ~3)
            i = i + 1
    
        self.ip_protos = []
        i = 0
        while i < n:
            self.ip_protos.append(random.randint(0, (1 << 8) - 1))
            i = i + 1
    
        self.l4_ports = []
        i = 0
        while i < n:
            self.l4_ports.append(random.randint(0, (1 << 16) - 1))
            i = i + 1

    def rand_priority(self):
        return rand_pick(self.priorities)

    def rand_dl_addr(self):
        return rand_pick(self.dl_addrs)

    def rand_vlan(self):
        return rand_pick(self.vlans)

    def rand_ethertype(self):
        return rand_pick(self.ethertypes)

    def rand_ip_addr(self):
        return rand_pick(self.ip_addrs)

    def rand_ip_tos(self):
        return rand_pick(self.ip_tos)

    def rand_ip_proto(self):
        return rand_pick(self.ip_protos)

    def rand_l4_port(self):
        return rand_pick(self.l4_ports)


# TBD - These don't belong here

all_wildcards_list = [ofp.OFPFW_IN_PORT,
                      ofp.OFPFW_DL_VLAN,
                      ofp.OFPFW_DL_SRC,
                      ofp.OFPFW_DL_DST,
                      ofp.OFPFW_DL_TYPE,
                      ofp.OFPFW_NW_PROTO,
                      ofp.OFPFW_TP_SRC,
                      ofp.OFPFW_TP_DST,
                      ofp.OFPFW_NW_SRC_MASK,
                      ofp.OFPFW_NW_DST_MASK,
                      ofp.OFPFW_DL_VLAN_PCP,
                      ofp.OFPFW_NW_TOS
                      ]


all_actions_list = [ofp.OFPAT_OUTPUT,
                    ofp.OFPAT_SET_VLAN_VID,
                    ofp.OFPAT_SET_VLAN_PCP,
                    ofp.OFPAT_STRIP_VLAN,
                    ofp.OFPAT_SET_DL_SRC,
                    ofp.OFPAT_SET_DL_DST,
                    ofp.OFPAT_SET_NW_SRC,
                    ofp.OFPAT_SET_NW_DST,
                    ofp.OFPAT_SET_NW_TOS,
                    ofp.OFPAT_SET_TP_SRC,
                    ofp.OFPAT_SET_TP_DST,
                    ofp.OFPAT_ENQUEUE
                    ]

def dl_addr_to_str(a):
    return "%x:%x:%x:%x:%x:%x" % tuple(a)

def ip_addr_to_str(a, n):
    result = "%d.%d.%d.%d" % (a >> 24, \
                              (a >> 16) & 0xff, \
                              (a >> 8) & 0xff, \
                              a & 0xff \
                              )
    if n is not None:
        result = result + ("/%d" % (n))
    return result
    

class flow_cfg:
    # Members:
    # - match
    # - idle_timeout
    # - hard_timeout
    # - priority
    # - action_list

    def __init__(self):
        self.priority        = 0
        self.match           = parse.ofp_match()
        self.match.wildcards = ofp.OFPFW_ALL
        self.idle_timeout    = 0
        self.hard_timeout    = 0
        self.actions         = action_list.action_list()

    def __eq__(self, x):
        if self.priority != x.priority:
            return False
        # TBD - Should this logic be moved to ofp_match.__eq__()?
        if self.match.wildcards != x.match.wildcards:
            return False
        if (self.match.wildcards & ofp.OFPFW_IN_PORT) == 0 \
           and self.match.in_port != x.match.in_port:
            return False
        if (self.match.wildcards & ofp.OFPFW_DL_SRC) == 0 \
           and self.match.dl_src != x.match.dl_src:
            return False
        if (self.match.wildcards & ofp.OFPFW_DL_DST) == 0 \
           and self.match.dl_dst != x.match.dl_dst:
            return False
        if (self.match.wildcards & ofp.OFPFW_DL_VLAN) == 0 \
           and self.match.dl_vlan != x.match.dl_vlan:
            return False
        if (self.match.wildcards & ofp.OFPFW_DL_VLAN_PCP) == 0 \
           and self.match.dl_vlan_pcp != x.match.dl_vlan_pcp:
            return False
        if (self.match.wildcards & ofp.OFPFW_DL_TYPE) == 0 \
           and self.match.dl_type != x.match.dl_type:
            return False
        if (self.match.wildcards & ofp.OFPFW_NW_TOS) == 0 \
           and self.match.nw_tos != x.match.nw_tos:
            return False
        if (self.match.wildcards & ofp.OFPFW_NW_PROTO) == 0 \
           and self.match.nw_proto != x.match.nw_proto:
            return False
        if (self.match.wildcards & ofp.OFPFW_NW_SRC_MASK) \
               < ofp.OFPFW_NW_SRC_ALL:
            m = ~((1 << ((self.match.wildcards & ofp.OFPFW_NW_SRC_MASK) \
                         >> ofp.OFPFW_NW_SRC_SHIFT)) - 1)
            if (self.match.nw_src & m) != (x.match.nw_src & m):
                return False
        if (self.match.wildcards & ofp.OFPFW_NW_DST_MASK) \
               < ofp.OFPFW_NW_DST_ALL:
            m = ~((1 << ((self.match.wildcards & ofp.OFPFW_NW_DST_MASK) \
                         >> ofp.OFPFW_NW_DST_SHIFT)) - 1)
            if (self.match.nw_dst & m) != (x.match.nw_dst & m):
                return False
        if (self.match.wildcards & ofp.OFPFW_TP_SRC) == 0 \
           and self.match.tp_src != x.match.tp_src:
            return False
        if (self.match.wildcards & ofp.OFPFW_TP_DST) == 0 \
           and self.match.tp_dst != x.match.tp_dst:
            return False
        if self.idle_timeout != x.idle_timeout:
            return False
        if self.hard_timeout != x.hard_timeout:
            return False
        return self.actions == x.actions  # N.B. Action lists are ordered

    def __str__(self):
        result = "priority=%d" % self.priority
        # TBD - Would be nice if ofp_match.show() was better behaved
        # (no newlines), and more intuitive (things in hex where approprate), etc.
        result = result + ", wildcards={"
        sep = ""
        for w in ofp.ofp_flow_wildcards_map:
            if w == ofp.OFPFW_NW_SRC_SHIFT \
               or w == ofp.OFPFW_NW_SRC_BITS \
               or w == ofp.OFPFW_NW_SRC_ALL \
               or w == ofp.OFPFW_NW_DST_SHIFT \
               or w == ofp.OFPFW_NW_DST_BITS \
               or w == ofp.OFPFW_NW_DST_ALL \
               or w == ofp.OFPFW_ALL \
               or self.match.wildcards & w == 0:
                continue
            if w == ofp.OFPFW_NW_SRC_MASK:
                result = result + sep + "OFPFW_NW_SRC"
            elif w == ofp.OFPFW_NW_DST_MASK:
                result = result + sep + "OFPFW_NW_DST"
            else:
                result = result + sep + ofp.ofp_flow_wildcards_map[w]
            sep = ", "
        result = result +"}"
        if (self.match.wildcards & ofp.OFPFW_IN_PORT) == 0:
            result = result + (", in_port=%d" % (self.match.in_port))
        if (self.match.wildcards & ofp.OFPFW_DL_SRC) == 0:
            result = result + (", dl_src=%s" % (dl_addr_to_str(self.match.dl_src)))
        if (self.match.wildcards & ofp.OFPFW_DL_DST) == 0:
            result = result + (", dl_dst=%s" % (dl_addr_to_str(self.match.dl_dst)))
        if (self.match.wildcards & ofp.OFPFW_DL_VLAN) == 0:
            result = result + (", dl_vlan=%d" % (self.match.dl_vlan))
        if (self.match.wildcards & ofp.OFPFW_DL_VLAN_PCP) == 0:
            result = result + (", dl_vlan_pcp=%d" % (self.match.dl_vlan_pcp))
        if (self.match.wildcards & ofp.OFPFW_DL_TYPE) == 0:
            result = result + (", dl_type=0x%x" % (self.match.dl_type))
        if (self.match.wildcards & ofp.OFPFW_NW_TOS) == 0:
            result = result + (", nw_tos=0x%x" % (self.match.nw_tos))
        if (self.match.wildcards & ofp.OFPFW_NW_PROTO) == 0:
            result = result + (", nw_proto=%d" % (self.match.nw_proto))
        n = (self.match.wildcards & ofp.OFPFW_NW_SRC_MASK) >> ofp.OFPFW_NW_SRC_SHIFT
        if n < 32:
            result = result + (", nw_src=%s" % (ip_addr_to_str(self.match.nw_src, n)))
        n = (self.match.wildcards & ofp.OFPFW_NW_DST_MASK) >> ofp.OFPFW_NW_DST_SHIFT
        if n < 32:
            result = result + (", nw_dst=%s" % (ip_addr_to_str(self.match.nw_dst, n)))
        if (self.match.wildcards & ofp.OFPFW_TP_SRC) == 0:
            result = result + (", tp_src=%d" % self.match.tp_src)
        if (self.match.wildcards & ofp.OFPFW_TP_DST) == 0:
            result = result + (", tp_dst=%d" % self.match.tp_dst)
        result = result + (", idle_timeout=%d" % self.idle_timeout)
        result = result + (", hard_timeout=%d" % self.hard_timeout)
        result = result + (", hard_timeout=%d" % self.hard_timeout)
        for a in self.actions.actions:
            result = result + (", action=%s" % ofp.ofp_action_type_map[a.type])
            if a.type == ofp.OFPAT_OUTPUT:
                result = result + ("(%d)" % (a.port))
            elif a.type == ofp.OFPAT_SET_VLAN_VID:
                result = result + ("(%d)" % (a.vlan_vid))
            elif a.type == ofp.OFPAT_SET_VLAN_PCP:
                result = result + ("(%d)" % (a.vlan_pcp))
            elif a.type == ofp.OFPAT_SET_DL_SRC or a.type == ofp.OFPAT_SET_DL_DST:
                result = result + ("(%s)" % (dl_addr_to_str(a.dl_addr)))
            elif a.type == ofp.OFPAT_SET_NW_SRC or a.type == ofp.OFPAT_SET_NW_DST:
                result = result + ("(%s)" % (ip_addr_to_str(a.nw_addr, None)))
            elif a.type == ofp.OFPAT_SET_NW_TOS:
                result = result + ("(0x%x)" % (a.nw_tos))
            elif a.type == ofp.OFPAT_SET_TP_SRC or a.type == ofp.OFPAT_SET_TP_DST:
                result = result + ("(%d)" % (a.tp_port))
            elif a.type == ofp.OFPAT_ENQUEUE:
                result = result + ("(port=%d,queue=%d)" % (a.port, a.queue_id))
        return result

    def rand(self, fi, valid_wildcards, valid_actions, valid_ports):
        # Start with no wildcards, i.e. everything specified
        self.match.wildcards = 0
        
        # Make approx. 1% of flows exact
        exact = True if random.randint(1, 100) == 1 else False

        # For each qualifier Q,
        #   if (wildcarding is not supported for Q,
        #       or an exact flow is specified
        #       or a coin toss comes up heads), 
        #      specify Q
        #   else
        #      wildcard Q

        if (ofp.OFPFW_IN_PORT & valid_wildcards) == 0 \
           or exact \
           or random.randint(1, 100) <= 50:
            self.match.in_port = rand_pick(valid_ports)
        else:
            self.match.wildcards = self.match.wildcards | ofp.OFPFW_IN_PORT
            
        if (ofp.OFPFW_DL_DST & valid_wildcards) == 0 \
           or exact \
           or random.randint(1, 100) <= 50:
            self.match.dl_dst = fi.rand_dl_addr()
        else:
            self.match.wildcards = self.match.wildcards | ofp.OFPFW_DL_DST

        if (ofp.OFPFW_DL_SRC & valid_wildcards) == 0 \
           or exact \
           or random.randint(1, 100) <= 50:
            self.match.dl_src = fi.rand_dl_addr()
        else:
            self.match.wildcards = self.match.wildcards | ofp.OFPFW_DL_SRC

        if (ofp.OFPFW_DL_VLAN_PCP & valid_wildcards) == 0 \
           or exact \
           or random.randint(1, 100) <= 50:
            self.match.dl_vlan_pcp = random.randint(0, (1 << 3) - 1)
        else:
            self.match.wildcards = self.match.wildcards | ofp.OFPFW_DL_VLAN_PCP

        if (ofp.OFPFW_DL_VLAN & valid_wildcards) == 0 \
           or exact \
           or random.randint(1, 100) <= 50:
            self.match.dl_vlan = fi.rand_vlan()
        else:
            self.match.wildcards = self.match.wildcards | ofp.OFPFW_DL_VLAN

        if (ofp.OFPFW_DL_TYPE & valid_wildcards) == 0 \
           or exact \
           or random.randint(1, 100) <= 50:
            self.match.dl_type = fi.rand_ethertype()
        else:
            self.match.wildcards = self.match.wildcards | ofp.OFPFW_DL_TYPE

        if exact:
            n = 0
        else:
            n = (valid_wildcards & ofp.OFPFW_NW_SRC_MASK) \
                >> ofp.OFPFW_NW_SRC_SHIFT
            if n > 32:
                n = 32
            n = random.randint(0, n)
        self.match.wildcards = self.match.wildcards \
                               | (n << ofp.OFPFW_NW_SRC_SHIFT)
        if n < 32:
            self.match.nw_src    = fi.rand_ip_addr() & ~((1 << n) - 1)
            # Specifying any IP address match other than all bits
            # don't care requires that Ethertype is one of {IP, ARP}
            self.match.dl_type   = rand_pick([0x0800, 0x0806])
            self.match.wildcards = self.match.wildcards & ~ofp.OFPFW_DL_TYPE

        if exact:
            n = 0
        else:
            n = (valid_wildcards & ofp.OFPFW_NW_DST_MASK) \
                >> ofp.OFPFW_NW_DST_SHIFT
            if n > 32:
                n = 32
            n = random.randint(0, n)
        self.match.wildcards = self.match.wildcards \
                               | (n << ofp.OFPFW_NW_DST_SHIFT)
        if n < 32:
            self.match.nw_dst    = fi.rand_ip_addr() & ~((1 << n) - 1)
            # Specifying any IP address match other than all bits
            # don't care requires that Ethertype is one of {IP, ARP}
            self.match.dl_type   = rand_pick([0x0800, 0x0806])
            self.match.wildcards = self.match.wildcards & ~ofp.OFPFW_DL_TYPE

        if (ofp.OFPFW_NW_TOS & valid_wildcards) == 0 \
           or exact \
           or random.randint(1, 100) <= 50:
            self.match.nw_tos = fi.rand_ip_tos()
            # Specifying a TOS value requires that Ethertype is IP
            self.match.dl_type   = 0x0800
            self.match.wildcards = self.match.wildcards & ~ofp.OFPFW_DL_TYPE
        else:
            self.match.wildcards = self.match.wildcards | ofp.OFPFW_NW_TOS

        if (ofp.OFPFW_NW_PROTO & valid_wildcards) == 0 \
           or exact \
           or random.randint(1, 100) <= 50:
            self.match.nw_proto = fi.rand_ip_proto()
            # Specifying an IP protocol requires that Ethertype is IP
            self.match.dl_type   = 0x0800
            self.match.wildcards = self.match.wildcards & ~ofp.OFPFW_DL_TYPE
        else:            
            self.match.wildcards = self.match.wildcards | ofp.OFPFW_NW_PROTO
            
        if (ofp.OFPFW_TP_SRC & valid_wildcards) == 0 \
           or exact\
           or random.randint(1, 100) <= 50:
            self.match.tp_src = fi.rand_l4_port()
            # Specifying a L4 port requires that IP protcol is
            # one of {ICMP, TCP, UDP}
            self.match.nw_proto = rand_pick([1, 6, 17])
            self.match.wildcards = self.match.wildcards & ~ofp.OFPFW_NW_PROTO
            # Specifying a L4 port requirues that Ethertype is IP
            self.match.dl_type   = 0x0800
            self.match.wildcards = self.match.wildcards & ~ofp.OFPFW_DL_TYPE
        else:
            self.match.wildcards = self.match.wildcards | ofp.OFPFW_TP_SRC

        if (ofp.OFPFW_TP_DST & valid_wildcards) == 0 \
           or exact \
           or random.randint(1, 100) <= 50:
            self.match.tp_dst = fi.rand_l4_port()
            # Specifying a L4 port requires that IP protcol is
            # one of {ICMP, TCP, UDP}
            self.match.nw_proto = rand_pick([1, 6, 17])
            self.match.wildcards = self.match.wildcards & ~ofp.OFPFW_NW_PROTO
            # Specifying a L4 port requirues that Ethertype is IP
            self.match.dl_type   = 0x0800
            self.match.wildcards = self.match.wildcards & ~ofp.OFPFW_DL_TYPE
        else:
            self.match.wildcards = self.match.wildcards | ofp.OFPFW_TP_DST

        # N.B. Don't make the timeout too short, else the flow might
        # disappear before we get a chance to check for it.
        t = random.randint(0, 65535)
        self.idle_timeout = 0 if t < 60 else t
        t = random.randint(0, 65535)
        self.hard_timeout = 0 if t < 60 else t

        # If nothing is wildcarded, it is an exact flow spec -- some switches
        # (Open vSwitch, for one) *require* that exact flow specs have priority 65535.
        self.priority = 65535 if self.match.wildcards == 0 else fi.rand_priority()

        # Action lists are ordered, so pick an ordered random subset of
        # supported actions
        supported_actions = []
        for a in all_actions_list:
            if ((1 << a) & valid_actions) != 0:
                supported_actions.append(a)

        supported_actions = shuffle(supported_actions)
        supported_actions \
            = supported_actions[0 : random.randint(1, len(supported_actions))]

        self.actions = action_list.action_list()
        for a in supported_actions:
            if a == ofp.OFPAT_OUTPUT:
                # TBD - Output actions are clustered in list, spread them out?
                port_idxs = shuffle(range(len(valid_ports)))
                port_idxs = port_idxs[0 : random.randint(1, len(valid_ports))]
                for pi in port_idxs:
                    act = action.action_output()
                    act.port = valid_ports[pi]
                    self.actions.add(act)
            elif a == ofp.OFPAT_SET_VLAN_VID:
                act = action.action_set_vlan_vid()
                act.vlan_vid = fi.rand_vlan()
                self.actions.add(act)
            elif a == ofp.OFPAT_SET_VLAN_PCP:
                # TBD - Temporaily removed, broken in Indigo
                #act = action.action_set_vlan_pcp()
                #act.vlan_pcp = random.randint(0, (1 << 3) - 1)
                pass
            elif a == ofp.OFPAT_STRIP_VLAN:
                act = action.action_strip_vlan()
                self.actions.add(act)
            elif a == ofp.OFPAT_SET_DL_SRC:
                act = action.action_set_dl_src()
                act.dl_addr = fi.rand_dl_addr()
                self.actions.add(act)
            elif a == ofp.OFPAT_SET_DL_DST:
                act = action.action_set_dl_dst()
                act.dl_addr = fi.rand_dl_addr()
                self.actions.add(act)
            elif a == ofp.OFPAT_SET_NW_SRC:
                act = action.action_set_nw_src()
                act.nw_addr = fi.rand_ip_addr()
                self.actions.add(act)
            elif a == ofp.OFPAT_SET_NW_DST:
                act = action.action_set_nw_dst()
                act.nw_addr = fi.rand_ip_addr()
                self.actions.add(act)
            elif a == ofp.OFPAT_SET_NW_TOS:
                act = action.action_set_nw_tos()
                act.nw_tos = fi.rand_ip_tos()
                self.actions.add(act)
            elif a == ofp.OFPAT_SET_TP_SRC:
                act = action.action_set_tp_src()
                act.tp_port = fi.rand_l4_port()
                self.actions.add(act)
            elif a == ofp.OFPAT_SET_TP_DST:
                act = action.action_set_tp_dst()
                act.tp_port = fi.rand_l4_port()
                self.actions.add(act)
            elif a == ofp.OFPAT_ENQUEUE:
                # TBD - Enqueue actions are clustered in list, spread them out?
                port_idxs = shuffle(range(len(valid_ports)))
                port_idxs = port_idxs[0 : random.randint(1, len(valid_ports))]
                for pi in port_idxs:
                    act = action.action_enqueue()
                    act.port = valid_ports[pi]
                    # TBD - Limits for queue number?
                    act.queue_id = random.randint(0, 7)
                    self.actions.add(act)

        return self

    # Overlap check
    # delf == True <=> Check for delete overlap, else add overlap
    # "Add overlap" is defined as there exists a packet that could match both the
    # receiver and argument flowspecs
    # "Delete overlap" is defined as the specificity of the argument flowspec
    # is greater than or equal to the specificity of the receiver flowspec
    def overlaps(self, x, delf):
        if self.priority != x.priority:
            return False
        if (self.match.wildcards & ofp.OFPFW_IN_PORT) == 0:
            if (x.match.wildcards & ofp.OFPFW_IN_PORT) == 0:
                if self.match.in_port != x.match.in_port:
                    return False        # Both specified, and not equal
            elif delf:
                return False            # Receiver more specific
        if (self.match.wildcards & ofp.OFPFW_DL_VLAN) == 0:
            if (x.match.wildcards & ofp.OFPFW_DL_VLAN) == 0:
                if self.match.dl_vlan != x.match.dl_vlan:
                    return False        # Both specified, and not equal
            elif delf:
                return False            # Receiver more specific
        if (self.match.wildcards & ofp.OFPFW_DL_SRC) == 0:
            if (x.match.wildcards & ofp.OFPFW_DL_SRC) == 0:
                if self.match.dl_src != x.match.dl_src:
                    return False        # Both specified, and not equal
            elif delf:
                return False            # Receiver more specific
        if (self.match.wildcards & ofp.OFPFW_DL_DST) == 0:
            if (x.match.wildcards & ofp.OFPFW_DL_DST) == 0:
                if self.match.dl_dst != x.match.dl_dst:
                    return False        # Both specified, and not equal
            elif delf:
                return False            # Receiver more specific
        if (self.match.wildcards & ofp.OFPFW_DL_TYPE) == 0:
            if (x.match.wildcards & ofp.OFPFW_DL_TYPE) == 0:
                if self.match.dl_type != x.match.dl_type:
                    return False        # Both specified, and not equal
            elif delf:
                return False            # Recevier more specific
        if (self.match.wildcards & ofp.OFPFW_NW_PROTO) == 0:
            if (x.match.wildcards & ofp.OFPFW_NW_PROTO) == 0:
                if self.match.nw_proto != x.match.nw_proto:
                    return False        # Both specified, and not equal
            elif delf:
                return False            # Receiver more specific
        if (self.match.wildcards & ofp.OFPFW_TP_SRC) == 0:
            if (x.match.wildcards & ofp.OFPFW_TP_SRC) == 0:
                if self.match.tp_src != x.match.tp_src:
                    return False        # Both specified, and not equal
            elif delf:
                return False            # Receiver more specific
        if (self.match.wildcards & ofp.OFPFW_TP_DST) == 0:
            if (x.match.wildcards & ofp.OFPFW_TP_DST) == 0:
                if self.match.tp_dst != x.match.tp_dst:
                    return False        # Both specified, and not equal
            elif delf:
                return False            # Receiver more specific
        na = (self.match.wildcards & ofp.OFPFW_NW_SRC_MASK) \
             >> ofp.OFPFW_NW_SRC_SHIFT
        nb = (x.match.wildcards & ofp.OFPFW_NW_SRC_MASK) \
             >> ofp.OFPFW_NW_SRC_SHIFT
        if delf and na < nb:
            return False                # Receiver more specific
        if (na < 32 and nb < 32):
            m = ~((1 << na) - 1) & ~((1 << nb) - 1)
            if (self.match.nw_src & m) != (x.match.nw_src & m):
                return False            # Overlapping bits not equal
        na = (self.match.wildcards & ofp.OFPFW_NW_DST_MASK) \
             >> ofp.OFPFW_NW_DST_SHIFT
        nb = (x.match.wildcards & ofp.OFPFW_NW_DST_MASK) \
             >> ofp.OFPFW_NW_DST_SHIFT
        if delf and na < nb:
            return False                # Receiver more specific
        if (na < 32 and nb < 32):
            m = ~((1 << na) - 1) & ~((1 << nb) - 1)
            if (self.match.nw_dst & m) != (x.match.nw_dst & m):
                return False            # Overlapping bit not equal
        if (self.match.wildcards & ofp.OFPFW_DL_VLAN_PCP) == 0:
            if (x.match.wildcards & ofp.OFPFW_DL_VLAN_PCP) == 0:
                if self.match.dl_vlan_pcp != x.match.dl_vlan_pcp:
                    return False        # Both specified, and not equal
            elif delf:
                return False            # Receiver more specific
        if (self.match.wildcards & ofp.OFPFW_NW_TOS) == 0:
            if (x.match.wildcards & ofp.OFPFW_NW_TOS) == 0:
                if self.match.nw_tos != x.match.nw_tos:
                    return False        # Both specified, and not equal
            elif delf:
                return False            # Receiver more specific
        return True                     # Flows overlap

    def to_flow_mod_msg(self, msg):
        msg.match        = self.match
        msg.idle_timeout = self.idle_timeout
        msg.hard_timeout = self.hard_timeout
        msg.priority     = self.priority
        msg.actions      = self.actions
        return msg

    def from_flow_stat(self, msg):
        self.match        = msg.match
        self.idle_timeout = msg.idle_timeout
        self.hard_timeout = msg.hard_timeout
        self.priority     = msg.priority
        self.actions      = msg.actions


class FlowQuery(basic.SimpleProtocol):
    """
    """

    def do_barrier(self):
        barrier = message.barrier_request()
        (resp, pkt) = self.controller.transact(barrier, 5)
        self.assertTrue(resp is not None,
                        "Did not receive response to barrier request"
                        )
    

    def verify_flows(self,
                     sw_features,
                     tbl_flows,
                     num_flows,
                     overlapf,
                     num_overlaps
                     ):
        result = True
        
        # Check number of flows reported in table stats

        self.logger.debug("Verifying table stats reports correct number of")
        self.logger.debug("  active flows")
        request = message.table_stats_request()
        (tbl_stats_after, pkt) = self.controller.transact(request, timeout=2)
        self.assertTrue(tbl_stats_after is not None,
                        "No reply to table_stats_request"
                        )

        num_flows_reported = 0
        for ts in tbl_stats_after.stats:
            num_flows_reported = num_flows_reported + ts.active_count

        num_flows_expected = num_flows
        if overlapf:
            num_flows_expected = num_flows_expected - num_overlaps

        self.logger.debug("Number of flows reported = "
                          + str(num_flows_reported)
                          )
        self.logger.debug("Numer of flows expected = "
                          + str(num_flows_expected)
                          )
        if num_flows_reported != num_flows_expected:
            self.logger.error("Incorrect number of flows returned by table stats")
            result = False

        # Retrieve all flows from switch

        self.logger.debug("Retrieving all flows from switch")
        stat_req = message.flow_stats_request()
        query_match           = ofp.ofp_match()
        query_match.wildcards = ofp.OFPFW_ALL
        stat_req.match    = query_match
        stat_req.table_id = 0xff
        stat_req.out_port = ofp.OFPP_NONE;
        flow_stats, pkt = self.controller.transact(stat_req, timeout=2)
        self.assertTrue(flow_stats is not None, "Get all flow stats failed")

        # Verify retrieved flows

        self.logger.debug("Verifying retrieved flows")

        self.assertEqual(flow_stats.type,
                         ofp.OFPST_FLOW,
                         "Unexpected type of response message"
                         )

        num_flows_reported = len(flow_stats.stats)

        self.logger.debug("Number of flows reported = "
                          + str(num_flows_reported)
                          )
        self.logger.debug("Numer of flows expected = "
                          + str(num_flows_expected)
                          )
        if num_flows_reported != num_flows_expected:
            self.logger.error("Incorrect number of flows returned by table stats")
            result = False

        for f in tbl_flows:
            f.resp_matched = False

        num_resp_flows_matched = 0
        for flow_stat in flow_stats.stats:
            flow_in = flow_cfg()
            flow_in.from_flow_stat(flow_stat)

            matched = False
            for f in tbl_flows:
                if f.deleted:
                    continue
                if not f.resp_matched \
                   and (not overlapf or not f.overlap) \
                   and f == flow_in:
                    f.resp_matched = True
                    num_resp_flows_matched = num_resp_flows_matched + 1
                    matched = True
                    break
            if not matched:
                self.logger.error("Response flow")
                self.logger.error(str(flow_in))
                self.logger.error("does not match any configured flow")
                result = False

        self.logger.debug("Number of flows matched in response = "
                          + str(num_resp_flows_matched)
                          )
        self.logger.debug("Number of flows expected = "
                          + str(num_flows_expected)
                          )
        if num_resp_flows_matched != num_flows_expected:
            for f in tbl_flows:
                if not f.resp_matched:
                    self.logger.error("Configured flow")
                    self.logger.error("tbl_idx=%d, flow_idx=%d, %s" % (f.tbl_idx, f.flow_idx, str(f)))
                    self.logger.error("missing in flow response")
                    result = False

        self.assertTrue(result, "Flow verification failed")

    def flow_add(self, flow, overlapf):
        flow_mod_msg = message.flow_mod()
        flow_mod_msg.command     = ofp.OFPFC_ADD
        flow_mod_msg.buffer_id   = 0xffffffff
        flow_mod_msg.cookie      = random.randint(0, (1 << 53) - 1)
        flow.to_flow_mod_msg(flow_mod_msg)
        if overlapf:
            flow_mod_msg.flags = flow_mod_msg.flags | ofp.OFPFF_CHECK_OVERLAP
        self.logger.debug("Sending flow_mod(add) request to switch")
        rv = self.controller.message_send(flow_mod_msg)
        self.assertTrue(rv != -1, "Error installing flow mod")

        # TBD - Don't poll for each error message
        if flow.overlap:
            self.logger.debug("Flow overlaps with tbl_idx=%d flow_idx=%d"
                              % (flow.overlaps_with[0], flow.overlaps_with[1])
                              )
        else:
            self.logger.debug("Flow does not overlap")
        self.logger.debug("Checking for error response from switch")
        (errmsg, pkt) = self.controller.poll(ofp.OFPT_ERROR, 1)
        if errmsg is not None:
            # Got ERROR message
            self.logger.debug("Got ERROR message, type = "
                              + str(errmsg.type)
                              + ", code = "
                              + str(errmsg.code)
                              )
            
            if errmsg.type == ofp.OFPET_FLOW_MOD_FAILED \
               and errmsg.code == ofp.OFPFMFC_OVERLAP:
                # Got "overlap" ERROR message
                self.logger.debug("ERROR is overlap")
                
                self.assertTrue(overlapf and flow.overlap,
                                "Overlap not expected"
                                )
            else:
                self.logger.debug("ERROR is not overlap")
                self.assertTrue(False,
                                "Unexpected error message")

        else:
            # Did not get ERROR message
            self.logger.debug("No ERROR message received")
            self.assertTrue(not (overlapf and flow.overlap),
                            "Did not get expected OVERLAP"
                            )


    def flow_del(self, flow, strictf):
        flow_mod_msg = message.flow_mod()
        flow_mod_msg.command     = ofp.OFPFC_DELETE_STRICT \
            if strictf else ofp.OFPFC_DELETE
        flow_mod_msg.buffer_id   = 0xffffffff
        flow_mod_msg.cookie      = random.randint(0, (1 << 53) - 1)
        # TBD - Needs to be a test variable
        flow_mod_msg.out_port    = ofp.OFPP_NONE
        flow.to_flow_mod_msg(flow_mod_msg)
        rv = self.controller.message_send(flow_mod_msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        # TBD - Don't poll for each error message
        (errmsg, pkt) = self.controller.poll(ofp.OFPT_ERROR, 1)
        if errmsg is not None:
            # Got ERROR message
            self.logger.debug("Got ERROR message, type = "
                              + str(errmsg.type)
                              + ", code = "
                              + str(errmsg.code)
                              )
            self.assertTrue(False,
                            "Unexpected error message"
                            )


    # Add flows to capacity, make sure they can be read back, and delete them

    def test1(self,
              overlapf,                 # True <=> When sending flow adds to
                                        # switch, include the "check for
                                        # overlap" flag, and verify that an
                                        # error message is received
                                        # if an overlapping flow is defined
              strictf                   # True <=> When deleting flows, delete
                                        # them strictly
              ):
        """
        """

        # Clear all flows from switch
        self.logger.debug("Deleting all flows from switch")
        rc = delete_all_flows(self.controller, pa_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # Get valid port numbers
        # Get number of tables supported
        # Get actions supported by switch

        self.logger.debug("Retrieving features from switch")
        request = message.features_request()
        (sw_features, pkt) = self.controller.transact(request, timeout=2)
        self.assertTrue(sw_features is not None, "No reply to features_request")
        self.logger.debug("Switch features -")
        self.logger.debug("Number of tables: " + str(sw_features.n_tables))
        self.logger.debug("Supported actions: " + hex(sw_features.actions))
        self.logger.debug("Ports: "
                          + str(map(lambda x: x.port_no, sw_features.ports))
                          )

        # For each table, get wildcards supported maximum number of flows

        self.logger.debug("Retrieving table stats from switch")
        request = message.table_stats_request()
        (tbl_stats, pkt) = self.controller.transact(request, timeout=2)
        self.assertTrue(tbl_stats is not None,
                        "No reply to table_stats_request"
                        )
        active_count = 0
        max_entries  = 0
        tbl_idx = 0
        while tbl_idx < sw_features.n_tables:
            self.logger.debug("Table " + str(tbl_idx) + " - ")
            self.logger.debug("Supported wildcards: "
                              + hex(tbl_stats.stats[tbl_idx].wildcards)
                              )
            self.logger.debug("Max entries: "
                              + str(tbl_stats.stats[tbl_idx].max_entries)
                              )
            self.logger.debug("Active count: "
                              + str(tbl_stats.stats[tbl_idx].active_count)
                              )
            max_entries  = max_entries + tbl_stats.stats[tbl_idx].max_entries
            active_count = active_count + tbl_stats.stats[tbl_idx].active_count
            tbl_idx = tbl_idx + 1

        self.logger.debug("Total active entries = "
                          + str(active_count)
                          )
        self.assertEqual(active_count,
                         0,
                         "Delete all flows failed"
                         )

        # TBD - For testing only, since Open vSWitch reports
        # ridiculously large capacity; remove
        sw_features.n_tables = 1
        tbl_stats.stats[0].max_entries = 10
        max_entries = tbl_stats.stats[0].max_entries

        # Dream up some flow information, i.e. space to chose from for
        # random flow parameter generation
        fi = flow_info()
        n = int(math.log(max_entries))
        if not overlapf:
            # Generated space smaller when testing overlaps,
            # to increase likelihood of some
            n = 2 * n
        fi.rand(n)

        # For each table, think up flows to fill it

        self.logger.debug("Creating flows")
        num_flows = 0
        num_overlaps = 0
        tbl_flows = []
        tbl_idx = 0

        while tbl_idx < sw_features.n_tables:
            flow_idx = 0
            while flow_idx < tbl_stats.stats[tbl_idx].max_entries:
                flow_out = flow_cfg()
                if overlapf and num_flows == 1:
                    # Make 2nd flow a copy of the first,
                    # to guarantee at least 1 overlap
                    flow_out = copy.deepcopy(tbl_flows[0])
                    flow_out.overlap = True
                    flow_out.overlaps_with = [0, 0]
                    num_overlaps = num_overlaps + 1
                else:
                    flow_out.rand(fi,
                                  tbl_stats.stats[tbl_idx].wildcards,
                                  sw_features.actions,
                                  map(lambda x: x.port_no, sw_features.ports)
                                  )
                    flow_out.overlap  = False
                    
                    for f in tbl_flows:
                        if (not overlapf or not f.overlap) \
                           and flow_out.overlaps(f, False):
                            flow_out.overlap = True
                            flow_out.overlaps_with = [f.tbl_idx, f.flow_idx]
                            num_overlaps = num_overlaps + 1

                flow_out.tbl_idx  = tbl_idx
                flow_out.flow_idx = flow_idx

                self.logger.debug("tbl_idx=%d, flow_idx=%d, %s" % (tbl_idx, flow_idx, str(flow_out)))

                tbl_flows.append(flow_out)

                num_flows = num_flows + 1
                flow_idx = flow_idx + 1
            tbl_idx = tbl_idx + 1

        self.logger.debug("Created " + str(num_flows)
                          + " flows, with " + str(num_overlaps)
                          + " overlaps"
                          )

        # Send all flows to switch

        self.logger.debug("Sending flows to switch")
        for f in tbl_flows:
            self.flow_add(f, overlapf)
            f.deleted = False

        # Send barrier, to make sure all flows are in
        self.do_barrier()               

        # Red back all flows from switch, and verify

        self.verify_flows(sw_features,
                          tbl_flows,
                          num_flows,
                          overlapf,
                          num_overlaps
                          )

        # Delete a flows from switch

        if strictf:
            # Strict delete
            
            # Delete a few flows, in random order, individually (i.e. strictly)
            
            del_flow_idxs = shuffle(range(len(tbl_flows)))
            # TBD - Limited, for testing only; remove
            del_flow_idxs = del_flow_idxs[0 : random.randint(3, 3)]
            for di in del_flow_idxs:
                f = tbl_flows[di]
                tbl_idx  = f.tbl_idx
                flow_idx = f.flow_idx
                if (overlapf and f.overlap):
                    self.logger.debug("Flow tbl_idx = " + str(tbl_idx)
                                      + ", flow_idx = " + str(flow_idx)
                                      + " was an overlap, skipping delete"
                                      )
                else:
                    self.logger.debug("Deleting flow, tbl_idx = "
                                      + str(tbl_idx) + ", flow_idx = "
                                      + str(flow_idx)
                                      )
                    self.flow_del(f, True)
                    f.deleted = True
                    num_flows = num_flows - 1

            # Send barrier, to make sure all flows are deleted
            self.do_barrier();

            # Red back all flows from switch, and verify

            self.verify_flows(sw_features,
                              tbl_flows,
                              num_flows,
                              overlapf,
                              num_overlaps
                              )

            # Delete all remaining flows, in random order,
            # individually (i.e. strictly)
            
            del_flow_idxs = shuffle(range(len(tbl_flows)))
            for di in del_flow_idxs:
                f = tbl_flows[di]
                if f.deleted:
                    continue
                tbl_idx  = f.tbl_idx
                flow_idx = f.flow_idx
                if (overlapf and f.overlap):
                    self.logger.debug("Flow tbl_idx = "
                                      + str(tbl_idx)
                                      + ", flow_idx = "
                                      + str(flow_idx)
                                      + " was an overlap, skipping delete"
                                      )
                else:
                    self.logger.debug("Deleting flow, tbl_idx = "
                                      + str(tbl_idx)
                                      + ", flow_idx = "
                                      + str(flow_idx)
                                      )
                    self.flow_del(f, True)
                    f.deleted = True
                    num_flows = num_flows - 1

            # Send barrier, to make sure all flows are deleted
            self.do_barrier()
            
            # Red back all flows from switch (i.e. none), and verify
            
            self.verify_flows(sw_features,
                              tbl_flows,
                              num_flows,
                              overlapf,
                              num_overlaps
                              )

        else:
            # Non-strict delete

            # Pick a flow at random that had at least 1 qualifier specified,
            # wildcard a qualifier that was specified,
            # and do a non-strict delete
            # Keep wildcarding specified qualifiers, one by one, and deleteing,
            # until everything is wildcarded,
            # and hence all flows should be deleted

            while True:
                f = tbl_flows[random.randint(0, len(tbl_flows) - 1)]
                if f.match.wildcards != tbl_stats.stats[f.tbl_idx].wildcards:
                    self.logger.debug("Choosing flow for basis of non-strict delete")
                    self.logger.debug("  tbl_idx=%d flow_idx=%d" % (f.tbl_idx, f.flow_idx))
                    self.logger.debug("  " + str(f))
                    break

            # For each qualifier, in random order, if it was specified,
            # wildcard it, do a delete, and check the results
                
            wildcard_idxs = shuffle(range(len(all_wildcards_list)))
            for wi in wildcard_idxs:
                w = all_wildcards_list[wi]
                if (f.match.wildcards & w) != 0:
                    continue

                if w ==  ofp.OFPFW_NW_SRC_MASK:
                    f.match.wildcards = (f.match.wildcards
                                         & ~ofp.OFPFW_NW_SRC_MASK
                                         ) \
                                        | ofp.OFPFW_NW_SRC_ALL
                    wn = "OFPFW_NW_SRC"
                elif w ==  ofp.OFPFW_NW_DST_MASK:
                    f.match.wildcards = (f.match.wildcards
                                         & ~ofp.OFPFW_NW_DST_MASK
                                         ) \
                                        | ofp.OFPFW_NW_DST_ALL
                    wn = "OFPFW_NW_DST"
                else:
                    f.match.wildcards = f.match.wildcards | w
                    wn = ofp.ofp_flow_wildcards_map[w]

                self.logger.debug("Adding wildcard %s" % (wn))
                self.logger.debug(str(f))

                # Mark all flows which would be deleted by this
                # non-strict delete
                
                for ff in tbl_flows:
                    if not ff.deleted and f.overlaps(ff, True):
                        self.logger.debug("Deleting flow, tbl_idx = "
                                          + str(ff.tbl_idx) + ", flow_idx = "
                                          + str(ff.flow_idx)
                                          )
                        ff.deleted = True
                        num_flows = num_flows - 1
                        
                self.flow_del(f, False)
                
                # Send barrier, to make sure all flows are deleted
                self.do_barrier()
                
                # Red back all flows from switch, and verify
                
                self.verify_flows(sw_features,
                                  tbl_flows,
                                  num_flows,
                                  overlapf,
                                  num_overlaps
                                  )



    def runTest(self):
        """
        Run all tests
        """

        self.test1(False, True)         # Test with no overlaps, strict delete
        self.test1(True,  True)         # Test with overlaps, strict delete
#        self.test1(False, False)        # Test with no overlaps, non-strict delete
#        self.test1(True,  False)        # Test with overlaps, non-strict delete

