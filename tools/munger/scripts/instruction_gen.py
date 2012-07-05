#!/usr/bin/env python
#
# This python script generates action subclasses
#

import sys
sys.path.append("../../src/python/oftest")
from cstruct import *
from class_maps import class_to_members_map
from common_gen import *

print """
# Python OpenFlow instruction wrapper classes

from cstruct import *
from action_list import action_list

"""

# Template for classes with an action list
template_action_list = """
class --OBJ_TYPE--_--TYPE--(--PARENT_TYPE--):
    \"""
    Wrapper class for --TYPE-- --OBJ_TYPE-- object

    --DOC_INFO--
    \"""
    def __init__(self):
        --PARENT_TYPE--.__init__(self)
        self.type = --ACT_INST_NAME--
        self.actions = action_list()
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "--OBJ_TYPE--_--TYPE--\\n"
        outstr += --PARENT_TYPE--.show(self, prefix)
        outstr += self.actions.show(prefix)
        return outstr
    def unpack(self, binary_string):
        binary_string = --PARENT_TYPE--.unpack(self, binary_string)
        bytes = self.len - OFP_INSTRUCTION_ACTIONS_BYTES
        self.actions = action_list()
        binary_string = self.actions.unpack(binary_string, bytes=bytes)
        return binary_string
    def pack(self):
        self.len = self.__len__()
        packed = ""
        packed += --PARENT_TYPE--.pack(self)
        packed += self.actions.pack()
        return packed
    def __len__(self):
        return --PARENT_TYPE--.__len__(self) + self.actions.__len__()
"""


################################################################
#
# Instruction subclasses
#
################################################################

instruction_class_map = {
    'goto_table'         : 'ofp_instruction_goto_table',
    'write_metadata'     : 'ofp_instruction_write_metadata',
    'write_actions'      : 'ofp_instruction_actions',
    'apply_actions'      : 'ofp_instruction_actions',
    'clear_actions'      : 'ofp_instruction',
}

# These require an action list
action_list_classes = ['write_actions', 'apply_actions']
    
if __name__ == '__main__':
    for (t, parent) in instruction_class_map.items():
        template = None
        if t in action_list_classes:
            template = template_action_list
        gen_class(t, parent, "instruction", template=template)

    # Generate a list of instruction classes
    inst_list = instruction_class_map.keys()
    inst_list.sort()
    print "instruction_class_list = ("
    prev = None
    for t in inst_list:
        if prev:
            print "    instruction_" + prev + ","
        prev = t
    print "    instruction_" + prev + ")"
