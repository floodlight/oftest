"""
Basic test cases for the oftest OpenFlow test framework

Current Assumptions:

  The oftest framework source is in ../src/python/oftest
  Configuration of the platform and system is stored in oft_config in that dir
  The switch is actively attempting to contact the controller at the address
indicated oin oft_config

"""

from scapy.all import *
import unittest

import time
import sys
sys.path.append("../src/python/oftest")
from message import *
from dataplane import *
from controller import *
from oft_config import *

class SimpleProtocolTestCase(unittest.TestCase):
    """
    Root class for setting up the controller
    """

    def setUp(self):
        debug_log("CTTC", debug_level_default,
                  DEBUG_INFO, "setup for " + str(self))
        self.controller = Controller()
        self.controller.connect()

    def tearDown(self):
        debug_log("CTTC", debug_level_default, 
                  DEBUG_INFO, "teardown for simple proto test")
        self.controller.shutdown()
        self.controller.join()

    def runTest(self):
        self.assertTrue(self.controller.connected, 
                        str(self) + 'No connection to switch')

class SimpleDataPlaneTestCase(SimpleProtocolTestCase):
    """
    Root class that sets up the controller and dataplane
    """
    def setUp(self):
        SimpleProtocolTestCase.setUp(self)
        self.dataplane = DataPlane()
        for of_port, ifname in interface_ofport_map.items():
            self.dataplane.port_add(ifname, of_port)

    def tearDown(self):
        debug_log("DPTC", debug_level_default,
                  DEBUG_INFO, "teardown for simple dataplane test")
        SimpleProtocolTestCase.tearDown(self)
        self.dataplane.kill(join_threads=False)

    def runTest(self):
        self.assertTrue(self.controller.connected, 
                        str(self) + 'No connection to switch')
        # self.dataplane.show()
        # Would like an assert that checks the data plane

class EchoTestCase(SimpleProtocolTestCase):
    """
    Test echo response with no data
    """
    def runTest(self):
        request = echo_request()
        response = self.controller.transact(request)
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
        response = self.controller.transact(request)
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
        # Send packet to dataplane
        # Poll controller with expect message type packet in
        # For now, a random packet from scapy tutorial
        pkt=Ether()/IP(dst="www.slashdot.org")/TCP()/\
            "GET /index.html HTTP/1.0 \n\n"
        for of_port in interface_ofport_map.keys():
            self.dataplane.send(of_port, str(pkt))
            # For now, just send one packet
            break

        time.sleep(2) # @todo Implement poll timeout for test cases
        #@todo Check for unexpected messages?
        (response, raw) = self.controller.poll(OFPT_PACKET_IN)

        self.assertTrue(not response is None, 'Packet in message not received')
        # Data has CRC on it, so take off last 4 bytes
        self.assertEqual(str(pkt), response.data[:-4], 
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
        msg = packet_out()
        msg.data = str(outpkt)
        act = action_output()
        act.port = interface_ofport_map.keys()[0]
        self.assertTrue(msg.actions.add(act), 'Could not add action to msg')

        msg.header.xid = 0x12345678
        self.controller.message_send(msg.pack())

        time.sleep(2) # @todo Implement poll timeout for test cases
        (of_port, pkt, pkt_time) = self.dataplane.packet_get()
        print "pkt in on of_port" + str(of_port)
        hexdump(str(pkt))

        self.assertTrue(not pkt is None, 'Packet not received')
        # Data has CRC on it, so take off last 4 bytes
        self.assertEqual(str(outpkt), str(pkt),
                         'Response packet does not match send packet')


if __name__ == "__main__":
    unittest.main()
