"""
Test cases for testing actions taken on packets

See basic.py for other info.

It is recommended that these definitions be kept in their own
namespace as different groups of tests will likely define 
similar identifiers.

  The switch is actively attempting to contact the controller at the address
indicated oin oft_config

"""

import logging
import ipaddr

from oftest import config
import ofp
import oftest.oft12.testutils as testutils
import oftest.base_tests as base_tests
import oftest.parse

TEST_VID_DEFAULT = 2

IPV6_ETHERTYPE = 0x86dd
ETHERTYPE_VLAN = 0x8100
ETHERTYPE_MPLS = 0x8847
TCP_PROTOCOL = 0x6
UDP_PROTOCOL = 0x11
ICMPV6_PROTOCOL = 0x3a


# TESTS
class MatchIPv6Simple(base_tests.SimpleDataPlane):
    """
    Just send a packet IPv6 to match a simple entry on the matching table
    """
    def runTest(self):
        
        of_ports = config["port_map"].keys()
        of_ports.sort()
        ing_port = of_ports[0]
        egr_port = of_ports[3]
        
        # Remove all entries Add entry match all
        rc = testutils.delete_all_flows(self.controller, logging)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # Add entry match 

        request = ofp.message.flow_add()
        port = ofp.oxm.in_port(of_ports[0])
        eth_type = ofp.oxm.eth_type(IPV6_ETHERTYPE)
        eth_dst = ofp.oxm.eth_dst(oftest.parse.parse_mac("00:01:02:03:04:05"))
        ipv6_src = ofp.oxm.ipv6_src(oftest.parse.parse_ipv6('fe80::2420:52ff:fe8f:5189'))
        
        request.match.oxm_list.append(port)
        request.match.oxm_list.append(eth_type)
        request.match.oxm_list.append(eth_dst)
        request.match.oxm_list.append(ipv6_src)
        act = ofp.action.output()
        act.port = of_ports[3]
        inst = ofp.instruction.apply_actions()
        inst.actions.append(act)
        request.instructions.append(inst)
        request.buffer_id = 0xffffffff
        
        request.priority = 1000
        logging.debug("Adding flow ")

        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Failed to insert test flow")

        #Send packet
        pkt = testutils.simple_ipv6_packet(dl_dst='00:01:02:03:04:05',ip_src='fe80::2420:52ff:fe8f:5189')
        logging.info("Sending IPv6 packet to " + str(ing_port))
        logging.debug("Data: " + str(pkt).encode('hex'))
        self.dataplane.send(ing_port, str(pkt))
        
        #Receive packet
        exp_pkt = testutils.simple_ipv6_packet()
        testutils.receive_pkt_verify(self, egr_port, exp_pkt)

        #Remove flows
        rc = testutils.delete_all_flows(self.controller, logging)
        self.assertEqual(rc, 0, "Failed to delete all flows")


class MatchICMPv6Simple(base_tests.SimpleDataPlane):
    """
    Match on an ICMPv6 packet
    """
    def runTest(self):
        of_ports = config["port_map"].keys()
        of_ports.sort()
        ing_port = of_ports[0]
        egr_port = of_ports[3]
        
        # Remove all entries Add entry match all
        rc = testutils.delete_all_flows(self.controller, logging)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # Add entry match 

        request = ofp.message.flow_add()
        port = ofp.oxm.in_port(of_ports[0])
        eth_type = ofp.oxm.eth_type(IPV6_ETHERTYPE)
        ipv6_src = ofp.oxm.ipv6_src(oftest.parse.parse_ipv6('fe80::2420:52ff:fe8f:5189'))
        ip_proto = ofp.oxm.ip_proto(ICMPV6_PROTOCOL)
        icmpv6_type = ofp.oxm.icmpv6_type(128)
        
        request.match.oxm_list.append(port)
        request.match.oxm_list.append(eth_type)
        request.match.oxm_list.append(ipv6_src)
        request.match.oxm_list.append(ip_proto)
        request.match.oxm_list.append(icmpv6_type)
        
        act = ofp.action.output()
        act.port = of_ports[3]
        inst = ofp.instruction.apply_actions()
        inst.actions.append(act)
        request.instructions.append(inst)
        request.buffer_id = 0xffffffff
        
        request.priority = 1000
        logging.debug("Adding flow ")
        
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Failed to insert test flow")

        #Send packet
        pkt = testutils.simple_icmpv6_packet()
        logging.info("Sending IPv6 packet to " + str(ing_port))
        logging.debug("Data: " + str(pkt).encode('hex'))
        self.dataplane.send(ing_port, str(pkt))
        
        #Receive packet
        exp_pkt = testutils.simple_icmpv6_packet()
        testutils.receive_pkt_verify(self, egr_port, exp_pkt)

        #Remove flows
        rc = testutils.delete_all_flows(self.controller, logging)
        self.assertEqual(rc, 0, "Failed to delete all flows")    


class IPv6SetField(base_tests.SimpleDataPlane):

    def runTest(self):
        of_ports = config["port_map"].keys()
        of_ports.sort()
        ing_port = of_ports[0]
        egr_port = of_ports[3]
        
        # Remove all entries Add entry match all
        rc = testutils.delete_all_flows(self.controller, logging)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # Add entry match 

        request = ofp.message.flow_add()
        port = ofp.oxm.in_port(of_ports[0])
        eth_type = ofp.oxm.eth_type(IPV6_ETHERTYPE)
        ipv6_src = ofp.oxm.ipv6_src(oftest.parse.parse_ipv6('fe80::2420:52ff:fe8f:5189'))
        
        request.match.oxm_list.append(port)
        request.match.oxm_list.append(eth_type)
        request.match.oxm_list.append(ipv6_src)
        
        field_2b_set = ofp.oxm.ipv6_dst(oftest.parse.parse_ipv6('fe80::2420:52ff:fe8f:DDDD'))
        act_setfield = ofp.action.set_field()
        act_setfield.field = field_2b_set.pack() # HACK
        
#       TODO: insert action set field properly
        act_out = ofp.action.output()
        act_out.port = of_ports[3]
        
        
        inst = ofp.instruction.apply_actions()
        inst.actions.append(act_setfield)
        inst.actions.append(act_out)
        request.instructions.append(inst)
        request.buffer_id = 0xffffffff
        
        request.priority = 1000
        logging.debug("Adding flow ")
        
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Failed to insert test flow")

        #Send packet
        pkt = testutils.simple_ipv6_packet(ip_src='fe80::2420:52ff:fe8f:5189',ip_dst='fe80::2420:52ff:fe8f:5190')
        logging.info("Sending IPv6 packet to " + str(ing_port))
        logging.debug("Data: " + str(pkt).encode('hex'))
        self.dataplane.send(ing_port, str(pkt))
        
        #Receive packet
        exp_pkt = testutils.simple_ipv6_packet(ip_dst='fe80::2420:52ff:fe8f:DDDD')
        testutils.receive_pkt_verify(self, egr_port, exp_pkt)

        #See flow match
        response = testutils.flow_stats_get(self)
        logging.debug("Response" + response.show())
        
        #Remove flows
        rc = testutils.delete_all_flows(self.controller, logging)
        self.assertEqual(rc, 0, "Failed to delete all flows")    


class MatchIPv6TCP(base_tests.SimpleDataPlane):

    def runTest(self):
       	# Config
        of_ports = config["port_map"].keys()
        of_ports.sort()
        ing_port = of_ports[0]
        egr_port =   of_ports[3]
        
        # Remove flows
        rc = testutils.delete_all_flows(self.controller, logging)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        # Add entry match 

        request = ofp.message.flow_add()
        request.match.type = ofp.OFPMT_OXM
        port = ofp.oxm.in_port(of_ports[0])
        eth_type = ofp.oxm.eth_type(IPV6_ETHERTYPE)
        ipv6_src = ofp.oxm.ipv6_src(oftest.parse.parse_ipv6('fe80::2420:52ff:fe8f:5189'))
        ip_proto = ofp.oxm.ip_proto(TCP_PROTOCOL)
        tcp_port = ofp.oxm.tcp_src(80)
        
        
        request.match.oxm_list.append(port)
        request.match.oxm_list.append(eth_type)
        request.match.oxm_list.append(ipv6_src)
        request.match.oxm_list.append(ip_proto)
        request.match.oxm_list.append(tcp_port)
        
        act = ofp.action.output()
        act.port = of_ports[3]
        inst = ofp.instruction.apply_actions()
        inst.actions.append(act)
        request.instructions.append(inst)
        request.buffer_id = 0xffffffff
        
        request.priority = 1000
        logging.debug("Adding flow ")
        
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Failed to send test flow")

        #Send packet
        pkt = testutils.simple_ipv6_packet(tcp_sport=80, tcp_dport=8080) 

        logging.info("Sending IPv6 packet to " + str(ing_port))
        logging.debug("Data: " + str(pkt).encode('hex'))
        
        self.dataplane.send(ing_port, str(pkt))

        #Receive packet
        exp_pkt = testutils.simple_ipv6_packet(tcp_sport=80, tcp_dport=8080) 

        testutils.receive_pkt_verify(self, egr_port, exp_pkt)

        #Remove flows
        rc = testutils.delete_all_flows(self.controller, logging)
        self.assertEqual(rc, 0, "Failed to delete all flows")

if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test-spec=ipv6"
