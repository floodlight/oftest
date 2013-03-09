"""
OpenFlow actions list class
"""

from action import *
from cstruct import ofp_header
import copy

# # Map OFP action identifiers to the actual structures used on the wire
# action_object_map = {
#     OFPAT_OUTPUT                        : ofp_action_output,
#     OFPAT_SET_VLAN_VID                  : ofp_action_vlan_vid,
#     OFPAT_SET_VLAN_PCP                  : ofp_action_vlan_pcp,
#     OFPAT_STRIP_VLAN                    : ofp_action_header,
#     OFPAT_SET_DL_SRC                    : ofp_action_dl_addr,
#     OFPAT_SET_DL_DST                    : ofp_action_dl_addr,
#     OFPAT_SET_NW_SRC                    : ofp_action_nw_addr,
#     OFPAT_SET_NW_DST                    : ofp_action_nw_addr,
#     OFPAT_SET_NW_TOS                    : ofp_action_nw_tos,
#     OFPAT_SET_TP_SRC                    : ofp_action_tp_port,
#     OFPAT_SET_TP_DST                    : ofp_action_tp_port,
#     OFPAT_ENQUEUE                       : ofp_action_enqueue
# }

action_object_map = {
    OFPAT_OUTPUT                        : action_output,
    OFPAT_SET_VLAN_VID                  : action_set_vlan_vid,
    OFPAT_SET_VLAN_PCP                  : action_set_vlan_pcp,
    OFPAT_STRIP_VLAN                    : action_strip_vlan,
    OFPAT_SET_DL_SRC                    : action_set_dl_src,
    OFPAT_SET_DL_DST                    : action_set_dl_dst,
    OFPAT_SET_NW_SRC                    : action_set_nw_src,
    OFPAT_SET_NW_DST                    : action_set_nw_dst,
    OFPAT_SET_NW_TOS                    : action_set_nw_tos,
    OFPAT_SET_TP_SRC                    : action_set_tp_src,
    OFPAT_SET_TP_DST                    : action_set_tp_dst,
    OFPAT_ENQUEUE                       : action_enqueue,
    OFPAT_VENDOR                        : action_vendor
}

class action_list(object):
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

    def __init__(self, actions=None):
        if actions == None:
            actions = []
        self.actions = actions

    def pack(self):
        """
        Pack a list of actions

        Returns the packed string
        """

        packed = ""
        for act in self.actions:
            packed += act.pack()
        return packed

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

    def append(self, action):
        """
        Append an action to an action list

        @param action The action to append

        """
        if not isinstance(action, action_class_list):
            raise ValueError("%s is not an action" % type(action))
        self.actions.append(copy.deepcopy(action))
        return True # for backwards compatibility

    def remove_type(self, type):
        """
        Remove the first action on the list of the given type

        @param type The type of action to search

        @return The object removed, if any; otherwise None

        """
        for index in xrange(len(self.actions)):
            if self.actions[index].type == type:
                return self.actions.pop(index)
        return None

    def find_type(self, type):
        """
        Find the first action on the list of the given type

        @param type The type of action to search

        @return The object with the matching type if any; otherwise None

        """
        for index in xrange(len(self.actions)):
            if self.actions[index].type == type:
                return self.actions[index]
        return None

    def extend(self, other):
        """
        Add the actions in other to this list

        @param other An object of type action_list whose
        entries are to be merged into this list

        @return True if successful.  If not successful, the list
        may have been modified.

        @todo Check if this is proper deep copy or not

        """
        for act in other.actions:
            self.add(act)
        return True # for backwards compatibility
        
    def __len__(self):
        length = 0
        for act in self.actions:
            length += act.__len__()
        return length

    def __eq__(self, other):
        if type(self) != type(other): return False
        if self.actions != other.actions: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)
        
    def show(self, prefix=''):
        outstr = prefix + "Action List with " + str(len(self.actions)) + \
            " actions\n"
        count = 0
        for obj in self.actions:
            count += 1
            outstr += prefix + "  Action " + str(count) + ": \n"
            outstr += obj.show(prefix + '    ')
        return outstr
