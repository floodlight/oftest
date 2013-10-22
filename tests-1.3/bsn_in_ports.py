# Distributed under the OpenFlow Software License (see LICENSE)
# Copyright (c) 2012, 2013 Big Switch Networks, Inc.
"""
Test the bsn_in_ports_128 OXM, which enables the controller to specify a bitmap
of allowed input ports.
"""

import logging

from oftest import config
import oftest.base_tests as base_tests
import ofp
import oftest.packet as scapy

from oftest.testutils import *

class MatchInPorts128(base_tests.SimpleDataPlane):
    """
    Match on ingress port bitmap
    """
    def runTest(self):
        in_port1, in_port2, out_port, bad_port = openflow_ports(4)

        # See the loxigen bsn_in_ports input file for encoding details
        match = ofp.match([
            ofp.oxm.bsn_in_ports_128_masked(set(), set(range(0,128)) - set((in_port1,in_port2)))
        ])

        pkt = simple_tcp_packet()

        logging.info("Running match test for %s", match.show())

        delete_all_flows(self.controller)

        logging.info("Inserting flow sending matching packets to port %d", out_port)
        request = ofp.message.flow_add(
                table_id=0,
                match=match,
                instructions=[
                    ofp.instruction.apply_actions(
                        actions=[
                            ofp.action.output(
                                port=out_port,
                                max_len=ofp.OFPCML_NO_BUFFER)])],
                buffer_id=ofp.OFP_NO_BUFFER,
                priority=1000)
        self.controller.message_send(request)

        logging.info("Inserting match-all flow sending packets to controller")
        request = ofp.message.flow_add(
            table_id=0,
            instructions=[
                ofp.instruction.apply_actions(
                    actions=[
                        ofp.action.output(
                            port=ofp.OFPP_CONTROLLER,
                            max_len=ofp.OFPCML_NO_BUFFER)])],
            buffer_id=ofp.OFP_NO_BUFFER,
            priority=1)
        self.controller.message_send(request)

        do_barrier(self.controller)

        pktstr = str(pkt)

        logging.info("Sending packet on matching ingress port, expecting output to port %d", out_port)
        self.dataplane.send(in_port1, pktstr)
        verify_packets(self, pktstr, [out_port])

        logging.info("Sending packet on other matching ingress port, expecting output to port %d", out_port)
        self.dataplane.send(in_port2, pktstr)
        verify_packets(self, pktstr, [out_port])

        logging.info("Sending packet on non-matching ingress port, expecting packet-in")
        self.dataplane.send(bad_port, pktstr)
        verify_packet_in(self, pktstr, bad_port, ofp.OFPR_ACTION)
