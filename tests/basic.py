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
import signal
import sys
sys.path.append("../src/python/oftest")
from message import *
from dataplane import *
from controller import *
from oft_config import *

#debug_level_default = DEBUG_VERBOSE
dbg_lvl = debug_level_default

class SimpleProtocolTestCase(unittest.TestCase):
    """
    Root class for setting up the controller
    """

    def dbg(self, level, string):
        debug_log(str(self), dbg_lvl, level, string)

    def sig_handler(self):
        print "Received interrupt signal; exiting"
        self.controller.shutdown()
        sys.exit(1)

    def setUp(self):
        signal.signal(signal.SIGINT, self.sig_handler)
        self.dbg(DEBUG_INFO, "Setup for " + str(self))
        self.controller = Controller()
        self.controller.start()
        self.controller.connect(timeout=20)
        self.dbg(DEBUG_INFO, "Connected " + str(self.controller.switch_addr))

    def tearDown(self):
        self.dbg(DEBUG_INFO, "Teardown for simple proto test")
        self.controller.shutdown()
        # self.controller.join()

    def runTest(self):
        # Just a simple sanity check as illustration
        self.assertTrue(self.controller.switch_socket is not None,
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
        self.dbg(DEBUG_INFO, "Teardown for simple dataplane test")
        SimpleProtocolTestCase.tearDown(self)
        self.dataplane.kill(join_threads=False)
        self.dbg(DEBUG_INFO, "Teardown done")

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

        self.assertTrue(response is not None, 'Packet in message not received')
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
        dp_port = act.port = interface_ofport_map.keys()[0]
        self.assertTrue(msg.actions.add(act), 'Could not add action to msg')

        self.dbg(DEBUG_INFO, "pkt out to port " + str(dp_port))
        rv = self.controller.message_send(msg)
        self.assertTrue(rv == 0, "Error sending out message")

        time.sleep(1) # @todo Implement poll timeout for test cases
        (of_port, pkt, pkt_time) = self.dataplane.packet_get()

        self.assertTrue(pkt is not None, 'Packet not received')
        if of_port is not None:
            self.assertEqual(of_port, dp_port, "Unexpected receive port")
        self.assertEqual(str(outpkt), str(pkt),
                         'Response packet does not match send packet')


if __name__ == "__main__":
    unittest.main()
#    suite = unittest.TestLoader().loadTestsFromTestCase(PacketOutTestCase)
#    unittest.TextTestRunner(verbosity=2).run(suite) 
