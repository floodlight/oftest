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
from flow import FlowEntry
from threading import Lock
import oftest.cstruct as ofp

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

    def flow_mod_process(self, flow_mod):
        """
        Update the flow table according to the operation
        @param operation add/mod/delete operation (OFPFC_ value)
        @param flow_mod
        """
        # First, generate a list of flows matching the flow mod
        

        # Then based on the operation, do things to those flows

        found = False
        # @todo Handle delete; differentiate mod and add
        self.flow_sync.acquire()
        for flow in self.flow_entries:
            if flow.match_flow_mod(flow_mod):
                self.logger.debug("Matched in table " + str(self.table_id))
                flow.update(flow_mod)
                found = True
                break
        if not found:
            if flow_mod.command == ofp.OFPFC_ADD:
                # @todo Do this for modify/strict too, right?
                new_flow = FlowEntry()
                new_flow.flow_mod_set(flow_mod)
                # @todo Is there a sorted list insert operation?
                self.flow_entries.append(new_flow)
                self.flow_entries.sort(prio_sort)

        #@todo Implement other flow mod operations
        elif flow_mod.command == ofp.OFPFC_MODIFY:
            self.logger.debug("flow mod modify")
        elif flow_mod.command == ofp.OFPFC_MODIFY_STRICT:
            self.logger.debug("flow mod modify strict")
        elif flow_mod.command == ofp.OFPFC_DELETE:
            self.logger.debug("flow mod delete")
        elif flow_mod.command == ofp.OFPFC_DELETE_STRICT:
            self.logger.debug("flow mod delete strict")

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
            if flow.is_match(packet.match, packet.bytes):
                found = flow
                break
        self.flow_sync.release()
        return found
