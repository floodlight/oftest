# Distributed under the OpenFlow Software License (see LICENSE)
# Copyright (c) 2012, 2013 Big Switch Networks, Inc.
"""
Packet-in match test cases

Checks the match sent in packet-in messages.
"""

import logging

from oftest import config
import oftest.base_tests as base_tests
import ofp

from oftest.testutils import *

class PktinMatchTest(base_tests.SimpleDataPlane):
    """
    Base class for packet-in match tests
    """

    def setUp(self):
        base_tests.SimpleDataPlane.setUp(self)
        delete_all_flows(self.controller)

    def verify_pktin_match(self, pkt, expected_oxm, optional=False):
        """
        Cause a packet-in and verify that the expected OXM is present
        (unless optional) and equal
        """

        in_port, = openflow_ports(1)
        pktstr = str(pkt)

        logging.debug("Inserting match-all flow sending packets to controller")
        request = ofp.message.flow_add(
            table_id=test_param_get_table(),
            instructions=[
                ofp.instruction.apply_actions(
                    actions=[
                        ofp.action.output(
                            port=ofp.OFPP_CONTROLLER,
                            max_len=ofp.OFPCML_NO_BUFFER)])],
            buffer_id=ofp.OFP_NO_BUFFER,
            priority=0)
        self.controller.message_send(request)
        do_barrier(self.controller)

        logging.debug("Sending packet")
        self.dataplane.send(in_port, pktstr)

        logging.debug("Expecting packet-in")
        msg = verify_packet_in(self, pktstr, in_port, ofp.OFPR_NO_MATCH)
        oxms = { type(oxm): oxm for oxm in msg.match.oxm_list }
        oxm = oxms.get(type(expected_oxm))
        if oxm:
            self.assertEquals(oxm, expected_oxm, "Received %s != expected %s" % (oxm.show(), expected_oxm.show()))
        elif optional:
            logging.info("Optional OXM not received")
        else:
            raise AssertionError("Required OXM not received")

class VlanAbsent(PktinMatchTest):
    """
    Absent VLAN tag
    """
    def runTest(self):
        self.verify_pktin_match(
            simple_tcp_packet(),
            ofp.oxm.vlan_vid(0),
            optional=True)

class VlanVid(PktinMatchTest):
    """
    VLAN tag
    """
    def runTest(self):
        self.verify_pktin_match(
            simple_tcp_packet(dl_vlan_enable=True, vlan_vid=1),
            ofp.oxm.vlan_vid(ofp.OFPVID_PRESENT|1),
            optional=True)
