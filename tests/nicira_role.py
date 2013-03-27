"""
"""
import struct

import logging

from oftest import config
import oftest.controller as controller
import ofp
import oftest.base_tests as base_tests

from oftest.testutils import *

NX_ROLE_OTHER = 0
NX_ROLE_MASTER = 1
NX_ROLE_SLAVE = 2

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
