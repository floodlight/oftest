# Distributed under the OpenFlow Software License (see LICENSE)
# Copyright (c) 2010 The Board of Trustees of The Leland Stanford Junior University
# Copyright (c) 2012, 2013 Big Switch Networks, Inc.
"""
Wrap scapy to satisfy pylint
"""
from oftest import config
import sys

try:
    import scapy.config
    import scapy.route
    import scapy.layers.l2
    import scapy.layers.inet
    import scapy.layers.sctp
    if not config["disable_ipv6"]:
        import scapy.route6
        import scapy.layers.inet6
except ImportError:
    sys.exit("Need to install scapy for packet parsing")

Ether = scapy.layers.l2.Ether
LLC = scapy.layers.l2.LLC
SNAP = scapy.layers.l2.SNAP
Dot1Q = scapy.layers.l2.Dot1Q
ARP = scapy.layers.l2.ARP
IP = scapy.layers.inet.IP
IPOption = scapy.layers.inet.IPOption
TCP = scapy.layers.inet.TCP
UDP = scapy.layers.inet.UDP
ICMP = scapy.layers.inet.ICMP
SCTP = scapy.layers.sctp.SCTP

if not config["disable_ipv6"]:
    IPv6 = scapy.layers.inet6.IPv6
    ICMPv6Unknown = scapy.layers.inet6.ICMPv6Unknown
    ICMPv6EchoRequest = scapy.layers.inet6.ICMPv6EchoRequest
    ICMPv6EchoReply = scapy.layers.inet6.ICMPv6EchoReply
    ICMPv6ND_NS = scapy.layers.inet6.ICMPv6ND_NS
    ICMPv6ND_NA = scapy.layers.inet6.ICMPv6ND_NA
    ICMPv6ND_RA = scapy.layers.inet6.ICMPv6ND_RA
    ICMPv6ND_RS = scapy.layers.inet6.ICMPv6ND_RS
    ICMPv6NDOptSrcLLAddr = scapy.layers.inet6.ICMPv6NDOptSrcLLAddr
    ICMPv6NDOptDstLLAddr = scapy.layers.inet6.ICMPv6NDOptDstLLAddr
    ICMPv6NDOptPrefixInfo = scapy.layers.inet6.ICMPv6NDOptPrefixInfo
    ICMPv6DestUnreach = scapy.layers.inet6.ICMPv6DestUnreach
    ICMPv6TimeExceeded = scapy.layers.inet6.ICMPv6TimeExceeded

import scapy.config as scapy_config
if 'vxlan' in scapy_config.Conf.load_layers:
    # pylint: disable=no-name-in-module, import-error
    import scapy.layers.vxlan
    # pylint: disable=no-member
    VXLAN = scapy.layers.vxlan.VXLAN
else:
    from oftest import vxlan
    VXLAN = vxlan.VXLAN
