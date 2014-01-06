# Distributed under the OpenFlow Software License (see LICENSE)
# Copyright (c) 2012, 2013 Big Switch Networks, Inc.
"""
BSN gentable extension test cases
"""

import logging

from oftest import config
import oftest.base_tests as base_tests
import ofp

from oftest.testutils import *

# Hardcoded in the switch to ease testing
TABLE_ID = 0

class BaseGenTableTest(base_tests.SimpleProtocol):
    def setUp(self):
        base_tests.SimpleProtocol.setUp(self)
        self.clear()

    def tearDown(self):
        self.clear()
        base_tests.SimpleProtocol.tearDown(self)

    def clear(self):
        request = ofp.message.bsn_gentable_clear_request(table_id=TABLE_ID)
        response, _ = self.controller.transact(request)
        self.assertIsInstance(response, ofp.message.bsn_gentable_clear_reply)
        self.assertEquals(response.error_count, 0)

    def do_add(self, vlan_vid, ipv4, mac, idle_notification=False):
        msg = ofp.message.bsn_gentable_entry_add(
            table_id=TABLE_ID,
            key=[
                ofp.bsn_tlv.vlan_vid(vlan_vid),
                ofp.bsn_tlv.ipv4(ipv4)],
            value=[
                ofp.bsn_tlv.mac(mac)],
            checksum=0)
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
        request = ofp.message.bsn_gentable_clear_request(table_id=TABLE_ID)
        response, _ = self.controller.transact(request)
        self.assertIsInstance(response, ofp.message.bsn_gentable_clear_reply)
        self.assertEquals(response.error_count, 0)
        self.assertEquals(response.deleted_count, 3)

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
