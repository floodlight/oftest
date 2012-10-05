"""
Flow stats test case.
Similar to Flow stats test case in the perl test harness.

"""

import logging

import unittest
import random

import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action
import oftest.parse as parse
import basic

from oftest.testutils import *
from time import sleep

#@var fs_port_map Local copy of the configuration map from OF port
# numbers to OS interfaces
fs_port_map = None
#@var fs_config Local copy of global configuration data
fs_config = None

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

def test_set_init(config):
    """
    Set up function for packet action test classes

    @param config The configuration dictionary; see oft
    """

    basic.test_set_init(config)

    global fs_port_map
    global fs_config

    fs_port_map = config["port_map"]
    fs_config = config

def sendPacket(obj, pkt, ingress_port, egress_port, test_timeout):

    logging.info("Sending packet to dp port " + str(ingress_port) +
                   ", expecting output on " + str(egress_port))
    obj.dataplane.send(ingress_port, str(pkt))

    exp_pkt_arg = None
    exp_port = None
    if fs_config["relax"]:
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

class SingleFlowStats(basic.SimpleDataPlane):
    """
    Verify flow stats are properly retrieved.

    Generate a packet
    Generate and install a matching flow
    Send the packet
    Send a flow stats request to match the flow and retrieve stats
    Verify that the packet counter has incremented
    """

    def verifyStats(self, match, out_port, test_timeout, packet_count):
        stat_req = message.flow_stats_request()
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
            self.assertTrue(len(response.stats) == 1,
                            "Did not receive flow stats reply")
            for obj in response.stats:
                # TODO: pad1 and pad2 fields may be nonzero, is this a bug?
                # for now, just clear them so the assert is simpler
                #obj.match.pad1 = 0
                #obj.match.pad2 = [0, 0]
                #self.assertEqual(match, obj.match,
                #                 "Matches do not match")
                logging.info("Received " + str(obj.packet_count) + " packets")
                if obj.packet_count == packet_count:
                    all_packets_received = 1

            if all_packets_received:
                break
            sleep(1)

        self.assertTrue(all_packets_received,
                        "Packet count does not match number sent")

    def runTest(self):
        global fs_port_map

        # TODO: set from command-line parameter
        test_timeout = 60

        of_ports = fs_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # build packet
        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        # build flow
        ingress_port = of_ports[0];
        egress_port = of_ports[1];
        logging.info("Ingress " + str(ingress_port) + 
                       " to egress " + str(egress_port))
        match.in_port = ingress_port
        flow_mod_msg = message.flow_mod()
        flow_mod_msg.match = match
        flow_mod_msg.cookie = random.randint(0,9007199254740992)
        flow_mod_msg.buffer_id = 0xffffffff
        flow_mod_msg.idle_timeout = 0
        flow_mod_msg.hard_timeout = 0
        act.port = egress_port
        self.assertTrue(flow_mod_msg.actions.add(act), "Could not add action")
       
        # send flow
        logging.info("Inserting flow")
        rv = self.controller.message_send(flow_mod_msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        # no packets sent, so zero packet count
        self.verifyStats(match, ofp.OFPP_NONE, test_timeout, 0)

        # send packet N times
        num_sends = random.randint(10,20)
        logging.info("Sending " + str(num_sends) + " test packets")
        for i in range(0,num_sends):
            sendPacket(self, pkt, ingress_port, egress_port,
                       test_timeout)

        self.verifyStats(match, ofp.OFPP_NONE, test_timeout, num_sends)
        self.verifyStats(match, egress_port, test_timeout, num_sends)
        for wc in WILDCARD_VALUES:
            match.wildcards = required_wildcards(self) | wc
            self.verifyStats(match, egress_port, test_timeout, num_sends)


class TwoFlowStats(basic.SimpleDataPlane):
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
        
        flow_mod_msg = message.flow_mod()
        flow_mod_msg.match = match
        flow_mod_msg.cookie = random.randint(0,9007199254740992)
        flow_mod_msg.buffer_id = 0xffffffff
        flow_mod_msg.idle_timeout = 0
        flow_mod_msg.hard_timeout = 0
        act = action.action_output()
        act.port = egress_port
        self.assertTrue(flow_mod_msg.actions.add(act), "Could not add action")

        logging.info("Ingress " + str(ingress_port) + 
                       " to egress " + str(egress_port))

        return flow_mod_msg

    def sumStatsReplyCounts(self, response):
        total_packets = 0
        for obj in response.stats:
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
        stat_req = message.flow_stats_request()
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
        global fs_port_map

        # TODO: set from command-line parameter
        test_timeout = 60

        of_ports = fs_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) >= 3, "Not enough ports for test")
        ingress_port = of_ports[0];
        egress_port1 = of_ports[1];
        egress_port2 = of_ports[2];

        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        pkt1 = simple_tcp_packet()
        flow_mod_msg1 = self.buildFlowModMsg(pkt1, ingress_port, egress_port1)
       
        pkt2 = simple_tcp_packet(dl_src='0:7:7:7:7:7')
        flow_mod_msg2 = self.buildFlowModMsg(pkt2, ingress_port, egress_port2)
       
        logging.info("Inserting flow1")
        rv = self.controller.message_send(flow_mod_msg1)
        self.assertTrue(rv != -1, "Error installing flow mod")
        logging.info("Inserting flow2")
        rv = self.controller.message_send(flow_mod_msg2)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

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


class AggregateStats(basic.SimpleDataPlane):
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
        
        flow_mod_msg = message.flow_mod()
        flow_mod_msg.match = match
        flow_mod_msg.cookie = random.randint(0,9007199254740992)
        flow_mod_msg.buffer_id = 0xffffffff
        flow_mod_msg.idle_timeout = 0
        flow_mod_msg.hard_timeout = 0
        act = action.action_output()
        act.port = egress_port
        self.assertTrue(flow_mod_msg.actions.add(act), "Could not add action")

        logging.info("Ingress " + str(ingress_port) + 
                       " to egress " + str(egress_port))

        return flow_mod_msg

    def verifyAggFlowStats(self, match, out_port, test_timeout, 
                           flow_count, packet_count):
        stat_req = message.aggregate_stats_request()
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
            self.assertTrue(len(response.stats) == 1, 
                            "Did not receive flow stats reply")
            for obj in response.stats:
                self.assertTrue(obj.flow_count == flow_count,
                                "Flow count " + str(obj.flow_count) +
                                " does not match expected " + str(flow_count))
                logging.info("Received " + str(obj.packet_count) + " packets")
                if obj.packet_count == packet_count:
                    all_packets_received = 1

            if all_packets_received:
                break
            sleep(1)

        self.assertTrue(all_packets_received,
                        "Packet count does not match number sent")

    def runTest(self):
        global fs_port_map

        # TODO: set from command-line parameter
        test_timeout = 60

        of_ports = fs_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) >= 3, "Not enough ports for test")
        ingress_port = of_ports[0];
        egress_port1 = of_ports[1];
        egress_port2 = of_ports[2];

        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        pkt1 = simple_tcp_packet()
        flow_mod_msg1 = self.buildFlowModMsg(pkt1, ingress_port, egress_port1)
       
        pkt2 = simple_tcp_packet(dl_src='0:7:7:7:7:7')
        flow_mod_msg2 = self.buildFlowModMsg(pkt2, ingress_port, egress_port2)
       
        logging.info("Inserting flow1")
        rv = self.controller.message_send(flow_mod_msg1)
        self.assertTrue(rv != -1, "Error installing flow mod")
        logging.info("Inserting flow2")
        rv = self.controller.message_send(flow_mod_msg2)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

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
