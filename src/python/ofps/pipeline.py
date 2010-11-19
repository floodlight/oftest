"""
The FlowPipeline class implementation

All files associated with the OpenFlow Python Switch (ofps) are made
available for public use and benefit with the expectation
that others will use, modify and enhance the Software and contribute
those enhancements back to the community. However, since we would
like to make the Software available for broadest use, with as few
restrictions as possible permission is hereby granted, free of
charge, to any person obtaining a copy of this Software to deal in
the Software under the copyrights without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import time
import logging
from flowtable import FlowTable
from threading import Thread
from ofps_act import execute_actions
from ofps_act import packet_in_to_controller

import oftest.message as ofp 

DEFAULT_TABLE_COUNT=1

class FlowPipeline(Thread):
    """
    Class to implement a pipeline of flow tables
    The thread interface is to allow flow expiration operations
    """
    def __init__(self, n_tables):
        """
        Constructor for base class
        """
        super(FlowPipeline, self).__init__()
        self.controller = None
        self.tables = []
        self.n_tables = n_tables
        self.active = True
        # Instantiate table instances
        for idx in range(n_tables):
            self.tables.append(FlowTable(table_id=idx))
        self.logger = logging.getLogger("pipeline")

    def run(self):
        """
        Thread to run expiration checks
        """
        self.logger.info("Pipeline started")
        while self.active:
            time.sleep(1)
            #self.logger.debug("Pipeline thread awake");
            if self.active:
                for idx in range(self.n_tables):
                    expired_flows = self.tables[idx].expire()
                    for flow in expired_flows:
                        # @todo  Send flow expiration report
                        self.logger.debug("Expire " + str(flow))
        self.logger.info("Exiting pipeline thread")

    def kill(self):
        self.active = False
                
    def controller_set(self, controller):
        """
        Set the controller connection object for transmits to controller
        For example, the flow table may generate flow expired messages
        """
        self.controller = controller

    def flow_mod(self, flow_mod):
        """
        Update the table according to the flow mod message 
        @param operation The flow operation add, mod delete
        @param flow_mod The flow mod message to process
        """
        if flow_mod.table_id >= self.n_tables:
            self.logger.debug("bad table id " + str(flow_mod.table_id))
            return (-1, OFPFMFC_BAD_TABLE_ID)
        if flow_mod.command == ofp.OFPFC_ADD:
            self.logger.debug("flow mod add")
            return self.tables[flow_mod.table_id].flow_mod_add(operation, 
                                                               flow_mod)
        elif flow_mod.command == ofp.OFPFC_MODIFY:
            self.logger.debug("flow mod modify")
        elif flow_mod.command == ofp.OFPFC_MODIFY_STRICT:
            self.logger.debug("flow mod modify strict")
        elif flow_mod.command == ofp.OFPFC_DELETE:
            self.logger.debug("flow mod delete")
        elif flow_mod.command == ofp.OFPFC_DELETE_STRICT:
            self.logger.debug("flow mod delete strict")


    def table_caps_get(self, table_id=0):
        """
        Return the capabilities supported by this implementation
        """
        return 0

    def n_tables_get(self):
        """
        Return the number of tables supported by this implementation
        """
        return self.n_tables

    def stats_get(self):
        """
        Return an ofp_table_stats object
        """
        return None

    def flow_stats_get(self, flow_stats_request):
        """
        Return an ofp_flow_stats object based on the flow stats request
        """
        return None

    def aggregate_stats_get(self, aggregate_stats_request):
        """
        Return an ofp_aggregate_stats_reply object based on the request
        """
        return None

    def apply_pipeline(self, switch, packet):
        """
        Run the pipeline on the packet and execute any actions indicated
        @param packet An OFPS packet object, already parsed
        """
        # Generate a match structure from the packet
        table_id = 0
        action_set = {}
        matched = False  # Did we get any match?
        while 1:
            flow = self.tables[table_id].match_packet(packet)
            if flow is not None:
                matched = True
                # Check instruction set and execute it updating action_set
                self.logger.debug("Matched packet in table " + str(table_id))
                # FIXME
                break
            else:
                self.logger.debug("No match in table " + str(table_id))
                break
        if matched:
            execute_actions(switch, packet, action_set)
        else:
            #@todo for now, just forward to controller; this should be cfgable
            packet_in_to_controller(switch, packet)

