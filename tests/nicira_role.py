"""
Test the Nicira controller role extension
"""
import struct
import unittest
import logging

import oftest
from oftest import config
import oftest.controller as controller
import ofp
import oftest.base_tests as base_tests

from oftest.testutils import *

NX_ROLE_OTHER = 0
NX_ROLE_MASTER = 1
NX_ROLE_SLAVE = 2

def set_role(test, role, con=None):
    if con == None:
        con = test.controller
    request = ofp.message.nicira_controller_role_request(role=role)
    response, _ = con.transact(request)
    test.assertTrue(isinstance(response, ofp.message.nicira_controller_role_reply), "Expected a role reply")
    test.assertEquals(response.role, role)

class AnyReply(base_tests.SimpleDataPlane):
    """
    Verify that a role request gets either a role reply or an error.

    This test should pass on any switch, no matter whether it implements
    the extension.
    """
    def runTest(self):
        request = ofp.message.nicira_controller_role_request(role=NX_ROLE_MASTER)
        response, pkt = self.controller.transact(request)
        self.assertTrue(response is not None, "No reply to Nicira role request")
        if isinstance(response, ofp.message.nicira_controller_role_reply):
            logging.info("Role reply received")
            logging.info(response.show())
            self.assertEquals(response.role, NX_ROLE_MASTER)
        elif isinstance(response, ofp.message.error_msg):
            logging.info("Error message received")
            logging.info(response.show())
            self.assertEquals(response.err_type, ofp.OFPET_BAD_REQUEST)
            self.assertEquals(response.code, ofp.OFPBRC_BAD_VENDOR)
        else:
            raise AssertionError("Unexpected reply type")

@nonstandard
class RolePermissions(base_tests.SimpleDataPlane):
    """
    Verify that a slave connection cannot modify switch state, but
    a master or equal can.
    """
    def runTest(self):
        self.features_reply, _ = self.controller.transact(ofp.message.features_request())
        delete_all_flows(self.controller)
        self.verify_permission(True)

        set_role(self, NX_ROLE_MASTER)
        self.verify_permission(True)

        set_role(self, NX_ROLE_SLAVE)
        self.verify_permission(False)

        set_role(self, NX_ROLE_OTHER)
        self.verify_permission(True)

    def verify_permission(self, perm):
        port = self.features_reply.ports[0]

        self.controller.message_send(ofp.message.port_mod(port_no=port.port_no, hw_addr=port.hw_addr))
        self.controller.message_send(ofp.message.packet_out(buffer_id=0xffffffff))
        self.controller.message_send(ofp.message.flow_add(buffer_id=0xffffffff))
        do_barrier(self.controller)

        err_count = 0
        while self.controller.packets:
            msg = self.controller.packets.pop(0)[0]
            if isinstance(msg, ofp.message.error_msg):
                self.assertEquals(msg.err_type, ofp.OFPET_BAD_REQUEST)
                self.assertEquals(msg.code, ofp.OFPBRC_EPERM)
                err_count += 1

        if perm:
            self.assertEquals(err_count, 0, "Expected no errors")
        else:
            self.assertEquals(err_count, 3, "Expected errors for each message")

@nonstandard
class SlaveNoPacketIn(base_tests.SimpleDataPlane):
    """
    Verify that slave connections do not receive OFPT_PACKET_IN messages but other roles do.
    """
    def runTest(self):
        delete_all_flows(self.controller)

        set_role(self, NX_ROLE_MASTER)
        self.verify_packetin(True)

        set_role(self, NX_ROLE_SLAVE)
        self.verify_packetin(False)

        set_role(self, NX_ROLE_OTHER)
        self.verify_packetin(True)

    def verify_packetin(self, enabled):
        ingress_port = config["port_map"].keys()[0]
        self.dataplane.send(ingress_port, str(simple_tcp_packet()))

        if enabled:
            timeout = -1
        else:
            timeout = 0.5
        msg, _ = self.controller.poll(exp_msg=ofp.OFPT_PACKET_IN, timeout=timeout)

        if enabled:
            self.assertTrue(msg != None, "Expected a packet-in message")
        else:
            self.assertTrue(msg == None, "Did not expect a packet-in message")

@nonstandard
@disabled
class RoleSwitch(unittest.TestCase):
    """
    Verify that when a connection becomes a master the existing master is
    downgraded to slave.

    Requires the switch to attempt to connect in parallel to ports 6633
    and 6634 on the configured IP.
    """

    def setUp(self):
        host = config["controller_host"]
        self.controllers = [
            controller.Controller(host=host,port=6633),
            controller.Controller(host=host,port=6634)
        ]

    def runTest(self):
        # Connect and handshake with both controllers
        for con in self.controllers:
            con.start()
            if not con.connect():
                raise AssertionError("failed to connect controller %s" % str(con))
            reply, _ = con.transact(ofp.message.features_request())
            self.assertTrue(isinstance(reply, ofp.message.features_reply))

        # Initial role assignment, controller 0 is master
        set_role(self, NX_ROLE_MASTER, con=self.controllers[0])
        set_role(self, NX_ROLE_SLAVE, con=self.controllers[1])
        self.verify_role(self.controllers[0], True)
        self.verify_role(self.controllers[1], False)

        # Controller 1 becomes master
        set_role(self, NX_ROLE_MASTER, con=self.controllers[1])
        self.verify_role(self.controllers[0], False)
        self.verify_role(self.controllers[1], True)

        # Controller 0 becomes master
        set_role(self, NX_ROLE_MASTER, con=self.controllers[0])
        self.verify_role(self.controllers[0], True)
        self.verify_role(self.controllers[1], False)

        # Controller 1 becomes equal
        set_role(self, NX_ROLE_OTHER, con=self.controllers[1])
        self.verify_role(self.controllers[0], True)
        self.verify_role(self.controllers[1], True)

        # Both controllers become slaves
        set_role(self, NX_ROLE_SLAVE, con=self.controllers[0])
        set_role(self, NX_ROLE_SLAVE, con=self.controllers[1])
        self.verify_role(self.controllers[0], False)
        self.verify_role(self.controllers[1], False)

    def verify_role(self, con, master):
        con.message_send(ofp.message.flow_add(buffer_id=0xffffffff))
        do_barrier(con)

        err_count = 0
        while con.packets:
            msg = con.packets.pop(0)[0]
            if isinstance(msg, ofp.message.error_msg):
                self.assertEquals(msg.err_type, ofp.OFPET_BAD_REQUEST)
                self.assertEquals(msg.code, ofp.OFPBRC_EPERM)
                err_count += 1

        if master:
            self.assertEquals(err_count, 0, "Expected no errors")
        else:
            self.assertEquals(err_count, 1, "Expected errors for each message")

    def tearDown(self):
        for con in self.controllers:
            con.shutdown()

@nonstandard
@disabled
class EqualAsyncMessages(unittest.TestCase):
    """
    Verify that 'equal' controllers all get async events.

    Requires the switch to attempt to connect in parallel to ports 6633
    and 6634 on the configured IP.
    """

    def setUp(self):
        host = config["controller_host"]
        self.controllers = [
            controller.Controller(host=host,port=6633),
            controller.Controller(host=host,port=6634)
        ]
        self.dataplane = oftest.dataplane_instance
        self.dataplane.flush()

    def runTest(self):
        # Connect and handshake with both controllers
        for con in self.controllers:
            con.start()
            if not con.connect():
                raise AssertionError("failed to connect controller %s" % str(con))
            reply, _ = con.transact(ofp.message.features_request())
            self.assertTrue(isinstance(reply, ofp.message.features_reply))

        delete_all_flows(self.controllers[0])
        do_barrier(self.controllers[0])

        pkt = str(simple_tcp_packet())
        ingress_port = config["port_map"].keys()[0]
        self.dataplane.send(ingress_port, pkt)

        for con in self.controllers:
            msg, _ = con.poll(ofp.OFPT_PACKET_IN)
            self.assertTrue(msg != None)
            self.assertEquals(msg.data, pkt)

    def tearDown(self):
        for con in self.controllers:
            con.shutdown()
            con.join()
        del self.controllers
