import logging
import struct

from oftest import config
import of10 as ofp
import oftest.base_tests as base_tests

from oftest.testutils import *

class action_nx_dec_ttl(ofp.action.vendor):
    def __init__(self):
        ofp.action.vendor.__init__(self)
        self.vendor = 0x00002320

    def pack(self):
        return ofp.action.vendor.pack(self) + struct.pack("!HHL", 18, 0x0, 0x0)

    def __len__(self):
        return 16

    def show(self, prefix=''):
        return prefix + 'dec_ttl: ' + '\n' + ofp.action.vendor.show(self)

@nonstandard
class TtlDecrement(base_tests.SimpleDataPlane):
    def runTest(self):
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) >= 3, "Not enough ports for test")
        portA = of_ports[0]
        portB = of_ports[1]
        portC = of_ports[2]

        # Test using flow mods (does not test drop)
        flow_match_test(self, config["port_map"],
                        pkt=simple_tcp_packet(pktlen=100, ip_ttl=2),
                        exp_pkt=simple_tcp_packet(pktlen=100, ip_ttl=1),
                        action_list=[action_nx_dec_ttl()])

        outpkt = simple_tcp_packet(pktlen=100, ip_ttl=3)
        msg = ofp.message.packet_out(in_port=ofp.OFPP_NONE,
                                     data=str(outpkt),
                                     actions=[
                                         action_nx_dec_ttl(),
                                         ofp.action.output(port=portA),
                                         action_nx_dec_ttl(),
                                         ofp.action.output(port=portB),
                                         action_nx_dec_ttl(),
                                         ofp.action.output(port=portC)])
        self.controller.message_send(msg)

        receive_pkt_check(self.dataplane, simple_tcp_packet(ip_ttl=2), [portA], [], self)
        receive_pkt_check(self.dataplane, simple_tcp_packet(ip_ttl=1), [portB], [], self)
        receive_pkt_check(self.dataplane, simple_tcp_packet(ip_ttl=0), [], [portC], self)
