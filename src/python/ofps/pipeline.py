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
from exec_actions import execute_actions
from exec_actions import packet_in_to_controller
import oftest.cstruct as ofp
import oftest.message as message 

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

    def flow_mod_process(self, flow_mod, groups):
        """
        Update the table according to the flow mod message 
        @param operation The flow operation add, mod delete
        @param flow_mod The flow mod message to process
        """
        if flow_mod.table_id >= self.n_tables:
            self.logger.debug("bad table id " + str(flow_mod.table_id))
            return (-1, ofp.OFPFMFC_BAD_TABLE_ID)

        return self.tables[flow_mod.table_id].flow_mod_process(flow_mod,
                                                               groups)


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

    def flow_stats_get(self, flow_stats_request, groups):
        """
        Return an ofp_flow_stats object based on the flow stats request
        """
        replies = []
        if flow_stats_request.table_id == 0xff:     # do they want all tables?
            for table in self.tables:
                replies += table.flow_stats_get(flow_stats_request, groups)
        else:
            if flow_stats_request.table_id < len(self.tables): # else specific table
                replies += self.tables[flow_stats_request.table_id].flow_stats_get(flow_stats_request,groups)
            else:
                #@todo find/create an error message library and replace this with it
                err = message.bad_request_error_msg()
                err.header.xid = flow_stats_request.header.xid
                err.data = flow_stats_request
                err.type = ofp.OFPET_BAD_REQUEST
                err.code = ofp.OFPBRC_BAD_TABLE_ID                
                return err
        reply = message.flow_stats_reply()
        reply.header.xid = flow_stats_request.header.xid
        reply.stats = replies
        return reply

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
                for inst in flow.instructions.instructions:
                    if inst.__class__ == instruction_goto_table:
                        table_id = inst.table_id
                        if table_id >= self.n_tables:
                            self.logger.error("Bad goto table %d" % table_id)
                            break
                    elif inst.__class__ == instruction_write_actions:
                        for action in inst.actions.actions:
                            packet.write_action(action)
                    elif inst.__class__ == instruction_apply_actions:
                        execute_actions(switch, packet, inst.actions)
                    elif inst.__class__ == instruction_experimenter:
                        self.logger.error("Got experimenter instruction")
                    elif inst.__class__ == instruction_write_metadata:
                        packet.set_metadata(inst.metadata, inst.metadata_mask)
                    elif inst.__class__ == instruction_clear_actions:
                        packet.clear_actions()
                    else:
                        self.logger.error("Bad instruction")
                        
                        
                self.logger.debug("Matched packet in table " + str(table_id))
                # FIXME
                break
            else:
                self.logger.debug("No match in table " + str(table_id))
                break
        if matched:
            execute_actions(switch, packet, action_set)

            # @todo This needs clarification.
            if packet.output_port is not None:
                switch.dataplane.send(packet.output_port, packet.data)
        else:
            #@todo for now, just forward to controller; this should be cfgable
            packet_in_to_controller(switch, packet)

