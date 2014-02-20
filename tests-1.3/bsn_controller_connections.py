"""
Test the BSN controller connections request
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

class BsnControllerConnectionsRequest(base_tests.SimpleProtocol):
    """
    Verify that the switch sends a bsn_controller_connections_reply in response
    to the request
    """
    def runTest(self):
        request = ofp.message.bsn_controller_connections_request()
        response, _ = self.controller.transact(request)
        self.assertIsInstance(response, ofp.message.bsn_controller_connections_reply)
