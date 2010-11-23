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
from oftest.action import action_set_output_port

"""
FlowEntry class definition

The implementation of the basic abstraction of an entry in a flow
table.
"""

import oftest.cstruct as ofp
import oftest.message as message
import copy
import time

def is_delete_cmd(command):
    """
    Return boolean indicating if this flow mod operation is delete
    """
    return (command == ofp.OFPFC_DELETE or 
            command == ofp.OFPFC_DELETE_STRICT)

def is_strict_cmd(command):
    """
    Return boolean indicating if this flow mod operation is delete
    """
    return (command == ofp.OFPFC_MODIFY_STRICT or 
            command == ofp.OFPFC_DELETE_STRICT)

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
            return False

    #@todo Does this 64 bit stuff work in Python?
    if (match_a.metadata_mask & match_a.metadata !=
        match_a.metadata_mask & match_b.metadata):
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
            return False
        idx += 1
    idx = 0
    for byte in match_a.dl_dst_mask:
        byte = ~byte
        if match_a.dl_dst[idx] & byte != match_b.dl_dst[idx] & byte:
            return False
        idx += 1
    mask = ~match_a.metadata_mask
    if match_a.metadata & mask != match_b.metadata & mask:
        return False

    # @todo  Check untagged logic
    if not (wildcards & ofp.OFPFW_DL_VLAN):
        if match_a.dl_vlan != match_b.dl_vlan:
            return False
    if not (wildcards & ofp.OFPFW_DL_VLAN_PCP):
        if match_a.dl_vlan_pcp != match_b.dl_vlan_pcp:
            return False
    if not (wildcards & ofp.OFPFW_DL_TYPE):
        if match_a.dl_type != match_b.dl_type:
            return False

    if not (wildcards & ofp.OFPFW_MPLS_LABEL):
        if match_a.mpls_label != match_b.mpls_label:
            return False
    if not (wildcards & ofp.OFPFW_MPLS_TC):
        if match_a.mpls_tc != match_b.mpls_tc:
            return False

def l3_match(match_a, match_b):
    """
    Check IP fields for match, not strict
    @params match_a Used for wildcards and masks
    @params match_b Other fields for match
    """

    wildcards = match_a.wildcards
    if not (wildcards & ofp.OFPFW_NW_TOS):
        if match_a.nw_tos != match_b.nw_tos:
            return False
    if not (wildcards & ofp.OFPFW_NW_PROTO):
        if match_a.nw_proto != match_b.nw_proto:
            return False
        #@todo COMPLETE THIS
    mask = ~match_a.nw_src_mask
    if match_a.nw_src & mask != match_b.nw_src & mask:
        return False
    mask = ~match_a.nw_dst_mask
    if match_a.nw_dst & mask != match_b.nw_dst & mask:
        return False

    return True

def flow_match_strict(flow_a, flow_b):
    """
    Check if flows match strictly
    @param flow_a Primary key for cookie mask, etc
    @param flow_b Other key to match
    """
    wildcards_a = flow_a.match.wildcards
    wildcards_b = flow_b.match.wildcards
    if (wildcards_a != wildcards_b):
        return False
    if (flow_a.priority != flow_b.priority):
        return False
    if (flow_a.cookie_mask & flow_a.cookie != 
        flow_a.cookie & flow_b.cookie):
        return False
    if is_delete_cmd(flow_a.command):
        if (flow_a.out_port != ofp.OFPP_ANY):
            if (flow_a.out_port != flow_b.out_port):
                return False
        if (flow_a.out_group != ofp.OFPG_ANY):
            if (flow_a.out_group != flow_b.out_group):
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

    def match_flow_mod(self, new_flow):
        """
        Return boolean indicating whether new_flow matches this flow
        This is used for add/modify/delete operations
        @param new_flow The flow_mod object to match.
        """
        if (new_flow.flags & ofp.OFPFF_CHECK_OVERLAP):
            print("Check overlap set but not implemented")
            #@todo implement

        if is_strict_cmd(new_flow.command):
            return flow_match_strict(new_flow, self.flow_mod)
        
        # This just looks like a packet match from here.
        if not meta_match(new_flow.match, self.flow_mod.match):
            return False
        if not l2_match(new_flow.match, self.flow_mod.match):
            return False
        if new_flow.match.dl_type == 0x800:
            if not l3_match(new_flow.match, self.flow_mod.match):
                return False

        return True

    def match_port(self, port):
        """
        Takes an integer as parameter and returns true if any of the actions in this flow
        go to the corresponding port
        
        @todo Currently only looks for action_output == port ; needs to recurse on group tables etc.
        """
        if port == ofp.OFPP_ANY:    # shortcut a response if they want any port
            #@todo figure out of this should include OFPP_ALL (not clear) 
            return True
        for instr in self.flow_mod.instructions:
            if instr.isinstance(ofp.ofp_action_set_output_port):
                return instr.port == port
            if instr.isinstance(ofp.ofp_action_group):
                raise "UNSUPPORTED::  FIXME!!!"

    def match_cookie(self,cookie):
        """
        Takes a openflow cookie (as in flow_mod.cookie) as parameter and returns true if
        this flow entry matches that cookie
        
        cookie == 0 implies match all cookies
        """
        #@todo Think about implementing Dave Erikson's flexible cookie matching here
        if cookie == 0 or cookie == self.flow_mod.cookie:
            return True
        else: 
            return False
        
    def match_packet(self, packet):
        """
        Return boolean indicating packet matches this flow entry
        Updates flow's counters if match occurs
        @param packet The packet object to match.  Assumes parse is up to date
        """

        if not meta_match(self.flow_mod.match, packet.match):
            return False
        if not l2_match(self.flow_mod.match, packet.match):
            return False
        if not l3_match(self.flow_mod.match, packet.match):
            return False

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
        """
        stat = message.flow_stats_request
        stat.duration_sec = self.duration_sec
        stat.duration_nsec = self.duration_nsec
        stat.priority = self.priority
        stat.idle_timeout = self.idle_timeout
        stat.hard_timeout = self.hard_timeout
        stat.cookie = self.flow_mod.cookie
        stat.packet_count = self.packet_count
        stat.byte_count = self.byte_count
        stat.match = self.flow_mod.match
        stat.instructions = self.flow_mod.instructions
        return stat 
