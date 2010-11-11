
from oftest.cstruct import ofp_match

class Packet:
    """
    Packet abstraction for packet object while in the switch
    """

    def __init__(in_port=None, data=""):
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
        if data != "":
            self.parse()

    def length(self):
        return len(self.data)

    def parse(self):
        self.bytes = len(data)
        #@todo Parse structure into self.match (ofp_match object)
        #@todo determine mpls_tag_offset
        #@todo determine vlan_tag_offset
        #@todo determine ip_addr_offset
        #@todo determine tcp_addr_offset

    def set_output_port(self, port):
        self.output_port = port

    def set_metadata(self, data, mask):
        self.match.metadata = (self.match.metadata & ~mask) | (data & mask)

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


