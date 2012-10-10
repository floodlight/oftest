"""
Prototype test cases related to operation under load

It is recommended that these definitions be kept in their own
namespace as different groups of tests will likely define 
similar identifiers.

The switch is actively attempting to contact the controller at the address
indicated in config.

In general these test cases make some assumption about the external
configuration of the switch under test.  For now, the assumption is
that the first two OF ports are connected by a loopback cable.
"""

import copy

import logging

import unittest

from oftest import config
import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action
import oftest.parse as parse
import oftest.base_tests as base_tests
import time

from oftest.testutils import *

class LoadBarrier(base_tests.SimpleProtocol):
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
        lb_port = test_param_get('lb_port', default=1)
        barrier_count = test_param_get('barrier_count', 
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

class PacketInLoad(base_tests.SimpleDataPlane):
    """
    Generate lots of packet-in messages

    Test packet-in function by sending lots of packets to the dataplane.
    This test tracks the number of pkt-ins received but does not enforce
    any requirements about the number received.
    """
    def runTest(self):
        # Construct packet to send to dataplane
        # Send packet to dataplane, once to each port
        # Poll controller with expect message type packet in

        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
        out_count = 0
        in_count = 0

        of_ports = config["port_map"].keys()
        for of_port in of_ports:
            for pkt, pt in [
               (simple_tcp_packet(), "simple TCP packet"),
               (simple_tcp_packet(dl_vlan_enable=True,pktlen=108), 
                "simple tagged TCP packet"),
               (simple_eth_packet(), "simple Ethernet packet"),
               (simple_eth_packet(pktlen=40), "tiny Ethernet packet")]:

               logging.info("PKT IN test with %s, port %s" % (pt, of_port))
               for count in range(100):
                   out_count += 1
                   self.dataplane.send(of_port, str(pkt))
        time.sleep(2)
        while True:
            (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,
                                                   timeout=0)
            if not response:
                break
            in_count += 1
        logging.info("PacketInLoad Sent %d. Got %d." % (out_count, in_count))
        


class PacketOutLoad(base_tests.SimpleDataPlane):
    """
    Generate lots of packet-out messages

    Test packet-out function by sending lots of packet-out msgs
    to the switch.  This test tracks the number of packets received in 
    the dataplane, but does not enforce any requirements about the 
    number received.
    """
    def runTest(self):
        # Construct packet to send to dataplane
        # Send packet to dataplane
        # Poll controller with expect message type packet in

        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # These will get put into function
        of_ports = config["port_map"].keys()
        of_ports.sort()
        out_count = 0
        in_count = 0
        xid = 100
        for dp_port in of_ports:
            for outpkt, opt in [
               (simple_tcp_packet(), "simple TCP packet"),
               (simple_eth_packet(), "simple Ethernet packet"),
               (simple_eth_packet(pktlen=40), "tiny Ethernet packet")]:

               logging.info("PKT OUT test with %s, port %s" % (opt, dp_port))
               msg = message.packet_out()
               msg.data = str(outpkt)
               act = action.action_output()
               act.port = dp_port
               self.assertTrue(msg.actions.add(act), 'Could not add action to msg')

               logging.info("PacketOutLoad to: " + str(dp_port))
               for count in range(100):
                   msg.xid = xid
                   xid += 1
                   rv = self.controller.message_send(msg)
                   self.assertTrue(rv == 0, "Error sending out message")
                   out_count += 1

               exp_pkt_arg = None
               exp_port = None
        time.sleep(2)
        while True:
            (of_port, pkt, pkt_time) = self.dataplane.poll(timeout=0)
            if pkt is None:
                break
            in_count += 1
        logging.info("PacketOutLoad Sent %d. Got %d." % (out_count, in_count))
