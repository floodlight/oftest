
# Python OpenFlow error wrapper classes

from cstruct import *



class hello_failed_error_msg(ofp_error_msg):
    """
    Wrapper class for hello_failed error message class

    Data members inherited from ofp_error_msg:
    @arg type
    @arg code
    @arg data: Binary string following message members
    
    """
    def __init__(self):
        ofp_error_msg.__init__(self)
        self.version = OFP_VERSION
        self.type = OFPT_ERROR
        self.xid = None
        self.err_type = OFPET_HELLO_FAILED
        self.data = ""

    def pack(self, assertstruct=True):
        self.header.length = self.__len__()
        packed = ""
        packed += ofp_error_msg.pack(self)
        packed += self.data
        return packed

    def unpack(self, binary_string):
        binary_string = ofp_error_msg.unpack(self, binary_string)
        self.data = binary_string
        return ""

    def __len__(self):
        return OFP_ERROR_MSG_BYTES + len(self.data)

    def show(self, prefix=''):
        outstr = prefix + "hello_failed_error_msg\m"
        outstr += ofp_error_msg.show(self, prefix + '  ')
        outstr += prefix + "data is of length " + str(len(self.data)) + '\n'
        ##@todo Consider trying to parse the string
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (ofp_error_msg.__eq__(self, other) and
                self.data == other.data)

    def __ne__(self, other): return not self.__eq__(other)


class bad_request_error_msg(ofp_error_msg):
    """
    Wrapper class for bad_request error message class

    Data members inherited from ofp_error_msg:
    @arg type
    @arg code
    @arg data: Binary string following message members
    
    """
    def __init__(self):
        ofp_error_msg.__init__(self)
        self.version = OFP_VERSION
        self.type = OFPT_ERROR
        self.xid = None
        self.err_type = OFPET_BAD_REQUEST
        self.data = ""

    def pack(self, assertstruct=True):
        self.header.length = self.__len__()
        packed = ""
        packed += ofp_error_msg.pack(self)
        packed += self.data
        return packed

    def unpack(self, binary_string):
        binary_string = ofp_error_msg.unpack(self, binary_string)
        self.data = binary_string
        return ""

    def __len__(self):
        return OFP_ERROR_MSG_BYTES + len(self.data)

    def show(self, prefix=''):
        outstr = prefix + "bad_request_error_msg\m"
        outstr += ofp_error_msg.show(self, prefix + '  ')
        outstr += prefix + "data is of length " + str(len(self.data)) + '\n'
        ##@todo Consider trying to parse the string
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (ofp_error_msg.__eq__(self, other) and
                self.data == other.data)

    def __ne__(self, other): return not self.__eq__(other)


class bad_action_error_msg(ofp_error_msg):
    """
    Wrapper class for bad_action error message class

    Data members inherited from ofp_error_msg:
    @arg type
    @arg code
    @arg data: Binary string following message members
    
    """
    def __init__(self):
        ofp_error_msg.__init__(self)
        self.version = OFP_VERSION
        self.type = OFPT_ERROR
        self.xid = None
        self.err_type = OFPET_BAD_ACTION
        self.data = ""

    def pack(self, assertstruct=True):
        self.header.length = self.__len__()
        packed = ""
        packed += ofp_error_msg.pack(self)
        packed += self.data
        return packed

    def unpack(self, binary_string):
        binary_string = ofp_error_msg.unpack(self, binary_string)
        self.data = binary_string
        return ""

    def __len__(self):
        return OFP_ERROR_MSG_BYTES + len(self.data)

    def show(self, prefix=''):
        outstr = prefix + "bad_action_error_msg\m"
        outstr += ofp_error_msg.show(self, prefix + '  ')
        outstr += prefix + "data is of length " + str(len(self.data)) + '\n'
        ##@todo Consider trying to parse the string
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (ofp_error_msg.__eq__(self, other) and
                self.data == other.data)

    def __ne__(self, other): return not self.__eq__(other)


class flow_mod_failed_error_msg(ofp_error_msg):
    """
    Wrapper class for flow_mod_failed error message class

    Data members inherited from ofp_error_msg:
    @arg type
    @arg code
    @arg data: Binary string following message members
    
    """
    def __init__(self):
        ofp_error_msg.__init__(self)
        self.version = OFP_VERSION
        self.type = OFPT_ERROR
        self.xid = None
        self.err_type = OFPET_FLOW_MOD_FAILED
        self.data = ""

    def pack(self, assertstruct=True):
        self.header.length = self.__len__()
        packed = ""
        packed += ofp_error_msg.pack(self)
        packed += self.data
        return packed

    def unpack(self, binary_string):
        binary_string = ofp_error_msg.unpack(self, binary_string)
        self.data = binary_string
        return ""

    def __len__(self):
        return OFP_ERROR_MSG_BYTES + len(self.data)

    def show(self, prefix=''):
        outstr = prefix + "flow_mod_failed_error_msg\m"
        outstr += ofp_error_msg.show(self, prefix + '  ')
        outstr += prefix + "data is of length " + str(len(self.data)) + '\n'
        ##@todo Consider trying to parse the string
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (ofp_error_msg.__eq__(self, other) and
                self.data == other.data)

    def __ne__(self, other): return not self.__eq__(other)


class port_mod_failed_error_msg(ofp_error_msg):
    """
    Wrapper class for port_mod_failed error message class

    Data members inherited from ofp_error_msg:
    @arg type
    @arg code
    @arg data: Binary string following message members
    
    """
    def __init__(self):
        ofp_error_msg.__init__(self)
        self.version = OFP_VERSION
        self.type = OFPT_ERROR
        self.xid = None
        self.err_type = OFPET_PORT_MOD_FAILED
        self.data = ""

    def pack(self, assertstruct=True):
        self.header.length = self.__len__()
        packed = ""
        packed += ofp_error_msg.pack(self)
        packed += self.data
        return packed

    def unpack(self, binary_string):
        binary_string = ofp_error_msg.unpack(self, binary_string)
        self.data = binary_string
        return ""

    def __len__(self):
        return OFP_ERROR_MSG_BYTES + len(self.data)

    def show(self, prefix=''):
        outstr = prefix + "port_mod_failed_error_msg\m"
        outstr += ofp_error_msg.show(self, prefix + '  ')
        outstr += prefix + "data is of length " + str(len(self.data)) + '\n'
        ##@todo Consider trying to parse the string
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (ofp_error_msg.__eq__(self, other) and
                self.data == other.data)

    def __ne__(self, other): return not self.__eq__(other)


class queue_op_failed_error_msg(ofp_error_msg):
    """
    Wrapper class for queue_op_failed error message class

    Data members inherited from ofp_error_msg:
    @arg type
    @arg code
    @arg data: Binary string following message members
    
    """
    def __init__(self):
        ofp_error_msg.__init__(self)
        self.version = OFP_VERSION
        self.type = OFPT_ERROR
        self.xid = None
        self.err_type = OFPET_QUEUE_OP_FAILED
        self.data = ""

    def pack(self, assertstruct=True):
        self.header.length = self.__len__()
        packed = ""
        packed += ofp_error_msg.pack(self)
        packed += self.data
        return packed

    def unpack(self, binary_string):
        binary_string = ofp_error_msg.unpack(self, binary_string)
        self.data = binary_string
        return ""

    def __len__(self):
        return OFP_ERROR_MSG_BYTES + len(self.data)

    def show(self, prefix=''):
        outstr = prefix + "queue_op_failed_error_msg\m"
        outstr += ofp_error_msg.show(self, prefix + '  ')
        outstr += prefix + "data is of length " + str(len(self.data)) + '\n'
        ##@todo Consider trying to parse the string
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (ofp_error_msg.__eq__(self, other) and
                self.data == other.data)

    def __ne__(self, other): return not self.__eq__(other)

