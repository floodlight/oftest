"""
OpenFlow action, instruction and bucket list classes
"""

from action import *
from cstruct import ofp_header
from base_list import ofp_base_list
import copy

action_object_map = {
    OFPAT_OUTPUT                        : output,
    OFPAT_SET_FIELD                     : set_field,
    OFPAT_COPY_TTL_OUT                  : copy_ttl_out,
    OFPAT_COPY_TTL_IN                   : copy_ttl_in,
    OFPAT_SET_MPLS_TTL                  : set_mpls_ttl,
    OFPAT_DEC_MPLS_TTL                  : dec_mpls_ttl,
    OFPAT_PUSH_VLAN                     : push_vlan,
    OFPAT_POP_VLAN                      : pop_vlan,
    OFPAT_PUSH_MPLS                     : push_mpls,
    OFPAT_POP_MPLS                      : pop_mpls,
    OFPAT_SET_QUEUE                     : set_queue,
    OFPAT_GROUP                         : group,
    OFPAT_SET_NW_TTL                    : set_nw_ttl,
    OFPAT_DEC_NW_TTL                    : dec_nw_ttl,
    OFPAT_EXPERIMENTER                  : experimenter
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

    def __init__(self, actions=None):
        ofp_base_list.__init__(self)
        self.actions = self.items
        if actions:
            self.actions.extend(actions)
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

