######################################################################
#
# All files associated with the OpenFlow Python Switch (ofps) are
# made available for public use and benefit with the expectation
# that others will use, modify and enhance the Software and contribute
# those enhancements back to the community. However, since we would
# like to make the Software available for broadest use, with as few
# restrictions as possible permission is hereby granted, free of
# charge, to any person obtaining a copy of this Software to deal in
# the Software under the copyrights without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject
# to the following conditions:
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# 
######################################################################

"""
OFPS packet class

This class implements the basic abstraction of a packet for OFPS.  It
includes parsing functionality and OpenFlow actions related to 
packet modifications.

"""

from oftest.cstruct import ofp_match

class Packet:
    """
    Packet abstraction for packet object while in the switch
    """

    def __init__(self, in_port=None, data=""):
        # Use entries in match when possible.
        self.in_port = in_port
        self.data = data
        self.bytes = len(data)
        self.output_port = None
        self.queue = None
        self.ip_header_offset = None
        self.tcp_header_offset = None
        self.mpls_tag_offset = None
        self.vlan_tag_offset = None
        self.match = ofp_match()
        if self.data != "":
            self.parse()

    def length(self):
        return len(self.data)

    def parse(self):
        self.bytes = len(self.data)
        #@todo Parse structure into self.match (ofp_match object)
        #@todo determine mpls_tag_offset
        #@todo determine vlan_tag_offset
        #@todo determine ip_addr_offset
        #@todo determine tcp_addr_offset

    def set_output_port(self, port):
        self.output_port = port

    def set_metadata(self, value, mask):
        self.match.metadata = (self.match.metadata & ~mask) | \
            (value & mask)

    def set_queue(self, queue):
        self.queue = queue

    def set_vlan_vid(self, vid):
        # @todo Verify proper location of VLAN id
        if self.vlan_tag_offset is None:
            return
        offset = self.vlan_tag_offset
        first = self.data[offset]
        first = (first & 0xf0) | ((vid & 0xf00) >> 8)
        self.data[offset] = first
        self.data[offset + 1] = vid & 0xff

    def set_vlan_pcp(self, pcp):
        # @todo Verify proper location of VLAN pcp
        if self.vlan_tag_offset is None:
            return
        offset = self.vlan_tag_offset
        first = self.data[offset]
        first = (first & 0x1f) | (pcp << 5)
        self.data[offset] = first

    def set_dl_src(self, dl_src):
        # @todo Do as a slice
        for idx in range(len(dl_src)):
            self.data[6+idx] = dl_src[idx]

    def set_dl_dst(self, dl_dst):
        # @todo Do as a slice
        for idx in range(len(dl_dst)):
            self.data[idx] = dl_dst[idx]

    def set_nw_src(self, nw_src):
        # @todo Verify byte order
        if self.ip_header_offset is None:
            return
        offset = self.ip_header_offset
        self.data[offset] = (nw_src >> 24) & 0xff
        self.data[offset + 1] = (nw_src >> 16) & 0xff
        self.data[offset + 2] = (nw_src >> 8) & 0xff
        self.data[offset + 3] = nw_src & 0xff

    def set_nw_dst(self, nw_dst):
        # @todo Verify byte order
        if self.ip_header_offset is None:
            return
        offset = self.ip_header_offset + 4
        self.data[offset] = (nw_dst >> 24) & 0xff
        self.data[offset + 1] = (nw_dst >> 16) & 0xff
        self.data[offset + 2] = (nw_dst >> 8) & 0xff
        self.data[offset + 3] = nw_dst & 0xff

    def set_nw_tos(self, nw_tos):
        pass

    def set_nw_ecn(self, nw_ecn):
        pass

    def set_tp_src(self, tp_src):
        pass

    def set_tp_dst(self, tp_dst):
        pass

    def copy_ttl_out(self, packet):
        pass

    def copy_ttl_in(self, packet):
        pass

    def set_mpls_label(self, mpls_label):
        pass

    def set_mpls_tc(self, mpls_tc):
        pass

    def set_mpls_ttl(self, mpls_ttl):
        pass

    def dec_mpls_ttl(self, packet):
        pass

    def push_vlan(self, packet):
        pass

    def pop_vlan(self, packet):
        pass

    def push_mpls(self, packet):
        pass

    def pop_mpls(self, packet):
        pass

    def set_nw_ttl(self, nw_ttl):
        pass

    def dec_nw_ttl(self, packet):
        pass


