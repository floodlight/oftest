'''
Created on Jan 27, 2011

@author: capveg
'''

import logging

import basic
import testutils
from oftest import cstruct as ofp

def test_set_init(config):
    """
    Set up function for flow_mods test classes

    @param config The configuration dictionary; see oft
    """

    global flow_mods_port_map
    global flow_mods_logger
    global flow_mods_config

    flow_mods_logger = logging.getLogger("flow_mods")
    flow_mods_logger.info("Initializing test set")
    flow_mods_port_map = config["port_map"]
    flow_mods_config = config
    
class FlowMod_ModifyStrict(basic.SimpleProtocol):
    """ Simple FlowMod Modify test
    delete all flows in the table
    insert an exact match flow_mod sending to port[1]
    then swap the output action from port[1] to port[2]
    then get flow_stats
    assert that the new actions are in place
    """
    def runTest(self):
        ing_port = flow_mods_port_map.keys()[0]
        out_port1 = flow_mods_port_map.keys()[1]
        out_port2 = flow_mods_port_map.keys()[2]
        pkt = testutils.simple_tcp_packet()
        testutils.delete_all_flows(self.controller, self.logger)
        fm_orig = testutils.flow_msg_create(self, pkt, 
                                            ing_port=ing_port, 
                                            egr_port=out_port1)
        fm_new = testutils.flow_msg_create(self, pkt, 
                                            ing_port=ing_port, 
                                            egr_port=out_port2)
        fm_new.command = ofp.OFPFC_MODIFY_STRICT
        rv = self.controller.message_send(fm_orig)
        self.assertEqual(rv, 0, "Failed to insert 1st flow_mod")
        testutils.do_barrier(self.controller)
        rv = self.controller.message_send(fm_new)
        testutils.do_barrier(self.controller)
        self.assertEqual(rv, 0, "Failed to insert 2nd flow_mod")
        flow_stats = testutils.flow_stats_get(self)
        self.assertEqual(len(flow_stats.stats),1, 
                         "Expected only one flow_mod")
        stat = flow_stats.stats[0]
        self.assertEqual(stat.match, fm_new.match)
        self.assertEqual(stat.instructions, fm_new.instructions)
        # @todo consider adding more tests here
        

if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test_spec=flow_mods"
