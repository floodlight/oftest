"""
Basic protocol and dataplane test cases

It is recommended that these definitions be kept in their own
namespace as different groups of tests will likely define 
similar identifiers.
"""

import sys
import logging
import unittest
import ipaddr

from oftest import config
import ofp
import oftest.base_tests as base_tests
import oftest.oft12.testutils as testutils

class Echo(base_tests.SimpleProtocol):
    """
    Test echo response with no data
    """
    def runTest(self):
        testutils.do_echo_request_reply_test(self, self.controller)

class EchoWithData(base_tests.SimpleProtocol):
    """
    Test echo response with short string data
    """
    def runTest(self):
        request = ofp.message.echo_request()
        request.data = 'OpenFlow Will Rule The World'
        response, _ = self.controller.transact(request)
        self.assertEqual(response.header.type, ofp.OFPT_ECHO_REPLY,
                         'response is not echo_reply')
        self.assertEqual(request.header.xid, response.header.xid,
                         'response xid != request xid')
        self.assertEqual(request.data, response.data,
                         'response data does not match request')

class FeaturesRequest(base_tests.SimpleProtocol):
    """
    Test features_request to make sure we get a response
    
    Does NOT test the contents; just that we get a response
    """
    def runTest(self):
        request = ofp.message.features_request()
        response,_ = self.controller.transact(request)
        self.assertTrue(response,"Got no features_reply to features_request")
        self.assertEqual(response.header.type, ofp.OFPT_FEATURES_REPLY,
                         'response is not echo_reply')
        self.assertTrue(len(response) >= 32, "features_reply too short: %d < 32 " % len(response))
       
class PacketIn(base_tests.SimpleDataPlane):
    """
    Test packet in function

    Send a packet to each dataplane port and verify that a packet
    in message is received from the controller for each
    """
    def runTest(self):
        # Construct packet to send to dataplane
        # Send packet to dataplane, once to each port
        # Poll controller with expect message type packet in

        rc = testutils.delete_all_flows(self.controller, logging)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        for of_port in config["port_map"].keys():
            logging.info("PKT IN test, port " + str(of_port))
            pkt = testutils.simple_tcp_packet()
            self.dataplane.send(of_port, str(pkt))
            #@todo Check for unexpected messages?
            (response, _) = self.controller.poll(ofp.OFPT_PACKET_IN, 2)

            self.assertTrue(response is not None, 
                            'Packet in message not received on port ' + 
                            str(of_port))
            if str(pkt) != response.data:
                logging.debug("pkt  len " + str(len(str(pkt))) +
                                   ": " + str(pkt))
                logging.debug("resp len " + 
                                   str(len(str(response.data))) + 
                                   ": " + str(response.data))

            self.assertEqual(str(pkt), response.data,
                             'Response packet does not match send packet' +
                             ' for port ' + str(of_port))

class PacketOut(base_tests.SimpleDataPlane):
    """
    Test packet out function

    Send packet out message to controller for each dataplane port and
    verify the packet appears on the appropriate dataplane port
    """
    def runTest(self):
        # Construct packet to send to dataplane
        # Send packet to dataplane
        # Poll controller with expect message type packet in

        rc = testutils.delete_all_flows(self.controller, logging)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # These will get put into function
        outpkt = testutils.simple_tcp_packet()
        of_ports = config["port_map"].keys()
        of_ports.sort()
        for dp_port in of_ports:
            msg = ofp.message.packet_out()
            msg.in_port = ofp.OFPP_CONTROLLER
            msg.data = str(outpkt)
            act = ofp.action.action_output()
            act.port = dp_port
            self.assertTrue(msg.actions.add(act), 'Could not add action to msg')

            logging.info("PacketOut to: " + str(dp_port))
            rv = self.controller.message_send(msg)
            self.assertTrue(rv == 0, "Error sending out message")

            (of_port, pkt, _) = self.dataplane.poll(timeout=1)

            self.assertTrue(pkt is not None, 'Packet not received')
            logging.info("PacketOut: got pkt from " + str(of_port))
            if of_port is not None:
                self.assertEqual(of_port, dp_port, "Unexpected receive port")
            self.assertEqual(str(outpkt), str(pkt),
                             'Response packet does not match send packet')

class FlowRemoveAll(base_tests.SimpleProtocol):
    """
    Remove all flows; required for almost all tests 

    Add a bunch of flows, remove them, and then make sure there are no flows left
    This is an intentionally naive test to see if the baseline functionality works 
    and should be a precondition to any more complicated deletion test (e.g., 
    delete_strict vs. delete)
    """
    def runTest(self):
        logging.info("Running StatsGet")
        logging.info("Inserting trial flow")
        request = ofp.message.flow_mod()
        request.buffer_id = 0xffffffff
        for i in range(1,5):
            request.priority = i*1000
            logging.debug("Adding flow %d" % i)
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Failed to insert test flow %d" % i)
        logging.info("Removing all flows")
        testutils.delete_all_flows(self.controller, logging)
        logging.info("Sending flow request")
        request = ofp.message.flow_stats_request()
        request.out_port = ofp.OFPP_ANY
        request.out_group = ofp.OFPG_ANY
        request.table_id = 0xff
        response, _ = self.controller.transact(request, timeout=2)
        self.assertTrue(response is not None, "Did not get response")
        self.assertTrue(isinstance(response,ofp.message.flow_stats_reply),"Not a flow_stats_reply")
        self.assertEqual(len(response.stats),0)
        logging.debug(response.show())
        


class FlowStatsGet(base_tests.SimpleProtocol):
    """
    Get stats 

    Simply verify stats get transaction
    """
    def runTest(self):
        logging.info("Running StatsGet")
        logging.info("Inserting trial flow")
        request = ofp.message.flow_mod()
        request.buffer_id = 0xffffffff
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Failed to insert test flow")
        
        logging.info("Sending flow request")
        response = testutils.flow_stats_get(self)
        logging.debug(response.show())

class TableStatsGet(base_tests.SimpleProtocol):
    """
    Get table stats 

    Naively verify that we get a reply
    do better sanity check of data in stats.TableStats test
    """
    def runTest(self):
        logging.info("Running TableStatsGet")
        logging.info("Sending table stats request")
        request = ofp.message.table_stats_request()
        response, _ = self.controller.transact(request, timeout=2)
        self.assertTrue(response is not None, "Did not get response")
        logging.debug(response.show())

class FlowMod(base_tests.SimpleProtocol):
    """
    Insert a flow

    Simple verification of a flow mod transaction
    """

    def runTest(self):
        logging.info("Running " + str(self))
        request = ofp.message.flow_mod()
        request.buffer_id = 0xffffffff
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

class PortConfigMod(base_tests.SimpleProtocol):
    """
    Modify a bit in port config and verify changed

    Get the switch configuration, modify the port configuration
    and write it back; get the config again and verify changed.
    Then set it back to the way it was.
    """

    def runTest(self):
        logging.info("Running " + str(self))
        for of_port, _ in config["port_map"].items(): # Grab first port
            break

        (_, port_config, _) = \
            testutils.port_config_get(self.controller, of_port, logging)
        self.assertTrue(port_config is not None, "Did not get port config")

        logging.debug("No flood bit port " + str(of_port) + " is now " + 
                           str(port_config & ofp.OFPPC_NO_PACKET_IN))

        rv = testutils.port_config_set(self.controller, of_port,
                             port_config ^ ofp.OFPPC_NO_PACKET_IN, ofp.OFPPC_NO_PACKET_IN,
                             logging)
        self.assertTrue(rv != -1, "Error sending port mod")

        # Verify change took place with same feature request
        (_, port_config2, _) = \
            testutils.port_config_get(self.controller, of_port, logging)
        logging.debug("No packet_in bit port " + str(of_port) + " is now " + 
                           str(port_config2 & ofp.OFPPC_NO_PACKET_IN))
        self.assertTrue(port_config2 is not None, "Did not get port config2")
        self.assertTrue(port_config2 & ofp.OFPPC_NO_PACKET_IN !=
                        port_config & ofp.OFPPC_NO_PACKET_IN,
                        "Bit change did not take")
        # Set it back
        rv = testutils.port_config_set(self.controller, of_port, port_config, 
                             ofp.OFPPC_NO_PACKET_IN, logging)
        self.assertTrue(rv != -1, "Error sending port mod")
        
class TableModConfig(base_tests.SimpleProtocol):
    """ Simple table modification
    
    Mostly to make sure the switch correctly responds to these messages.
    More complicated tests in the multi-tables.py tests
    """        
    def runTest(self):
        logging.info("Running " + str(self))
        table_mod = ofp.message.table_mod()
        table_mod.table_id = 0 # first table should always exist
        table_mod.config = ofp.OFPTC_TABLE_MISS_CONTROLLER
        
        rv = self.controller.message_send(table_mod)
        self.assertTrue(rv != -1, "Error sending table_mod")
        testutils.do_echo_request_reply_test(self, self.controller)
    

if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test_spec=basic"
