# Distributed under the OpenFlow Software License (see LICENSE)
# Copyright (c) 2010 The Board of Trustees of The Leland Stanford Junior University
# Copyright (c) 2012, 2013 Big Switch Networks, Inc.
"""
Wrap scapy to satisfy pylint
"""
import sys

try:
    import scapy.config
    import scapy.route
    import scapy.route6
    import scapy.layers.l2
    import scapy.layers.inet
    import scapy.layers.inet6
except ImportError:
    sys.exit("Need to install scapy for packet parsing")

Ether = scapy.layers.l2.Ether
LLC = scapy.layers.l2.LLC
SNAP = scapy.layers.l2.SNAP
Dot1Q = scapy.layers.l2.Dot1Q
IP = scapy.layers.inet.IP
IPOption = scapy.layers.inet.IPOption
IPv6 = scapy.layers.inet6.IPv6
ARP = scapy.layers.inet.ARP
TCP = scapy.layers.inet.TCP
UDP = scapy.layers.inet.UDP
ICMP = scapy.layers.inet.ICMP
ICMPv6Unknown = scapy.layers.inet6.ICMPv6Unknown
ICMPv6EchoRequest = scapy.layers.inet6.ICMPv6EchoRequest
