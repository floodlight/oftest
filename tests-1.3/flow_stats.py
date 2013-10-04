# Distributed under the OpenFlow Software License (see LICENSE)
# Copyright (c) 2010 The Board of Trustees of The Leland Stanford Junior University
# Copyright (c) 2012, 2013 Big Switch Networks, Inc.
"""
Flow stats test cases

These tests check the behavior of the flow stats request.
"""

import logging

from oftest import config
import oftest.base_tests as base_tests
import ofp
import oftest.packet as scapy

from oftest.testutils import *
from oftest.parse import parse_ipv6

class AllFlowStats(base_tests.SimpleDataPlane):
    """
    Retrieve all flows and verify the stats entries match the flow-mods sent
    """
    def runTest(self):
        port1, port2, port3 = openflow_ports(3)
        delete_all_flows(self.controller)

        flow1 = ofp.message.flow_add(
                table_id=0,
                priority=0x11,
                idle_timeout=0x21,
                hard_timeout=0x31,
                flags=ofp.OFPFF_NO_PKT_COUNTS,
                cookie=1,
                match=ofp.match([
                    ofp.oxm.in_port(port1),
                    ofp.oxm.vlan_vid(ofp.OFPVID_PRESENT|1)]),
                instructions=[
                    ofp.instruction.write_actions(
                        actions=[
                            ofp.action.output(
                                port=port1,
                                max_len=ofp.OFPCML_NO_BUFFER)])],
                buffer_id=ofp.OFP_NO_BUFFER)

        flow2 = ofp.message.flow_add(
                table_id=0,
                priority=0x12,
                idle_timeout=0x22,
                hard_timeout=0x32,
                flags=ofp.OFPFF_NO_BYT_COUNTS,
                cookie=2,
                match=ofp.match([
                    ofp.oxm.in_port(port2),
                    ofp.oxm.vlan_vid(ofp.OFPVID_PRESENT|2)]),
                instructions=[
                    ofp.instruction.write_actions(
                        actions=[
                            ofp.action.output(
                                port=port2,
                                max_len=ofp.OFPCML_NO_BUFFER)])],
                buffer_id=ofp.OFP_NO_BUFFER)

        flow3 = ofp.message.flow_add(
                table_id=0,
                priority=0x13,
                idle_timeout=0x23,
                hard_timeout=0x33,
                flags=ofp.OFPFF_CHECK_OVERLAP,
                cookie=3,
                match=ofp.match([
                    ofp.oxm.in_port(port3),
                    ofp.oxm.vlan_vid(ofp.OFPVID_PRESENT|3)]),
                instructions=[
                    ofp.instruction.write_actions(
                        actions=[
                            ofp.action.output(
                                port=port3,
                                max_len=ofp.OFPCML_NO_BUFFER)])],
                buffer_id=ofp.OFP_NO_BUFFER)

        flows = [flow1, flow2, flow3]
        for flow in flows:
            logging.debug(flow.show())
            self.controller.message_send(flow)

        flows_by_cookie = { flow.cookie: flow for flow in flows }

        do_barrier(self.controller)

        logging.info("Sending flow stats request")
        stats = get_flow_stats(self, ofp.match())
        logging.info("Received %d flow stats entries", len(stats))

        seen_cookies = set()
        for entry in stats:
            logging.debug(entry.show())
            self.assertTrue(entry.cookie in flows_by_cookie, "Unexpected cookie")
            self.assertTrue(entry.cookie not in seen_cookies, "Duplicate cookie")
            flow = flows_by_cookie[entry.cookie]
            seen_cookies.add(entry.cookie)

            self.assertEqual(entry.table_id, flow.table_id)
            self.assertEqual(entry.priority, flow.priority)
            self.assertEqual(entry.idle_timeout, flow.idle_timeout)
            self.assertEqual(entry.hard_timeout, flow.hard_timeout)
            self.assertEqual(entry.flags, flow.flags)
            self.assertEqual(entry.cookie, flow.cookie)
            self.assertEqual(sorted(entry.match.oxm_list), sorted(flow.match.oxm_list))
            self.assertEqual(sorted(entry.instructions), sorted(flow.instructions))

        self.assertEqual(seen_cookies, set([1,2,3]))
