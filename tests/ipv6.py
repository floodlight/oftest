"""
Test cases for testing actions taken on packets

See basic.py for other info.

It is recommended that these definitions be kept in their own
namespace as different groups of tests will likely define 
similar identifiers.

  The function test_set_init is called with a complete configuration
dictionary prior to the invocation of any tests from this file.

  The switch is actively attempting to contact the controller at the address
indicated oin oft_config

"""

import logging

import oftest.cstruct as ofp
import oftest.match as match
import oftest.message as message
import oftest.action as action
import oftest.parse as parse
import oftest.instruction as instruction
import basic

import ipaddr

#import oftest.controller as controller

import testutils

import os.path
import subprocess

#@var port_map Local copy of the configuration map from OF port
# numbers to OS interfaces
ipv6_port_map = None
#@var ipv6_logger Local logger object
ipv6_logger = None
#@var ipv6_config Local copy of global configuration data
ipv6_config = None

# For test priority
#@var test_prio Set test priority for local tests
test_prio = {}

# Cache supported features to avoid transaction overhead
cached_supported_actions = None

TEST_VID_DEFAULT = 2

IPV6_ETHERTYPE = 0x86dd
ETHERTYPE_VLAN = 0x8100
ETHERTYPE_MPLS = 0x8847
TCP_PROTOCOL = 0x6
UDP_PROTOCOL = 0x11
ICMPV6_PROTOCOL = 0x3a

def test_set_init(config):
    """
    Set up function for IPv6 packet handling test classes

    @param config The configuration dictionary; see oft
    """

    global ipv6_port_map
    global ipv6_logger
    global ipv6_config

    ipv6_logger = logging.getLogger("ipv6")
    ipv6_logger.info("Initializing test set")
    ipv6_port_map = config["port_map"]
    ipv6_config = config


# TESTS
class MatchIPv6Simple(basic.SimpleDataPlane):
    """
    Just send a packet IPv6 to match a simple entry on the matching table
    """
    def runTest(self):
        
        of_ports = ipv6_port_map.keys()
        of_ports.sort()
        ing_port = of_ports[0]
        egr_port = of_ports[3]
        
        # Remove all entries Add entry match all
#        rc = testutils.delete_all_flows(self.controller, ipv6_logger)
#        self.assertEqual(rc, 0, "Failed to delete all flows")

        # Add entry match 

        request = message.flow_mod()
        request.match.type = ofp.OFPMT_OXM
        port = match.in_port(of_ports[0])
        eth_type = match.eth_type(IPV6_ETHERTYPE)
        eth_dst = match.eth_dst(parse.parse_mac("00:01:02:03:04:05"))
        ipv6_src = match.ipv6_src(ipaddr.IPv6Address('fe80::2420:52ff:fe8f:5189'))
        
        request.match_fields.tlvs.append(port)
        request.match_fields.tlvs.append(eth_type)
        request.match_fields.tlvs.append(eth_dst)
        request.match_fields.tlvs.append(ipv6_src)
        act = action.action_output()
        act.port = of_ports[3]
        inst = instruction.instruction_apply_actions()
        inst.actions.add(act)
        request.instructions.add(inst)
        request.buffer_id = 0xffffffff
        
        request.priority = 1000
        ipv6_logger.debug("Adding flow ")

        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Failed to insert test flow")

        #Send packet
        pkt = testutils.simple_ipv6_packet(dl_dst='00:01:02:03:04:05',ip_src='fe80::2420:52ff:fe8f:5189')
        ipv6_logger.info("Sending IPv6 packet to " + str(ing_port))
        ipv6_logger.debug("Data: " + str(pkt).encode('hex'))
        self.dataplane.send(ing_port, str(pkt))
        
        #Receive packet
        exp_pkt = testutils.simple_ipv6_packet()
        testutils.receive_pkt_verify(self, egr_port, exp_pkt)

        #See flow match
#        response = testutils.flow_stats_get(self)
#        ipv6_logger.debug(response.show())
        
        #Remove flows
        rc = testutils.delete_all_flows(self.controller, ipv6_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")


class MatchICMPv6Simple(basic.SimpleDataPlane):
    """
    Match on an ICMPv6 packet
    """
    def runTest(self):
        of_ports = ipv6_port_map.keys()
        of_ports.sort()
        ing_port = of_ports[0]
        egr_port = of_ports[3]
        
        # Remove all entries Add entry match all
        rc = testutils.delete_all_flows(self.controller, ipv6_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # Add entry match 

        request = message.flow_mod()
        request.match.type = ofp.OFPMT_OXM
        port = match.in_port(of_ports[0])
        eth_type = match.eth_type(IPV6_ETHERTYPE)
        ipv6_src = match.ipv6_src(ipaddr.IPv6Address('fe80::2420:52ff:fe8f:5189'))
        ip_proto = match.ip_proto(ICMPV6_PROTOCOL)
        icmpv6_type = match.icmpv6_type(128)
        
        request.match_fields.tlvs.append(port)
        request.match_fields.tlvs.append(eth_type)
        request.match_fields.tlvs.append(ipv6_src)
        request.match_fields.tlvs.append(ip_proto)
        request.match_fields.tlvs.append(icmpv6_type)
        
        act = action.action_output()
        act.port = of_ports[3]
        inst = instruction.instruction_apply_actions()
        inst.actions.add(act)
        request.instructions.add(inst)
        request.buffer_id = 0xffffffff
        
        request.priority = 1000
        ipv6_logger.debug("Adding flow ")
        
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Failed to insert test flow")

        #Send packet
        pkt = testutils.simple_icmpv6_packet()
        ipv6_logger.info("Sending IPv6 packet to " + str(ing_port))
        ipv6_logger.debug("Data: " + str(pkt).encode('hex'))
        self.dataplane.send(ing_port, str(pkt))
        
        #Receive packet
        exp_pkt = testutils.simple_icmpv6_packet()
        testutils.receive_pkt_verify(self, egr_port, exp_pkt)

        #See flow match
#        response = testutils.flow_stats_get(self)
#        ipv6_logger.debug("Response" + response.show())
        
        #Remove flows
        rc = testutils.delete_all_flows(self.controller, ipv6_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")    


class IPv6SetField(basic.SimpleDataPlane):

    def runTest(self):
        of_ports = ipv6_port_map.keys()
        of_ports.sort()
        ing_port = of_ports[0]
        egr_port = of_ports[3]
        
        # Remove all entries Add entry match all
        rc = testutils.delete_all_flows(self.controller, ipv6_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # Add entry match 

        request = message.flow_mod()
        request.match.type = ofp.OFPMT_OXM
        port = match.in_port(of_ports[0])
        eth_type = match.eth_type(IPV6_ETHERTYPE)
        ipv6_src = match.ipv6_src(ipaddr.IPv6Address('fe80::2420:52ff:fe8f:5189'))
        ip_proto = match.ip_proto(ICMPV6_PROTOCOL)
        icmpv6_type = match.icmpv6_type(128)
        
        request.match_fields.tlvs.append(port)
        request.match_fields.tlvs.append(eth_type)
#        request.match_fields.tlvs.append(eth_dst)
        request.match_fields.tlvs.append(ipv6_src)
        request.match_fields.tlvs.append(ip_proto)
        request.match_fields.tlvs.append(icmpv6_type)
        
        field_2b_set = match.ipv6_dst(ipaddr.IPv6Address('fe80::2420:52ff:fe8f:DDDD'))
        act_setfield = action.action_set_field()
        act_setfield.field = field_2b_set
        
#       TODO: insert action set field properly
        act_out = action.action_output()
        act_out.port = of_ports[3]
        
        
        inst = instruction.instruction_apply_actions()
        inst.actions.add(act_setfield)
        inst.actions.add(act_out)
        request.instructions.add(inst)
        request.buffer_id = 0xffffffff
        
        request.priority = 1000
        ipv6_logger.debug("Adding flow ")
        
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Failed to insert test flow")

        #Send packet
        pkt = simple_ipv6_packet()
        ipv6_logger.info("Sending IPv6 packet to " + str(ing_port))
        ipv6_logger.debug("Data: " + str(pkt).encode('hex'))
        self.dataplane.send(ing_port, str(pkt))
        
        #Receive packet
        exp_pkt = simple_ipv6_packet(ip_dst='fe80::2420:52ff:fe8f:DDDD')
        testutils.receive_pkt_verify(self, egr_port, exp_pkt)

        #See flow match
        response = testutils.flow_stats_get(self)
        ipv6_logger.debug("Response" + response.show())
        
        #Remove flows
        rc = testutils.delete_all_flows(self.controller, ipv6_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")    


class MatchIPv6TCP(basic.SimpleDataPlane):

    def runTest(self):
       	# Config
        of_ports = ipv6_port_map.keys()
        of_ports.sort()
        ing_port = of_ports[0]
        egr_port =   of_ports[3]
        
        # Remove flows
        rc = testutils.delete_all_flows(self.controller, ipv6_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # Add entry match 

        request = message.flow_mod()
        request.match.type = ofp.OFPMT_OXM
        port = match.in_port(of_ports[0])
        eth_type = match.eth_type(IPV6_ETHERTYPE)
        ipv6_src = match.ipv6_src(ipaddr.IPv6Address('fe80::2420:52ff:fe8f:5189'))        
        ip_proto = match.ip_proto(TCP_PROTOCOL)
        tcp_port = match.tcp_src(80)
        
        
        request.match_fields.tlvs.append(port)
        request.match_fields.tlvs.append(eth_type)
        request.match_fields.tlvs.append(ipv6_src)
        request.match_fields.tlvs.append(ip_proto)
        request.match_fields.tlvs.append(tcp_port)
        
        act = action.action_output()
        act.port = of_ports[3]
        inst = instruction.instruction_apply_actions()
        inst.actions.add(act)
        request.instructions.add(inst)
        request.buffer_id = 0xffffffff
        
        request.priority = 1000
        ipv6_logger.debug("Adding flow ")
        
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Failed to send test flow")

        #Send packet
        pkt = testutils.simple_ipv6_packet(tcp_sport=80, tcp_dport=8080) 

        ipv6_logger.info("Sending IPv6 packet to " + str(ing_port))
        ipv6_logger.debug("Data: " + str(pkt).encode('hex'))
        
        self.dataplane.send(ing_port, str(pkt))

        #Receive packet
        exp_pkt = testutils.simple_ipv6_packet(tcp_sport=80, tcp_dport=8080) 

        testutils.receive_pkt_verify(self, egr_port, exp_pkt)

        #See flow match
#        request_flow_stats()
        
        #Remove flows
        rc = testutils.delete_all_flows(self.controller, ipv6_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

# Receive and verify pkt
# testutils.receive_pkt_verify(self, egr_port, exp_pkt)
if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test-spec=ipv6"
