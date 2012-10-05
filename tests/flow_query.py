"""
Flow query test case.

Attempts to fill switch to capacity with randomized flows, and ensure that
they all are read back correctly.
"""

# COMMON TEST PARAMETERS
#
# Name: wildcards
# Type: number
# Description:
# Overrides bitmap of supported wildcards reported by switch
# Default: none
#
# Name: wildcards_force
# Type: number
# Description:
# Bitmap of wildcards to always be set
# Default: none
#
# Name: actions
# Type: number
# Description:
# Overrides bitmap of supported actions reported by switch
# Default: none
#
# Name: actions_force
# Type: number
# Description:
# Bitmap of actions to always be used
# Default: none
#
# Name: ports
# Type: list of OF port numbers
# Description:
# Override list of OF port numbers reported by switch
# Default: none
#
# Name: queues
# Type: list of OF (port-number, queue-id) pairs
# Description:
# Override list of OF (port-number, queue-id) pairs returned by switch
# Default: none
#
# Name: vlans
# Type: list of VLAN ids
# Description:
# Override VLAN ids used in tests to given list
# Default: []
#
# Name: conservative_ordered_actions
# Type: boolean (True or False)
# Description:
# Compare flow actions lists as unordered
# Default: True


import math

import logging

import unittest
import random
import time

import oftest.controller  as controller
import oftest.cstruct     as ofp
import oftest.message     as message
import oftest.dataplane   as dataplane
import oftest.action      as action
import oftest.action_list as action_list
import oftest.parse       as parse
import pktact
import basic

from oftest.testutils import *
from time import sleep

#@var port_map Local copy of the configuration map from OF port
# numbers to OS interfaces
fq_port_map = None
#@var fq_config Local copy of global configuration data
fq_config = None


def test_set_init(config):
    """
    Set up function for packet action test classes

    @param config The configuration dictionary; see oft
    """

    basic.test_set_init(config)

    global fq_port_map
    global fq_config

    fq_port_map = config["port_map"]
    fq_config = config


def flip_coin():
    return random.randint(1, 100) <= 50


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


class Flow_Info:
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
    
        if test_param_get(fq_config, "vlans", []) != []:
           self.vlans = test_param_get(fq_config, "vlans", [])

           logging.info("Overriding VLAN ids to:")
           logging.info(self.vlans)
        else:
           self.vlans = []
           i = 0
           while i < n:
              self.vlans.append(random.randint(1, 4094))
              i = i + 1
    
        self.ethertypes = [0x0800, 0x0806]
        i = 0
        while i < n:
            self.ethertypes.append(random.randint(0, (1 << 16) - 1))
            i = i + 1
        self.ethertypes = shuffle(self.ethertypes)[0 : n]
    
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
    
        self.ip_protos = [1, 6, 17]
        i = 0
        while i < n:
            self.ip_protos.append(random.randint(0, (1 << 8) - 1))
            i = i + 1
        self.ip_protos = shuffle(self.ip_protos)[0 : n]
    
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
                      ofp.OFPFW_DL_DST,
                      ofp.OFPFW_DL_SRC,
                      ofp.OFPFW_DL_VLAN,
                      ofp.OFPFW_DL_VLAN_PCP,
                      ofp.OFPFW_DL_TYPE,
                      ofp.OFPFW_NW_TOS,
                      ofp.OFPFW_NW_PROTO,
                      ofp.OFPFW_NW_SRC_MASK,
                      ofp.OFPFW_NW_DST_MASK,
                      ofp.OFPFW_TP_SRC,
                      ofp.OFPFW_TP_DST
                      ]

# TBD - Need this because there are duplicates in ofp.ofp_flow_wildcards_map
# -- FIX
all_wildcard_names = {
    1                               : 'OFPFW_IN_PORT',
    2                               : 'OFPFW_DL_VLAN',
    4                               : 'OFPFW_DL_SRC',
    8                               : 'OFPFW_DL_DST',
    16                              : 'OFPFW_DL_TYPE',
    32                              : 'OFPFW_NW_PROTO',
    64                              : 'OFPFW_TP_SRC',
    128                             : 'OFPFW_TP_DST',
    1048576                         : 'OFPFW_DL_VLAN_PCP',
    2097152                         : 'OFPFW_NW_TOS'
}

def wildcard_set(x, w, val):
    result = x
    if w == ofp.OFPFW_NW_SRC_MASK:
        result = (result & ~ofp.OFPFW_NW_SRC_MASK) \
                 | (val << ofp.OFPFW_NW_SRC_SHIFT)
    elif w == ofp.OFPFW_NW_DST_MASK:
        result = (result & ~ofp.OFPFW_NW_DST_MASK) \
                 | (val << ofp.OFPFW_NW_DST_SHIFT)
    elif val == 0:
        result = result & ~w
    else:
        result = result | w
    return result

def wildcard_get(x, w):
    if w == ofp.OFPFW_NW_SRC_MASK:
        return (x & ofp.OFPFW_NW_SRC_MASK) >> ofp.OFPFW_NW_SRC_SHIFT
    if w == ofp.OFPFW_NW_DST_MASK:
        return (x & ofp.OFPFW_NW_DST_MASK) >> ofp.OFPFW_NW_DST_SHIFT
    return 1 if (x & w) != 0 else 0

def wildcards_to_str(wildcards):
    result = "{"
    sep = ""
    for w in all_wildcards_list:
        if (wildcards & w) == 0:
            continue
        if w == ofp.OFPFW_NW_SRC_MASK:
            n = wildcard_get(wildcards, w)
            if n > 0:
                result = result + sep + ("OFPFW_NW_SRC(%d)" % (n))
        elif w == ofp.OFPFW_NW_DST_MASK:
            n = wildcard_get(wildcards, w)
            if n > 0:
                result = result + sep + ("OFPFW_NW_DST(%d)" % (n))
        else:
            result = result + sep + all_wildcard_names[w]
        sep = ", "
    result = result +"}"
    return result

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

def actions_bmap_to_str(bm):
    result = "{"
    sep    = ""
    for a in all_actions_list:
        if ((1 << a) & bm) != 0:
            result = result + sep + ofp.ofp_action_type_map[a]
            sep = ", "
    result = result + "}"
    return result

def dl_addr_to_str(a):
    return "%x:%x:%x:%x:%x:%x" % tuple(a)

def ip_addr_to_str(a, n):
    if n is not None:
        a = a & ~((1 << (32 - n)) - 1)
    result = "%d.%d.%d.%d" % (a >> 24, \
                              (a >> 16) & 0xff, \
                              (a >> 8) & 0xff, \
                              a & 0xff \
                              )
    if n is not None:
        result = result + ("/%d" % (n))
    return result
    

class Flow_Cfg:
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

    # {pri, match} is considered a flow key
    def key_equal(self, x):
        if self.priority != x.priority:
            return False
        # TBD - Should this logic be moved to ofp_match.__eq__()?
        if self.match.wildcards != x.match.wildcards:
            return False
        if wildcard_get(self.match.wildcards, ofp.OFPFW_IN_PORT) == 0 \
           and self.match.in_port != x.match.in_port:
            return False
        if wildcard_get(self.match.wildcards, ofp.OFPFW_DL_DST) == 0 \
           and self.match.dl_dst != x.match.dl_dst:
            return False
        if wildcard_get(self.match.wildcards, ofp.OFPFW_DL_SRC) == 0 \
           and self.match.dl_src != x.match.dl_src:
            return False
        if wildcard_get(self.match.wildcards, ofp.OFPFW_DL_VLAN) == 0 \
           and self.match.dl_vlan != x.match.dl_vlan:
            return False
        if wildcard_get(self.match.wildcards, ofp.OFPFW_DL_VLAN_PCP) == 0 \
           and self.match.dl_vlan_pcp != x.match.dl_vlan_pcp:
            return False
        if wildcard_get(self.match.wildcards, ofp.OFPFW_DL_TYPE) == 0 \
           and self.match.dl_type != x.match.dl_type:
            return False
        if wildcard_get(self.match.wildcards, ofp.OFPFW_NW_TOS) == 0 \
           and self.match.nw_tos != x.match.nw_tos:
            return False
        if wildcard_get(self.match.wildcards, ofp.OFPFW_NW_PROTO) == 0 \
           and self.match.nw_proto != x.match.nw_proto:
            return False
        n = wildcard_get(self.match.wildcards, ofp.OFPFW_NW_SRC_MASK)
        if n < 32:
            m = ~((1 << n) - 1)
            if (self.match.nw_src & m) != (x.match.nw_src & m):
                return False
        n = wildcard_get(self.match.wildcards, ofp.OFPFW_NW_DST_MASK)
        if n < 32:
            m = ~((1 << n) - 1)
            if (self.match.nw_dst & m) != (x.match.nw_dst & m):
                return False
        if wildcard_get(self.match.wildcards, ofp.OFPFW_TP_SRC) == 0 \
               and self.match.tp_src != x.match.tp_src:
            return False
        if wildcard_get(self.match.wildcards, ofp.OFPFW_TP_DST) == 0 \
               and self.match.tp_dst != x.match.tp_dst:
            return False
        return True

    def actions_equal(self, x):
        if test_param_get(fq_config, "conservative_ordered_actions", True):
            # Compare actions lists as unordered
            
            aa = copy.deepcopy(x.actions.actions)
            for a in self.actions.actions:
                i = 0
                while i < len(aa):
                    if a == aa[i]:
                        break
                    i = i + 1
                if i < len(aa):
                    aa.pop(i)
                else:
                    return False
            return aa == []
        else:
            return self.actions == x.actions

    def non_key_equal(self, x):
        if self.cookie != x.cookie:
            return False
        if self.idle_timeout != x.idle_timeout:
            return False
        if self.hard_timeout != x.hard_timeout:
            return False
        return self.actions_equal(x)
        
    def key_str(self):
        result = "priority=%d" % self.priority
        # TBD - Would be nice if ofp_match.show() was better behaved
        # (no newlines), and more intuitive (things in hex where approprate), etc.
        result = result + (", wildcards=0x%x=%s" \
                           % (self.match.wildcards, \
                              wildcards_to_str(self.match.wildcards) \
                              )
                           )
        if wildcard_get(self.match.wildcards, ofp.OFPFW_IN_PORT) == 0:
            result = result + (", in_port=%d" % (self.match.in_port))
        if wildcard_get(self.match.wildcards, ofp.OFPFW_DL_DST) == 0:
            result = result + (", dl_dst=%s" \
                               % (dl_addr_to_str(self.match.dl_dst)) \
                               )
        if wildcard_get(self.match.wildcards, ofp.OFPFW_DL_SRC) == 0:
            result = result + (", dl_src=%s" \
                               % (dl_addr_to_str(self.match.dl_src)) \
                               )
        if wildcard_get(self.match.wildcards, ofp.OFPFW_DL_VLAN) == 0:
            result = result + (", dl_vlan=%d" % (self.match.dl_vlan))
        if wildcard_get(self.match.wildcards, ofp.OFPFW_DL_VLAN_PCP) == 0:
            result = result + (", dl_vlan_pcp=%d" % (self.match.dl_vlan_pcp))
        if wildcard_get(self.match.wildcards, ofp.OFPFW_DL_TYPE) == 0:
            result = result + (", dl_type=0x%x" % (self.match.dl_type))
        if wildcard_get(self.match.wildcards, ofp.OFPFW_NW_TOS) == 0:
            result = result + (", nw_tos=0x%x" % (self.match.nw_tos))
        if wildcard_get(self.match.wildcards, ofp.OFPFW_NW_PROTO) == 0:
            result = result + (", nw_proto=%d" % (self.match.nw_proto))
        n = wildcard_get(self.match.wildcards, ofp.OFPFW_NW_SRC_MASK)
        if n < 32:
            result = result + (", nw_src=%s" % \
                               (ip_addr_to_str(self.match.nw_src, 32 - n)) \
                               )
        n = wildcard_get(self.match.wildcards, ofp.OFPFW_NW_DST_MASK)
        if n < 32:
            result = result + (", nw_dst=%s" % \
                               (ip_addr_to_str(self.match.nw_dst, 32 - n)) \
                               )
        if wildcard_get(self.match.wildcards, ofp.OFPFW_TP_SRC) == 0:
            result = result + (", tp_src=%d" % self.match.tp_src)
        if wildcard_get(self.match.wildcards, ofp.OFPFW_TP_DST) == 0:
            result = result + (", tp_dst=%d" % self.match.tp_dst)
        return result

    def __eq__(self, x):
        return (self.key_equal(x) and self.non_key_equal(x))

    def __str__(self):
        result = self.key_str()
        result = result + (", cookie=%d" % self.cookie)
        result = result + (", idle_timeout=%d" % self.idle_timeout)
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

    def rand_actions_ordered(self, fi, valid_actions, valid_ports, valid_queues):
        # Action lists are ordered, so pick an ordered random subset of
        # supported actions

        actions_force = test_param_get(fq_config, "actions_force", 0)
        if actions_force != 0:
            logging.info("Forced actions:")
            logging.info(actions_bmap_to_str(actions_force))

        ACTION_MAX_LEN = 65535 # @fixme Should be test param?
        supported_actions = []
        for a in all_actions_list:
            if ((1 << a) & valid_actions) != 0:
                supported_actions.append(a)

        actions \
            = shuffle(supported_actions)[0 : random.randint(1, len(supported_actions))]

        for a in all_actions_list:
            if ((1 << a) & actions_force) != 0:
                actions.append(a)

        actions = shuffle(actions)

        set_vlanf   = False
        strip_vlanf = False
        self.actions = action_list.action_list()
        for a in actions:
            act = None
            if a == ofp.OFPAT_OUTPUT:
                pass                    # OUTPUT actions must come last
            elif a == ofp.OFPAT_SET_VLAN_VID:
               if not strip_vlanf:
                  act = action.action_set_vlan_vid()
                  act.vlan_vid = fi.rand_vlan()
                  set_vlanf = True
            elif a == ofp.OFPAT_SET_VLAN_PCP:
               if not strip_vlanf:
                  act = action.action_set_vlan_pcp()
                  act.vlan_pcp = random.randint(0, (1 << 3) - 1)
                  set_vlanf = True
            elif a == ofp.OFPAT_STRIP_VLAN:
               if not set_vlanf:
                  act = action.action_strip_vlan()
                  strip_vlanf = True
            elif a == ofp.OFPAT_SET_DL_SRC:
                act = action.action_set_dl_src()
                act.dl_addr = fi.rand_dl_addr()
            elif a == ofp.OFPAT_SET_DL_DST:
                act = action.action_set_dl_dst()
                act.dl_addr = fi.rand_dl_addr()
            elif a == ofp.OFPAT_SET_NW_SRC:
                act = action.action_set_nw_src()
                act.nw_addr = fi.rand_ip_addr()
            elif a == ofp.OFPAT_SET_NW_DST:
                act = action.action_set_nw_dst()
                act.nw_addr = fi.rand_ip_addr()
            elif a == ofp.OFPAT_SET_NW_TOS:
                act = action.action_set_nw_tos()
                act.nw_tos = fi.rand_ip_tos()
            elif a == ofp.OFPAT_SET_TP_SRC:
                act = action.action_set_tp_src()
                act.tp_port = fi.rand_l4_port()
            elif a == ofp.OFPAT_SET_TP_DST:
                act = action.action_set_tp_dst()
                act.tp_port = fi.rand_l4_port()
            elif a == ofp.OFPAT_ENQUEUE:
                pass                    # Enqueue actions must come last
            if act:
                act.max_len = ACTION_MAX_LEN
                self.actions.add(act)
                
        p = random.randint(1, 100)
        if (((1 << ofp.OFPAT_ENQUEUE) & actions_force) != 0 or p <= 33) \
           and len(valid_queues) > 0 \
           and ofp.OFPAT_ENQUEUE in actions:
            # In not forecd, one third of the time, include ENQUEUE actions
            # at end of list
            # At most 1 ENQUEUE action
            act = action.action_enqueue()
            (act.port, act.queue_id) = rand_pick(valid_queues)
            act.max_len = ACTION_MAX_LEN
            self.actions.add(act)
        if (((1 << ofp.OFPAT_OUTPUT) & actions_force) != 0 \
            or (p > 33 and p <= 66) \
            ) \
            and len(valid_ports) > 0 \
            and ofp.OFPAT_OUTPUT in actions:
            # One third of the time, include OUTPUT actions at end of list
            port_idxs = shuffle(range(len(valid_ports)))
            # Only 1 output action allowed if IN_PORT wildcarded
            n = 1 if wildcard_get(self.match.wildcards, ofp.OFPFW_IN_PORT) != 0 \
                else random.randint(1, len(valid_ports))
            port_idxs = port_idxs[0 : n]
            for pi in port_idxs:
                act = action.action_output()
                act.port = valid_ports[pi]
                act.max_len = ACTION_MAX_LEN
                if act.port != ofp.OFPP_IN_PORT \
                   or wildcard_get(self.match.wildcards, ofp.OFPFW_IN_PORT) == 0:
                    # OUTPUT(IN_PORT) only valid if OFPFW_IN_PORT not wildcarded
                    self.actions.add(act)
        else:
            # One third of the time, include neither
            pass


    # Randomize flow data for flow modifies (i.e. cookie and actions)
    def rand_mod(self, fi, valid_actions, valid_ports, valid_queues):
        self.cookie = random.randint(0, (1 << 53) - 1)

        # By default, test with conservative ordering conventions
        # This should probably be indicated in a profile
        if test_param_get(fq_config, "conservative_ordered_actions", True):
            self.rand_actions_ordered(fi, valid_actions, valid_ports, valid_queues)
            return self

        actions_force = test_param_get(fq_config, "actions_force", 0)
        if actions_force != 0:
            logging.info("Forced actions:")
            logging.info(actions_bmap_to_str(actions_force))

        ACTION_MAX_LEN = 65535 # @fixme Should be test param?
        supported_actions = []
        for a in all_actions_list:
            if ((1 << a) & valid_actions) != 0:
                supported_actions.append(a)

        actions \
            = shuffle(supported_actions)[0 : random.randint(1, len(supported_actions))]

        for a in all_actions_list:
            if ((1 << a) & actions_force) != 0:
                actions.append(a)

        actions = shuffle(actions)

        self.actions = action_list.action_list()
        for a in actions:
            if a == ofp.OFPAT_OUTPUT:
                # TBD - Output actions are clustered in list, spread them out?
                if len(valid_ports) == 0:
                    continue
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
                act = action.action_set_vlan_pcp()
                act.vlan_pcp = random.randint(0, (1 << 3) - 1)
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
                if len(valid_queues) == 0:
                    continue
                qidxs = shuffle(range(len(valid_queues)))
                qidxs = qidxs[0 : random.randint(1, len(valid_queues))]
                for qi in qidxs:
                    act = action.action_enqueue()
                    (act.port, act.queue_id) = valid_queues[qi]
                    self.actions.add(act)

        return self

    # Randomize flow cfg
    def rand(self, fi, wildcards_force, valid_wildcards, valid_actions, valid_ports,
             valid_queues):
        if wildcards_force != 0:
            logging.info("Wildcards forced:")
            logging.info(wildcards_to_str(wildcards_force))
        
        # Start with no wildcards, i.e. everything specified
        self.match.wildcards = 0

        if wildcards_force != 0:
            exact = False
        else:
            # Make approx. 5% of flows exact
            exact = (random.randint(1, 100) <= 5)

        # For each qualifier Q,
        #   if (wildcarding is not supported for Q,
        #       or an exact flow is specified
        #       or a coin toss comes up heads), 
        #      specify Q
        #   else
        #      wildcard Q

        if wildcard_get(wildcards_force, ofp.OFPFW_IN_PORT) == 0 \
               and (wildcard_get(valid_wildcards, ofp.OFPFW_IN_PORT) == 0 \
                    or exact \
                    or flip_coin() \
                    ):
            self.match.in_port = rand_pick(valid_ports)
        else:
            self.match.wildcards = wildcard_set(self.match.wildcards, \
                                                ofp.OFPFW_IN_PORT, \
                                                1 \
                                                )
            
        if wildcard_get(wildcards_force, ofp.OFPFW_DL_DST) == 0 \
               and (wildcard_get(valid_wildcards, ofp.OFPFW_DL_DST) == 0 \
                    or exact \
                    or flip_coin() \
                    ):
            self.match.dl_dst = fi.rand_dl_addr()
        else:
            self.match.wildcards = wildcard_set(self.match.wildcards, \
                                                ofp.OFPFW_DL_DST, \
                                                1 \
                                                )

        if wildcard_get(wildcards_force, ofp.OFPFW_DL_SRC) == 0 \
               and (wildcard_get(valid_wildcards, ofp.OFPFW_DL_SRC) == 0 \
                    or exact \
                    or flip_coin() \
                    ):
            self.match.dl_src = fi.rand_dl_addr()
        else:
            self.match.wildcards = wildcard_set(self.match.wildcards, \
                                                ofp.OFPFW_DL_SRC, \
                                                1 \
                                                )

        if wildcard_get(wildcards_force, ofp.OFPFW_DL_VLAN) == 0 \
               and (wildcard_get(valid_wildcards, ofp.OFPFW_DL_VLAN) == 0 \
                    or exact \
                    or flip_coin() \
                    ):
            self.match.dl_vlan = fi.rand_vlan()
        else:
            self.match.wildcards = wildcard_set(self.match.wildcards, \
                                                ofp.OFPFW_DL_VLAN, \
                                                1 \
                                                )

        if wildcard_get(wildcards_force, ofp.OFPFW_DL_VLAN_PCP) == 0 \
               and (wildcard_get(valid_wildcards, ofp.OFPFW_DL_VLAN_PCP) == 0 \
                    or exact \
                    or flip_coin() \
                    ):
            self.match.dl_vlan_pcp = random.randint(0, (1 << 3) - 1)
        else:
            self.match.wildcards = wildcard_set(self.match.wildcards, \
                                                ofp.OFPFW_DL_VLAN_PCP, \
                                                1 \
                                                )

        if wildcard_get(wildcards_force, ofp.OFPFW_DL_TYPE) == 0 \
               and (wildcard_get(valid_wildcards, ofp.OFPFW_DL_TYPE) == 0 \
                    or exact \
                    or flip_coin() \
                    ):
            self.match.dl_type = fi.rand_ethertype()
        else:
            self.match.wildcards = wildcard_set(self.match.wildcards, \
                                                ofp.OFPFW_DL_TYPE, \
                                                1 \
                                                )

        n = wildcard_get(wildcards_force, ofp.OFPFW_NW_SRC_MASK)
        if n == 0:
            if exact or flip_coin():
                n = 0
            else:
                n = wildcard_get(valid_wildcards, ofp.OFPFW_NW_SRC_MASK)
                if n > 32:
                    n = 32
                n = random.randint(0, n)
        self.match.wildcards = wildcard_set(self.match.wildcards, \
                                            ofp.OFPFW_NW_SRC_MASK, \
                                            n \
                                            )
        if n < 32:
            self.match.nw_src    = fi.rand_ip_addr() & ~((1 << n) - 1)
            # Specifying any IP address match other than all bits
            # don't care requires that Ethertype is one of {IP, ARP}
            if flip_coin():
                self.match.dl_type   = rand_pick([0x0800, 0x0806])
                self.match.wildcards = wildcard_set(self.match.wildcards, \
                                                    ofp.OFPFW_DL_TYPE, \
                                                    0 \
                                                    )

        n = wildcard_get(wildcards_force, ofp.OFPFW_NW_DST_MASK)
        if n == 0:
            if exact or flip_coin():
                n = 0
            else:
                n = wildcard_get(valid_wildcards, ofp.OFPFW_NW_DST_MASK)
                if n > 32:
                    n = 32
                n = random.randint(0, n)
        self.match.wildcards = wildcard_set(self.match.wildcards, \
                                            ofp.OFPFW_NW_DST_MASK, \
                                            n \
                                            )
        if n < 32:
            self.match.nw_dst    = fi.rand_ip_addr() & ~((1 << n) - 1)
            # Specifying any IP address match other than all bits
            # don't care requires that Ethertype is one of {IP, ARP}
            if flip_coin():
                self.match.dl_type   = rand_pick([0x0800, 0x0806])
                self.match.wildcards = wildcard_set(self.match.wildcards, \
                                                    ofp.OFPFW_DL_TYPE, \
                                                    0 \
                                                    )

        if wildcard_get(wildcards_force, ofp.OFPFW_NW_TOS) == 0 \
               and (wildcard_get(valid_wildcards, ofp.OFPFW_NW_TOS) == 0 \
                    or exact \
                    or flip_coin() \
                    ):
            self.match.nw_tos = fi.rand_ip_tos()
            # Specifying a TOS value requires that Ethertype is IP
            if flip_coin():
                self.match.dl_type   = 0x0800
                self.match.wildcards = wildcard_set(self.match.wildcards, \
                                                    ofp.OFPFW_DL_TYPE, \
                                                    0 \
                                                    )
        else:
            self.match.wildcards = wildcard_set(self.match.wildcards, \
                                                ofp.OFPFW_NW_TOS, \
                                                1 \
                                                )

        # Known issue on OVS with specifying nw_proto w/o dl_type as IP
        if wildcard_get(wildcards_force, ofp.OFPFW_NW_PROTO) == 0 \
               and (wildcard_get(valid_wildcards, ofp.OFPFW_NW_PROTO) == 0 \
                    or exact \
                    or flip_coin() \
                    ):
            self.match.nw_proto = fi.rand_ip_proto()
            # Specifying an IP protocol requires that Ethertype is IP
            if flip_coin():
                self.match.dl_type   = 0x0800
                self.match.wildcards = wildcard_set(self.match.wildcards, \
                                                    ofp.OFPFW_DL_TYPE, \
                                                    0 \
                                                    )
        else:            
            self.match.wildcards = wildcard_set(self.match.wildcards, \
                                                ofp.OFPFW_NW_PROTO, \
                                                1 \
                                                )

        if wildcard_get(wildcards_force, ofp.OFPFW_TP_SRC) == 0 \
               and (wildcard_get(valid_wildcards, ofp.OFPFW_TP_SRC) == 0 \
                    or exact\
                    or flip_coin() \
                    ):
            self.match.tp_src = fi.rand_l4_port()
            # Specifying a L4 port requires that IP protcol is
            # one of {ICMP, TCP, UDP}
            if flip_coin():
                self.match.nw_proto = rand_pick([1, 6, 17])
                self.match.wildcards = wildcard_set(self.match.wildcards, \
                                                    ofp.OFPFW_NW_PROTO, \
                                                    0 \
                                                    )
                # Specifying a L4 port requirues that Ethertype is IP
                self.match.dl_type   = 0x0800
                self.match.wildcards = wildcard_set(self.match.wildcards, \
                                                    ofp.OFPFW_DL_TYPE, \
                                                    0 \
                                                    )
                if self.match.nw_proto == 1:
                    self.match.tp_src = self.match.tp_src & 0xff
        else:
            self.match.wildcards = wildcard_set(self.match.wildcards, \
                                                ofp.OFPFW_TP_SRC, \
                                                1 \
                                                )

        if wildcard_get(wildcards_force, ofp.OFPFW_TP_DST) == 0 \
               and (wildcard_get(valid_wildcards, ofp.OFPFW_TP_DST) == 0 \
                    or exact \
                    or flip_coin() \
                    ):
            self.match.tp_dst = fi.rand_l4_port()
            # Specifying a L4 port requires that IP protcol is
            # one of {ICMP, TCP, UDP}
            if flip_coin():
                self.match.nw_proto = rand_pick([1, 6, 17])
                self.match.wildcards = wildcard_set(self.match.wildcards, \
                                                    ofp.OFPFW_NW_PROTO, \
                                                    0 \
                                                    )
                # Specifying a L4 port requirues that Ethertype is IP
                self.match.dl_type   = 0x0800
                self.match.wildcards = wildcard_set(self.match.wildcards, \
                                                    ofp.OFPFW_DL_TYPE, \
                                                    0 \
                                                    )
                if self.match.nw_proto == 1:
                    self.match.tp_dst = self.match.tp_dst & 0xff
        else:
            self.match.wildcards = wildcard_set(self.match.wildcards, \
                                                ofp.OFPFW_TP_DST, \
                                                1 \
                                                )

        # If nothing is wildcarded, it is an exact flow spec -- some switches
        # (Open vSwitch, for one) *require* that exact flow specs
        # have priority 65535.
        self.priority = 65535 if self.match.wildcards == 0 \
                        else fi.rand_priority()

        # N.B. Don't make the timeout too short, else the flow might
        # disappear before we get a chance to check for it.
        t = random.randint(0, 65535)
        self.idle_timeout = 0 if t < 60 else t
        t = random.randint(0, 65535)
        self.hard_timeout = 0 if t < 60 else t

        self.rand_mod(fi, valid_actions, valid_ports, valid_queues)

        return self

    # Return flow cfg in canonical form
    # - There are dependencies between flow qualifiers, e.g. it only makes
    #   sense to qualify nw_proto if dl_type is qualified to be 0x0800 (IP).
    #   The canonical form of flow match criteria will "wildcard out"
    #   all such cases.
    def canonical(self):
        result = copy.deepcopy(self)
        
        if wildcard_get(result.match.wildcards, ofp.OFPFW_DL_VLAN) != 0:
            result.match.wildcards = wildcard_set(result.match.wildcards, \
                                                  ofp.OFPFW_DL_VLAN_PCP, \
                                                  1 \
                                                  )

        if wildcard_get(result.match.wildcards, ofp.OFPFW_DL_TYPE) != 0 \
               or result.match.dl_type not in [0x0800, 0x0806]:
            # dl_tyoe is wildcarded, or specified as something other
            # than IP or ARP
            # => nw_src, nw_dst, nw_proto cannot be specified,
            # must be wildcarded
            result.match.wildcards = wildcard_set(result.match.wildcards, \
                                                  ofp.OFPFW_NW_SRC_MASK, \
                                                  32 \
                                                  )
            result.match.wildcards = wildcard_set(result.match.wildcards, \
                                                  ofp.OFPFW_NW_DST_MASK, \
                                                  32 \
                                                  )
            result.match.wildcards = wildcard_set(result.match.wildcards, \
                                                  ofp.OFPFW_NW_PROTO, \
                                                  1 \
                                                  )

        if wildcard_get(result.match.wildcards, ofp.OFPFW_DL_TYPE) != 0 \
               or result.match.dl_type != 0x0800:
            # dl_type is wildcarded, or specified as something other than IP
            # => nw_tos, tp_src and tp_dst cannot be specified,
            #    must be wildcarded
            result.match.wildcards = wildcard_set(result.match.wildcards, \
                                                  ofp.OFPFW_NW_TOS, \
                                                  1 \
                                                  )
            result.match.wildcards = wildcard_set(result.match.wildcards, \
                                                  ofp.OFPFW_TP_SRC, \
                                                  1 \
                                                  )
            result.match.wildcards = wildcard_set(result.match.wildcards, \
                                                  ofp.OFPFW_TP_DST, \
                                                  1 \
                                                  )
            result.match.wildcards = wildcard_set(result.match.wildcards, \
                                                  ofp.OFPFW_NW_SRC_MASK, \
                                                  32 \
                                                  )
            result.match.wildcards = wildcard_set(result.match.wildcards, \
                                                  ofp.OFPFW_NW_DST_MASK, \
                                                  32 \
                                                  )
            result.match.wildcards = wildcard_set(result.match.wildcards, \
                                                  ofp.OFPFW_NW_PROTO, \
                                                  1 \
                                                  )
            
        if wildcard_get(result.match.wildcards, ofp.OFPFW_NW_PROTO) != 0 \
               or result.match.nw_proto not in [1, 6, 17]:
            # nw_proto is wildcarded, or specified as something other than ICMP,
            # TCP or UDP
            # => tp_src and tp_dst cannot be specified, must be wildcarded
            result.match.wildcards = wildcard_set(result.match.wildcards, \
                                                  ofp.OFPFW_TP_SRC, \
                                                  1 \
                                                  )
            result.match.wildcards = wildcard_set(result.match.wildcards, \
                                                  ofp.OFPFW_TP_DST, \
                                                  1 \
                                                  )
        return result

    # Overlap check
    # delf == True <=> Check for delete overlap, else add overlap
    # "Add overlap" is defined as there exists a packet that could match both the
    # receiver and argument flowspecs
    # "Delete overlap" is defined as the specificity of the argument flowspec
    # is greater than or equal to the specificity of the receiver flowspec
    def overlaps(self, x, delf):
        if wildcard_get(self.match.wildcards, ofp.OFPFW_IN_PORT) == 0:
            if wildcard_get(x.match.wildcards, ofp.OFPFW_IN_PORT) == 0:
                if self.match.in_port != x.match.in_port:
                    return False        # Both specified, and not equal
            elif delf:
                return False            # Receiver more specific
        if wildcard_get(self.match.wildcards, ofp.OFPFW_DL_VLAN) == 0:
            if wildcard_get(x.match.wildcards, ofp.OFPFW_DL_VLAN) == 0:
                if self.match.dl_vlan != x.match.dl_vlan:
                    return False        # Both specified, and not equal
            elif delf:
                return False            # Receiver more specific
        if wildcard_get(self.match.wildcards, ofp.OFPFW_DL_SRC) == 0:
            if wildcard_get(x.match.wildcards, ofp.OFPFW_DL_SRC) == 0:
                if self.match.dl_src != x.match.dl_src:
                    return False        # Both specified, and not equal
            elif delf:
                return False            # Receiver more specific
        if wildcard_get(self.match.wildcards, ofp.OFPFW_DL_DST) == 0:
            if wildcard_get(x.match.wildcards, ofp.OFPFW_DL_DST) == 0:
                if self.match.dl_dst != x.match.dl_dst:
                    return False        # Both specified, and not equal
            elif delf:
                return False            # Receiver more specific
        if wildcard_get(self.match.wildcards, ofp.OFPFW_DL_TYPE) == 0:
            if wildcard_get(x.match.wildcards, ofp.OFPFW_DL_TYPE) == 0:
                if self.match.dl_type != x.match.dl_type:
                    return False        # Both specified, and not equal
            elif delf:
                return False            # Recevier more specific
        if wildcard_get(self.match.wildcards, ofp.OFPFW_NW_PROTO) == 0:
            if wildcard_get(x.match.wildcards, ofp.OFPFW_NW_PROTO) == 0:
                if self.match.nw_proto != x.match.nw_proto:
                    return False        # Both specified, and not equal
            elif delf:
                return False            # Receiver more specific
        if wildcard_get(self.match.wildcards, ofp.OFPFW_TP_SRC) == 0:
            if wildcard_get(x.match.wildcards, ofp.OFPFW_TP_SRC) == 0:
                if self.match.tp_src != x.match.tp_src:
                    return False        # Both specified, and not equal
            elif delf:
                return False            # Receiver more specific
        if wildcard_get(self.match.wildcards, ofp.OFPFW_TP_DST) == 0:
            if wildcard_get(x.match.wildcards, ofp.OFPFW_TP_DST) == 0:
                if self.match.tp_dst != x.match.tp_dst:
                    return False        # Both specified, and not equal
            elif delf:
                return False            # Receiver more specific
        na = wildcard_get(self.match.wildcards, ofp.OFPFW_NW_SRC_MASK)
        nb = wildcard_get(x.match.wildcards, ofp.OFPFW_NW_SRC_MASK)
        if delf and na < nb:
            return False                # Receiver more specific
        if (na < 32 and nb < 32):
            m = ~((1 << na) - 1) & ~((1 << nb) - 1)
            if (self.match.nw_src & m) != (x.match.nw_src & m):
                return False            # Overlapping bits not equal
        na = wildcard_get(self.match.wildcards, ofp.OFPFW_NW_DST_MASK)
        nb = wildcard_get(x.match.wildcards, ofp.OFPFW_NW_DST_MASK)
        if delf and na < nb:
            return False                # Receiver more specific
        if (na < 32 and nb < 32):
            m = ~((1 << na) - 1) & ~((1 << nb) - 1)
            if (self.match.nw_dst & m) != (x.match.nw_dst & m):
                return False            # Overlapping bits not equal
        if wildcard_get(self.match.wildcards, ofp.OFPFW_DL_VLAN_PCP) == 0:
            if wildcard_get(x.match.wildcards, ofp.OFPFW_DL_VLAN_PCP) == 0:
                if self.match.dl_vlan_pcp != x.match.dl_vlan_pcp:
                    return False        # Both specified, and not equal
            elif delf:
                return False            # Receiver more specific
        if wildcard_get(self.match.wildcards, ofp.OFPFW_NW_TOS) == 0:
            if wildcard_get(x.match.wildcards, ofp.OFPFW_NW_TOS) == 0:
                if self.match.nw_tos != x.match.nw_tos:
                    return False        # Both specified, and not equal
            elif delf:
                return False            # Receiver more specific
        return True                     # Flows overlap

    def to_flow_mod_msg(self, msg):
        msg.match        = self.match
        msg.cookie       = self.cookie
        msg.idle_timeout = self.idle_timeout
        msg.hard_timeout = self.hard_timeout
        msg.priority     = self.priority
        msg.actions      = self.actions
        return msg

    def from_flow_stat(self, msg):
        self.match        = msg.match
        self.cookie       = msg.cookie
        self.idle_timeout = msg.idle_timeout
        self.hard_timeout = msg.hard_timeout
        self.priority     = msg.priority
        self.actions      = msg.actions

    def from_flow_rem(self, msg):
        self.match        = msg.match
        self.idle_timeout = msg.idle_timeout
        self.priority     = msg.priority


class Flow_Tbl:
    def clear(self):
        self.dict = {}

    def __init__(self):
        self.clear()

    def find(self, f):
        return self.dict.get(f.key_str(), None)

    def insert(self, f):
        self.dict[f.key_str()] = f

    def delete(self, f):
        del self.dict[f.key_str()]

    def values(self):
        return self.dict.values()

    def count(self):
        return len(self.dict)

    def rand(self, wildcards_force, sw, fi, num_flows):
        self.clear()
        i = 0
        tbl = 0
        j = 0
        while i < num_flows:
            fc = Flow_Cfg()
            fc.rand(fi, \
                    wildcards_force, \
                    sw.tbl_stats.stats[tbl].wildcards, \
                    sw.sw_features.actions, \
                    sw.valid_ports, \
                    sw.valid_queues \
                    )
            fc = fc.canonical()
            if self.find(fc):
                continue
            fc.send_rem = False
            self.insert(fc)
            i = i + 1
            j = j + 1
            if j >= sw.tbl_stats.stats[tbl].max_entries:
                tbl = tbl + 1
                j = 0


class Switch:
    # Members:
    # controller   - switch's test controller
    # sw_features  - switch's OFPT_FEATURES_REPLY message
    # valid_ports  - list of valid port numbers
    # valid_queues - list of valid [port, queue] pairs
    # tbl_stats    - switch's OFPT_STATS_REPLY message, for table stats request
    # queue_stats  - switch's OFPT_STATS_REPLY message, for queue stats request
    # flow_stats   - switch's OFPT_STATS_REPLY message, for flow stats request
    # flow_tbl     - (test's idea of) switch's flow table

    def __init__(self):
        self.controller   = None
        self.sw_features  = None
        self.valid_ports  = []
        self.valid_queues = []
        self.tbl_stats    = None
        self.flow_stats   = None
        self.flow_tbl     = Flow_Tbl()
        self.error_msgs   = []
        self.removed_msgs = []

    def error_handler(self, controller, msg, rawmsg):
        logging.info("Got an ERROR message, type=%d, code=%d" \
                          % (msg.type, msg.code) \
                          )
        logging.info("Message header:")
        logging.info(msg.header.show())
        self.error_msgs.append(msg)

    def removed_handler(self, controller, msg, rawmsg):
        logging.info("Got a REMOVED message")
        logging.info("Message header:")
        logging.info(msg.header.show())
        self.removed_msgs.append(msg)

    def controller_set(self, controller):
        self.controller = controller
        # Register error message handler
        self.error_msgs = []
        self.removed_msgs = []
        controller.register(ofp.OFPT_ERROR, self.error_handler)
        controller.register(ofp.OFPT_FLOW_REMOVED, self.removed_handler)

    def features_get(self):
        # Get switch features
        request = message.features_request()
        (self.sw_features, pkt) = self.controller.transact(request)
        if self.sw_features is None:
            logging.error("Get switch features failed")
            return False
        self.valid_ports = map(lambda x: x.port_no, self.sw_features.ports)
        logging.info("Ports reported by switch:")
        logging.info(self.valid_ports)
        ports_override = test_param_get(fq_config, "ports", [])
        if ports_override != []:
            logging.info("Overriding ports to:")
            logging.info(ports_override)
            self.valid_ports = ports_override
        
        # TBD - OFPP_LOCAL is returned by OVS is switch features --
        # is that universal?

        # TBD - There seems to be variability in which switches support which
        # ports; need to sort that out
        # TBD - Is it legal to enqueue to a special port?  Depends on switch?
#         self.valid_ports.extend([ofp.OFPP_IN_PORT, \
#                                  ofp.OFPP_NORMAL, \
#                                  ofp.OFPP_FLOOD, \
#                                  ofp.OFPP_ALL, \
#                                  ofp.OFPP_CONTROLLER \
#                                  ] \
#                                 )
        logging.info("Supported actions reported by switch:")
        logging.info("0x%x=%s" \
                       % (self.sw_features.actions, \
                          actions_bmap_to_str(self.sw_features.actions) \
                          ) \
                       )
        actions_override = test_param_get(fq_config, "actions", -1)
        if actions_override != -1:
            logging.info("Overriding supported actions to:")
            logging.info(actions_bmap_to_str(actions_override))
            self.sw_features.actions = actions_override
        return True

    def tbl_stats_get(self):
        # Get table stats
        request = message.table_stats_request()
        (self.tbl_stats, pkt) = self.controller.transact(request)
        if self.tbl_stats is None:
            logging.error("Get table stats failed")
            return False
        i = 0
        for ts in self.tbl_stats.stats:
            logging.info("Supported wildcards for table %d reported by switch:"
                           % (i)
                           )
            logging.info("0x%x=%s" \
                           % (ts.wildcards, \
                              wildcards_to_str(ts.wildcards) \
                              ) \
                           )
            wildcards_override = test_param_get(fq_config, "wildcards", -1)
            if wildcards_override != -1:
                logging.info("Overriding supported wildcards for table %d to:"
                               % (i)
                               )
                logging.info(wildcards_to_str(wildcards_override))
                ts.wildcards = wildcards_override
            i = i + 1
        return True

    def queue_stats_get(self):
        # Get queue stats
        request = message.queue_stats_request()
        request.port_no  = ofp.OFPP_ALL
        request.queue_id = ofp.OFPQ_ALL
        (self.queue_stats, pkt) = self.controller.transact(request)
        if self.queue_stats is None:
            logging.error("Get queue stats failed")
            return False
        self.valid_queues = map(lambda x: (x.port_no, x.queue_id), \
                                self.queue_stats.stats \
                                )
        logging.info("(Port, queue) pairs reported by switch:")
        logging.info(self.valid_queues)
        queues_override = test_param_get(fq_config, "queues", [])
        if queues_override != []:
            logging.info("Overriding (port, queue) pairs to:")
            logging.info(queues_override)
            self.valid_queues = queues_override
        return True

    def connect(self, controller):
        # Connect to controller, and get all switch capabilities
        self.controller_set(controller)
        return (self.features_get() \
                and self.tbl_stats_get() \
                and self.queue_stats_get() \
                )

    def flow_stats_get(self, limit = 10000):
        request = message.flow_stats_request()
        query_match           = ofp.ofp_match()
        query_match.wildcards = ofp.OFPFW_ALL
        request.match    = query_match
        request.table_id = 0xff
        request.out_port = ofp.OFPP_NONE;
        if self.controller.message_send(request) == -1:
            return False
        # <TBD>
        # Glue together successive reponse messages for stats reply.
        # Looking at the "more" flag and performing re-assembly
        # should be a part of the infrastructure.
        # </TBD>
        n = 0
        while True:
            (resp, pkt) = self.controller.poll(ofp.OFPT_STATS_REPLY)
            if resp is None:
                return False            # Did not get expected response
            if n == 0:
                self.flow_stats = resp
            else:
                self.flow_stats.stats.extend(resp.stats)
            n = n + 1
            if len(self.flow_stats.stats) > limit:
                logging.error("Too many flows returned")
                return False
            if (resp.flags & 1) == 0:
                break                   # No more responses expected
        return (n > 0)

    def flow_add(self, flow_cfg, overlapf = False):
        flow_mod_msg = message.flow_mod()
        flow_mod_msg.command     = ofp.OFPFC_ADD
        flow_mod_msg.buffer_id   = 0xffffffff
        flow_cfg.to_flow_mod_msg(flow_mod_msg)
        if overlapf:
            flow_mod_msg.flags = flow_mod_msg.flags | ofp.OFPFF_CHECK_OVERLAP
        if flow_cfg.send_rem:
            flow_mod_msg.flags = flow_mod_msg.flags | ofp.OFPFF_SEND_FLOW_REM
        flow_mod_msg.header.xid = random.randrange(1,0xffffffff)
        logging.info("Sending flow_mod(add), xid=%d"
                        % (flow_mod_msg.header.xid)
                        )
        return (self.controller.message_send(flow_mod_msg) != -1)

    def flow_mod(self, flow_cfg, strictf):
        flow_mod_msg = message.flow_mod()
        flow_mod_msg.command     = ofp.OFPFC_MODIFY_STRICT if strictf \
                                   else ofp.OFPFC_MODIFY
        flow_mod_msg.buffer_id   = 0xffffffff
        flow_cfg.to_flow_mod_msg(flow_mod_msg)
        flow_mod_msg.header.xid = random.randrange(1,0xffffffff)
        logging.info("Sending flow_mod(mod), xid=%d"
                        % (flow_mod_msg.header.xid)
                        )
        return (self.controller.message_send(flow_mod_msg) != -1)

    def flow_del(self, flow_cfg, strictf):
        flow_mod_msg = message.flow_mod()
        flow_mod_msg.command     = ofp.OFPFC_DELETE_STRICT if strictf \
                                   else ofp.OFPFC_DELETE
        flow_mod_msg.buffer_id   = 0xffffffff
        # TBD - "out_port" filtering of deletes needs to be tested
        flow_mod_msg.out_port    = ofp.OFPP_NONE
        flow_cfg.to_flow_mod_msg(flow_mod_msg)
        flow_mod_msg.header.xid = random.randrange(1,0xffffffff)
        logging.info("Sending flow_mod(del), xid=%d"
                        % (flow_mod_msg.header.xid)
                        )
        return (self.controller.message_send(flow_mod_msg) != -1)

    def barrier(self):
        barrier = message.barrier_request()
        (resp, pkt) = self.controller.transact(barrier, 30)
        return (resp is not None)

    def errors_verify(self, num_exp, type = 0, code = 0):
        result = True
        logging.info("Expecting %d error messages" % (num_exp))
        num_got = len(self.error_msgs)
        logging.info("Got %d error messages" % (num_got))
        if num_got != num_exp:
            logging.error("Incorrect number of error messages received")
            result = False
        if num_exp == 0:
            return result
        elif num_exp == 1:
            logging.info("Expecting error message, type=%d, code=%d" \
                            % (type, code) \
                            )
            f = False
            for e in self.error_msgs:
                if e.type == type and e.code == code:
                    logging.info("Got it")
                    f = True
            if not f:
                logging.error("Did not get it")
                result = False
        else:
            logging.error("Can't expect more than 1 error message type")
            result = False
        return result

    def removed_verify(self, num_exp):
        result = True
        logging.info("Expecting %d removed messages" % (num_exp))
        num_got = len(self.removed_msgs)
        logging.info("Got %d removed messages" % (num_got))
        if num_got != num_exp:
            logging.error("Incorrect number of removed messages received")
            result = False
        if num_exp < 2:
            return result
        logging.error("Can't expect more than 1 error message type")
        return False

    # modf == True <=> Verify for flow modify, else for add/delete
    def flow_tbl_verify(self, modf = False):
        result = True
    
        # Verify flow count in switch
        logging.info("Reading table stats")
        logging.info("Expecting %d flows" % (self.flow_tbl.count()))
        if not self.tbl_stats_get():
            logging.error("Get table stats failed")
            return False
        n = 0
        for ts in self.tbl_stats.stats:
            n = n + ts.active_count
        logging.info("Table stats reported %d active flows" \
                          % (n) \
                          )
        if n != self.flow_tbl.count():
            logging.error("Incorrect number of active flows reported")
            result = False
    
        # Read flows from switch
        logging.info("Retrieving flows from switch")
        logging.info("Expecting %d flows" % (self.flow_tbl.count()))
        if not self.flow_stats_get():
            logging.error("Get flow stats failed")
            return False
        logging.info("Retrieved %d flows" % (len(self.flow_stats.stats)))
    
        # Verify flows returned by switch
    
        if len(self.flow_stats.stats) != self.flow_tbl.count():
            logging.error("Switch reported incorrect number of flows")
            result = False
    
        logging.info("Verifying received flows")
        for fc in self.flow_tbl.values():
            fc.matched = False
        for fs in self.flow_stats.stats:
            flow_in = Flow_Cfg()
            flow_in.from_flow_stat(fs)
            logging.info("Received flow:")
            logging.info(str(flow_in))
            fc = self.flow_tbl.find(flow_in)
            if fc is None:
                logging.error("Received flow:")
                logging.error(str(flow_in))
                logging.error("does not match any defined flow")
                result = False
            elif fc.matched:
                logging.error("Received flow:")
                logging.error(str(flow_in))
                logging.error("re-matches defined flow:")
                logging.info(str(fc))
                result = False
            else:
                logging.info("matched")
                if modf:
                    # Check for modify
                    
                    if flow_in.cookie != fc.cookie:
                        logging.warning("Defined flow:")
                        logging.warning(str(fc))
                        logging.warning("Received flow:")
                        logging.warning(str(flow_in))
                        logging.warning("cookies do not match")
                    if not flow_in.actions_equal(fc):
                        logging.error("Defined flow:")
                        logging.error(str(fc))
                        logging.error("Received flow:")
                        logging.error(str(flow_in))
                        logging.error("actions do not match")
                else:
                    # Check for add/delete
                    
                    if not flow_in == fc:
                        logging.error("Defined flow:")
                        logging.error(str(fc))
                        logging.error("Received flow:")
                        logging.error(str(flow_in))
                        logging.error("non-key portions of flow do not match")
                        result = False
                fc.matched = True
        for fc in self.flow_tbl.values():
            if not fc.matched:
                logging.error("Defined flow:")
                logging.error(str(fc))
                logging.error("was not returned by switch")
                result = False
    
        return result

    def settle(self):
        time.sleep(2)

# FLOW ADD 5
#
# OVERVIEW
# Add flows to switch, read back and verify flow configurations
#
# PURPOSE
# - Test acceptance of flow adds
# - Test ability of switch to process additions to flow table in random
#   priority order
# - Test correctness of flow configuration responses
#
# PARAMETERS
#
# Name: num_flows
# Type: number
# Description:
# Number of flows to define; 0 => maximum number of flows, as determined
# from switch capabilities
# Default: 100
#
# PROCESS
# 1. Delete all flows from switch
# 2. Generate <num_flows> distinct flow configurations
# 3. Send <num_flows> flow adds to switch, for flows generated in step 2 above
# 4. Verify that no OFPT_ERROR responses were generated by switch
# 5. Retrieve flow stats from switch
# 6. Compare flow configurations returned by switch
# 7. Test PASSED iff all flows sent to switch in step 3 above are returned
#    in step 5 above; else test FAILED

class Flow_Add_5(basic.SimpleProtocol):
    """
    Test FLOW_ADD_5 from draft top-half test plan
    
    INPUTS
    num_flows - Number of flows to generate
    """

    def runTest(self):
        logging.info("Flow_Add_5 TEST BEGIN")

        num_flows = test_param_get(fq_config, "num_flows", 100)

        # Clear all flows from switch

        logging.info("Deleting all flows from switch")
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # Get switch capabilites

        sw = Switch()
        self.assertTrue(sw.connect(self.controller), \
                        "Failed to connect to switch" \
                        )

        if num_flows == 0:
            # Number of flows requested was 0
            # => Generate max number of flows

            for ts in sw.tbl_stats.stats:
                num_flows = num_flows + ts.max_entries

        logging.info("Generating %d flows" % (num_flows))        

        # Dream up some flow information, i.e. space to chose from for
        # random flow parameter generation

        fi = Flow_Info()
        fi.rand(max(2 * int(math.log(num_flows)), 1))

        # Create a flow table

        ft = Flow_Tbl()
        ft.rand(required_wildcards(self), sw, fi, num_flows)

        # Send flow table to switch

        logging.info("Sending flow adds to switch")
        for fc in ft.values():          # Randomizes order of sending
            logging.info("Adding flow:")
            logging.info(str(fc));
            self.assertTrue(sw.flow_add(fc), "Failed to add flow")

        # Do barrier, to make sure all flows are in

        self.assertTrue(sw.barrier(), "Barrier failed")

        result = True

        sw.settle()  # Allow switch to settle and generate any notifications
        
        # Check for any error messages

        if not sw.errors_verify(0):
            result = False

        # Verify flow table

        sw.flow_tbl = ft
        if not sw.flow_tbl_verify():
            result = False

        self.assertTrue(result, "Flow_Add_5 TEST FAILED")
        logging.info("Flow_Add_5 TEST PASSED")


# FLOW ADD 5_1
#
# OVERVIEW
# Verify handling of non-canonical flows
#
# PURPOSE
# - Test that switch detects and correctly responds to a non-canonical flow
#   definition.  A canonical flow is one that satisfies all match qualifier
#   dependencies; a non-canonical flow is one that does not.
#
# PARAMETERS
# - None
#
# PROCESS
# 1. Delete all flows from switch
# 2. Generate 1 flow definition, which is different from its canonicalization
# 3. Send flow to switch
# 4. Retrieve flow from switch
# 5. Compare returned flow to canonical form of defined flow
# 7. Test PASSED iff flow received in step 4 above is identical to canonical form of flow defined in step 3 above

# Disabled.
# Should be DUT dependent.

class Flow_Add_5_1(basic.SimpleProtocol):
    """
    Test FLOW_ADD_5.1 from draft top-half test plan

    INPUTS
    None
    """

    priority = -1
    
    def runTest(self):
        logging.info("Flow_Add_5_1 TEST BEGIN")

        num_flows = test_param_get(fq_config, "num_flows", 100)
        
        # Clear all flows from switch

        logging.info("Deleting all flows from switch")
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # Get switch capabilites

        sw = Switch()
        self.assertTrue(sw.connect(self.controller), \
                        "Failed to connect to switch" \
                        )

        # Dream up some flow information, i.e. space to chose from for
        # random flow parameter generation

        fi = Flow_Info()
        fi.rand(10)
        
        # Dream up a flow config that will be canonicalized by the switch

        while True:
            fc = Flow_Cfg()
            fc.rand(fi, \
                    required_wildcards(self), \
                    sw.tbl_stats.stats[0].wildcards, \
                    sw.sw_features.actions, \
                    sw.valid_ports, \
                    sw.valid_queues \
                    )
            fcc = fc.canonical()
            if fcc.match != fc.match:
                break

        ft = Flow_Tbl()
        ft.insert(fcc)

        # Send it to the switch

        logging.info("Sending flow add to switch:")
        logging.info(str(fc))
        logging.info("should be canonicalized as:")
        logging.info(str(fcc))
        fc.send_rem = False
        self.assertTrue(sw.flow_add(fc), "Failed to add flow")

        # Do barrier, to make sure all flows are in

        self.assertTrue(sw.barrier(), "Barrier failed")

        result = True

        sw.settle()  # Allow switch to settle and generate any notifications

        # Check for any error messages

        if not sw.errors_verify(0):
            result = False

        # Verify flow table

        sw.flow_tbl = ft
        if not sw.flow_tbl_verify():
            result = False

        self.assertTrue(result, "Flow_Add_5_1 TEST FAILED")
        logging.info("Flow_Add_5_1 TEST PASSED")


# FLOW ADD 6
#
# OVERVIEW
# Test flow table capacity
#
# PURPOSE
# - Test switch can accept as many flow definitions as it claims
# - Test generation of OFPET_FLOW_MOD_FAILED/OFPFMFC_ALL_TABLES_FULL
# - Test that attempting to create flows beyond capacity does not corrupt
#   flow table
#
# PARAMETERS
# None
#
# PROCESS
# 1. Delete all flows from switch
# 2. Send OFPT_FEATURES_REQUEST and OFPT_STATS_REQUEST/OFPST_TABLE enquiries
#    to determine flow table size, N
# 3. Generate (N + 1) distinct flow configurations
# 4. Send N flow adds to switch, for flows generated in step 3 above
# 5. Verify flow table in switch
# 6. Send one more flow add to switch
# 7. Verify that OFPET_FLOW_MOD_FAILED/OFPFMFC_ALL_TABLES_FULL error
#    response was generated by switch, for last flow mod sent
# 7. Retrieve flow stats from switch
# 8. Verify flow table in switch
# 9. Test PASSED iff:
#    - error message received, for correct flow
#    - last flow definition sent to switch is not in flow table
#    else test FAILED

# Disabled because of bogus capacity reported by OVS.
# Should be DUT dependent.

class Flow_Add_6(basic.SimpleProtocol):
    """
    Test FLOW_ADD_6 from draft top-half test plan
    
    INPUTS
    num_flows - Number of flows to generate
    """

    priority = -1

    def runTest(self):
        logging.info("Flow_Add_6 TEST BEGIN")

        # Clear all flows from switch

        logging.info("Deleting all flows from switch")
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # Get switch capabilites

        sw = Switch()
        self.assertTrue(sw.connect(self.controller), \
                        "Failed to connect to switch" \
                        )

        num_flows = 0
        for ts in sw.tbl_stats.stats:
            num_flows = num_flows + ts.max_entries

        logging.info("Switch capacity is %d flows" % (num_flows))        
        logging.info("Generating %d flows" % (num_flows))        

        # Dream up some flow information, i.e. space to chose from for
        # random flow parameter generation

        fi = Flow_Info()
        fi.rand(max(2 * int(math.log(num_flows)), 1))

        # Create a flow table, to switch's capacity

        ft = Flow_Tbl()
        ft.rand(required_wildcards(self), sw, fi, num_flows)

        # Send flow table to switch

        logging.info("Sending flow adds to switch")
        for fc in ft.values():          # Randomizes order of sending
            logging.info("Adding flow:")
            logging.info(str(fc));
            self.assertTrue(sw.flow_add(fc), "Failed to add flow")

        # Do barrier, to make sure all flows are in

        self.assertTrue(sw.barrier(), "Barrier failed")

        result = True

        sw.settle()  # Allow switch to settle and generate any notifications

        # Check for any error messages

        if not sw.errors_verify(0):
            result = False

        # Dream up one more flow

        logging.info("Creating one more flow")
        while True:
            fc = Flow_Cfg()
            fc.rand(fi, \
                    required_wildcards(self), \
                    sw.tbl_stats.stats[0].wildcards, \
                    sw.sw_features.actions, \
                    sw.valid_ports, \
                    sw.valid_queues \
                    )
            fc = fc.canonical()
            if not ft.find(fc):
                break

        # Send one-more flow

        fc.send_rem = False
        logging.info("Sending flow add switch")
        logging.info(str(fc));
        self.assertTrue(sw.flow_add(fc), "Failed to add flow")

        # Do barrier, to make sure all flows are in

        self.assertTrue(sw.barrier(), "Barrier failed")

        sw.settle()  # Allow switch to settle and generate any notifications

        # Check for expected error message

        if not sw.errors_verify(1, \
                                ofp.OFPET_FLOW_MOD_FAILED, \
                                ofp.OFPFMFC_ALL_TABLES_FULL \
                                ):
            result = False

        # Verify flow table

        sw.flow_tbl = ft
        if not sw.flow_tbl_verify():
            result = False

        self.assertTrue(result, "Flow_add_6 TEST FAILED")
        logging.info("Flow_add_6 TEST PASSED")


# FLOW ADD 7
#
# OVERVIEW
# Test flow redefinition
#
# PURPOSE
# Verify that successive flow adds with same priority and match criteria
# overwrite in flow table
#
# PARAMETERS
# None
#
# PROCESS
# 1. Delete all flows from switch
# 2. Generate flow definition F1
# 3. Generate flow definition F2, with same key (priority and match) as F1,
#    but with different actions
# 4. Send flow adds for F1 and F2 to switch
# 5. Verify flow definitions in switch
# 6. Test PASSED iff 1 flow returned by switch, matching configuration of F2;
#    else test FAILED

class Flow_Add_7(basic.SimpleProtocol):
    """
    Test FLOW_ADD_7 from draft top-half test plan
    
    INPUTS
    None
    """

    def runTest(self):
        logging.info("Flow_Add_7 TEST BEGIN")

        # Clear all flows from switch

        logging.info("Deleting all flows from switch")
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # Get switch capabilites

        sw = Switch()
        self.assertTrue(sw.connect(self.controller), \
                        "Failed to connect to switch" \
                        )

        # Dream up some flow information, i.e. space to chose from for
        # random flow parameter generation

        fi = Flow_Info()
        fi.rand(10)
        
        # Dream up a flow config

        fc = Flow_Cfg()
        fc.rand(fi, \
                required_wildcards(self), \
                sw.tbl_stats.stats[0].wildcards, \
                sw.sw_features.actions, \
                sw.valid_ports, \
                sw.valid_queues \
                )
        fc = fc.canonical()

        # Send it to the switch

        logging.info("Sending flow add to switch:")
        logging.info(str(fc))
        ft = Flow_Tbl()
        fc.send_rem = False
        self.assertTrue(sw.flow_add(fc), "Failed to add flow")
        ft.insert(fc)

        # Dream up some different actions, with the same flow key

        fc2 = copy.deepcopy(fc)
        while True:
            fc2.rand_mod(fi, \
                         sw.sw_features.actions, \
                         sw.valid_ports, \
                         sw.valid_queues \
                         )
            if fc2 != fc:
                break

        # Send that to the switch
        
        logging.info("Sending flow add to switch:")
        logging.info(str(fc2))
        fc2.send_rem = False
        self.assertTrue(sw.flow_add(fc2), "Failed to add flow")
        ft.insert(fc2)

        # Do barrier, to make sure all flows are in

        self.assertTrue(sw.barrier(), "Barrier failed")

        result = True

        sw.settle()  # Allow switch to settle and generate any notifications

        # Check for any error messages

        if not sw.errors_verify(0):
            result = False

        # Verify flow table

        sw.flow_tbl = ft
        if not sw.flow_tbl_verify():
            result = False

        self.assertTrue(result, "Flow_Add_7 TEST FAILED")
        logging.info("Flow_Add_7 TEST PASSED")


# FLOW ADD 8
#
# OVERVIEW
# Add overlapping flows to switch, verify that overlapping flows are rejected
#
# PURPOSE
# - Test detection of overlapping flows by switch
# - Test generation of OFPET_FLOW_MOD_FAILED/OFPFMFC_OVERLAP messages
# - Test rejection of overlapping flows
# - Test defining overlapping flows does not corrupt flow table
#
# PARAMETERS
# None
#
# PROCESS
# 1. Delete all flows from switch
# 2. Generate flow definition F1
# 3. Generate flow definition F2, with key overlapping F1
# 4. Send flow add to switch, for F1
# 5. Send flow add to switch, for F2, with OFPFF_CHECK_OVERLAP set
# 6. Verify that OFPET_FLOW_MOD_FAILED/OFPFMFC_OVERLAP error response
#    was generated by switch
# 7. Verifiy flows configured in swtich
# 8. Test PASSED iff:
#    - error message received, for overlapping flow
#    - overlapping flow is not in flow table
#    else test FAILED

class Flow_Add_8(basic.SimpleProtocol):
    """
    Test FLOW_ADD_8 from draft top-half test plan
    
    INPUTS
    None
    """

    def runTest(self):
        logging.info("Flow_Add_8 TEST BEGIN")

        # Clear all flows from switch

        logging.info("Deleting all flows from switch")
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # Get switch capabilites

        sw = Switch()
        self.assertTrue(sw.connect(self.controller), \
                        "Failed to connect to switch" \
                        )

        # Dream up some flow information, i.e. space to chose from for
        # random flow parameter generation

        fi = Flow_Info()
        fi.rand(10)
        
        # Dream up a flow config, with at least 1 qualifier specified

        fc = Flow_Cfg()
        while True:
            fc.rand(fi, \
                    required_wildcards(self), \
                    sw.tbl_stats.stats[0].wildcards, \
                    sw.sw_features.actions, \
                    sw.valid_ports, \
                    sw.valid_queues \
                    )
            fc = fc.canonical()
            if fc.match.wildcards != ofp.OFPFW_ALL:
                break

        # Send it to the switch

        logging.info("Sending flow add to switch:")
        logging.info(str(fc))
        ft = Flow_Tbl()
        fc.send_rem = False
        self.assertTrue(sw.flow_add(fc), "Failed to add flow")
        ft.insert(fc)

        # Wildcard out one qualifier that was specified, to create an
        # overlapping flow

        fc2 = copy.deepcopy(fc)
        for wi in shuffle(range(len(all_wildcards_list))):
            w = all_wildcards_list[wi]
            if (fc2.match.wildcards & w) == 0:
                break
        if w == ofp.OFPFW_NW_SRC_MASK:
            w  = ofp.OFPFW_NW_SRC_ALL
            wn = "OFPFW_NW_SRC"
        elif w == ofp.OFPFW_NW_DST_MASK:
            w  = ofp.OFPFW_NW_DST_ALL
            wn = "OFPFW_NW_DST"
        else:
            wn = all_wildcard_names[w]
        logging.info("Wildcarding out %s" % (wn))
        fc2.match.wildcards = fc2.match.wildcards | w
        fc2 = fc2.canonical()

        # Send that to the switch, with overlap checking
        
        logging.info("Sending flow add to switch:")
        logging.info(str(fc2))
        fc2.send_rem = False
        self.assertTrue(sw.flow_add(fc2, True), "Failed to add flow")

        # Do barrier, to make sure all flows are in
        self.assertTrue(sw.barrier(), "Barrier failed")

        result = True

        sw.settle()  # Allow switch to settle and generate any notifications

        # Check for expected error message

        if not sw.errors_verify(1, \
                                ofp.OFPET_FLOW_MOD_FAILED, \
                                ofp.OFPFMFC_OVERLAP \
                                ):
            result = False

        # Verify flow table

        sw.flow_tbl = ft
        if not sw.flow_tbl_verify():
            result = False

        self.assertTrue(result, "Flow_Add_8 TEST FAILED")
        logging.info("Flow_Add_8 TEST PASSED")


# FLOW MODIFY 1
#
# OVERVIEW
# Strict modify of single existing flow
#
# PURPOSE
# - Verify that strict flow modify operates only on specified flow
# - Verify that flow is correctly modified
#
# PARAMETERS
# None
#
# PROCESS
# 1. Delete all flows from switch
# 2. Generate 1 flow F
# 3. Send flow add to switch, for flow F
# 4. Generate new action list for flow F, yielding F'
# 5. Send strict flow modify to switch, for flow F'
# 6. Verify flow table in switch
# 7. Test PASSED iff flow returned by switch is F'; else FAILED

class Flow_Mod_1(basic.SimpleProtocol):
    """
    Test FLOW_MOD_1 from draft top-half test plan
    
    INPUTS
    None
    """

    def runTest(self):
        logging.info("Flow_Mod_1 TEST BEGIN")

        # Clear all flows from switch

        logging.info("Deleting all flows from switch")
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # Get switch capabilites

        sw = Switch()
        self.assertTrue(sw.connect(self.controller), \
                        "Failed to connect to switch" \
                        )

        # Dream up some flow information, i.e. space to chose from for
        # random flow parameter generation

        fi = Flow_Info()
        fi.rand(10)
        
        # Dream up a flow config

        fc = Flow_Cfg()
        fc.rand(fi, \
                required_wildcards(self), \
                sw.tbl_stats.stats[0].wildcards, \
                sw.sw_features.actions, \
                sw.valid_ports, \
                sw.valid_queues \
                )
        fc = fc.canonical()

        # Send it to the switch

        logging.info("Sending flow add to switch:")
        logging.info(str(fc))
        ft = Flow_Tbl()
        fc.send_rem = False
        self.assertTrue(sw.flow_add(fc), "Failed to add flow")
        ft.insert(fc)

        # Dream up some different actions, with the same flow key

        fc2 = copy.deepcopy(fc)
        while True:
            fc2.rand_mod(fi, \
                         sw.sw_features.actions, \
                         sw.valid_ports, \
                         sw.valid_queues \
                         )
            if fc2 != fc:
                break

        # Send that to the switch
        
        logging.info("Sending strict flow mod to switch:")
        logging.info(str(fc2))
        fc2.send_rem = False
        self.assertTrue(sw.flow_mod(fc2, True), "Failed to modify flow")
        ft.insert(fc2)

        # Do barrier, to make sure all flows are in

        self.assertTrue(sw.barrier(), "Barrier failed")

        result = True

        sw.settle()  # Allow switch to settle and generate any notifications

        # Check for any error messages

        if not sw.errors_verify(0):
            result = False

        # Verify flow table

        sw.flow_tbl = ft
        if not sw.flow_tbl_verify(True):
            result = False

        self.assertTrue(result, "Flow_Mod_1 TEST FAILED")
        logging.info("Flow_Mod_1 TEST PASSED")


# FLOW MODIFY 2
#
# OVERVIEW
# Loose modify of mutiple flows
#
# PURPOSE
# - Verify that loose flow modify operates only on matching flows
# - Verify that matching flows are correctly modified
#
# PARAMETERS
# Name: num_flows
# Type: number
# Description:
# Number of flows to define
# Default: 100
#
# PROCESS
# 1. Delete all flows from switch
# 2. Generate <num_flows> distinct flow configurations
# 3. Send <num_flows> flow adds to switch
# 4. Pick 1 defined flow F at random
# 5. Create overlapping loose flow mod match criteria by repeatedly
#    wildcarding out qualifiers in match of F => F',
#    and create new actions list A' for F'
# 6. Send loose flow modify for F' to switch
# 7. Verify flow table in swtich
# 8. Test PASSED iff all flows sent to switch in steps 3 and 6 above,
#    are returned in step 7 above, each with correct (original or modified)
#    action list;
#    else test FAILED
        
class Flow_Mod_2(basic.SimpleProtocol):
    """
    Test FLOW_MOD_2 from draft top-half test plan
    
    INPUTS
    None
    """

    def runTest(self):
        logging.info("Flow_Mod_2 TEST BEGIN")

        num_flows = test_param_get(fq_config, "num_flows", 100)

        # Clear all flows from switch

        logging.info("Deleting all flows from switch")
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # Get switch capabilites

        sw = Switch()
        self.assertTrue(sw.connect(self.controller), \
                        "Failed to connect to switch" \
                        )

        # Dream up some flow information, i.e. space to chose from for
        # random flow parameter generation

        fi = Flow_Info()
        # Shrunk, to increase chance of meta-matches
        fi.rand(max(int(math.log(num_flows)) / 2, 1))
        
        # Dream up some flows

        ft = Flow_Tbl()
        ft.rand(required_wildcards(self), sw, fi, num_flows)

        # Send flow table to switch

        logging.info("Sending flow adds to switch")
        for fc in ft.values():          # Randomizes order of sending
            logging.info("Adding flow:")
            logging.info(str(fc));
            self.assertTrue(sw.flow_add(fc), "Failed to add flow")

        # Do barrier, to make sure all flows are in

        self.assertTrue(sw.barrier(), "Barrier failed")

        result = True

        sw.settle()  # Allow switch to settle and generate any notifications

        # Check for any error messages

        if not sw.errors_verify(0):
            result = False

        # Verify flow table

        sw.flow_tbl = ft
        if not sw.flow_tbl_verify():
            result = False

        # Pick a random flow as a basis

        mfc = copy.deepcopy((ft.values())[0])
        mfc.rand_mod(fi, \
                     sw.sw_features.actions, \
                     sw.valid_ports, \
                     sw.valid_queues \
                     )

        # Repeatedly wildcard qualifiers

        for wi in shuffle(range(len(all_wildcards_list))):
            w = all_wildcards_list[wi]
            if w == ofp.OFPFW_NW_SRC_MASK or w == ofp.OFPFW_NW_DST_MASK:
                n = wildcard_get(mfc.match.wildcards, w)
                if n < 32:
                    mfc.match.wildcards = wildcard_set(mfc.match.wildcards, \
                                                       w, \
                                                       random.randint(n + 1, 32) \
                                                       )
                else:
                    continue
            else:
                if wildcard_get(mfc.match.wildcards, w) == 0:
                    mfc.match.wildcards = wildcard_set(mfc.match.wildcards, w, 1)
                else:
                    continue
            mfc = mfc.canonical()

            # Count the number of flows that would be modified

            n = 0
            for fc in ft.values():
                if mfc.overlaps(fc, True) and not mfc.non_key_equal(fc):
                    n = n + 1

            # If more than 1, we found our loose delete flow spec
            if n > 1:
                break
                    
        logging.info("Modifying %d flows" % (n))
        logging.info("Sending flow mod to switch:")
        logging.info(str(mfc))
        self.assertTrue(sw.flow_mod(mfc, False), "Failed to modify flow")

        # Do barrier, to make sure all flows are in
        self.assertTrue(sw.barrier(), "Barrier failed")

        sw.settle()  # Allow switch to settle and generate any notifications

        # Check for error message

        if not sw.errors_verify(0):
            result = False

        # Apply flow mod to local flow table

        for fc in ft.values():
            if mfc.overlaps(fc, True):
                fc.actions = mfc.actions

        # Verify flow table

        sw.flow_tbl = ft
        if not sw.flow_tbl_verify(True):
            result = False

        self.assertTrue(result, "Flow_Mod_2 TEST FAILED")
        logging.info("Flow_Mod_2 TEST PASSED")


# FLOW MODIFY 3

# OVERVIEW
# Strict modify of non-existent flow
#
# PURPOSE
# Verify that strict modify of a non-existent flow is equivalent to a flow add
#
# PARAMETERS
# None
#
# PROCESS
# 1. Delete all flows from switch
# 2. Send single flow mod, as strict modify, to switch
# 3. Verify flow table in switch
# 4. Test PASSED iff flow defined in step 2 above verified; else FAILED

class Flow_Mod_3(basic.SimpleProtocol):
    """
    Test FLOW_MOD_3 from draft top-half test plan
    
    INPUTS
    None
    """

    def runTest(self):
        logging.info("Flow_Mod_3 TEST BEGIN")

        # Clear all flows from switch

        logging.info("Deleting all flows from switch")
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # Get switch capabilites

        sw = Switch()
        self.assertTrue(sw.connect(self.controller), \
                        "Failed to connect to switch" \
                        )

        # Dream up some flow information, i.e. space to chose from for
        # random flow parameter generation

        fi = Flow_Info()
        fi.rand(10)
        
        # Dream up a flow config

        fc = Flow_Cfg()
        fc.rand(fi, \
                required_wildcards(self), \
                sw.tbl_stats.stats[0].wildcards, \
                sw.sw_features.actions, \
                sw.valid_ports, \
                sw.valid_queues \
                )
        fc = fc.canonical()

        # Send it to the switch

        logging.info("Sending flow mod to switch:")
        logging.info(str(fc))
        ft = Flow_Tbl()
        fc.send_rem = False
        self.assertTrue(sw.flow_mod(fc, True), "Failed to modify flows")
        ft.insert(fc)

        # Do barrier, to make sure all flows are in

        self.assertTrue(sw.barrier(), "Barrier failed")

        result = True

        sw.settle()  # Allow switch to settle and generate any notifications

        # Check for any error messages

        if not sw.errors_verify(0):
            result = False

        # Verify flow table

        sw.flow_tbl = ft
        if not sw.flow_tbl_verify():
            result = False

        self.assertTrue(result, "Flow_Mod_3 TEST FAILED")
        logging.info("Flow_Mod_3 TEST PASSED")


# FLOW MODIFY 3_1

# OVERVIEW
# No-op modify
#
# PURPOSE
# Verify that modify of a flow with new actions same as old ones operates correctly
#
# PARAMETERS
# None
#
# PROCESS
# 1. Delete all flows from switch
# 2. Send single flow mod, as strict modify, to switch
# 3. Verify flow table in switch
# 4. Send same flow mod, as strict modify, to switch
# 5. Verify flow table in switch
# 6. Test PASSED iff flow defined in step 2 and 4 above verified; else FAILED

class Flow_Mod_3_1(basic.SimpleProtocol):
    """
    Test FLOW_MOD_3_1 from draft top-half test plan
    
    INPUTS
    None
    """

    def runTest(self):
        logging.info("Flow_Mod_3_1 TEST BEGIN")

        # Clear all flows from switch

        logging.info("Deleting all flows from switch")
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # Get switch capabilites

        sw = Switch()
        self.assertTrue(sw.connect(self.controller), \
                        "Failed to connect to switch" \
                        )

        # Dream up some flow information, i.e. space to chose from for
        # random flow parameter generation

        fi = Flow_Info()
        fi.rand(10)
        
        # Dream up a flow config

        fc = Flow_Cfg()
        fc.rand(fi, \
                required_wildcards(self), \
                sw.tbl_stats.stats[0].wildcards, \
                sw.sw_features.actions, \
                sw.valid_ports, \
                sw.valid_queues \
                )
        fc = fc.canonical()

        # Send it to the switch

        logging.info("Sending flow mod to switch:")
        logging.info(str(fc))
        ft = Flow_Tbl()
        fc.send_rem = False
        self.assertTrue(sw.flow_mod(fc, True), "Failed to modify flows")
        ft.insert(fc)

        # Do barrier, to make sure all flows are in

        self.assertTrue(sw.barrier(), "Barrier failed")

        result = True

        sw.settle()  # Allow switch to settle and generate any notifications

        # Check for any error messages

        if not sw.errors_verify(0):
            result = False

        # Verify flow table

        sw.flow_tbl = ft
        if not sw.flow_tbl_verify():
            result = False

        # Send same flow to the switch again

        logging.info("Sending flow mod to switch:")
        logging.info(str(fc))
        self.assertTrue(sw.flow_mod(fc, True), "Failed to modify flows")

        # Do barrier, to make sure all flows are in

        self.assertTrue(sw.barrier(), "Barrier failed")

        sw.settle()  # Allow switch to settle and generate any notifications

        # Check for any error messages

        if not sw.errors_verify(0):
            result = False

        # Verify flow table

        if not sw.flow_tbl_verify():
            result = False

        self.assertTrue(result, "Flow_Mod_3_1 TEST FAILED")
        logging.info("Flow_Mod_3_1 TEST PASSED")


# FLOW DELETE 1
#
# OVERVIEW
# Strict delete of single flow
#
# PURPOSE
# Verify correct operation of strict delete of single defined flow
#
# PARAMETERS
# None
#
# PROCESS
# 1. Delete all flows from switch
# 2. Send flow F to switch
# 3. Send strict flow delete for F to switch
# 4. Verify flow table in swtich
# 6. Test PASSED iff all flows sent to switch in step 2 above,
#    less flow removed in step 3 above, are returned in step 4 above;
#    else test FAILED

class Flow_Del_1(basic.SimpleProtocol):
    """
    Test FLOW_DEL_1 from draft top-half test plan
    
    INPUTS
    None
    """

    def runTest(self):
        logging.info("Flow_Del_1 TEST BEGIN")

        # Clear all flows from switch

        logging.info("Deleting all flows from switch")
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # Get switch capabilites

        sw = Switch()
        self.assertTrue(sw.connect(self.controller), \
                        "Failed to connect to switch" \
                        )

        # Dream up some flow information, i.e. space to chose from for
        # random flow parameter generation

        fi = Flow_Info()
        fi.rand(10)
        
        # Dream up a flow config

        fc = Flow_Cfg()
        fc.rand(fi, \
                required_wildcards(self), \
                sw.tbl_stats.stats[0].wildcards, \
                sw.sw_features.actions, \
                sw.valid_ports, \
                sw.valid_queues \
                )
        fc = fc.canonical()

        # Send it to the switch

        logging.info("Sending flow add to switch:")
        logging.info(str(fc))
        ft = Flow_Tbl()
        fc.send_rem = False
        self.assertTrue(sw.flow_add(fc), "Failed to add flow")
        ft.insert(fc)

        # Dream up some different actions, with the same flow key

        fc2 = copy.deepcopy(fc)
        while True:
            fc2.rand_mod(fi, \
                         sw.sw_features.actions, \
                         sw.valid_ports, \
                         sw.valid_queues \
                         )
            if fc2 != fc:
                break

        # Delete strictly
        
        logging.info("Sending strict flow del to switch:")
        logging.info(str(fc2))
        self.assertTrue(sw.flow_del(fc2, True), "Failed to delete flow")
        ft.delete(fc)

        # Do barrier, to make sure all flows are in

        self.assertTrue(sw.barrier(), "Barrier failed")

        result = True

        sw.settle()  # Allow switch to settle and generate any notifications

        # Check for any error messages

        if not sw.errors_verify(0):
            result = False

        # Verify flow table

        sw.flow_tbl = ft
        if not sw.flow_tbl_verify():
            result = False

        self.assertTrue(result, "Flow_Del_1 TEST FAILED")
        logging.info("Flow_Del_1 TEST PASSED")


# FLOW DELETE 2
#
# OVERVIEW
# Loose delete of multiple flows
#
# PURPOSE
# - Verify correct operation of loose delete of multiple flows
#
# PARAMETERS
# Name: num_flows
# Type: number
# Description:
# Number of flows to define
# Default: 100
#
# PROCESS
# 1. Delete all flows from switch
# 2. Generate <num_flows> distinct flow configurations
# 3. Send <num_flows> flow adds to switch, for flows generated in step 2 above
# 4. Pick 1 defined flow F at random
# 5. Repeatedly wildcard out qualifiers in match of F, creating F', such that
#    F' will match more than 1 existing flow key
# 6. Send loose flow delete for F' to switch
# 7. Verify flow table in switch
# 8. Test PASSED iff all flows sent to switch in step 3 above, less flows
#    removed in step 6 above (i.e. those that match F'), are returned
#    in step 7 above;
#    else test FAILED

class Flow_Del_2(basic.SimpleProtocol):
    """
    Test FLOW_DEL_2 from draft top-half test plan
    
    INPUTS
    None
    """

    def runTest(self):
        logging.info("Flow_Del_2 TEST BEGIN")

        num_flows = test_param_get(fq_config, "num_flows", 100)

        # Clear all flows from switch

        logging.info("Deleting all flows from switch")
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # Get switch capabilites

        sw = Switch()
        self.assertTrue(sw.connect(self.controller), \
                        "Failed to connect to switch" \
                        )

        # Dream up some flow information, i.e. space to chose from for
        # random flow parameter generation

        fi = Flow_Info()
        # Shrunk, to increase chance of meta-matches
        fi.rand(max(int(math.log(num_flows)) / 2, 1))
        
        # Dream up some flows

        ft = Flow_Tbl()
        ft.rand(required_wildcards(self), sw, fi, num_flows)

        # Send flow table to switch

        logging.info("Sending flow adds to switch")
        for fc in ft.values():          # Randomizes order of sending
            logging.info("Adding flow:")
            logging.info(str(fc));
            self.assertTrue(sw.flow_add(fc), "Failed to add flow")

        # Do barrier, to make sure all flows are in

        self.assertTrue(sw.barrier(), "Barrier failed")

        result = True

        sw.settle()  # Allow switch to settle and generate any notifications

        # Check for any error messages

        if not sw.errors_verify(0):
            result = False

        # Verify flow table

        sw.flow_tbl = ft
        if not sw.flow_tbl_verify():
            result = False

        # Pick a random flow as a basis
        
        dfc = copy.deepcopy(ft.values()[0])
        dfc.rand_mod(fi, \
                     sw.sw_features.actions, \
                     sw.valid_ports, \
                     sw.valid_queues \
                     )

        # Repeatedly wildcard qualifiers

        for wi in shuffle(range(len(all_wildcards_list))):
            w = all_wildcards_list[wi]
            if w == ofp.OFPFW_NW_SRC_MASK or w == ofp.OFPFW_NW_DST_MASK:
                n = wildcard_get(dfc.match.wildcards, w)
                if n < 32:
                    dfc.match.wildcards = wildcard_set(dfc.match.wildcards, \
                                                       w, \
                                                       random.randint(n + 1, 32) \
                                                       )
                else:
                    continue
            else:
                if wildcard_get(dfc.match.wildcards, w) == 0:
                    dfc.match.wildcards = wildcard_set(dfc.match.wildcards, w, 1)
                else:
                    continue
            dfc = dfc.canonical()

            # Count the number of flows that would be deleted

            n = 0
            for fc in ft.values():
                if dfc.overlaps(fc, True):
                    n = n + 1

            # If more than 1, we found our loose delete flow spec
            if n > 1:
                break
                    
        logging.info("Deleting %d flows" % (n))
        logging.info("Sending flow del to switch:")
        logging.info(str(dfc))
        self.assertTrue(sw.flow_del(dfc, False), "Failed to delete flows")

        # Do barrier, to make sure all flows are in
        self.assertTrue(sw.barrier(), "Barrier failed")

        sw.settle()  # Allow switch to settle and generate any notifications

        # Check for error message

        if not sw.errors_verify(0):
            result = False

        # Apply flow mod to local flow table

        for fc in ft.values():
            if dfc.overlaps(fc, True):
                ft.delete(fc)

        # Verify flow table

        sw.flow_tbl = ft
        if not sw.flow_tbl_verify():
            result = False

        self.assertTrue(result, "Flow_Del_2 TEST FAILED")
        logging.info("Flow_Del_2 TEST PASSED")


# FLOW DELETE 4
#
# OVERVIEW
# Flow removed messages
#
# PURPOSE
# Verify that switch generates OFPT_FLOW_REMOVED/OFPRR_DELETE response
# messages when deleting flows that were added with OFPFF_SEND_FLOW_REM flag
#
# PARAMETERS
# None
#
# PROCESS
# 1. Delete all flows from switch
# 2. Send flow add to switch, with OFPFF_SEND_FLOW_REM set
# 3. Send strict flow delete of flow to switch
# 4. Verify that OFPT_FLOW_REMOVED/OFPRR_DELETE message is received from switch
# 5. Verify flow table in switch
# 6. Test PASSED iff all flows sent to switch in step 2 above, less flow
#    removed in step 3 above, are returned in step 5 above, and that
#    asynch message was received; else test FAILED


class Flow_Del_4(basic.SimpleProtocol):
    """
    Test FLOW_DEL_4 from draft top-half test plan
    
    INPUTS
    None
    """

    def runTest(self):
        logging.info("Flow_Del_4 TEST BEGIN")

        # Clear all flows from switch

        logging.info("Deleting all flows from switch")
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # Get switch capabilites

        sw = Switch()
        self.assertTrue(sw.connect(self.controller), \
                        "Failed to connect to switch" \
                        )

        # Dream up some flow information, i.e. space to chose from for
        # random flow parameter generation

        fi = Flow_Info()
        fi.rand(10)
        
        # Dream up a flow config

        fc = Flow_Cfg()
        fc.rand(fi, \
                required_wildcards(self), \
                sw.tbl_stats.stats[0].wildcards, \
                sw.sw_features.actions, \
                sw.valid_ports, \
                sw.valid_queues \
                )
        fc = fc.canonical()

        # Send it to the switch. with "notify on removed"

        logging.info("Sending flow add to switch:")
        logging.info(str(fc))
        ft = Flow_Tbl()
        fc.send_rem = True
        self.assertTrue(sw.flow_add(fc), "Failed to add flow")
        ft.insert(fc)

        # Dream up some different actions, with the same flow key

        fc2 = copy.deepcopy(fc)
        while True:
            fc2.rand_mod(fi, \
                         sw.sw_features.actions, \
                         sw.valid_ports, \
                         sw.valid_queues \
                         )
            if fc2 != fc:
                break

        # Delete strictly
        
        logging.info("Sending strict flow del to switch:")
        logging.info(str(fc2))
        self.assertTrue(sw.flow_del(fc2, True), "Failed to delete flow")
        ft.delete(fc)

        # Do barrier, to make sure all flows are in

        self.assertTrue(sw.barrier(), "Barrier failed")

        result = True

        sw.settle()  # Allow switch to settle and generate any notifications

        # Check for expected "removed" message

        if not sw.errors_verify(0):
            result = False

        if not sw.removed_verify(1):
            result = False

        # Verify flow table

        sw.flow_tbl = ft
        if not sw.flow_tbl_verify():
            result = False

        self.assertTrue(result, "Flow_Del_4 TEST FAILED")
        logging.info("Flow_Del_4 TEST PASSED")
        
