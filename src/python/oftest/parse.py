"""
OpenFlow message parsing functions
"""

import sys
import logging
from message import *
from error import *
from action import *
from action_list import action_list
from cstruct import *
try:
    import scapy.all as scapy
except:
    try:
        import scapy as scapy
    except:
        sys.exit("Need to install scapy for packet parsing")

"""
of_message.py
Contains wrapper functions and classes for the of_message namespace
that are generated by hand.  It includes the rest of the wrapper
function information into the of_message namespace
"""

parse_logger = logging.getLogger("parse")
#parse_logger.setLevel(logging.DEBUG)

# These message types are subclassed
msg_type_subclassed = [
    OFPT_STATS_REQUEST,
    OFPT_STATS_REPLY,
    OFPT_ERROR
]

# Maps from sub-types to classes
stats_reply_to_class_map = {
    OFPST_DESC                      : desc_stats_reply,
    OFPST_AGGREGATE                 : aggregate_stats_reply,
    OFPST_FLOW                      : flow_stats_reply,
    OFPST_TABLE                     : table_stats_reply,
    OFPST_PORT                      : port_stats_reply,
    OFPST_QUEUE                     : queue_stats_reply
}

stats_request_to_class_map = {
    OFPST_DESC                      : desc_stats_request,
    OFPST_AGGREGATE                 : aggregate_stats_request,
    OFPST_FLOW                      : flow_stats_request,
    OFPST_TABLE                     : table_stats_request,
    OFPST_PORT                      : port_stats_request,
    OFPST_QUEUE                     : queue_stats_request
}

error_to_class_map = {
    OFPET_HELLO_FAILED              : hello_failed_error_msg,
    OFPET_BAD_REQUEST               : bad_request_error_msg,
    OFPET_BAD_ACTION                : bad_action_error_msg,
    OFPET_FLOW_MOD_FAILED           : flow_mod_failed_error_msg,
    OFPET_PORT_MOD_FAILED           : port_mod_failed_error_msg,
    OFPET_QUEUE_OP_FAILED           : queue_op_failed_error_msg
}

# Map from header type value to the underlieing message class
msg_type_to_class_map = {
    OFPT_HELLO                      : hello,
    OFPT_ERROR                      : error,
    OFPT_ECHO_REQUEST               : echo_request,
    OFPT_ECHO_REPLY                 : echo_reply,
    OFPT_VENDOR                     : vendor,
    OFPT_FEATURES_REQUEST           : features_request,
    OFPT_FEATURES_REPLY             : features_reply,
    OFPT_GET_CONFIG_REQUEST         : get_config_request,
    OFPT_GET_CONFIG_REPLY           : get_config_reply,
    OFPT_SET_CONFIG                 : set_config,
    OFPT_PACKET_IN                  : packet_in,
    OFPT_FLOW_REMOVED               : flow_removed,
    OFPT_PORT_STATUS                : port_status,
    OFPT_PACKET_OUT                 : packet_out,
    OFPT_FLOW_MOD                   : flow_mod,
    OFPT_PORT_MOD                   : port_mod,
    OFPT_STATS_REQUEST              : stats_request,
    OFPT_STATS_REPLY                : stats_reply,
    OFPT_BARRIER_REQUEST            : barrier_request,
    OFPT_BARRIER_REPLY              : barrier_reply,
    OFPT_QUEUE_GET_CONFIG_REQUEST   : queue_get_config_request,
    OFPT_QUEUE_GET_CONFIG_REPLY     : queue_get_config_reply
}

def _of_message_to_object(binary_string):
    """
    Map a binary string to the corresponding class.

    Appropriately resolves subclasses
    """
    hdr = ofp_header()
    hdr.unpack(binary_string)
    # FIXME: Add error detection
    if not hdr.type in msg_type_subclassed:
        return msg_type_to_class_map[hdr.type]()
    if hdr.type == OFPT_STATS_REQUEST:
        sub_hdr = ofp_stats_request()
        sub_hdr.unpack(binary_string[OFP_HEADER_BYTES:])
        try:
            obj = stats_request_to_class_map[sub_hdr.type]()
        except KeyError:
            obj = None
        return obj
    elif hdr.type == OFPT_STATS_REPLY:
        sub_hdr = ofp_stats_reply()
        sub_hdr.unpack(binary_string[OFP_HEADER_BYTES:])
        try:
            obj = stats_reply_to_class_map[sub_hdr.type]()
        except KeyError:
            obj = None
        return obj
    elif hdr.type == OFPT_ERROR:
        sub_hdr = ofp_error_msg()
        sub_hdr.unpack(binary_string[OFP_HEADER_BYTES:])
        return error_to_class_map[sub_hdr.type]()
    else:
        parse_logger.error("Cannot parse pkt to message")
        return None

def of_message_parse(binary_string, raw=False):
    """
    Parse an OpenFlow packet

    Parses a raw OpenFlow packet into a Python class, with class
    members fully populated.

    @param binary_string The packet (string) to be parsed
    @param raw If true, interpret the packet as an L2 packet.  Not
    yet supported.
    @return An object of some message class or None if fails
    Note that any data beyond that parsed is not returned

    """

    if raw:
        parse_logger.error("raw packet message parsing not supported")
        return None

    obj = _of_message_to_object(binary_string)
    if obj:
        obj.unpack(binary_string)
    return obj


def of_header_parse(binary_string, raw=False):
    """
    Parse only the header from an OpenFlow packet

    Parses the header from a raw OpenFlow packet into a
    an ofp_header Python class.

    @param binary_string The packet (string) to be parsed
    @param raw If true, interpret the packet as an L2 packet.  Not
    yet supported.
    @return An ofp_header object

    """

    if raw:
        parse_logger.error("raw packet message parsing not supported")
        return None

    hdr = ofp_header()
    hdr.unpack(binary_string)

    return hdr

map_wc_field_to_match_member = {
    'OFPFW_DL_VLAN'                 : 'dl_vlan',
    'OFPFW_DL_SRC'                  : 'dl_src',
    'OFPFW_DL_DST'                  : 'dl_dst',
    'OFPFW_DL_TYPE'                 : 'dl_type',
    'OFPFW_NW_PROTO'                : 'nw_proto',
    'OFPFW_TP_SRC'                  : 'tp_src',
    'OFPFW_TP_DST'                  : 'tp_dst',
    'OFPFW_NW_SRC_SHIFT'            : 'nw_src_shift',
    'OFPFW_NW_SRC_BITS'             : 'nw_src_bits',
    'OFPFW_NW_SRC_MASK'             : 'nw_src_mask',
    'OFPFW_NW_SRC_ALL'              : 'nw_src_all',
    'OFPFW_NW_DST_SHIFT'            : 'nw_dst_shift',
    'OFPFW_NW_DST_BITS'             : 'nw_dst_bits',
    'OFPFW_NW_DST_MASK'             : 'nw_dst_mask',
    'OFPFW_NW_DST_ALL'              : 'nw_dst_all',
    'OFPFW_DL_VLAN_PCP'             : 'dl_vlan_pcp',
    'OFPFW_NW_TOS'                  : 'nw_tos'
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

    # @todo arp is not yet supported
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
        parse_logger.error("Only L2 supported for packet_to_flow")
        return None

    if type(packet) == type(""):
        ether = scapy.Ether(packet)
    else:
        ether = packet

    # For now, assume ether IP packet and ignore wildcards
    try:
        (dot1q, ip, tcp, udp, icmp, arp) = packet_type_classify(ether)
    except:
        parse_logger.error("packet_to_flow_match: Classify error")
        return None

    match = ofp_match()
    match.wildcards = OFPFW_ALL
    #@todo Check if packet is other than L2 format
    match.dl_dst = parse_mac(ether.dst)
    match.wildcards &= ~OFPFW_DL_DST
    match.dl_src = parse_mac(ether.src)
    match.wildcards &= ~OFPFW_DL_SRC
    match.dl_type = ether.type
    match.wildcards &= ~OFPFW_DL_TYPE

    if dot1q:
        match.dl_vlan = dot1q.vlan
        match.dl_vlan_pcp = dot1q.prio
        match.dl_type = dot1q.type
    else:
        match.dl_vlan = OFP_VLAN_NONE
        match.dl_vlan_pcp = 0
    match.wildcards &= ~OFPFW_DL_VLAN
    match.wildcards &= ~OFPFW_DL_VLAN_PCP

    if ip:
        match.nw_src = parse_ip(ip.src)
        match.wildcards &= ~OFPFW_NW_SRC_MASK
        match.nw_dst = parse_ip(ip.dst)
        match.wildcards &= ~OFPFW_NW_DST_MASK
        match.nw_tos = ip.tos
        match.wildcards &= ~OFPFW_NW_TOS

    if tcp:
        match.nw_proto = 6
        match.wildcards &= ~OFPFW_NW_PROTO
    elif not tcp and udp:
        tcp = udp
        match.nw_proto = 17
        match.wildcards &= ~OFPFW_NW_PROTO

    if tcp:
        match.tp_src = tcp.sport
        match.wildcards &= ~OFPFW_TP_SRC
        match.tp_dst = tcp.dport
        match.wildcards &= ~OFPFW_TP_DST

    if icmp:
        match.nw_proto = 1
        match.tp_src = icmp.type
        match.tp_dst = icmp.code

    #@todo Implement ARP fields

    return match
