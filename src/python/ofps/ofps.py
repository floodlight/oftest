"""
OFPS:  OpenFlow Python Switch

This is a very simple implementation of an OpenFlow switch based on 
the structures generated for OpenFlow test.

To a large extent, we try to follow the openflow.h conventions;
one point of departure is an attempt to better isolate matching
structures, flow table entries with status and actions resulting
from a match.
"""

import oftest.cstruct as ofp
import oftest.dataplane as dataplane
import oftest.message as message
import oftest.action as action
from ctrl_if import *
import copy
from threading import Condition
from threading import Thread
from threading import Lock
from ofps_act import *
from ofps_pkt import Packet

class OFSwitchConfig:
    """
    Class to document normal configuration parameters
    """
    def __init__(self):
        self.controller_ip = None
        self.controller_port = None
        self.passive_listen_port = None
        self.port_map = {}
        self.env = {}  # Extensible array

def execute_actions(packet, actions, groups, dataplane, ctrl_if, 
                    output_now=False):
    """
    Execute the list of actions on the packet
    @param packet The ingress packet on which to execute the actions
    @param actions The list of actions to be applied to the packet
    @param groups The GroupTable object for the switch
    @param dataplane The DataPlane object for the switch
    @param ctrl_if The controller interface for the switch
    @param output_immediate If an set-output-port action is seen,
    execute it immediately and do not update the output-port metadata

    Actions are executed in whatever order they are passed without
    checking the integrity of this ordering.
    """
    for action in actions:
        exec_str = "do_" + action.__name__ + \
            "(packet, action, groups, dataplane, ctrl_if, output_now)"
        try:
            exec(exec_str)
        except:  #@todo: Add constraint
            #@todo Define logging module
            print("Could not execute " + str(action))

    if packet.output_port is not None:
        dataplane.send(packet.output_port, packet.data)
        pass
        
class OFSwitch(Thread):
    """
    Top level class for the ofps implementation
    Components:
       A set of dataplane ports in a DataPlane object
       A controller connection and ofp stack
       A flow table object
    The switch is responsible for:
       Plumbing the packets from the dataplane to the flow table
       Executing actions as specified by the output from the flow table
       Processing the controller messages
    The main thread processes dataplane packets and control packets
    """
    # @todo Support fail open/closed
    def __init__(self):
        """
        Constructor for base class
        """
        Thread.__init__(self)
        self.flow_table = FlowTable()
        self.ctrl_if = ctrl_if.ControllerInterface()
        self.dataplane = dataplane.DataPlane()
        self.config = OFSwitchConfig()
        

    def config_set(self, config):
        """
        Set the configuration for the switch.
        Contents:
            Controller IP address and port
            Fail open/closed
            Passive listener port
            Number of tables to support
        """
        self.config = config

    def dp_pkt_handler(self, port_number, data):
        """
        Packet handler registered with datapath
        Enqueue packets for main thread to process
        """
        pass

    def run(self):
        """
        Main execute function for running the switch
        """
        self.pipeline = FlowPipeline(n_tables=config.n_tables)
        for of_port, ifname in config.port_map.items():
            self.dataplane.port_add(ifname, of_port)
        self.dataplane.register(self.dp_pkt_handler)
        # Kick off the dataplane and add ports to it
        # Kick off the controller interface
        # Register to receive packets 

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
        
    def is_match(self, fields, bytes, match_only=False):
        """
        Return boolean indicating if this flow entry matches "match"
        which is generated from a packet.  If so, update counters unless
        match_only is true (indicating we're searching for a flow entry)
        Otherwise return None.
        @fields An ofp_match object typically generated from a packet
        @bytes Number of bytes in the packet for statistics
        @match_only If True, do not update state of flow, just return T/F.
        """
        # Initial lazy approach
        # Should probably generate list of identifiers from non-wildcards

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
        if not match_only:
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

def prio_sort(x, y):
    """
    Sort flow entries by priority
    """
    if x.flow_mod.priority > y.flow_mod.priority:
        return 1
    if x.flow_mod.priority < y.flow_mod.priority:
        return -1
    return 0
                
class FlowTable(Thread):
    def __init__(self, table_id=0):
        Thread.__init__(self)
        self.flow_entries = []
        self.table_id = table_id
        self.flow_sync = Condition()

    def expire(self):
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

    def flow_mod_add(self, flow_mod):
        self.flow_sync.acquire()
        for flow in self.flow_entries:
            if flow.flow_match(flow_mod, match_only=True):
                flow.update(flow_mod)
                self.flow_sync.release()
                return
        new_flow = FlowEntry()
        new_flow.flow_mod_set(flow_mod)
        # @todo Is there a sorted list insert operation?
        self.flow_entries.insert(new_flow)
        self.flow_entries.sort(prio_sort)
        self.flow_sync.release()
        # @todo Check for priority conflict?

    def match_packet(self, match, bytes):
        """
        Return a flow object if a match is found for the match structure
        @match Match structure derived from a packet
        @bytes The number of bytes in the packet for statistics
        """
        self.flow_sync.acquire()
        for flow in self.flow_entries:
            if flow.is_match(match, bytes):
                self.flow_sync.release()
                return flow
        self.flow_sync.release()
        return None

#@todo
DEFAULT_TABLE_COUNT=1

class FlowPipeline(Thread):
    """
    Class to implement a pipeline of flow tables
    The thread interface is to allow flow expiration operations
    """
    def __init__(self, n_tables=DEFAULT_TABLE_COUNT):
        """
        Constructor for base class
        """
        self.controller = None
        self.tables = []
        self.n_tables = n_tables
        # Instantiate table instances
        for idx in range(n_tables):
            self.tables.append(FlowTable(table_id=idx))

    def run(self):
        """
        Thread to run expiration checks
        """
        while 1:
            time.sleep(1)
            for idx in range(self.n_tables):
                expired_flows = self.tables[idx].expire
                for flow in expired_flows:
                    # @todo  Send flow expiration report
                    print "Need to expire " + str(flow)
                
    def controller_set(self, controller):
        """
        Set the controller connection object for transmits to controller
        For example, the flow table may generate flow expired messages
        """
        self.controller = controller

    def flow_mod_add(self, flow_mod):
        """
        Update the table according to the flow mod message 
        @param flow_mod The flow mod message to process
        """
        if flow_mod.table_id > self.n_tables:
            return -1
        return self.tables[flow_mod.table_id].flow_mod_add(flow_moe)

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

    def apply_pipeline(self, match, bytes):
        """
        Run the pipeline on the packet and execute any actions indicated
        """
        table_id = 0
        action_set = {}
        while 1:
            flow = self.tables[table_id].match_packet(match, bytes)
            if flow is not None:
                # Check instruction set and execute it updating action_set
                pass

        # Execute action set
        
class GroupTable:
    """
    Class to implement a group table object
    """
    def __init__(self):
        """
        Constructor for base class
        """
        self.groups = []

    def update(self, group_mod):
        """
        Execute the group_mod operation on the table
        """
        
    def group_stats_get(self, group_id):
        """
        Return an ofp_group_stats object for the group_id
        """
        return None

