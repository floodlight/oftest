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
        if action.__class__ == action.set_output:
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
            flow_logger.debug("Failed in port (%d, %d)" %
                              (match_a.in_port, match_b.in_port))
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
    # @todo Check masks are negated correctly
    idx = 0
    for byte in match_a.dl_src_mask:
        byte = ~byte
        if match_a.dl_src[idx] & byte != match_b.dl_src[idx] & byte:
            flow_logger.debug("Failed dl_src byte %d: %x vs %x" %
                              (idx, match_a.dl_src[idx], match_b.dl_src[idx]))
            return False
        idx += 1
    idx = 0
    for byte in match_a.dl_dst_mask:
        byte = ~byte
        if match_a.dl_dst[idx] & byte != match_b.dl_dst[idx] & byte:
            flow_logger.debug("Failed dl_dst byte %d: %x vs %x" %
                              (idx, match_a.dl_dst[idx], match_b.dl_dst[idx]))
            return False
        idx += 1
    mask = ~match_a.metadata_mask
    if match_a.metadata & mask != match_b.metadata & mask:
        flow_logger.debug("Failed L2 metadata " + str(match_a.metadata) +
                          " vs " + str(match_b.metadata))
        return False

    if not (wildcards & ofp.OFPFW_DL_VLAN):
        if match_a.dl_vlan == ofp.OFPVID_ANY:
            if match_b.dl_vlan == ofp.OFPVID_NONE:
                flow_logger.debug("Failed dl_vlan: ANY vs NONE")
                return False
        elif match_b.dl_vlan == ofp.OFPVID_ANY:
            if match_a.dl_vlan == ofp.OFPVID_NONE:
                flow_logger.debug("Failed dl_vlan: NONE vs ANY")
                return False
        elif match_a.dl_vlan != match_b.dl_vlan:
            flow_logger.debug("Failed dl_vlan: %d vs %d" % 
                              (match_a.dl_vlan, match_b.dl_vlan))
            return False
        # @note check pcp only if there is a vlan tag 
        if not (wildcards & ofp.OFPFW_DL_VLAN_PCP):
            if match_a.dl_vlan_pcp != match_b.dl_vlan_pcp:
                flow_logger.debug("Failed dl_vlan_pcp: %d vs %d" %
                                  (match_a.dl_vlan_pcp, match_b.dl_vlan_pcp))
                return False
            
    if not (wildcards & ofp.OFPFW_DL_TYPE):
        if match_a.dl_type != match_b.dl_type:
            flow_logger.debug("Failed dl_type: %d vs %d" % 
                              (match_a.dl_type, match_b.dl_type))
            return False
        
        # MPLS only evaluated if type is not wild and is one of the MPLS types.
        if (match_a.dl_type in (0x8847, 0x8848)):
            if not (wildcards & ofp.OFPFW_MPLS_LABEL):
                if match_a.mpls_label != match_b.mpls_label:
                    flow_logger.debug("Failed mpls_label: %d vs %d" % 
                                      (match_a.mpls_label, match_b.mpls_label))
                    return False
            
            if not (wildcards & ofp.OFPFW_MPLS_TC):
                if match_a.mpls_tc != match_b.mpls_tc:
                    flow_logger.debug("Failed mpls_tc: %d vs %d" % 
                                      (match_a.mpls_tc, match_b.mpls_tc))
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
            flow_logger.debug("Failed nw_tos: %d vs %d" % 
                              (match_a.nw_tos, match_b.nw_tos))
            return False
    if not (wildcards & ofp.OFPFW_NW_PROTO):
        if match_a.nw_proto != match_b.nw_proto:
            flow_logger.debug("Failed nw_proto: %d vs %d" % 
                              (match_a.nw_proto, match_b.nw_proto))
            return False
    mask = ~match_a.nw_src_mask
    if match_a.nw_src & mask != match_b.nw_src & mask:
        flow_logger.debug("Failed nw_src: 0x%x vs 0x%x" % 
                          (match_a.nw_src & mask, match_b.nw_src & mask))
        return False
    mask = ~match_a.nw_dst_mask
    if match_a.nw_dst & mask != match_b.nw_dst & mask:
        flow_logger.debug("Failed nw_dst: %x vs %x" % 
                          (match_a.nw_dst & mask, match_b.nw_dst & mask))
        return False

    if not (wildcards & ofp.OFPFW_TP_SRC):
        if match_a.tp_src != match_b.tp_src:
            flow_logger.debug("Failed tp_src: %d vs %d" % 
                              (match_a.tp_src, match_b.tp_src))
            return False
    if not (wildcards & ofp.OFPFW_TP_DST):
        if match_a.tp_dst != match_b.tp_dst:
            flow_logger.debug("Failed tp_dst: %d vs %d" % 
                              (match_a.tp_dst, match_b.tp_dst))
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
        flow_logger.debug("Failed wildcards: %x vs %x" % 
                          (wildcards_a, wildcards_b))
        return False
    if (flow_a.priority != flow_b.priority):
        flow_logger.debug("Failed priority: %d vs %d" % 
        (flow_a.priority, flow_b.priority))
        return False
    if (flow_a.cookie_mask & flow_a.cookie != 
        flow_a.cookie_mask & flow_b.cookie):
        flow_logger.debug("Failed cookie: 0x%x vs 0x%x" % 
                          (flow_a.cookie, flow_b.cookie))
        return False
    if is_delete_cmd(flow_a.command):
        if (flow_a.out_port != ofp.OFPP_ANY):
            if not flow_has_out_port(flow_b, flow_a.out_port, groups):
                flow_logger.debug("Failed out_port" + str(flow_a.out_port))
                return False
        if (flow_a.out_group != ofp.OFPG_ANY):
            if not flow_has_out_group(flow_b, flow_a.out_group, groups):
                flow_logger.debug("Failed out_group" + str(flow_a.out_group))
                return False

    if not l2_match(flow_a.match, flow_b.match):
        return False

    # @todo  Switch on DL type; handle ARP cases, etc
    # L3 only evaluated if DL_TYPE is not wild and equal to 0x800.
    if (not (wildcards_a & ofp.OFPFW_DL_TYPE)) and (flow_a.match.dl_type == 0x800):
        if not l3_match(flow_a.match, flow_b.match):
            return False
    else:
        flow_logger.debug("Not an L3 packet")

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
        self.packets = 0
        self.bytes = 0
        self.insert_time = time.time()
        self.last_hit = time.time() # important for idle expiration

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

        # Uncomment these for dump of matches being checked
        # flow_logger.debug("Matching:\n" + packet.match.show())
        # flow_logger.debug("Me:\n" + self.flow_mod.match.show())
        if not meta_match(self.flow_mod.match, packet.match):
            flow_logger.debug("packet match failed meta_match")
            return False
        if (self.flow_mod.match.dl_vlan == ofp.OFPVID_NONE and 
                (self.flow_mod.match.wildcards & ofp.OFPFMF_DL_VLAN) == 0):
            self.flow_mod.match.dl_vlan_pcp = 9
#        if ((self.flow_mod.match.dl_vlan == ofp.OFPVID_ANY) and
#            (packet.match.dl_vlan != ofp.OFPVID_NONE)):
#                self.flow_mod.match.dl_vlan_pcp = 0
#                packet.match.dl_vlan = ofp.OFPVID_ANY
#                packet.match.dl_vlan_pcp = 0
        if not l2_match(self.flow_mod.match, packet.match):
            flow_logger.debug("packet match failed l2_match")
            return False
        if self.flow_mod.match.dl_type == 0x800:
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
        ret = None
        h_delta = 999999
        i_delta = 999999
        if self.flow_mod.hard_timeout and self.insert_time:
            h_delta = now - self.insert_time
            if h_delta > self.flow_mod.hard_timeout:
                ret = ofp.OFPRR_HARD_TIMEOUT
        if self.flow_mod.idle_timeout and self.last_hit:
            i_delta = now - self.last_hit
            if i_delta > self.flow_mod.idle_timeout:
                ret = ofp.OFPRR_IDLE_TIMEOUT
#        str = "-------- FLOWEXP: ht=%f it=%f h=%f i=%f" % (
#                     h_delta,
#                     i_delta, 
#                     self.flow_mod.hard_timeout, 
#                     self.flow_mod.idle_timeout,
#                     )
#        if ret is not None:
#            str += " dec=%d" % ret
#        else: 
#            str += " dec=LATER"
#        flow_logger.error(str)
        return ret
    
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
