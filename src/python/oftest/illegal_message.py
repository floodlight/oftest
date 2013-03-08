"""
Support an illegal message
"""

import of10

ILLEGAL_MESSAGE_TYPE=217

class illegal_message_type:
    """
    Wrapper class for illegal message

    OpenFlow message header: length, version, xid, type
    @arg length: The total length of the message
    @arg version: The OpenFlow version (1)
    @arg xid: The transaction ID
    @arg type: The message type (OFPT_ECHO_REQUEST=2)

    @arg data: Binary string following message members

    The message type is set to "illegal" and the pack assert
    check for the OF header is disabled
    """

    def __init__(self):
        self.header = of10.ofp_header()
        self.header.type = ILLEGAL_MESSAGE_TYPE
        self.data = ""

    def pack(self):
        """
        Pack object into string

        @return The packed string which can go on the wire

        """
        self.header.length = len(self)
        packed = self.header.pack(assertstruct=False)

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
        length = of10.OFP_HEADER_BYTES

        length += len(self.data)
        return length

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """

        outstr = prefix + 'illegal_message (' + \
            str(ILLEGAL_MESSAGE_TYPE) + ')\n'
        prefix += '  '
        outstr += prefix + 'ofp header\n'
        outstr += self.header.show(prefix + '  ')
        outstr += prefix + 'data is of length ' + str(len(self.data)) + '\n'
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
