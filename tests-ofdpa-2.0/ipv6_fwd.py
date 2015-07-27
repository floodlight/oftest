# Copyright (c) 2015 Big Switch Networks, Inc.
"""
Testing IPv6 forwarding

Test cases in other modules depend on this functionality.
"""

import logging
import pdb

from oftest import config
import oftest.base_tests as base_tests
import ofp
import ofdpa_utils
from oftest.parse import parse_ipv6

from oftest.testutils import *
import oftest.oft12.testutils as testutils12

def macAddrToHexList(mac):
    """ Takes '00:11:22:33:44:ff' and returns [ 0x00, 0x11, 0x22, 0x33, 0x44, 0xff] """
    return map(int,mac.split(':'),[16]*6)

@group('ipv6_fwd')
class IPv6_Untagged_Unicast(base_tests.SimpleDataPlane):
    """
    Test routing function for an IPv6 IP packet

    Need to insert rules into:
    1) A group action in the group table
    2) Vlan table to map packet to a vlan
    3) Mac Term table to send router's mac packets to the routing table
    4) the actual routing rule in the unicast routing table

    Then test from all ports to all ports

    """
    def runTest(self):
        router_mac = '00:11:22:33:44:55'
        dst_ip = 'fe80::2420:52ff:fe8f:5190'        
        dst_mac = '00:11:11:11:11:11'
        dst_vlan = 2        # used for internal switch purposes
        ports = sorted(config["port_map"].keys())

        delete_all_flows(self.controller)
        delete_all_groups(self.controller)

        #pdb.set_trace()
        l3_group_id = ofdpa_utils.makeGroupID("L3 Unicast",1)
        l2_group_id = ofdpa_utils.makeGroupID("L2 Interface",(dst_vlan<<16) + 1)  # bits 27:16 of the local_id are the vlan (!?)

        # OF-DPA requires vlans to function
        ofdpa_utils.installDefaultVlan(self.controller)
        ofdpa_utils.enableVlanOnPort(self.controller, dst_vlan)


        # Create the L2 interface group entry
        #   Note that the port here is temp; will be reset in the testing loop
        group_msg = ofp.message.group_add(
            group_type=ofp.OFPGT_ALL,
            group_id=l2_group_id,
            buckets=[
            ofp.bucket(
                actions=[
                    ofp.action.pop_vlan(),
                    ofp.action.output(ports[0])  # set port now, but inner loop will change
                    ])
            ])

        logging.info("Creating IPv6 L2 interface group")
        self.controller.message_send(group_msg)
        do_barrier(self.controller)
        verify_no_errors(self.controller)


        # Create the L3 unicast group entry
        group_msg = ofp.message.group_add(
            group_type=ofp.OFPGT_ALL,
            group_id=l3_group_id,  
            buckets=[
            ofp.bucket(
                actions=[
                    ofp.action.group(l2_group_id),  # chain to L2 group
                    ofp.action.set_field( ofp.oxm.eth_dst( macAddrToHexList(dst_mac))),
                    ofp.action.set_field( ofp.oxm.eth_src( macAddrToHexList(router_mac))),
                    ofp.action.set_field( ofp.oxm.vlan_vid( dst_vlan)),
                    ])
            ])

        logging.info("Creating IPv6 Unicast group")
        self.controller.message_send(group_msg)
        do_barrier(self.controller)
        verify_no_errors(self.controller)

        # Insert a rule in the MAC termination table to send to Unicast router table
        #   Must match on dst mac and ethertype; other fields are optional
        macterm_match = ofp.match([
            ofp.oxm.eth_dst(macAddrToHexList(router_mac)),
            ofp.oxm.eth_type(0x86dd)    # ethertype = IPv6
            ])

        request = ofp.message.flow_add(
            table_id = ofdpa_utils.MACTERM_TABLE.table_id,
            cookie=55,
            match=macterm_match,
            instructions=[
                    ofp.instruction.goto_table(ofdpa_utils.UNICAST_ROUTING_TABLE.table_id)
                ],
            buffer_id=ofp.OFP_NO_BUFFER,
            priority=1000)

        logging.info("Inserting IPv6 MacTermination rule")
        self.controller.message_send(request)
        do_barrier(self.controller)
        verify_no_errors(self.controller)

        # Insert a rule into the Unicast Routing table to forward this packet
        unicast_match = ofp.match([
            ofp.oxm.eth_type(0x86dd),    # ethertype = IPv6
            ofp.oxm.ipv6_dst(parse_ipv6(dst_ip)),
             ])

        request = ofp.message.flow_add(
            table_id = ofdpa_utils.UNICAST_ROUTING_TABLE.table_id,
            cookie=66,
            match=unicast_match,
            instructions=[
                    ofp.instruction.goto_table(ofdpa_utils.ACL_TABLE.table_id),
                    ofp.instruction.write_actions([ofp.action.group(l3_group_id)])
                ],
            buffer_id=ofp.OFP_NO_BUFFER,
            priority=1000)

        logging.info("Inserting IPv6 MacTermination rule")
        self.controller.message_send(request)
        do_barrier(self.controller)
        verify_no_errors(self.controller)

        # Generate the test and expected packets
        parsed_pkt = testutils12.simple_ipv6_packet()
        pkt = str(parsed_pkt)

        parsed_expected_pkt = testutils12.simple_ipv6_packet(
               dl_dst = router_mac,
#               dl_vlan_enable=True,
#               vlan_vid=ofdpa_utils.DEFAULT_VLAN,
#               vlan_pcp=0,
#               pktlen=104 # 4 less than we started with, because the way simple_tcp calc's length
               ) 
        expected_pkt = str(parsed_expected_pkt)

        for out_port in ports:
            msg = ofp.message.group_modify(
                    group_type=ofp.OFPGT_ALL,
                    group_id=l2_group_id,
                    buckets=[
                        ofp.action.pop_vlan(),
                        ofp.bucket(actions=[ofp.action.output(out_port)])
                        ])

            self.controller.message_send(msg)
            logging.info("Changing output port for group %d to %d" % (l2_group_id, out_port))
            do_barrier(self.controller)
            verify_no_errors(self.controller)

            for in_port in ports:
                if in_port == out_port:
                    continue
                logging.info("IPv6_Untagged_Unicast test, ports %d to %d", in_port, out_port)
                self.dataplane.send(in_port, pkt)
                verify_packets(self, expected_pkt, [out_port])
