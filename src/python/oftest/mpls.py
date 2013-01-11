# Imported from scapy at revision 1270:113ef25f9583
# This file is not included in the Ubuntu packages of scapy, so it is checked
# in to our repo to simplify installation. This file is under the GPLv2.

# http://trac.secdev.org/scapy/ticket/31 

# scapy.contrib.description = MPLS
# scapy.contrib.status = loads

from scapy.packet import Packet,bind_layers
from scapy.fields import BitField,ByteField
from scapy.layers.l2 import Ether

class MPLS(Packet): 
   name = "MPLS" 
   fields_desc =  [ BitField("label", 3, 20), 
                    BitField("cos", 0, 3), 
                    BitField("s", 1, 1), 
                    ByteField("ttl", 0)  ] 

bind_layers(Ether, MPLS, type=0x8847)

# Not in upstream scapy
bind_layers(MPLS, MPLS, s=0)
