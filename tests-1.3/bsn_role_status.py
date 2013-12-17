"""
Test the BSN role status message

This is a backport of the OpenFlow 1.4 functionality.
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

@disabled
@nonstandard
class RoleStatus(unittest.TestCase):
    """
    Verify that when a connection becomes a master the existing master is
    downgraded to slave and receives a role-status message.

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

        # Controller 0 should receive a bsn_role_status message
        msg, _ = self.controllers[0].poll(ofp.OFPT_EXPERIMENTER)
        self.assertIsInstance(msg, ofp.message.bsn_role_status)
        self.assertEqual(msg.role, ofp.OFPCR_ROLE_SLAVE)
        self.assertEqual(msg.reason, ofp.OFP_BSN_CONTROLLER_ROLE_REASON_MASTER_REQUEST)
        self.assertEqual(msg.generation_id, gen1)

    def verify_role(self, con, role):
        rcv_role, _ = simple_role_request(self, ofp.OFPCR_ROLE_NOCHANGE, con=con)
        self.assertEqual(rcv_role, role)

    def tearDown(self):
        for con in self.controllers:
            con.shutdown()

