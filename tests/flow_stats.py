"""
Flow stats test case.
Similar to Flow stats test case in the perl test harness.

"""

import logging

import unittest
import random

import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action
import oftest.parse as parse
import basic

from testutils import *
from time import sleep

#@var port_map Local copy of the configuration map from OF port
# numbers to OS interfaces
pa_port_map = None
#@var pa_logger Local logger object
pa_logger = None
#@var pa_config Local copy of global configuration data
pa_config = None

def test_set_init(config):
    """
    Set up function for packet action test classes

    @param config The configuration dictionary; see oft
    """

    global pa_port_map
    global pa_logger
    global pa_config

    pa_logger = logging.getLogger("pkt_act")
    pa_logger.info("Initializing test set")
    pa_port_map = config["port_map"]
    pa_config = config

class FlowStats(basic.SimpleDataPlane):
    """
    Verify flow stats are properly retrieved.

    Generate a packet
    Generate and install a matching flow with idle timeout = 1 sec
    Verify the flow expiration message is received
    """
    def runTest(self):
        global pa_port_map

        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        rc = delete_all_flows(self.controller, pa_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        ingress_port = of_ports[0];
        egress_port = of_ports[1];
        pa_logger.info("Ingress " + str(ingress_port) + 
                       " to egress " + str(egress_port))
        
        match.in_port = ingress_port
        
        flow_mod_msg = message.flow_mod()
        flow_mod_msg.match = match
        flow_mod_msg.cookie = random.randint(0,9007199254740992)
        flow_mod_msg.buffer_id = 0xffffffff
        flow_mod_msg.idle_timeout = 1
        act.port = egress_port
        self.assertTrue(flow_mod_msg.actions.add(act), "Could not add action")
        
        stat_req = message.flow_stats_request()
        stat_req.match = match
        stat_req.table_id = 0xff
        stat_req.out_port = ofp.OFPP_NONE;

        do_barrier(self.controller)
        pa_logger.info("Sending stats request")
        rv = self.controller.message_send(stat_req)
        self.assertTrue(rv != -1, "Error sending flow stat req")
        do_barrier(self.controller)

        (response, raw) = self.controller.poll(ofp.OFPT_STATS_REPLY, 2)
        
        pa_logger.info("Inserting flow")
        rv = self.controller.message_send(flow_mod_msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        do_barrier(self.controller)

        pa_logger.info("Sending packet to dp port " + 
                       str(ingress_port))
        self.dataplane.send(ingress_port, str(pkt))
        (rcv_port, rcv_pkt, pkt_time) = self.dataplane.poll(timeout=2)
        self.assertTrue(rcv_pkt is not None, "Did not receive packet")
        pa_logger.debug("Packet len " + str(len(pkt)) + " in on " + 
                        str(rcv_port))
        self.assertEqual(rcv_port, egress_port, "Unexpected receive port")
        self.assertEqual(str(pkt), str(rcv_pkt),
                         'Response packet does not match send packet')
            
        pa_logger.info("Sending stats request")
        rv = self.controller.message_send(stat_req)
        self.assertTrue(rv != -1, "Error sending flow stat req")
        do_barrier(self.controller)

        (response, raw) = self.controller.poll(ofp.OFPT_STATS_REPLY, 2)
        #print "YYY: Stats reply is \n%s" % (response.show())
        self.assertTrue(len(response.stats) == 1, "Did not receive flow stats reply")
