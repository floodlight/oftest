# Distributed under the OpenFlow Software License (see LICENSE)
# Copyright (c) 2014 Big Switch Networks, Inc.
"""
Flow-mod test cases
"""

import logging

import oftest
from oftest import config
import oftest.base_tests as base_tests
import ofp
from loxi.pp import pp

from oftest.testutils import *
from oftest.parse import parse_ipv6

class Overwrite(base_tests.SimpleDataPlane):
    """
    Verify that overwriting a flow changes most fields but preserves stats
    """
    def runTest(self):
        in_port, out_port1, out_port2 = openflow_ports(3)

        delete_all_flows(self.controller)

        table_id = test_param_get("table", 0)
        match = ofp.match([
            ofp.oxm.in_port(in_port),
        ])
        priority = 1000

        logging.info("Inserting flow")
        request = ofp.message.flow_add(
                table_id=table_id,
                match=match,
                instructions=[
                    ofp.instruction.apply_actions([ofp.action.output(out_port1)]),
                ],
                buffer_id=ofp.OFP_NO_BUFFER,
                priority=priority,
                flags=ofp.OFPFF_SEND_FLOW_REM,
                cookie=0x1234,
                hard_timeout=1000,
                idle_timeout=2000)
        self.controller.message_send(request)
        do_barrier(self.controller)

        # Send a packet through so that we can check stats were preserved
        self.dataplane.send(in_port, str(simple_tcp_packet(pktlen=100)))
        verify_flow_stats(self, ofp.match(), table_id=table_id, pkts=1)

        # Send a flow-add with the same table_id, match, and priority, causing
        # an overwrite
        logging.info("Overwriting flow")
        request = ofp.message.flow_add(
                table_id=table_id,
                match=match,
                instructions=[
                    ofp.instruction.apply_actions([ofp.action.output(out_port2)]),
                ],
                buffer_id=ofp.OFP_NO_BUFFER,
                priority=priority,
                flags=0,
                cookie=0xabcd,
                hard_timeout=3000,
                idle_timeout=4000)
        self.controller.message_send(request)
        do_barrier(self.controller)

        # Should not get a flow-removed message
        msg, _ = self.controller.poll(exp_msg=ofp.message.flow_removed,
                                      timeout=oftest.ofutils.default_negative_timeout)
        self.assertEquals(msg, None)

        # Check that the fields in the flow stats entry match the second flow-add
        stats = get_flow_stats(self, ofp.match())
        self.assertEquals(len(stats), 1)
        entry = stats[0]
        logging.debug(entry.show())
        self.assertEquals(entry.instructions, request.instructions)
        self.assertEquals(entry.flags, request.flags)
        self.assertEquals(entry.cookie, request.cookie)
        self.assertEquals(entry.hard_timeout, request.hard_timeout)
        self.assertEquals(entry.idle_timeout, request.idle_timeout)

        # Flow stats should have been preserved
        verify_flow_stats(self, ofp.match(), table_id=table_id, pkts=1)
