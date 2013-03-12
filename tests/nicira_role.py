"""
"""
import struct

import logging

from oftest import config
import oftest.controller as controller
import ofp
import oftest.base_tests as base_tests

from oftest.testutils import *

NX_ROLE_MASTER = 2

@nonstandard
class NiciraRoleRequest(base_tests.SimpleDataPlane):
    """
    Exercise Nicira vendor extension for requesting HA roles
    """

    def runTest(self):
        '''
        For now, we only verify that a response is received.
        '''
        request = ofp.message.nicira_controller_role_request(role=NX_ROLE_MASTER)
        response, pkt = self.controller.transact(request)
        self.assertTrue(response is not None, "No reply to Nicira role request")
