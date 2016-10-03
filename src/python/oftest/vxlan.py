# Virtual eXtensible Local Area Network (VXLAN)
# https://tools.ietf.org/html/draft-mahalingam-dutt-dcops-vxlan-06

#Taken from https://github.com/secdev/scapy/tree/master/scapy/layers/vxlan.py
#License Info: GNU GENERAL PUBLIC LICENSE

from scapy.packet import *
from scapy.fields import *
from scapy.all import * # Otherwise failing at the UDP reference below
from scapy.layers.l2 import Ether
from scapy.layers.inet import UDP

class ThreeBytesField(X3BytesField, ByteField):
    def i2repr(self, pkt, x):
        return ByteField.i2repr(self, pkt, x)

class VXLAN(Packet):
    name = "VXLAN"
    fields_desc = [ FlagsField("flags", 0x08, 8, ['R', 'R', 'R', 'I', 'R', 'R', 'R', 'R']),
                    X3BytesField("reserved1", 0x000000),
                    ThreeBytesField("vni", 0),
                    XByteField("reserved2", 0x00)]

    def mysummary(self):
        return self.sprintf("VXLAN (vni=%VXLAN.vni%)")

bind_layers(UDP, VXLAN, dport=4789)
bind_layers(VXLAN, Ether)
