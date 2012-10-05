"""
Prototype test cases related to operation under load

It is recommended that these definitions be kept in their own
namespace as different groups of tests will likely define 
similar identifiers.

  The function test_set_init is called with a complete configuration
dictionary prior to the invocation of any tests from this file.

  The switch is actively attempting to contact the controller at the address
indicated in oft_config

In general these test cases make some assumption about the external
configuration of the switch under test.  For now, the assumption is
that the first two OF ports are connected by a loopback cable.
"""

import copy

import logging

import unittest

import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action
import oftest.parse as parse
import basic
import time

from oftest.testutils import *

#@var load_port_map Local copy of the configuration map from OF port
# numbers to OS interfaces
load_port_map = None
#@var load_config Local copy of global configuration data
load_config = None


def test_set_init(config):
    """
    Set up function for packet action test classes

    @param config The configuration dictionary; see oft
    """

    global load_port_map
    global load_config

    load_port_map = config["port_map"]
    load_config = config

class LoadBarrier(basic.SimpleProtocol):
    """
    Test barrier under load with loopback

    This test assumes there is a pair of ports on the switch with
    a loopback cable connected and that spanning tree is disabled.
    A flow is installed to cause a storm of packet-in messages
    when a packet is sent to the loopbacked interface.  After causing 
    this storm, a barrier request is sent.

    The test succeeds if the barrier response is received.  Otherwise
    the test fails.
    """

    priority = -1

    def runTest(self):
        # Set up flow to send from port 1 to port 2 and copy to CPU
        # Test parameter gives LB port base (assumes consecutive)
        lb_port = test_param_get(self.config, 'lb_port', default=1)
        barrier_count = test_param_get(self.config, 'barrier_count', 
                                       default=10)

        # Set controller to filter packet ins
        self.controller.filter_packet_in = True
        self.controller.pkt_in_filter_limit = 10

        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        match.in_port = lb_port
        act = action.action_output()
        act.port = lb_port + 1

        request = message.flow_mod()
        request.match = match
        request.hard_timeout = 2 * barrier_count

        request.buffer_id = 0xffffffff
        self.assertTrue(request.actions.add(act), "Could not add action")

        act = action.action_output()
        act.port = ofp.OFPP_CONTROLLER
        self.assertTrue(request.actions.add(act), "Could not add action")

        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        # Create packet out and send to port lb_port + 1
        msg = message.packet_out()
        msg.data = str(pkt)
        act = action.action_output()
        act.port = lb_port + 1
        self.assertTrue(msg.actions.add(act), 'Could not add action to msg')
        logging.info("Sleeping before starting storm")
        time.sleep(1) # Root causing issue with fast disconnects
        logging.info("Sending packet out to %d" % (lb_port + 1))
        rv = self.controller.message_send(msg)
        self.assertTrue(rv == 0, "Error sending out message")

        for idx in range(0, barrier_count):
            self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
            # To do:  Add some interesting functionality here
            logging.info("Barrier %d completed" % idx)

        # Clear the flow table when done
        logging.debug("Deleting all flows from switch")
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")
