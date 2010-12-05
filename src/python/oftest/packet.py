######################################################################
#
# All files associated with the OpenFlow Python Test (oftest) are
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
OpenFlow packet class

This class implements the basic abstraction of an OpenFlow packet.  It
includes parsing functionality and OpenFlow actions related to 
packet modifications.
"""

import socket
import struct
import logging
import oftest.cstruct as ofp
import unittest
import binascii
import string
import oftest.action as action

ETHERTYPE_IP = 0x0800
ETHERTYPE_VLAN = 0x8100
ETHERTYPE_VLAN_QinQ = 0x88a8
ETHERTYPE_ARP = 0x0806

DL_MASK_ALL = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
NW_MASK_ALL = 0xffffffff

class Packet(object):
    """
    Packet abstraction

    This is meant to support the abstraction of a packet in an
    OpenFlow 1.1 switch so it includes an action set, ingress port,
    and metadata.  These members may be ignored and the rest of the
    packet parsing and modification functions used to manipulate
    a packet.
    """

    def __init__(self, in_port=None, data=""):
        # Use entries in match when possible.
        self.in_port = in_port
        self.data = data
        self.bytes = len(data)
        self.match = ofp.ofp_match()
        self.logger = logging.getLogger("packet")  
        self.instructions = []
        # parsable tags
        self.ip_header_offset = None
        self.tcp_header_offset = None
        self.mpls_tag_offset = None
        self.vlan_tag_offset = None       
        self.action_set = {}
        self.queue_id = 0

        if self.data != "":
            self.parse()

    def length(self):
        return len(self.data)

    def clear_actions(self):
        self.action_set = {}

    def parse(self):
        """
        Update the headers in self.match based on self.data 
        
        Parses the relevant header features out of the packet, usieng
        the table outlined in the OF1.1 spec, Figure 4
        """
        self.bytes = len(self.data)
        self.match.in_port = self.in_port
        self.match.type = ofp.OFPMT_STANDARD
        self.match.length = ofp.OFPMT_STANDARD_LENGTH
        self.match.wildcards = 0
        
        idx = 0
        try:
            idx = self._parse_l2(idx)
            # idx = self._parse_mpls(idx)  #@todo add MPLS support
            if self.match.dl_type == ETHERTYPE_IP:
                self.ip_header_offset = idx 
                idx = self._parse_ip(idx)
                if self.match.nw_proto in [ socket.IPPROTO_TCP,
                                            socket.IPPROTO_UDP,
                                            socket.IPPROTO_ICMP]:
                    self.tcp_header_offset = idx
                    if self.match.nw_proto != socket.IPPROTO_ICMP:
                        idx = self._parse_l4(idx)
                    else:
                        idx = self._parse_icmp(idx)
            elif self.match.dl_type == ETHERTYPE_ARP:
                self._parse_arp(idx)
        except (parse_error), e:
            self.logger.warn("Giving up on parsing packet, got %s" % 
                             (str(e)))

    def _parse_arp(self, idx):
        # @todo Implement
        pass

    def _parse_l2(self, idx):
        """
        Parse Layer2 Headers of packet
        
        Parse ether src,dst,type (and vlan and QinQ headers if exists) from 
        self.data starting at idx
        """
        if self.bytes < 14 :
            raise parse_error("_parse_l2:: packet too shorter <14 bytes")
            
        self.match.dl_dst = list(struct.unpack("!6B", self.data[idx:idx+6]))
        self.match.dl_dst_mask = DL_MASK_ALL
        idx += 6
        self.match.dl_src = list(struct.unpack("!6B", self.data[idx:idx+6]))
        self.match.dl_src_mask = DL_MASK_ALL
        idx += 6
        #pdb.set_trace()
        l2_type = struct.unpack("!H", self.data[idx:idx+2])[0]
        idx += 2
        if l2_type in [ETHERTYPE_VLAN, ETHERTYPE_VLAN_QinQ] :
            blob = struct.unpack("H", self.data[idx:idx+2])
            self.match.dl_vlan_pcp = blob & 0xd000
            #cfi = blob & 0x1000     #@todo figure out what to do if cfi!=0
            self.match.dl_vlan = socket.ntohs(blob & 0x0fff)
            idx += 2
            l2_type = struct.unpack("!H", self.data[idx:idx+2])[0]
            # now skip past any more nest VLAN tags (per the spec)
            while l2_type in [ETHERTYPE_VLAN, ETHERTYPE_VLAN_QinQ] :
                idx += 4
                if self.bytes < idx :
                    raise parse_error("_parse_l2(): Too many vlan tags")
                l2_type = struct.unpack("!H", self.data[idx:idx+2])[0]
        else:
            self.match.dl_vlan = 0xFFFF
            self.match.dl_vlan_pcp = 0
        self.match.dl_type = l2_type
        return idx
            
    def _parse_ip(self, idx):
        """
        Parse IP Headers of a packet starting at self.data[idx]
        """
        if self.bytes < (idx + 20) :
            raise parse_error("_parse_ip: Invalid IP header")
        # the three blanks are id (2bytes), frag offset (2bytes), 
        # and ttl (1byte)
        (hlen_and_v, self.match.nw_tos, len, _,_,_, self.match.nw_proto) = \
            struct.unpack("!BBHHHBB", self.data[idx:idx+10])
        #@todo add fragmentation parsing
        hlen = hlen_and_v & 0x0f
        (self.match.nw_src, self.match.nw_dst) = \
            struct.unpack("!II", self.data[idx + 12:idx+20])
        self.match.nw_dst_mask = NW_MASK_ALL
        self.match.nw_src_mask = NW_MASK_ALL
        return idx + (hlen *4) # this should correctly skip IP options
    
    def _parse_l4(self, idx):
        """
        Parse the src/dst ports of UDP and TCP packets
        """
        if self.bytes < (idx + 8):
            raise parse_error("_parse_l4: Invalid L4 header")
        (self.match.tp_src, self.match.tp_dst) = \
            struct.unpack("!HH", self.data[idx:idx+4])

    def _parse_icmp(self, idx):
        """
        Parse the type/code of ICMP Packets 
        """
        if self.bytes < (idx + 4):
            raise parse_error("_parse_icmp: Invalid icmp header")
        # yes, type and code get stored into tp_dst and tp_src...
        (self.match.tp_src, self.match.tp_dst) = \
            struct.unpack("!BB", self.data[idx:idx+2])


    #
    # NOTE:  See comment string in write_action regarding exactly
    # when actions are executed (for apply vs write instructions)
    #

    def write_action(self, action):
        """
        Write the action into the packet's action set

        Note that we do nothing to the packet when the write_action
        instruction is executed.  We only record the actions for 
        later processing.  Because of this, the output port is not
        explicitly recorded in the packet; that state is recorded
        in the action_set[set_output_port] item.
        """
        self.logger.debug("Setting action " + action.show())
        self.action_set[action.__class__] = action

    def set_metadata(self, value, mask):
        self.match.metadata = (self.match.metadata & ~mask) | \
            (value & mask)

    #
    # All action functions need to take the action object for params
    #

    def action_set_output_port(self, action, switch):
        #@todo Does packet need to be repacked?
        switch.dataplane.send(action.port, self.data, queue_id=self.queue_id)

    def action_set_queue(self, action, switch):
        self.queue_id = action.queue_id

    def action_set_vlan_vid(self, action, switch):
        vid = action.vlan_vid
        # @todo Verify proper location of VLAN id
        if self.vlan_tag_offset is None:
            return
        offset = self.vlan_tag_offset
        first = self.data[offset]
        first = (first & 0xf0) | ((vid & 0xf00) >> 8)
        self.data[offset] = first
        self.data[offset + 1] = vid & 0xff

    def action_set_vlan_pcp(self, action, switch):
        pcp = action.vlan_pcp
        # @todo Verify proper location of VLAN pcp
        if self.vlan_tag_offset is None:
            return
        offset = self.vlan_tag_offset
        first = self.data[offset]
        first = (first & 0x1f) | (pcp << 5)
        self.data[offset] = first

    def action_set_dl_src(self, action, switch):
        dl_src = action.dl_addr
        # @todo Do as a slice
        for idx in range(len(dl_src)):
            self.data[6 + idx] = dl_src[idx]

    def action_set_dl_dst(self, action, switch):
        dl_dst = action.dl_addr
        # @todo Do as a slice
        for idx in range(len(dl_dst)):
            self.data[idx] = dl_dst[idx]

    def action_set_nw_src(self, action, switch):
        nw_src = action.nw_addr
        # @todo Verify byte order
        if self.ip_header_offset is None:
            return
        offset = self.ip_header_offset
        self.data[offset] = (nw_src >> 24) & 0xff
        self.data[offset + 1] = (nw_src >> 16) & 0xff
        self.data[offset + 2] = (nw_src >> 8) & 0xff
        self.data[offset + 3] = nw_src & 0xff

    def action_set_nw_dst(self, action, switch):
        nw_dst = action.nw_addr
        # @todo Verify byte order
        if self.ip_header_offset is None:
            return
        offset = self.ip_header_offset + 4
        self.data[offset] = (nw_dst >> 24) & 0xff
        self.data[offset + 1] = (nw_dst >> 16) & 0xff
        self.data[offset + 2] = (nw_dst >> 8) & 0xff
        self.data[offset + 3] = nw_dst & 0xff

    def action_set_nw_tos(self, action, switch):
        pass

    def action_set_nw_ecn(self, action, switch):
        pass

    def action_set_tp_src(self, action, switch):
        pass

    def action_set_tp_dst(self, action, switch):
        pass

    def action_copy_ttl_out(self, action, switch):
        pass

    def action_copy_ttl_in(self, action, switch):
        pass

    def action_set_mpls_label(self, action, switch):
        pass

    def action_set_mpls_tc(self, action, switch):
        pass

    def action_set_mpls_ttl(self, action, switch):
        pass

    def action_dec_mpls_ttl(self, action, switch):
        pass

    def action_push_vlan(self, action, switch):
        pass

    def action_pop_vlan(self, action, switch):
        pass

    def action_push_mpls(self, action, switch):
        pass

    def action_pop_mpls(self, action, switch):
        pass
    
    def action_experimenter(self, action, switch):
        pass

    def action_set_nw_ttl(self, action, switch):
        pass

    def action_dec_nw_ttl(self, action, switch):
        pass

    def action_group(self, action, switch):
        pass

    def execute_action_set(self, switch):
        """
        Execute the actions in the action set for the packet
        according to the order given in ordered_action_list.

        This determines the order in which
        actions in the packet's action set are executed

        @param switch The parent switch object (for sending pkts out)

        @todo Verify the ordering in this list
        """
        cls = action.action_copy_ttl_in
        if cls in self.action_set.keys():
            self.logger.debug("Action copy_ttl_in")
            self.action_copy_ttl_in(self.action_set[cls], switch)

        cls = action.action_pop_mpls
        if cls in self.action_set.keys():
            self.logger.debug("Action pop_mpls")
            self.action_pop_mpls(self.action_set[cls], switch)
        cls = action.action_pop_vlan
        if cls in self.action_set.keys():
            self.logger.debug("Action pop_vlan")
            self.action_pop_vlan(self.action_set[cls], switch)
        cls = action.action_push_mpls
        if cls in self.action_set.keys():
            self.logger.debug("Action push_mpls")
            self.action_push_mpls(self.action_set[cls], switch)
        cls = action.action_push_vlan
        if cls in self.action_set.keys():
            self.logger.debug("Action push_vlan")
            self.action_push_vlan(self.action_set[cls], switch)

        cls = action.action_dec_mpls_ttl
        if cls in self.action_set.keys():
            self.logger.debug("Action dec_mpls_ttl")
            self.action_dec_mpls_ttl(self.action_set[cls], switch)
        cls = action.action_dec_nw_ttl
        if cls in self.action_set.keys():
            self.logger.debug("Action dec_nw_ttl")
            self.action_dec_nw_ttl(self.action_set[cls], switch)
        cls = action.action_copy_ttl_out
        if cls in self.action_set.keys():
            self.logger.debug("Action copy_ttl_out")
            self.action_copy_ttl_out(self.action_set[cls], switch)

        cls = action.action_set_dl_dst
        if cls in self.action_set.keys():
            self.logger.debug("Action set_dl_dst")
            self.action_set_dl_dst(self.action_set[cls], switch)
        cls = action.action_set_dl_src
        if cls in self.action_set.keys():
            self.logger.debug("Action set_dl_src")
            self.action_set_dl_src(self.action_set[cls], switch)
        cls = action.action_set_mpls_label
        if cls in self.action_set.keys():
            self.logger.debug("Action set_mpls_label")
            self.action_set_mpls_label(self.action_set[cls], switch)
        cls = action.action_set_mpls_tc
        if cls in self.action_set.keys():
            self.logger.debug("Action set_mpls_tc")
            self.action_set_mpls_tc(self.action_set[cls], switch)
        cls = action.action_set_mpls_ttl
        if cls in self.action_set.keys():
            self.logger.debug("Action set_mpls_ttl")
            self.action_set_mpls_ttl(self.action_set[cls], switch)
        cls = action.action_set_nw_dst
        if cls in self.action_set.keys():
            self.logger.debug("Action set_nw_dst")
            self.action_set_nw_dst(self.action_set[cls], switch)
        cls = action.action_set_nw_ecn
        if cls in self.action_set.keys():
            self.logger.debug("Action set_nw_ecn")
            self.action_set_nw_ecn(self.action_set[cls], switch)
        cls = action.action_set_nw_src
        if cls in self.action_set.keys():
            self.logger.debug("Action set_nw_src")
            self.action_set_nw_src(self.action_set[cls], switch)
        cls = action.action_set_nw_tos
        if cls in self.action_set.keys():
            self.logger.debug("Action set_nw_tos")
            self.action_set_nw_tos(self.action_set[cls], switch)
        cls = action.action_set_nw_ttl
        if cls in self.action_set.keys():
            self.logger.debug("Action set_nw_ttl")
            self.action_set_nw_ttl(self.action_set[cls], switch)
        cls = action.action_set_queue
        if cls in self.action_set.keys():
            self.logger.debug("Action set_queue")
            self.action_set_queue(self.action_set[cls], switch)
        cls = action.action_set_tp_dst
        if cls in self.action_set.keys():
            self.logger.debug("Action set_tp_dst")
            self.action_set_tp_dst(self.action_set[cls], switch)
        cls = action.action_set_tp_src
        if cls in self.action_set.keys():
            self.logger.debug("Action set_tp_src")
            self.action_set_tp_src(self.action_set[cls], switch)
        cls = action.action_set_vlan_pcp
        if cls in self.action_set.keys():
            self.logger.debug("Action set_vlan_pcp")
            self.action_set_vlan_pcp(self.action_set[cls], switch)
        cls = action.action_set_vlan_vid
        if cls in self.action_set.keys():
            self.logger.debug("Action set_vlan_vid")
            self.action_set_vlan_vid(self.action_set[cls], switch)

        cls = action.action_group
        if cls in self.action_set.keys():
            self.logger.debug("Action group")
            self.action_group(self.action_set[cls], switch)
        cls = action.action_experimenter
        if cls in self.action_set.keys():
            self.logger.debug("Action experimenter")
            self.action_experimenter(self.action_set[cls], switch)
        cls = action.action_set_output_port
        if cls in self.action_set.keys():
            self.logger.debug("Action set_output_port")
            self.action_set_output_port(self.action_set[cls], switch)

class parse_error(Exception):
    """
    Thrown internally if there is an error in packet parsing
    """
    
    def __init__(self, why):
        self.why = why
        
    def __str__(self):
        return "%s:: %s" % (super.__str__(self), self.why)
        
class packet_test(unittest.TestCase):
    """
    Unit tests for packet class
    """
    
    def ascii_to_data(self, str):
        return binascii.unhexlify(str.translate(string.maketrans('',''),
                                                string.whitespace))
    
    def setUp(self):
        """
        Simple packet data for parsing tests.  

        Ethernet II, Src: Fujitsu_ef:cd:8d (00:17:42:ef:cd:8d), 
            Dst: ZhsZeitm_5d:24:00 (00:d0:05:5d:24:00)
        Internet Protocol, Src: 172.24.74.96 (172.24.74.96), 
            Dst: 171.64.74.58 (171.64.74.58)
        Transmission Control Protocol, Src Port: 59581 (59581), 
            Dst Port: ssh (22), Seq: 2694, Ack: 2749, Len: 48
        """
        pktdata = self.ascii_to_data(
            """00 d0 05 5d 24 00 00 17 42 ef cd 8d 08 00 45 10
               00 64 65 67 40 00 40 06 e9 29 ac 18 4a 60 ab 40
               4a 3a e8 bd 00 16 7c 28 2f 88 f2 bd 7a 03 80 18
               00 b5 ec 49 00 00 01 01 08 0a 00 d1 46 8b 32 ed
               7c 88 78 4b 8a dc 0a 1f c4 d3 02 a3 ae 1d 3c aa
               6f 1a 36 9f 27 11 12 71 5b 5d 88 f2 97 fa e7 f9
               99 c1 9f 9c 7f c5 1e 3e 45 c6 a6 ac ec 0b 87 64
               98 dd""")
        self.pkt = Packet(data=pktdata)

    def runTest(self):
        self.assertTrue(self.pkt)
        
class l2_parsing_test(packet_test):
    def runTest(self):
        match = self.pkt.match
        self.assertEqual(match.dl_dst,[0x00,0xd0,0x05,0x5d,0x24,0x00])
        self.assertEqual(match.dl_src,[0x00,0x17,0x42,0xef,0xcd,0x8d])
        self.assertEqual(match.dl_type,ETHERTYPE_IP)

class ip_parsing_test(packet_test):
    def runTest(self):
        match = self.pkt.match
        # @todo Verify byte ordering of the following
        self.assertEqual(match.nw_dst,0xab404a3a)
        self.assertEqual(match.nw_src,0xac184a60)
        self.assertEqual(match.nw_proto, socket.IPPROTO_TCP)

class l4_parsing_test(packet_test):
    def runTest(self):
        match = self.pkt.match
        self.assertEqual(match.tp_dst,22)
        self.assertEqual(match.tp_src,59581)

if __name__ == '__main__':
    print("Running packet tests\n")
    unittest.main()

