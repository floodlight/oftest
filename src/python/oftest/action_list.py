"""
OpenFlow action, instruction and bucket list classes
"""

from action import *
from cstruct import ofp_header
import copy


#
# Base list class for inheritance.
# Most of the list stuff is common; unpacking is the only thing that
# is left pure virtual.
#

class ofp_base_list(object):
    """
    Container type to maintain a list of ofp objects

    Data members:
    @arg items An array of objects
    @arg class_list A list of classes that may be added to the list;
         If None, no checking is done
    @arg name The name to use when displaying the list

    Methods:
    @arg pack Pack the structure into a string
    @arg unpack Unpack a string to objects, with proper typing
    @arg add Add an item to the list; you can directly access
    the item member, but add will validate that the added object 
    is of the right type.
    @arg extend Add the items for another list to this list

    """

    def __init__(self):
        self.items = []
        self.class_list = None
        self.name = "unspecified"

    def pack(self):
        """
        Pack a list of items

        Returns the packed string
        """
        packed = ""
        for obj in self.items:
            packed += obj.pack()
        return packed

    def unpack(self, binary_string, bytes=None):
        """
        Pure virtual function for a list of items

        Unpack items from a binary string, creating an array
        of objects of the appropriate type

        @param binary_string The string to be unpacked

        @param bytes The total length of the list in bytes.  
        Ignored if decode is True.  If None and decode is false, the
        list is assumed to extend through the entire string.

        @return The remainder of binary_string that was not parsed
        """
        pass

    def add(self, item):
        """
        Add an item to a list

        @param item The item to add
        @return True if successful, False if not proper type object

        """
        if (self.class_list is not None) and \
                not isinstance(item, self.class_list):
            return False

        tmp = copy.deepcopy(item)
        self.items.append(tmp)
        return True

    def remove_type(self, type):
        """
        Remove the first item on the list of the given type

        @param type The type of item to search

        @return The object removed, if any; otherwise None

        """
        for index in xrange(len(self.items)):
            if self.items[index].type == type:
                return self.items.pop(index)
        return None

    def find_type(self, type):
        """
        Find the first item on the list of the given type

        @param type The type of item to search

        @return The object with the matching type if any; otherwise None

        """
        for index in xrange(len(self.items)):
            if self.items[index].type == type:
                return self.items[index]
        return None

    def extend(self, other):
        """
        Add the items in other to this list

        @param other An object of the same type of list whose
        entries are to be merged into this list

        @return True if successful.  If not successful, the list
        may have been modified.

        @todo Check if this is proper deep copy or not

        """
        for act in other.items:
            if not self.add(act):
                return False
        return True
        
    def __len__(self):
        length = 0
        for act in self.items:
            length += act.__len__()
        return length

    def __eq__(self, other):
        if type(self) != type(other): return False
        if self.items != other.items: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)
        
    def show(self, prefix=''):
        outstr = prefix + self.name + "list with " + str(len(self.items)) + \
            " items\n"
        count = 0
        for obj in self.items:
            count += 1
            outstr += prefix + " " + self.name + " " + str(count) + ": \n"
            outstr += obj.show(prefix + '    ')
        return outstr

action_object_map = {
    OFPAT_SET_OUTPUT_PORT               : action_set_output_port,
    OFPAT_SET_VLAN_VID                  : action_set_vlan_vid,
    OFPAT_SET_VLAN_PCP                  : action_set_vlan_pcp,
    OFPAT_SET_DL_SRC                    : action_set_dl_src,
    OFPAT_SET_DL_DST                    : action_set_dl_dst,
    OFPAT_SET_NW_SRC                    : action_set_nw_src,
    OFPAT_SET_NW_DST                    : action_set_nw_dst,
    OFPAT_SET_NW_TOS                    : action_set_nw_tos,
    OFPAT_SET_NW_ECN                    : action_set_nw_ecn,
    OFPAT_SET_TP_SRC                    : action_set_tp_src,
    OFPAT_SET_TP_DST                    : action_set_tp_dst,
    OFPAT_COPY_TTL_OUT                  : action_copy_ttl_out,
    OFPAT_COPY_TTL_IN                   : action_copy_ttl_in,
    OFPAT_SET_MPLS_LABEL                : action_set_mpls_label,
    OFPAT_SET_MPLS_TC                   : action_set_mpls_tc,
    OFPAT_SET_MPLS_TTL                  : action_set_mpls_ttl,
    OFPAT_DEC_MPLS_TTL                  : action_dec_mpls_ttl,
    OFPAT_PUSH_VLAN                     : action_push_vlan,
    OFPAT_POP_VLAN                      : action_pop_vlan,
    OFPAT_PUSH_MPLS                     : action_push_mpls,
    OFPAT_POP_MPLS                      : action_pop_mpls,
    OFPAT_SET_QUEUE                     : action_set_queue,
    OFPAT_GROUP                         : action_group,
    OFPAT_SET_NW_TTL                    : action_set_nw_ttl,
    OFPAT_DEC_NW_TTL                    : action_dec_nw_ttl,
    OFPAT_EXPERIMENTER                  : action_experimenter
}

class action_list(ofp_base_list):
    """
    Maintain a list of actions

    Data members:
    @arg actions: An array of action objects such as action_output, etc.

    Methods:
    @arg pack: Pack the structure into a string
    @arg unpack: Unpack a string to objects, with proper typing
    @arg add: Add an action to the list; you can directly access
    the action member, but add will validate that the added object 
    is an action.

    """

    def __init__(self):
        ofp_base_list.__init__(self)
        self.actions = self.items
        self.name = "action"
        self.class_list = action_class_list

    def unpack(self, binary_string, bytes=None):
        """
        Unpack a list of actions
        
        Unpack actions from a binary string, creating an array
        of objects of the appropriate type

        @param binary_string The string to be unpacked

        @param bytes The total length of the action list in bytes.  
        Ignored if decode is True.  If None and decode is false, the
        list is assumed to extend through the entire string.

        @return The remainder of binary_string that was not parsed

        """
        if bytes == None:
            bytes = len(binary_string)
        bytes_done = 0
        count = 0
        cur_string = binary_string
        while bytes_done < bytes:
            hdr = ofp_action_header()
            hdr.unpack(cur_string)
            if hdr.len < OFP_ACTION_HEADER_BYTES:
                print "ERROR: Action too short"
                break
            if not hdr.type in action_object_map.keys():
                print "WARNING: Skipping unknown action ", hdr.type, hdr.len
            else:
                self.actions.append(action_object_map[hdr.type]())
                self.actions[count].unpack(cur_string)
                count += 1
            cur_string = cur_string[hdr.len:]
            bytes_done += hdr.len
        return cur_string


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
        self.class_list = [bucket]

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
