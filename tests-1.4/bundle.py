# Distributed under the OpenFlow Software License (see LICENSE)
# Copyright (c) 2014 Big Switch Networks, Inc.
"""
Bundle test cases
"""

import logging

from oftest import config
import oftest.base_tests as base_tests
import ofp

from oftest.testutils import *

class Commit(base_tests.SimpleProtocol):
    """
    Verify that messages added to a bundle are executed only after a commit
    """
    def runTest(self):
        request = ofp.message.bundle_ctrl_msg(
            bundle_ctrl_type=ofp.OFPBCT_OPEN_REQUEST,
            bundle_id=1)

        response, _ = self.controller.transact(request)
        self.assertIsInstance(response, ofp.message.bundle_ctrl_msg)
        self.assertEqual(response.bundle_ctrl_type, ofp.OFPBCT_OPEN_REPLY)
        self.assertEqual(response.bundle_id, 1)

        for i in xrange(0, 10):
            request = ofp.message.bundle_add_msg(
                xid=i,
                bundle_id=1,
                data=ofp.message.echo_request(xid=i).pack())
            self.controller.message_send(request)

        # Make sure the messages aren't executed
        msg, _ = self.controller.poll(ofp.message.echo_reply)
        self.assertIsNone(msg)

        request = ofp.message.bundle_ctrl_msg(
            bundle_ctrl_type=ofp.OFPBCT_COMMIT_REQUEST,
            bundle_id=1)

        response, _ = self.controller.transact(request)
        self.assertIsInstance(response, ofp.message.bundle_ctrl_msg)
        self.assertEqual(response.bundle_ctrl_type, ofp.OFPBCT_COMMIT_REPLY)
        self.assertEqual(response.bundle_id, 1)

        for i in xrange(0, 10):
            response, _ = self.controller.poll(ofp.message.echo_reply)
            self.assertIsNotNone(response)
            self.assertEquals(response.xid, i)

class Discard(base_tests.SimpleProtocol):
    """
    Verify that messages in a discarded bundle are not executed
    """
    def runTest(self):
        request = ofp.message.bundle_ctrl_msg(
            bundle_ctrl_type=ofp.OFPBCT_OPEN_REQUEST,
            bundle_id=1)

        response, _ = self.controller.transact(request)
        self.assertIsInstance(response, ofp.message.bundle_ctrl_msg)
        self.assertEqual(response.bundle_ctrl_type, ofp.OFPBCT_OPEN_REPLY)
        self.assertEqual(response.bundle_id, 1)

        for i in xrange(0, 10):
            request = ofp.message.bundle_add_msg(
                xid=i,
                bundle_id=1,
                data=ofp.message.echo_request(xid=i).pack())
            self.controller.message_send(request)

        # Make sure the messages aren't executed
        msg, _ = self.controller.poll(ofp.message.echo_reply)
        self.assertIsNone(msg)

        request = ofp.message.bundle_ctrl_msg(
            bundle_ctrl_type=ofp.OFPBCT_DISCARD_REQUEST,
            bundle_id=1)

        response, _ = self.controller.transact(request)
        self.assertIsInstance(response, ofp.message.bundle_ctrl_msg)
        self.assertEqual(response.bundle_ctrl_type, ofp.OFPBCT_DISCARD_REPLY)
        self.assertEqual(response.bundle_id, 1)

        # Make sure the messages aren't executed
        msg, _ = self.controller.poll(ofp.message.echo_reply)
        self.assertIsNone(msg)

class Disconnect(base_tests.SimpleProtocol):
    """
    Disconnect without explicitly discarding the bundle
    """
    def runTest(self):
        request = ofp.message.bundle_ctrl_msg(
            bundle_ctrl_type=ofp.OFPBCT_OPEN_REQUEST,
            bundle_id=1)

        response, _ = self.controller.transact(request)
        self.assertIsInstance(response, ofp.message.bundle_ctrl_msg)
        self.assertEqual(response.bundle_ctrl_type, ofp.OFPBCT_OPEN_REPLY)
        self.assertEqual(response.bundle_id, 1)

        for i in xrange(0, 10):
            request = ofp.message.bundle_add_msg(
                xid=i,
                bundle_id=1,
                data=ofp.message.echo_request(xid=i).pack())
            self.controller.message_send(request)

        # Disconnect without committing/discarding

class TooManyMsgs(base_tests.SimpleProtocol):
    """
    Verify that exactly 262144 messages can be added to a bundle

    This is tied to the limit in Indigo.
    """
    def runTest(self):
        request = ofp.message.bundle_ctrl_msg(
            bundle_ctrl_type=ofp.OFPBCT_OPEN_REQUEST,
            bundle_id=1)

        response, _ = self.controller.transact(request)
        self.assertIsInstance(response, ofp.message.bundle_ctrl_msg)
        self.assertEqual(response.bundle_ctrl_type, ofp.OFPBCT_OPEN_REPLY)
        self.assertEqual(response.bundle_id, 1)

        request = ofp.message.bundle_add_msg(
            xid=0,
            bundle_id=1,
            data=ofp.message.echo_request(xid=0).pack())

        buf = request.pack()

        logging.debug("Sending bundle-add messages")

        count = 0
        for i in xrange(0, 256*1024):
            with self.controller.tx_lock:
                if self.controller.switch_socket.sendall(buf) is not None:
                    raise AssertionError("failed to send message to switch")
            count += 1

        logging.debug("Sent %d bundle-add messages", count)

        do_barrier(self.controller)
        verify_no_errors(self.controller)

        request = ofp.message.bundle_add_msg(
            xid=1,
            bundle_id=1,
            data=ofp.message.echo_request(xid=1).pack())
        self.controller.message_send(request)

        do_barrier(self.controller)

        msg, _ = self.controller.poll(exp_msg=ofp.message.error_msg)
        self.assertIsNotNone(msg)

class TooManyBytes(base_tests.SimpleProtocol):
    """
    Verify that 50 MB of messages can be added to a bundle

    This is tied to the limit in Indigo.
    """
    def runTest(self):
        request = ofp.message.bundle_ctrl_msg(
            bundle_ctrl_type=ofp.OFPBCT_OPEN_REQUEST,
            bundle_id=1)

        response, _ = self.controller.transact(request)
        self.assertIsInstance(response, ofp.message.bundle_ctrl_msg)
        self.assertEqual(response.bundle_ctrl_type, ofp.OFPBCT_OPEN_REPLY)
        self.assertEqual(response.bundle_id, 1)

        echo_buf = ofp.message.echo_request(xid=0, data="\x00" * 1016).pack()
        self.assertEquals(len(echo_buf), 1024)

        request = ofp.message.bundle_add_msg(
            xid=0,
            bundle_id=1,
            data=echo_buf)

        buf = request.pack()

        max_bytes = 50*1024*1024
        num_msgs = max_bytes / len(echo_buf)

        logging.debug("Sending bundle-add messages")

        count = 0
        for i in xrange(0, num_msgs):
            with self.controller.tx_lock:
                if self.controller.switch_socket.sendall(buf) is not None:
                    raise AssertionError("failed to send message to switch")
            count += 1

        logging.debug("Sent %d bundle-add messages", count)

        do_barrier(self.controller)
        verify_no_errors(self.controller)

        request = ofp.message.bundle_add_msg(
            xid=1,
            bundle_id=1,
            data=ofp.message.echo_request(xid=1).pack())
        self.controller.message_send(request)

        do_barrier(self.controller)

        msg, _ = self.controller.poll(exp_msg=ofp.message.error_msg)
        self.assertIsNotNone(msg)
