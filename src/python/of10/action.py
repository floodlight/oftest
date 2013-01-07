
# Python OpenFlow action wrapper classes

from cstruct import *



class vendor(ofp_action_vendor_header):
    """
    Wrapper class for vendor action object

    Data members inherited from ofp_action_vendor_header:
    @arg type
    @arg len
    @arg vendor

    """
    def __init__(self, **kwargs):
        ofp_action_vendor_header.__init__(self)
        self.type = OFPAT_VENDOR
        self.len = self.__len__()
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))
    def show(self, prefix=''):
        outstr = prefix + "action_vendor\n"
        outstr += ofp_action_vendor_header.show(self, prefix)
        return outstr

action_vendor = vendor # for backwards compatibility


class set_tp_dst(ofp_action_tp_port):
    """
    Wrapper class for set_tp_dst action object

    Data members inherited from ofp_action_tp_port:
    @arg type
    @arg len
    @arg tp_port

    """
    def __init__(self, **kwargs):
        ofp_action_tp_port.__init__(self)
        self.type = OFPAT_SET_TP_DST
        self.len = self.__len__()
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))
    def show(self, prefix=''):
        outstr = prefix + "action_set_tp_dst\n"
        outstr += ofp_action_tp_port.show(self, prefix)
        return outstr

action_set_tp_dst = set_tp_dst # for backwards compatibility


class set_vlan_pcp(ofp_action_vlan_pcp):
    """
    Wrapper class for set_vlan_pcp action object

    Data members inherited from ofp_action_vlan_pcp:
    @arg type
    @arg len
    @arg vlan_pcp

    """
    def __init__(self, **kwargs):
        ofp_action_vlan_pcp.__init__(self)
        self.type = OFPAT_SET_VLAN_PCP
        self.len = self.__len__()
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))
    def show(self, prefix=''):
        outstr = prefix + "action_set_vlan_pcp\n"
        outstr += ofp_action_vlan_pcp.show(self, prefix)
        return outstr

action_set_vlan_pcp = set_vlan_pcp # for backwards compatibility


class enqueue(ofp_action_enqueue):
    """
    Wrapper class for enqueue action object

    Data members inherited from ofp_action_enqueue:
    @arg type
    @arg len
    @arg port
    @arg queue_id

    """
    def __init__(self, **kwargs):
        ofp_action_enqueue.__init__(self)
        self.type = OFPAT_ENQUEUE
        self.len = self.__len__()
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))
    def show(self, prefix=''):
        outstr = prefix + "action_enqueue\n"
        outstr += ofp_action_enqueue.show(self, prefix)
        return outstr

action_enqueue = enqueue # for backwards compatibility


class set_tp_src(ofp_action_tp_port):
    """
    Wrapper class for set_tp_src action object

    Data members inherited from ofp_action_tp_port:
    @arg type
    @arg len
    @arg tp_port

    """
    def __init__(self, **kwargs):
        ofp_action_tp_port.__init__(self)
        self.type = OFPAT_SET_TP_SRC
        self.len = self.__len__()
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))
    def show(self, prefix=''):
        outstr = prefix + "action_set_tp_src\n"
        outstr += ofp_action_tp_port.show(self, prefix)
        return outstr

action_set_tp_src = set_tp_src # for backwards compatibility


class set_nw_tos(ofp_action_nw_tos):
    """
    Wrapper class for set_nw_tos action object

    Data members inherited from ofp_action_nw_tos:
    @arg type
    @arg len
    @arg nw_tos

    """
    def __init__(self, **kwargs):
        ofp_action_nw_tos.__init__(self)
        self.type = OFPAT_SET_NW_TOS
        self.len = self.__len__()
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))
    def show(self, prefix=''):
        outstr = prefix + "action_set_nw_tos\n"
        outstr += ofp_action_nw_tos.show(self, prefix)
        return outstr

action_set_nw_tos = set_nw_tos # for backwards compatibility


class set_nw_dst(ofp_action_nw_addr):
    """
    Wrapper class for set_nw_dst action object

    Data members inherited from ofp_action_nw_addr:
    @arg type
    @arg len
    @arg nw_addr

    """
    def __init__(self, **kwargs):
        ofp_action_nw_addr.__init__(self)
        self.type = OFPAT_SET_NW_DST
        self.len = self.__len__()
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))
    def show(self, prefix=''):
        outstr = prefix + "action_set_nw_dst\n"
        outstr += ofp_action_nw_addr.show(self, prefix)
        return outstr

action_set_nw_dst = set_nw_dst # for backwards compatibility


class strip_vlan(ofp_action_header):
    """
    Wrapper class for strip_vlan action object

    Data members inherited from ofp_action_header:
    @arg type
    @arg len

    """
    def __init__(self, **kwargs):
        ofp_action_header.__init__(self)
        self.type = OFPAT_STRIP_VLAN
        self.len = self.__len__()
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))
    def show(self, prefix=''):
        outstr = prefix + "action_strip_vlan\n"
        outstr += ofp_action_header.show(self, prefix)
        return outstr

action_strip_vlan = strip_vlan # for backwards compatibility


class set_dl_dst(ofp_action_dl_addr):
    """
    Wrapper class for set_dl_dst action object

    Data members inherited from ofp_action_dl_addr:
    @arg type
    @arg len
    @arg dl_addr

    """
    def __init__(self, **kwargs):
        ofp_action_dl_addr.__init__(self)
        self.type = OFPAT_SET_DL_DST
        self.len = self.__len__()
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))
    def show(self, prefix=''):
        outstr = prefix + "action_set_dl_dst\n"
        outstr += ofp_action_dl_addr.show(self, prefix)
        return outstr

action_set_dl_dst = set_dl_dst # for backwards compatibility


class set_nw_src(ofp_action_nw_addr):
    """
    Wrapper class for set_nw_src action object

    Data members inherited from ofp_action_nw_addr:
    @arg type
    @arg len
    @arg nw_addr

    """
    def __init__(self, **kwargs):
        ofp_action_nw_addr.__init__(self)
        self.type = OFPAT_SET_NW_SRC
        self.len = self.__len__()
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))
    def show(self, prefix=''):
        outstr = prefix + "action_set_nw_src\n"
        outstr += ofp_action_nw_addr.show(self, prefix)
        return outstr

action_set_nw_src = set_nw_src # for backwards compatibility


class set_vlan_vid(ofp_action_vlan_vid):
    """
    Wrapper class for set_vlan_vid action object

    Data members inherited from ofp_action_vlan_vid:
    @arg type
    @arg len
    @arg vlan_vid

    """
    def __init__(self, **kwargs):
        ofp_action_vlan_vid.__init__(self)
        self.type = OFPAT_SET_VLAN_VID
        self.len = self.__len__()
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))
    def show(self, prefix=''):
        outstr = prefix + "action_set_vlan_vid\n"
        outstr += ofp_action_vlan_vid.show(self, prefix)
        return outstr

action_set_vlan_vid = set_vlan_vid # for backwards compatibility


class set_dl_src(ofp_action_dl_addr):
    """
    Wrapper class for set_dl_src action object

    Data members inherited from ofp_action_dl_addr:
    @arg type
    @arg len
    @arg dl_addr

    """
    def __init__(self, **kwargs):
        ofp_action_dl_addr.__init__(self)
        self.type = OFPAT_SET_DL_SRC
        self.len = self.__len__()
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))
    def show(self, prefix=''):
        outstr = prefix + "action_set_dl_src\n"
        outstr += ofp_action_dl_addr.show(self, prefix)
        return outstr

action_set_dl_src = set_dl_src # for backwards compatibility


class output(ofp_action_output):
    """
    Wrapper class for output action object

    Data members inherited from ofp_action_output:
    @arg type
    @arg len
    @arg port
    @arg max_len

    """
    def __init__(self, **kwargs):
        ofp_action_output.__init__(self)
        self.type = OFPAT_OUTPUT
        self.len = self.__len__()
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))
    def show(self, prefix=''):
        outstr = prefix + "action_output\n"
        outstr += ofp_action_output.show(self, prefix)
        return outstr

action_output = output # for backwards compatibility

action_class_list = (
    action_vendor,
    action_set_tp_dst,
    action_set_vlan_pcp,
    action_enqueue,
    action_set_tp_src,
    action_set_nw_tos,
    action_set_nw_dst,
    action_strip_vlan,
    action_set_dl_dst,
    action_set_nw_src,
    action_set_vlan_vid,
    action_set_dl_src,
    action_output)
