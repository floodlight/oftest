"""
"""
import struct
import logging
import scapy

from oftest import config
import oftest.controller as controller
import ofp
import oftest.base_tests as base_tests

from oftest.testutils import *

def normal_ip_mask(index):
    """
    Return the IP mask for the given wildcard index 0 - 63 per the OF 1.0 spec
    """
    if index < 32:
        return ((1 << 32) - 1) ^ ((1 << index) - 1)
    else:
        return 0

def fancy_ip_mask(index):
    """
    Return the IP mask for the given wildcard index 0 - 31 per the OF 1.0 spec.
    For wildcard index 32 - 63, return a "negative" IP mask:
      32 : wildcard the first bit, mask 127.255.255.255
      33 : wildcard all first 2 bits, mask 63.255.255.255
      ...
      62 : wildcard all but last bit, mask 0.0.0.1
      63 : wildcard all bits, mask 0.0.0.0
    """
    if index < 32:
        return ((1 << 32) - 1) ^ ((1 << index) - 1)
    else:
        return (1 << (63 - index)) - 1

@nonstandard
class BSNConfigIPMask(base_tests.SimpleDataPlane):
    """
    Exercise BSN vendor extension for configuring IP source/dest match mask
    """

    def bsn_set_ip_mask(self, index, mask):
        """
        Use the BSN_SET_IP_MASK vendor command to change the IP mask for the
        given wildcard index
        """
        logging.info("Setting index %d to mask is %s" % (index, mask))
        m = ofp.message.bsn_set_ip_mask(index=index, mask=mask)
        self.controller.message_send(m)

    def bsn_get_ip_mask(self, index):
        """
        Use the BSN_GET_IP_MASK_REQUEST vendor command to get the current IP mask
        for the given wildcard index
        """
        request = ofp.message.bsn_get_ip_mask_request(index=index)
        reply, _ = self.controller.transact(request)
        self.assertTrue(isinstance(reply, ofp.message.bsn_get_ip_mask_reply), "Wrong reply type")
        self.assertEqual(reply.index, index, "Wrong index")
        return reply.mask

    def runTest(self):
        self.assertFalse(required_wildcards(self) & ofp.OFPFW_NW_DST_ALL,
                         "IP dst must be wildcarded")
        self.assertFalse(required_wildcards(self) & ofp.OFPFW_NW_SRC_ALL,
                         "IP src must be wildcarded")
        for index in range(0, 64):
            mask = self.bsn_get_ip_mask(index)
            logging.info("Index %d mask is %s" %
                           (index, scapy.utils.ltoa(mask)))
            self.assertEqual(mask, normal_ip_mask(index), "Unexpected IP mask")

        for index in range(0, 64):
            mask = normal_ip_mask(index)
            if mask == 0:
                logging.info("Skipping IP wildcard index %d" % index)
            else:
                logging.info("Testing IP wildcard index %d" % index)
                self.check_ip_mask(True, index, mask)
                self.check_ip_mask(False, index, mask)

        logging.info("Setting fancy IP masks")
        for index in range(0, 64):
            self.bsn_set_ip_mask(index, fancy_ip_mask(index))
        for index in range(0, 64):
            mask = self.bsn_get_ip_mask(index)
            logging.info("Index %d mask is %s" %
                           (index, scapy.utils.ltoa(mask)))
            self.assertEqual(mask, fancy_ip_mask(index), "Unexpected IP mask")

        for index in range(0, 64):
            mask = fancy_ip_mask(index)
            if mask == 0:
                logging.info("Skipping IP wildcard index %d" % index)
            else:
                logging.info("Testing IP wildcard index %d" % index)
                self.check_ip_mask(True, index, mask)
                self.check_ip_mask(False, index, mask)

    def check_ip_mask(self, source, index, mask):
        ports = config["port_map"].keys()

        # For each mask we install two flow entries, one which matches
        # on IP source or dest addr all-0s (modulo the mask) and
        # outputs to port 1, the other which matches on all-1s (modulo
        # the mask) and outputs to port 2.

        # Then we construct four packets: The first two are the same
        # as the two flow entry matches (all 0s and all 1s), and we
        # check that the packets go to ports 1 and 2, respectively.
        # For the second set of packets, we flip the un-masked bits
        # and check that only the masked bits are matched.

        ip0 = scapy.utils.ltoa(0x00000000)
        ip1 = scapy.utils.ltoa(0xffffffff)
        ip2 = scapy.utils.ltoa(0xffffffff ^ mask)
        ip3 = scapy.utils.ltoa(0x00000000 ^ mask)

        if source:
           wildcards = ((ofp.OFPFW_ALL ^ ofp.OFPFW_DL_TYPE ^ ofp.OFPFW_NW_SRC_MASK)
                        | (index << ofp.OFPFW_NW_SRC_SHIFT))
           pkt0 = simple_tcp_packet(ip_src=ip0)
           pkt1 = simple_tcp_packet(ip_src=ip1)
           pkt2 = simple_tcp_packet(ip_src=ip2)
           pkt3 = simple_tcp_packet(ip_src=ip3)
           msg = lambda ip: logging.info("Testing source IP %s" % ip)
        else:
           wildcards = ((ofp.OFPFW_ALL ^ ofp.OFPFW_DL_TYPE ^ ofp.OFPFW_NW_DST_MASK)
                        | (index << ofp.OFPFW_NW_DST_SHIFT))
           pkt0 = simple_tcp_packet(ip_dst=ip0)
           pkt1 = simple_tcp_packet(ip_dst=ip1)
           pkt2 = simple_tcp_packet(ip_dst=ip2)
           pkt3 = simple_tcp_packet(ip_dst=ip3)
           msg = lambda ip: logging.info("Testing dest IP %s" % ip)

        delete_all_flows(self.controller)

        self.controller.message_send(flow_msg_create(
              self, pkt0, ing_port=ports[0], egr_ports=[ports[1]],
              wildcards=wildcards))
        self.controller.message_send(flow_msg_create(
              self, pkt1, ing_port=ports[0], egr_ports=[ports[2]],
              wildcards=wildcards))

        do_barrier(self.controller)
            
        msg(ip0)
        self.dataplane.send(ports[0], str(pkt0))
        receive_pkt_verify(self, [ports[1]], pkt0, ports[0])

        msg(ip1)
        self.dataplane.send(ports[0], str(pkt1))
        receive_pkt_verify(self, [ports[2]], pkt1, ports[0])

        msg(ip2)
        self.dataplane.send(ports[0], str(pkt2))
        receive_pkt_verify(self, [ports[1]], pkt2, ports[0])

        msg(ip3)
        self.dataplane.send(ports[0], str(pkt3))
        receive_pkt_verify(self, [ports[2]], pkt3, ports[0])
