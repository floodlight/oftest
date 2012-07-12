
# Python OpenFlow instruction wrapper classes

import ipaddr
from cstruct import *


class oxm_tlv:
    def __init__(self, field, hasmask, length, value, mask=None, class_ = 0x8000):
        self.class_ = class_
        self.field = field
        self.hasmask = hasmask
        self.length = length
        self.value = value
        self.mask = mask
    
    def pack(self, assertstruct=True):
        
        packed = ""
        packed += struct.pack("!I", ((self.class_ << 16) | (self.field << 9) | (self.hasmask << 8) | self.length))
        if self.length == 1:
            packed += struct.pack("B", self.value)
            if self.hasmask:
                packed += struct.pack("B", self.mask)
        elif self.length == 2 or (self.length == 4 and self.hasmask == True):
            packed += struct.pack("!H", self.value)
            if self.hasmask:
                packed += struct.pack("!H", self.mask)
        elif self.length == 4 or (self.length == 8 and self.hasmask == True):
            packed += struct.pack("!I", self.value)
            if self.hasmask:
                packed += struct.pack("!I", self.mask)
        elif self.length == 6 or self.length == 12:
            packed += struct.pack("!BBBBBB", self.value[0],self.value[1],self.value[2],self.value[3],self.value[4],self.value[5])
            if self.hasmask:
                packed += struct.pack("!BBBBBB", self.mask[0],self.mask[1],self.mask[2],self.mask[3],self.mask[4],self.mask[5])
        elif self.length == 8 or (self.length == 16 and self.hasmask == True):
            packed += struct.pack("!Q", self.value)
            if self.hasmask:
                packed += struct.pack("!Q", self.mask)
        elif self.length == 16 or self.length == 32:
            packed += self.value.packed
            if self.hasmask:
                packed += self.mask.packed
        return packed
    
    def __len__(self):
        return self.length + 4
    
    def show(self, prefix=''):
        return "\n".join(
        ("oxm_tlv_class=" + hex(self.class_),
        "oxm_tlv_field=" + hex(self.field),
        "oxm_tlv_hasmask=" + str(bool(self.hasmask)),
        "oxm_tlv_length: " + hex(self.length),
        "value: " + str(self.value),))


def roundup (x,y): 
    return (((x) + ((y) - 1)) / (y) * (y))

class in_port(oxm_tlv):
    """
    Wrapper class for in_port match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_IN_PORT , hasmask, 4, value)
    def show(self, prefix=''):
        outstr = prefix + "in_port\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr


class in_phy_port(oxm_tlv):
    """
    Wrapper class for in_phy_port match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self,OFPXMT_OFB_IN_PHY_PORT, hasmask, 4, value)
    def show(self, prefix=''):
        outstr = prefix + "in_phy_port\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr


class metadata(oxm_tlv):
    """
    Wrapper class for metadata match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, mask = None):
        if mask == None:
            oxm_tlv.__init__(self, OFPXMT_OFB_METADATA, False, 8, value)
        else:
            oxm_tlv.__init__(self, OFPXMT_OFB_METADATA, True, 16, value, mask)            
    def show(self, prefix=''):
        outstr = prefix + "metadata\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr

class eth_dst(oxm_tlv):
    """
    Wrapper class for eth_dst match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, mask = None):
        if mask == None:
            oxm_tlv.__init__(self, OFPXMT_OFB_ETH_DST, False, 6, value)
        else:
            oxm_tlv.__init__(self, OFPXMT_OFB_ETH_DST, True, 12, value, mask)            
    def show(self, prefix=''):
        outstr = prefix + "eth_dst\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr
  
class eth_src(oxm_tlv):
    """
    Wrapper class for eth_src match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        if not hasmask:
            oxm_tlv.__init__(self, OFPXMT_OFB_ETH_SRC, hasmask, 6, value)
        else:
            oxm_tlv.__init__(self, OFPXMT_OFB_ETH_SRC, hasmask, 12, value, mask)            
    def show(self, prefix=''):
        outstr = prefix + "eth_src\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr

class eth_type(oxm_tlv):
    """
    Wrapper class for eth_type match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_ETH_TYPE, hasmask, 2, value)
    def show(self, prefix=''):
        outstr = prefix + "eth_type\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr

class vlan_vid(oxm_tlv):
    """
    Wrapper class for vlan_vid match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_VLAN_VID, hasmask, 2, value)
    def show(self, prefix=''):
        outstr = prefix + "vlan_vid\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr

class vlan_pcp(oxm_tlv):
    """
    Wrapper class for vlan_pcp match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_VLAN_PCP, hasmask, 1, value)
    def show(self, prefix=''):
        outstr = prefix + "vlan_pcp\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr
        
class ip_dscp(oxm_tlv):
    """
    Wrapper class for ip_dscp match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_IP_DSCP, hasmask, 1, value)
    def show(self, prefix=''):
        outstr = prefix + "ip_dscp\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr

class ip_ecn(oxm_tlv):
    """
    Wrapper class for ip_dscp match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_IP_ECN, hasmask, 1, value)
    def show(self, prefix=''):
        outstr = prefix + "ip_ecn\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr

class ip_proto(oxm_tlv):
    """
    Wrapper class for ip_proto match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_IP_PROTO, hasmask, 1, value)
    def show(self, prefix=''):
        outstr = prefix + "ip_proto\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr

class ipv4_src(oxm_tlv):
    """
    Wrapper class for ipv4_src match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        if not hasmask:
            oxm_tlv.__init__(self, OFPXMT_OFB_IPV4_SRC, hasmask, 4, value)
        else: 
            oxm_tlv.__init__(self, OFPXMT_OFB_IPV4_SRC, hasmask, 4, value, mask)
    def show(self, prefix=''):
        outstr = prefix + "ipv4_src\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr

class ipv4_dst(oxm_tlv):
    """
    Wrapper class for ipv4_dst match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        if not hasmask:
            oxm_tlv.__init__(self, OFPXMT_OFB_IPV4_DST, hasmask, 4, value)
        else:
            oxm_tlv.__init__(self, OFPXMT_OFB_IPV4_DST, hasmask, 4, value, mask)
    def show(self, prefix=''):
        outstr = prefix + "ipv4_dst\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr
        
class tcp_src(oxm_tlv):
    """
    Wrapper class for tcp_src match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_TCP_SRC, hasmask, 2, value)
    def show(self, prefix=''):
        outstr = prefix + "tcp_src\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr

class tcp_dst(oxm_tlv):
    """
    Wrapper class for tcp_src match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_TCP_DST, hasmask, 2, value)
    def show(self, prefix=''):
        outstr = prefix + "tcp_dst\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr      

class udp_src(oxm_tlv):
    """
    Wrapper class for udp_src match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_UDP_SRC, hasmask, 2, value)
    def show(self, prefix=''):
        outstr = prefix + "udp_src\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr   
        
class udp_dst(oxm_tlv):
    """
    Wrapper class for udp_dst match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_UDP_DST, hasmask, 2, value)
    def show(self, prefix=''):
        outstr = prefix + "udp_dst\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr 
        
class sctp_src(oxm_tlv):
    """
    Wrapper class for sctp_src match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_SCTP_SRC, hasmask, 2, value)
    def show(self, prefix=''):
        outstr = prefix + "sctp_src\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr  


class sctp_dst(oxm_tlv):
    """
    Wrapper class for sctp_dst match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_SCTP_DST, hasmask, 2, value)
    def show(self, prefix=''):
        outstr = prefix + "sctp_dst\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr         
  
class icmpv4_type(oxm_tlv):
    """
    Wrapper class for icmpv4_type match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_ICMPV4_TYPE, hasmask, 1, value)
    def show(self, prefix=''):
        outstr = prefix + "icmpv4_type\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr          

class icmpv4_code(oxm_tlv):
    """
    Wrapper class for icmpv4_code match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_ICMPV4_CODE, hasmask, 1, value)
    def show(self, prefix=''):
        outstr = prefix + "icmpv4_code\n"
        outstr += oxm_tlv.show(self, prefix)
        return outs
        
class arp_op(oxm_tlv):
    """
    Wrapper class for arp_op match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_ARP_OP, hasmask, 2, value)
    def show(self, prefix=''):
        outstr = prefix + "arp_op\n"
        outstr += oxm_tlv.show(self, prefix)
        return outs

class arp_spa(oxm_tlv):
    """
    Wrapper class for arp_spa match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        if not hasmask:
            oxm_tlv.__init__(self, OFPXMT_OFB_ARP_SPA, hasmask, 4, value)
        else: 
            oxm_tlv.__init__(self, OFPXMT_OFB_ARP_SPA, hasmask, 4, value, mask)
    def show(self, prefix=''):
        outstr = prefix + "arp_spa\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr
        
class arp_tpa(oxm_tlv):
    """
    Wrapper class for arp_tpa match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        if not hasmask:
            oxm_tlv.__init__(self, OFPXMT_OFB_ARP_TPA, hasmask, 4, value)
        else: 
            oxm_tlv.__init__(self, OFPXMT_OFB_ARP_TPA, hasmask, 4, value, mask)
    def show(self, prefix=''):
        outstr = prefix + "arp_tpa\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr


class arp_sha(oxm_tlv):
    """
    Wrapper class for arp_sha match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        if not hasmask:
            oxm_tlv.__init__(self, OFPXMT_OFB_ARP_SHA, hasmask, 6, value)
        else:
            oxm_tlv.__init__(self, OFPXMT_OFB_ARP_SHA, hasmask, 12, value)            
    def show(self, prefix=''):
        outstr = prefix + "arp_sha\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr
 
class arp_tha(oxm_tlv):
    """
    Wrapper class for arp_tha match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        if not hasmask:
            oxm_tlv.__init__(self, OFPXMT_OFB_ARP_THA, hasmask, 6, value)
        else:
            oxm_tlv.__init__(self, OFPXMT_OFB_ARP_THA, hasmask, 12, value)            
    def show(self, prefix=''):
        outstr = prefix + "arp_tha\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr
        
class ipv6_src(oxm_tlv):
    """
    Wrapper class for ipv6_src match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        if not hasmask:
            oxm_tlv.__init__(self, OFPXMT_OFB_IPV6_SRC, False, 16, value)
        else:
            oxm_tlv.__init__(self, OFPXMT_OFB_IPV6_SRC, True, 32, value)            
    def show(self, prefix=''):
        outstr = prefix + "ipv6_src\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr
        
class ipv6_dst(oxm_tlv):
    """
    Wrapper class for ipv6_dst match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        if not hasmask:
            oxm_tlv.__init__(self, OFPXMT_OFB_IPV6_DST, False, 16, value)
        else:
            oxm_tlv.__init__(self, OFPXMT_OFB_IPV6_DST, True, 32, value)            
    def show(self, prefix=''):
        outstr = prefix + "ipv6_dst\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr
 
class ipv6_flabel(oxm_tlv):
    """
    Wrapper class for ipv6_flabel match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        if not hasmask:
            oxm_tlv.__init__(self, OFPXMT_OFB_IPV6_FLABEL, hasmask, 4, value)
        else:
            oxm_tlv.__init__(self, OFPXMT_OFB_IPV6_FLABEL, hasmask, 8, value)            
    def show(self, prefix=''):
        outstr = prefix + "ipv6_flabel\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr

class icmpv6_type(oxm_tlv):
    """
    Wrapper class for icmpv6_type match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_ICMPV6_TYPE, hasmask, 1, value)
    def show(self, prefix=''):
        outstr = prefix + "icmpv6_type\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr          

class icmpv6_code(oxm_tlv):
    """
    Wrapper class for icmpv6_code match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_ICMPV6_CODE, hasmask, 1, value)
    def show(self, prefix=''):
        outstr = prefix + "icmpv6_code\n"
        outstr += oxm_tlv.show(self, prefix)
        return outs

class ipv6_nd_target(oxm_tlv):
    """
    Wrapper class for ipv6_nd_target match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_IPV6_ND_TARGET, hasmask, 16, value)
    def show(self, prefix=''):
        outstr = prefix + "ipv6_nd_target\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr
        
class ipv6_nd_sll(oxm_tlv):
    """
    Wrapper class for ipv6_nd_sll match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_IPV6_ND_SLL, hasmask, 6, value)
    def show(self, prefix=''):
        outstr = prefix + "ipv6_nd_sll\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr

class ipv6_nd_tll(oxm_tlv):
    """
    Wrapper class for ipv6_nd_tll match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_IPV6_ND_TLL, hasmask, 6, value)          
    def show(self, prefix=''):
        outstr = prefix + "ipv6_nd_tll\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr

class mpls_label(oxm_tlv):
    """
    Wrapper class for mpls_label match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_MPLS_LABEL, hasmask, 4, value)
    def show(self, prefix=''):
        outstr = prefix + "mpls_label\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr
        
class mpls_tc(oxm_tlv):
    """
    Wrapper class for mpls_ltc match object

    Data members inherited from oxm_tlv:
    @arg class
    @arg field
    @arg hasmask
    @arg body

    """
    def __init__(self, value, hasmask = False):
        oxm_tlv.__init__(self, OFPXMT_OFB_MPLS_TC, hasmask, 1, value)
    def show(self, prefix=''):
        outstr = prefix + "mpls_tc\n"
        outstr += oxm_tlv.show(self, prefix)
        return outstr

match_class_list = (
    in_port,
    in_phy_port,
    metadata,
    eth_dst,
    eth_src,
    eth_type,
    vlan_vid,
    vlan_pcp,
    ip_dscp,
    ip_ecn,
    ip_proto,
    ipv4_src,
    ipv4_dst,
    tcp_src,
    tcp_dst,
    udp_src,
    udp_dst,
    sctp_src,
    sctp_dst,
    icmpv4_type,
    icmpv4_code,
    arp_op,
    arp_spa,
    arp_tpa,
    arp_sha,
    arp_tha,
    ipv6_src,
    ipv6_dst,
    ipv6_flabel,
    icmpv6_type,
    icmpv6_code,
    ipv6_nd_target,
    ipv6_nd_sll,
    ipv6_nd_tll,
    mpls_label,
    mpls_tc)
