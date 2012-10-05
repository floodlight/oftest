"""
Basic protocol and dataplane test cases

It is recommended that these definitions be kept in their own
namespace as different groups of tests will likely define 
similar identifiers.

Current Assumptions:

  The function test_set_init is called with a complete configuration
dictionary prior to the invocation of any tests from this file.

  The switch is actively attempting to contact the controller at the address
indicated oin oft_config

"""

import time
import sys
import logging

import unittest
import random

import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action

import oftest.illegal_message as illegal_message

from oftest.testutils import *

#@var basic_port_map Local copy of the configuration map from OF port
# numbers to OS interfaces
basic_port_map = None
#@var basic_config Local copy of global configuration data
basic_config = None

TEST_VID_DEFAULT = 2

def test_set_init(config):
    """
    Set up function for basic test classes

    @param config The configuration dictionary; see oft
    """

    global basic_port_map
    global basic_config

    basic_port_map = config["port_map"]
    basic_config = config

class SimpleProtocol(unittest.TestCase):
    """
    Root class for setting up the controller
    """

    priority = 1

    def setUp(self):
        self.config = basic_config
        logging.info("** START TEST CASE " + str(self))
        self.controller = controller.Controller(
            host=basic_config["controller_host"],
            port=basic_config["controller_port"])
        # clean_shutdown should be set to False to force quit app
        self.clean_shutdown = True
        self.controller.start()
        #@todo Add an option to wait for a pkt transaction to ensure version
        # compatibilty?
        self.controller.connect(timeout=20)

        # By default, respond to echo requests
        self.controller.keep_alive = True
        
        if not self.controller.active:
            raise Exception("Controller startup failed")
        if self.controller.switch_addr is None: 
            raise Exception("Controller startup failed (no switch addr)")
        logging.info("Connected " + str(self.controller.switch_addr))
        request = message.features_request()
        reply, pkt = self.controller.transact(request)
        self.assertTrue(reply is not None,
                        "Did not complete features_request for handshake")
        self.supported_actions = reply.actions
        logging.info("Supported actions: " + hex(self.supported_actions))

    def inheritSetup(self, parent):
        """
        Inherit the setup of a parent

        This allows running at test from within another test.  Do the
        following:

        sub_test = SomeTestClass()  # Create an instance of the test class
        sub_test.inheritSetup(self) # Inherit setup of parent
        sub_test.runTest()          # Run the test

        Normally, only the parent's setUp and tearDown are called and
        the state after the sub_test is run must be taken into account
        by subsequent operations.
        """
        self.config = parent.config
        logging.info("** Setup " + str(self) + " inheriting from "
                          + str(parent))
        self.controller = parent.controller
        self.supported_actions = parent.supported_actions
        
    def tearDown(self):
        logging.info("** END TEST CASE " + str(self))
        self.controller.shutdown()
        #@todo Review if join should be done on clean_shutdown
        if self.clean_shutdown:
            self.controller.join()

    def runTest(self):
        # Just a simple sanity check as illustration
        logging.info("Running simple proto test")
        self.assertTrue(self.controller.switch_socket is not None,
                        str(self) + 'No connection to switch')

    def assertTrue(self, cond, msg):
        if not cond:
            logging.error("** FAILED ASSERTION: " + msg)
        unittest.TestCase.assertTrue(self, cond, msg)

class SimpleDataPlane(SimpleProtocol):
    """
    Root class that sets up the controller and dataplane
    """
    def setUp(self):
        SimpleProtocol.setUp(self)
        self.dataplane = dataplane.DataPlane(self.config)
        for of_port, ifname in basic_port_map.items():
            self.dataplane.port_add(ifname, of_port)

    def inheritSetup(self, parent):
        """
        Inherit the setup of a parent

        See SimpleProtocol.inheritSetup
        """
        SimpleProtocol.inheritSetup(self, parent)
        self.dataplane = parent.dataplane

    def tearDown(self):
        logging.info("Teardown for simple dataplane test")
        SimpleProtocol.tearDown(self)
        if hasattr(self, 'dataplane'):
            self.dataplane.kill(join_threads=self.clean_shutdown)
        logging.info("Teardown done")

    def runTest(self):
        self.assertTrue(self.controller.switch_socket is not None,
                        str(self) + 'No connection to switch')
        # self.dataplane.show()
        # Would like an assert that checks the data plane

class DataPlaneOnly(unittest.TestCase):
    """
    Root class that sets up only the dataplane
    """

    priority = -1

    def setUp(self):
        self.clean_shutdown = True
        self.config = basic_config
        logging.info("** START DataPlaneOnly CASE " + str(self))
        self.dataplane = dataplane.DataPlane(self.config)
        for of_port, ifname in basic_port_map.items():
            self.dataplane.port_add(ifname, of_port)

    def tearDown(self):
        logging.info("Teardown for simple dataplane test")
        self.dataplane.kill(join_threads=self.clean_shutdown)
        logging.info("Teardown done")

    def runTest(self):
        logging.info("DataPlaneOnly")
        # self.dataplane.show()
        # Would like an assert that checks the data plane

class Echo(SimpleProtocol):
    """
    Test echo response with no data
    """
    def runTest(self):
        request = message.echo_request()
        response, pkt = self.controller.transact(request)
        self.assertTrue(response is not None,
                        "Did not get echo reply")
        self.assertEqual(response.header.type, ofp.OFPT_ECHO_REPLY,
                         'response is not echo_reply')
        self.assertEqual(request.header.xid, response.header.xid,
                         'response xid != request xid')
        self.assertEqual(len(response.data), 0, 'response data non-empty')

class EchoWithData(SimpleProtocol):
    """
    Test echo response with short string data
    """
    def runTest(self):
        request = message.echo_request()
        request.data = 'OpenFlow Will Rule The World'
        response, pkt = self.controller.transact(request)
        self.assertTrue(response is not None,
                        "Did not get echo reply (with data)")
        self.assertEqual(response.header.type, ofp.OFPT_ECHO_REPLY,
                         'response is not echo_reply')
        self.assertEqual(request.header.xid, response.header.xid,
                         'response xid != request xid')
        self.assertEqual(request.data, response.data,
                         'response data does not match request')

class PacketIn(SimpleDataPlane):
    """
    Test packet in function

    Send a packet to each dataplane port and verify that a packet
    in message is received from the controller for each
    """
    def runTest(self):
        # Construct packet to send to dataplane
        # Send packet to dataplane, once to each port
        # Poll controller with expect message type packet in

        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        vid = test_param_get(self.config, 'vid', default=TEST_VID_DEFAULT)

        for of_port in basic_port_map.keys():
            for pkt, pt in [
               (simple_tcp_packet(), "simple TCP packet"),
               (simple_tcp_packet(dl_vlan_enable=True,dl_vlan=vid,pktlen=108), 
                "simple tagged TCP packet"),
               (simple_eth_packet(), "simple Ethernet packet"),
               (simple_eth_packet(pktlen=40), "tiny Ethernet packet")]:

               logging.info("PKT IN test with %s, port %s" % (pt, of_port))
               self.dataplane.send(of_port, str(pkt))
               #@todo Check for unexpected messages?
               count = 0
               while True:
                   (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN)
                   if not response:  # Timeout
                       break
                   if dataplane.match_exp_pkt(pkt, response.data): # Got match
                       break
                   if not basic_config["relax"]:  # Only one attempt to match
                       break
                   count += 1
                   if count > 10:   # Too many tries
                       break

               self.assertTrue(response is not None, 
                               'Packet in message not received on port ' + 
                               str(of_port))
               if not dataplane.match_exp_pkt(pkt, response.data):
                   logging.debug("Sent %s" % format_packet(pkt))
                   logging.debug("Resp %s" % format_packet(response.data))
                   self.assertTrue(False,
                                   'Response packet does not match send packet' +
                                   ' for port ' + str(of_port))

class PacketInDefaultDrop(SimpleDataPlane):
    """
    Test packet in function

    Send a packet to each dataplane port and verify that a packet
    in message is received from the controller for each
    """

    priority = -1

    def runTest(self):
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        for of_port in basic_port_map.keys():
            pkt = simple_tcp_packet()
            self.dataplane.send(of_port, str(pkt))
            count = 0
            while True:
                (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN)
                if not response:  # Timeout
                    break
                if dataplane.match_exp_pkt(pkt, response.data): # Got match
                    break
                if not basic_config["relax"]:  # Only one attempt to match
                    break
                count += 1
                if count > 10:   # Too many tries
                    break

            self.assertTrue(response is None, 
                            'Packet in message received on port ' + 
                            str(of_port))

class PacketInBroadcastCheck(SimpleDataPlane):
    """
    Check if bcast pkts leak when no flows are present

    Clear the flow table
    Send in a broadcast pkt
    Look for the packet on other dataplane ports.
    """

    priority = -1

    def runTest(self):
        # Need at least two ports
        self.assertTrue(len(basic_port_map) > 1, "Too few ports for test")

        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        of_ports = basic_port_map.keys()
        d_port = of_ports[0]
        pkt = simple_eth_packet(dl_dst='ff:ff:ff:ff:ff:ff')

        logging.info("BCast Leak Test, send to port %s" % d_port)
        self.dataplane.send(d_port, str(pkt))

        (of_port, pkt_in, pkt_time) = self.dataplane.poll(exp_pkt=pkt)
        self.assertTrue(pkt_in is None,
                        'BCast packet received on port ' + str(of_port))

class PacketOut(SimpleDataPlane):
    """
    Test packet out function

    Send packet out message to controller for each dataplane port and
    verify the packet appears on the appropriate dataplane port
    """
    def runTest(self):
        # Construct packet to send to dataplane
        # Send packet to dataplane
        # Poll controller with expect message type packet in

        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # These will get put into function
        of_ports = basic_port_map.keys()
        of_ports.sort()
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

               logging.info("PacketOut to: " + str(dp_port))
               rv = self.controller.message_send(msg)
               self.assertTrue(rv == 0, "Error sending out message")

               exp_pkt_arg = None
               exp_port = None
               if basic_config["relax"]:
                   exp_pkt_arg = outpkt
                   exp_port = dp_port
               (of_port, pkt, pkt_time) = self.dataplane.poll(port_number=exp_port,
                                                              exp_pkt=exp_pkt_arg)

               self.assertTrue(pkt is not None, 'Packet not received')
               logging.info("PacketOut: got pkt from " + str(of_port))
               if of_port is not None:
                   self.assertEqual(of_port, dp_port, "Unexpected receive port")
               if not dataplane.match_exp_pkt(outpkt, pkt):
                   logging.debug("Sent %s" % format_packet(outpkt))
                   logging.debug("Resp %s" % format_packet(
                           str(pkt)[:len(str(outpkt))]))
               self.assertEqual(str(outpkt), str(pkt)[:len(str(outpkt))],
                                'Response packet does not match send packet')

class PacketOutMC(SimpleDataPlane):
    """
    Test packet out to multiple output ports

    Send packet out message to controller for 1 to N dataplane ports and
    verify the packet appears on the appropriate ports
    """
    def runTest(self):
        # Construct packet to send to dataplane
        # Send packet to dataplane
        # Poll controller with expect message type packet in

        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # These will get put into function
        of_ports = basic_port_map.keys()
        random.shuffle(of_ports)
        for num_ports in range(1,len(of_ports)+1):
            for outpkt, opt in [
               (simple_tcp_packet(), "simple TCP packet"),
               (simple_eth_packet(), "simple Ethernet packet"),
               (simple_eth_packet(pktlen=40), "tiny Ethernet packet")]:

               dp_ports = of_ports[0:num_ports]
               logging.info("PKT OUT test with " + opt +
                                 ", ports " + str(dp_ports))
               msg = message.packet_out()
               msg.data = str(outpkt)
               act = action.action_output()
               for i in range(0,num_ports):
                  act.port = dp_ports[i]
                  self.assertTrue(msg.actions.add(act),
                                  'Could not add action to msg')

               logging.info("PacketOut to: " + str(dp_ports))
               rv = self.controller.message_send(msg)
               self.assertTrue(rv == 0, "Error sending out message")

               receive_pkt_check(self.dataplane, outpkt, dp_ports,
                                 set(of_ports).difference(dp_ports),
                                 self, basic_config)

class FlowStatsGet(SimpleProtocol):
    """
    Get stats 

    Simply verify stats get transaction
    """

    priority = -1

    def runTest(self):
        logging.info("Running StatsGet")
        logging.info("Inserting trial flow")
        request = flow_mod_gen(basic_port_map, True)
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Failed to insert test flow")
        
        logging.info("Sending flow request")
        request = message.flow_stats_request()
        request.out_port = ofp.OFPP_NONE
        request.table_id = 0xff
        request.match.wildcards = 0 # ofp.OFPFW_ALL
        response, pkt = self.controller.transact(request)
        self.assertTrue(response is not None,
                        "Did not get response for flow stats")
        logging.debug(response.show())

class TableStatsGet(SimpleProtocol):
    """
    Get table stats 

    Simply verify table stats get transaction
    """
    def runTest(self):
        logging.info("Running TableStatsGet")
        logging.info("Inserting trial flow")
        request = flow_mod_gen(basic_port_map, True)
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Failed to insert test flow")
        
        logging.info("Sending table stats request")
        request = message.table_stats_request()
        response, pkt = self.controller.transact(request)
        self.assertTrue(response is not None,
                        "Did not get reply for table stats")
        logging.debug(response.show())

class DescStatsGet(SimpleProtocol):
    """
    Get stats 

    Simply verify stats get transaction
    """
    def runTest(self):
        logging.info("Running DescStatsGet")
        
        logging.info("Sending stats request")
        request = message.desc_stats_request()
        response, pkt = self.controller.transact(request)
        self.assertTrue(response is not None,
                        "Did not get reply for desc stats")
        logging.debug(response.show())

class FlowMod(SimpleProtocol):
    """
    Insert a flow

    Simple verification of a flow mod transaction
    """

    def runTest(self):
        logging.info("Running " + str(self))
        request = flow_mod_gen(basic_port_map, True)
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

class PortConfigMod(SimpleProtocol):
    """
    Modify a bit in port config and verify changed

    Get the switch configuration, modify the port configuration
    and write it back; get the config again and verify changed.
    Then set it back to the way it was.
    """

    def runTest(self):
        logging.info("Running " + str(self))
        for of_port, ifname in basic_port_map.items(): # Grab first port
            break

        (hw_addr, config, advert) = \
            port_config_get(self.controller, of_port)
        self.assertTrue(config is not None, "Did not get port config")

        logging.debug("No flood bit port " + str(of_port) + " is now " + 
                           str(config & ofp.OFPPC_NO_FLOOD))

        rv = port_config_set(self.controller, of_port,
                             config ^ ofp.OFPPC_NO_FLOOD, ofp.OFPPC_NO_FLOOD)
        self.assertTrue(rv != -1, "Error sending port mod")

        # Verify change took place with same feature request
        (hw_addr, config2, advert) = \
            port_config_get(self.controller, of_port)
        logging.debug("No flood bit port " + str(of_port) + " is now " + 
                           str(config2 & ofp.OFPPC_NO_FLOOD))
        self.assertTrue(config2 is not None, "Did not get port config2")
        self.assertTrue(config2 & ofp.OFPPC_NO_FLOOD !=
                        config & ofp.OFPPC_NO_FLOOD,
                        "Bit change did not take")
        # Set it back
        rv = port_config_set(self.controller, of_port, config, 
                             ofp.OFPPC_NO_FLOOD)
        self.assertTrue(rv != -1, "Error sending port mod")

class PortConfigModErr(SimpleProtocol):
    """
    Modify a bit in port config on an invalid port and verify
    error message is received.
    """

    def runTest(self):
        logging.info("Running " + str(self))

        # pick a random bad port number
        bad_port = random.randint(1, ofp.OFPP_MAX)
        count = 0
        while (count < 50) and (bad_port in basic_port_map.keys()):
            bad_port = random.randint(1, ofp.OFPP_MAX)
            count = count + 1
        self.assertTrue(count < 50, "Error selecting bad port")
        logging.info("Select " + str(bad_port) + " as invalid port")

        rv = port_config_set(self.controller, bad_port,
                             ofp.OFPPC_NO_FLOOD, ofp.OFPPC_NO_FLOOD)
        self.assertTrue(rv != -1, "Error sending port mod")

        # poll for error message
        while True:
            (response, raw) = self.controller.poll(ofp.OFPT_ERROR)
            if not response:  # Timeout
                break
            if response.code == ofp.OFPPMFC_BAD_PORT:
                logging.info("Received error message with OFPPMFC_BAD_PORT code")
                break
            if not basic_config["relax"]:  # Only one attempt to match
                break
            count += 1
            if count > 10:   # Too many tries
                break

        self.assertTrue(response is not None, 'Did not receive error message')

class BadMessage(SimpleProtocol):
    """
    Send a message with a bad type and verify an error is returned
    """

    def runTest(self):
        logging.info("Running " + str(self))
        request = illegal_message.illegal_message_type()

        reply, pkt = self.controller.transact(request)
        self.assertTrue(reply is not None, "Did not get response to bad req")
        self.assertTrue(reply.header.type == ofp.OFPT_ERROR,
                        "reply not an error message")
        self.assertTrue(reply.type == ofp.OFPET_BAD_REQUEST,
                        "reply error type is not bad request")
        self.assertTrue(reply.code == ofp.OFPBRC_BAD_TYPE,
                        "reply error code is not bad type")

if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test_spec=basic"
