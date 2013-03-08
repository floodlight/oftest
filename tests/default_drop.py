"""
These tests require a switch that drops packet-ins.
"""

import logging

from oftest import config
import oftest.controller as controller
import ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action
import oftest.base_tests as base_tests

from oftest.testutils import *

@nonstandard
class PacketInDefaultDrop(base_tests.SimpleDataPlane):
    """
    Verify that packet-ins are not received.
    """

    def runTest(self):
        delete_all_flows(self.controller)
        do_barrier(self.controller)

        for of_port in config["port_map"].keys():
            pkt = simple_tcp_packet()
            self.dataplane.send(of_port, str(pkt))
            count = 0
            while True:
                (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN)
                if not response:  # Timeout
                    break
                if dataplane.match_exp_pkt(pkt, response.data): # Got match
                    break
                if not config["relax"]:  # Only one attempt to match
                    break
                count += 1
                if count > 10:   # Too many tries
                    break

            self.assertTrue(response is None, 
                            'Packet in message received on port ' + 
                            str(of_port))
