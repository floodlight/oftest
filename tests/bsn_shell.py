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
        m = ofp.message.vendor()
        m.vendor = 0x005c16c7
        m.data = struct.pack("!LL", 6, 0) + cmd
        rc = self.controller.message_send(m)
        self.assertNotEqual(rc, -1, "Error sending shell command")
        out = ""
        while True:
            m, r = self.controller.poll(ofp.OFPT_VENDOR, 60)
            self.assertEqual(m.vendor, 0x005c16c7, "Wrong vendor ID")
            subtype = struct.unpack("!L", m.data[:4])[0]
            if subtype == 7:
               out += m.data[4:]
            elif subtype == 8:
               status = struct.unpack("!LL", m.data)[1]
               return status, out
            else:
               assert False, "Wrong subtype"

    def runTest(self):
        status, out = self.bsn_shell_command("echo _one     space_")
        self.assertEqual(status, 0, "Shell command returned %s != 0" % status)
        self.assertEqual(out, "_one space_\n", "Shell command output: '%r'" % out)
