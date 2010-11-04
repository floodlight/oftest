"""
OpenFlow instruction list class
"""

from action import *
from instruction import *
from action_list import action_list
from base_list import ofp_base_list
from cstruct import ofp_header
import copy

# Instruction list

instruction_object_map = {
    OFPIT_GOTO_TABLE          : instruction_goto_table,
    OFPIT_WRITE_METADATA      : instruction_write_metadata,      
    OFPIT_WRITE_ACTIONS       : instruction_write_actions,       
    OFPIT_APPLY_ACTIONS       : instruction_apply_actions,       
    OFPIT_CLEAR_ACTIONS       : instruction_clear_actions,       
    OFPIT_EXPERIMENTER        : instruction_experimenter        
}

class instruction_list(ofp_base_list):
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
        self.instructions = self.items
        self.name = "instruction"
        self.class_list = instruction_class_list

    def unpack(self, binary_string, bytes=None):
        """
        Unpack a list of instructions
        
        Unpack instructions from a binary string, creating an array
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
        count = 0
        cur_string = binary_string
        while bytes_done < bytes:
            hdr = ofp_instruction()
            hdr.unpack(cur_string)
            if hdr.len < OFP_ACTION_HEADER_BYTES:
                print "ERROR: Action too short"
                break
            if not hdr.type in instruction_object_map.keys():
                print "WARNING: Skipping unknown action ", hdr.type, hdr.len
            else:
                self.instructions.append(instruction_object_map[hdr.type]())
                self.instructions[count].unpack(cur_string)
                count += 1
            cur_string = cur_string[hdr.len:]
            bytes_done += hdr.len
        return cur_string
