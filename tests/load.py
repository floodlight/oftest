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
import random
import logging
import unittest

from oftest import config
import oftest.controller as controller
import ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action
import oftest.parse as parse
import oftest.base_tests as base_tests
import time

from oftest.testutils import *

@nonstandard
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
        request.actions.add(act)

        act = action.action_output()
        act.port = ofp.OFPP_CONTROLLER
        request.actions.add(act)

        self.controller.message_send(request)
        do_barrier(self.controller)

        # Create packet out and send to port lb_port + 1
        msg = message.packet_out()
        msg.in_port = lb_port
        msg.data = str(pkt)
        act = action.action_output()
        act.port = lb_port + 1
        msg.actions.add(act)
        logging.info("Sleeping before starting storm")
        time.sleep(1) # Root causing issue with fast disconnects
        logging.info("Sending packet out to %d" % (lb_port + 1))
        self.controller.message_send(msg)

        for idx in range(0, barrier_count):
            do_barrier(self.controller)
            # To do:  Add some interesting functionality here
            logging.info("Barrier %d completed" % idx)

        # Clear the flow table when done
        logging.debug("Deleting all flows from switch")
        delete_all_flows(self.controller)

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

        delete_all_flows(self.controller)
        do_barrier(self.controller)
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
        while True:
            (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN)
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

        delete_all_flows(self.controller)

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
               msg.in_port = ofp.OFPP_NONE
               msg.data = str(outpkt)
               act = action.action_output()
               act.port = dp_port
               msg.actions.add(act)

               logging.info("PacketOutLoad to: " + str(dp_port))
               for count in range(100):
                   msg.xid = xid
                   xid += 1
                   self.controller.message_send(msg)
                   out_count += 1

               exp_pkt_arg = None
               exp_port = None
        while True:
            (of_port, pkt, pkt_time) = self.dataplane.poll()
            if pkt is None:
                break
            in_count += 1
        logging.info("PacketOutLoad Sent %d. Got %d." % (out_count, in_count))

class FlowModLoad(base_tests.SimpleProtocol):

    def checkBarrier(self):
        msg, pkt = self.controller.transact(message.barrier_request(), timeout=60)
        self.assertNotEqual(msg, None, "Barrier failed")
        while self.controller.packets:
           msg = self.controller.packets.pop(0)[0]
           self.assertNotEqual(msg.header.type, message.OFPT_ERROR,
                               "Error received")

    def runTest(self):
        msg, pkt = self.controller.transact(message.table_stats_request())

        # Some switches report an extremely high max_entries that would cause
        # us to run out of memory attempting to create all the flow-mods.
        num_flows = min(msg.stats[0].max_entries, 32678)

        logging.info("Creating %d flow-mods messages", num_flows)

        requests = []
        for i in range(num_flows):
            match = ofp.ofp_match()
            match.wildcards = ofp.OFPFW_ALL & ~ofp.OFPFW_DL_VLAN & ~ofp.OFPFW_DL_DST
            match.dl_vlan = ofp.OFP_VLAN_NONE
            match.dl_dst = [0, 1, 2, 3, i / 256, i % 256]
            act = action.action_output()
            act.port = ofp.OFPP_CONTROLLER
            request = message.flow_mod()
            request.command = ofp.OFPFC_ADD
            request.buffer_id = 0xffffffff
            request.priority = num_flows - i
            request.out_port = ofp.OFPP_NONE
            request.match = match
            request.actions.add(act)
            requests.append(request)

        for i in range(3):
            logging.info("Iteration %d: delete all flows" % i)
            delete_all_flows(self.controller)
            self.checkBarrier()

            logging.info("Iteration %d: add %s flows" % (i, num_flows))
            random.shuffle(requests)
            for request in requests:
               self.assertNotEqual(self.controller.message_send(request), -1,
                               "Error installing flow mod")
            self.checkBarrier()
