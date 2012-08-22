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

#@var fs_port_map Local copy of the configuration map from OF port
# numbers to OS interfaces
fs_port_map = None
#@var fs_logger Local logger object
fs_logger = None
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
    global fs_logger
    global fs_config

    fs_logger = logging.getLogger("flow_stats")
    fs_logger.info("Initializing test set")
    fs_port_map = config["port_map"]
    fs_config = config

def sendPacket(obj, pkt, ingress_port, egress_port, test_timeout):

    fs_logger.info("Sending packet to dp port " + str(ingress_port) +
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
    fs_logger.debug("Packet len " + str(len(rcv_pkt)) + " in on " + 
                    str(rcv_port))
    obj.assertEqual(rcv_port, egress_port,
                    "Packet received on port " + str(rcv_port) +
                    ", expected port " + str(egress_port))
    obj.assertEqual(str(pkt), str(rcv_pkt),
                    'Response packet does not match send packet')

def getStats(obj, port):
    stat_req = message.port_stats_request()
    stat_req.port_no = port

    fs_logger.info("Sending stats request")
    response, pkt = obj.controller.transact(stat_req, timeout=2)
    obj.assertTrue(response is not None, 
                    "No response to stats request")
    obj.assertTrue(len(response.stats) == 1,
                    "Did not receive port stats reply")
    for item in response.stats:
        fs_logger.info("Sent " + str(item.tx_packets) + " packets")
        packet_sent = item.tx_packets
        packet_recv = item.rx_packets
    fs_logger.info("Port %d stats count: tx %d rx %d" % (port, packet_sent, packet_recv))
    return packet_sent, packet_recv

def verifyStats(obj, port, test_timeout, packet_sent, packet_recv):
    stat_req = message.port_stats_request()
    stat_req.port_no = port

    all_packets_received = 0
    all_packets_sent = 0
    sent = recv = 0
    for i in range(0,test_timeout):
        fs_logger.info("Sending stats request")
        response, pkt = obj.controller.transact(stat_req,
                                                timeout=test_timeout)
        obj.assertTrue(response is not None, 
                       "No response to stats request")
        obj.assertTrue(len(response.stats) == 1,
                       "Did not receive port stats reply")
        for item in response.stats:
            sent = item.tx_packets
            recv = item.rx_packets
            fs_logger.info("Sent " + str(item.tx_packets) + " packets")
            if item.tx_packets == packet_sent:
                all_packets_sent = 1
            fs_logger.info("Received " + str(item.rx_packets) + " packets")
            if item.rx_packets == packet_recv:
                all_packets_received = 1

        if all_packets_received and all_packets_sent:
            break
        sleep(1)

    fs_logger.info("Expected port %d stats count: tx %d rx %d" % (port, packet_sent, packet_recv))
    fs_logger.info("Actual port %d stats count: tx %d rx %d" % (port, sent, recv))
    obj.assertTrue(all_packets_sent,
                   "Packet sent does not match number sent")
    obj.assertTrue(all_packets_received,
                   "Packet received does not match number sent")

class SingleFlowStats(basic.SimpleDataPlane):
    """
    Verify flow stats are properly retrieved.

    Generate a packet
    Generate and install a flow from port 1 to 2
    Send the packet
    Send port stats request to port 1 & 2
    Verify that the packet counter has incremented
    """

    def runTest(self):
        global fs_port_map

        # TODO: set from command-line parameter
        test_timeout = 60

        of_ports = fs_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        rc = delete_all_flows(self.controller, fs_logger)
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
        fs_logger.info("Ingress " + str(ingress_port) + 
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
        fs_logger.info("Inserting flow")
        rv = self.controller.message_send(flow_mod_msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        # get initial port stats count
        initTxInPort, initRxInPort = getStats(self, ingress_port)
        initTxOutPort, initRxOutPort = getStats(self, egress_port)

        # send packet N times
        num_sends = random.randint(10,20)
        fs_logger.info("Sending " + str(num_sends) + " test packets")
        for i in range(0,num_sends):
            sendPacket(self, pkt, ingress_port, egress_port,
                       test_timeout)

        verifyStats(self, ingress_port, test_timeout, initTxInPort, initRxInPort + num_sends)
        verifyStats(self, egress_port, test_timeout, initTxOutPort + num_sends, initRxOutPort)


class MultiFlowStats(basic.SimpleDataPlane):
    """
    Verify flow stats are properly retrieved.

    Generate two packets and install two matching flows
    Send some number of packets
    Send a port stats request to get packet count
    Verify that the packet counter has incremented
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

        fs_logger.info("Ingress " + str(ingress_port) + 
                       " to egress " + str(egress_port))

        return flow_mod_msg

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

        rc = delete_all_flows(self.controller, fs_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        pkt1 = simple_tcp_packet()
        flow_mod_msg1 = self.buildFlowModMsg(pkt1, ingress_port, egress_port1)
       
        pkt2 = simple_tcp_packet(dl_src='0:7:7:7:7:7')
        flow_mod_msg2 = self.buildFlowModMsg(pkt2, ingress_port, egress_port2)
       
        fs_logger.info("Inserting flow1")
        rv = self.controller.message_send(flow_mod_msg1)
        self.assertTrue(rv != -1, "Error installing flow mod")
        fs_logger.info("Inserting flow2")
        rv = self.controller.message_send(flow_mod_msg2)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        # get initial port stats count
        initTxInPort, initRxInPort = getStats(self, ingress_port)
        initTxOutPort1, initRxOutPort1 = getStats(self, egress_port1)
        initTxOutPort2, initRxOutPort2 = getStats(self, egress_port2)

        num_pkt1s = random.randint(10,30)
        fs_logger.info("Sending " + str(num_pkt1s) + " pkt1s")
        num_pkt2s = random.randint(10,30)
        fs_logger.info("Sending " + str(num_pkt2s) + " pkt2s")
        for i in range(0,num_pkt1s):
            sendPacket(self, pkt1, ingress_port, egress_port1, test_timeout)
        for i in range(0,num_pkt2s):
            sendPacket(self, pkt2, ingress_port, egress_port2, test_timeout)

        verifyStats(self, ingress_port, test_timeout,
                    initTxInPort, initRxInPort + num_pkt1s + num_pkt2s)
        verifyStats(self, egress_port1, test_timeout,
                    initTxOutPort1 + num_pkt1s, initRxOutPort1)
        verifyStats(self, egress_port2, test_timeout,
                    initTxOutPort2 + num_pkt2s, initRxOutPort2)
