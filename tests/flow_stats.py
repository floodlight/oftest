"""
Flow stats test case.
Similar to Flow stats test case in the perl test harness.

"""

import logging

import unittest
import random
import copy

from oftest import config
import oftest.controller as controller
import ofp
import oftest.dataplane as dataplane
import oftest.parse as parse
import oftest.base_tests as base_tests

from oftest.testutils import *
from time import sleep

# TODO: ovs has problems with VLAN id?
WILDCARD_VALUES = [ofp.OFPFW_IN_PORT,
                   # (ofp.OFPFW_DL_VLAN | ofp.OFPFW_DL_VLAN_PCP),
                   ofp.OFPFW_DL_SRC,
                   ofp.OFPFW_DL_DST,
                   (ofp.OFPFW_DL_TYPE | ofp.OFPFW_NW_SRC_ALL |
                    ofp.OFPFW_NW_DST_ALL | ofp.OFPFW_NW_TOS | ofp.OFPFW_NW_PROTO |
                    ofp.OFPFW_TP_SRC | ofp.OFPFW_TP_DST),
                   (ofp.OFPFW_NW_PROTO | ofp.OFPFW_TP_SRC | ofp.OFPFW_TP_DST),
                   ofp.OFPFW_TP_SRC,
                   ofp.OFPFW_TP_DST,
                   ofp.OFPFW_NW_SRC_MASK,
                   ofp.OFPFW_NW_DST_MASK,
                   ofp.OFPFW_DL_VLAN_PCP,
                   ofp.OFPFW_NW_TOS]

def sendPacket(obj, pkt, ingress_port, egress_port, test_timeout):

    logging.info("Sending packet to dp port " + str(ingress_port) +
                   ", expecting output on " + str(egress_port))
    obj.dataplane.send(ingress_port, str(pkt))

    exp_pkt_arg = None
    exp_port = None
    if config["relax"]:
        exp_pkt_arg = pkt
        exp_port = egress_port

    (rcv_port, rcv_pkt, pkt_time) = obj.dataplane.poll(port_number=exp_port,
                                                       exp_pkt=exp_pkt_arg)
    obj.assertTrue(rcv_pkt is not None,
                   "Packet not received on port " + str(egress_port))
    logging.debug("Packet len " + str(len(rcv_pkt)) + " in on " + 
                    str(rcv_port))
    obj.assertEqual(rcv_port, egress_port,
                    "Packet received on port " + str(rcv_port) +
                    ", expected port " + str(egress_port))
    obj.assertEqual(str(pkt), str(rcv_pkt),
                    'Response packet does not match send packet')

class SingleFlowStats(base_tests.SimpleDataPlane):
    """
    Verify flow stats are properly retrieved.

    Generate a packet
    Generate and install a matching flow
    Send the packet
    Send a flow stats request to match the flow and retrieve stats
    Verify that the packet counter has incremented
    """

    def verifyStats(self, flow_mod_msg, match, out_port, test_timeout, packet_count):
        stat_req = ofp.message.flow_stats_request()
        stat_req.match = match
        stat_req.table_id = 0xff
        stat_req.out_port = out_port

        all_packets_received = 0
        for i in range(0,test_timeout):
            logging.info("Sending stats request")
            response, pkt = self.controller.transact(stat_req,
                                                     timeout=test_timeout)
            self.assertTrue(response is not None, 
                            "No response to stats request")
            self.assertTrue(len(response.entries) == 1,
                            "Did not receive flow stats reply")
            for obj in response.entries:
                # TODO: pad1 and pad2 fields may be nonzero, is this a bug?
                # for now, just clear them so the assert is simpler
                obj.match.pad1 = 0
                obj.match.pad2 = [0, 0]
                self.assertEqual(flow_mod_msg.match, obj.match,
                                 "Matches do not match")
                self.assertEqual(obj.cookie, flow_mod_msg.cookie)
                self.assertEqual(obj.priority, flow_mod_msg.priority)
                self.assertEqual(obj.idle_timeout, flow_mod_msg.idle_timeout)
                self.assertEqual(obj.hard_timeout, flow_mod_msg.hard_timeout)
                self.assertEqual(obj.actions, flow_mod_msg.actions)
                logging.info("Received " + str(obj.packet_count) + " packets")
                if obj.packet_count == packet_count:
                    all_packets_received = 1

            if all_packets_received:
                break
            sleep(1)

        self.assertTrue(all_packets_received,
                        "Packet count does not match number sent")

    def runTest(self):
        # TODO: set from command-line parameter
        test_timeout = 60

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        delete_all_flows(self.controller)

        # build packet
        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = ofp.action.output()

        # build flow
        ingress_port = of_ports[0];
        egress_port = of_ports[1];
        logging.info("Ingress " + str(ingress_port) + 
                       " to egress " + str(egress_port))
        match.in_port = ingress_port
        flow_mod_msg = ofp.message.flow_add()
        flow_mod_msg.match = copy.deepcopy(match)
        flow_mod_msg.cookie = random.randint(0,9007199254740992)
        flow_mod_msg.buffer_id = 0xffffffff
        flow_mod_msg.idle_timeout = 60000
        flow_mod_msg.hard_timeout = 65000
        flow_mod_msg.priority = 100
        act.port = egress_port
        flow_mod_msg.actions.append(act)
       
        # send flow
        logging.info("Inserting flow")
        self.controller.message_send(flow_mod_msg)
        do_barrier(self.controller)

        # no packets sent, so zero packet count
        self.verifyStats(flow_mod_msg, match, ofp.OFPP_NONE, test_timeout, 0)

        # send packet N times
        num_sends = random.randint(10,20)
        logging.info("Sending " + str(num_sends) + " test packets")
        for i in range(0,num_sends):
            sendPacket(self, pkt, ingress_port, egress_port,
                       test_timeout)

        self.verifyStats(flow_mod_msg, match, ofp.OFPP_NONE, test_timeout, num_sends)
        self.verifyStats(flow_mod_msg, match, egress_port, test_timeout, num_sends)
        for wc in WILDCARD_VALUES:
            match.wildcards = required_wildcards(self) | wc
            self.verifyStats(flow_mod_msg, match, egress_port, test_timeout, num_sends)


class TwoFlowStats(base_tests.SimpleDataPlane):
    """
    Verify flow stats are properly retrieved.

    Generate two packets and install two matching flows
    Send some number of packets
    Send a flow stats request to match the flows and retrieve stats
    Verify that the packet counter has incremented

    TODO: add a third flow, and then configure the match to exclude
    that flow?
    """

    def buildFlowModMsg(self, pkt, ingress_port, egress_port):
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        match.in_port = ingress_port
        
        flow_mod_msg = ofp.message.flow_add()
        flow_mod_msg.match = match
        flow_mod_msg.cookie = random.randint(0,9007199254740992)
        flow_mod_msg.buffer_id = 0xffffffff
        flow_mod_msg.idle_timeout = 0
        flow_mod_msg.hard_timeout = 0
        act = ofp.action.output()
        act.port = egress_port
        flow_mod_msg.actions.append(act)

        logging.info("Ingress " + str(ingress_port) + 
                       " to egress " + str(egress_port))

        return flow_mod_msg

    def sumStatsReplyCounts(self, response):
        total_packets = 0
        for obj in response.entries:
            # TODO: pad1 and pad2 fields may be nonzero, is this a bug?
            # for now, just clear them so the assert is simpler
            #obj.match.pad1 = 0
            #obj.match.pad2 = [0, 0]
            #self.assertEqual(match, obj.match,
            #                 "Matches do not match")
           logging.info("Received " + str(obj.packet_count)
                          + " packets")
           total_packets += obj.packet_count
        return total_packets

    def verifyStats(self, match, out_port, test_timeout, packet_count):
        stat_req = ofp.message.flow_stats_request()
        stat_req.match = match
        stat_req.table_id = 0xff
        stat_req.out_port = out_port

        all_packets_received = 0
        for i in range(0,test_timeout):
            logging.info("Sending stats request")
            # TODO: move REPLY_MORE handling to controller.transact?
            response, pkt = self.controller.transact(stat_req,
                                                     timeout=test_timeout)
            self.assertTrue(response is not None,
                            "No response to stats request")
            total_packets = self.sumStatsReplyCounts(response)

            while response.flags == ofp.OFPSF_REPLY_MORE:
               response, pkt = self.controller.poll(exp_msg=
                                                    ofp.OFPT_STATS_REPLY,
                                                    timeout=test_timeout)
               total_packets += self.sumStatsReplyCounts(response)

            if total_packets == packet_count:
                all_packets_received = 1
                break
            sleep(1)

        self.assertTrue(all_packets_received,
                        "Total stats packet count " + str(total_packets) +
                        " does not match number sent " + str(packet_count))

    def runTest(self):
        # TODO: set from command-line parameter
        test_timeout = 60

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) >= 3, "Not enough ports for test")
        ingress_port = of_ports[0];
        egress_port1 = of_ports[1];
        egress_port2 = of_ports[2];

        delete_all_flows(self.controller)

        pkt1 = simple_tcp_packet()
        flow_mod_msg1 = self.buildFlowModMsg(pkt1, ingress_port, egress_port1)
       
        pkt2 = simple_tcp_packet(eth_src='0:7:7:7:7:7')
        flow_mod_msg2 = self.buildFlowModMsg(pkt2, ingress_port, egress_port2)
       
        logging.info("Inserting flow1")
        self.controller.message_send(flow_mod_msg1)
        logging.info("Inserting flow2")
        self.controller.message_send(flow_mod_msg2)
        do_barrier(self.controller)

        num_pkt1s = random.randint(10,30)
        logging.info("Sending " + str(num_pkt1s) + " pkt1s")
        num_pkt2s = random.randint(10,30)
        logging.info("Sending " + str(num_pkt2s) + " pkt2s")
        for i in range(0,num_pkt1s):
            sendPacket(self, pkt1, ingress_port, egress_port1, test_timeout)
        for i in range(0,num_pkt2s):
            sendPacket(self, pkt2, ingress_port, egress_port2, test_timeout)
            
        match1 = packet_to_flow_match(self, pkt1)
        logging.info("Verifying flow1's " + str(num_pkt1s) + " packets")
        self.verifyStats(match1, ofp.OFPP_NONE, test_timeout, num_pkt1s)
        match2 = packet_to_flow_match(self, pkt2)
        logging.info("Verifying flow2's " + str(num_pkt2s) + " packets")
        self.verifyStats(match2, ofp.OFPP_NONE, test_timeout, num_pkt2s)
        match1.wildcards |= ofp.OFPFW_DL_SRC
        logging.info("Verifying combined " + str(num_pkt1s+num_pkt2s) + " packets")
        self.verifyStats(match1, ofp.OFPP_NONE, test_timeout, 
                         num_pkt1s+num_pkt2s)
        # TODO: sweep through the wildcards to verify matching?


class AggregateStats(base_tests.SimpleDataPlane):
    """
    Verify aggregate flow stats are properly retrieved.

    Generate two packets
    Generate and install two matching flows
    Send an aggregate stats request
    Verify that aggregate stats are correct
    Also verify out_port filtering
    """

    def buildFlowModMsg(self, pkt, ingress_port, egress_port):
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        match.in_port = ingress_port
        
        flow_mod_msg = ofp.message.flow_add()
        flow_mod_msg.match = match
        flow_mod_msg.cookie = random.randint(0,9007199254740992)
        flow_mod_msg.buffer_id = 0xffffffff
        flow_mod_msg.idle_timeout = 0
        flow_mod_msg.hard_timeout = 0
        act = ofp.action.output()
        act.port = egress_port
        flow_mod_msg.actions.append(act)

        logging.info("Ingress " + str(ingress_port) + 
                       " to egress " + str(egress_port))

        return flow_mod_msg

    def verifyAggFlowStats(self, match, out_port, test_timeout, 
                           flow_count, packet_count):
        stat_req = ofp.message.aggregate_stats_request()
        stat_req.match = match
        stat_req.table_id = 0xff
        stat_req.out_port = out_port

        all_packets_received = 0
        for i in range(0,test_timeout):
            logging.info("Sending stats request")
            response, pkt = self.controller.transact(stat_req,
                                                     timeout=test_timeout)
            self.assertTrue(response is not None, 
                            "No response to stats request")
            self.assertTrue(response.flow_count == flow_count,
                            "Flow count " + str(response.flow_count) +
                            " does not match expected " + str(flow_count))
            logging.info("Received " + str(response.packet_count) + " packets")
            if response.packet_count == packet_count:
                all_packets_received = 1

            if all_packets_received:
                break
            sleep(1)

        self.assertTrue(all_packets_received,
                        "Packet count does not match number sent")

    def runTest(self):
        # TODO: set from command-line parameter
        test_timeout = 60

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) >= 3, "Not enough ports for test")
        ingress_port = of_ports[0];
        egress_port1 = of_ports[1];
        egress_port2 = of_ports[2];

        delete_all_flows(self.controller)

        pkt1 = simple_tcp_packet()
        flow_mod_msg1 = self.buildFlowModMsg(pkt1, ingress_port, egress_port1)
       
        pkt2 = simple_tcp_packet(eth_src='0:7:7:7:7:7')
        flow_mod_msg2 = self.buildFlowModMsg(pkt2, ingress_port, egress_port2)
       
        logging.info("Inserting flow1")
        self.controller.message_send(flow_mod_msg1)
        logging.info("Inserting flow2")
        self.controller.message_send(flow_mod_msg2)
        do_barrier(self.controller)

        num_pkt1s = random.randint(10,30)
        logging.info("Sending " + str(num_pkt1s) + " pkt1s")
        num_pkt2s = random.randint(10,30)
        logging.info("Sending " + str(num_pkt2s) + " pkt2s")
        for i in range(0,num_pkt1s):
            sendPacket(self, pkt1, ingress_port, egress_port1, test_timeout)
        for i in range(0,num_pkt2s):
            sendPacket(self, pkt2, ingress_port, egress_port2, test_timeout)
            
        # loop on flow stats request until timeout
        match = packet_to_flow_match(self, pkt1)
        match.wildcards |= ofp.OFPFW_DL_SRC
        self.verifyAggFlowStats(match, ofp.OFPP_NONE, test_timeout, 
                                2, num_pkt1s+num_pkt2s)

        # out_port filter for egress_port1
        self.verifyAggFlowStats(match, egress_port1, test_timeout, 
                                1, num_pkt1s)

        # out_port filter for egress_port1
        self.verifyAggFlowStats(match, egress_port2, test_timeout, 
                                1, num_pkt2s)

class EmptyFlowStats(base_tests.SimpleDataPlane):
    """
    Verify the switch replies to a flow stats request when
    the query doesn't match any flows.
    """
    def runTest(self):
        delete_all_flows(self.controller)
        match = ofp.match()
        match.wildcards = 0
        stat_req = ofp.message.flow_stats_request()
        stat_req.match = match
        stat_req.table_id = 0xff
        stat_req.out_port = ofp.OFPP_NONE

        response, pkt = self.controller.transact(stat_req)
        self.assertTrue(response is not None,
                        "No response to stats request")
        self.assertEquals(len(response.entries), 0)
        self.assertEquals(response.flags, 0)

class EmptyAggregateStats(base_tests.SimpleDataPlane):
    """
    Verify aggregate flow stats are properly retrieved when
    the query doesn't match any flows.
    """
    def runTest(self):
        delete_all_flows(self.controller)
        match = ofp.match()
        match.wildcards = 0
        stat_req = ofp.message.aggregate_stats_request()
        stat_req.match = match
        stat_req.table_id = 0xff
        stat_req.out_port = ofp.OFPP_NONE

        response, pkt = self.controller.transact(stat_req)
        self.assertTrue(response is not None,
                        "No response to stats request")
        self.assertEquals(response.flow_count, 0)
        self.assertEquals(response.packet_count, 0)
        self.assertEquals(response.byte_count, 0)

class DeletedFlowStats(base_tests.SimpleDataPlane):
    """
    Verify flow stats are properly returned when a flow is deleted.

    Generate a packet
    Generate and install a matching flow
    Send the packet
    Delete the flow
    Verify that the flow_removed message has the correct stats
    """

    def runTest(self):
        # TODO: set from command-line parameter
        test_timeout = 60

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        delete_all_flows(self.controller)

        # build packet
        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None,
                        "Could not generate flow match from pkt")
        act = ofp.action.output()

        # build flow
        ingress_port = of_ports[0];
        egress_port = of_ports[1];
        logging.info("Ingress " + str(ingress_port) +
                       " to egress " + str(egress_port))
        match.in_port = ingress_port
        flow_mod_msg = ofp.message.flow_add()
        flow_mod_msg.match = copy.deepcopy(match)
        flow_mod_msg.cookie = random.randint(0,9007199254740992)
        flow_mod_msg.buffer_id = 0xffffffff
        flow_mod_msg.idle_timeout = 0
        flow_mod_msg.hard_timeout = 0
        flow_mod_msg.priority = 100
        flow_mod_msg.flags = ofp.OFPFF_SEND_FLOW_REM
        act.port = egress_port
        flow_mod_msg.actions.append(act)

        # send flow
        logging.info("Inserting flow")
        self.controller.message_send(flow_mod_msg)
        do_barrier(self.controller)

        # send packet N times
        num_sends = random.randint(10,20)
        logging.info("Sending " + str(num_sends) + " test packets")
        for i in range(0,num_sends):
            sendPacket(self, pkt, ingress_port, egress_port,
                       test_timeout)

        # wait some time for flow stats to be propagated
        # FIXME timeout handling should be unified
        sleep(test_param_get('default_timeout', default=2))

        # delete flow
        logging.info("Deleting flow")
        delete_all_flows(self.controller)

        # wait for flow_removed message
        flow_removed, _ = self.controller.poll(
            exp_msg=ofp.OFPT_FLOW_REMOVED, timeout=test_timeout)

        self.assertTrue(flow_removed != None, "Did not receive flow_removed message")
        self.assertEqual(flow_removed.cookie, flow_mod_msg.cookie, 
                         "Received cookie " + str(flow_removed.cookie) +
                         " does not match expected " + str(flow_mod_msg.cookie))
        self.assertEqual(flow_removed.reason, ofp.OFPRR_DELETE,
                         "Received reason " + str(flow_removed.reason) + 
                         " does not match expected " + str(ofp.OFPRR_DELETE))
        self.assertEqual(flow_removed.packet_count, num_sends,
                         "Received packet count " + str(flow_removed.packet_count) + 
                         " does not match expected " + str(num_sends))
        tolerance = 5 # percent
        self.assertTrue(flow_removed.byte_count >= 
                        (1-tolerance/100.0) * num_sends * len(str(pkt)) and
                        flow_removed.byte_count <= 
                        (1+tolerance/100.0) * num_sends * len(str(pkt)),
                        "Received byte count " + str(flow_removed.byte_count) +
                        " is not within " + str(tolerance) + "% of expected " + 
                        str(num_sends*len(str(pkt))))
