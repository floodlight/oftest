# Distributed under the OpenFlow Software License (see LICENSE)
# Copyright (c) 2012, 2013 Big Switch Networks, Inc.
"""
BSN gentable extension test cases
"""

import logging
import math
import random

from oftest import config
import oftest.base_tests as base_tests
import ofp

from oftest.testutils import *

# Hardcoded in the switch to ease testing
TABLE_ID = 0

def tlv_dict(tlvs):
    d = {}
    for tlv in tlvs:
        d[tlv.__class__] = tlv.value
    return d

def make_checksum(hi, lo):
    """
    Place 'hi' in the upper 8 bits and 'lo' in the lower bits.
    """
    return ((hi & 0xff) << 120) | lo

assert make_checksum(0xab, 0xcd) == 0xab0000000000000000000000000000cd

def add_checksum(a, b):
    return (a + b) % 2**128

def subtract_checksum(a, b):
    return (a - b) % 2**128

def bucket_index(num_buckets, checksum):
    """
    Use the top bits of the checksum to select a bucket index
    """
    return checksum >> (128 - int(math.log(num_buckets, 2)))

def add_bucket_checksum(buckets, checksum):
    """
    Add the checksum to the correct bucket
    """
    index = bucket_index(len(buckets), checksum)
    buckets[index] = add_checksum(buckets[index], checksum)

def subtract_bucket_checksum(buckets, checksum):
    """
    Subtract the checksum from the correct bucket
    """
    index = bucket_index(len(buckets), checksum)
    buckets[index] = subtract_checksum(buckets[index], checksum)

class BaseGenTableTest(base_tests.SimpleProtocol):
    def setUp(self):
        base_tests.SimpleProtocol.setUp(self)
        self.do_clear()

    def tearDown(self):
        self.do_clear()
        base_tests.SimpleProtocol.tearDown(self)

    def do_clear(self, checksum=0, checksum_mask=0):
        request = ofp.message.bsn_gentable_clear_request(
            table_id=TABLE_ID,
            checksum=checksum,
            checksum_mask=checksum_mask)
        response, _ = self.controller.transact(request)
        self.assertIsInstance(response, ofp.message.bsn_gentable_clear_reply)
        return response.deleted_count, response.error_count

    def do_add(self, vlan_vid, ipv4, mac, idle_notification=False, checksum=0):
        msg = ofp.message.bsn_gentable_entry_add(
            table_id=TABLE_ID,
            key=[
                ofp.bsn_tlv.vlan_vid(vlan_vid),
                ofp.bsn_tlv.ipv4(ipv4)],
            value=[
                ofp.bsn_tlv.mac(mac)],
            checksum=checksum)
        if idle_notification:
            msg.value.append(ofp.bsn_tlv.idle_notification())
        self.controller.message_send(msg)

    def do_delete(self, vlan_vid, ipv4):
        msg = ofp.message.bsn_gentable_entry_delete(
            table_id=TABLE_ID,
            key=[
                ofp.bsn_tlv.vlan_vid(vlan_vid),
                ofp.bsn_tlv.ipv4(ipv4)])
        self.controller.message_send(msg)

    def do_entry_stats(self, checksum=0, checksum_mask=0):
        request = ofp.message.bsn_gentable_entry_stats_request(
            table_id=TABLE_ID,
            checksum=checksum,
            checksum_mask=checksum_mask)
        return get_stats(self, request)

    def do_entry_desc_stats(self, checksum=0, checksum_mask=0):
        request = ofp.message.bsn_gentable_entry_desc_stats_request(
            table_id=TABLE_ID,
            checksum=checksum,
            checksum_mask=checksum_mask)
        return get_stats(self, request)

    def do_table_desc_stats(self):
        request = ofp.message.bsn_gentable_desc_stats_request()
        return get_stats(self, request)

    def do_table_stats(self):
        request = ofp.message.bsn_gentable_stats_request()
        return get_stats(self, request)

    def do_test_table_stats(self):
        entries = self.do_table_stats()
        for entry in entries:
            if entry.table_id == TABLE_ID:
                return entry
        raise AssertionError("did not find test table")

    def do_bucket_stats(self):
        request = ofp.message.bsn_gentable_bucket_stats_request(table_id=TABLE_ID)
        return get_stats(self, request)

    def do_set_buckets_size(self, buckets_size):
        msg = ofp.message.bsn_gentable_set_buckets_size(
            table_id=TABLE_ID,
            buckets_size=buckets_size)
        self.controller.message_send(msg)

class ClearAll(BaseGenTableTest):
    """
    Test clearing entire table
    """
    def runTest(self):
        # Add a few entries
        for i in range(0, 3):
            self.do_add(vlan_vid=i, ipv4=0x12345678, mac=(0, 1, 2, 3, 4, i))

        do_barrier(self.controller)
        verify_no_errors(self.controller)

        # Delete all entries
        deleted, errors = self.do_clear(checksum=0, checksum_mask=0)
        self.assertEquals(deleted, 3)
        self.assertEquals(errors, 0)

class ClearMasked(BaseGenTableTest):
    """
    Test clearing with a checksum mask
    """
    def runTest(self):
        # Add 4 entries to each checksum bucket
        for i in range(0, 256):
            self.do_add(vlan_vid=i, ipv4=0x12345678, mac=(0, 1, 2, 3, 4, i),
                        checksum=make_checksum(i, i*31))

        do_barrier(self.controller)
        verify_no_errors(self.controller)

        # Delete bucket 0
        deleted, errors = self.do_clear(make_checksum(0, 0), make_checksum(0xFC, 0))
        self.assertEquals(deleted, 4)
        self.assertEquals(errors, 0)

        # Delete buckets 0 (already cleared), 1, 2, 3
        deleted, errors = self.do_clear(make_checksum(0, 0), make_checksum(0xF0, 0))
        self.assertEquals(deleted, 12)
        self.assertEquals(errors, 0)

        # Delete second half of bucket 4
        deleted, errors = self.do_clear(make_checksum(0x10, 0), make_checksum(0xFE, 0))
        self.assertEquals(deleted, 2)
        self.assertEquals(errors, 0)

class AddDelete(BaseGenTableTest):
    """
    Test adding and deleting entries
    """
    def runTest(self):
        # Add a few entries
        for i in range(0, 3):
            self.do_add(vlan_vid=i, ipv4=0x12345678, mac=(0, 1, 2, 3, 4, i))

        do_barrier(self.controller)
        verify_no_errors(self.controller)

        # Delete each entry
        for i in range(0, 3):
            self.do_delete(vlan_vid=i, ipv4=0x12345678)

        do_barrier(self.controller)
        verify_no_errors(self.controller)

        # Clear table, but expect it to have already been empty
        request = ofp.message.bsn_gentable_clear_request(table_id=TABLE_ID)
        response, _ = self.controller.transact(request)
        self.assertIsInstance(response, ofp.message.bsn_gentable_clear_reply)
        self.assertEquals(response.error_count, 0)
        self.assertEquals(response.deleted_count, 0)

class EntryStats(BaseGenTableTest):
    """
    Test retrieving entry stats
    """
    def runTest(self):
        # Add a few entries
        for i in range(0, 3):
            self.do_add(vlan_vid=i, ipv4=0x12345678, mac=(0, 1, 2, 3, 4, i))

        do_barrier(self.controller)
        verify_no_errors(self.controller)

        entries = self.do_entry_stats()
        seen = set()
        for entry in entries:
            logging.debug(entry.show())
            key = tlv_dict(entry.key)
            stats = tlv_dict(entry.stats)
            self.assertIn(ofp.bsn_tlv.vlan_vid, key)
            self.assertIn(ofp.bsn_tlv.ipv4, key)
            self.assertIn(ofp.bsn_tlv.rx_packets, stats)
            self.assertIn(ofp.bsn_tlv.tx_packets, stats)
            vlan_vid = key[ofp.bsn_tlv.vlan_vid]
            seen.add(vlan_vid)
            self.assertEqual(key[ofp.bsn_tlv.ipv4], 0x12345678)
            self.assertEqual(stats[ofp.bsn_tlv.rx_packets], 100 * vlan_vid)
            self.assertEqual(stats[ofp.bsn_tlv.tx_packets], 101 * vlan_vid)

        self.assertEquals(seen, set([0, 1, 2]))

class EntryStatsMasked(BaseGenTableTest):
    """
    Test retrieving entry stats with a checksum mask
    """
    def runTest(self):
        def get_range(checksum, checksum_mask):
            entries = self.do_entry_stats(checksum, checksum_mask)
            vlan_vids = []
            for entry in entries:
                key = tlv_dict(entry.key)
                vlan_vids.append(key[ofp.bsn_tlv.vlan_vid])
            return sorted(vlan_vids)

        # Add 4 entries to each checksum bucket
        for i in range(0, 256):
            self.do_add(vlan_vid=i, ipv4=0x12345678, mac=(0, 1, 2, 3, 4, i),
                        checksum=make_checksum(i, i))

        do_barrier(self.controller)
        verify_no_errors(self.controller)

        # Check first bucket
        self.assertEquals(get_range(make_checksum(0, 0), make_checksum(0xFC, 0)),
                          [0, 1, 2, 3])

        # Check last bucket
        self.assertEquals(get_range(make_checksum(0xFC, 0), make_checksum(0xFC, 0)),
                          [252, 253, 254, 255])

        # Check first half of first bucket
        self.assertEquals(get_range(make_checksum(0x00, 0), make_checksum(0xFE, 0)),
                          [0, 1])

        # Check second half of first bucket
        self.assertEquals(get_range(make_checksum(0x02, 0), make_checksum(0xFE, 0)),
                          [2, 3])

        # Check first half of last bucket
        self.assertEquals(get_range(make_checksum(0xFC, 0), make_checksum(0xFE, 0)),
                          [252, 253])

        # Check second half of last bucket
        self.assertEquals(get_range(make_checksum(0xFE, 0), make_checksum(0xFE, 0)),
                          [254, 255])

        # Check first two buckets
        self.assertEquals(get_range(make_checksum(0, 0), make_checksum(0xF8, 0)),
                          [0, 1, 2, 3, 4, 5, 6, 7])

        # Check last two buckets
        self.assertEquals(get_range(make_checksum(0xF8, 0), make_checksum(0xF8, 0)),
                          [248, 249, 250, 251, 252, 253, 254, 255])

        # Check matching on low bits
        self.assertEquals(get_range(make_checksum(0x00, 0x00), ~1), [0])
        self.assertEquals(get_range(make_checksum(0x01, 0x00), ~1), [1])
        self.assertEquals(get_range(make_checksum(0x01, 0x02), ~1), [])

class EntryStatsFragmented(BaseGenTableTest):
    """
    Test retrieving entry stats in mutiple replies
    """
    def runTest(self):
        # Add a bunch of entries
        # Enough for 3 stats replies
        for i in range(0, 4095):
            self.do_add(vlan_vid=i, ipv4=0x12345678, mac=(0, 1, 2, 3, 4, 5))

        do_barrier(self.controller)
        verify_no_errors(self.controller)

        entries = self.do_entry_stats()
        seen = set()
        for entry in entries:
            key = tlv_dict(entry.key)
            vlan_vid = key[ofp.bsn_tlv.vlan_vid]
            self.assertNotIn(vlan_vid, seen)
            seen.add(vlan_vid)

        self.assertEquals(seen, set(range(0, 4095)))

class EntryDescStats(BaseGenTableTest):
    """
    Test retrieving entry desc stats
    """
    def runTest(self):
        # Add a few entries
        for i in range(0, 3):
            self.do_add(vlan_vid=i, ipv4=0x12345678, mac=(0, 1, 2, 3, 4, i),
                        checksum=0xfedcba9876543210fedcba9876543210 + i)

        do_barrier(self.controller)
        verify_no_errors(self.controller)

        entries = self.do_entry_desc_stats()
        seen = set()
        for entry in entries:
            logging.debug(entry.show())
            key = tlv_dict(entry.key)
            value = tlv_dict(entry.value)
            self.assertIn(ofp.bsn_tlv.vlan_vid, key)
            self.assertIn(ofp.bsn_tlv.ipv4, key)
            self.assertIn(ofp.bsn_tlv.mac, value)
            vlan_vid = key[ofp.bsn_tlv.vlan_vid]
            seen.add(vlan_vid)
            self.assertEqual(key[ofp.bsn_tlv.ipv4], 0x12345678)
            self.assertEqual(value[ofp.bsn_tlv.mac], [0, 1, 2, 3, 4, vlan_vid])
            self.assertEqual(entry.checksum, 0xfedcba9876543210fedcba9876543210 + vlan_vid)

        self.assertEquals(seen, set([0, 1, 2]))

class EntryDescStatsMasked(BaseGenTableTest):
    """
    Test retrieving entry desc stats with a checksum mask
    """
    def runTest(self):
        def get_range(checksum, checksum_mask):
            entries = self.do_entry_desc_stats(checksum, checksum_mask)
            vlan_vids = []
            for entry in entries:
                key = tlv_dict(entry.key)
                vlan_vids.append(key[ofp.bsn_tlv.vlan_vid])
            return sorted(vlan_vids)

        # Add 4 entries to each checksum bucket
        for i in range(0, 256):
            self.do_add(vlan_vid=i, ipv4=0x12345678, mac=(0, 1, 2, 3, 4, i),
                        checksum=make_checksum(i, i))

        do_barrier(self.controller)
        verify_no_errors(self.controller)

        # Check first bucket
        self.assertEquals(get_range(make_checksum(0, 0), make_checksum(0xFC, 0)),
                          [0, 1, 2, 3])

        # Check last bucket
        self.assertEquals(get_range(make_checksum(0xFC, 0), make_checksum(0xFC, 0)),
                          [252, 253, 254, 255])

        # Check first half of first bucket
        self.assertEquals(get_range(make_checksum(0x00, 0), make_checksum(0xFE, 0)),
                          [0, 1])

        # Check second half of first bucket
        self.assertEquals(get_range(make_checksum(0x02, 0), make_checksum(0xFE, 0)),
                          [2, 3])

        # Check first half of last bucket
        self.assertEquals(get_range(make_checksum(0xFC, 0), make_checksum(0xFE, 0)),
                          [252, 253])

        # Check second half of last bucket
        self.assertEquals(get_range(make_checksum(0xFE, 0), make_checksum(0xFE, 0)),
                          [254, 255])

        # Check first two buckets
        self.assertEquals(get_range(make_checksum(0, 0), make_checksum(0xF8, 0)),
                          [0, 1, 2, 3, 4, 5, 6, 7])

        # Check last two buckets
        self.assertEquals(get_range(make_checksum(0xF8, 0), make_checksum(0xF8, 0)),
                          [248, 249, 250, 251, 252, 253, 254, 255])

        # Check matching on low bits
        self.assertEquals(get_range(make_checksum(0x00, 0x00), ~1), [0])
        self.assertEquals(get_range(make_checksum(0x01, 0x00), ~1), [1])
        self.assertEquals(get_range(make_checksum(0x01, 0x02), ~1), [])

class EntryDescStatsFragmented(BaseGenTableTest):
    """
    Test retrieving entry stats in mutiple replies
    """
    def runTest(self):
        # Add a bunch of entries
        # Enough for 3 stats replies
        for i in range(0, 4095):
            self.do_add(vlan_vid=i, ipv4=0x12345678, mac=(0, 1, 2, 3, 4, 5))

        do_barrier(self.controller)
        verify_no_errors(self.controller)

        entries = self.do_entry_desc_stats()
        seen = set()
        for entry in entries:
            key = tlv_dict(entry.key)
            vlan_vid = key[ofp.bsn_tlv.vlan_vid]
            self.assertNotIn(vlan_vid, seen)
            seen.add(vlan_vid)

        self.assertEquals(seen, set(range(0, 4095)))

class TableDescStats(BaseGenTableTest):
    """
    Test retrieving table desc stats
    """
    def runTest(self):
        entries = self.do_table_desc_stats()
        seen = set()
        for entry in entries:
            logging.debug(entry.show())
            self.assertNotIn(entry.table_id, seen)
            self.assertNotIn(entry.name, seen)
            seen.add(entry.table_id)
            seen.add(entry.name)
            if entry.table_id == TABLE_ID:
                self.assertEqual(entry.name, "test")
                self.assertEqual(entry.buckets_size, 64)
                self.assertEqual(entry.max_entries, 1000)

        self.assertIn(TABLE_ID, seen)

class TableStats(BaseGenTableTest):
    """
    Test retrieving table stats
    """
    def runTest(self):
        # Verify we have the test table and no duplicates
        entries = self.do_table_stats()
        seen = set()
        for entry in entries:
            logging.debug(entry.show())
            self.assertNotIn(entry.table_id, seen)
            seen.add(entry.table_id)
            if entry.table_id == TABLE_ID:
                self.assertEqual(entry.entry_count, 0)
                self.assertEqual(entry.checksum, 0)
        self.assertIn(TABLE_ID, seen)

        table_checksum = 0

        # Add a bunch of entries, spread among the checksum buckets
        for i in range(0, 256):
            table_checksum = add_checksum(table_checksum, make_checksum(i, i*31))
            self.do_add(vlan_vid=i, ipv4=0x12345678, mac=(0, 1, 2, 3, 4, i),
                        checksum=make_checksum(i, i*31))

        do_barrier(self.controller)
        verify_no_errors(self.controller)

        table_stats = self.do_test_table_stats()
        self.assertEqual(table_stats.entry_count, 256)
        self.assertEqual(table_stats.checksum, table_checksum)

        # Modify an entry, changing its checksum
        i = 30
        table_checksum = subtract_checksum(table_checksum, make_checksum(i, i*31)) # subtract old checksum
        table_checksum = add_checksum(table_checksum, make_checksum(i, i*37)) # add new checksum
        self.do_add(vlan_vid=i, ipv4=0x12345678, mac=(0, 4, 3, 2, 1, i),
                    checksum=make_checksum(i, i*37))

        do_barrier(self.controller)
        verify_no_errors(self.controller)

        table_stats = self.do_test_table_stats()
        self.assertEqual(table_stats.entry_count, 256)
        self.assertEqual(table_stats.checksum, table_checksum)

        # Delete an entry
        i = 87
        table_checksum = subtract_checksum(table_checksum, make_checksum(i, i*31))
        self.do_delete(vlan_vid=i, ipv4=0x12345678)

        do_barrier(self.controller)
        verify_no_errors(self.controller)

        table_stats = self.do_test_table_stats()
        self.assertEqual(table_stats.entry_count, 255)
        self.assertEqual(table_stats.checksum, table_checksum)

class BucketStats(BaseGenTableTest):
    """
    Test retrieving checksum bucket stats
    """
    def runTest(self):
        # Verify initial state
        entries = self.do_bucket_stats()
        self.assertEquals(len(entries), 64)
        for entry in entries:
            self.assertEquals(entry.checksum, 0)

        buckets = [0] * len(entries)

        # Add a bunch of entries, spread among the checksum buckets
        for i in range(0, 256):
            add_bucket_checksum(buckets, make_checksum(i, i*31))
            self.do_add(vlan_vid=i, ipv4=0x12345678, mac=(0, 1, 2, 3, 4, i),
                        checksum=make_checksum(i, i*31))

        entries = self.do_bucket_stats()
        self.assertEquals(len(entries), 64)
        for i, entry in enumerate(entries):
            self.assertEquals(entry.checksum, buckets[i])

        # Modify an entry, changing its checksum
        i = 30
        subtract_bucket_checksum(buckets, make_checksum(i, i*31)) # subtract old checksum
        add_bucket_checksum(buckets, make_checksum(i, i*37)) # add new checksum
        self.do_add(vlan_vid=i, ipv4=0x12345678, mac=(0, 4, 3, 2, 1, i),
                    checksum=make_checksum(i, i*37))

        do_barrier(self.controller)
        verify_no_errors(self.controller)

        entries = self.do_bucket_stats()
        self.assertEquals(len(entries), 64)
        for i, entry in enumerate(entries):
            self.assertEquals(entry.checksum, buckets[i])

        # Delete an entry
        i = 87
        subtract_bucket_checksum(buckets, make_checksum(i, i*31))
        self.do_delete(vlan_vid=i, ipv4=0x12345678)

        do_barrier(self.controller)
        verify_no_errors(self.controller)

        entries = self.do_bucket_stats()
        self.assertEquals(len(entries), 64)
        for i, entry in enumerate(entries):
            self.assertEquals(entry.checksum, buckets[i])

class BucketStatsFragmented(BaseGenTableTest):
    """
    Test retrieving checksum bucket stats in multiple replies
    """

    def tearDown(self):
        self.do_set_buckets_size(64)
        do_barrier(self.controller)
        BaseGenTableTest.tearDown(self)

    def runTest(self):
        # Enough for 3 stats messages
        self.do_set_buckets_size(8192)
        do_barrier(self.controller)
        verify_no_errors(self.controller)

        entries = self.do_bucket_stats()
        self.assertEquals(len(entries), 8192)

class SetBucketsSize(BaseGenTableTest):
    """
    Test setting the checksum buckets size
    """
    def setUp(self):
        BaseGenTableTest.setUp(self)
        self.do_set_buckets_size(64)
        do_barrier(self.controller)

    def tearDown(self):
        self.do_set_buckets_size(64)
        do_barrier(self.controller)
        BaseGenTableTest.tearDown(self)

    def runTest(self):
        # Verify initial state
        entries = self.do_bucket_stats()
        self.assertEquals(len(entries), 64)
        for entry in entries:
            self.assertEquals(entry.checksum, 0)

        buckets32 = [0] * 32
        buckets64 = [0] * 64

        # Add a bunch of entries, spread among the checksum buckets
        for i in range(0, 256):
            checksum = make_checksum(i, i*31)
            add_bucket_checksum(buckets32, checksum)
            add_bucket_checksum(buckets64, checksum)
            self.do_add(vlan_vid=i, ipv4=0x12345678, mac=(0, 1, 2, 3, 4, i),
                        checksum=checksum)

        entries = self.do_bucket_stats()
        self.assertEquals(len(entries), 64)
        for i, entry in enumerate(entries):
            self.assertEquals(entry.checksum, buckets64[i])

        self.do_set_buckets_size(32)
        do_barrier(self.controller)

        entries = self.do_bucket_stats()
        self.assertEquals(len(entries), 32)
        for i, entry in enumerate(entries):
            self.assertEquals(entry.checksum, buckets32[i])

        self.do_set_buckets_size(64)
        do_barrier(self.controller)

        entries = self.do_bucket_stats()
        self.assertEquals(len(entries), 64)
        for i, entry in enumerate(entries):
            self.assertEquals(entry.checksum, buckets64[i])

class SetBucketsSizeError(BaseGenTableTest):
    """
    Test error cases in setting the checksum buckets size
    """
    def setUp(self):
        BaseGenTableTest.setUp(self)
        self.do_set_buckets_size(64)
        do_barrier(self.controller)

    def tearDown(self):
        self.do_set_buckets_size(64)
        do_barrier(self.controller)
        BaseGenTableTest.tearDown(self)

    def runTest(self):
        # Zero buckets size
        self.do_set_buckets_size(0)
        do_barrier(self.controller)

        error, _ = self.controller.poll(ofp.OFPT_ERROR, 0)
        self.assertIsInstance(error, ofp.message.bad_request_error_msg)
        self.assertEquals(error.code, ofp.OFPBRC_EPERM)

        # Non power of 2 buckets size
        self.do_set_buckets_size(7)
        do_barrier(self.controller)

        error, _ = self.controller.poll(ofp.OFPT_ERROR, 0)
        self.assertIsInstance(error, ofp.message.bad_request_error_msg)
        self.assertEquals(error.code, ofp.OFPBRC_EPERM)

class AddError(BaseGenTableTest):
    """
    Test failure adding entries
    """
    def runTest(self):
        # Invalid key
        self.do_add(vlan_vid=10000, ipv4=0x12345678, mac=(0, 1, 2, 3, 4, 5))
        do_barrier(self.controller)

        error, _ = self.controller.poll(ofp.OFPT_ERROR, 0)
        self.assertIsInstance(error, ofp.message.bad_request_error_msg)
        self.assertEquals(error.code, ofp.OFPBRC_EPERM)

        self.assertEquals(len(self.do_entry_desc_stats()), 0)

        # Invalid value
        self.do_add(vlan_vid=100, ipv4=0x12345678, mac=(1, 1, 2, 3, 4, 5))
        do_barrier(self.controller)

        error, _ = self.controller.poll(ofp.OFPT_ERROR, 0)
        self.assertIsInstance(error, ofp.message.bad_request_error_msg)
        self.assertEquals(error.code, ofp.OFPBRC_EPERM)

        self.assertEquals(len(self.do_entry_desc_stats()), 0)

class ModifyError(BaseGenTableTest):
    """
    Test failure modifying entries
    """
    def runTest(self):
        # Add a valid entry we'll try to modify
        self.do_add(vlan_vid=100, ipv4=0x12345678, mac=(0, 1, 2, 3, 4, 5))
        do_barrier(self.controller)
        verify_no_errors(self.controller)

        orig_entries = self.do_entry_desc_stats()
        self.assertEquals(len(orig_entries), 1)

        # Invalid value
        self.do_add(vlan_vid=100, ipv4=0x12345678, mac=(1, 1, 2, 3, 4, 5))
        do_barrier(self.controller)

        error, _ = self.controller.poll(ofp.OFPT_ERROR, 0)
        self.assertIsInstance(error, ofp.message.bad_request_error_msg)
        self.assertEquals(error.code, ofp.OFPBRC_EPERM)

        # Check that the table wasn't modified
        new_entries = self.do_entry_desc_stats()
        self.assertEquals(len(new_entries), 1)
        self.assertEquals(new_entries, orig_entries)

class DeleteNonexistentError(BaseGenTableTest):
    """
    Test failure deleting a nonexistent entry
    """
    def runTest(self):
        self.do_delete(vlan_vid=1000, ipv4=0x12345678)
        do_barrier(self.controller)

        error, _ = self.controller.poll(ofp.OFPT_ERROR, 0)
        self.assertEquals(error, None)

class DeleteFailureError(BaseGenTableTest):
    """
    Test failure deleting a nonexistent entry

    The very special idle_notification TLV will cause the entry to fail
    being deleted the first time. This behavior is only there to help
    test this error path.
    """
    def runTest(self):
        self.do_add(vlan_vid=1000, ipv4=0x12345678,
                    mac=(0, 1, 2, 3, 4, 5), idle_notification=True)
        do_barrier(self.controller)
        verify_no_errors(self.controller)

        orig_entries = self.do_entry_desc_stats()
        self.assertEquals(len(orig_entries), 1)

        # This will fail
        self.do_delete(vlan_vid=1000, ipv4=0x12345678)
        do_barrier(self.controller)

        error, _ = self.controller.poll(ofp.OFPT_ERROR, 0)
        self.assertIsInstance(error, ofp.message.bad_request_error_msg)
        self.assertEquals(error.code, ofp.OFPBRC_EPERM)

        # Check that the table wasn't modified
        new_entries = self.do_entry_desc_stats()
        self.assertEquals(len(new_entries), 1)
        self.assertEquals(new_entries, orig_entries)

        # This will succeed
        self.do_delete(vlan_vid=1000, ipv4=0x12345678)
        do_barrier(self.controller)
        verify_no_errors(self.controller)

class BadTableIdError(BaseGenTableTest):
    """
    Test failure of each message when specifying a nonexistent table id
    """
    def runTest(self):
        def check_error(msg):
            reply, _ = self.controller.transact(msg)
            self.assertIsInstance(reply, ofp.message.bad_request_error_msg)
            self.assertEquals(reply.code, ofp.OFPBRC_BAD_TABLE_ID)

        valid_table_ids = set([x.table_id for x in self.do_table_desc_stats()])
        invalid_table_id = TABLE_ID
        while invalid_table_id in valid_table_ids:
            invalid_table_id = random.randrange(65536)

        logging.debug("Using invalid table id %d", invalid_table_id)

        check_error(ofp.message.bsn_gentable_clear_request(
            table_id=invalid_table_id))

        check_error(ofp.message.bsn_gentable_entry_add(
            table_id=invalid_table_id))

        check_error(ofp.message.bsn_gentable_entry_delete(
            table_id=invalid_table_id))

        check_error(ofp.message.bsn_gentable_entry_stats_request(
            table_id=invalid_table_id))

        check_error(ofp.message.bsn_gentable_entry_desc_stats_request(
            table_id=invalid_table_id))

        check_error(ofp.message.bsn_gentable_bucket_stats_request(
            table_id=invalid_table_id))

        check_error(ofp.message.bsn_gentable_set_buckets_size(
            table_id=invalid_table_id))
