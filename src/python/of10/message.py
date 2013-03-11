
# Python OpenFlow message wrapper classes

from cstruct import *
from action_list import action_list
from error import *

# Define templates for documentation
class ofp_template_msg:
    """
    Sample base class for template_msg; normally auto generated
    This class should live in the of_header name space and provides the
    base class for this type of message.  It will be wrapped for the
    high level API.

    """
    def __init__(self):
        """
        Constructor for base class

        """
        self.header = ofp_header()
        # Additional base data members declared here

    # Normally will define pack, unpack, __len__ functions

class template_msg(ofp_template_msg):
    """
    Sample class wrapper for template_msg
    This class should live in the of_message name space and provides the
    high level API for an OpenFlow message object.  These objects must
    implement the functions indicated in this template.

    """
    def __init__(self):
        """
        Constructor
        Must set the header type value appropriately for the message

        """

        ##@var header
        # OpenFlow message header: length, version, xid, type
        ofp_template_msg.__init__(self)
        self.header = ofp_header()
        # For a real message, will be set to an integer
        self.header.type = "TEMPLATE_MSG_VALUE"
    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        pass
    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.

        @return Typically returns the remainder of binary_string that
        was not parsed.  May give a warning if that string is non-empty

        """
        pass
    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        pass
    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """
        pass
    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        pass
    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        pass


################################################################
#
# OpenFlow Message Definitions
#
################################################################

class barrier_reply:
    """
    Wrapper class for barrier_reply

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_BARRIER_REPLY=19)


    """

    def __init__(self, **kwargs):
        self.header = ofp_header()
        self.header.type = OFPT_BARRIER_REPLY
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        # Fixme: If no self.data, add check for data remaining
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'barrier_reply (OFPT_BARRIER_REPLY)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    

class barrier_request:
    """
    Wrapper class for barrier_request

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_BARRIER_REQUEST=18)


    """

    def __init__(self, **kwargs):
        self.header = ofp_header()
        self.header.type = OFPT_BARRIER_REQUEST
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        # Fixme: If no self.data, add check for data remaining
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'barrier_request (OFPT_BARRIER_REQUEST)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    

class echo_reply:
    """
    Wrapper class for echo_reply

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_ECHO_REPLY=3)

    @arg data: Binary string following message members

    """

    def __init__(self, **kwargs):
        self.header = ofp_header()
        self.header.type = OFPT_ECHO_REPLY
        self.data = ""
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        packed += self.data
        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        self.data = binary_string
        binary_string = ''
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        length += len(self.data)
        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'echo_reply (OFPT_ECHO_REPLY)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        outstr += prefix + 'data is of length ' + str(len(self.data)) + '\n'
        ##@todo Fix this circular reference
        # if len(self.data) > 0:
            # obj = of_message_parse(self.data)
            # if obj != None:
                # outstr += obj.show(prefix)
            # else:
                # outstr += prefix + "Unable to parse data\n"
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        if self.data != other.data: return False
        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    

class echo_request:
    """
    Wrapper class for echo_request

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_ECHO_REQUEST=2)

    @arg data: Binary string following message members

    """

    def __init__(self, **kwargs):
        self.header = ofp_header()
        self.header.type = OFPT_ECHO_REQUEST
        self.data = ""
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        packed += self.data
        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        self.data = binary_string
        binary_string = ''
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        length += len(self.data)
        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'echo_request (OFPT_ECHO_REQUEST)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        outstr += prefix + 'data is of length ' + str(len(self.data)) + '\n'
        ##@todo Fix this circular reference
        # if len(self.data) > 0:
            # obj = of_message_parse(self.data)
            # if obj != None:
                # outstr += obj.show(prefix)
            # else:
                # outstr += prefix + "Unable to parse data\n"
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        if self.data != other.data: return False
        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    

class error(ofp_error_msg):
    """
    Wrapper class for error

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_ERROR=1)

    Data members inherited from ofp_error_msg:
    @arg type
    @arg code
    @arg data: Binary string following message members

    """

    def __init__(self, **kwargs):
        ofp_error_msg.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_ERROR
        self.data = ""
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        packed += ofp_error_msg.pack(self)
        packed += self.data
        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        binary_string = ofp_error_msg.unpack(self, binary_string)
        self.data = binary_string
        binary_string = ''
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        length += ofp_error_msg.__len__(self)
        length += len(self.data)
        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'error (OFPT_ERROR)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_error_msg.show(self, prefix)
        outstr += prefix + 'data is of length ' + str(len(self.data)) + '\n'
        ##@todo Fix this circular reference
        # if len(self.data) > 0:
            # obj = of_message_parse(self.data)
            # if obj != None:
                # outstr += obj.show(prefix)
            # else:
                # outstr += prefix + "Unable to parse data\n"
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        if not ofp_error_msg.__eq__(self, other): return False
        if self.data != other.data: return False
        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    

class features_reply(ofp_switch_features):
    """
    Wrapper class for features_reply

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_FEATURES_REPLY=6)

    Data members inherited from ofp_switch_features:
    @arg datapath_id
    @arg n_buffers
    @arg n_tables
    @arg capabilities
    @arg actions
    @arg ports: Variable length array of TBD

    """

    def __init__(self, **kwargs):
        ofp_switch_features.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_FEATURES_REPLY
        self.ports = []
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        packed += ofp_switch_features.pack(self)
        for obj in self.ports:
            packed += obj.pack()
        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        binary_string = ofp_switch_features.unpack(self, binary_string)
        while len(binary_string) >= OFP_PHY_PORT_BYTES:
            new_port = ofp_phy_port()
            binary_string = new_port.unpack(binary_string)
            self.ports.append(new_port)
        # Fixme: If no self.data, add check for data remaining
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        length += ofp_switch_features.__len__(self)
        for obj in self.ports:
            length += len(obj)
        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'features_reply (OFPT_FEATURES_REPLY)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_switch_features.show(self, prefix)
        outstr += prefix + "Array ports\n"
        for obj in self.ports:
            outstr += obj.show(prefix + '  ')
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        if not ofp_switch_features.__eq__(self, other): return False
        if self.ports != other.ports: return False
        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    

class features_request:
    """
    Wrapper class for features_request

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_FEATURES_REQUEST=5)


    """

    def __init__(self, **kwargs):
        self.header = ofp_header()
        self.header.type = OFPT_FEATURES_REQUEST
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        # Fixme: If no self.data, add check for data remaining
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'features_request (OFPT_FEATURES_REQUEST)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    

class flow_mod(ofp_flow_mod):
    """
    Wrapper class for flow_mod

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_FLOW_MOD=14)

    Data members inherited from ofp_flow_mod:
    @arg match
    @arg cookie
    @arg command
    @arg idle_timeout
    @arg hard_timeout
    @arg priority
    @arg buffer_id
    @arg out_port
    @arg flags
    @arg actions: Object of type action_list

    """

    def __init__(self, **kwargs):
        ofp_flow_mod.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_FLOW_MOD
        self.actions = []
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        packed += ofp_flow_mod.pack(self)
        packed += action_list(self.actions).pack()
        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        binary_string = ofp_flow_mod.unpack(self, binary_string)
        ai_len = self.header.length - (OFP_FLOW_MOD_BYTES + OFP_HEADER_BYTES)
        obj = action_list()
        binary_string = obj.unpack(binary_string, bytes=ai_len)
        self.actions = list(obj)
        # Fixme: If no self.data, add check for data remaining
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        length += ofp_flow_mod.__len__(self)
        for obj in self.actions:
            length += len(obj)
        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'flow_mod (OFPT_FLOW_MOD)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_flow_mod.show(self, prefix)
        outstr += prefix + "List actions\n"
        for obj in self.actions:
            outstr += obj.show(prefix + "  ")
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        if not ofp_flow_mod.__eq__(self, other): return False
        if self.actions != other.actions: return False
        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    

class flow_removed(ofp_flow_removed):
    """
    Wrapper class for flow_removed

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_FLOW_REMOVED=11)

    Data members inherited from ofp_flow_removed:
    @arg match
    @arg cookie
    @arg priority
    @arg reason
    @arg duration_sec
    @arg duration_nsec
    @arg idle_timeout
    @arg packet_count
    @arg byte_count

    """

    def __init__(self, **kwargs):
        ofp_flow_removed.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_FLOW_REMOVED
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        packed += ofp_flow_removed.pack(self)
        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        binary_string = ofp_flow_removed.unpack(self, binary_string)
        # Fixme: If no self.data, add check for data remaining
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        length += ofp_flow_removed.__len__(self)
        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'flow_removed (OFPT_FLOW_REMOVED)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_flow_removed.show(self, prefix)
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        if not ofp_flow_removed.__eq__(self, other): return False
        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    

class get_config_reply(ofp_switch_config):
    """
    Wrapper class for get_config_reply

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_GET_CONFIG_REPLY=8)

    Data members inherited from ofp_switch_config:
    @arg flags
    @arg miss_send_len

    """

    def __init__(self, **kwargs):
        ofp_switch_config.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_GET_CONFIG_REPLY
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        packed += ofp_switch_config.pack(self)
        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        binary_string = ofp_switch_config.unpack(self, binary_string)
        # Fixme: If no self.data, add check for data remaining
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        length += ofp_switch_config.__len__(self)
        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'get_config_reply (OFPT_GET_CONFIG_REPLY)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_switch_config.show(self, prefix)
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        if not ofp_switch_config.__eq__(self, other): return False
        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    

class get_config_request:
    """
    Wrapper class for get_config_request

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_GET_CONFIG_REQUEST=7)


    """

    def __init__(self, **kwargs):
        self.header = ofp_header()
        self.header.type = OFPT_GET_CONFIG_REQUEST
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        # Fixme: If no self.data, add check for data remaining
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'get_config_request (OFPT_GET_CONFIG_REQUEST)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    

class hello:
    """
    Wrapper class for hello

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_HELLO=0)

    @arg data: Binary string following message members

    """

    def __init__(self, **kwargs):
        self.header = ofp_header()
        self.header.type = OFPT_HELLO
        self.data = ""
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        packed += self.data
        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        self.data = binary_string
        binary_string = ''
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        length += len(self.data)
        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'hello (OFPT_HELLO)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        outstr += prefix + 'data is of length ' + str(len(self.data)) + '\n'
        ##@todo Fix this circular reference
        # if len(self.data) > 0:
            # obj = of_message_parse(self.data)
            # if obj != None:
                # outstr += obj.show(prefix)
            # else:
                # outstr += prefix + "Unable to parse data\n"
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        if self.data != other.data: return False
        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    

class packet_in(ofp_packet_in):
    """
    Wrapper class for packet_in

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_PACKET_IN=10)

    Data members inherited from ofp_packet_in:
    @arg buffer_id
    @arg total_len
    @arg in_port
    @arg reason
    @arg data: Binary string following message members

    """

    def __init__(self, **kwargs):
        ofp_packet_in.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_PACKET_IN
        self.data = ""
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        packed += ofp_packet_in.pack(self)
        packed += self.data
        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        binary_string = ofp_packet_in.unpack(self, binary_string)
        self.data = binary_string
        binary_string = ''
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        length += ofp_packet_in.__len__(self)
        length += len(self.data)
        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'packet_in (OFPT_PACKET_IN)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_packet_in.show(self, prefix)
        outstr += prefix + 'data is of length ' + str(len(self.data)) + '\n'
        ##@todo Fix this circular reference
        # if len(self.data) > 0:
            # obj = of_message_parse(self.data)
            # if obj != None:
                # outstr += obj.show(prefix)
            # else:
                # outstr += prefix + "Unable to parse data\n"
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        if not ofp_packet_in.__eq__(self, other): return False
        if self.data != other.data: return False
        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    

class packet_out(ofp_packet_out):
    """
    Wrapper class for packet_out

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_PACKET_OUT=13)

    Data members inherited from ofp_packet_out:
    @arg buffer_id
    @arg in_port
    @arg actions_len
    @arg actions: Object of type action_list
    @arg data: Binary string following message members

    """

    def __init__(self, **kwargs):
        ofp_packet_out.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_PACKET_OUT
        self.actions = []
        self.data = ""
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        self.actions_len = 0
        for obj in self.actions:
            self.actions_len += len(obj)
        packed += ofp_packet_out.pack(self)
        packed += action_list(self.actions).pack()
        packed += self.data
        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        binary_string = ofp_packet_out.unpack(self, binary_string)
        obj = action_list()
        binary_string = obj.unpack(binary_string, bytes=self.actions_len)
        self.actions = list(obj)
        self.data = binary_string
        binary_string = ''
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        length += ofp_packet_out.__len__(self)
        for obj in self.actions:
            length += len(obj)
        length += len(self.data)
        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'packet_out (OFPT_PACKET_OUT)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_packet_out.show(self, prefix)
        outstr += prefix + "List actions\n"
        for obj in self.actions:
            outstr += obj.show(prefix + "  ")
        outstr += prefix + 'data is of length ' + str(len(self.data)) + '\n'
        ##@todo Fix this circular reference
        # if len(self.data) > 0:
            # obj = of_message_parse(self.data)
            # if obj != None:
                # outstr += obj.show(prefix)
            # else:
                # outstr += prefix + "Unable to parse data\n"
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        if not ofp_packet_out.__eq__(self, other): return False
        if self.data != other.data: return False
        if self.actions != other.actions: return False
        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    

class port_mod(ofp_port_mod):
    """
    Wrapper class for port_mod

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_PORT_MOD=15)

    Data members inherited from ofp_port_mod:
    @arg port_no
    @arg hw_addr
    @arg config
    @arg mask
    @arg advertise

    """

    def __init__(self, **kwargs):
        ofp_port_mod.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_PORT_MOD
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        packed += ofp_port_mod.pack(self)
        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        binary_string = ofp_port_mod.unpack(self, binary_string)
        # Fixme: If no self.data, add check for data remaining
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        length += ofp_port_mod.__len__(self)
        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'port_mod (OFPT_PORT_MOD)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_port_mod.show(self, prefix)
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        if not ofp_port_mod.__eq__(self, other): return False
        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    

class port_status(ofp_port_status):
    """
    Wrapper class for port_status

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_PORT_STATUS=12)

    Data members inherited from ofp_port_status:
    @arg reason
    @arg desc

    """

    def __init__(self, **kwargs):
        ofp_port_status.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_PORT_STATUS
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        packed += ofp_port_status.pack(self)
        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        binary_string = ofp_port_status.unpack(self, binary_string)
        # Fixme: If no self.data, add check for data remaining
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        length += ofp_port_status.__len__(self)
        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'port_status (OFPT_PORT_STATUS)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_port_status.show(self, prefix)
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        if not ofp_port_status.__eq__(self, other): return False
        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    

class queue_get_config_reply(ofp_queue_get_config_reply):
    """
    Wrapper class for queue_get_config_reply

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_QUEUE_GET_CONFIG_REPLY=21)

    Data members inherited from ofp_queue_get_config_reply:
    @arg port
    @arg queues: Variable length array of TBD

    """

    def __init__(self, **kwargs):
        ofp_queue_get_config_reply.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_QUEUE_GET_CONFIG_REPLY
        self.queues = []
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        packed += ofp_queue_get_config_reply.pack(self)
        for obj in self.queues:
            packed += obj.pack()
        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        binary_string = ofp_queue_get_config_reply.unpack(self, binary_string)
        for obj in self.queues:
            binary_string = obj.unpack(binary_string)
        # Fixme: If no self.data, add check for data remaining
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        length += ofp_queue_get_config_reply.__len__(self)
        for obj in self.queues:
            length += len(obj)
        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'queue_get_config_reply (OFPT_QUEUE_GET_CONFIG_REPLY)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_queue_get_config_reply.show(self, prefix)
        outstr += prefix + "Array queues\n"
        for obj in self.queues:
            outstr += obj.show(prefix + '  ')
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        if not ofp_queue_get_config_reply.__eq__(self, other): return False
        if self.queues != other.queues: return False
        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    

class queue_get_config_request(ofp_queue_get_config_request):
    """
    Wrapper class for queue_get_config_request

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_QUEUE_GET_CONFIG_REQUEST=20)

    Data members inherited from ofp_queue_get_config_request:
    @arg port

    """

    def __init__(self, **kwargs):
        ofp_queue_get_config_request.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_QUEUE_GET_CONFIG_REQUEST
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        packed += ofp_queue_get_config_request.pack(self)
        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        binary_string = ofp_queue_get_config_request.unpack(self, binary_string)
        # Fixme: If no self.data, add check for data remaining
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        length += ofp_queue_get_config_request.__len__(self)
        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'queue_get_config_request (OFPT_QUEUE_GET_CONFIG_REQUEST)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_queue_get_config_request.show(self, prefix)
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        if not ofp_queue_get_config_request.__eq__(self, other): return False
        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    

class set_config(ofp_switch_config):
    """
    Wrapper class for set_config

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_SET_CONFIG=9)

    Data members inherited from ofp_switch_config:
    @arg flags
    @arg miss_send_len

    """

    def __init__(self, **kwargs):
        ofp_switch_config.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_SET_CONFIG
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        packed += ofp_switch_config.pack(self)
        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        binary_string = ofp_switch_config.unpack(self, binary_string)
        # Fixme: If no self.data, add check for data remaining
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        length += ofp_switch_config.__len__(self)
        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'set_config (OFPT_SET_CONFIG)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_switch_config.show(self, prefix)
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        if not ofp_switch_config.__eq__(self, other): return False
        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    

class stats_reply(ofp_stats_reply):
    """
    Wrapper class for stats_reply

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_STATS_REPLY=17)

    Data members inherited from ofp_stats_reply:
    @arg type
    @arg flags

    """

    def __init__(self, **kwargs):
        ofp_stats_reply.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_STATS_REPLY
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        packed += ofp_stats_reply.pack(self)
        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        binary_string = ofp_stats_reply.unpack(self, binary_string)
        # Fixme: If no self.data, add check for data remaining
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        length += ofp_stats_reply.__len__(self)
        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'stats_reply (OFPT_STATS_REPLY)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_stats_reply.show(self, prefix)
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        if not ofp_stats_reply.__eq__(self, other): return False
        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    

class stats_request(ofp_stats_request):
    """
    Wrapper class for stats_request

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_STATS_REQUEST=16)

    Data members inherited from ofp_stats_request:
    @arg type
    @arg flags

    """

    def __init__(self, **kwargs):
        ofp_stats_request.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_STATS_REQUEST
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        packed += ofp_stats_request.pack(self)
        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        binary_string = ofp_stats_request.unpack(self, binary_string)
        # Fixme: If no self.data, add check for data remaining
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        length += ofp_stats_request.__len__(self)
        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'stats_request (OFPT_STATS_REQUEST)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_stats_request.show(self, prefix)
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        if not ofp_stats_request.__eq__(self, other): return False
        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    

class vendor(ofp_vendor_header):
    """
    Wrapper class for vendor

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_VENDOR=4)

    Data members inherited from ofp_vendor_header:
    @arg vendor
    @arg data: Binary string following message members

    """

    def __init__(self, **kwargs):
        ofp_vendor_header.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_VENDOR
        self.data = ""
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))


    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack()

        packed += ofp_vendor_header.pack(self)
        packed += self.data
        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """
        binary_string = self.header.unpack(binary_string)

        binary_string = ofp_vendor_header.unpack(self, binary_string)
        self.data = binary_string
        binary_string = ''
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = OFP_HEADER_BYTES

        length += ofp_vendor_header.__len__(self)
        length += len(self.data)
        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'vendor (OFPT_VENDOR)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_vendor_header.show(self, prefix)
        outstr += prefix + 'data is of length ' + str(len(self.data)) + '\n'
        ##@todo Fix this circular reference
        # if len(self.data) > 0:
            # obj = of_message_parse(self.data)
            # if obj != None:
                # outstr += obj.show(prefix)
            # else:
                # outstr += prefix + "Unable to parse data\n"
        return outstr

    def __eq__(self, other):
        """
        Return True if self and other hold the same data

        @param other Other object in comparison

        """
        if type(self) != type(other): return False
        if not self.header.__eq__(other.header): return False

        if not ofp_vendor_header.__eq__(self, other): return False
        if self.data != other.data: return False
        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
    


################################################################
#
# Stats request and reply subclass definitions
#
################################################################


# Stats request bodies for desc and table stats are not defined in the
# OpenFlow header;  We define them here.  They are empty classes, really

class ofp_desc_stats_request:
    """
    Forced definition of ofp_desc_stats_request (empty class)
    """
    def __init__(self):
        pass
    def pack(self, assertstruct=True):
        return ""
    def unpack(self, binary_string):
        return binary_string
    def __len__(self):
        return 0
    def show(self, prefix=''):
        return prefix + "ofp_desc_stats_request (empty)\n"
    def __eq__(self, other):
        return type(self) == type(other)
    def __ne__(self, other):
        return type(self) != type(other)

OFP_DESC_STATS_REQUEST_BYTES = 0

class ofp_table_stats_request:
    """
    Forced definition of ofp_table_stats_request (empty class)
    """
    def __init__(self):
        pass
    def pack(self, assertstruct=True):
        return ""
    def unpack(self, binary_string):
        return binary_string
    def __len__(self):
        return 0
    def show(self, prefix=''):
        return prefix + "ofp_table_stats_request (empty)\n"
    def __eq__(self, other):
        return type(self) == type(other)
    def __ne__(self, other):
        return type(self) != type(other)

OFP_TABLE_STATS_REQUEST_BYTES = 0



# Stats entries define the content of one element in a stats
# reply for the indicated type; define _entry for consistency

aggregate_stats_entry = ofp_aggregate_stats_reply
desc_stats_entry = ofp_desc_stats
port_stats_entry = ofp_port_stats
queue_stats_entry = ofp_queue_stats
table_stats_entry = ofp_table_stats


#
# Flow stats entry contains an action list of variable length, so
# it is done by hand
#

class flow_stats_entry(ofp_flow_stats):
    """
    Special case flow stats entry to handle action list object
    """
    def __init__(self):
        ofp_flow_stats.__init__(self)
        self.actions = []

    def pack(self, assertstruct=True):
        self.length = len(self)
        packed = ofp_flow_stats.pack(self, assertstruct)
        packed += action_list(self.actions).pack()
        if len(packed) != self.length:
            print("ERROR: flow_stats_entry pack length not equal",
                  self.length, len(packed))
        return packed

    def unpack(self, binary_string):
        binary_string = ofp_flow_stats.unpack(self, binary_string)
        ai_len = self.length - OFP_FLOW_STATS_BYTES
        if ai_len < 0:
            print("ERROR: flow_stats_entry unpack length too small",
                  self.length)
        obj = action_list()
        binary_string = obj.unpack(binary_string, bytes=ai_len)
        self.actions = list(obj)
        return binary_string

    def __len__(self):
        return OFP_FLOW_STATS_BYTES + len(self.actions)

    def show(self, prefix=''):
        outstr = prefix + "flow_stats_entry\n"
        outstr += ofp_flow_stats.show(self, prefix + '  ')
        outstr += prefix + "List actions\n"
        for obj in self.actions:
            outstr += obj.show(prefix + '  ')
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (ofp_flow_stats.__eq__(self, other) and 
                self.actions == other.actions)

    def __ne__(self, other): return not self.__eq__(other)


class aggregate_stats_request(ofp_stats_request, ofp_aggregate_stats_request):
    """
    Wrapper class for aggregate stats request message
    """
    def __init__(self, **kwargs):
        self.header = ofp_header()
        ofp_stats_request.__init__(self)
        ofp_aggregate_stats_request.__init__(self)
        self.header.type = OFPT_STATS_REQUEST
        self.type = OFPST_AGGREGATE
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))

    def pack(self, assertstruct=True):
        self.header.length = len(self)
        packed = self.header.pack()
        packed += ofp_stats_request.pack(self)
        packed += ofp_aggregate_stats_request.pack(self)
        return packed

    def unpack(self, binary_string):
        binary_string = self.header.unpack(binary_string)
        binary_string = ofp_stats_request.unpack(self, binary_string)
        binary_string = ofp_aggregate_stats_request.unpack(self, binary_string)
        if len(binary_string) != 0:
            print "ERROR unpacking aggregate: extra data"
        return binary_string

    def __len__(self):
        return len(self.header) + OFP_STATS_REQUEST_BYTES + \
               OFP_AGGREGATE_STATS_REQUEST_BYTES

    def show(self, prefix=''):
        outstr = prefix + "aggregate_stats_request\n"
        outstr += prefix + "ofp header:\n"
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_stats_request.show(self)
        outstr += ofp_aggregate_stats_request.show(self)
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (self.header == other.header and
                ofp_stats_request.__eq__(self, other) and
                ofp_aggregate_stats_request.__eq__(self, other))

    def __ne__(self, other): return not self.__eq__(other)


class aggregate_stats_reply(ofp_stats_reply):
    """
    Wrapper class for aggregate stats reply
    """
    def __init__(self):
        self.header = ofp_header()
        ofp_stats_reply.__init__(self)
        self.header.type = OFPT_STATS_REPLY
        self.type = OFPST_AGGREGATE
        # stats: Array of type aggregate_stats_entry
        self.stats = []

    def pack(self, assertstruct=True):
        self.header.length = len(self)
        packed = self.header.pack()
        packed += ofp_stats_reply.pack(self)
        for obj in self.stats:
            packed += obj.pack()
        return packed

    def unpack(self, binary_string):
        binary_string = self.header.unpack(binary_string)
        binary_string = ofp_stats_reply.unpack(self, binary_string)
        dummy = aggregate_stats_entry()
        while len(binary_string) >= len(dummy):
            obj = aggregate_stats_entry()
            binary_string = obj.unpack(binary_string)
            self.stats.append(obj)
        if len(binary_string) != 0:
            print "ERROR unpacking aggregate stats string: extra bytes"
        return binary_string

    def __len__(self):
        length = len(self.header) + OFP_STATS_REPLY_BYTES
        for obj in self.stats:
            length += len(obj)
        return length

    def show(self, prefix=''):
        outstr = prefix + "aggregate_stats_reply\n"
        outstr += prefix + "ofp header:\n"
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_stats_reply.show(self)
        outstr += prefix + "Stats array of length " + str(len(self.stats)) + '\n'
        for obj in self.stats:
            outstr += obj.show()
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (self.header == other.header and
                ofp_stats_reply.__eq__(self, other) and
                self.stats == other.stats)

    def __ne__(self, other): return not self.__eq__(other)


class desc_stats_request(ofp_stats_request, ofp_desc_stats_request):
    """
    Wrapper class for desc stats request message
    """
    def __init__(self, **kwargs):
        self.header = ofp_header()
        ofp_stats_request.__init__(self)
        ofp_desc_stats_request.__init__(self)
        self.header.type = OFPT_STATS_REQUEST
        self.type = OFPST_DESC
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))

    def pack(self, assertstruct=True):
        self.header.length = len(self)
        packed = self.header.pack()
        packed += ofp_stats_request.pack(self)
        packed += ofp_desc_stats_request.pack(self)
        return packed

    def unpack(self, binary_string):
        binary_string = self.header.unpack(binary_string)
        binary_string = ofp_stats_request.unpack(self, binary_string)
        binary_string = ofp_desc_stats_request.unpack(self, binary_string)
        if len(binary_string) != 0:
            print "ERROR unpacking desc: extra data"
        return binary_string

    def __len__(self):
        return len(self.header) + OFP_STATS_REQUEST_BYTES + \
               OFP_DESC_STATS_REQUEST_BYTES

    def show(self, prefix=''):
        outstr = prefix + "desc_stats_request\n"
        outstr += prefix + "ofp header:\n"
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_stats_request.show(self)
        outstr += ofp_desc_stats_request.show(self)
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (self.header == other.header and
                ofp_stats_request.__eq__(self, other) and
                ofp_desc_stats_request.__eq__(self, other))

    def __ne__(self, other): return not self.__eq__(other)


class desc_stats_reply(ofp_stats_reply):
    """
    Wrapper class for desc stats reply
    """
    def __init__(self):
        self.header = ofp_header()
        ofp_stats_reply.__init__(self)
        self.header.type = OFPT_STATS_REPLY
        self.type = OFPST_DESC
        # stats: Array of type desc_stats_entry
        self.stats = []

    def pack(self, assertstruct=True):
        self.header.length = len(self)
        packed = self.header.pack()
        packed += ofp_stats_reply.pack(self)
        for obj in self.stats:
            packed += obj.pack()
        return packed

    def unpack(self, binary_string):
        binary_string = self.header.unpack(binary_string)
        binary_string = ofp_stats_reply.unpack(self, binary_string)
        dummy = desc_stats_entry()
        while len(binary_string) >= len(dummy):
            obj = desc_stats_entry()
            binary_string = obj.unpack(binary_string)
            self.stats.append(obj)
        if len(binary_string) != 0:
            print "ERROR unpacking desc stats string: extra bytes"
        return binary_string

    def __len__(self):
        length = len(self.header) + OFP_STATS_REPLY_BYTES
        for obj in self.stats:
            length += len(obj)
        return length

    def show(self, prefix=''):
        outstr = prefix + "desc_stats_reply\n"
        outstr += prefix + "ofp header:\n"
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_stats_reply.show(self)
        outstr += prefix + "Stats array of length " + str(len(self.stats)) + '\n'
        for obj in self.stats:
            outstr += obj.show()
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (self.header == other.header and
                ofp_stats_reply.__eq__(self, other) and
                self.stats == other.stats)

    def __ne__(self, other): return not self.__eq__(other)


class flow_stats_request(ofp_stats_request, ofp_flow_stats_request):
    """
    Wrapper class for flow stats request message
    """
    def __init__(self, **kwargs):
        self.header = ofp_header()
        ofp_stats_request.__init__(self)
        ofp_flow_stats_request.__init__(self)
        self.header.type = OFPT_STATS_REQUEST
        self.type = OFPST_FLOW
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))

    def pack(self, assertstruct=True):
        self.header.length = len(self)
        packed = self.header.pack()
        packed += ofp_stats_request.pack(self)
        packed += ofp_flow_stats_request.pack(self)
        return packed

    def unpack(self, binary_string):
        binary_string = self.header.unpack(binary_string)
        binary_string = ofp_stats_request.unpack(self, binary_string)
        binary_string = ofp_flow_stats_request.unpack(self, binary_string)
        if len(binary_string) != 0:
            print "ERROR unpacking flow: extra data"
        return binary_string

    def __len__(self):
        return len(self.header) + OFP_STATS_REQUEST_BYTES + \
               OFP_FLOW_STATS_REQUEST_BYTES

    def show(self, prefix=''):
        outstr = prefix + "flow_stats_request\n"
        outstr += prefix + "ofp header:\n"
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_stats_request.show(self)
        outstr += ofp_flow_stats_request.show(self)
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (self.header == other.header and
                ofp_stats_request.__eq__(self, other) and
                ofp_flow_stats_request.__eq__(self, other))

    def __ne__(self, other): return not self.__eq__(other)


class flow_stats_reply(ofp_stats_reply):
    """
    Wrapper class for flow stats reply
    """
    def __init__(self):
        self.header = ofp_header()
        ofp_stats_reply.__init__(self)
        self.header.type = OFPT_STATS_REPLY
        self.type = OFPST_FLOW
        # stats: Array of type flow_stats_entry
        self.stats = []

    def pack(self, assertstruct=True):
        self.header.length = len(self)
        packed = self.header.pack()
        packed += ofp_stats_reply.pack(self)
        for obj in self.stats:
            packed += obj.pack()
        return packed

    def unpack(self, binary_string):
        binary_string = self.header.unpack(binary_string)
        binary_string = ofp_stats_reply.unpack(self, binary_string)
        dummy = flow_stats_entry()
        while len(binary_string) >= len(dummy):
            obj = flow_stats_entry()
            binary_string = obj.unpack(binary_string)
            self.stats.append(obj)
        if len(binary_string) != 0:
            print "ERROR unpacking flow stats string: extra bytes"
        return binary_string

    def __len__(self):
        length = len(self.header) + OFP_STATS_REPLY_BYTES
        for obj in self.stats:
            length += len(obj)
        return length

    def show(self, prefix=''):
        outstr = prefix + "flow_stats_reply\n"
        outstr += prefix + "ofp header:\n"
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_stats_reply.show(self)
        outstr += prefix + "Stats array of length " + str(len(self.stats)) + '\n'
        for obj in self.stats:
            outstr += obj.show()
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (self.header == other.header and
                ofp_stats_reply.__eq__(self, other) and
                self.stats == other.stats)

    def __ne__(self, other): return not self.__eq__(other)


class port_stats_request(ofp_stats_request, ofp_port_stats_request):
    """
    Wrapper class for port stats request message
    """
    def __init__(self, **kwargs):
        self.header = ofp_header()
        ofp_stats_request.__init__(self)
        ofp_port_stats_request.__init__(self)
        self.header.type = OFPT_STATS_REQUEST
        self.type = OFPST_PORT
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))

    def pack(self, assertstruct=True):
        self.header.length = len(self)
        packed = self.header.pack()
        packed += ofp_stats_request.pack(self)
        packed += ofp_port_stats_request.pack(self)
        return packed

    def unpack(self, binary_string):
        binary_string = self.header.unpack(binary_string)
        binary_string = ofp_stats_request.unpack(self, binary_string)
        binary_string = ofp_port_stats_request.unpack(self, binary_string)
        if len(binary_string) != 0:
            print "ERROR unpacking port: extra data"
        return binary_string

    def __len__(self):
        return len(self.header) + OFP_STATS_REQUEST_BYTES + \
               OFP_PORT_STATS_REQUEST_BYTES

    def show(self, prefix=''):
        outstr = prefix + "port_stats_request\n"
        outstr += prefix + "ofp header:\n"
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_stats_request.show(self)
        outstr += ofp_port_stats_request.show(self)
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (self.header == other.header and
                ofp_stats_request.__eq__(self, other) and
                ofp_port_stats_request.__eq__(self, other))

    def __ne__(self, other): return not self.__eq__(other)


class port_stats_reply(ofp_stats_reply):
    """
    Wrapper class for port stats reply
    """
    def __init__(self):
        self.header = ofp_header()
        ofp_stats_reply.__init__(self)
        self.header.type = OFPT_STATS_REPLY
        self.type = OFPST_PORT
        # stats: Array of type port_stats_entry
        self.stats = []

    def pack(self, assertstruct=True):
        self.header.length = len(self)
        packed = self.header.pack()
        packed += ofp_stats_reply.pack(self)
        for obj in self.stats:
            packed += obj.pack()
        return packed

    def unpack(self, binary_string):
        binary_string = self.header.unpack(binary_string)
        binary_string = ofp_stats_reply.unpack(self, binary_string)
        dummy = port_stats_entry()
        while len(binary_string) >= len(dummy):
            obj = port_stats_entry()
            binary_string = obj.unpack(binary_string)
            self.stats.append(obj)
        if len(binary_string) != 0:
            print "ERROR unpacking port stats string: extra bytes"
        return binary_string

    def __len__(self):
        length = len(self.header) + OFP_STATS_REPLY_BYTES
        for obj in self.stats:
            length += len(obj)
        return length

    def show(self, prefix=''):
        outstr = prefix + "port_stats_reply\n"
        outstr += prefix + "ofp header:\n"
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_stats_reply.show(self)
        outstr += prefix + "Stats array of length " + str(len(self.stats)) + '\n'
        for obj in self.stats:
            outstr += obj.show()
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (self.header == other.header and
                ofp_stats_reply.__eq__(self, other) and
                self.stats == other.stats)

    def __ne__(self, other): return not self.__eq__(other)


class queue_stats_request(ofp_stats_request, ofp_queue_stats_request):
    """
    Wrapper class for queue stats request message
    """
    def __init__(self, **kwargs):
        self.header = ofp_header()
        ofp_stats_request.__init__(self)
        ofp_queue_stats_request.__init__(self)
        self.header.type = OFPT_STATS_REQUEST
        self.type = OFPST_QUEUE
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))

    def pack(self, assertstruct=True):
        self.header.length = len(self)
        packed = self.header.pack()
        packed += ofp_stats_request.pack(self)
        packed += ofp_queue_stats_request.pack(self)
        return packed

    def unpack(self, binary_string):
        binary_string = self.header.unpack(binary_string)
        binary_string = ofp_stats_request.unpack(self, binary_string)
        binary_string = ofp_queue_stats_request.unpack(self, binary_string)
        if len(binary_string) != 0:
            print "ERROR unpacking queue: extra data"
        return binary_string

    def __len__(self):
        return len(self.header) + OFP_STATS_REQUEST_BYTES + \
               OFP_QUEUE_STATS_REQUEST_BYTES

    def show(self, prefix=''):
        outstr = prefix + "queue_stats_request\n"
        outstr += prefix + "ofp header:\n"
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_stats_request.show(self)
        outstr += ofp_queue_stats_request.show(self)
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (self.header == other.header and
                ofp_stats_request.__eq__(self, other) and
                ofp_queue_stats_request.__eq__(self, other))

    def __ne__(self, other): return not self.__eq__(other)


class queue_stats_reply(ofp_stats_reply):
    """
    Wrapper class for queue stats reply
    """
    def __init__(self):
        self.header = ofp_header()
        ofp_stats_reply.__init__(self)
        self.header.type = OFPT_STATS_REPLY
        self.type = OFPST_QUEUE
        # stats: Array of type queue_stats_entry
        self.stats = []

    def pack(self, assertstruct=True):
        self.header.length = len(self)
        packed = self.header.pack()
        packed += ofp_stats_reply.pack(self)
        for obj in self.stats:
            packed += obj.pack()
        return packed

    def unpack(self, binary_string):
        binary_string = self.header.unpack(binary_string)
        binary_string = ofp_stats_reply.unpack(self, binary_string)
        dummy = queue_stats_entry()
        while len(binary_string) >= len(dummy):
            obj = queue_stats_entry()
            binary_string = obj.unpack(binary_string)
            self.stats.append(obj)
        if len(binary_string) != 0:
            print "ERROR unpacking queue stats string: extra bytes"
        return binary_string

    def __len__(self):
        length = len(self.header) + OFP_STATS_REPLY_BYTES
        for obj in self.stats:
            length += len(obj)
        return length

    def show(self, prefix=''):
        outstr = prefix + "queue_stats_reply\n"
        outstr += prefix + "ofp header:\n"
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_stats_reply.show(self)
        outstr += prefix + "Stats array of length " + str(len(self.stats)) + '\n'
        for obj in self.stats:
            outstr += obj.show()
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (self.header == other.header and
                ofp_stats_reply.__eq__(self, other) and
                self.stats == other.stats)

    def __ne__(self, other): return not self.__eq__(other)


class table_stats_request(ofp_stats_request, ofp_table_stats_request):
    """
    Wrapper class for table stats request message
    """
    def __init__(self, **kwargs):
        self.header = ofp_header()
        ofp_stats_request.__init__(self)
        ofp_table_stats_request.__init__(self)
        self.header.type = OFPT_STATS_REQUEST
        self.type = OFPST_TABLE
        for (k, v) in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise NameError("field %s does not exist in %s" % (k, self.__class__))

    def pack(self, assertstruct=True):
        self.header.length = len(self)
        packed = self.header.pack()
        packed += ofp_stats_request.pack(self)
        packed += ofp_table_stats_request.pack(self)
        return packed

    def unpack(self, binary_string):
        binary_string = self.header.unpack(binary_string)
        binary_string = ofp_stats_request.unpack(self, binary_string)
        binary_string = ofp_table_stats_request.unpack(self, binary_string)
        if len(binary_string) != 0:
            print "ERROR unpacking table: extra data"
        return binary_string

    def __len__(self):
        return len(self.header) + OFP_STATS_REQUEST_BYTES + \
               OFP_TABLE_STATS_REQUEST_BYTES

    def show(self, prefix=''):
        outstr = prefix + "table_stats_request\n"
        outstr += prefix + "ofp header:\n"
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_stats_request.show(self)
        outstr += ofp_table_stats_request.show(self)
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (self.header == other.header and
                ofp_stats_request.__eq__(self, other) and
                ofp_table_stats_request.__eq__(self, other))

    def __ne__(self, other): return not self.__eq__(other)


class table_stats_reply(ofp_stats_reply):
    """
    Wrapper class for table stats reply
    """
    def __init__(self):
        self.header = ofp_header()
        ofp_stats_reply.__init__(self)
        self.header.type = OFPT_STATS_REPLY
        self.type = OFPST_TABLE
        # stats: Array of type table_stats_entry
        self.stats = []

    def pack(self, assertstruct=True):
        self.header.length = len(self)
        packed = self.header.pack()
        packed += ofp_stats_reply.pack(self)
        for obj in self.stats:
            packed += obj.pack()
        return packed

    def unpack(self, binary_string):
        binary_string = self.header.unpack(binary_string)
        binary_string = ofp_stats_reply.unpack(self, binary_string)
        dummy = table_stats_entry()
        while len(binary_string) >= len(dummy):
            obj = table_stats_entry()
            binary_string = obj.unpack(binary_string)
            self.stats.append(obj)
        if len(binary_string) != 0:
            print "ERROR unpacking table stats string: extra bytes"
        return binary_string

    def __len__(self):
        length = len(self.header) + OFP_STATS_REPLY_BYTES
        for obj in self.stats:
            length += len(obj)
        return length

    def show(self, prefix=''):
        outstr = prefix + "table_stats_reply\n"
        outstr += prefix + "ofp header:\n"
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_stats_reply.show(self)
        outstr += prefix + "Stats array of length " + str(len(self.stats)) + '\n'
        for obj in self.stats:
            outstr += obj.show()
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (self.header == other.header and
                ofp_stats_reply.__eq__(self, other) and
                self.stats == other.stats)

    def __ne__(self, other): return not self.__eq__(other)


message_type_list = (
    aggregate_stats_reply,
    aggregate_stats_request,
    bad_action_error_msg,
    bad_request_error_msg,
    barrier_reply,
    barrier_request,
    desc_stats_reply,
    desc_stats_request,
    echo_reply,
    echo_request,
    features_reply,
    features_request,
    flow_mod,
    flow_mod_failed_error_msg,
    flow_removed,
    flow_stats_reply,
    flow_stats_request,
    get_config_reply,
    get_config_request,
    hello,
    hello_failed_error_msg,
    packet_in,
    packet_out,
    port_mod,
    port_mod_failed_error_msg,
    port_stats_reply,
    port_stats_request,
    port_status,
    queue_get_config_reply,
    queue_get_config_request,
    queue_op_failed_error_msg,
    queue_stats_reply,
    queue_stats_request,
    set_config,
    table_stats_reply,
    table_stats_request,
    vendor
    )

