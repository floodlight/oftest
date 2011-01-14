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
import pdb
import os

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
import collections
import oftest.action as action

ETHERTYPE_IP = 0x0800
ETHERTYPE_VLAN = 0x8100
ETHERTYPE_VLAN_QinQ = 0x88a8
ETHERTYPE_ARP = 0x0806
ETHERTYPE_MPLS = 0x8847
ETHERTYPE_MPLS_MCAST = 0x8848
ETHERTYPES_MPLS = [ETHERTYPE_MPLS, ETHERTYPE_MPLS_MCAST]

DL_MASK_ALL = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
NW_MASK_ALL = 0xffffffff

MPLS_BOTTOM_OF_STACK = 0x00000100
MplsTag = collections.namedtuple("MplsTag", "label tc ttl")

def pack_tag(mpls_tag, bos = 0):
    packed_tag = ((mpls_tag.label & 0xfffff) << 12) | \
                 ((mpls_tag.tc & 0x7) << 9) | \
                 (mpls_tag.ttl & 0xFF) | \
                 (MPLS_BOTTOM_OF_STACK if bos else 0)
    return packed_tag

def unpack_tag(packed_tag):
    tag = MplsTag(packed_tag >> 12,
                  (packed_tag >> 9) & 0x0007,
                  packed_tag & 0xFF)
    bos = bool(packed_tag & MPLS_BOTTOM_OF_STACK)
    return (tag, bos)

class Packet(object):
    """
    Packet abstraction

    This is meant to support the abstraction of a packet in an
    OpenFlow 1.1 switch so it includes an action set, ingress port,
    and metadata.  These members may be ignored and the rest of the
    packet parsing and modification functions used to manipulate
    a packet.
    """
    
    icmp_counter = 1

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

    def show(self):
        """ Return a ascii hex representation of the packet's data"""
        ret = ""
        c = 0
        for b in list(self.data):
            if c != 0:
                if c % 16  == 0:
                    ret += '\n'
                elif c % 8 == 0:
                    ret += '  '
            c += 1
            ret += "%0.2x " % struct.unpack('B', b)
        return ret

    def __repr__(self):
        return self.data
    
    def __str__(self):
        return  self.__repr__()

    def __len__(self):
        return len(self.data)

    def simple_tcp_packet(self,
                          pktlen=100, 
                          dl_dst='00:01:02:03:04:05',
                          dl_src='00:06:07:08:09:0a',
                          dl_vlan_enable=False,
                          dl_vlan=0,
                          dl_vlan_pcp=0,
                          dl_vlan_cfi=0,
                          mpls_type=None,
                          mpls_tags=None,
                          ip_src='192.168.0.1',
                          ip_dst='192.168.0.2',
                          ip_tos=0,
                          ip_ttl=64,
                          tcp_sport=1234,
                          tcp_dport=80):
        """
        Return a simple dataplane TCP packet

        Supports a few parameters:
        @param len Length of packet in bytes w/o CRC
        @param dl_dst Destinatino MAC
        @param dl_src Source MAC
        @param dl_vlan_enable True if the packet is with vlan, False otherwise
        @param dl_vlan VLAN ID
        @param dl_vlan_pcp VLAN priority
        @param ip_src IP source
        @param ip_dst IP destination
        @param ip_tos IP ToS
        @param tcp_dport TCP destination port
        @param ip_sport TCP source port

        Generates a simple TCP request.  Users shouldn't assume anything 
        about this packet other than that it is a valid ethernet/IP/TCP frame.
        """
        self.data = ""
        self._make_ip_packet(dl_dst, dl_src, dl_vlan_enable, dl_vlan, 
                             dl_vlan_pcp, dl_vlan_cfi, mpls_type, mpls_tags, 
                             ip_tos, ip_ttl, ip_src, ip_dst, socket.IPPROTO_TCP)

        # Add TCP header
        self.data += struct.pack("!HHLLBBHHH",
                                 tcp_sport,
                                 tcp_dport,
                                 1,     # tcp.seq
                                 0,     # tcp.ack
                                 0x50,  # tcp.doff + tcp.res1
                                 0x12,  # tcp.syn + tcp.ack
                                 0,     # tcp.wnd
                                 0,     # tcp.check
                                 0,     # tcp.urgent pointer
                                 )

        # Fill out packet
        self.data += "D" * (pktlen - len(self.data))
        return self
    
    def simple_icmp_packet(self,
                          pktlen=100, 
                          dl_dst='00:01:02:03:04:05',
                          dl_src='00:06:07:08:09:0a',
                          dl_vlan_enable=False,
                          dl_vlan=0,
                          dl_vlan_pcp=0,
                          dl_vlan_cfi=0,
                          ip_src='192.168.0.1',
                          ip_dst='192.168.0.2',
                          ip_tos=0,
                          ip_ttl=64,
                          icmp_type=8, # ICMP_ECHO_REQUEST
                          icmp_code=0, 
                          ):
        """
        Return a simple dataplane ICMP packet

        Supports a few parameters:
        @param len Length of packet in bytes w/o CRC
        @param dl_dst Destinatino MAC
        @param dl_src Source MAC
        @param dl_vlan_enable True if the packet is with vlan, False otherwise
        @param dl_vlan VLAN ID
        @param dl_vlan_pcp VLAN priority
        @param ip_src IP source
        @param ip_dst IP destination
        @param ip_tos IP ToS
        @param tcp_dport TCP destination port
        @param ip_sport TCP source port

        Generates a simple TCP request.  Users shouldn't assume anything 
        about this packet other than that it is a valid ethernet/IP/TCP frame.
        """
        self.data = ""
        self._make_ip_packet(dl_dst, dl_src, dl_vlan_enable, dl_vlan, 
                             dl_vlan_pcp, dl_vlan_cfi, None, None, ip_tos, ip_ttl, ip_src, 
                             ip_dst, socket.IPPROTO_ICMP)

        # Add ICMP header
        self.data += struct.pack("!BBHHH",
                                 icmp_type,
                                 icmp_code,
                                 0,  # icmp.checksum
                                 os.getpid() & 0xffff,  # icmp.echo.id
                                 Packet.icmp_counter   # icmp.echo.seq
                                 )                  
        Packet.icmp_counter += 1       

        # Fill out packet
        self.data += "D" * (pktlen - len(self.data))

        return self

    
    def _make_ip_packet(self, dl_dst, dl_src, dl_vlan_enable, dl_vlan, 
                          dl_vlan_pcp, dl_vlan_cfi, mpls_type, mpls_tags, 
                          ip_tos, ip_ttl, ip_src, ip_dst, ip_proto):
        self.data = ""
        addr = dl_dst.split(":")
        for byte in map(lambda z: int(z, 16), addr):
            self.data += struct.pack("!B", byte)
        addr = dl_src.split(":")
        for byte in map(lambda z: int(z, 16), addr):
            self.data += struct.pack("!B", byte)

        if (dl_vlan_enable):
            # Form and add VLAN tag
            self.data += struct.pack("!H", 0x8100)
            vtag = dl_vlan | dl_vlan_pcp >> 12 | dl_vlan_cfi >> 15
            self.data += struct.pack("!H", vtag)
            
        if mpls_tags and len(mpls_tags):
            # Add type/len field
            self.data += struct.pack("!H", mpls_type)
            mpls_tags = list(mpls_tags)          
            while len(mpls_tags):
                tag = mpls_tags.pop(0)
                packed_tag = pack_tag(tag, bos = not len(mpls_tags))
                self.data += struct.pack("!I", packed_tag)
            
        else:
            # Add type/len field
            self.data += struct.pack("!H", ETHERTYPE_IP)

        # Add IP header
        v_and_hlen = 0x45  # assumes no ip or tcp options
        ip_len = 120 + 40  # assumes no ip or tcp options
        self.data += struct.pack("!BBHHHBBH", v_and_hlen, ip_tos, ip_len, 
                                 0, # ip.id 
                                 0, # ip.frag_off
                                 ip_ttl, # ip.ttl
                                 ip_proto,
                                 0)  # ip.checksum
        # convert  ipsrc/dst to ints
        self.data += struct.pack("!LL", ascii_ip_to_bin(ip_src), 
                                 ascii_ip_to_bin(ip_dst))

    def length(self):
        return len(self.data)

    def clear_actions(self):
        self.action_set = {}

    def parse(self):
        """
        Update the headers in self.match based on self.data 
        
        Parses the relevant header features out of the packet, using
        the table outlined in the OF1.1 spec, Figure 4
        """
        self.bytes = len(self.data)
        self.match.in_port = self.in_port
        self.match.type = ofp.OFPMT_STANDARD
        self.match.length = ofp.OFPMT_STANDARD_LENGTH
        self.match.wildcards = 0
        self.match.nw_dst_mask = 0
        self.match.nw_dst_mask = 0
        self.match.dl_dst_mask = [ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        self.match.dl_src_mask = [ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        self.mpls_tag_offset = None
        self.ip_header_offset = None
        
        idx = 0
        try:
            idx = self._parse_l2(idx)
            
            if self.match.dl_type in ETHERTYPES_MPLS:
                self.mpls_tag_offset = idx
                idx = self._parse_mpls(idx)
            elif self.match.dl_type == ETHERTYPE_IP:
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
            return None
        return self.match

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
            blob = struct.unpack("H", self.data[idx:idx+2])[0]
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
      
    def _parse_mpls(self, idx):
        """
        Parse MPLS Header starting at self.data[idx]
        """
        if self.bytes < (idx + 4):
            raise parse_error("_parse_mpls:  Invalid MPLS header")
        
        tag = struct.unpack("!I", self.data[idx:idx+4])[0]
        self.match.mpls_label = tag >> 12
        self.match.mpls_tc = (tag >> 9) & 0x0007        
        return idx + 4
            
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
        self.action_set[action.__class__] = action

    def _set_1bytes(self,offset,byte):
        """ Writes the byte at data[offset] 
        
        This function only exists to match the other _set_Xbytes() and
        is trivial
    
        """
        tmp= "%s%s" % (self.data[0:offset], 
                               struct.pack('B',byte & 0xff))
        if len(self.data) > offset + 1 :
            tmp += self.data[offset+1:len(self.data)]
        self.data=tmp

    def _set_2bytes(self,offset,short):
        """ Writes the 2 byte short in network byte order at data[offset] """
        tmp= "%s%s" % (self.data[0:offset], 
                               struct.pack('!H',short & 0xffff))
        if len(self.data) > offset + 2 :
            tmp += self.data[offset+2:len(self.data)]
        self.data=tmp

    def _set_4bytes(self,offset,word,forceNBO=True):
        """ Writes the 4 byte word at data[offset] 
        
        Use network byte order if forceNBO is True,
        else it's assumed that word is already in NBO
        
        """
        # @todo Verify byte order
        #pdb.set_trace()
        fmt ="L"
        if forceNBO:
            fmt = '!' + fmt 
        
        tmp= "%s%s" % (self.data[0:offset], 
                               struct.pack(fmt,word & 0xffffffff))
        if len(self.data) > offset + 4 :
            tmp += self.data[offset+4:len(self.data)]
        self.data=tmp
        
    def _set_6bytes(self,offset,byte_list):
        """ Writes the 6 byte sequence in the given order to data[offset] """
        # @todo Do as a slice
        tmp= self.data[0:offset] 
        tmp += struct.pack("BBBBBB", *byte_list)
        if len(self.data) > offset + 6 :
            tmp += self.data[offset+6:len(self.data)]
        self.data=tmp
    
    def _update_l4_checksum(self):
        """ Recalculate the L4 checksum, if there
        
        Can be safely called on non-tcp/non-udp packets as a NOOP
        """
        if (self.ip_header_offset is None or 
            self.tcp_header_offset is None):
            return
        if self.match.nw_proto == socket.IPPROTO_TCP:
            return self._update_tcp_checksum()
        elif self.match.nw_proto == socket.IPPROTO_UDP:
            return self._update_udp_checksum()
        
    def _update_tcp_checksum(self):
        """ Recalculate the TCP checksum
        
        @warning:  Must only be called on actual TCP Packets
        """
        #@todo implemnt tcp checksum update
        pass
    
    def _update_udp_checksum(self):
        """ Recalculate the TCP checksum
        
        @warning:  Must only be called on actual TCP Packets
        """
        #@todo implemnt udp checksum update
        pass

    def set_metadata(self, value, mask):
        self.match.metadata = (self.match.metadata & ~mask) | \
            (value & mask)

    #
    # These are the main action operations that take the 
    # required parameters
    # 
    # Note that 'group', 'experimenter' and 'set_output_port' are only 
    # implemented for the action versions.

    def set_queue(self, queue_id):
        self.queue_id = queue_id

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
        self._set_6bytes(6, dl_src)

    def set_dl_dst(self, dl_dst):
        self._set_6bytes(0, dl_dst)
        
    def set_nw_src(self, nw_src):
        if self.ip_header_offset is None:
            return
        self._set_4bytes(self.ip_header_offset + 12, nw_src)
        self._update_l4_checksum()
    
    def set_nw_dst(self, nw_dst):
        # @todo Verify byte order
        if self.ip_header_offset is None:
            return
        self._set_4bytes(self.ip_header_offset + 16, nw_dst)
        self._update_l4_checksum()

    def set_nw_tos(self, tos):
        if self.ip_header_offset is None:
            return
        self._set_1bytes(self.ip_header_offset + 1, tos)

    def set_nw_ecn(self, ecn):
        #@todo look up ecn implementation details
        pass

    def set_tp_src(self, tp_src):
        if self.tcp_header_offset is None:
            return
        if (self.match.nw_proto == socket.IPPROTO_TCP or
            self.match.nw_proto == socket.IPPROTO_UDP): 
            self._set_2bytes(self.tcp_header_offset, tp_src)
        elif (self.match.nw_proto == socket.IPPROTO_ICMP):
            self._set_1bytes(self.tcp_header_offset, tp_src)
        self._update_l4_checksum()
            
    def set_tp_dst(self, tp_dst):
        if self.tcp_header_offset is None:
            return
        if (self.match.nw_proto == socket.IPPROTO_TCP or
            self.match.nw_proto == socket.IPPROTO_UDP): 
            self._set_2bytes(self.tcp_header_offset +2, tp_dst)
        elif (self.match.nw_proto == socket.IPPROTO_ICMP):
            self._set_1bytes(self.tcp_header_offset + 1, tp_dst)
        self._update_l4_checksum()

    def copy_ttl_out(self):
        pass

    def copy_ttl_in(self):
        pass

    def set_mpls_label(self, mpls_label):
        if self.mpls_tag_offset is None:
            return
        tag = struct.unpack("!I", self.data[self.mpls_tag_offset:
                                            self.mpls_tag_offset+4])[0]
        tag = ((mpls_label & 0xfffff) << 12) | (tag & 0x00000fff)     
        self._set_4bytes(self.mpls_tag_offset, tag)

    def set_mpls_tc(self, mpls_tc):
        if self.mpls_tag_offset is None:
            return
        tag = struct.unpack("!I", self.data[self.mpls_tag_offset:
                                            self.mpls_tag_offset+4])[0]
        tag = ((mpls_tc & 0x7) << 9) | (tag & 0xfffff1ff)     
        self._set_4bytes(self.mpls_tag_offset, tag)

    def set_mpls_ttl(self, ttl):
        if self.mpls_tag_offset is None:
            return   
        self._set_1bytes(self.mpls_tag_offset + 3, ttl)

    def dec_mpls_ttl(self):
        if self.mpls_tag_offset is None:
            return
        ttl = struct.unpack("B", self.data[self.mpls_tag_offset + 3])[0]
        self.set_mpls_ttl(ttl - 1)

    def push_vlan(self, ethertype):
        pass

    def pop_vlan(self):
        pass

    IP_OFFSET_TTL = 8
    
    def push_mpls(self, ethertype):
        tag = MplsTag(0, 0, 0)
        bos = False
        
        if self.mpls_tag_offset:
            # The new tag defaults to the old one.
            packed_tag = struct.unpack("!I", self.data[self.mpls_tag_offset:
                                                       self.mpls_tag_offset+4])[0]
            (tag, _) = unpack_tag(packed_tag)
            
        else:
            # Pushing a new label stack, set the BoS bit and ethertype
            self._set_2bytes(12, ethertype)
            bos = True
            # And get TTL from IP.
            if self.ip_header_offset:
                ttl = struct.unpack("B", self.data[self.ip_header_offset + \
                                                       Packet.IP_OFFSET_TTL])[0]
                tag = MplsTag(0, 0, ttl)
                                                       
        self.data = self.data[0:14] + \
                    struct.pack("!I", pack_tag(tag, bos)) + \
                    self.data[14:]
        
        # Reparse to update offsets, ethertype, etc.
        self.parse()
            
    def pop_mpls(self, ethertype):
        # Ignore if no existing tags.
        if self.mpls_tag_offset:
            # If the existing tag has the BoS bit set, this is the bottom.
            tag = struct.unpack("!I", self.data[self.mpls_tag_offset:
                                                self.mpls_tag_offset+4])[0]
            bos = bool(tag & MPLS_BOTTOM_OF_STACK)
            
            self.data = self.data[0:self.mpls_tag_offset] + \
                        self.data[self.mpls_tag_offset + 4:]
            if bos:
                self._set_2bytes(12, ethertype)
            
            # Reparse to update offsets, ethertype, etc.
            self.parse()
    
    def set_nw_ttl(self, ttl):
        if self.ip_header_offset is None:
            return
        self._set_1bytes(self.ip_header_offset + Packet.IP_OFFSET_TTL, ttl)
        self._update_l4_checksum()

    def dec_nw_ttl(self):
        if self.ip_header_offset is None:
            return
        self.set_nw_ttl(self.data[self.ip_header_offset + 
                                  Packet.IP_OFFSET_TTL] - 1)

    #
    # All action functions need to take the action object for params
    # These take an action object to facilitate the switch implementation
    #

    def action_set_output_port(self, action, switch):
        if action.port < ofp.OFPP_MAX:
            switch.dataplane.send(action.port, self.data, 
                                  queue_id=self.queue_id)
        elif action.port == ofp.OFPP_ALL:
            for of_port in switch.ports.iterkeys():
                if of_port != self.in_port: 
                    switch.dataplane.send(of_port, self.data, 
                                          queue_id=self.queue_id)
        elif action.port == ofp.OFPP_IN_PORT:
            switch.dataplane.send(self.in_port, self.data, 
                                  queue_id=self.queue_id)
        else:
            switch.logger.error("NEED to implement action_set_output_port" + 
                                " for port %d" % action.port)        

    def action_set_queue(self, action, switch):
        self.set_queue(action.queue_id)

    def action_set_vlan_vid(self, action, switch):
        self.set_vlan_vid(action.vlan_vid)

    def action_set_vlan_pcp(self, action, switch):
        self.set_vlan_pcp(action.vlan_pcp)

    def action_set_dl_src(self, action, switch):
        self.set_dl_src(action.dl_addr)

    def action_set_dl_dst(self, action, switch):
        self.set_dl_dst(action.dl_addr)

    def action_set_nw_src(self, action, switch):
        self.set_nw_src(action.nw_addr)

    def action_set_nw_dst(self, action, switch):
        self.set_nw_dst(action.nw_addr)

    def action_set_nw_tos(self, action, switch):
        self.set_nw_tos(action.nw_tos)

    def action_set_nw_ecn(self, action, switch):
        self.set_nw_ecn(action.nw_ecn)

    def action_set_tp_src(self, action, switch):
        self.set_tp_src(action.tp_port)

    def action_set_tp_dst(self, action, switch):
        self.set_tp_dst(action.tp_port)

    def action_copy_ttl_out(self, action, switch):
        self.copy_ttl_out()

    def action_copy_ttl_in(self, action, switch):
        self.copy_ttl_in()

    def action_set_mpls_label(self, action, switch):
        self.set_mpls_label(action.mpls_label)

    def action_set_mpls_tc(self, action, switch):
        self.set_mpls_tc(action.mpls_tc)

    def action_set_mpls_ttl(self, action, switch):
        self.set_mpls_ttl(action.mpls_ttl)

    def action_dec_mpls_ttl(self, action, switch):
        self.dec_mpls_ttl()

    def action_push_vlan(self, action, switch):
        self.push_vlan(action.ethertype)

    def action_pop_vlan(self, action, switch):
        self.pop_vlan()

    def action_push_mpls(self, action, switch):
        self.push_mpls(action.ethertype)

    def action_pop_mpls(self, action, switch):
        self.pop_mpls(action.ethertype)
    
    def action_experimenter(self, action, switch):
        pass

    def action_set_nw_ttl(self, action, switch):
        self.set_nw_ttl(action.nw_ttl)

    def action_dec_nw_ttl(self, action, switch):
        self.dec_nw_ttl()

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


def ascii_ip_to_bin(ip):
        """ Take '192.168.0.1' and return the NBO decimal equivalent 0xc0a80101 """
        #Lookup the cleaner, one-line way of doing this
        # or if there isn't just a library (!?)
        s = ip.split('.')
        return struct.unpack("!L", struct.pack("BBBB", int(s[0]), 
                                               int(s[1]), 
                                               int(s[2]), 
                                               int(s[3]) ))[0]
    

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
        
        """
        MPLS packet data for MPLS parsing tests.  

        Ethernet II, Src: Fujitsu_ef:cd:8d (00:17:42:ef:cd:8d), 
            Dst: ZhsZeitm_5d:24:00 (00:d0:05:5d:24:00)
        MPLS, Label: 0xFEFEF, TC: 5, S: 1, TTL: 0xAA
        Internet Protocol, Src: 172.24.74.96 (172.24.74.96), 
            Dst: 171.64.74.58 (171.64.74.58)
        Transmission Control Protocol, Src Port: 59581 (59581), 
            Dst Port: ssh (22), Seq: 2694, Ack: 2749, Len: 48
        """
        mplspktdata = self.ascii_to_data(
            """00 d0 05 5d 24 00 00 17 42 ef cd 8d 88 47
               FE FE FB AA
               45 10 00 64 65 67 40 00 40 06 e9 29 ac 18 4a 60 
               ab 40 4a 3a 
               e8 bd 00 16 7c 28 2f 88 f2 bd 7a 03 80 18
               00 b5 ec 49 00 00 01 01 08 0a 00 d1 46 8b 32 ed
               7c 88 78 4b 8a dc 0a 1f c4 d3 02 a3 ae 1d 3c aa
               6f 1a 36 9f 27 11 12 71 5b 5d 88 f2 97 fa e7 f9
               99 c1 9f 9c 7f c5 1e 3e 45 c6 a6 ac ec 0b 87 64
               98 dd""")
        self.mplspkt = Packet(data=mplspktdata)

    def runTest(self):
        self.assertTrue(self.pkt)
        
class l2_parsing_test(packet_test):
    def runTest(self):
        match = self.pkt.match
        self.assertEqual(match.dl_dst,[0x00,0xd0,0x05,0x5d,0x24,0x00])
        self.assertEqual(match.dl_src,[0x00,0x17,0x42,0xef,0xcd,0x8d])
        self.assertEqual(match.dl_type,ETHERTYPE_IP)
        
class mpls_parsing_test(packet_test):
    def runTest(self):
        match = self.mplspkt.match
        self.assertEqual(match.mpls_label, 0xFEFEF)
        self.assertEqual(match.mpls_tc, 5)

class ip_parsing_test(packet_test):
    def runTest(self):
        match = self.pkt.match
        # @todo Verify byte ordering of the following
        self.assertEqual(match.nw_dst,ascii_ip_to_bin('171.64.74.58'))
        self.assertEqual(match.nw_src,ascii_ip_to_bin('172.24.74.96'))
        self.assertEqual(match.nw_proto, socket.IPPROTO_TCP)

class mpls_setting_test(packet_test):
    def runTest(self):
        orig_len = len(self.mplspkt)
        label = 0x12345
        tc = 6
        ttl = 0x78
        self.mplspkt.set_mpls_label(label)
        self.mplspkt.set_mpls_tc(tc)
        self.mplspkt.set_mpls_ttl(ttl)
        self.mplspkt.dec_mpls_ttl()
        self.mplspkt.parse()
        
        self.assertEqual(len(self.mplspkt), orig_len)
        self.assertTrue(self.mplspkt.mpls_tag_offset)
        match = self.mplspkt.match
        
        self.assertEqual(match.mpls_label, label)
        self.assertEqual(match.mpls_tc, tc)
        new_ttl = struct.unpack("B", self.mplspkt.data[self.mplspkt.mpls_tag_offset + 3:
                                                       self.mplspkt.mpls_tag_offset + 4])[0]
        self.assertEqual(new_ttl, ttl - 1)

class mpls_pop_test(packet_test):
    def runTest(self):
        orig_len = len(self.mplspkt)
        self.mplspkt.pop_mpls(ETHERTYPE_IP)
        self.mplspkt.parse()
        
        self.assertEqual(len(self.mplspkt), orig_len - 4)
        self.assertFalse(self.mplspkt.mpls_tag_offset)
        match = self.mplspkt.match
        
        self.assertEqual(match.dl_type,ETHERTYPE_IP)
        self.assertEqual(match.nw_dst,ascii_ip_to_bin('171.64.74.58'))
        self.assertEqual(match.nw_src,ascii_ip_to_bin('172.24.74.96'))
        self.assertEqual(match.nw_proto, socket.IPPROTO_TCP)
        
class mpls_push_test(packet_test):
    def runTest(self):
        orig_len = len(self.pkt)
        self.pkt.push_mpls(ETHERTYPE_MPLS)
        self.pkt.parse()
        
        self.assertEqual(len(self.pkt), orig_len + 4)
        self.assertTrue(self.pkt.mpls_tag_offset)
        match = self.pkt.match
        
        self.assertEqual(match.dl_type, ETHERTYPE_MPLS)
        self.assertEqual(match.mpls_label, 0)
        self.assertEqual(match.mpls_tc, 0)

class ip_setting_test(packet_test):
    def runTest(self):
        orig_len = len(self.pkt)
        ip1 = '11.22.33.44'
        ip2 = '55.66.77.88'
        self.pkt.set_nw_src(ascii_ip_to_bin(ip1))
        self.pkt.set_nw_dst(ascii_ip_to_bin(ip2))
        self.pkt.parse()
        self.assertEqual(len(self.pkt), orig_len)
        match = self.pkt.match
        
        # @todo Verify byte ordering of the following
        self.assertEqual(match.nw_src,ascii_ip_to_bin(ip1))
        self.assertEqual(match.nw_dst,ascii_ip_to_bin(ip2))
        



class l4_parsing_test(packet_test):
    def runTest(self):
        match = self.pkt.match
        self.assertEqual(match.tp_dst,22)
        self.assertEqual(match.tp_src,59581)

class l4_setting_test(packet_test):
    def runTest(self):
        orig_len = len(self.pkt)
        self.pkt.set_tp_src(777)
        self.pkt.set_tp_dst(666)
        self.pkt.parse()
        self.assertEqual(len(self.pkt), orig_len)
        match = self.pkt.match
        self.assertEqual(match.tp_src,777)
        self.assertEqual(match.tp_dst,666)


class simple_tcp_test(unittest.TestCase):
    """ Make sure that simple_tcp_test does what it should 
                          pktlen=100, 
                          dl_dst='00:01:02:03:04:05',
                          dl_src='00:06:07:08:09:0a',
                          dl_vlan_enable=False,
                          dl_vlan=0,
                          dl_vlan_pcp=0,
                          dl_vlan_cfi=0,
                          ip_src='192.168.0.1',
                          ip_dst='192.168.0.2',
                          ip_tos=0,
                          tcp_sport=1234,
                          tcp_dport=80):
    """
    def setUp(self):
        self.pkt = Packet().simple_tcp_packet()
        self.pkt.parse()
       
    def runTest(self):
        match = self.pkt.match
        self.assertEqual(match.dl_dst, [0x00, 0x01, 0x02, 0x03, 0x04, 0x05])
        self.assertEqual(match.dl_src, [0x00, 0x06, 0x07, 0x08, 0x09, 0x0a])
        self.assertEqual(match.dl_type, ETHERTYPE_IP)
        self.assertEqual(match.nw_src, ascii_ip_to_bin('192.168.0.1'))
        self.assertEqual(match.nw_dst, ascii_ip_to_bin('192.168.0.2'))
        self.assertEqual(match.tp_dst, 80)
        self.assertEqual(match.tp_src, 1234)
        
class simple_tcp_with_mpls_test(unittest.TestCase):
    """ Make sure that simple_tcp_packet does what it should 
                          pktlen=100, 
                          dl_dst='00:01:02:03:04:05',
                          dl_src='00:06:07:08:09:0a',
                          dl_vlan_enable=False,
                          dl_vlan=0,
                          dl_vlan_pcp=0,
                          dl_vlan_cfi=0,
                          ip_src='192.168.0.1',
                          ip_dst='192.168.0.2',
                          ip_tos=0,
                          tcp_sport=1234,
                          tcp_dport=80):
    """
    def setUp(self):
        tag1 = MplsTag(0xabcde, 0x5, 0xAA)
        tag2 = MplsTag(0x54321, 0x2, 0xBB)
        mpls_tags = (tag1, tag2)        
        
        self.pkt = Packet().simple_tcp_packet(mpls_type=ETHERTYPE_MPLS,
                                              mpls_tags=mpls_tags)
        self.pkt.parse()
       
    def runTest(self):
        match = self.pkt.match
        self.assertEqual(match.dl_dst, [0x00, 0x01, 0x02, 0x03, 0x04, 0x05])
        self.assertEqual(match.dl_src, [0x00, 0x06, 0x07, 0x08, 0x09, 0x0a])
        self.assertEqual(match.dl_type, ETHERTYPE_MPLS)
        self.assertEqual(match.mpls_label, 0xabcde)
        self.assertEqual(match.mpls_tc, 0x5)

if __name__ == '__main__':
    print("Running packet tests\n")
    unittest.main()

