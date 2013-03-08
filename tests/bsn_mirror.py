"""
"""
import struct

import logging

from oftest import config
import oftest.controller as controller
import ofp
import oftest.message as message
import oftest.action as action
import oftest.action_list as action_list
import oftest.base_tests as base_tests

from oftest.testutils import *

class bsn_action_mirror(action.action_vendor):
    def __init__(self):
        self.type = ofp.OFPAT_VENDOR
        self.len = 24
        self.vendor = 0x005c16c7
        self.subtype = 1
        self.dest_port = 0
        self.vlan_tag = 0
        self.copy_stage = 0

    def __assert(self):
        return (True, None)

    def pack(self, assertstruct=True):
        return struct.pack("!HHLLLLBBBB", self.type, self.len, self.vendor,
                           self.subtype, self.dest_port, self.vlan_tag,
                           self.copy_stage, 0, 0, 0)

    def unpack(self, binaryString):
        if len(binaryString) < self.len:
            raise Exception("too short")
        x = struct.unpack("!HHLLLLBBBB", binaryString[:self.len])
        if x[0] != self.type:
            raise Exception("wrong type")
        if x[1] != self.len:
            raise Exception("wrong length")
        if x[2] != self.vendor:
            raise Exception("wrong vendor")
        if x[3] != self.subtype:
            raise Exception("wrong subtype")
        self.dest_port = x[4]
        self.vlan_tag = x[5]
        self.copy_stage = x[6]
        return binaryString[self.len:]

    def __len__(self):
        return self.len

    def __eq__(self, other):
        if type(self) != type(other): return False
        if self.type != other.type: return False
        if self.len != other.len: return False
        if self.vendor != other.vendor: return False
        if self.subtype != other.subtype: return False
        if self.dest_port != other.dest_port: return False
        if self.vlan_tag != other.vlan_tag: return False
        if self.copy_stage != other.copy_stage: return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def show(self, prefix=""):
        outstr = prefix + "action_vendor\n"
        for f in ["type", "len", "vendor", "subtype", "dest_port", "vlan_tag",
                  "copy_stage"]:
            outstr += prefix + ("%s: %s\n" % (f, getattr(self, f)))
        return outstr

action_list.action_object_map[ofp.OFPAT_VENDOR] = bsn_action_mirror

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
        m = message.vendor()
        m.vendor = 0x005c16c7
        m.data = struct.pack("!LBBBB", 3, enabled, 0, 0, 0)
        self.controller.message_send(m)

    def bsn_get_mirroring(self):
        """
        Use the BSN_GET_MIRRORING_REQUEST vendor command to get the
        enabled/disabled state of mirror action support
        """
        m = message.vendor()
        m.vendor = 0x005c16c7
        m.data = struct.pack("!LBBBB", 4, 0, 0, 0, 0)
        self.controller.message_send(m)
        m, r = self.controller.poll(ofp.OFPT_VENDOR, 2)
        self.assertEqual(m.vendor, 0x005c16c7, "Wrong vendor ID")
        x = struct.unpack("!LBBBB", m.data)
        self.assertEqual(x[0], 5, "Wrong subtype")
        return x[1]

    def runTest(self):
        mirror_ports = test_param_get("mirror_ports")
        ports = [p for p in config["port_map"].keys() if p not in mirror_ports]
        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.in_port = ports[0]
        match.wildcards &= ~ofp.OFPFW_IN_PORT

        logging.info("Checking that mirror ports are not reported")
        self.assertEqual(bool(self.bsn_get_mirroring()), False)
        m, r = self.controller.transact(message.features_request(), 2)
        p = dict([(pt.port_no, pt) for pt in m.ports])
        self.assertFalse(mirror_ports[0] in p or mirror_ports[1] in p,
                         "Mirror port in features reply")

        logging.info("Enabling mirror port reporting")
        self.bsn_set_mirroring(True)

        logging.info("Checking that mirror ports are reported")
        self.assertEqual(bool(self.bsn_get_mirroring()), True)
        m, r = self.controller.transact(message.features_request(), 2)
        p = dict([(pt.port_no, pt) for pt in m.ports])
        self.assertTrue(mirror_ports[0] in p and mirror_ports[1] in p,
                        "Mirror port not in features reply")
        self.assertTrue(p[mirror_ports[0]].config & (1 << 31),
                        "Mirror port config flag not set in features reply")
        self.assertTrue(p[mirror_ports[1]].config & (1 << 31),
                        "Mirror port config flag not set in features reply")

        act1 = bsn_action_mirror()
        act1.dest_port = mirror_ports[0]
        act1.copy_stage = 0
        act2 = bsn_action_mirror()
        act2.dest_port = mirror_ports[1]
        act2.copy_stage = 0
        act3 = action.action_output()
        act3.port = ports[1]
        flow_mod = message.flow_mod()
        flow_mod.match = match
        flow_mod.actions.add(act1)
        flow_mod.actions.add(act2)
        flow_mod.actions.add(act3)
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
