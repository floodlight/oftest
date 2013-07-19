"""
Utility parsing functions
"""

import sys
import socket
try:
    import scapy.all as scapy
except:
    try:
        import scapy as scapy
    except:
        sys.exit("Need to install scapy for packet parsing")

def parse_mac(mac_str):
    """
    Parse a MAC address

    Parse a MAC address ':' separated string of hex digits to an
    array of integer values.  '00:d0:05:5d:24:00' => [0, 208, 5, 93, 36, 0]
    @param mac_str The string to convert
    @return Array of 6 integer values
    """
    return map(lambda val: int(val, 16), mac_str.split(":"))

def parse_ip(ip_str):
    """
    Parse an IP address

    Parse an IP address '.' separated string of decimal digits to an
    host ordered integer.  '172.24.74.77' => 
    @param ip_str The string to convert
    @return Integer value
    """
    array = map(lambda val: int(val), ip_str.split("."))
    val = 0
    for a in array:
        val <<= 8
        val += a
    return val

def parse_ipv6(ip_str):
    """
    Parse an IPv6 address

    Parse a textual IPv6 address and return a 16 byte binary string.
    """
    return socket.inet_pton(socket.AF_INET6, ip_str)

def packet_type_classify(ether):
    try:
        dot1q = ether[scapy.Dot1Q]
    except:
        dot1q = None

    try:
        ip = ether[scapy.IP]
    except:
        ip = None

    try:
        tcp = ether[scapy.TCP]
    except:
        tcp = None

    try:
        udp = ether[scapy.UDP]
    except:
        udp = None

    try:
        icmp = ether[scapy.ICMP]
    except:
        icmp = None

    try:
        arp = ether[scapy.ARP]
    except:
        arp = None
    return (dot1q, ip, tcp, udp, icmp, arp)

def packet_to_flow_match(packet):
    """
    Create a flow match that matches packet with the given wildcards

    @param packet The packet to use as a flow template
    @return An loxi.of10.match object

    @todo check min length of packet
    """
    import ofp
    if ofp.OFP_VERSION == 1:
        return packet_to_flow_match_v1(packet)
    elif ofp.OFP_VERSION == 3:
        return packet_to_flow_match_v3(packet)
    elif ofp.OFP_VERSION == 4:
        return packet_to_flow_match_v4(packet)
    else:
        raise NotImplementedError()

def packet_to_flow_match_v1(packet):
    """
    OpenFlow 1.0 implementation of packet_to_flow_match
    """
    import loxi.of10 as ofp

    if type(packet) == type(""):
        ether = scapy.Ether(packet)
    else:
        ether = packet

    # For now, assume ether IP packet and ignore wildcards
    try:
        (dot1q, ip, tcp, udp, icmp, arp) = packet_type_classify(ether)
    except:
        raise ValueError("could not classify packet")

    match = ofp.match()
    match.wildcards = ofp.OFPFW_ALL
    #@todo Check if packet is other than L2 format
    match.eth_dst = parse_mac(ether.dst)
    match.wildcards &= ~ofp.OFPFW_DL_DST
    match.eth_src = parse_mac(ether.src)
    match.wildcards &= ~ofp.OFPFW_DL_SRC
    match.eth_type = ether.type
    match.wildcards &= ~ofp.OFPFW_DL_TYPE

    if dot1q:
        match.vlan_vid = dot1q.vlan
        match.vlan_pcp = dot1q.prio
        match.eth_type = dot1q.type
    else:
        match.vlan_vid = ofp.OFP_VLAN_NONE
        match.vlan_pcp = 0
    match.wildcards &= ~ofp.OFPFW_DL_VLAN
    match.wildcards &= ~ofp.OFPFW_DL_VLAN_PCP

    if ip:
        match.ipv4_src = parse_ip(ip.src)
        match.wildcards &= ~ofp.OFPFW_NW_SRC_MASK
        match.ipv4_dst = parse_ip(ip.dst)
        match.wildcards &= ~ofp.OFPFW_NW_DST_MASK
        match.ip_dscp = ip.tos
        match.wildcards &= ~ofp.OFPFW_NW_TOS

    if tcp:
        match.ip_proto = 6
        match.wildcards &= ~ofp.OFPFW_NW_PROTO
    elif not tcp and udp:
        tcp = udp
        match.ip_proto = 17
        match.wildcards &= ~ofp.OFPFW_NW_PROTO

    if tcp:
        match.tcp_src = tcp.sport
        match.wildcards &= ~ofp.OFPFW_TP_SRC
        match.tcp_dst = tcp.dport
        match.wildcards &= ~ofp.OFPFW_TP_DST

    if icmp:
        match.ip_proto = 1
        match.tcp_src = icmp.type
        match.tcp_dst = icmp.code
        match.wildcards &= ~ofp.OFPFW_NW_PROTO

    if arp:
        match.ip_proto = arp.op
        match.wildcards &= ~ofp.OFPFW_NW_PROTO
        match.ipv4_src = parse_ip(arp.psrc)
        match.wildcards &= ~ofp.OFPFW_NW_SRC_MASK
        match.ipv4_dst = parse_ip(arp.pdst)
        match.wildcards &= ~ofp.OFPFW_NW_DST_MASK

    return match

def packet_to_flow_match_v3(packet):
    """
    OpenFlow 1.2 implementation of packet_to_flow_match
    """
    import loxi.of12 as ofp
    return packet_to_flow_match_oxm(packet, ofp)

def packet_to_flow_match_v4(packet):
    """
    OpenFlow 1.3 implementation of packet_to_flow_match
    """
    import loxi.of13 as ofp
    return packet_to_flow_match_oxm(packet, ofp)

def packet_to_flow_match_oxm(packet, ofp):
    def parse_ether_layer(layer, match):
        assert(type(layer) == scapy.Ether)
        match.oxm_list.append(ofp.oxm.eth_dst(parse_mac(layer.dst)))
        match.oxm_list.append(ofp.oxm.eth_src(parse_mac(layer.src)))

        if type(layer.payload) == scapy.Dot1Q:
            layer = layer.payload
            match.oxm_list.append(ofp.oxm.eth_type(layer.type))
            match.oxm_list.append(ofp.oxm.vlan_vid(ofp.OFPVID_PRESENT|layer.vlan))
            match.oxm_list.append(ofp.oxm.vlan_pcp(layer.prio))
        else:
            match.oxm_list.append(ofp.oxm.eth_type(layer.type))
            match.oxm_list.append(ofp.oxm.vlan_vid(ofp.OFP_VLAN_NONE))

        if type(layer.payload) == scapy.IP:
            parse_ipv4_layer(layer.payload, match)
        elif type(layer.payload) == scapy.IPv6:
            parse_ipv6_layer(layer.payload, match)
        elif type(layer.payload) == scapy.ARP:
            parse_arp_layer(layer.payload, match)
        # TODO MPLS

    def parse_ipv4_layer(layer, match):
        assert(type(layer) == scapy.IP)
        match.oxm_list.append(ofp.oxm.ip_proto(layer.proto))
        match.oxm_list.append(ofp.oxm.ip_dscp(layer.tos >> 2))
        match.oxm_list.append(ofp.oxm.ip_ecn(layer.tos & 3))
        match.oxm_list.append(ofp.oxm.ipv4_src(parse_ip(layer.src)))
        match.oxm_list.append(ofp.oxm.ipv4_dst(parse_ip(layer.dst)))

        if type(layer.payload) == scapy.TCP:
            parse_tcp_layer(layer.payload, match)
        elif type(layer.payload) == scapy.UDP:
            parse_udp_layer(layer.payload, match)
        elif type(layer.payload) == scapy.ICMP:
            parse_icmpv4_layer(layer.payload, match)
        # TODO SCTP

    def parse_tcp_layer(layer, match):
        assert(type(layer) == scapy.TCP)
        match.oxm_list.append(ofp.oxm.tcp_src(layer.sport))
        match.oxm_list.append(ofp.oxm.tcp_dst(layer.dport))

    def parse_udp_layer(layer, match):
        assert(type(layer) == scapy.UDP)
        match.oxm_list.append(ofp.oxm.udp_src(layer.sport))
        match.oxm_list.append(ofp.oxm.udp_dst(layer.dport))

    def parse_icmpv4_layer(layer, match):
        assert(type(layer) == scapy.ICMP)
        match.oxm_list.append(ofp.oxm.icmpv4_type(layer.type))
        match.oxm_list.append(ofp.oxm.icmpv4_code(layer.code))

    def parse_arp_layer(layer, match):
        assert(type(layer) == scapy.ARP)
        match.oxm_list.append(ofp.oxm.arp_op(layer.op))
        match.oxm_list.append(ofp.oxm.arp_spa(parse_ip(layer.psrc)))
        match.oxm_list.append(ofp.oxm.arp_tpa(parse_ip(layer.pdst)))
        match.oxm_list.append(ofp.oxm.arp_sha(parse_mac(layer.hwsrc)))
        match.oxm_list.append(ofp.oxm.arp_tha(parse_mac(layer.hwdst)))

    def parse_ipv6_layer(layer, match):
        assert(type(layer) == scapy.IPv6)
        # TODO handle chained headers
        match.oxm_list.append(ofp.oxm.ip_proto(layer.nh))
        match.oxm_list.append(ofp.oxm.ip_dscp(layer.tc >> 2))
        match.oxm_list.append(ofp.oxm.ip_ecn(layer.tc & 3))
        match.oxm_list.append(ofp.oxm.ipv6_src(parse_ipv6(layer.src)))
        match.oxm_list.append(ofp.oxm.ipv6_dst(parse_ipv6(layer.dst)))
        match.oxm_list.append(ofp.oxm.ipv6_flabel(layer.fl))

        if type(layer.payload) == scapy.TCP:
            parse_tcp_layer(layer.payload, match)
        elif type(layer.payload) == scapy.UDP:
            parse_udp_layer(layer.payload, match)
        elif layer.nh == 0x3a:
            parse_icmpv6_layer(layer.payload, match)
        # TODO ND
        # TODO SCTP

    def parse_icmpv6_layer(layer, match):
        match.oxm_list.append(ofp.oxm.icmpv6_type(layer.type))
        match.oxm_list.append(ofp.oxm.icmpv6_code(layer.code))

    if type(packet) == type(""):
        ether = scapy.Ether(packet)
    else:
        ether = packet

    match = ofp.match()
    parse_ether_layer(packet, match)
    return match
