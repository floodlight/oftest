# Distributed under the OpenFlow Software License (see LICENSE)
# Copyright (c) 2010 The Board of Trustees of The Leland Stanford Junior University
# Copyright (c) 2012, 2013 Big Switch Networks, Inc.
"""
Flow stats test cases

These tests check the behavior of the flow stats request.
"""

import logging
import random

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
        table_id = test_param_get("table", 0)
        delete_all_flows(self.controller)

        flow1 = ofp.message.flow_add(
                table_id=table_id,
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
                table_id=table_id,
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
                table_id=table_id,
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

class CookieFlowStats(base_tests.SimpleDataPlane):
    """
    Retrieve flows using various masks on the cookie
    """
    def runTest(self):
        delete_all_flows(self.controller)

        # Also used as masks
        cookies = [
            0x0000000000000000,
            0xDDDDDDDD00000000,
            0x00000000DDDDDDDD,
            0xDDDDDDDDDDDDDDDD,
            0xDDDD0000DDDD0000,
            0x0000DDDD0000DDDD,
            0xDD00DD00DD00DD00,
            0xD0D0D0D0D0D0D0D0,
            0xF000000000000000,
            0xFF00000000000000,
            0xFFF0000000000000,
            0xFFFF000000000000,
        ]

        for i in range(0, 10):
            cookies.append(random.getrandbits(64))

        # Generate the matching cookies for each combination of cookie and mask
        matches = {}
        for mask in cookies:
            for cookie in cookies:
                matching = []
                for cookie2 in cookies:
                    if cookie & mask == cookie2 & mask:
                        matching.append(cookie2)
                matches[(cookie, mask)] = sorted(matching)

        # Generate a flow for each cookie
        flows = {}
        table_id = test_param_get("table", 0)
        for idx, cookie in enumerate(cookies):
            flows[cookie] = ofp.message.flow_add(
                table_id=table_id,
                cookie=cookie,
                match=ofp.match([ofp.oxm.vlan_vid(ofp.OFPVID_PRESENT|idx)]),
                buffer_id=ofp.OFP_NO_BUFFER)

        # Install flows
        for flow in flows.values():
            self.controller.message_send(flow)
        do_barrier(self.controller)

        # For each combination of cookie and match, verify the correct flows
        # are retrieved
        for (cookie, mask), expected_cookies in matches.iteritems():
            stats = get_flow_stats(self, ofp.match(), cookie=cookie, cookie_mask=mask)
            received_cookies = sorted([entry.cookie for entry in stats])
            logging.debug("expected 0x%016x/0x%016x: %s", cookie, mask,
                          ' '.join(["0x%016x" % x for x in expected_cookies]))
            logging.debug("received 0x%016x/0x%016x: %s", cookie, mask,
                          ' '.join(["0x%016x" % x for x in received_cookies]))
            self.assertEqual(expected_cookies, received_cookies)
