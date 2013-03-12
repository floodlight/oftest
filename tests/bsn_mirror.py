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
class BSNMirrorAction(base_tests.SimpleDataPlane):
    """
    Exercise BSN vendor extension for copying packets to a mirror destination
    port
    """

    def bsn_set_mirroring(self, enabled):
        """
        Use the BSN_SET_MIRRORING vendor command to enable/disable
        mirror action support
        """
        m = ofp.message.bsn_set_mirroring(report_mirror_ports=enabled)
        self.controller.message_send(m)

    def bsn_get_mirroring(self):
        """
        Use the BSN_GET_MIRRORING_REQUEST vendor command to get the
        enabled/disabled state of mirror action support
        """
        request = ofp.message.bsn_get_mirroring_request()
        reply, _ = self.controller.transact(request)
        self.assertTrue(isinstance(reply, ofp.message.bsn_get_mirroring_reply), "Unexpected reply type")
        return reply.report_mirror_ports

    def runTest(self):
        mirror_ports = test_param_get("mirror_ports")
        ports = [p for p in config["port_map"].keys() if p not in mirror_ports]
        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.in_port = ports[0]
        match.wildcards &= ~ofp.OFPFW_IN_PORT

        logging.info("Checking that mirror ports are not reported")
        self.assertEqual(bool(self.bsn_get_mirroring()), False)
        m, r = self.controller.transact(ofp.message.features_request(), 2)
        p = dict([(pt.port_no, pt) for pt in m.ports])
        self.assertFalse(mirror_ports[0] in p or mirror_ports[1] in p,
                         "Mirror port in features reply")

        logging.info("Enabling mirror port reporting")
        self.bsn_set_mirroring(True)

        logging.info("Checking that mirror ports are reported")
        self.assertEqual(bool(self.bsn_get_mirroring()), True)
        m, r = self.controller.transact(ofp.message.features_request(), 2)
        p = dict([(pt.port_no, pt) for pt in m.ports])
        self.assertTrue(mirror_ports[0] in p and mirror_ports[1] in p,
                        "Mirror port not in features reply")
        self.assertTrue(p[mirror_ports[0]].config & (1 << 31),
                        "Mirror port config flag not set in features reply")
        self.assertTrue(p[mirror_ports[1]].config & (1 << 31),
                        "Mirror port config flag not set in features reply")

        act1 = ofp.action.bsn_mirror()
        act1.dest_port = mirror_ports[0]
        act1.copy_stage = 0
        act2 = ofp.action.bsn_mirror()
        act2.dest_port = mirror_ports[1]
        act2.copy_stage = 0
        act3 = ofp.action.output()
        act3.port = ports[1]
        flow_mod = ofp.message.flow_add()
        flow_mod.match = match
        flow_mod.actions.append(act1)
        flow_mod.actions.append(act2)
        flow_mod.actions.append(act3)
        delete_all_flows(self.controller)
        self.controller.message_send(flow_mod)
        do_barrier(self.controller)
        
        logging.info("Sending packet to port %s" % ports[0])
        self.dataplane.send(ports[0], str(pkt))
        logging.info("Checking that packet was received from output port %s, "
                     "mirror ports %s and %s" % (
              ports[1], mirror_ports[0], mirror_ports[1]))
        receive_pkt_check(self.dataplane, pkt,
                          [ports[1], mirror_ports[0], mirror_ports[1]], [],
                          self)
