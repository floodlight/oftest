# Distributed under the OpenFlow Software License (see LICENSE)
# Copyright (c) 2010 The Board of Trustees of The Leland Stanford Junior University
# Copyright (c) 2012, 2013 Big Switch Networks, Inc.
"""
Flow match test cases

These tests check the behavior of each match field. The only action used is a
single output.
"""

import logging

from oftest import config
import oftest.base_tests as base_tests
import ofp
import scapy.all as scapy

from oftest.testutils import *

class MatchTest(base_tests.SimpleDataPlane):
    """
    Base class for match tests
    """

    def verify_match(self, match, matching, nonmatching):
        """
        Verify matching behavior

        Checks that all the packets in 'matching' match 'match', and that
        the packets in 'nonmatching' do not.

        'match' is a LOXI match object. 'matching' and 'nonmatching' are
        dicts mapping from string names (used in log messages) to string
        packet data.
        """
        ports = sorted(config["port_map"].keys())
        in_port = ports[0]
        out_port = ports[1]

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

        for name, pkt in matching.items():
            logging.info("Sending matching packet %s, expecting output to port %d", repr(name), out_port)
            pktstr = str(pkt)
            self.dataplane.send(in_port, pktstr)
            receive_pkt_verify(self, [out_port], pktstr, in_port)

        for name, pkt in nonmatching.items():
            logging.info("Sending non-matching packet %s, expecting packet-in", repr(name))
            pktstr = str(pkt)
            self.dataplane.send(in_port, pktstr)
            verify_packet_in(self, pktstr, in_port, ofp.OFPR_ACTION)

# Does not use MatchTest because the ingress port is not a packet field
class InPort(base_tests.SimpleDataPlane):
    """
    Match on ingress port
    """
    def runTest(self):
        ports = sorted(config["port_map"].keys())
        in_port = ports[0]
        out_port = ports[1]
        bad_port = ports[2]

        match = ofp.match([
            ofp.oxm.in_port(in_port)
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
        self.dataplane.send(in_port, pktstr)
        receive_pkt_verify(self, [out_port], pktstr, in_port)

        logging.info("Sending packet on non-matching ingress port, expecting packet-in")
        self.dataplane.send(bad_port, pktstr)
        verify_packet_in(self, pktstr, bad_port, ofp.OFPR_ACTION)

class EthDst(MatchTest):
    """
    Match on ethernet destination
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_dst([0x00, 0x01, 0x02, 0x03, 0x04, 0x05])
        ])

        matching = {
            "correct": simple_tcp_packet(eth_dst='00:01:02:03:04:05'),
        }

        nonmatching = {
            "incorrect": simple_tcp_packet(eth_dst='00:01:02:03:04:06'),
            "multicast": simple_tcp_packet(eth_dst='01:01:02:03:04:05'),
            "local": simple_tcp_packet(eth_dst='02:01:02:03:04:05'),
        }

        self.verify_match(match, matching, nonmatching)

class EthDstBroadcast(MatchTest):
    """
    Match on ethernet destination (broadcast)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_dst([0xff, 0xff, 0xff, 0xff, 0xff, 0xff])
        ])

        matching = {
            "ff:ff:ff:ff:ff:ff": simple_tcp_packet(eth_dst='ff:ff:ff:ff:ff:ff'),
        }

        nonmatching = {
            "fd:ff:ff:ff:ff:ff": simple_tcp_packet(eth_dst='fd:ff:ff:ff:ff:ff'),
            "fe:ff:ff:ff:ff:ff": simple_tcp_packet(eth_dst='fe:ff:ff:ff:ff:ff'),
            "ff:fe:ff:ff:ff:ff": simple_tcp_packet(eth_dst='ff:fe:ff:ff:ff:ff'),
        }

        self.verify_match(match, matching, nonmatching)

class EthDstMulticast(MatchTest):
    """
    Match on ethernet destination (IPv4 multicast)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_dst([0x01, 0x00, 0x5e, 0xed, 0x99, 0x02])
        ])

        matching = {
            "correct": simple_tcp_packet(eth_dst='01:00:5e:ed:99:02'),
        }

        nonmatching = {
            "incorrect": simple_tcp_packet(eth_dst='01:00:5e:ed:99:03'),
            "unicast": simple_tcp_packet(eth_dst='00:00:5e:ed:99:02'),
            "local": simple_tcp_packet(eth_dst='03:00:5e:ed:99:02'),
        }

        self.verify_match(match, matching, nonmatching)

class EthDstMasked(MatchTest):
    """
    Match on ethernet destination (masked)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_dst_masked([0x00, 0x01, 0x02, 0x03, 0x04, 0x05],
                                   [0x00, 0xff, 0xff, 0x0f, 0xff, 0xff])
        ])

        matching = {
            "00:01:02:03:04:05": simple_tcp_packet(eth_dst='00:01:02:03:04:05'),
            "ff:01:02:f3:04:05": simple_tcp_packet(eth_dst='ff:01:02:f3:04:05'),
        }

        nonmatching = {
            "00:02:02:03:04:05": simple_tcp_packet(eth_dst='00:02:02:03:04:05'),
            "00:01:02:07:04:05": simple_tcp_packet(eth_dst='00:01:02:07:04:05'),
        }

        self.verify_match(match, matching, nonmatching)

class EthSrc(MatchTest):
    """
    Match on ethernet source
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_src([0,1,2,3,4,5])
        ])

        matching = {
            "correct": simple_tcp_packet(eth_src='00:01:02:03:04:05'),
        }

        nonmatching = {
            "incorrect": simple_tcp_packet(eth_src='00:01:02:03:04:06'),
            "multicast": simple_tcp_packet(eth_src='01:01:02:03:04:05'),
            "local": simple_tcp_packet(eth_src='02:01:02:03:04:05'),
        }

        self.verify_match(match, matching, nonmatching)

class EthSrcMasked(MatchTest):
    """
    Match on ethernet source (masked)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_src_masked([0x00, 0x01, 0x02, 0x03, 0x04, 0x05],
                                   [0x00, 0xff, 0xff, 0x0f, 0xff, 0xff])
        ])

        matching = {
            "00:01:02:03:04:05": simple_tcp_packet(eth_src='00:01:02:03:04:05'),
            "ff:01:02:f3:04:05": simple_tcp_packet(eth_src='ff:01:02:f3:04:05'),
        }

        nonmatching = {
            "00:02:02:03:04:05": simple_tcp_packet(eth_src='00:02:02:03:04:05'),
            "00:01:02:07:04:05": simple_tcp_packet(eth_src='00:01:02:07:04:05'),
        }

        self.verify_match(match, matching, nonmatching)

class EthTypeIPv4(MatchTest):
    """
    Match on ethertype (IPv4)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0800)
        ])

        snap_pkt = \
            scapy.Ether(dst='00:01:02:03:04:05', src='00:06:07:08:09:0a', type=48)/ \
            scapy.LLC(dsap=0xaa, ssap=0xaa, ctrl=0x03)/ \
            scapy.SNAP(OUI=0x000000, code=0x0800)/ \
            scapy.IP(src='192.168.0.1', dst='192.168.0.2', proto=6)/ \
            scapy.TCP(sport=1234, dport=80)

        llc_pkt = \
            scapy.Ether(dst='00:01:02:03:04:05', src='00:06:07:08:09:0a', type=17)/ \
            scapy.LLC(dsap=0xaa, ssap=0xab, ctrl=0x03)

        matching = {
            "ipv4/tcp": simple_tcp_packet(),
            "ipv4/udp": simple_udp_packet(),
            "ipv4/icmp": simple_icmp_packet(),
            "vlan tagged": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2, vlan_pcp=3),
            "llc/snap": snap_pkt,
        }

        nonmatching = {
            "arp": simple_arp_packet(),
            "llc": llc_pkt,
            "ipv6/tcp": simple_tcpv6_packet(),
        }

        self.verify_match(match, matching, nonmatching)

class EthTypeIPv6(MatchTest):
    """
    Match on ethertype (IPv6)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x86dd)
        ])

        matching = {
            "ipv6/tcp": simple_tcpv6_packet(),
            "ipv6/udp": simple_udpv6_packet(),
            "ipv6/icmp": simple_icmpv6_packet(),
            "vlan tagged": simple_tcpv6_packet(vlan_vid=2, vlan_pcp=3),
        }

        nonmatching = {
            "ipv4/tcp": simple_tcp_packet(),
            "arp": simple_arp_packet(),
        }

        self.verify_match(match, matching, nonmatching)

class EthTypeARP(MatchTest):
    """
    Match on ethertype (ARP)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0806)
        ])

        matching = {
            "arp": simple_arp_packet(),
            # TODO vlan tagged
        }

        nonmatching = {
            "ipv4/tcp": simple_tcp_packet(),
            "ipv6/tcp": simple_tcpv6_packet(),
        }

        self.verify_match(match, matching, nonmatching)

class EthTypeNone(MatchTest):
    """
    Match on no ethertype (IEEE 802.3 without SNAP header)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x05ff)
        ])

        snap_pkt = \
            scapy.Ether(dst='00:01:02:03:04:05', src='00:06:07:08:09:0a', type=48)/ \
            scapy.LLC(dsap=0xaa, ssap=0xaa, ctrl=0x03)/ \
            scapy.SNAP(OUI=0x000000, code=0x0800)/ \
            scapy.IP(src='192.168.0.1', dst='192.168.0.2', proto=6)/ \
            scapy.TCP(sport=1234, dport=80)

        llc_pkt = \
            scapy.Ether(dst='00:01:02:03:04:05', src='00:06:07:08:09:0a', type=17)/ \
            scapy.LLC(dsap=0xaa, ssap=0xab, ctrl=0x03)

        matching = {
            "llc": llc_pkt,
        }

        nonmatching = {
            "ipv4/tcp": simple_tcp_packet(),
            "ipv6/tcp": simple_tcpv6_packet(),
            "llc/snap": snap_pkt,
        }

        self.verify_match(match, matching, nonmatching)

class VlanExact(MatchTest):
    """
    Match on VLAN VID and PCP
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.vlan_vid(ofp.OFPVID_PRESENT|2),
            ofp.oxm.vlan_pcp(3),
        ])

        matching = {
            "vid=2 pcp=3": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2, vlan_pcp=3),
        }

        nonmatching = {
            "vid=4 pcp=2": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=4, vlan_pcp=2),
            "vid=4 pcp=3": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=4, vlan_pcp=2),
            "vid=2 pcp=2": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=4, vlan_pcp=2),
            "vid=0 pcp=3": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=4, vlan_pcp=2),
            "vid=2 pcp=0": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=4, vlan_pcp=2),
            "no vlan tag": simple_tcp_packet(),
        }

        self.verify_match(match, matching, nonmatching)

class VlanVID(MatchTest):
    """
    Match on VLAN VID
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.vlan_vid(ofp.OFPVID_PRESENT|2),
        ])

        matching = {
            "vid=2 pcp=3": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2, vlan_pcp=3),
            "vid=2 pcp=7": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2, vlan_pcp=7),
        }

        nonmatching = {
            "vid=4 pcp=2": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=4, vlan_pcp=2),
            "no vlan tag": simple_tcp_packet(),
        }

        self.verify_match(match, matching, nonmatching)

class VlanVIDMasked(MatchTest):
    """
    Match on VLAN VID (masked)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.vlan_vid_masked(ofp.OFPVID_PRESENT|3, ofp.OFPVID_PRESENT|3),
        ])

        matching = {
            "vid=3 pcp=2": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=3, vlan_pcp=2),
            "vid=7 pcp=2": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=7, vlan_pcp=2),
            "vid=11 pcp=2": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=11, vlan_pcp=2),
        }

        nonmatching = {
            "vid=0 pcp=2": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=0, vlan_pcp=2),
            "vid=1 pcp=2": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=1, vlan_pcp=2),
            "vid=2 pcp=2": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2, vlan_pcp=2),
            "vid=4 pcp=2": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=4, vlan_pcp=2),
            "no vlan tag": simple_tcp_packet(),
        }

        self.verify_match(match, matching, nonmatching)

class VlanPCP(MatchTest):
    """
    Match on VLAN PCP (VID matched)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.vlan_vid(ofp.OFPVID_PRESENT|2),
            ofp.oxm.vlan_pcp(3),
        ])

        matching = {
            "vid=2 pcp=3": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2, vlan_pcp=3),
        }

        nonmatching = {
            "vid=2 pcp=4": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2, vlan_pcp=4),
            "no vlan tag": simple_tcp_packet(),
        }

        self.verify_match(match, matching, nonmatching)

@nonstandard
class VlanPCPMasked(MatchTest):
    """
    Match on VLAN PCP (masked, VID matched)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.vlan_vid(ofp.OFPVID_PRESENT|2),
            ofp.oxm.vlan_pcp_masked(3, 3),
        ])

        matching = {
            "vid=2 pcp=3": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2, vlan_pcp=3),
            "vid=2 pcp=7": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2, vlan_pcp=7),
        }

        nonmatching = {
            "vid=2 pcp=1": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2, vlan_pcp=1),
            "vid=2 pcp=2": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2, vlan_pcp=2),
            "vid=2 pcp=4": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2, vlan_pcp=4),
            "vid=2 pcp=5": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2, vlan_pcp=5),
            "vid=2 pcp=6": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2, vlan_pcp=6),
            "no vlan tag": simple_tcp_packet(),
        }

        self.verify_match(match, matching, nonmatching)

class VlanPCPAnyVID(MatchTest):
    """
    Match on VLAN PCP (VID present)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.vlan_vid_masked(ofp.OFPVID_PRESENT, ofp.OFPVID_PRESENT),
            ofp.oxm.vlan_pcp(3),
        ])

        matching = {
            "vid=2 pcp=3": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2, vlan_pcp=3),
            "vid=0 pcp=3": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=0, vlan_pcp=3),
        }

        nonmatching = {
            "vid=2 pcp=4": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2, vlan_pcp=4),
            "no vlan tag": simple_tcp_packet(),
        }

        self.verify_match(match, matching, nonmatching)

class VlanPresent(MatchTest):
    """
    Match on any VLAN tag (but must be present)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.vlan_vid_masked(ofp.OFPVID_PRESENT, ofp.OFPVID_PRESENT),
        ])

        matching = {
            "vid=2 pcp=3": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2, vlan_pcp=3),
            "vid=0 pcp=7": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=0, vlan_pcp=7),
            "vid=2 pcp=0": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2, vlan_pcp=0),
        }

        nonmatching = {
            "no vlan tag": simple_tcp_packet()
        }

        self.verify_match(match, matching, nonmatching)

class VlanAbsent(MatchTest):
    """
    Match on absent VLAN tag
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.vlan_vid(ofp.OFPVID_NONE),
        ])

        matching = {
            "no vlan tag": simple_tcp_packet()
        }

        nonmatching = {
            "vid=2 pcp=3": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2, vlan_pcp=3),
            "vid=0 pcp=7": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=0, vlan_pcp=7),
            "vid=2 pcp=0": simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2, vlan_pcp=0),
        }

        self.verify_match(match, matching, nonmatching)

class IPv4Dscp(MatchTest):
    """
    Match on ipv4 dscp
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0800),
            ofp.oxm.ip_dscp(4),
        ])

        matching = {
            "dscp=4 ecn=0": simple_tcp_packet(ip_tos=0x10),
            "dscp=4 ecn=3": simple_tcp_packet(ip_tos=0x13),
        }

        nonmatching = {
            "dscp=5 ecn=0": simple_tcp_packet(ip_tos=0x14),
        }

        self.verify_match(match, matching, nonmatching)

class IPv6Dscp(MatchTest):
    """
    Match on ipv6 dscp
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x86dd),
            ofp.oxm.ip_dscp(4),
        ])

        matching = {
            "dscp=4 ecn=0": simple_tcpv6_packet(ipv6_tc=0x10),
            "dscp=4 ecn=3": simple_tcpv6_packet(ipv6_tc=0x13),
        }

        nonmatching = {
            "dscp=5 ecn=0": simple_tcpv6_packet(ipv6_tc=0x14),
        }

        self.verify_match(match, matching, nonmatching)

class IPv4Ecn(MatchTest):
    """
    Match on ipv4 ecn
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0800),
            ofp.oxm.ip_ecn(2),
        ])

        matching = {
            "dscp=4 ecn=2": simple_tcp_packet(ip_tos=0x12),
            "dscp=6 ecn=2": simple_tcp_packet(ip_tos=0x1a),
        }

        nonmatching = {
            "dscp=4 ecn=0": simple_tcp_packet(ip_tos=0x10),
            "dscp=4 ecn=3": simple_tcp_packet(ip_tos=0x13),
        }

        self.verify_match(match, matching, nonmatching)

class IPv6Ecn(MatchTest):
    """
    Match on ipv6 ecn
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x86dd),
            ofp.oxm.ip_ecn(2),
        ])

        matching = {
            "dscp=4 ecn=2": simple_tcpv6_packet(ipv6_tc=0x12),
            "dscp=6 ecn=2": simple_tcpv6_packet(ipv6_tc=0x1a),
        }

        nonmatching = {
            "dscp=4 ecn=0": simple_tcpv6_packet(ipv6_tc=0x10),
            "dscp=4 ecn=3": simple_tcpv6_packet(ipv6_tc=0x13),
        }

        self.verify_match(match, matching, nonmatching)

class IPv4ProtoTCP(MatchTest):
    """
    Match on ipv4 protocol field (TCP)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0800),
            ofp.oxm.ip_proto(6),
        ])

        matching = {
            "tcp": simple_tcp_packet(),
        }

        nonmatching = {
            "udp": simple_udp_packet(),
            "icmp": simple_icmp_packet(),
        }

        self.verify_match(match, matching, nonmatching)

class IPv6ProtoTCP(MatchTest):
    """
    Match on ipv6 protocol field (TCP)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x86dd),
            ofp.oxm.ip_proto(6),
        ])

        matching = {
            "tcp": simple_tcpv6_packet(),
        }

        nonmatching = {
            "udp": simple_udpv6_packet(),
            "icmp": simple_icmpv6_packet(),
        }

        self.verify_match(match, matching, nonmatching)

class IPv4ProtoUDP(MatchTest):
    """
    Match on ipv4 protocol field (UDP)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0800),
            ofp.oxm.ip_proto(17),
        ])

        matching = {
            "udp": simple_udp_packet(),
        }

        nonmatching = {
            "tcp": simple_tcp_packet(),
            "icmp": simple_icmp_packet(),
        }

        self.verify_match(match, matching, nonmatching)

class IPv6ProtoUDP(MatchTest):
    """
    Match on ipv6 protocol field (UDP)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x86dd),
            ofp.oxm.ip_proto(17),
        ])

        matching = {
            "udp": simple_udpv6_packet(),
        }

        nonmatching = {
            "tcp": simple_tcpv6_packet(),
            "icmp": simple_icmpv6_packet(),
        }

        self.verify_match(match, matching, nonmatching)

class IPv4ProtoICMP(MatchTest):
    """
    Match on ipv4 protocol field (ICMP)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0800),
            ofp.oxm.ip_proto(1),
        ])

        matching = {
            "icmp": simple_icmp_packet(),
        }

        nonmatching = {
            "tcp": simple_tcp_packet(),
            "udp": simple_udp_packet(),
        }

        self.verify_match(match, matching, nonmatching)

class IPv6ProtoICMP(MatchTest):
    """
    Match on ipv6 protocol field (ICMP)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x86dd),
            ofp.oxm.ip_proto(58),
        ])

        matching = {
            "icmp": simple_icmpv6_packet(),
        }

        nonmatching = {
            "tcp": simple_tcpv6_packet(),
            "udp": simple_udpv6_packet(),
        }

        self.verify_match(match, matching, nonmatching)

class IPv4Src(MatchTest):
    """
    Match on ipv4 source address
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0800),
            ofp.oxm.ipv4_src(0xc0a80001), # 192.168.0.1
        ])

        matching = {
            "192.168.0.1": simple_tcp_packet(ip_src='192.168.0.1'),
        }

        nonmatching = {
            "192.168.0.2": simple_tcp_packet(ip_src='192.168.0.2'),
            "255.255.255.255": simple_tcp_packet(ip_src='255.255.255.255'),
        }

        self.verify_match(match, matching, nonmatching)

class IPv4SrcSubnetMasked(MatchTest):
    """
    Match on ipv4 source address (subnet masked)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0800),
            # 192.168.0.0/20 (255.255.240.0)
            ofp.oxm.ipv4_src_masked(0xc0a80000, 0xfffff000),
        ])

        matching = {
            "192.168.0.1": simple_tcp_packet(ip_src='192.168.0.1'),
            "192.168.0.2": simple_tcp_packet(ip_src='192.168.0.2'),
            "192.168.4.2": simple_tcp_packet(ip_src='192.168.4.2'),
            "192.168.0.0": simple_tcp_packet(ip_src='192.168.0.0'),
            "192.168.15.255": simple_tcp_packet(ip_src='192.168.15.255'),
        }

        nonmatching = {
            "192.168.16.0": simple_tcp_packet(ip_src='192.168.16.0'),
            "192.167.255.255": simple_tcp_packet(ip_src='192.167.255.255'),
            "192.168.31.1": simple_tcp_packet(ip_src='192.168.31.1'),
        }

        self.verify_match(match, matching, nonmatching)

class IPv4SrcMasked(MatchTest):
    """
    Match on ipv4 source address (arbitrarily masked)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0800),
            # 192.168.0.1 255.254.255.255
            ofp.oxm.ipv4_src_masked(0xc0a80001, 0xfffeffff),
        ])

        matching = {
            "192.168.0.1": simple_tcp_packet(ip_src='192.168.0.1'),
            "192.169.0.1": simple_tcp_packet(ip_src='192.169.0.1'),
        }

        nonmatching = {
            "192.168.0.2": simple_tcp_packet(ip_src='192.168.0.2'),
            "192.167.0.1": simple_tcp_packet(ip_src='192.167.0.1'),
        }

        self.verify_match(match, matching, nonmatching)

class IPv4Dst(MatchTest):
    """
    Match on ipv4 source address
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0800),
            ofp.oxm.ipv4_dst(0xc0a80001), # 192.168.0.1
        ])

        matching = {
            "192.168.0.1": simple_tcp_packet(ip_dst='192.168.0.1'),
        }

        nonmatching = {
            "192.168.0.2": simple_tcp_packet(ip_dst='192.168.0.2'),
            "255.255.255.255": simple_tcp_packet(ip_dst='255.255.255.255'),
        }

        self.verify_match(match, matching, nonmatching)

class IPv4DstSubnetMasked(MatchTest):
    """
    Match on ipv4 source address (subnet masked)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0800),
            # 192.168.0.0/20 (255.255.240.0)
            ofp.oxm.ipv4_dst_masked(0xc0a80000, 0xfffff000),
        ])

        matching = {
            "192.168.0.1": simple_tcp_packet(ip_dst='192.168.0.1'),
            "192.168.0.2": simple_tcp_packet(ip_dst='192.168.0.2'),
            "192.168.4.2": simple_tcp_packet(ip_dst='192.168.4.2'),
            "192.168.0.0": simple_tcp_packet(ip_dst='192.168.0.0'),
            "192.168.15.255": simple_tcp_packet(ip_dst='192.168.15.255'),
        }

        nonmatching = {
            "192.168.16.0": simple_tcp_packet(ip_dst='192.168.16.0'),
            "192.167.255.255": simple_tcp_packet(ip_dst='192.167.255.255'),
            "192.168.31.1": simple_tcp_packet(ip_dst='192.168.31.1'),
        }

        self.verify_match(match, matching, nonmatching)

class IPv4DstMasked(MatchTest):
    """
    Match on ipv4 source address (arbitrarily masked)
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0800),
            # 192.168.0.1 255.254.255.255
            ofp.oxm.ipv4_dst_masked(0xc0a80001, 0xfffeffff),
        ])

        matching = {
            "192.168.0.1": simple_tcp_packet(ip_dst='192.168.0.1'),
            "192.169.0.1": simple_tcp_packet(ip_dst='192.169.0.1'),
        }

        nonmatching = {
            "192.168.0.2": simple_tcp_packet(ip_dst='192.168.0.2'),
            "192.167.0.1": simple_tcp_packet(ip_dst='192.167.0.1'),
        }

        self.verify_match(match, matching, nonmatching)

# TODO IPv6 source address
# TODO IPv6 destination address

class IPv4TCPSrc(MatchTest):
    """
    Match on ipv4 tcp source port
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0800),
            ofp.oxm.ip_proto(6),
            ofp.oxm.tcp_src(53),
        ])

        matching = {
            "tcp sport=53": simple_tcp_packet(tcp_sport=53),
        }

        nonmatching = {
            "tcp sport=52": simple_tcp_packet(tcp_sport=52),
            "udp sport=53": simple_udp_packet(udp_sport=53),
        }

        self.verify_match(match, matching, nonmatching)

class IPv6TCPSrc(MatchTest):
    """
    Match on ipv4 tcp source port
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x86dd),
            ofp.oxm.ip_proto(6),
            ofp.oxm.tcp_src(53),
        ])

        matching = {
            "tcp sport=53": simple_tcpv6_packet(tcp_sport=53),
        }

        nonmatching = {
            "tcp sport=52": simple_tcpv6_packet(tcp_sport=52),
            "udp sport=53": simple_udpv6_packet(udp_sport=53),
        }

        self.verify_match(match, matching, nonmatching)

class IPv4TCPDst(MatchTest):
    """
    Match on ipv4 tcp destination port
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0800),
            ofp.oxm.ip_proto(6),
            ofp.oxm.tcp_dst(53),
        ])

        matching = {
            "tcp dport=53": simple_tcp_packet(tcp_dport=53),
        }

        nonmatching = {
            "tcp dport=52": simple_tcp_packet(tcp_dport=52),
            "udp dport=53": simple_udp_packet(udp_dport=53),
        }

        self.verify_match(match, matching, nonmatching)

class IPv6TCPDst(MatchTest):
    """
    Match on ipv6 tcp destination port
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x86dd),
            ofp.oxm.ip_proto(6),
            ofp.oxm.tcp_dst(53),
        ])

        matching = {
            "tcp dport=53": simple_tcpv6_packet(tcp_dport=53),
        }

        nonmatching = {
            "tcp dport=52": simple_tcpv6_packet(tcp_dport=52),
            "udp dport=53": simple_udpv6_packet(udp_dport=53),
        }

        self.verify_match(match, matching, nonmatching)

class IPv4UDPSrc(MatchTest):
    """
    Match on ipv4 udp source port
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0800),
            ofp.oxm.ip_proto(17),
            ofp.oxm.udp_src(53),
        ])

        matching = {
            "udp sport=53": simple_udp_packet(udp_sport=53),
        }

        nonmatching = {
            "udp sport=52": simple_udp_packet(udp_sport=52),
            "tcp sport=53": simple_tcp_packet(tcp_sport=53),
        }

        self.verify_match(match, matching, nonmatching)

class IPv6UDPSrc(MatchTest):
    """
    Match on ipv4 udp source port
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x86dd),
            ofp.oxm.ip_proto(17),
            ofp.oxm.udp_src(53),
        ])

        matching = {
            "udp sport=53": simple_udpv6_packet(udp_sport=53),
        }

        nonmatching = {
            "udp sport=52": simple_udpv6_packet(udp_sport=52),
            "tcp sport=53": simple_tcpv6_packet(tcp_sport=53),
        }

        self.verify_match(match, matching, nonmatching)

class IPv4UDPDst(MatchTest):
    """
    Match on ipv4 udp destination port
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0800),
            ofp.oxm.ip_proto(17),
            ofp.oxm.udp_dst(53),
        ])

        matching = {
            "udp dport=53": simple_udp_packet(udp_dport=53),
        }

        nonmatching = {
            "udp dport=52": simple_udp_packet(udp_dport=52),
            "tcp dport=53": simple_tcp_packet(tcp_dport=53),
        }

        self.verify_match(match, matching, nonmatching)

class IPv6UDPDst(MatchTest):
    """
    Match on ipv4 udp destination port
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x86dd),
            ofp.oxm.ip_proto(17),
            ofp.oxm.udp_dst(53),
        ])

        matching = {
            "udp dport=53": simple_udpv6_packet(udp_dport=53),
        }

        nonmatching = {
            "udp dport=52": simple_udpv6_packet(udp_dport=52),
            "tcp dport=53": simple_tcpv6_packet(tcp_dport=53),
        }

        self.verify_match(match, matching, nonmatching)

class IPv4ICMPType(MatchTest):
    """
    Match on ipv4 icmp type
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0800),
            ofp.oxm.ip_proto(1),
            ofp.oxm.icmpv4_type(3),
        ])

        matching = {
            "type=3 code=1": simple_icmp_packet(icmp_type=3, icmp_code=1),
            "type=3 code=2": simple_icmp_packet(icmp_type=3, icmp_code=2),
        }

        nonmatching = {
            "type=2 code=1": simple_icmp_packet(icmp_type=2, icmp_code=1),
        }

        self.verify_match(match, matching, nonmatching)

class IPv4ICMPCode(MatchTest):
    """
    Match on ipv4 icmp code
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0800),
            ofp.oxm.ip_proto(1),
            ofp.oxm.icmpv4_code(2),
        ])

        matching = {
            "type=3 code=2": simple_icmp_packet(icmp_type=3, icmp_code=2),
            "type=5 code=2": simple_icmp_packet(icmp_type=5, icmp_code=2),
        }

        nonmatching = {
            "type=3 code=1": simple_icmp_packet(icmp_type=2, icmp_code=1),
        }

        self.verify_match(match, matching, nonmatching)

class IPv6ICMPType(MatchTest):
    """
    Match on ipv6 icmp type
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x86dd),
            ofp.oxm.ip_proto(58),
            ofp.oxm.icmpv6_type(3),
        ])

        matching = {
            "type=3 code=1": simple_icmpv6_packet(icmp_type=3, icmp_code=1),
            "type=3 code=2": simple_icmpv6_packet(icmp_type=3, icmp_code=2),
        }

        nonmatching = {
            "type=2 code=1": simple_icmpv6_packet(icmp_type=2, icmp_code=1),
        }

        self.verify_match(match, matching, nonmatching)

class IPv6ICMPCode(MatchTest):
    """
    Match on ipv6 icmp code
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x86dd),
            ofp.oxm.ip_proto(58),
            ofp.oxm.icmpv6_code(2),
        ])

        matching = {
            "type=3 code=2": simple_icmpv6_packet(icmp_type=3, icmp_code=2),
            "type=5 code=2": simple_icmpv6_packet(icmp_type=5, icmp_code=2),
        }

        nonmatching = {
            "type=3 code=1": simple_icmpv6_packet(icmp_type=2, icmp_code=1),
        }

        self.verify_match(match, matching, nonmatching)

class ArpOp(MatchTest):
    """
    Match on ARP operation
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0806),
            ofp.oxm.arp_op(3),
        ])

        matching = {
            "op=3": simple_arp_packet(arp_op=3),
        }

        nonmatching = {
            "op=4": simple_arp_packet(arp_op=4),
        }

        self.verify_match(match, matching, nonmatching)

class ArpSPA(MatchTest):
    """
    Match on ARP sender IP
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0806),
            ofp.oxm.arp_spa(0xc0a80001), # 192.168.0.1
        ])

        matching = {
            "192.168.0.1": simple_arp_packet(ip_snd="192.168.0.1"),
        }

        nonmatching = {
            "192.168.0.2": simple_arp_packet(ip_snd="192.168.0.2"),
        }

        self.verify_match(match, matching, nonmatching)

class ArpTPA(MatchTest):
    """
    Match on ARP target IP
    """
    def runTest(self):
        match = ofp.match([
            ofp.oxm.eth_type(0x0806),
            ofp.oxm.arp_tpa(0xc0a80001), # 192.168.0.1
        ])

        matching = {
            "192.168.0.1": simple_arp_packet(ip_tgt="192.168.0.1"),
        }

        nonmatching = {
            "192.168.0.2": simple_arp_packet(ip_tgt="192.168.0.2"),
        }

        self.verify_match(match, matching, nonmatching)
