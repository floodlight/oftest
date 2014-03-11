# Distributed under the OpenFlow Software License (see LICENSE)
# Copyright (c) 2014 Big Switch Networks, Inc.
"""
BSN flow checksum extension test cases
"""

import logging
import math
import random

from oftest import config
import oftest.base_tests as base_tests
import ofp

from oftest.testutils import *

TABLE_ID = 0

def make_checksum(hi, lo):
    """
    Place 'hi' in the upper 8 bits and 'lo' in the lower bits.
    """
    return ((hi & 0xff) << 56) | lo

assert make_checksum(0xab, 0xcd) == 0xab000000000000cd

def shuffled(seq):
    l = list(seq)[:]
    random.shuffle(l)
    return l

class FlowChecksumBase(base_tests.SimpleProtocol):
    """
    Base class that maintains the expected table and bucket checksums
    """
    checksum_buckets = None
    table_checksum = None
    all_checksums = []

    def get_table_checksum(self):
        for entry in get_stats(self, ofp.message.bsn_table_checksum_stats_request()):
            if entry.table_id == TABLE_ID:
                return entry.checksum
        return None

    def get_checksum_buckets(self):
        stats = get_stats(self,
            ofp.message.bsn_flow_checksum_bucket_stats_request(table_id=TABLE_ID))
        return [x.checksum for x in stats]

    def verify_checksums(self):
        self.assertEquals(self.get_table_checksum(), self.table_checksum)
        self.assertEquals(self.get_checksum_buckets(), self.checksum_buckets)

    def update_checksums(self, checksum):
        self.table_checksum ^= checksum
        checksum_shift = 64 - int(math.log(len(self.checksum_buckets), 2))
        self.checksum_buckets[checksum >> checksum_shift] ^= checksum

    def insert_checksum(self, checksum):
        self.update_checksums(checksum)
        self.all_checksums.append(checksum)

    def remove_checksum(self, checksum):
        self.update_checksums(checksum)
        self.all_checksums.remove(checksum)

    def set_buckets_size(self, buckets_size):
        self.controller.message_send(
            ofp.message.bsn_table_set_buckets_size(
                table_id=TABLE_ID, buckets_size=buckets_size))
        do_barrier(self.controller)
        verify_no_errors(self.controller)

        self.checksum_buckets = [0] * buckets_size
        self.table_checksum = 0
        for checksum in self.all_checksums:
            self.update_checksums(checksum)

class FlowChecksum(FlowChecksumBase):
    """
    Test flow checksum buckets and table checksums
    """
    def runTest(self):
        delete_all_flows(self.controller)

        # Deleted all flows, table checksum should be 0
        self.assertEquals(self.get_table_checksum(), 0)

        self.set_buckets_size(8)
        self.verify_checksums()

        # Interesting checksums
        checksums = [
            make_checksum(0, 1),
            make_checksum(0, 2),
            make_checksum(1, 0xab),
            make_checksum(1, 0xab),
            make_checksum(7, 0xff),
            make_checksum(7, 0xaa),
        ]

        # Random checksums
        for _ in xrange(0, 8):
            checksums.append(random.randint(0, 2**64-1))

        # Add flows in random order
        for i, checksum in shuffled(enumerate(checksums)):
            self.insert_checksum(checksum)
            request = ofp.message.flow_add(
                table_id=TABLE_ID,
                cookie=checksum,
                buffer_id=ofp.OFP_NO_BUFFER,
                priority=i)
            self.controller.message_send(request)
            do_barrier(self.controller)
            verify_no_errors(self.controller)
            self.verify_checksums()

        # Delete flows in random order
        for i, checksum in shuffled(enumerate(checksums)):
            self.remove_checksum(checksum)
            request = ofp.message.flow_delete_strict(
                table_id=TABLE_ID,
                priority=i,
                out_port=ofp.OFPP_ANY,
                out_group=ofp.OFPG_ANY)
            self.controller.message_send(request)
            do_barrier(self.controller)
            verify_no_errors(self.controller)
            self.verify_checksums()

        # Deleted all flows, table checksum should be 0
        self.assertEquals(self.get_table_checksum(), 0)

class Resize(FlowChecksumBase):
    """
    Resize the checksum buckets, checking limits and redistribution
    """
    def runTest(self):
        delete_all_flows(self.controller)

        self.assertEquals(self.get_table_checksum(), 0)

        self.set_buckets_size(128)
        self.verify_checksums()

        checksums = [random.randint(0, 2**64-1) for _ in xrange(0, 128)]

        # Add flows
        for i, checksum in enumerate(checksums):
            self.insert_checksum(checksum)
            request = ofp.message.flow_add(
                table_id=TABLE_ID,
                cookie=checksum,
                buffer_id=ofp.OFP_NO_BUFFER,
                priority=i)
            self.controller.message_send(request)
            if i % 17 == 0:
                do_barrier(self.controller)
                verify_no_errors(self.controller)
                self.verify_checksums()

        do_barrier(self.controller)
        verify_no_errors(self.controller)
        self.verify_checksums()

        # Shrink checksum buckets
        self.set_buckets_size(64)
        self.verify_checksums()

        # Shrink checksum buckets to minimum
        self.set_buckets_size(1)
        self.verify_checksums()

        # Grow checksum buckets
        self.set_buckets_size(2)
        self.verify_checksums()

        # Grow checksum buckets
        self.set_buckets_size(256)
        self.verify_checksums()

        # Grow checksum buckets to maximum
        self.set_buckets_size(65536)
        self.verify_checksums()

        # Delete flows
        for i, checksum in enumerate(checksums):
            self.remove_checksum(checksum)
            request = ofp.message.flow_delete_strict(
                table_id=TABLE_ID,
                priority=i,
                out_port=ofp.OFPP_ANY,
                out_group=ofp.OFPG_ANY)
            self.controller.message_send(request)
            if i % 17 == 0:
                do_barrier(self.controller)
                verify_no_errors(self.controller)
                self.verify_checksums()

        do_barrier(self.controller)
        verify_no_errors(self.controller)
        self.verify_checksums()

        # Deleted all flows, table checksum should be 0
        self.assertEquals(self.get_table_checksum(), 0)

class ResizeError(FlowChecksumBase):
    """
    Check that the switch rejects invalid checksum buckets sizes
    """
    def runTest(self):
        # buckets_size = 0
        self.controller.message_send(
            ofp.message.bsn_table_set_buckets_size(
                table_id=TABLE_ID, buckets_size=0))
        do_barrier(self.controller)
        error, _ = self.controller.poll(ofp.OFPT_ERROR)
        self.assertIsInstance(error, ofp.message.error_msg)

        # buckets_size = 3
        self.controller.message_send(
            ofp.message.bsn_table_set_buckets_size(
                table_id=TABLE_ID, buckets_size=3))
        do_barrier(self.controller)
        error, _ = self.controller.poll(ofp.OFPT_ERROR)
        self.assertIsInstance(error, ofp.message.error_msg)

        # buckets_size = 100
        self.controller.message_send(
            ofp.message.bsn_table_set_buckets_size(
                table_id=TABLE_ID, buckets_size=100))
        do_barrier(self.controller)
        error, _ = self.controller.poll(ofp.OFPT_ERROR)
        self.assertIsInstance(error, ofp.message.error_msg)

        # buckets_size = 2**32 - 1
        self.controller.message_send(
            ofp.message.bsn_table_set_buckets_size(
                table_id=TABLE_ID, buckets_size=2**32-1))
        do_barrier(self.controller)
        error, _ = self.controller.poll(ofp.OFPT_ERROR)
        self.assertIsInstance(error, ofp.message.error_msg)

        # buckets_size = 2**31
        self.controller.message_send(
            ofp.message.bsn_table_set_buckets_size(
                table_id=TABLE_ID, buckets_size=2**31))
        do_barrier(self.controller)
        error, _ = self.controller.poll(ofp.OFPT_ERROR)
        self.assertIsInstance(error, ofp.message.error_msg)
