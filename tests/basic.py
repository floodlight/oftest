"""
Basic test cases for the oftest OpenFlow test framework

It is recommended that these definitions be kept in their own
namespace as different groups of tests will likely define 
similar identifiers.

Current Assumptions:

  The oftest framework source is in ../src/python/oftest
  Configuration of the platform and system is stored in oft_config in that dir
  The switch is actively attempting to contact the controller at the address
indicated oin oft_config


"""

from scapy.all import *
import unittest

import time
import signal
import sys
##@todo Use setup to place OFT modules in path
sys.path.append("../src/python/oftest")
from message import *
from dataplane import *
from controller import *
import logging

basic_port_map = None
basic_logger = None
basic_config = None

def test_set_init(config):
    """
    Set up function for basic test classes

    @param config The configuration dictionary; see oft
    @return TestSuite object for the class; may depend on config
    """

    global basic_port_map
    global basic_logger
    global basic_config

    basic_logger = logging.getLogger("basic")
    basic_logger.info("Initializing test set")
    basic_port_map = config["port_map"]
    basic_config = config
    return suite()

def suite():
    suite = unittest.TestSuite()
    suite.addTest(SimpleProtocolTestCase())
    suite.addTest(SimpleDataPlaneTestCase())
    suite.addTest(EchoTestCase())
    suite.addTest(EchoWithDataTestCase())
    suite.addTest(PacketInTestCase())
    suite.addTest(PacketOutTestCase())
    return suite

class SimpleProtocolTestCase(unittest.TestCase):
    """
    Root class for setting up the controller
    """

    def sig_handler(self):
        basic_logger.critical("Received interrupt signal; exiting")
        print "Received interrupt signal; exiting"
        self.controller.shutdown()
        sys.exit(1)

    def setUp(self):
        signal.signal(signal.SIGINT, self.sig_handler)
        basic_logger.info("Setup for " + str(self))
        self.controller = Controller(host=basic_config["controller_host"],
                                     port=basic_config["controller_port"])
        self.controller.start()
        self.controller.connect(timeout=20)
        basic_logger.info("Connected " + str(self.controller.switch_addr))

    def tearDown(self):
        basic_logger.info("Teardown for simple proto test")
        self.controller.shutdown()
        # self.controller.join()

    def runTest(self):
        # Just a simple sanity check as illustration
        basic_logger.info("Running simple proto test")
        self.assertTrue(self.controller.switch_socket is not None,
                        str(self) + 'No connection to switch')

class SimpleDataPlaneTestCase(SimpleProtocolTestCase):
    """
    Root class that sets up the controller and dataplane
    """
    def setUp(self):
        SimpleProtocolTestCase.setUp(self)
        self.dataplane = DataPlane()
        for of_port, ifname in basic_port_map.items():
            self.dataplane.port_add(ifname, of_port)

    def tearDown(self):
        basic_logger.info("Teardown for simple dataplane test")
        SimpleProtocolTestCase.tearDown(self)
        self.dataplane.kill(join_threads=True)
        basic_logger.info("Teardown done")

    def runTest(self):
        self.assertTrue(self.controller.switch_socket is not None,
                        str(self) + 'No connection to switch')
        # self.dataplane.show()
        # Would like an assert that checks the data plane

class EchoTestCase(SimpleProtocolTestCase):
    """
    Test echo response with no data
    """
    def runTest(self):
        request = echo_request()
        response, pkt = self.controller.transact(request)
        self.assertEqual(response.header.type, OFPT_ECHO_REPLY,
                         'response is not echo_reply')
        self.assertEqual(request.header.xid, response.header.xid,
                         'response xid != request xid')
        self.assertEqual(len(response.data), 0, 'response data non-empty')

class EchoWithDataTestCase(SimpleProtocolTestCase):
    """
    Test echo response with short string data
    """
    def runTest(self):
        request = echo_request()
        request.data = 'OpenFlow Will Rule The World'
        response, pkt = self.controller.transact(request)
        self.assertEqual(response.header.type, OFPT_ECHO_REPLY,
                         'response is not echo_reply')
        self.assertEqual(request.header.xid, response.header.xid,
                         'response xid != request xid')
        self.assertEqual(request.data, response.data,
                         'response data does not match request')

class PacketInTestCase(SimpleDataPlaneTestCase):
    """
    Test packet in function
    """
    def runTest(self):
        # Construct packet to send to dataplane
        # Send packet to dataplane, once to each port
        # Poll controller with expect message type packet in
        # For now, a random packet from scapy tutorial

        for of_port in basic_port_map.keys():
            basic_logger.info("PKT IN test, port " + str(of_port))
            pkt=Ether()/IP(dst="www.slashdot.org")/TCP()/\
                ("GET /index.html HTTP/1.0. port" + str(of_port))
            self.dataplane.send(of_port, str(pkt))
            #@todo Check for unexpected messages?
            (response, raw) = self.controller.poll(OFPT_PACKET_IN, 2)

            self.assertTrue(response is not None, 
                            'Packet in message not received')
            if str(pkt) != response.data:
                basic_logger.debug("pkt: "+str(pkt)+"  resp: " +
                                   str(response))

            self.assertEqual(str(pkt), response.data,
                             'Response packet does not match send packet')

class PacketOutTestCase(SimpleDataPlaneTestCase):
    """
    Test packet out function
    """
    def runTest(self):
        # Construct packet to send to dataplane
        # Send packet to dataplane
        # Poll controller with expect message type packet in
        # For now, a random packet from scapy tutorial

        # These will get put into function
        outpkt=Ether()/IP(dst="www.slashdot.org")/TCP()/\
            "GET /index.html HTTP/1.0 \n\n"
        of_ports = basic_port_map.keys()
        of_ports.sort()
        for dp_port in of_ports:
            msg = packet_out()
            msg.data = str(outpkt)
            act = action_output()
            act.port = dp_port
            self.assertTrue(msg.actions.add(act), 'Could not add action to msg')

            basic_logger.info("PacketOut to: " + str(dp_port))
            rv = self.controller.message_send(msg)
            self.assertTrue(rv == 0, "Error sending out message")

            (of_port, pkt, pkt_time) = self.dataplane.poll(timeout=1)

            self.assertTrue(pkt is not None, 'Packet not received')
            basic_logger.info("PacketOut: got pkt from " + str(of_port))
            if of_port is not None:
                self.assertEqual(of_port, dp_port, "Unexpected receive port")
            self.assertEqual(str(outpkt), str(pkt),
                             'Response packet does not match send packet')

if __name__ == "__main__":
    unittest.main()

#    suite = unittest.TestLoader().loadTestsFromTestCase(PacketOutTestCase)
#    unittest.TextTestRunner(verbosity=2).run(suite) 
