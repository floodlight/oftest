"""
"""
import struct

import logging

from oftest import config
import oftest.controller as controller
import ofp
import oftest.message as message
import oftest.base_tests as base_tests

from oftest.testutils import *

# Nicira vendor extension constants
NXT_VENDOR = 0x00002320

NXT_ROLE_REQUEST = 10

NXT_ROLE_VALUE = dict( other=0, slave=1, master=2 )

@nonstandard
class NiciraRoleRequest(base_tests.SimpleDataPlane):
    """
    Exercise Nicira vendor extension for requesting HA roles
    """

    def nicira_role_request(self, role):
        """
        Use the BSN_SET_IP_MASK vendor command to change the IP mask for the
        given wildcard index
        """
        logging.info("Sending role request %s" % role)
        m = message.vendor()
        m.vendor = NXT_VENDOR
        m.data = struct.pack("!LL", NXT_ROLE_REQUEST, NXT_ROLE_VALUE[role])
        return m

    def runTest(self):
        '''
        For now, we only verify that a response is received.
        '''
        request = self.nicira_role_request("master")
        response, pkt = self.controller.transact(request)
        self.assertTrue(response is not None, "No reply to Nicira role request")
