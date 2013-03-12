"""
Utility parsing functions
"""

import sys
import logging
import of10 as ofp
try:
    import scapy.all as scapy
except:
    try:
        import scapy as scapy
    except:
        sys.exit("Need to install scapy for packet parsing")

map_wc_field_to_match_member = {
    'OFPFW_DL_VLAN'                 : 'vlan_vid',
    'OFPFW_DL_SRC'                  : 'eth_src',
    'OFPFW_DL_DST'                  : 'eth_dst',
    'OFPFW_DL_TYPE'                 : 'eth_type',
    'OFPFW_NW_PROTO'                : 'ip_proto',
    'OFPFW_TP_SRC'                  : 'tcp_src',
    'OFPFW_TP_DST'                  : 'tcp_dst',
    'OFPFW_NW_SRC_SHIFT'            : 'nw_src_shift',
    'OFPFW_NW_SRC_BITS'             : 'nw_src_bits',
    'OFPFW_NW_SRC_MASK'             : 'nw_src_mask',
    'OFPFW_NW_SRC_ALL'              : 'nw_src_all',
    'OFPFW_NW_DST_SHIFT'            : 'nw_dst_shift',
    'OFPFW_NW_DST_BITS'             : 'nw_dst_bits',
    'OFPFW_NW_DST_MASK'             : 'nw_dst_mask',
    'OFPFW_NW_DST_ALL'              : 'nw_dst_all',
    'OFPFW_DL_VLAN_PCP'             : 'vlan_pcp',
    'OFPFW_NW_TOS'                  : 'ip_dscp'
}


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

def packet_to_flow_match(packet, pkt_format="L2"):
    """
    Create a flow match that matches packet with the given wildcards

    @param packet The packet to use as a flow template
    @param pkt_format Currently only L2 is supported.  Will indicate the 
    overall packet type for parsing
    @return An ofp_match object if successful.  None if format is not
    recognized.  The wildcards of the match will be cleared for the
    values extracted from the packet.

    @todo check min length of packet
    @todo Check if packet is other than L2 format
    @todo Implement ICMP and ARP fields
    """

    #@todo check min length of packet
    if pkt_format.upper() != "L2":
        logging.error("Only L2 supported for packet_to_flow")
        return None

    if type(packet) == type(""):
        ether = scapy.Ether(packet)
    else:
        ether = packet

    # For now, assume ether IP packet and ignore wildcards
    try:
        (dot1q, ip, tcp, udp, icmp, arp) = packet_type_classify(ether)
    except:
        logging.error("packet_to_flow_match: Classify error")
        return None

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
