
# Python OpenFlow action wrapper classes

from cstruct import *
from match import roundup
from match_list import match_list

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
    def __len__(self):
        return roundup(4 + 4,8)


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


class action_set_field(ofp_action_set_field):
    """
    Wrapper class for set_field action object

    Data members inherited from ofp_action_set_field:
    @arg type
    @arg len
    @arg field

    """
    def __init__(self):
        ofp_action_set_field.__init__(self)
        self.type = OFPAT_SET_FIELD
        self.len = self.__len__()
        self.field = match_list()
        
    def pack(self):
        packed = ""
        if len(self.field) <= 4:
            packed += ofp_action_set_field.pack()
        else:
            self.len = len(self)
            packed += struct.pack("!HH", self.type, self.len)
            packed += self.field.pack()
            padding_size = roundup(len(self.field) -4,8) -  (len(self.field) -4)
            if padding_size:
                padding = [0] * padding_size
                packed += struct.pack("!" + str(padding_size) + "B", *padding)
        return packed
    
    def unpack(self, binary_string):
        if len(binary_string) <= 8:
            binary_string = ofp_action_set_field.unpack(self)
        else: 
            (self.type, self.len) = struct.unpack("!HH",  binary_string[0:4])
            binary_string = binary_string[4:]
            binary_string = self.field.unpack(binary_string, bytes = self.len - 4)
            padding_size = roundup(len(self.field) -4,8) -  (len(self.field) -4) 
            if padding_size:
                binary_string = binary_string[padding_size:]
        return binary_string
        
    def show(self, prefix=''):
        outstr = prefix + "action_set_field\n"
        outstr += ofp_action_set_field.show(self, prefix)
        return outstr
    
    def __len__(self):
        return roundup(4 + len(self.field),8)
         

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
    action_set_field,
    action_set_mpls_ttl,
    action_set_nw_ttl,
    action_set_queue)

