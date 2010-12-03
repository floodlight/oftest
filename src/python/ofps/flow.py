######################################################################
#
# All files associated with the OpenFlow Python Switch (ofps) are
# made available for public use and benefit with the expectation
# that others will use, modify and enhance the Software and contribute
# those enhancements back to the community. However, since we would
# like to make the Software available for broadest use, with as few
# restrictions as possible permission is hereby granted, free of
# charge, to any person obtaining a copy of this Software to deal in
# the Software under the copyrights without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject
# to the following conditions:
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# 
######################################################################

"""
FlowEntry class definition

The implementation of the basic abstraction of an entry in a flow
table.
"""

import oftest.cstruct as ofp
import oftest.message as message
import oftest.instruction as instruction
import copy
import time
import logging

flow_logger = logging.getLogger("flow")

def is_delete_cmd(command):
    """
    Return boolean indicating if this flow mod operation is delete
    """
    return (command == ofp.OFPFC_DELETE or 
            command == ofp.OFPFC_DELETE_STRICT)

def is_strict_cmd(command):
    """
    Return boolean indicating if this flow mod operation is delete
    We indicate ADD as a strict operation for matching.
    """
    return (command == ofp.OFPFC_MODIFY_STRICT or 
            command == ofp.OFPFC_DELETE_STRICT or
            command == ofp.OFPFC_ADD)

def action_list_has_out_port(action_list, port, groups):
    """
    Return boolean indicating if the flow has a set output port
    action for the given port.  Assumes port is not OFPP_ANY.
    Called recursively on bucket action lists (so someone had
    better check for loops in group lists elsewhere).
    """
    for action in action_list:
        if action.__class__ == action.set_output_port:
            if action.port == port:
                return True
        if action.__class__ == action.action_group:
            group = groups.group_get(action.group_id)
            for bucket in group.buckets:
                # @todo Do we need to take into account bucket type?
                if action_list_has_out_port(bucket.actions, port, groups):
                    return True
    return False

def flow_has_out_port(flow, port, groups):
    """
    Return boolean indicating if the flow has a set output port
    action for the given port.  Assumes port is not OFPP_ANY.

    NOTE: All groups and all group buckets are searched, not just
    active buckets.
    """
    if port == ofp.OFPP_ANY or port == ofp.OFPP_ALL:
        return True

    for inst in flow.flow_mod.instructions:
        if inst.__class__ == instruction.instruction_write_actions or \
                inst.__class__ == instruction.instruction_apply_actions:
            if action_list_has_out_port(inst.actions, port, groups):
                return True

    return False

def flow_has_cookie(flow, cookie):
    """ Check if this flow matches this cookie
    
    #@todo extend to include Dave's extenisble cookie thinger
    """
    
    if cookie == 0 or flow.flow_mod.cookie == cookie:
        return True
    return False
        
def action_list_has_out_group(action_list, group_id, groups):
    """
    Return boolean indicating if the action list has a group action
    action for the given port.  Assumes group is not OFPG_ANY.
    """
    for action in action_list:
        if action.__class__ == action.set_group:
            if action.group_id == group_id:
                return True
            group = groups.group_get(action.group_id)
            for bucket in group.buckets:
                # @todo Do we need to take into account bucket type?
                if action_list_has_out_group(bucket.actions, group_id, groups):
                    return True
    return False

def flow_has_out_group(flow, group_id, groups):
    """
    Return boolean indicating if the flow has a group action
    action for the given port.  Assumes group is not OFPG_ANY.
    """
    for inst in flow.instructions:
        if inst.__class__ == instruction.instruction_write_actions or \
                inst.__class__ == instruction.instruction_apply_actions:
            if action_list_has_out_group(inst.actions, group_id, groups):
                return True

def meta_match(match_a, match_b):
    """
    Compare non-packet data in_port and metadata
    @params match_a Used for wildcards and masks
    @params match_b Other fields for match
    """
    wildcards = match_a.wildcards
    if not (wildcards & ofp.OFPFW_IN_PORT):
        # @todo logical port match?
        if match_a.in_port != match_b.in_port:
            flow_logger.debug("Failed in port")
            return False

    #@todo Does this 64 bit stuff work in Python?
    if (match_a.metadata_mask & match_a.metadata !=
        match_a.metadata_mask & match_b.metadata):
        flow_logger.debug("Failed metadata")
        return False

    return True

def l2_match(match_a, match_b):
    """
    Compare in_port, L2 fields and VLAN and MPLS tags for two flows
    @params match_a Used for wildcards and masks
    @params match_b Other fields for match
    """
    wildcards = match_a.wildcards

    # Addresses and metadata:  
    # @todo Check masks are negated ecorrectly
    idx = 0
    for byte in match_a.dl_src_mask:
        byte = ~byte
        if match_a.dl_src[idx] & byte != match_b.dl_src[idx] & byte:
            flow_logger.debug("Failed dl_src byte" + str(idx))
            return False
        idx += 1
    idx = 0
    for byte in match_a.dl_dst_mask:
        byte = ~byte
        if match_a.dl_dst[idx] & byte != match_b.dl_dst[idx] & byte:
            flow_logger.debug("Failed dl_dst byte" + str(idx))
            return False
        idx += 1
    mask = ~match_a.metadata_mask
    if match_a.metadata & mask != match_b.metadata & mask:
        flow_logger.debug("Failed L2 metadata" + str(idx))
        return False

    # @todo  Check untagged logic
    if not (wildcards & ofp.OFPFW_DL_VLAN):
        if match_a.dl_vlan != match_b.dl_vlan:
            flow_logger.debug("Failed dl_vlan")
            return False
    if not (wildcards & ofp.OFPFW_DL_VLAN_PCP):
        if match_a.dl_vlan_pcp != match_b.dl_vlan_pcp:
            flow_logger.debug("Failed dl_vlan_pcp")
            return False
    if not (wildcards & ofp.OFPFW_DL_TYPE):
        if match_a.dl_type != match_b.dl_type:
            flow_logger.debug("Failed dl_type")
            return False

    if not (wildcards & ofp.OFPFW_MPLS_LABEL):
        if match_a.mpls_label != match_b.mpls_label:
            flow_logger.debug("Failed mpls_label")
            return False
    if not (wildcards & ofp.OFPFW_MPLS_TC):
        if match_a.mpls_tc != match_b.mpls_tc:
            flow_logger.debug("Failed mpls_tc")
            return False

    return True

def l3_match(match_a, match_b):
    """
    Check IP fields for match, not strict
    @params match_a Used for wildcards and masks
    @params match_b Other fields for match
    """

    wildcards = match_a.wildcards
    if not (wildcards & ofp.OFPFW_NW_TOS):
        if match_a.nw_tos != match_b.nw_tos:
            flow_logger.debug("Failed nw_tos")
            return False
    if not (wildcards & ofp.OFPFW_NW_PROTO):
        if match_a.nw_proto != match_b.nw_proto:
            flow_logger.debug("Failed nw_proto")
            return False
        #@todo COMPLETE THIS
    mask = ~match_a.nw_src_mask
    if match_a.nw_src & mask != match_b.nw_src & mask:
        flow_logger.debug("Failed nw_src")
        return False
    mask = ~match_a.nw_dst_mask
    if match_a.nw_dst & mask != match_b.nw_dst & mask:
        flow_logger.debug("Failed nw_dst")
        return False

    return True

def flow_match_strict(flow_a, flow_b, groups):
    """
    Check if flows match strictly
    @param flow_a Primary key for cookie mask, etc
    @param flow_b Other key to match
    """
    wildcards_a = flow_a.match.wildcards
    wildcards_b = flow_b.match.wildcards
    if (wildcards_a != wildcards_b):
        flow_logger.debug("Failed wildcards")
        return False
    if (flow_a.priority != flow_b.priority):
        flow_logger.debug("Failed priority")
        return False
    if (flow_a.cookie_mask & flow_a.cookie != 
        flow_a.cookie_mask & flow_b.cookie):
        flow_logger.debug("Failed cookie")
        return False
    if is_delete_cmd(flow_a.command):
        if (flow_a.out_port != ofp.OFPP_ANY):
            if not flow_has_out_port(flow_b, flow_a.out_port, groups):
                flow_logger.debug("Failed out_port")
                return False
        if (flow_a.out_group != ofp.OFPG_ANY):
            if not flow_has_out_group(flow_b, flow_a.out_group, groups):
                flow_logger.debug("Failed out_group")
                return False

    if not l2_match(flow_a.match, flow_b.match):
        return False

    # @todo  Switch on DL type; handle ARP cases, etc
    # @todo  What if DL_TYPE is wildcarded?
    if flow_a.match.dl_type == 0x800:
        if not l3_match(flow_a.match, flow_b.match):
            return False

    return True

class FlowEntry(object):
    """
    Structure to track a flow table entry
    """
    def __init__(self):
        self.flow_mod = message.flow_mod()
        self.last_hit = None
        self.packets = 0
        self.bytes = 0
        self.insert_time = None

    def flow_mod_set(self, flow_mod):
        """
        Set this flow entry's core flow_mod message
        """
        self.flow_mod = copy.deepcopy(flow_mod)
        self.last_hit = None
        self.packets = 0
        self.bytes = 0
        self.insert_time = time.time()

    def match_flow_mod(self, new_flow, groups):
        """
        Return boolean indicating whether new_flow matches this flow
        This is used for add/modify/delete operations
        @param new_flow The flow_mod object to match.
        """
        if (new_flow.flags & ofp.OFPFF_CHECK_OVERLAP):
            print("Check overlap set but not implemented")
            #@todo implement

        if is_strict_cmd(new_flow.command):
            return flow_match_strict(new_flow, self.flow_mod, groups)
        
        # This just looks like a packet match from here.
        if not meta_match(new_flow.match, self.flow_mod.match):
            return False
        if not l2_match(new_flow.match, self.flow_mod.match):
            return False
        if new_flow.match.dl_type == 0x800:
            if not l3_match(new_flow.match, self.flow_mod.match):
                return False

        return True
        
    def match_packet(self, packet):
        """
        Return boolean indicating packet matches this flow entry
        Updates flow's counters if match occurs
        @param packet The packet object to match.  Assumes parse is up to date
        """

        if not meta_match(self.flow_mod.match, packet.match):
            flow_logger.debug("packet match failed meta_match")
            return False
        if not l2_match(self.flow_mod.match, packet.match):
            flow_logger.debug("packet match failed l2_match")
            return False
        if not l3_match(self.flow_mod.match, packet.match):
            flow_logger.debug("packet match failed l3_match")
            return False

        flow_logger.debug("Packet matched flow")
        # Okay, if we get here, we have a match.
        self.last_hit = time.time()
        self.packets += 1
        self.bytes += packet.bytes

        return True

    def expire(self):
        """
        Check if this entry should be expired.  
        Returns True if so, False otherwise
        """
        now = time.time()
        if self.flow_mod.hard_timeout:
            delta = now - self.insert_time
            if delta > self.flow_mod.hard_timeout:
                return True
        if self.flow_mod.idle_timeout:
            if self.last_hit is None:
                delta = now - self.insert_time
            else:
                delta = now - self.last_hit
            if delta > self.flow_mod.idle_timeout:
                return True
        return False
    
    def flow_stat_get(self):
        """
        Create a single flow_stat object representing this flow entry
        
        NOTE: the table_id is left blank and needs to be filled in by calling function
        (FlowEntries have no idea which table they're in)

        @todo Check if things like match and instructions should be copies
        """
        stat = message.flow_stats_entry()
        delta = time.time() - self.insert_time
        stat.duration_sec = int(delta)
        # need the extra int() line here because python time might have
        # higher precision
        stat.duration_nsec = int((delta - stat.duration_sec) * 1e9)
        stat.priority = self.flow_mod.priority
        stat.idle_timeout = self.flow_mod.idle_timeout
        stat.hard_timeout = self.flow_mod.hard_timeout
        stat.cookie = self.flow_mod.cookie
        stat.packet_count = self.packets
        stat.byte_count = self.bytes
        stat.match = self.flow_mod.match
        stat.instructions = self.flow_mod.instructions
        return stat 

    def show(self, prefix=''):
        """
        Generate a string (with multiple lines) describing the contents
        of the object in a readable manner

        @param prefix Pre-pended at the beginning of each line.

        """
        outstr = prefix + 'flow_entry\n'
        prefix += '  '
        outstr += self.flow_mod.show(prefix)
        outstr += prefix + 'packets:   ' + str(self.packets)
        outstr += prefix + 'bytes:     ' + str(self.bytes)
        outstr += prefix + 'in time:   ' + str(self.insert_time)
        outstr += prefix + 'last hit:  ' + str(self.last_hit)
        return outstr
