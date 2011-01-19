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
import time

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
        self.lookup_count = 0
        self.matched_count = 0
        # by default, when a packet does not match the table
        # is send to controller -- OpenFlow Spec, A.3.3
        self.miss_policy = ofp.OFPTC_TABLE_MISS_CONTROLLER

    def expire(self):
        """
        Run the expiration process on this table
        Run through all flows in the table and call the expire
        method.  Build a list of expired flows.
        @return A list of flow_removed messages, ready to send to controller
        """
        msgs = []
        # @todo May be a better approach than sync'ing
        self.flow_sync.acquire()
        delete_list = []
        for flow in self.flow_entries:
            timeout = flow.expire()
            if timeout is not None: # timeout == one of None, OFPRR_IDLE_TIMEOUT, or OFPRR_HARD_TIMEOUT
                delete_list.append(flow)
                if flow.flow_mod.flags & ofp.OFPFF_SEND_FLOW_REM:
                    msg = message.flow_removed()
                    msg.cookie = flow.flow_mod.cookie
                    msg.priority = flow.flow_mod.priority
                    msg.reason = timeout
                    msg.table_id = self.table_id
                    if flow.insert_time:
                        duration = time.time() - flow.insert_time
                    else:
                        duration = 0
                    msg.duration_sec = int(duration)
                    msg.duration_nsec = (duration-msg.duration_sec) * 10e9
                    msg.idle_timeout = flow.flow_mod.idle_timeout
                    msg.packet_count = flow.packets
                    msg.byte_count = flow.bytes
                    msg.match = flow.flow_mod.match
                    msgs.append(msg)
        for flow in delete_list:
            self.flow_entries.remove(flow)
        self.flow_sync.release()
        return msgs

    def flow_mod_process(self, flow_mod, groups):
        """
        Update the flow table according to the operation
        @param operation add/mod/delete operation (OFPFC_ value)
        @param flow_mod
        """
        # @todo Need to check overlap flags
        if (flow_mod.command == ofp.OFPFC_ADD):
            return self._flow_mod_process_add(flow_mod, groups)
        elif (flow_mod.command == ofp.OFPFC_MODIFY or 
              flow_mod.command == ofp.OFPFC_MODIFY_STRICT):
            return self._flow_mod_process_modify(flow_mod, groups)
        elif (flow_mod.command == ofp.OFPFC_DELETE or 
              flow_mod.command == ofp.OFPFC_DELETE_STRICT):
            return self._flow_mod_process_delete(flow_mod, groups)
        else:
            return (-1, ofp.OFPFMFC_BAD_COMMAND)
    
    def _match(self,flow_mod, groups):
        """ Return the set of flows that match this flow_mod and group
        
        Strict vs. non-strict is done in the flow.match_flow_mod structure
        @param flow_mod: a valid flow_mod
        @param groups: the group table
        @param strict: whether or not we are doing strict matching
        @attention:  ASSUMES caller has the flow_sync lock!
        @return a list of flows that match the flow_mod
        """
        match_list = []    
        # @todo Verify this will iterate in sorted order by priority
        for flow in self.flow_entries:
            if flow.match_flow_mod(flow_mod, groups):
                self.logger.debug("flow_mod matched in table " + 
                                  str(self.table_id))
                match_list.append(flow)
        return match_list
    
    def _flow_mod_process_add(self, flow_mod, groups):
        ret = (0, None)
        self.flow_sync.acquire()
        match_list = self._match(flow_mod, groups)                
        if len(match_list) != 0 and \
                    (flow_mod.flags & ofp.OFPFF_CHECK_OVERLAP) != 0:
            self.logger.info("Not adding overlapping flow_mod %s" % 
                             flow_mod.show())
            ret= (-1, ofp.OFPFMFC_OVERLAP)
        else:
            new_flow = ofps_flow.FlowEntry()
            new_flow.flow_mod_set(flow_mod)
            # @todo Is there a sorted list insert operation?
            self.flow_entries.append(new_flow)
            self.flow_entries.sort(prio_sort)
            self.logger.debug(
                    "Installing flow into table %d: now has %d entries" % 
                                  (flow_mod.table_id, len(self.flow_entries))
                                  )
        self.flow_sync.release()
        return ret

    def _flow_mod_process_modify(self, flow_mod, groups):
        ret = (0, None)
        self.flow_sync.acquire()
        match_list = self._match(flow_mod, groups)
        if len(match_list) > 0 : 
            for flow in match_list:
                    self.logger.debug("Updating flow " + str(flow.cookie))
                    flow.update(flow_mod)
        else:
            ret = (-1, ofp.OFPFMFC_BAD_MATCH) 
        self.flow_sync.release()
        return ret

    def _flow_mod_process_delete(self, flow_mod, groups):
        ret = (0, None)
        del_count = 0
        self.flow_sync.acquire()
        # this is O(n^2) in the worst case b/c
        # list.remove() is O(n)
        #@todo add a test for common case, i.e., 
        #    if flow_mod.match == ALL, then self.flow_entries.clear()
        for flow in self._match(flow_mod, groups):
            self.flow_entries.remove(flow)
            del_count+=1
        if del_count == 0:
            ret = (-1, ofp.OFPFMFC_BAD_MATCH) 
        self.flow_sync.release()
        return ret

    def match_packet(self, packet):
        """
        Return a flow object if a match is found for the match structure
        @packet An OFPS packet structure, already parsed
        """
        found = None
        self.flow_sync.acquire()
        self.lookup_count += 1
        for flow in self.flow_entries:
            if flow.match_packet(packet):
                found = flow
                self.matched_count +=1
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
    
    def __len__(self):
        return len(self.flow_entries)
