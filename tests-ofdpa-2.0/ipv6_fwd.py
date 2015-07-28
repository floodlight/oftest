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



class L3Iface(object):
    def __init__(self, mac,vlan,port, dst_mac, dst_ip):
        self.mac = mac              # this is the mac of the router interface
        self.port = port            # this is the port of the router
        self.vlan = vlan
        self.dst_mac = dst_mac
        self.dst_ip = dst_ip


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
    def create_interface(self, iface):
        l2_group_id = ofdpa_utils.makeGroupID("L2 Interface",(iface.vlan<<16) + iface.port)  # bits 27:16 of the local_id are the vlan (!?)
        l3_group_id = ofdpa_utils.makeGroupID("L3 Unicast",iface.port)
        self.send_log_check("Creating IPv6 L2 interface group for port %d" % iface.port, ofp.message.group_add(
            group_type=ofp.OFPGT_ALL,
            group_id=l2_group_id,
            buckets=[
            ofp.bucket(
                actions=[
                    ofp.action.pop_vlan(),
                    ofp.action.output(iface.port)
                    ])
            ]))

        # Insert a rule in the MAC termination table to send to Unicast router table
        #   Must match on dst mac and ethertype; other fields are optional
        macterm_match = ofp.match([
            ofp.oxm.eth_dst(macAddrToHexList(iface.mac)),
            ofp.oxm.eth_type(0x86dd)    # ethertype = IPv6
            ])

        self.send_log_check( "Inserting IPv6 MacTermination rule", ofp.message.flow_add(
            table_id = ofdpa_utils.MACTERM_TABLE.table_id,
            cookie=55,
            match=macterm_match,
            instructions=[
                    ofp.instruction.goto_table(ofdpa_utils.UNICAST_ROUTING_TABLE.table_id)
                ],
            buffer_id=ofp.OFP_NO_BUFFER,
            priority=1000))

        # Create the L3 unicast group entry
        self.send_log_check("Creating IPv6 Unicast group for %d" % iface.port, ofp.message.group_add(
            group_type=ofp.OFPGT_ALL,
            group_id=l3_group_id,  
            buckets=[
            ofp.bucket(
                actions=[
                    ofp.action.group(l2_group_id),  # chain to last L2 group; doesn't matter; will fix in test loop
                    ofp.action.set_field( ofp.oxm.eth_dst( macAddrToHexList(iface.dst_mac))),
                    ofp.action.set_field( ofp.oxm.eth_src( macAddrToHexList(iface.mac))),
                    ofp.action.set_field( ofp.oxm.vlan_vid( iface.vlan)),
                    ])
            ]))

        # Store the match for the unicast match below
        unicast_match = ofp.match([
              ofp.oxm.eth_type(0x86dd),    # ethertype = IPv6
              ofp.oxm.ipv6_dst(parse_ipv6(iface.dst_ip)),
              ])

        # OF-DPA requires vlans to function
        ofdpa_utils.installDefaultVlan(self.controller, iface.vlan, iface.port)


        self.send_log_check("Modifying IPv6 route rule to output to port %d" % iface.port, ofp.message.flow_modify(
                    table_id = ofdpa_utils.UNICAST_ROUTING_TABLE.table_id,
                    cookie=66,
                    match=unicast_match,
                    instructions=[
                        ofp.instruction.goto_table(ofdpa_utils.ACL_TABLE.table_id),
                            # set the l3_group_id to correspond to out_port's buckets
                            ofp.instruction.write_actions([
                                ofp.action.group(ofdpa_utils.makeGroupID("L3 Unicast",iface.port))]) 
                        ],
                    buffer_id=ofp.OFP_NO_BUFFER,
                    priority=1000))
        

    def send_log_check(self, log_msg, of_msg):
        logging.info(log_msg)
        self.controller.message_send(of_msg)
        do_barrier(self.controller)
        verify_no_errors(self.controller)

    def runTest(self):
        ports = sorted(config["port_map"].keys())

        delete_all_flows(self.controller)
        delete_all_groups(self.controller)
        do_barrier(self.controller)

        ifaces = {
            # mac,vlan,port, dst_mac, dst_ip
            L3Iface('00:11:11:11:11:11', 1, 1, '00:11:11:11:11:ff', 'fe80::1111'): 1,
            L3Iface('00:22:22:22:22:22', 2, 2, '00:22:22:22:22:ff', 'fe80::2222'): 2,
            L3Iface('00:33:33:33:33:33', 3, 3, '00:33:33:33:33:ff', 'fe80::3333'): 3,
            L3Iface('00:44:44:44:44:44', 4, 4, '00:44:44:44:44:ff', 'fe80::4444'): 4,
            L3Iface('00:55:55:55:55:55', 5, 5, '00:55:55:55:55:ff', 'fe80::5555'): 5,
            L3Iface('00:66:66:66:66:66', 6, 6, '00:66:66:66:66:ff', 'fe80::6666'): 6,
        }

        for iface in ifaces:
            self.create_interface(iface)

        # test sending from every inteface to every other interface
        for in_iface in sorted(ifaces):
            for out_iface in sorted(ifaces):
                if in_iface == out_iface:
                    continue
                # Generate the test and expected packets
                parsed_pkt = testutils12.simple_ipv6_packet(
                    ip_dst = out_iface.dst_ip,
                    dl_dst = in_iface.mac)
                pkt = str(parsed_pkt)

                parsed_expected_pkt = testutils12.simple_ipv6_packet(
                       dl_src = out_iface.mac,
                       dl_dst = out_iface.dst_mac,
                       ip_dst = out_iface.dst_ip,
#               dl_vlan_enable=True,
#               vlan_vid=ofdpa_utils.DEFAULT_VLAN,
#               vlan_pcp=0,
#               pktlen=104 # 4 less than we started with, because the way simple_tcp calc's length
                       ) 
                expected_pkt = str(parsed_expected_pkt)
                logging.info("IPv6_Untagged_Unicast test, iface %d to %d", ifaces[in_iface], ifaces[out_iface])
                self.dataplane.send(in_iface.port, pkt)
                verify_packets(self, expected_pkt, [out_iface.port])
            
