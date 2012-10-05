"""
Flow expire test case.
Similar to Flow expire test case in the perl test harness.

"""

import logging

import unittest
import random

from oftest import config
import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action
import oftest.parse as parse
import basic

from oftest.testutils import *
from time import sleep

class FlowExpire(basic.SimpleDataPlane):
    """
    Verify flow expire messages are properly generated.

    Generate a packet
    Generate and install a matching flow with idle timeout = 1 sec
    Verify the flow expiration message is received
    """
    def runTest(self):
        # TODO: set from command-line parameter
        test_timeout = 60

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        ingress_port = of_ports[0]
        egress_port  = of_ports[1]
        logging.info("Ingress " + str(ingress_port) + 
                       " to egress " + str(egress_port))
        
        match.in_port = ingress_port
        
        request = message.flow_mod()
        request.match = match
        request.cookie = random.randint(0,9007199254740992)
        request.buffer_id = 0xffffffff
        request.idle_timeout = 1
        request.flags |= ofp.OFPFF_SEND_FLOW_REM
        act.port = egress_port
        self.assertTrue(request.actions.add(act), "Could not add action")
        
        logging.info("Inserting flow")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_FLOW_REMOVED,
                                               timeout=test_timeout)

        self.assertTrue(response is not None, 
                        'Did not receive flow removed message ')

        self.assertEqual(request.cookie, response.cookie,
                         'Cookies do not match')

        self.assertEqual(ofp.OFPRR_IDLE_TIMEOUT, response.reason,
                         'Flow table entry removal reason is not idle_timeout')

        self.assertEqual(match, response.match,
                         'Flow table entry does not match')
        
