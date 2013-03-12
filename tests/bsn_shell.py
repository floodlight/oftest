"""
"""
import struct

import logging

from oftest import config
import oftest.controller as controller
import ofp
import oftest.base_tests as base_tests

from oftest.testutils import *

@nonstandard
class BSNShellCommand(base_tests.SimpleDataPlane):
    """
    Exercise BSN vendor extension for running a shell command on the switch
    """

    def bsn_shell_command(self, cmd):
        """
        Use the BSN_SHELL_COMMAND vendor command to run the given command
        and receive the output
        """
        m = ofp.message.bsn_shell_command(service=0, data=cmd)
        self.controller.message_send(m)
        out = ""
        while True:
            m, _ = self.controller.poll(ofp.OFPT_VENDOR, 60)
            if isinstance(m, ofp.message.bsn_shell_output):
                out += m.data
            elif isinstance(m, ofp.message.bsn_shell_status):
                return m.status, out
            else:
                raise AssertionError("Unexpected message received")

    def runTest(self):
        status, out = self.bsn_shell_command("echo _one     space_")
        self.assertEqual(status, 0, "Shell command returned %s != 0" % status)
        self.assertEqual(out, "_one space_\n", "Shell command output: '%r'" % out)
