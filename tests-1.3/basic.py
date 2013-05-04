"""
Basic test cases

Test cases in other modules depend on this functionality.
"""

from oftest import config
import oftest.base_tests as base_tests
import ofp

from oftest.testutils import *

@group('smoke')
class Echo(base_tests.SimpleProtocol):
    """
    Test echo response with no data
    """
    def runTest(self):
        request = ofp.message.echo_request()
        response, pkt = self.controller.transact(request)
        self.assertTrue(response is not None,
                        "Did not get echo reply")
        self.assertEqual(response.type, ofp.OFPT_ECHO_REPLY,
                         'response is not echo_reply')
        self.assertEqual(request.xid, response.xid,
                         'response xid != request xid')
        self.assertEqual(len(response.data), 0, 'response data non-empty')
