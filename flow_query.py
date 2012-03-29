"""
Flow query test case.

Attempts to fill switch to capacity with randomized flows, and ensure that they all are read back correctly.
"""

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


def rand_dl_addr():
    return [random.randint(0, 255) & ~1, random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]


def rand_nw_addr():
    return random.randint(0, (1 << 32) - 1)


# TBD - These don't belong here

all_wildcards = [ofp.OFPFW_IN_PORT, \
                 ofp.OFPFW_DL_VLAN, \
                 ofp.OFPFW_DL_SRC, \
                 ofp.OFPFW_DL_DST, \
                 ofp.OFPFW_DL_TYPE, \
                 ofp.OFPFW_NW_PROTO, \
                 ofp.OFPFW_TP_SRC, \
                 ofp.OFPFW_TP_DST, \
                 ofp.OFPFW_NW_SRC_ALL, \
                 ofp.OFPFW_NW_DST_ALL, \
                 ofp.OFPFW_DL_VLAN_PCP, \
                 ofp.OFPFW_NW_TOS \
                 ]

all_actions = [ofp.OFPAT_OUTPUT,
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


class flow_cfg:
    # Members:
    # - match
    # - idle_timeout
    # - hard_timeout
    # - priority
    # - action_list

    def __init__(self):
        self.match           = parse.ofp_match()
        self.match.wildcards = ofp.OFPFW_ALL
        self.idle_timeout    = 0
        self.hard_timeout    = 0
        self.priority        = 0
        self.actions         = action_list.action_list()

    def __eq__(self, x):
        if self.match != x.match:
            return False
        if self.idle_timeout != x.idle_timeout:
            return False
        if self.hard_timeout != x.hard_timeout:
            return False
        if self.priority != x.priority:
            return False
        return self.actions == x.actions  # N.B. Action lists are ordered

    def rand(self, valid_wildcards, valid_actions, valid_ports):
        # TBD - Are IP addr wildcard specs all or nothing, valid wildcard reported as all 1s or all 0s?
        self.match.wildcards = valid_wildcards
        if (self.match.wildcards & ofp.OFPFW_NW_SRC_MASK) == ofp.OFPFW_NW_SRC_MASK:
            self.match.wildcards = (self.match.wildcards & ~ofp.OFPFW_NW_SRC_MASK) | ofp.OFPFW_NW_SRC_ALL
        if (self.match.wildcards & ofp.OFPFW_NW_DST_MASK) == ofp.OFPFW_NW_DST_MASK:
            self.match.wildcards = (self.match.wildcards & ~ofp.OFPFW_NW_DST_MASK) | ofp.OFPFW_NW_DST_ALL

        exact = True if random.randint(1, 100) == 1 else False

        for w in all_wildcards:
            if not exact and (w & valid_wildcards) != 0:
                if random.randint(1, 100) <= 50:
                    continue

            if w == ofp.OFPFW_IN_PORT:
                self.match.in_port = valid_ports[random.randint(0, len(valid_ports) - 1)].port_no
                self.match.wildcards = self.match.wildcards & ~w
            elif w == ofp.OFPFW_DL_VLAN:
                self.match.vl_vlan = random.randint(1, 4094)
                self.match.wildcards = self.match.wildcards & ~w
            elif w == ofp.OFPFW_DL_SRC:
                self.match.dl_src = rand_dl_addr()
                self.match.wildcards = self.match.wildcards & ~w
            elif w == ofp.OFPFW_DL_DST:
                self.match.dl_dst = rand_dl_addr()
                self.match.wildcards = self.match.wildcards & ~w
            elif w == ofp.OFPFW_DL_TYPE:
                if (self.match.wildcards & w) != 0:
                    self.match.dl_type = random.randint(0, (1 << 16) - 1)
                    self.match.wildcards = self.match.wildcards & ~w
            elif w == ofp.OFPFW_NW_PROTO:
                if (self.match.wildcards & w) != 0:
                    self.match.nw_proto = random.randint(0, (1 << 8) - 1)
                    self.match.wildcards = self.match.wildcards & ~w
                    self.match.dl_type   = 0x0800
                    self.match.wildcards = self.match.wildcards & ~ofp.OFPFW_DL_TYPE
            elif w == ofp.OFPFW_TP_SRC:
                self.match.tp_src = random.randint(0, (1 << 16) - 1)
                self.match.wildcards = self.match.wildcards & ~w
                self.match.nw_proto = [1, 6, 17][random.randint(0, 2)]
                self.match.wildcards = self.match.wildcards & ~ofp.OFPFW_NW_PROTO
                self.match.dl_type   = 0x0800
                self.match.wildcards = self.match.wildcards & ~ofp.OFPFW_DL_TYPE
            elif w == ofp.OFPFW_TP_DST:
                self.match.tp_dst = random.randint(0, (1 << 16) - 1)
                self.match.wildcards = self.match.wildcards & ~w
                self.match.nw_proto = [1, 6, 17][random.randint(0, 2)]
                self.match.wildcards = self.match.wildcards & ~ofp.OFPFW_NW_PROTO
                self.match.dl_type   = 0x0800
                self.match.wildcards = self.match.wildcards & ~ofp.OFPFW_DL_TYPE
            elif w == ofp.OFPFW_NW_SRC_MASK:
                n = 0 if exact else random.randint(0, 31)
                self.match.nw_src    = rand_nw_addr() & ~((1 << n) - 1)
                self.match.wildcards = (self.match.wildcards & ~w) | (n << ofp.OFPFW_NW_SRC_SHIFT)
                self.match.dl_type   = [0x0800, 0x0806][random.randint(0, 1)]
                self.match.wildcards = self.match.wildcards & ~ofp.OFPFW_DL_TYPE
            elif w == ofp.OFPFW_NW_DST_MASK:
                n = 0 if exact else random.randint(0, 31)
                self.match.nw_dst    = rand_nw_addr() & ~((1 << n) - 1)
                self.match.wildcards = (self.match.wildcards & ~w) | (n << ofp.OFPFW_NW_DST_SHIFT)
                self.match.dl_type   = [0x0800, 0x0806][random.randint(0, 1)]
                self.match.wildcards = self.match.wildcards & ~ofp.OFPFW_DL_TYPE
            elif w == ofp.OFPFW_DL_VLAN_PCP:
                self.match.dl_vlan_pcp = random.randint(0, (1 << 3) - 1)
                self.match.wildcards = self.match.wildcards & ~w
            elif w == ofp.OFPFW_NW_TOS:
                while True:
                    self.match.nw_tos = random.randint(0, (1 << 8) - 1)
                    if (self.match.nw_tos & 3) == 0:
                        break
                self.match.wildcards = self.match.wildcards & ~w
                self.match.dl_type   = 0x0800
                self.match.wildcards = self.match.wildcards & ~ofp.OFPFW_DL_TYPE

        # N.B. Don't make the timeout too short, else the flow might disappear before we
        # get a chance to check for it.
        t = random.randint(0, 65535)
        self.idle_timeout = 0 if t < 60 else t
        t = random.randint(0, 65535)
        self.hard_timeout = 0 if t < 60 else t
        self.priority     = 65535 if exact else random.randint(1, 65535)

        # N.B. Action lists are ordered
        supported_action_idxs = []
        ai = 0
        while ai < len(all_actions):
            if ((1 << all_actions[ai]) & valid_actions) != 0:
                supported_action_idxs.append(ai)
            ai = ai + 1

        supported_action_idxs = shuffle(supported_action_idxs)
        supported_action_idxs = supported_action_idxs[0 : random.randint(1, len(supported_action_idxs) - 1)]

        self.actions = action_list.action_list()
        for ai in supported_action_idxs:
            a = all_actions[ai]

            if a == ofp.OFPAT_OUTPUT:
                # TBD - Output actions are clustered in list, spread them out?
                port_idxs = shuffle(range(len(valid_ports)))
                port_idxs = port_idxs[0 : random.randint(1, len(valid_ports) - 1)]
                for pi in port_idxs:
                    act = action.action_output()
                    act.port = valid_ports[pi].port_no
                    self.actions.add(act)
            elif a == ofp.OFPAT_SET_VLAN_VID:
                act = action.action_set_vlan_vid()
                act.vlan_vid = random.randint(1, 4094)
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
                act.dl_addr = rand_dl_addr()
                self.actions.add(act)
            elif a == ofp.OFPAT_SET_DL_DST:
                act = action.action_set_dl_dst()
                act.dl_addr = rand_dl_addr()
                self.actions.add(act)
            elif a == ofp.OFPAT_SET_NW_SRC:
                act = action.action_set_nw_src()
                act.nw_addr = rand_nw_addr()
                self.actions.add(act)
            elif a == ofp.OFPAT_SET_NW_DST:
                act = action.action_set_nw_dst()
                act.nw_addr = rand_nw_addr()
                self.actions.add(act)
            elif a == ofp.OFPAT_SET_NW_TOS:
                act = action.action_set_nw_tos()
                act.nw_tos = random.randint(0, (1 << 8) - 1)
                self.actions.add(act)
            elif a == ofp.OFPAT_SET_TP_SRC:
                act = action.action_set_tp_src()
                act.tp_port = random.randint(0, (1 << 16) - 1)
                self.actions.add(act)
            elif a == ofp.OFPAT_SET_TP_DST:
                act = action.action_set_tp_dst()
                act.tp_port = random.randint(0, (1 << 16) - 1)
                self.actions.add(act)
            elif a == ofp.OFPAT_ENQUEUE:
                # TBD - Enqueue actions are clustered in list, spread them out?
                port_idxs = shuffle(range(len(valid_ports)))
                port_idxs = port_idxs[0 : random.randint(1, len(valid_ports) - 1)]
                for pi in port_idxs:
                    act = action.action_enqueue()
                    act.port = valid_ports[pi].port_no
                    # TBD - Limits for queue number?
                    act.queue_id = random.randint(0, 7)
                    self.actions.add(act)

        return self

    def overlap(self, x):
        if self.priority != x.priority:
            return False
        if (self.match.wildcards & ofp.OFPFW_IN_PORT) == 0 and (x.match.wildcards & ofp.OFPFW_IN_PORT) == 0 and self.match.in_port != x.match.in_port:
            return False
        if (self.match.wildcards & ofp.OFPFW_DL_VLAN) == 0 and (x.match.wildcards & ofp.OFPFW_DL_VLAN) == 0 and self.match.dl_vlan != x.match.dl_vlan:
            return False
        if (self.match.wildcards & ofp.OFPFW_DL_SRC) == 0 and (x.match.wildcards & ofp.OFPFW_DL_SRC) == 0 and self.match.dl_src != x.match.dl_src:
            return False
        if (self.match.wildcards & ofp.OFPFW_DL_DST) == 0 and (x.match.wildcards & ofp.OFPFW_DL_DST) == 0 and self.match.dl_dst != x.match.dl_dst:
            return False
        if (self.match.wildcards & ofp.OFPFW_DL_TYPE) == 0 and (x.match.wildcards & ofp.OFPFW_DL_TYPE) == 0 and self.match.dl_type != x.match.dl_type:
            return False
        if (self.match.wildcards & ofp.OFPFW_NW_PROTO) == 0 and (x.match.wildcards & ofp.OFPFW_NW_PROTO) == 0 and self.match.nw_proto != x.match.nw_proto:
            return False
        if (self.match.wildcards & ofp.OFPFW_TP_SRC) == 0 and (x.match.wildcards & ofp.OFPFW_TP_SRC) == 0 and self.match.tp_src != x.match.tp_src:
            return False
        if (self.match.wildcards & ofp.OFPFW_TP_DST) == 0 and (x.match.wildcards & ofp.OFPFW_TP_DST) == 0 and self.match.tp_dst != x.match.tp_dst:
            return False
        na = (self.match.wildcards & ofp.OFPFW_NW_SRC_MASK) >> ofp.OFPFW_NW_SRC_SHIFT
        nb = (x.match.wildcards & ofp.OFPFW_NW_SRC_MASK) >> ofp.OFPFW_NW_SRC_SHIFT
        if (na < 32 and nb < 32):
            m = ~((1 << na) - 1) & ~((1 << nb) - 1)
            if (self.match.nw_src & m) != (x.match.nw_src & m):
                return False
        na = (self.match.wildcards & ofp.OFPFW_NW_DST_MASK) >> ofp.OFPFW_NW_DST_SHIFT
        nb = (x.match.wildcards & ofp.OFPFW_NW_DST_MASK) >> ofp.OFPFW_NW_DST_SHIFT
        if (na < 32 and nb < 32):
            m = ~((1 << na) - 1) & ~((1 << nb) - 1)
            if (self.match.nw_dst & m) != (x.match.nw_dst & m):
                return False
        if (self.match.wildcards & ofp.OFPFW_DL_VLAN_PCP) == 0 and (x.match.wildcards & ofp.OFPFW_DL_VLAN_PCP) == 0 and self.match.dl_vlan_pcp != x.match.dl_vlan_pcp:
            return False
        if (self.match.wildcards & ofp.OFPFW_NW_TOS) == 0 and (x.match.wildcards & ofp.OFPFW_NW_TOS) == 0 and self.match.nw_tos != x.match.nw_tos:
            return False
        return True

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

    def test1(self, overlapf):
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
        self.logger.debug("Ports: " + str(map(lambda x: x.port_no, sw_features.ports)))

        # For each table, get wildcards supported maximum number of flows

        self.logger.debug("Retrieving table stats from switch")
        request = message.table_stats_request()
        (tbl_stats, pkt) = self.controller.transact(request, timeout=2)
        self.assertTrue(tbl_stats is not None, "No reply to table_stats_request")
        active_count = 0
        tbl_idx = 0
        while tbl_idx < sw_features.n_tables:
            self.logger.debug("Table " + str(tbl_idx) + " - ")
            self.logger.debug("Supported wildcards: " + hex(tbl_stats.stats[tbl_idx].wildcards))
            self.logger.debug("Max entries: " + str(tbl_stats.stats[tbl_idx].max_entries))
            self.logger.debug("Active count: " + str(tbl_stats.stats[tbl_idx].active_count))
            active_count = active_count + tbl_stats.stats[tbl_idx].active_count
            tbl_idx = tbl_idx + 1

        self.assertEqual(active_count, 0, "Total number of active entries not 0 -- delete all flow failed?")


        # For each table, think up flows to fill it

        self.logger.debug("Creating flows")
        num_flows = 0
        num_overlaps = 0
        tbl_flows = []
        tbl_idx = 0
        while tbl_idx < sw_features.n_tables:
            flow_cfgs = []
            flow_idx = 0
            while flow_idx < tbl_stats.stats[tbl_idx].max_entries:
                flow_out = flow_cfg().rand(tbl_stats.stats[tbl_idx].wildcards, sw_features.actions, sw_features.ports)
                j = 0
                while j < len(flow_cfgs):
                    if flow_out.overlap(flow_cfgs[j]):
                        break
                    j = j + 1
                if j < len(flow_cfgs):
                    num_overlaps = num_overlaps + 1
                    flow_out.overlap = True
                else:
                    flow_out.overlap = False
                flow_cfgs.append(flow_out)
                num_flows = num_flows + 1
                flow_idx = flow_idx + 1
            tbl_flows.append(flow_cfgs)
            tbl_idx = tbl_idx + 1

        self.logger.debug("Created " + str(num_flows) + " flows, with " + str(num_overlaps) + " overlaps")

        # Send all flows to switch

        self.logger.debug("Sending flows to switch")
        flow_num = 1
        tbl_idx = 0
        while tbl_idx < sw_features.n_tables:
            flow_idx = 0
            while flow_idx < len(tbl_flows[tbl_idx]):
                self.logger.debug("Sending flow number " + str(flow_num))
                flow_mod_msg = message.flow_mod()
                flow_mod_msg.buffer_id = 0xffffffff
                flow_mod_msg.cookie    = random.randint(0, (1 << 53) - 1)
                tbl_flows[tbl_idx][flow_idx].to_flow_mod_msg(flow_mod_msg)
                if overlapf:
                    flow_mod_msg.flags = flow_mod_msg.flags | ofp.OFPFF_CHECK_OVERLAP
                rv = self.controller.message_send(flow_mod_msg)
                self.assertTrue(rv != -1, "Error installing flow mod")
                (errmsg, pkt) = self.controller.poll(ofp.OFPT_ERROR, 1) # TBD - Tune timeout for error message
                if errmsg is not None:
                    # Got ERROR message
                    if errmsg.type == ofp.OFPET_FLOW_MOD_FAILED and errmsg.code == ofp.OFPFMFC_OVERLAP:
                        # Got "overlap" ERROR message
                        self.assertTrue(overlapf and tbl_flows[tbl_idx][flow_idx].overlap, "Got unexpected OVERLAP error message")
                    else:
                        self.assertTrue(False, "Got unexpected error message, type = " + str(errmsg.type) + ", code = " + str(errmsg.code))
                else:
                    # Did not get ERROR message
                    self.assertTrue(not (overlapf and tbl_flows[tbl_idx][flow_idx].overlap), "Did not get expected OVERLAP message")

                flow_idx = flow_idx + 1
                flow_num = flow_num + 1
            tbl_idx = tbl_idx + 1

        # Send barrier, to make sure all flows are in

        barrier = message.barrier_request()
        (resp, pkt) = self.controller.transact(barrier, 5)
        self.assertTrue(resp is not None, "Did not receive response to barrier request")

        # Check number of flows reported in table stats

        self.logger.debug("Verifying that table stats reports the correct number of active flows")
        request = message.table_stats_request()
        (tbl_stats_after, pkt) = self.controller.transact(request, timeout=2)
        self.assertTrue(tbl_stats_after is not None, "No reply to table_stats_request")

        num_flows_reported = 0
        for ts in tbl_stats_after.stats:
            num_flows_reported = num_flows_reported + ts.active_count

        num_flows_expected = num_flows
        if overlapf:
            num_flows_expected = num_flows_expected - num_overlaps

        self.assertEqual(num_flows_reported, num_flows_expected, "Incorrect number of flows returned by table stats, reported = " + str(num_flows_reported) + ", expected = " + str(num_flows_expected))

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

        self.assertEqual(flow_stats.type, ofp.OFPST_FLOW, "Unexpected type of response message")

        num_flows_reported = len(flow_stats.stats)

        self.assertEqual(num_flows_reported, num_flows_expected, "Incorrect number of flows returned by table stats, reported = " + str(num_flows_reported) + ", expected = " + str(num_flows_expected))

        tbl_idx = 0
        while tbl_idx < sw_features.n_tables:
            flow_idx = 0
            while flow_idx < len(tbl_flows[tbl_idx]):
                tbl_flows[tbl_idx][flow_idx].resp_matched = False
                flow_idx = flow_idx + 1
            tbl_idx = tbl_idx + 1

        num_resp_flows_matched = 0
        for flow_stat in flow_stats.stats:
            flow_in = flow_cfg()
            flow_in.from_flow_stat(flow_stat)

            tbl_idx = 0
            while tbl_idx < sw_features.n_tables:
                flow_idx = 0
                while flow_idx < len(tbl_flows[tbl_idx]):
                    f = tbl_flows[tbl_idx][flow_idx]
                    if not f.resp_matched and (not overlapf or not f.overlap) and f == flow_in:
                        f.resp_matched = True
                        num_resp_flows_matched = num_resp_flows_matched + 1
                        break
                    flow_idx = flow_idx + 1
                self.assertTrue(flow_idx < len(tbl_flows[tbl_idx]), "Reponse flow does not match any configured flow")
                tbl_idx = tbl_idx + 1

        self.assertEqual(num_resp_flows_matched, num_flows_expected, "Configured flow(s) missing in response, num_resp_flows_matched = " + str(num_resp_flows_matched) + ", num_flows_expected = " + str(num_flows_expected))


    def runTest(self):
        """
        Run all tests
        """

        self.test1(False)               # Test with no overlaps
        self.test1(True)                # Test with overlaps

