
# Python OpenFlow bucket wrapper class

from cstruct import ofp_bucket
from action_list import action_list



class bucket(ofp_bucket):
    """
    Wrapper class for bucket object

    Data members inherited from ofp_bucket:
    @arg len
    @arg weight
    @arg watch_port
    @arg watch_group

    """
    def __init__(self):
        ofp_bucket.__init__(self)
        self.actions = action_list()
        self.type = None
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "bucket\n"
        outstr += ofp_bucket.show(self, prefix)
        outstr += self.actions.show()
        return outstr
    def unpack(self, binary_string):
        binary_string = ofp_bucket.unpack(self, binary_string)
        self.actions = action_list()
        return self.actions.unpack(binary_string)
    def pack(self):
        self.len = len(self)
        packed = ""
        packed += ofp_bucket.pack(self)
        packed += self.actions.pack()
        return packed
    def __len__(self):
        return ofp_bucket.__len__(self) + self.actions.__len__()

