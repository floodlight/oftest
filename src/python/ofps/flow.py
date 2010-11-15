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

class FlowEntry:
    """
    Structure to track a flow table entry
    """
    def __init__(self):
        self.flow_mod = message.flow_mod()
        self.last_hit = None
        self.packets = 0
        self.bytes = 0
        self.insert_time = None

    def flow_mod_set(flow_mod):
        self.flow_mod = copy.deepcopy(flow_mod)
        self.last_hit = None
        self.packets = 0
        self.bytes = 0
        self.insert_time = time.time()

    def _check_ip_fields(entry_fields, fields):
        if not (wc & ofp.OFPFW_NW_TOS):
            if entry_fields.nw_tos != fields.nw_tos:
                return False
        if not (wc & ofp.OFPFW_NW_PROTO):
            if entry_fields.nw_proto != fields.nw_proto:
                return False
        #@todo COMPLETE THIS
        mask = ~entry_fields.nw_src_mask
        if entry_fields.nw_src & mask != pkt_fields.nw_src & mask:
            return False
        mask = ~entry_fields.nw_dst_mask
        if entry_fields.nw_dst & mask != pkt_fields.nw_dst & mask:
            return False

        return True

    def is_match(self, pkt_fields, bytes, operation=None, flow_mod=None):
        """
        Return boolean indicating if this flow entry matches "match"
        which is generated from a packet.  If so, update counters unless
        match_only is true (indicating we're searching for a flow entry)
        Otherwise return None.
        @param pkt_fields An ofp_match structure to search for
        @param bytes to use if update required; 0 if no udpate required
        @param operation Check of add/delete strict matching; OFPFC_ value.
        @param flow_mod If not None, and bytes == 0, use for strict checks
        """
        # Initial lazy approach
        # Should probably generate list of identifiers from non-wildcards

        pkt_fields = packet.match

        # @todo Support "type" field for ofp_match
        entry_fields = self.flow_mod.match
        wc = entry_fields.wildcards
        if not (wc & ofp.OFPFW_IN_PORT):
            # @todo logical port match?
            if entry_fields.in_port != fields.in_port:
                return False

        # Addresses and metadata:  
        # @todo Check masks are negated correctly
        for byte in entry_fields.dl_src_mask:
            byte = ~byte
            if entry_fields.dl_src & byte != pkt_fields.dl_src & byte:
                return False
        for byte in entry_fields.dl_dst_mask:
            byte = ~byte
            if entry_fields.dl_dst & byte != pkt_fields.dl_dst & byte:
                return False
        mask = ~entry_fields.metadata_mask
        if entry_fields.metadata & mask != pkt_fields.metadata & mask:
            return False

        # @todo  Check untagged logic
        if not (wc & ofp.OFPFW_DL_VLAN):
            if entry_fields.dl_vlan != fields.dl_vlan:
                return False
        if not (wc & ofp.OFPFW_DL_VLAN_PCP):
            if entry_fields.dl_vlan_pcp != fields.dl_vlan_pcp:
                return False
        if not (wc & ofp.OFPFW_DL_TYPE):
            if entry_fields.dl_type != fields.dl_type:
                return False

        # @todo  Switch on DL type; handle ARP cases, etc
        if entry_fields.dl_type == 0x800:
            if not _check_ip_fields(entry_fields, fields):
                return False
        if not (wc & ofp.OFPFW_MPLS_LABEL):
            if entry_fields.mpls_label != fields.mpls_lablel:
                return False
        if not (wc & ofp.OFPFW_MPLS_TC):
            if entry_fields.mpls_tc != fields.mpls_tc:
                return False

        # Okay, if we get here, we have a match.
        if bytes != 0:  # Update counters
            self.last_hit = time.time()
            self.packets += 1
            self.bytes += bytes

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
