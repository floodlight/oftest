#!/usr/bin/env python
import unittest
import parse
import scapy.all as scapy

class TestPacketToFlowMatchV3(unittest.TestCase):
    def test_tcp(self):
        import loxi.of12 as ofp
        self.maxDiff = None
        pkt = scapy.Ether(dst='00:01:02:03:04:05', src='00:06:07:08:09:0a')/ \
            scapy.IP(src='192.168.0.1', dst='192.168.0.2', tos=2 | (32 << 2), ttl=64)/ \
            scapy.TCP(sport=1234, dport=80)
        expected = [
            ofp.oxm.eth_dst([0x00, 0x01, 0x02, 0x03, 0x04, 0x05]),
            ofp.oxm.eth_src([0x00, 0x06, 0x07, 0x08, 0x09, 0x0a]),
            ofp.oxm.eth_type(0x0800),
            ofp.oxm.vlan_vid(ofp.OFP_VLAN_NONE),
            ofp.oxm.ip_proto(6),
            ofp.oxm.ip_dscp(32),
            ofp.oxm.ip_ecn(2),
            ofp.oxm.ipv4_src(0xc0a80001),
            ofp.oxm.ipv4_dst(0xc0a80002),
            ofp.oxm.tcp_src(1234),
            ofp.oxm.tcp_dst(80)
        ]
        result = parse.packet_to_flow_match_v3(pkt).oxm_list
        self.assertEquals([x.show() for x in expected], [x.show() for x in result])

    def test_udp(self):
        import loxi.of12 as ofp
        self.maxDiff = None
        pkt = scapy.Ether(dst='00:01:02:03:04:05', src='00:06:07:08:09:0a')/ \
            scapy.IP(src='192.168.0.1', dst='192.168.0.2', tos=2 | (32 << 2), ttl=64)/ \
            scapy.UDP(sport=1234, dport=80)
        expected = [
            ofp.oxm.eth_dst([0x00, 0x01, 0x02, 0x03, 0x04, 0x05]),
            ofp.oxm.eth_src([0x00, 0x06, 0x07, 0x08, 0x09, 0x0a]),
            ofp.oxm.eth_type(0x0800),
            ofp.oxm.vlan_vid(ofp.OFP_VLAN_NONE),
            ofp.oxm.ip_proto(17),
            ofp.oxm.ip_dscp(32),
            ofp.oxm.ip_ecn(2),
            ofp.oxm.ipv4_src(0xc0a80001),
            ofp.oxm.ipv4_dst(0xc0a80002),
            ofp.oxm.udp_src(1234),
            ofp.oxm.udp_dst(80)
        ]
        result = parse.packet_to_flow_match_v3(pkt).oxm_list
        self.assertEquals([x.show() for x in expected], [x.show() for x in result])

    def test_icmp(self):
        import loxi.of12 as ofp
        self.maxDiff = None
        pkt = scapy.Ether(dst='00:01:02:03:04:05', src='00:06:07:08:09:0a')/ \
            scapy.IP(src='192.168.0.1', dst='192.168.0.2', tos=2 | (32 << 2), ttl=64)/ \
            scapy.ICMP(type=8, code=1)
        expected = [
            ofp.oxm.eth_dst([0x00, 0x01, 0x02, 0x03, 0x04, 0x05]),
            ofp.oxm.eth_src([0x00, 0x06, 0x07, 0x08, 0x09, 0x0a]),
            ofp.oxm.eth_type(0x0800),
            ofp.oxm.vlan_vid(ofp.OFP_VLAN_NONE),
            ofp.oxm.ip_proto(1),
            ofp.oxm.ip_dscp(32),
            ofp.oxm.ip_ecn(2),
            ofp.oxm.ipv4_src(0xc0a80001),
            ofp.oxm.ipv4_dst(0xc0a80002),
            ofp.oxm.icmpv4_type(8),
            ofp.oxm.icmpv4_code(1)
        ]
        result = parse.packet_to_flow_match_v3(pkt).oxm_list
        self.assertEquals([x.show() for x in expected], [x.show() for x in result])

    def test_arp(self):
        import loxi.of12 as ofp
        self.maxDiff = None
        pkt = scapy.Ether(dst='00:01:02:03:04:05', src='00:06:07:08:09:0a')/ \
            scapy.ARP(hwsrc='00:01:02:03:04:05', hwdst='00:06:07:08:09:0a', \
                      psrc='192.168.0.1', pdst='192.168.0.2', op=1)
        expected = [
            ofp.oxm.eth_dst([0x00, 0x01, 0x02, 0x03, 0x04, 0x05]),
            ofp.oxm.eth_src([0x00, 0x06, 0x07, 0x08, 0x09, 0x0a]),
            ofp.oxm.eth_type(0x0806),
            ofp.oxm.vlan_vid(ofp.OFP_VLAN_NONE),
            ofp.oxm.arp_op(1),
            ofp.oxm.arp_spa(0xc0a80001),
            ofp.oxm.arp_tpa(0xc0a80002),
            ofp.oxm.arp_sha([0x00, 0x01, 0x02, 0x03, 0x04, 0x05]),
            ofp.oxm.arp_tha([0x00, 0x06, 0x07, 0x08, 0x09, 0x0a]),
        ]
        result = parse.packet_to_flow_match_v3(pkt).oxm_list
        self.assertEquals([x.show() for x in expected], [x.show() for x in result])

    def test_tcpv6(self):
        import loxi.of12 as ofp
        self.maxDiff = None
        pkt = scapy.Ether(dst='00:01:02:03:04:05', src='00:06:07:08:09:0a')/ \
            scapy.IPv6(src="::1", dst="::2", nh=6, tc=2 | (32 << 2), fl=7)/ \
            scapy.TCP(sport=1234, dport=80)
        expected = [
            ofp.oxm.eth_dst([0x00, 0x01, 0x02, 0x03, 0x04, 0x05]),
            ofp.oxm.eth_src([0x00, 0x06, 0x07, 0x08, 0x09, 0x0a]),
            ofp.oxm.eth_type(0x86dd),
            ofp.oxm.vlan_vid(ofp.OFP_VLAN_NONE),
            ofp.oxm.ip_proto(6),
            ofp.oxm.ip_dscp(32),
            ofp.oxm.ip_ecn(2),
            ofp.oxm.ipv6_src("\x00" * 15 + "\x01"),
            ofp.oxm.ipv6_dst("\x00" * 15 + "\x02"),
            ofp.oxm.ipv6_flabel(7),
            ofp.oxm.tcp_src(1234),
            ofp.oxm.tcp_dst(80)
        ]
        result = parse.packet_to_flow_match_v3(pkt).oxm_list
        self.assertEquals([x.show() for x in expected], [x.show() for x in result])

    def test_icmpv6(self):
        import loxi.of12 as ofp
        self.maxDiff = None
        pkt = scapy.Ether(dst='00:01:02:03:04:05', src='00:06:07:08:09:0a')/ \
            scapy.IPv6(src="::1", dst="::2", tc=2 | (32 << 2), fl=7)/ \
            scapy.ICMPv6EchoRequest()
        expected = [
            ofp.oxm.eth_dst([0x00, 0x01, 0x02, 0x03, 0x04, 0x05]),
            ofp.oxm.eth_src([0x00, 0x06, 0x07, 0x08, 0x09, 0x0a]),
            ofp.oxm.eth_type(0x86dd),
            ofp.oxm.vlan_vid(ofp.OFP_VLAN_NONE),
            ofp.oxm.ip_proto(0x3a),
            ofp.oxm.ip_dscp(32),
            ofp.oxm.ip_ecn(2),
            ofp.oxm.ipv6_src("\x00" * 15 + "\x01"),
            ofp.oxm.ipv6_dst("\x00" * 15 + "\x02"),
            ofp.oxm.ipv6_flabel(7),
            ofp.oxm.icmpv6_type(128),
            ofp.oxm.icmpv6_code(0)
        ]
        result = parse.packet_to_flow_match_v3(pkt).oxm_list
        self.assertEquals([x.show() for x in expected], [x.show() for x in result])

    def test_vlan(self):
        import loxi.of12 as ofp
        self.maxDiff = None
        pkt = scapy.Ether(dst='00:01:02:03:04:05', src='00:06:07:08:09:0a')/ \
            scapy.Dot1Q(vlan=50, prio=5)/ \
            scapy.IP(src='192.168.0.1', dst='192.168.0.2', tos=2 | (32 << 2), ttl=64)/ \
            scapy.TCP(sport=1234, dport=80)
        expected = [
            ofp.oxm.eth_dst([0x00, 0x01, 0x02, 0x03, 0x04, 0x05]),
            ofp.oxm.eth_src([0x00, 0x06, 0x07, 0x08, 0x09, 0x0a]),
            ofp.oxm.eth_type(0x0800),
            ofp.oxm.vlan_vid(50),
            ofp.oxm.vlan_pcp(5),
            ofp.oxm.ip_proto(6),
            ofp.oxm.ip_dscp(32),
            ofp.oxm.ip_ecn(2),
            ofp.oxm.ipv4_src(0xc0a80001),
            ofp.oxm.ipv4_dst(0xc0a80002),
            ofp.oxm.tcp_src(1234),
            ofp.oxm.tcp_dst(80)
        ]
        result = parse.packet_to_flow_match_v3(pkt).oxm_list
        self.assertEquals([x.show() for x in expected], [x.show() for x in result])

    def test_unknown_ethertype(self):
        import loxi.of12 as ofp
        self.maxDiff = None
        pkt = scapy.Ether(dst='00:01:02:03:04:05', src='00:06:07:08:09:0a', type=0x0801)/ \
            ('\x11' * 20)
        expected = [
            ofp.oxm.eth_dst([0x00, 0x01, 0x02, 0x03, 0x04, 0x05]),
            ofp.oxm.eth_src([0x00, 0x06, 0x07, 0x08, 0x09, 0x0a]),
            ofp.oxm.eth_type(0x0801),
            ofp.oxm.vlan_vid(ofp.OFP_VLAN_NONE),
        ]
        result = parse.packet_to_flow_match_v3(pkt).oxm_list
        self.assertEquals([x.show() for x in expected], [x.show() for x in result])


if __name__ == '__main__':
    unittest.main(verbosity=2)
