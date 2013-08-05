# Distributed under the OpenFlow Software License (see LICENSE)
# Copyright (c) 2010 The Board of Trustees of The Leland Stanford Junior University
# Copyright (c) 2012, 2013 Big Switch Networks, Inc.
"""
Action test cases

These tests check the behavior of each type of action. The matches used are
exact-match, to satisfy the OXM prerequisites of the set-field actions.
These tests use a single apply-actions instruction.
"""

import logging

from oftest import config
import oftest.base_tests as base_tests
import ofp
from loxi.pp import pp

from oftest.testutils import *
from oftest.parse import parse_ipv6

class Output(base_tests.SimpleDataPlane):
    """
    Output to a single port
    """
    def runTest(self):
        ports = sorted(config["port_map"].keys())
        in_port = ports[0]
        out_port = ports[1]

        actions = [ofp.action.output(out_port)]

        pkt = simple_tcp_packet()

        logging.info("Running actions test for %s", pp(actions))

        delete_all_flows(self.controller)

        logging.info("Inserting flow")
        request = ofp.message.flow_add(
                table_id=0,
                match=packet_to_flow_match(self, pkt),
                instructions=[
                    ofp.instruction.apply_actions(actions)],
                buffer_id=ofp.OFP_NO_BUFFER,
                priority=1000)
        self.controller.message_send(request)

        do_barrier(self.controller)

        pktstr = str(pkt)

        logging.info("Sending packet, expecting output to port %d", out_port)
        self.dataplane.send(in_port, pktstr)
        receive_pkt_check(self.dataplane, pktstr, [out_port], set(ports) - set([out_port]), self)

class OutputMultiple(base_tests.SimpleDataPlane):
    """
    Output to three ports
    """
    def runTest(self):
        ports = sorted(config["port_map"].keys())
        in_port = ports[0]
        out_ports = ports[1:4]

        actions = [ofp.action.output(x) for x in out_ports]

        pkt = simple_tcp_packet()

        logging.info("Running actions test for %s", pp(actions))

        delete_all_flows(self.controller)

        logging.info("Inserting flow")
        request = ofp.message.flow_add(
                table_id=0,
                match=packet_to_flow_match(self, pkt),
                instructions=[
                    ofp.instruction.apply_actions(actions)],
                buffer_id=ofp.OFP_NO_BUFFER,
                priority=1000)
        self.controller.message_send(request)

        do_barrier(self.controller)

        pktstr = str(pkt)

        logging.info("Sending packet, expecting output to ports %r", out_ports)
        self.dataplane.send(in_port, pktstr)
        receive_pkt_check(self.dataplane, pktstr, out_ports, set(ports) - set(out_ports), self)

class BaseModifyPacketTest(base_tests.SimpleDataPlane):
    """
    Base class for action tests that modify a packet
    """

    def verify_modify(self, actions, pkt, exp_pkt):
        ports = sorted(config["port_map"].keys())
        in_port = ports[0]
        out_port = ports[1]

        actions = actions + [ofp.action.output(out_port)]

        logging.info("Running actions test for %s", pp(actions))

        delete_all_flows(self.controller)

        logging.info("Inserting flow")
        request = ofp.message.flow_add(
                table_id=0,
                match=packet_to_flow_match(self, pkt),
                instructions=[
                    ofp.instruction.apply_actions(actions)],
                buffer_id=ofp.OFP_NO_BUFFER,
                priority=1000)
        self.controller.message_send(request)

        do_barrier(self.controller)

        logging.info("Sending packet, expecting output to port %d", out_port)
        self.dataplane.send(in_port, str(pkt))
        receive_pkt_check(self.dataplane, str(exp_pkt), [out_port], set(ports) - set([out_port]), self)

class PushVlan(BaseModifyPacketTest):
    """
    Push a vlan tag (vid=0, pcp=0)
    """
    def runTest(self):
        actions = [ofp.action.push_vlan(ethertype=0x8100)]
        pkt = simple_tcp_packet()
        exp_pkt = simple_tcp_packet(dl_vlan_enable=True, pktlen=104)
        self.verify_modify(actions, pkt, exp_pkt)

class PopVlan(BaseModifyPacketTest):
    """
    Pop a vlan tag
    """
    def runTest(self):
        actions = [ofp.action.pop_vlan()]
        pkt = simple_tcp_packet(dl_vlan_enable=True, pktlen=104)
        exp_pkt = simple_tcp_packet()
        self.verify_modify(actions, pkt, exp_pkt)

class SetVlanVid(BaseModifyPacketTest):
    """
    Set the vlan vid
    """
    def runTest(self):
        actions = [ofp.action.set_field(ofp.oxm.vlan_vid(2))]
        pkt = simple_tcp_packet(dl_vlan_enable=True, vlan_vid=1)
        exp_pkt = simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2)
        self.verify_modify(actions, pkt, exp_pkt)

class SetVlanPcp(BaseModifyPacketTest):
    """
    Set the vlan priority
    """
    def runTest(self):
        actions = [ofp.action.set_field(ofp.oxm.vlan_pcp(2))]
        pkt = simple_tcp_packet(dl_vlan_enable=True, vlan_pcp=1)
        exp_pkt = simple_tcp_packet(dl_vlan_enable=True, vlan_pcp=2)
        self.verify_modify(actions, pkt, exp_pkt)
