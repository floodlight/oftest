import logging
import struct

from oftest import config
import ofp
import oftest.base_tests as base_tests

from oftest.testutils import *

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
                        action_list=[ofp.action.nicira_dec_ttl()])

        outpkt = simple_tcp_packet(pktlen=100, ip_ttl=3)
        msg = ofp.message.packet_out(in_port=ofp.OFPP_NONE,
                                     data=str(outpkt),
                                     buffer_id=0xffffffff,
                                     actions=[
                                         ofp.action.nicira_dec_ttl(),
                                         ofp.action.output(port=portA),
                                         ofp.action.nicira_dec_ttl(),
                                         ofp.action.output(port=portB),
                                         ofp.action.nicira_dec_ttl(),
                                         ofp.action.output(port=portC)])
        self.controller.message_send(msg)

        receive_pkt_check(self.dataplane, simple_tcp_packet(ip_ttl=2), [portA], [], self)
        receive_pkt_check(self.dataplane, simple_tcp_packet(ip_ttl=1), [portB], [], self)
        receive_pkt_check(self.dataplane, simple_tcp_packet(ip_ttl=0), [], [portC], self)
