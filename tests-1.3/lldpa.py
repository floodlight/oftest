# Distributed under the OpenFlow Software License (see LICENSE)
# Copyright (c) 2010 The Board of Trustees of The Leland Stanford Junior University
# Copyright (c) 2012, 2013 Big Switch Networks, Inc.
# Copyright (c) 2012, 2013 CPqD
# Copyright (c) 2012, 2013 Ericsson
"""
Basic test cases

Test cases in other modules depend on this functionality.
"""

import logging

from oftest import config
import oftest.base_tests as base_tests
import ofp
import struct
import time

from oftest.testutils import *

def simple_lldp_tx_packet(pktlen=128,
                          eth_dst=(0x55,0x16,0xc7,0x01,0x02,0x03),
                          eth_src=(0x55,0x16,0xc7,0xff,0xff,0x07), 
                          eth_type=0x88cc
                         ):                     
    """
    NOTE:
    """
    pkt = struct.pack("!BBBBBBBBBBBBH", 
                      eth_dst[0], eth_dst[1], eth_dst[2], eth_dst[3], eth_dst[4], eth_dst[5],
                      eth_src[0], eth_src[1], eth_src[2], eth_src[3], eth_src[4], eth_src[5], 
                      eth_type) 

    return pkt.ljust(pktlen, "\x00")

def simple_lldp_rx_packet(pktlen=64,
                          eth_dst=(0x55,0x16,0xc7,0xff,0xff,0x07), 
                          eth_src=(0x55,0x16,0xc7,0x04,0x05,0x06),
                          eth_type=0x88cc
                         ):                     
    """
    NOTE: swap src and dst as compare to tx
    """
    pkt = struct.pack("!BBBBBBBBBBBBH", 
                      eth_dst[0], eth_dst[1], eth_dst[2], eth_dst[3], eth_dst[4], eth_dst[5],
                      eth_src[0], eth_src[1], eth_src[2], eth_src[3], eth_src[4], eth_src[5], 
                      eth_type) 

    return pkt.ljust(pktlen, "\x00")

@group('smoke')
class SetTXRequest(base_tests.SimpleDataPlane):
    """
    Test TX Req :enable
    Test TX Req :disable
    """
    def runTest(self):
        #Set up openflow ports
        port1, port2=openflow_ports(2)

        #Set up data
        pkt_data = str(simple_lldp_tx_packet())

        #Test 1: TX Req enable
        request = ofp.message.bsn_pdu_tx_request(
            tx_interval_ms=1000,
            port_no=port1,
            data=pkt_data) #'LLDPA TX_REQ DUMMY')

        response, _ = self.controller.transact(request)
        self.assertTrue(response is not None, "Did not get TX reply")
        self.assertIsInstance(response, ofp.message.bsn_pdu_tx_reply)
        self.assertEquals(response.status, 0)
        self.assertEquals(response.port_no, port1)
        self.assertEqual(request.xid, response.xid, 'response xid != request xid')

        #add a flow in the flowtable to match against dst
        request = ofp.message.flow_add(
                table_id=test_param_get("table", 0),
                match = ofp.match([
                        ofp.oxm.eth_dst([0x55, 0x16, 0xc7, 0x01, 0x02, 0x03])]),
                instructions=[
                    ofp.instruction.apply_actions(
                        actions=[
                            ofp.action.output(
                                port=ofp.OFPP_CONTROLLER,
                                max_len=ofp.OFPCML_NO_BUFFER)])],
                buffer_id=ofp.OFP_NO_BUFFER,
                priority=1000)
        self.controller.message_send(request)
        do_barrier(self.controller)

        #Test 1a: verify 1st packet (immediately send)
        verify_packet(self, pkt_data, port1)

        #Test 1b: verify 2nd packet (periodically called)
        verify_packet(self, pkt_data, port1)

        #Test 2: Disable TX using interval_ms = 0;
        request = ofp.message.bsn_pdu_tx_request(
            tx_interval_ms=0,
            port_no=port1)

        response, _ = self.controller.transact(request)
        self.assertTrue(response is not None, "Did not get TX reply")
        self.assertIsInstance(response, ofp.message.bsn_pdu_tx_reply)
        self.assertEquals(response.status, 0)
        self.assertEquals(response.port_no, port1)
        self.assertEqual(request.xid, response.xid, 'response xid != request xid')

class SetRXRequest(base_tests.SimpleDataPlane):
    """
    Test RX Req
    """
    def runTest(self):
        #Set up openflow ports
        port1, port2=openflow_ports(2)

        #Set up rx_pkt
        pkt_data = str(simple_lldp_rx_packet())

        #This pkt will be fwd to controller
        pkt_data_fwd = str(simple_lldp_tx_packet())

        #Test 1: Create a request
        request = ofp.message.bsn_pdu_rx_request(
            timeout_ms=500,
            port_no=port1,
            data=pkt_data)

        response, _ = self.controller.transact(request)
        self.assertTrue(response is not None, "Did not get rx reply")
        self.assertIsInstance(response, ofp.message.bsn_pdu_rx_reply)
        self.assertEquals(response.status, 0)
        self.assertEquals(response.port_no, port1)
        self.assertEqual(request.xid, response.xid, 'response xid != request xid')

        #add a flow in the flowtable to match against eth_type
        request = ofp.message.flow_add(
                table_id=test_param_get("table", 0),
                match = ofp.match([
                        #ofp.oxm.eth_dst([0x01, 0x80, 0xc2, 0x00, 0x00, 0x02])]),
                         ofp.oxm.eth_type(0x88cc)]),
                instructions=[
                    ofp.instruction.apply_actions(
                        actions=[
                            ofp.action.output(
                                port=ofp.OFPP_CONTROLLER,
                                max_len=ofp.OFPCML_NO_BUFFER)])],
                buffer_id=ofp.OFP_NO_BUFFER,
                priority=1000)
        self.controller.message_send(request)
        do_barrier(self.controller)

        #Test1: Send pkt to LLDPA: Won't see timeout
        self.dataplane.send(port1, pkt_data)

        #Test2: Wrong pkt, controller should receive it
        self.dataplane.send(port1, pkt_data_fwd)
        verify_packet_in(self, pkt_data_fwd, port1, ofp.OFPR_ACTION)

        #Test3: Check Async Timeout message
        response, pkt = self.controller.poll(exp_msg=ofp.OFPT_EXPERIMENTER)
        self.assertIsInstance(response, ofp.message.bsn_pdu_rx_timeout);
        self.assertEquals(response.port_no, port1)

        #Test4: Disable with interval_ms = 0;
        request = ofp.message.bsn_pdu_rx_request(
            timeout_ms=0,
            port_no=port1)
        response, _ = self.controller.transact(request)
        self.assertTrue(response is not None, "Did not get rx reply")
        self.assertIsInstance(response, ofp.message.bsn_pdu_rx_reply)
        self.assertEquals(response.status, 0)
        self.assertEquals(response.port_no, port1)
        self.assertEqual(request.xid, response.xid, 'response xid != request xid')

