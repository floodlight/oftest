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
The FlowTable class definition
"""

import logging
import flow as ofps_flow
from threading import Lock
import oftest.cstruct as ofp
import oftest.message as message

def prio_sort(entry_x, entry_y):
    """
    Sort flow entries x and y by priority
    return -1 if x.prio < y.prio, etc.
    """
    if entry_x.flow_mod.priority > entry_y.flow_mod.priority:
        return 1
    if entry_x.flow_mod.priority < entry_y.flow_mod.priority:
        return -1
    return 0
                
class FlowTable(object):
    """
    The flow table class
    """

    def __init__(self, table_id=0):
        self.flow_entries = []
        self.table_id = table_id
        self.flow_sync = Lock()
        self.logger = logging.getLogger("flowtable")

    def expire(self):
        """
        Run the expiration process on this table
        Run through all flows in the table and call the expire
        method.  Build a list of expired flows.
        @return The list of expired flows
        """
        expired_flows = []
        # @todo May be a better approach to syncing
        self.flow_sync.acquire()
        for flow in self.flow_entries:
            if flow.expire():
                # remove flow from self.flows
                # add flow to expired_flows
                self.flow_entries.remove(flow)
                expired_flows.append(flow)
        self.flow_sync.release()
        return expired_flows

    def flow_mod_process(self, flow_mod, groups):
        """
        Update the flow table according to the operation
        @param operation add/mod/delete operation (OFPFC_ value)
        @param flow_mod
        """
        # @todo Need to check overlap flags
        match_list = []
        self.flow_sync.acquire()

        # @todo Verify this will iterate in sorted order by priority
        for flow in self.flow_entries:
            if flow.match_flow_mod(flow_mod, groups):
                self.logger.debug("flow_mod matched in table " + 
                                  str(self.table_id))
                if flow_mod.command == ofp.OFPPR_ADD:
                    match_list.append(flow)

        if len(match_list) == 0:  # No match
            self.logger.debug("No match in table " + str(self.table_id))
            if ((flow_mod.command == ofp.OFPFC_ADD) or
                (flow_mod.command == ofp.OFPFC_MODIFY) or
                (flow_mod.command == ofp.OFPFC_MODIFY_STRICT)):
                self.logger.debug("Installing flow into table " + 
                                  str(flow_mod.cookie))
                # @todo Do this for modify/strict too, right?
                new_flow = ofps_flow.FlowEntry()
                new_flow.flow_mod_set(flow_mod)
                # @todo Is there a sorted list insert operation?
                self.flow_entries.append(new_flow)
                self.flow_entries.sort(prio_sort)
        elif flow_mod.command == ofp.OFPFC_ADD:
            new_flow = ofps_flow.FlowEntry()
            new_flow.flow_mod_set(flow_mod)
            self.flow_entries.append(new_flow)
            self.flow_entries.sort(prio_sort)


        for flow in match_list:
            #@todo Implement other flow mod operations
            if flow_mod.command in [ofp.OFPFC_MODIFY, 
                                    ofp.OFPFC_MODIFY_STRICT]:
                self.logger.debug("Updating flow " + str(flow.cookie))
                flow.update(flow_mod)
            elif flow_mod.command in [ofp.OFPFC_DELETE, 
                                      ofp.OFPFC_DELETE_STRICT]:
                # @todo Generate flow_removed message
                self.logger.debug("flow mod delete" + str(flow.cookie))

        self.flow_sync.release()
        # @todo Check for priority conflict?
        return (0, None)

    def match_packet(self, packet):
        """
        Return a flow object if a match is found for the match structure
        @packet An OFPS packet structure, already parsed
        """
        found = None
        self.flow_sync.acquire()
        for flow in self.flow_entries:
            if flow.match_packet(packet):
                found = flow
                break
        self.flow_sync.release()
        return found
    
    def flow_stats_get(self, flow_stats_request, groups):
        """ 
        Takes an OFMatch structure as parameter and returns a list of the flow_mods
        that match that structure (implicitly including their stats)
        
        Used by pipeline to collect stats on each flow table
        
        @todo Decide if we really need to lock the flow_table before processing
        """
        self.flow_sync.acquire()
        stats = []
        fake_flow_mod = message.flow_mod()
        fake_flow_mod.match = flow_stats_request.match
        #@todo decide if flow_stats are 'strict' or not; if yes, then uncomment next line
        #fake_flow_mod.flags = ofp.OFPFF_CHECK_OVERLAP
        for flow in self.flow_entries:
            # match the out_port
            if ofps_flow.flow_has_out_port(flow, 
                                           flow_stats_request.out_port, groups) and \
                    ofps_flow.flow_has_cookie(flow, 
                                              flow_stats_request.cookie) and \
                    flow.match_flow_mod(fake_flow_mod, groups):
                # found a valid match, now fill in the stats
                stat = flow.flow_stat_get()
                stat.table_id = self.table_id
                stats.append(stat)
        self.flow_sync.release()
        return stats
