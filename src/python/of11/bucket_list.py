
from base_list import ofp_base_list
from bucket import bucket

class bucket_list(ofp_base_list):
    """
    Maintain a list of instructions

    Data members:
    @arg instructions An array of instructions such as write_actions

    Methods:
    @arg pack: Pack the structure into a string
    @arg unpack: Unpack a string to objects, with proper typing
    @arg add: Add an action to the list; you can directly access
    the action member, but add will validate that the added object 
    is an action.

    """

    def __init__(self):
        ofp_base_list.__init__(self)
        self.buckets = self.items
        self.name = "buckets"
        self.class_list = (bucket,)

    def unpack(self, binary_string, bytes=None):
        """
        Unpack a list of buckets
        
        Unpack buckets from a binary string, creating an array
        of objects of the appropriate type

        @param binary_string The string to be unpacked

        @param bytes The total length of the instruction list in bytes.  
        Ignored if decode is True.  If bytes is None and decode is false, the
        list is assumed to extend through the entire string.

        @return The remainder of binary_string that was not parsed

        """
        if bytes == None:
            bytes = len(binary_string)
        bytes_done = 0
        cur_string = binary_string
        while bytes_done < bytes:
            b = bucket()
            cur_string = b.unpack(cur_string)
            self.buckets.append(b)
            bytes_done += len(b)
        return cur_string
