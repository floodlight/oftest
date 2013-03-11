"""
Support an illegal message
"""

import of10

ILLEGAL_MESSAGE_TYPE=217

class illegal_message_type(of10.ofp_header):
    """
    Wrapper class for illegal_message_type

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (ILLEGAL_MESSAGE_TYPE=217)

    Data members inherited from ofp_header:
    @arg version
    @arg type
    @arg length
    @arg xid
    @arg data: Binary string following message members

    """

    def __init__(self, **kwargs):
        of10.ofp_header.__init__(self)
        self.version = of10.OFP_VERSION
        self.type = ILLEGAL_MESSAGE_TYPE
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
        self.length = len(self)
        packed = ""

        packed += of10.ofp_header.pack(self, assertstruct=False)
        packed += self.data
        return packed

    def unpack(self, binary_string):
        """
        Unpack object from a binary string

        @param binary_string The wire protocol byte string holding the object
        represented as an array of bytes.
        @return The remainder of binary_string that was not parsed.

        """

        binary_string = of10.ofp_header.unpack(self, binary_string)
        self.data = binary_string
        binary_string = ''
        return binary_string

    def __len__(self):
        """
        Return the length of this object once packed into a string

        @return An integer representing the number bytes in the packed
        string.

        """
        length = 0

        length += of10.ofp_header.__len__(self)
        length += len(self.data)
        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'illegal_message (217)\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += of10.ofp_header.show(self, prefix)
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

        if not of10.ofp_header.__eq__(self, other): return False
        if self.data != other.data: return False
        return True

    def __ne__(self, other):
        """
        Return True if self and other do not hold the same data

        @param other Other object in comparison

        """
        return not self.__eq__(other)
