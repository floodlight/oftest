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
        in_port, out_port = openflow_ports(2)

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
        receive_pkt_check(self.dataplane, pktstr, [out_port],
                          set(openflow_ports()) - set([out_port]), self)

class OutputMultiple(base_tests.SimpleDataPlane):
    """
    Output to three ports
    """
    def runTest(self):
        ports = openflow_ports(4)
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
        receive_pkt_check(self.dataplane, pktstr, out_ports,
                          set(openflow_ports()) - set(out_ports), self)

class BaseModifyPacketTest(base_tests.SimpleDataPlane):
    """
    Base class for action tests that modify a packet
    """

    def verify_modify(self, actions, pkt, exp_pkt):
        in_port, out_port = openflow_ports(2)

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
        receive_pkt_check(self.dataplane, str(exp_pkt), [out_port],
                          set(openflow_ports()) - set([out_port]), self)

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

class SetEthDst(BaseModifyPacketTest):
    """
    Set Eth Dst address 
    """
    def runTest(self):
        actions = [ofp.action.set_field(ofp.oxm.eth_dst([0x00,0xA1,0xCD,0x53,0xC6,0x55]))]
        pkt = simple_tcp_packet()
        exp_pkt = simple_tcp_packet(eth_dst="00:A1:CD:53:C6:55")
        self.verify_modify(actions, pkt, exp_pkt)

class SetEthSrc(BaseModifyPacketTest):
    """
    Set Eth Src address 
    """
    def runTest(self):
        actions = [ofp.action.set_field(ofp.oxm.eth_src([0x00,0xA1,0xCD,0x53,0xC6,0x55]))]
        pkt = simple_tcp_packet()
        exp_pkt = simple_tcp_packet(eth_src="00:A1:CD:53:C6:55")
        self.verify_modify(actions, pkt, exp_pkt)

class SetIpDscp(BaseModifyPacketTest):
    """
    Set IP DSCP 
    """
    def runTest(self):
        actions = [ofp.action.set_field(ofp.oxm.ip_dscp(0x01))]
        pkt = simple_tcp_packet()
        exp_pkt = simple_tcp_packet(ip_tos=0x04)
        self.verify_modify(actions, pkt, exp_pkt)

class SetIpECN(BaseModifyPacketTest):
    """
    Set IP ECN
    """
    def runTest(self):
        actions = [ofp.action.set_field(ofp.oxm.ip_ecn(0x01))]
        pkt = simple_tcp_packet()
        exp_pkt = simple_tcp_packet(ip_tos=0x01)
        self.verify_modify(actions, pkt, exp_pkt)

class SetIPv4Src(BaseModifyPacketTest):
    """
    Set IPv4 srouce address
    """
    def runTest(self):
        actions = [ofp.action.set_field(ofp.oxm.ipv4_src(167772161))]
        pkt = simple_tcp_packet()
        exp_pkt = simple_tcp_packet(ip_src="10.0.0.1")
        self.verify_modify(actions, pkt, exp_pkt)

class SetIPv4Dst(BaseModifyPacketTest):
    """
    Set IPv4 destination address
    """
    def runTest(self):
        actions = [ofp.action.set_field(ofp.oxm.ipv4_dst(167772161))]
        pkt = simple_tcp_packet()
        exp_pkt = simple_tcp_packet(ip_dst="10.0.0.1")
        self.verify_modify(actions, pkt, exp_pkt)

class SetTCPSrc(BaseModifyPacketTest):
    """
    Set TCP source port 
    """
    def runTest(self):
        actions = [ofp.action.set_field(ofp.oxm.tcp_src(800))]
        pkt = simple_tcp_packet()
        exp_pkt = simple_tcp_packet(tcp_sport=800)
        self.verify_modify(actions, pkt, exp_pkt)

class SetTCPDst(BaseModifyPacketTest):
    """
    Set TCP destination port 
    """
    def runTest(self):
        actions = [ofp.action.set_field(ofp.oxm.tcp_dst(800))]
        pkt = simple_tcp_packet()
        exp_pkt = simple_tcp_packet(tcp_dport=800)
        self.verify_modify(actions, pkt, exp_pkt)

class SetUDPSrc(BaseModifyPacketTest):
    """
    Set UDP source port 
    """
    def runTest(self):
        actions = [ofp.action.set_field(ofp.oxm.udp_src(800))]
        pkt = simple_udp_packet()
        exp_pkt = simple_udp_packet(udp_sport=800)
        self.verify_modify(actions, pkt, exp_pkt)

class SetUDPDst(BaseModifyPacketTest):
    """
    Set UDP destination port 
    """
    def runTest(self):
        actions = [ofp.action.set_field(ofp.oxm.udp_dst(800))]
        pkt = simple_udp_packet()
        exp_pkt = simple_udp_packet(udp_dport=800)
        self.verify_modify(actions, pkt, exp_pkt)

class SetIPv6Src(BaseModifyPacketTest):
    """
    Set IPv6 source address 
    """
    def runTest(self):
        actions = [ofp.action.set_field(ofp.oxm.ipv6_src("\x20\x01\xab\xb1\x34\x56\xbc\xcb\x00\x00\x00\x00\x03\x70\x73\x36"))]
        pkt = simple_tcpv6_packet()
        exp_pkt = simple_tcpv6_packet(ipv6_src="2001:abb1:3456:bccb:0000:0000:0370:7336")
        self.verify_modify(actions, pkt, exp_pkt)

class SetIPv6Dst(BaseModifyPacketTest):
    """
    Set IPv6 destination address 
    """
    def runTest(self):
        actions = [ofp.action.set_field(ofp.oxm.ipv6_dst("\x20\x01\xab\xb1\x34\x56\xbc\xcb\x00\x00\x00\x00\x03\x70\x73\x36"))]
        pkt = simple_tcpv6_packet()
        exp_pkt = simple_tcpv6_packet(ipv6_dst="2001:abb1:3456:bccb:0000:0000:0370:7336")
        self.verify_modify(actions, pkt, exp_pkt)

class SetIPv6Flabel(BaseModifyPacketTest):
    """
    Set IPv6 Flabel 
    """
    def runTest(self):
        actions = [ofp.action.set_field(ofp.oxm.ipv6_flabel(0))]
        pkt = simple_tcpv6_packet()
        exp_pkt = simple_tcpv6_packet(ipv6_fl=0)
        self.verify_modify(actions, pkt, exp_pkt)

class SetNwTTL(BaseModifyPacketTest):
    """
    Set Nw TTL 
    """
    def runTest(self):
        actions = [ofp.action.set_nw_ttl(10)]
        pkt = simple_tcp_packet()
        exp_pkt = simple_tcp_packet(ip_ttl=10)
        self.verify_modify(actions, pkt, exp_pkt)

class DecNwTTL(BaseModifyPacketTest):
    """
    Decrement Nw TTL 
    """
    def runTest(self):
        actions = [ofp.action.dec_nw_ttl()]
        pkt = simple_tcp_packet(ip_ttl=10)
        exp_pkt = simple_tcp_packet(ip_ttl=9)
        self.verify_modify(actions, pkt, exp_pkt)
