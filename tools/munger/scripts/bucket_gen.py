#!/usr/bin/python
#
# This python script generates bucket subclasses
#

import sys
sys.path.append("../../src/python/oftest")
from class_maps import class_to_members_map
from common_gen import *

print """
# Python OpenFlow bucket wrapper class

from oftest.cstruct import ofp_bucket
from oftest.action_list import action_list

"""

bucket_class_template = """
class bucket(--PARENT_TYPE--):
    \"""
    Wrapper class for bucket object

    --DOC_INFO--
    \"""
    def __init__(self):
        --PARENT_TYPE--.__init__(self)
        self.actions = action_list()
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "bucket\\n"
        outstr += --PARENT_TYPE--.show(self, prefix)
        outstr += self.actions.show()
        return outstr
    def unpack(self, binary_string):
        binary_string = --PARENT_TYPE--.unpack(self, binary_string)
        self.actions = action_list()
        return self.actions.unpack(binary_string)
    def pack(self):
        self.len = len(self)
        packed = ""
        packed += --PARENT_TYPE--.pack(self)
        packed += self.actions.pack()
        return packed
    def __len__(self):
        return --PARENT_TYPE--.__len__(self) + self.actions.__len__()
"""
    
if __name__ == '__main__':
    gen_class('bucket', 'ofp_bucket', "bucket", template=bucket_class_template)
