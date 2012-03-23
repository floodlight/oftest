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

from testutils import *
from time import sleep

#@var port_map Local copy of the configuration map from OF port
# numbers to OS interfaces
pa_port_map = None
#@var pa_logger Local logger object
pa_logger = None
#@var pa_config Local copy of global configuration data
pa_config = None

# TODO: ovs has problems with VLAN id?
WILDCARD_VALUES = [ofp.OFPFW_IN_PORT,
                   # ofp.OFPFW_DL_VLAN,
                   ofp.OFPFW_DL_SRC,
                   ofp.OFPFW_DL_DST,
                   ofp.OFPFW_DL_TYPE,
                   ofp.OFPFW_NW_PROTO,
                   ofp.OFPFW_TP_SRC,
                   ofp.OFPFW_TP_DST,
                   0x3F << ofp.OFPFW_NW_SRC_SHIFT,
                   0x3F << ofp.OFPFW_NW_DST_SHIFT,
                   ofp.OFPFW_DL_VLAN_PCP,
                   ofp.OFPFW_NW_TOS]

def test_set_init(config):
    """
    Set up function for packet action test classes

    @param config The configuration dictionary; see oft
    """

    global pa_port_map
    global pa_logger
    global pa_config

    pa_logger = logging.getLogger("pkt_act")
    pa_logger.info("Initializing test set")
    pa_port_map = config["port_map"]
    pa_config = config

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
            pa_logger.info("Sending stats request")
            rv = self.controller.message_send(stat_req)
            self.assertTrue(rv != -1, "Error sending flow stat req")
            do_barrier(self.controller)

            (response, raw) = self.controller.poll(ofp.OFPT_STATS_REPLY, 2)
            self.assertTrue(len(response.stats) == 1, "Did not receive flow stats reply")
            for obj in response.stats:
                # TODO: pad1 and pad2 fields may be nonzero, is this a bug?
                # for now, just clear them so the assert is simpler
                #obj.match.pad1 = 0
                #obj.match.pad2 = [0, 0]
                #self.assertEqual(match, obj.match,
                #                 "Matches do not match")
                pa_logger.info("Received " + str(obj.packet_count) + " packets")
                if obj.packet_count == packet_count:
                    all_packets_received = 1

            if all_packets_received:
                break
            sleep(1)

        self.assertTrue(all_packets_received,
                        "Packet count does not match number sent")

    def runTest(self):
        global pa_port_map

        # TODO: set from command-line parameter
        test_timeout = 60

        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        rc = delete_all_flows(self.controller, pa_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # build packet
        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        # build flow
        ingress_port = of_ports[0];
        egress_port = of_ports[1];
        pa_logger.info("Ingress " + str(ingress_port) + 
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
        pa_logger.info("Inserting flow")
        rv = self.controller.message_send(flow_mod_msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        do_barrier(self.controller)

        # no packets sent, so zero packet count
        self.verifyStats(match, ofp.OFPP_NONE, test_timeout, 0)

        # send packet N times
        num_sends = random.randint(10,20)
        pa_logger.info("Sending " + str(num_sends) + " test packets")
        for i in range(0,num_sends):
            pa_logger.info("Sending packet to dp port " + 
                           str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            (rcv_port, rcv_pkt, pkt_time) = self.dataplane.poll(timeout=test_timeout)
            self.assertTrue(rcv_pkt is not None, "Did not receive packet")
            pa_logger.debug("Packet len " + str(len(pkt)) + " in on " + 
                            str(rcv_port))
            self.assertEqual(rcv_port, egress_port, "Unexpected receive port")
            for j in range(0,test_timeout):
                if str(pkt) == str(rcv_pkt):
                    break
                sleep(1)
            self.assertTrue(j < test_timeout,
                            'Timeout sending packets for flow stats test')

        self.verifyStats(match, ofp.OFPP_NONE, test_timeout, num_sends)
        self.verifyStats(match, egress_port, test_timeout, num_sends)
        for wc in WILDCARD_VALUES:
            match.wildcards = wc
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
        match = parse.packet_to_flow_match(pkt)
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

        pa_logger.info("Ingress " + str(ingress_port) + 
                       " to egress " + str(egress_port))

        return flow_mod_msg

    def sendPacket(self, pkt, ingress_port, egress_port, test_timeout):
        pa_logger.info("Sending packet to dp port " + 
                       str(ingress_port))
        self.dataplane.send(ingress_port, str(pkt))
        (rcv_port, rcv_pkt, pkt_time) = self.dataplane.poll(timeout=test_timeout)
        self.assertTrue(rcv_pkt is not None, "Did not receive packet")
        pa_logger.debug("Packet len " + str(len(pkt)) + " in on " + 
                        str(rcv_port))
        self.assertEqual(rcv_port, egress_port, "Unexpected receive port")
        for j in range(0,test_timeout):
            if str(pkt) == str(rcv_pkt):
                break
            sleep(1)
        self.assertTrue(j < test_timeout,
                        'Timeout sending packets for flow stats test')

    def verifyStats(self, match, out_port, test_timeout, packet_count):
        stat_req = message.flow_stats_request()
        stat_req.match = match
        stat_req.table_id = 0xff
        stat_req.out_port = out_port

        all_packets_received = 0
        for i in range(0,test_timeout):
            pa_logger.info("Sending stats request")
            rv = self.controller.message_send(stat_req)
            self.assertTrue(rv != -1, "Error sending flow stat req")
            do_barrier(self.controller)

            (response, raw) = self.controller.poll(ofp.OFPT_STATS_REPLY, 2)
            self.assertTrue(len(response.stats) >= 1, "Did not receive flow stats reply")
            total_packets = 0
            for obj in response.stats:
                # TODO: pad1 and pad2 fields may be nonzero, is this a bug?
                # for now, just clear them so the assert is simpler
                #obj.match.pad1 = 0
                #obj.match.pad2 = [0, 0]
                #self.assertEqual(match, obj.match,
                #                 "Matches do not match")
                pa_logger.info("Received " + str(obj.packet_count) + " packets")
                total_packets += obj.packet_count
            if total_packets == packet_count:
                all_packets_received = 1
                break
            sleep(1)

        self.assertTrue(all_packets_received,
                        "Packet count does not match number sent")

    def runTest(self):
        global pa_port_map

        # TODO: set from command-line parameter
        test_timeout = 60

        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) >= 3, "Not enough ports for test")
        ingress_port = of_ports[0];
        egress_port1 = of_ports[1];
        egress_port2 = of_ports[2];

        rc = delete_all_flows(self.controller, pa_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        pkt1 = simple_tcp_packet()
        flow_mod_msg1 = self.buildFlowModMsg(pkt1, ingress_port, egress_port1)
       
        pkt2 = simple_tcp_packet(dl_src='0:7:7:7:7:7')
        flow_mod_msg2 = self.buildFlowModMsg(pkt2, ingress_port, egress_port2)
       
        pa_logger.info("Inserting flow1")
        rv = self.controller.message_send(flow_mod_msg1)
        self.assertTrue(rv != -1, "Error installing flow mod")
        pa_logger.info("Inserting flow2")
        rv = self.controller.message_send(flow_mod_msg2)
        self.assertTrue(rv != -1, "Error installing flow mod")
        do_barrier(self.controller)

        num_pkt1s = random.randint(10,30)
        pa_logger.info("Sending " + str(num_pkt1s) + " pkt1s")
        num_pkt2s = random.randint(10,30)
        pa_logger.info("Sending " + str(num_pkt2s) + " pkt2s")
        for i in range(0,num_pkt1s):
            self.sendPacket(pkt1, ingress_port, egress_port1, test_timeout)
        for i in range(0,num_pkt2s):
            self.sendPacket(pkt2, ingress_port, egress_port2, test_timeout)
            
        match1 = parse.packet_to_flow_match(pkt1)
        self.verifyStats(match1, ofp.OFPP_NONE, test_timeout, num_pkt1s)
        match2 = parse.packet_to_flow_match(pkt2)
        self.verifyStats(match2, ofp.OFPP_NONE, test_timeout, num_pkt2s)
        match1.wildcards |= ofp.OFPFW_DL_SRC
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
        match = parse.packet_to_flow_match(pkt)
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

        pa_logger.info("Ingress " + str(ingress_port) + 
                       " to egress " + str(egress_port))

        return flow_mod_msg

    def sendPacket(self, pkt, ingress_port, egress_port, test_timeout):
        pa_logger.info("Sending packet to dp port " + 
                       str(ingress_port))
        self.dataplane.send(ingress_port, str(pkt))
        (rcv_port, rcv_pkt, pkt_time) = self.dataplane.poll(timeout=test_timeout)
        self.assertTrue(rcv_pkt is not None, "Did not receive packet")
        pa_logger.debug("Packet len " + str(len(pkt)) + " in on " + 
                        str(rcv_port))
        self.assertEqual(rcv_port, egress_port, "Unexpected receive port")
        for j in range(0,test_timeout):
            if str(pkt) == str(rcv_pkt):
                break
            sleep(1)
        self.assertTrue(j < test_timeout,
                        'Timeout sending packets for flow stats test')

    def verifyAggFlowStats(self, match, out_port, test_timeout, 
                           flow_count, packet_count):
        stat_req = message.aggregate_stats_request()
        stat_req.match = match
        stat_req.table_id = 0xff
        stat_req.out_port = out_port

        all_packets_received = 0
        for i in range(0,test_timeout):
            pa_logger.info("Sending stats request")
            rv = self.controller.message_send(stat_req)
            self.assertTrue(rv != -1, "Error sending flow stat req")
            do_barrier(self.controller)

            (response, raw) = self.controller.poll(ofp.OFPT_STATS_REPLY, 2)
            self.assertTrue(len(response.stats) == 1, "Did not receive flow stats reply")
            for obj in response.stats:
                self.assertTrue(obj.flow_count == flow_count,
                                "Flow count " + str(obj.flow_count) +
                                " does not match expected " + str(flow_count))
                pa_logger.info("Received " + str(obj.packet_count) + " packets")
                if obj.packet_count == packet_count:
                    all_packets_received = 1

            if all_packets_received:
                break
            sleep(1)

        self.assertTrue(all_packets_received,
                        "Packet count does not match number sent")

    def runTest(self):
        global pa_port_map

        # TODO: set from command-line parameter
        test_timeout = 60

        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) >= 3, "Not enough ports for test")
        ingress_port = of_ports[0];
        egress_port1 = of_ports[1];
        egress_port2 = of_ports[2];

        rc = delete_all_flows(self.controller, pa_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        pkt1 = simple_tcp_packet()
        flow_mod_msg1 = self.buildFlowModMsg(pkt1, ingress_port, egress_port1)
       
        pkt2 = simple_tcp_packet(dl_src='0:7:7:7:7:7')
        flow_mod_msg2 = self.buildFlowModMsg(pkt2, ingress_port, egress_port2)
       
        pa_logger.info("Inserting flow1")
        rv = self.controller.message_send(flow_mod_msg1)
        self.assertTrue(rv != -1, "Error installing flow mod")
        pa_logger.info("Inserting flow2")
        rv = self.controller.message_send(flow_mod_msg2)
        self.assertTrue(rv != -1, "Error installing flow mod")
        do_barrier(self.controller)

        num_pkt1s = random.randint(10,30)
        pa_logger.info("Sending " + str(num_pkt1s) + " pkt1s")
        num_pkt2s = random.randint(10,30)
        pa_logger.info("Sending " + str(num_pkt2s) + " pkt2s")
        for i in range(0,num_pkt1s):
            self.sendPacket(pkt1, ingress_port, egress_port1, test_timeout)
        for i in range(0,num_pkt2s):
            self.sendPacket(pkt2, ingress_port, egress_port2, test_timeout)
            
        # loop on flow stats request until timeout
        match = parse.packet_to_flow_match(pkt1)
        match.wildcards |= ofp.OFPFW_DL_SRC
        self.verifyAggFlowStats(match, ofp.OFPP_NONE, test_timeout, 
                                2, num_pkt1s+num_pkt2s)

        # out_port filter for egress_port1
        self.verifyAggFlowStats(match, egress_port1, test_timeout, 
                                1, num_pkt1s)

        # out_port filter for egress_port1
        self.verifyAggFlowStats(match, egress_port2, test_timeout, 
                                1, num_pkt2s)
