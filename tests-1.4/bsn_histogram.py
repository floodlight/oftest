# Distributed under the OpenFlow Software License (see LICENSE)
# Copyright (c) 2016 Big Switch Networks, Inc.
"""
BSN histogram extension test cases
"""

import logging

from oftest import config
import oftest.base_tests as base_tests
import ofp
import loxi.pp

from oftest.testutils import *

@nonstandard
class HistogramStatsRequest(base_tests.SimpleProtocol):
    """
    Verify that the builtin "test" histogram returns expected keys and counts
    """
    def runTest(self):
        request = ofp.message.bsn_generic_stats_request(
            name="histogram",
            tlvs=[ofp.bsn_tlv.name("test")])

        entries = get_stats(self, request)
        self.assertEquals(1, len(entries))
        entry = entries[0]

        self.assertEquals(1, len(entry.tlvs))
        self.assertIsInstance(entry.tlvs[0], ofp.bsn_tlv.uint64_list)

        values = [x.value for x in entry.tlvs[0].value]
        expected = [
            0, 1, 1, 1, 2, 1, 3, 1, 4, 1, 5, 1, 6, 1, 7, 1, 8, 1, 9, 1, 10, 1, 11, 1, 12, 1, 13, 1, 14, 1, 15, 1,
            16, 1, 17, 1, 18, 1, 19, 1, 20, 1, 21, 1, 22, 1, 23, 1, 24, 1, 25, 1, 26, 1, 27, 1, 28, 1, 29, 1, 30, 1, 31, 1,
            32, 2, 34, 2, 36, 2, 38, 2, 40, 2, 42, 2, 44, 2, 46, 2, 48, 2, 50, 2, 52, 2, 54, 2, 56, 2, 58, 2, 60, 2, 62, 2,
            64, 4, 68, 4, 72, 4, 76, 4, 80, 4, 84, 4, 88, 4, 92, 4, 96, 4, 100, 4, 104, 4, 108, 4, 112, 4, 116, 4, 120, 4, 124, 4,
            128, 8, 136, 8, 144, 8, 152, 8, 160, 8, 168, 8, 176, 8, 184, 8, 192, 8, 200, 8, 208, 8, 216, 8, 224, 8, 232, 8, 240, 8, 248, 8]

        self.assertEquals(expected, values)

@nonstandard
class HistogramStatsRequestBadTLVs(base_tests.SimpleProtocol):
    """
    Verify the correct error messages are reeturned if the controller
    sends the wrong TLVs in the request
    """
    def runTest(self):
        request = ofp.message.bsn_generic_stats_request(
            name="histogram",
            tlvs=[])
        
        reply, _ = self.controller.transact(request)
        self.assertBsnError(reply, "Expected name TLV, found empty list")

        request = ofp.message.bsn_generic_stats_request(
            name="histogram",
            tlvs=[ofp.bsn_tlv.ipv4_src(), ofp.bsn_tlv.name("test")])
        
        reply, _ = self.controller.transact(request)
        self.assertBsnError(reply, "Expected name TLV, found of_bsn_tlv_ipv4_src")

        request = ofp.message.bsn_generic_stats_request(
            name="histogram",
            tlvs=[ofp.bsn_tlv.name("test"), ofp.bsn_tlv.ipv4_src()])
        
        reply, _ = self.controller.transact(request)
        self.assertBsnError(reply, "Expected end of TLV list, found of_bsn_tlv_ipv4_src")

    def assertBsnError(self, msg, text):
        self.assertIsInstance(msg, ofp.message.bsn_error)
        self.assertEqual(text, msg.err_msg)

@nonstandard
class HistogramListStatsRequest(base_tests.SimpleProtocol):
    """
    Verify that histogram names are returned
    """
    def runTest(self):
        request = ofp.message.bsn_generic_stats_request(name="histograms")
        entries = get_stats(self, request)

        names = []
        for entry in entries:
            self.assertEquals(1, len(entry.tlvs))
            self.assertIsInstance(entry.tlvs[0], ofp.bsn_tlv.name)
            names.append(entry.tlvs[0].value)

        logging.debug("Histograms: %r", names)
        self.assertIn("test", names)
