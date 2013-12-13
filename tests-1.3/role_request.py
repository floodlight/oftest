"""
Test the role request message
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

def add_mod64(a, b):
    return (a + b) & (2**64-1)

def simple_role_request(test, role, gen=None, con=None):
    """
    Send a role request we expect to succeed
    """
    if con == None:
        con = test.controller
    request = ofp.message.role_request(role=role, generation_id=gen)
    response, _ = con.transact(request)
    test.assertTrue(isinstance(response, ofp.message.role_reply), "Expected a role reply")
    if role != ofp.OFPCR_ROLE_NOCHANGE:
        test.assertEquals(response.role, role)
    if gen != None:
        test.assertEquals(response.generation_id, gen)
    return response.role, response.generation_id

def failed_role_request(test, role, gen, code, con=None):
    """
    Send a role request we expect to fail
    """
    if con == None:
        con = test.controller
    request = ofp.message.role_request(role=role, generation_id=gen)
    response, _ = con.transact(request)
    test.assertIsInstance(response, ofp.message.role_request_failed_error_msg)
    test.assertEqual(response.code, code)

class RoleRequestNochange(base_tests.SimpleDataPlane):
    """
    Verify that we can query the switch for our current role and generation ID

    The role should default to OFPCR_ROLE_EQUAL.
    """
    def runTest(self):
        role, gen = simple_role_request(self, ofp.OFPCR_ROLE_NOCHANGE)
        self.assertEqual(role, ofp.OFPCR_ROLE_EQUAL)

        # Make sure the generation ID is still the same
        role, new_gen = simple_role_request(self, ofp.OFPCR_ROLE_NOCHANGE)
        self.assertEqual(role, ofp.OFPCR_ROLE_EQUAL)
        self.assertEqual(new_gen, gen)

class RoleRequestEqualToSlave(base_tests.SimpleDataPlane):
    """
    Transition between equal and slave roles and back
    """
    def runTest(self):
        role, gen0 = simple_role_request(self, ofp.OFPCR_ROLE_NOCHANGE)
        self.assertEqual(role, ofp.OFPCR_ROLE_EQUAL)

        # Unchanged generation ID
        role, gen1 = simple_role_request(self, ofp.OFPCR_ROLE_SLAVE, gen0)

        # Back to equal
        simple_role_request(self, ofp.OFPCR_ROLE_EQUAL)

        # Smallest greater generation ID
        role, gen2 = simple_role_request(self, ofp.OFPCR_ROLE_SLAVE, add_mod64(gen1, 1))

        # Back to equal
        simple_role_request(self, ofp.OFPCR_ROLE_EQUAL)

        # Largest greater generation ID
        role, gen3 = simple_role_request(self, ofp.OFPCR_ROLE_SLAVE,
                                         add_mod64(gen2, 2**63-1))

        # Back to equal
        simple_role_request(self, ofp.OFPCR_ROLE_EQUAL)

        # Send least stale generation ID
        failed_role_request(self, ofp.OFPCR_ROLE_SLAVE,
                            add_mod64(gen3, -1),
                            ofp.OFPRRFC_STALE)

        # Check that our role is unchanged
        role, gen = simple_role_request(self, ofp.OFPCR_ROLE_NOCHANGE)
        self.assertEqual(role, ofp.OFPCR_ROLE_EQUAL)
        self.assertEqual(gen, gen3)

        # Send most stale generation ID
        failed_role_request(self, ofp.OFPCR_ROLE_SLAVE,
                            add_mod64(gen3, -(2**63)),
                            ofp.OFPRRFC_STALE)

        # Check that our role is unchanged
        role, gen = simple_role_request(self, ofp.OFPCR_ROLE_NOCHANGE)
        self.assertEqual(role, ofp.OFPCR_ROLE_EQUAL)
        self.assertEqual(gen, gen3)

class RoleRequestEqualToMaster(base_tests.SimpleDataPlane):
    """
    Transition between equal and master roles and back
    """
    def runTest(self):
        role, gen0 = simple_role_request(self, ofp.OFPCR_ROLE_NOCHANGE)
        self.assertEqual(role, ofp.OFPCR_ROLE_EQUAL)

        # Unchanged generation ID
        role, gen1 = simple_role_request(self, ofp.OFPCR_ROLE_MASTER, gen0)

        # Back to equal
        simple_role_request(self, ofp.OFPCR_ROLE_EQUAL)

        # Smallest greater generation ID
        role, gen2 = simple_role_request(self, ofp.OFPCR_ROLE_MASTER, add_mod64(gen1, 1))

        # Back to equal
        simple_role_request(self, ofp.OFPCR_ROLE_EQUAL)

        # Largest greater generation ID
        role, gen3 = simple_role_request(self, ofp.OFPCR_ROLE_MASTER,
                                         add_mod64(gen2, 2**63-1))

        # Back to equal
        simple_role_request(self, ofp.OFPCR_ROLE_EQUAL)

        # Send least stale generation ID
        failed_role_request(self, ofp.OFPCR_ROLE_MASTER,
                            add_mod64(gen3, -1),
                            ofp.OFPRRFC_STALE)

        # Check that our role is unchanged
        role, gen = simple_role_request(self, ofp.OFPCR_ROLE_NOCHANGE)
        self.assertEqual(role, ofp.OFPCR_ROLE_EQUAL)
        self.assertEqual(gen, gen3)

        # Send most stale generation ID
        failed_role_request(self, ofp.OFPCR_ROLE_MASTER,
                            add_mod64(gen3, -(2**63)),
                            ofp.OFPRRFC_STALE)

        # Check that our role is unchanged
        role, gen = simple_role_request(self, ofp.OFPCR_ROLE_NOCHANGE)
        self.assertEqual(role, ofp.OFPCR_ROLE_EQUAL)
        self.assertEqual(gen, gen3)

class RoleRequestSlaveToMaster(base_tests.SimpleDataPlane):
    """
    Transition between slave and master roles and back
    """
    def runTest(self):
        role, gen0 = simple_role_request(self, ofp.OFPCR_ROLE_NOCHANGE)
        self.assertEqual(role, ofp.OFPCR_ROLE_EQUAL)

        # Initial transition to slave
        role, gen1 = simple_role_request(self, ofp.OFPCR_ROLE_SLAVE, gen0)

        # Unchanged generation ID
        role, gen2 = simple_role_request(self, ofp.OFPCR_ROLE_MASTER, gen1)

        # Back to slave
        simple_role_request(self, ofp.OFPCR_ROLE_SLAVE, gen2)

        # Smallest greater generation ID
        role, gen3 = simple_role_request(self, ofp.OFPCR_ROLE_MASTER,
                                         add_mod64(gen2, 1))

        # Back to slave
        simple_role_request(self, ofp.OFPCR_ROLE_SLAVE, gen3)

        # Largest greater generation ID
        role, gen4 = simple_role_request(self, ofp.OFPCR_ROLE_MASTER,
                                         add_mod64(gen3, 2**63-1))

        # Back to slave
        simple_role_request(self, ofp.OFPCR_ROLE_SLAVE, gen4)

        # Send least stale generation ID
        failed_role_request(self, ofp.OFPCR_ROLE_MASTER,
                            add_mod64(gen4, -1),
                            ofp.OFPRRFC_STALE)

        # Check that our role is unchanged
        role, gen = simple_role_request(self, ofp.OFPCR_ROLE_NOCHANGE)
        self.assertEqual(role, ofp.OFPCR_ROLE_SLAVE)
        self.assertEqual(gen, gen4)

        # Send most stale generation ID
        failed_role_request(self, ofp.OFPCR_ROLE_MASTER,
                            add_mod64(gen4, -(2**63)),
                            ofp.OFPRRFC_STALE)

        # Check that our role is unchanged
        role, gen = simple_role_request(self, ofp.OFPCR_ROLE_NOCHANGE)
        self.assertEqual(role, ofp.OFPCR_ROLE_SLAVE)
        self.assertEqual(gen, gen4)

class RolePermissions(base_tests.SimpleDataPlane):
    """
    Verify that a slave connection cannot modify switch state, but
    a master or equal can.
    """
    def runTest(self):
        delete_all_flows(self.controller)
        self.verify_permission(True)

        role, gen = simple_role_request(self, ofp.OFPCR_ROLE_NOCHANGE)

        simple_role_request(self, ofp.OFPCR_ROLE_MASTER, gen)
        self.verify_permission(True)

        simple_role_request(self, ofp.OFPCR_ROLE_SLAVE, gen)
        self.verify_permission(False)

        simple_role_request(self, ofp.OFPCR_ROLE_EQUAL)
        self.verify_permission(True)

    def verify_permission(self, perm):
        self.controller.message_send(
            ofp.message.packet_out(buffer_id=ofp.OFP_NO_BUFFER))

        self.controller.message_send(
            ofp.message.flow_delete(
                buffer_id=ofp.OFP_NO_BUFFER,
                out_port=ofp.OFPP_ANY,
                out_group=ofp.OFPG_ANY))

        self.controller.message_send(
            ofp.message.group_mod(
                command=ofp.OFPGC_DELETE,
                group_id=ofp.OFPG_ALL))

        # TODO OFPT_PORT_MOD
        # TODO OFPT_TABLE_MOD

        do_barrier(self.controller)

        err_count = 0
        while self.controller.packets:
            msg = self.controller.packets.pop(0)[0]
            if msg.type == ofp.OFPT_ERROR:
                self.assertEquals(msg.err_type, ofp.OFPET_BAD_REQUEST)
                self.assertEquals(msg.code, ofp.OFPBRC_IS_SLAVE)
                err_count += 1

        if perm:
            self.assertEquals(err_count, 0, "Expected no errors")
        else:
            self.assertEquals(err_count, 3, "Expected errors for each message")

class SlaveNoPacketIn(base_tests.SimpleDataPlane):
    """
    Verify that slave connections do not receive OFPT_PACKET_IN messages but other roles do.
    """
    def runTest(self):
        delete_all_flows(self.controller)
        ingress_port, = openflow_ports(1)
        pkt = str(simple_tcp_packet())

        logging.info("Inserting table-miss flow sending all packets to controller")
        request = ofp.message.flow_add(
            table_id=test_param_get("table", 0),
            instructions=[
                ofp.instruction.apply_actions(
                    actions=[
                        ofp.action.output(
                            port=ofp.OFPP_CONTROLLER,
                            max_len=ofp.OFPCML_NO_BUFFER)])],
            buffer_id=ofp.OFP_NO_BUFFER,
            priority=0)
        self.controller.message_send(request)
        do_barrier(self.controller)

        _, gen = simple_role_request(self, ofp.OFPCR_ROLE_NOCHANGE)

        simple_role_request(self, ofp.OFPCR_ROLE_MASTER, gen)
        self.dataplane.send(ingress_port, pkt)
        verify_packet_in(self, pkt, ingress_port, ofp.OFPR_NO_MATCH)

        simple_role_request(self, ofp.OFPCR_ROLE_SLAVE, gen)
        self.dataplane.send(ingress_port, pkt)
        verify_no_packet_in(self, pkt, ingress_port)

        simple_role_request(self, ofp.OFPCR_ROLE_EQUAL, gen)
        self.dataplane.send(ingress_port, pkt)
        verify_packet_in(self, pkt, ingress_port, ofp.OFPR_NO_MATCH)

@disabled
class RoleSwitch(unittest.TestCase):
    """
    Verify that when a connection becomes a master the existing master is
    downgraded to slave.

    Requires the switch to attempt to connect in parallel to ports 6653
    and 6753 on the configured IP.
    """

    def setUp(self):
        host = config["controller_host"]
        self.controllers = [
            controller.Controller(host=host,port=6653),
            controller.Controller(host=host,port=6753)
        ]

    def runTest(self):
        # Connect and handshake with both controllers
        for con in self.controllers:
            con.start()
            if not con.connect():
                raise AssertionError("failed to connect controller %s" % str(con))
            reply, _ = con.transact(ofp.message.features_request())
            self.assertTrue(isinstance(reply, ofp.message.features_reply))

        # Assert initial role and get generation IDs
        role, gen0 = simple_role_request(self, ofp.OFPCR_ROLE_NOCHANGE, con=self.controllers[0])
        self.assertEqual(role, ofp.OFPCR_ROLE_EQUAL)
        role, gen1 = simple_role_request(self, ofp.OFPCR_ROLE_NOCHANGE, con=self.controllers[1])
        self.assertEqual(role, ofp.OFPCR_ROLE_EQUAL)

        # Initial role assignment: controller 0 is master, controller 1 is slave
        simple_role_request(self, ofp.OFPCR_ROLE_MASTER, gen0, con=self.controllers[0])
        simple_role_request(self, ofp.OFPCR_ROLE_SLAVE, gen1, con=self.controllers[1])
        self.verify_role(self.controllers[0], ofp.OFPCR_ROLE_MASTER)
        self.verify_role(self.controllers[1], ofp.OFPCR_ROLE_SLAVE)

        # Controller 1 requests master
        # Controller 0 becomes slave
        simple_role_request(self, ofp.OFPCR_ROLE_MASTER, gen1, con=self.controllers[1])
        self.verify_role(self.controllers[0], ofp.OFPCR_ROLE_SLAVE)
        self.verify_role(self.controllers[1], ofp.OFPCR_ROLE_MASTER)

        # Controller 0 requests master
        # Controller 1 becomes slave
        simple_role_request(self, ofp.OFPCR_ROLE_MASTER, gen0, con=self.controllers[0])
        self.verify_role(self.controllers[0], ofp.OFPCR_ROLE_MASTER)
        self.verify_role(self.controllers[1], ofp.OFPCR_ROLE_SLAVE)

        # Controller 1 requests equal
        # Controller 0 remains master
        simple_role_request(self, ofp.OFPCR_ROLE_EQUAL, gen1, con=self.controllers[1])
        self.verify_role(self.controllers[0], ofp.OFPCR_ROLE_MASTER)
        self.verify_role(self.controllers[1], ofp.OFPCR_ROLE_EQUAL)

        # Both controllers request slave
        simple_role_request(self, ofp.OFPCR_ROLE_SLAVE, gen0, con=self.controllers[0])
        simple_role_request(self, ofp.OFPCR_ROLE_SLAVE, gen1, con=self.controllers[1])
        self.verify_role(self.controllers[0], ofp.OFPCR_ROLE_SLAVE)
        self.verify_role(self.controllers[1], ofp.OFPCR_ROLE_SLAVE)

    def verify_role(self, con, role):
        rcv_role, _ = simple_role_request(self, ofp.OFPCR_ROLE_NOCHANGE, con=con)
        self.assertEqual(rcv_role, role)

    def tearDown(self):
        for con in self.controllers:
            con.shutdown()
