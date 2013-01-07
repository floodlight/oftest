
# Python OpenFlow action wrapper classes

from cstruct import *



class action_set_nw_src(ofp_action_nw_addr):
    """
    Wrapper class for set_nw_src action object

    Data members inherited from ofp_action_nw_addr:
    @arg type
    @arg len
    @arg nw_addr

    """
    def __init__(self):
        ofp_action_nw_addr.__init__(self)
        self.type = OFPAT_SET_NW_SRC
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_nw_src\n"
        outstr += ofp_action_nw_addr.show(self, prefix)
        return outstr


class action_set_mpls_tc(ofp_action_mpls_tc):
    """
    Wrapper class for set_mpls_tc action object

    Data members inherited from ofp_action_mpls_tc:
    @arg type
    @arg len
    @arg mpls_tc

    """
    def __init__(self):
        ofp_action_mpls_tc.__init__(self)
        self.type = OFPAT_SET_MPLS_TC
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_mpls_tc\n"
        outstr += ofp_action_mpls_tc.show(self, prefix)
        return outstr


class action_set_nw_tos(ofp_action_nw_tos):
    """
    Wrapper class for set_nw_tos action object

    Data members inherited from ofp_action_nw_tos:
    @arg type
    @arg len
    @arg nw_tos

    """
    def __init__(self):
        ofp_action_nw_tos.__init__(self)
        self.type = OFPAT_SET_NW_TOS
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_nw_tos\n"
        outstr += ofp_action_nw_tos.show(self, prefix)
        return outstr


class action_dec_mpls_ttl(ofp_action_header):
    """
    Wrapper class for dec_mpls_ttl action object

    Data members inherited from ofp_action_header:
    @arg type
    @arg len

    """
    def __init__(self):
        ofp_action_header.__init__(self)
        self.type = OFPAT_DEC_MPLS_TTL
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_dec_mpls_ttl\n"
        outstr += ofp_action_header.show(self, prefix)
        return outstr


class action_set_nw_dst(ofp_action_nw_addr):
    """
    Wrapper class for set_nw_dst action object

    Data members inherited from ofp_action_nw_addr:
    @arg type
    @arg len
    @arg nw_addr

    """
    def __init__(self):
        ofp_action_nw_addr.__init__(self)
        self.type = OFPAT_SET_NW_DST
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_nw_dst\n"
        outstr += ofp_action_nw_addr.show(self, prefix)
        return outstr


class action_set_mpls_label(ofp_action_mpls_label):
    """
    Wrapper class for set_mpls_label action object

    Data members inherited from ofp_action_mpls_label:
    @arg type
    @arg len
    @arg mpls_label

    """
    def __init__(self):
        ofp_action_mpls_label.__init__(self)
        self.type = OFPAT_SET_MPLS_LABEL
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_mpls_label\n"
        outstr += ofp_action_mpls_label.show(self, prefix)
        return outstr


class action_group(ofp_action_group):
    """
    Wrapper class for group action object

    Data members inherited from ofp_action_group:
    @arg type
    @arg len
    @arg group_id

    """
    def __init__(self):
        ofp_action_group.__init__(self)
        self.type = OFPAT_GROUP
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_group\n"
        outstr += ofp_action_group.show(self, prefix)
        return outstr


class action_copy_ttl_out(ofp_action_header):
    """
    Wrapper class for copy_ttl_out action object

    Data members inherited from ofp_action_header:
    @arg type
    @arg len

    """
    def __init__(self):
        ofp_action_header.__init__(self)
        self.type = OFPAT_COPY_TTL_OUT
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_copy_ttl_out\n"
        outstr += ofp_action_header.show(self, prefix)
        return outstr


class action_set_vlan_vid(ofp_action_vlan_vid):
    """
    Wrapper class for set_vlan_vid action object

    Data members inherited from ofp_action_vlan_vid:
    @arg type
    @arg len
    @arg vlan_vid

    """
    def __init__(self):
        ofp_action_vlan_vid.__init__(self)
        self.type = OFPAT_SET_VLAN_VID
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_vlan_vid\n"
        outstr += ofp_action_vlan_vid.show(self, prefix)
        return outstr


class action_set_mpls_ttl(ofp_action_mpls_ttl):
    """
    Wrapper class for set_mpls_ttl action object

    Data members inherited from ofp_action_mpls_ttl:
    @arg type
    @arg len
    @arg mpls_ttl

    """
    def __init__(self):
        ofp_action_mpls_ttl.__init__(self)
        self.type = OFPAT_SET_MPLS_TTL
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_mpls_ttl\n"
        outstr += ofp_action_mpls_ttl.show(self, prefix)
        return outstr


class action_pop_vlan(ofp_action_header):
    """
    Wrapper class for pop_vlan action object

    Data members inherited from ofp_action_header:
    @arg type
    @arg len

    """
    def __init__(self):
        ofp_action_header.__init__(self)
        self.type = OFPAT_POP_VLAN
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_pop_vlan\n"
        outstr += ofp_action_header.show(self, prefix)
        return outstr


class action_set_tp_dst(ofp_action_tp_port):
    """
    Wrapper class for set_tp_dst action object

    Data members inherited from ofp_action_tp_port:
    @arg type
    @arg len
    @arg tp_port

    """
    def __init__(self):
        ofp_action_tp_port.__init__(self)
        self.type = OFPAT_SET_TP_DST
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_tp_dst\n"
        outstr += ofp_action_tp_port.show(self, prefix)
        return outstr


class action_pop_mpls(ofp_action_pop_mpls):
    """
    Wrapper class for pop_mpls action object

    Data members inherited from ofp_action_pop_mpls:
    @arg type
    @arg len
    @arg ethertype

    """
    def __init__(self):
        ofp_action_pop_mpls.__init__(self)
        self.type = OFPAT_POP_MPLS
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_pop_mpls\n"
        outstr += ofp_action_pop_mpls.show(self, prefix)
        return outstr


class action_push_vlan(ofp_action_push):
    """
    Wrapper class for push_vlan action object

    Data members inherited from ofp_action_push:
    @arg type
    @arg len
    @arg ethertype

    """
    def __init__(self):
        ofp_action_push.__init__(self)
        self.type = OFPAT_PUSH_VLAN
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_push_vlan\n"
        outstr += ofp_action_push.show(self, prefix)
        return outstr


class action_set_vlan_pcp(ofp_action_vlan_pcp):
    """
    Wrapper class for set_vlan_pcp action object

    Data members inherited from ofp_action_vlan_pcp:
    @arg type
    @arg len
    @arg vlan_pcp

    """
    def __init__(self):
        ofp_action_vlan_pcp.__init__(self)
        self.type = OFPAT_SET_VLAN_PCP
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_vlan_pcp\n"
        outstr += ofp_action_vlan_pcp.show(self, prefix)
        return outstr


class action_set_tp_src(ofp_action_tp_port):
    """
    Wrapper class for set_tp_src action object

    Data members inherited from ofp_action_tp_port:
    @arg type
    @arg len
    @arg tp_port

    """
    def __init__(self):
        ofp_action_tp_port.__init__(self)
        self.type = OFPAT_SET_TP_SRC
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_tp_src\n"
        outstr += ofp_action_tp_port.show(self, prefix)
        return outstr


class action_experimenter(ofp_action_experimenter_header):
    """
    Wrapper class for experimenter action object

    Data members inherited from ofp_action_experimenter_header:
    @arg type
    @arg len
    @arg experimenter

    """
    def __init__(self):
        ofp_action_experimenter_header.__init__(self)
        self.type = OFPAT_EXPERIMENTER
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_experimenter\n"
        outstr += ofp_action_experimenter_header.show(self, prefix)
        return outstr


class action_set_nw_ttl(ofp_action_nw_ttl):
    """
    Wrapper class for set_nw_ttl action object

    Data members inherited from ofp_action_nw_ttl:
    @arg type
    @arg len
    @arg nw_ttl

    """
    def __init__(self):
        ofp_action_nw_ttl.__init__(self)
        self.type = OFPAT_SET_NW_TTL
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_nw_ttl\n"
        outstr += ofp_action_nw_ttl.show(self, prefix)
        return outstr


class action_copy_ttl_in(ofp_action_header):
    """
    Wrapper class for copy_ttl_in action object

    Data members inherited from ofp_action_header:
    @arg type
    @arg len

    """
    def __init__(self):
        ofp_action_header.__init__(self)
        self.type = OFPAT_COPY_TTL_IN
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_copy_ttl_in\n"
        outstr += ofp_action_header.show(self, prefix)
        return outstr


class action_set_nw_ecn(ofp_action_nw_ecn):
    """
    Wrapper class for set_nw_ecn action object

    Data members inherited from ofp_action_nw_ecn:
    @arg type
    @arg len
    @arg nw_ecn

    """
    def __init__(self):
        ofp_action_nw_ecn.__init__(self)
        self.type = OFPAT_SET_NW_ECN
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_nw_ecn\n"
        outstr += ofp_action_nw_ecn.show(self, prefix)
        return outstr


class action_set_dl_dst(ofp_action_dl_addr):
    """
    Wrapper class for set_dl_dst action object

    Data members inherited from ofp_action_dl_addr:
    @arg type
    @arg len
    @arg dl_addr

    """
    def __init__(self):
        ofp_action_dl_addr.__init__(self)
        self.type = OFPAT_SET_DL_DST
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_dl_dst\n"
        outstr += ofp_action_dl_addr.show(self, prefix)
        return outstr


class action_push_mpls(ofp_action_push):
    """
    Wrapper class for push_mpls action object

    Data members inherited from ofp_action_push:
    @arg type
    @arg len
    @arg ethertype

    """
    def __init__(self):
        ofp_action_push.__init__(self)
        self.type = OFPAT_PUSH_MPLS
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_push_mpls\n"
        outstr += ofp_action_push.show(self, prefix)
        return outstr


class action_dec_nw_ttl(ofp_action_header):
    """
    Wrapper class for dec_nw_ttl action object

    Data members inherited from ofp_action_header:
    @arg type
    @arg len

    """
    def __init__(self):
        ofp_action_header.__init__(self)
        self.type = OFPAT_DEC_NW_TTL
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_dec_nw_ttl\n"
        outstr += ofp_action_header.show(self, prefix)
        return outstr


class action_set_dl_src(ofp_action_dl_addr):
    """
    Wrapper class for set_dl_src action object

    Data members inherited from ofp_action_dl_addr:
    @arg type
    @arg len
    @arg dl_addr

    """
    def __init__(self):
        ofp_action_dl_addr.__init__(self)
        self.type = OFPAT_SET_DL_SRC
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_dl_src\n"
        outstr += ofp_action_dl_addr.show(self, prefix)
        return outstr


class action_set_queue(ofp_action_set_queue):
    """
    Wrapper class for set_queue action object

    Data members inherited from ofp_action_set_queue:
    @arg type
    @arg len
    @arg queue_id

    """
    def __init__(self):
        ofp_action_set_queue.__init__(self)
        self.type = OFPAT_SET_QUEUE
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_queue\n"
        outstr += ofp_action_set_queue.show(self, prefix)
        return outstr


class action_output(ofp_action_output):
    """
    Wrapper class for output action object

    Data members inherited from ofp_action_output:
    @arg type
    @arg len
    @arg port
    @arg max_len

    """
    def __init__(self):
        ofp_action_output.__init__(self)
        self.type = OFPAT_OUTPUT
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_output\n"
        outstr += ofp_action_output.show(self, prefix)
        return outstr

action_class_list = (
    action_copy_ttl_in,
    action_copy_ttl_out,
    action_dec_mpls_ttl,
    action_dec_nw_ttl,
    action_experimenter,
    action_group,
    action_output,
    action_pop_mpls,
    action_pop_vlan,
    action_push_mpls,
    action_push_vlan,
    action_set_dl_dst,
    action_set_dl_src,
    action_set_mpls_label,
    action_set_mpls_tc,
    action_set_mpls_ttl,
    action_set_nw_dst,
    action_set_nw_ecn,
    action_set_nw_src,
    action_set_nw_tos,
    action_set_nw_ttl,
    action_set_queue,
    action_set_tp_dst,
    action_set_tp_src,
    action_set_vlan_pcp,
    action_set_vlan_vid)

