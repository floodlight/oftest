"""These tests fall under Conformance Test-Suite (OF-SWITCH-1.0.0 TestCases).
    Refer Documentation -- Detailed testing methodology 
    <Some of test-cases are directly taken from oftest> """

"Test Suite 6 --> Flow Matches"


import logging

import unittest
import random

from oftest import config
import oftest.controller as controller
import ofp
import oftest.dataplane as dataplane
import oftest.parse as parse
import oftest.base_tests as base_tests
import time

from oftest.testutils import *
from time import sleep
from FuncUtils import *



class AllWildcardMatch(base_tests.SimpleDataPlane):

    """Verify for an all wildcarded flow all the injected packets would match that flow"""

    def runTest(self):
        
        logging.info("Running All Wildcard Match test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear Switch State
        delete_all_flows(self.controller)

        logging.info("Inserting an all wildcarded flow and sending packets with various match fields")
        logging.info("Expecting all sent packets to match")

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        #Insert an All Wildcarded flow.
        wildcard_all(self,of_ports)

        #check for different  match fields and verify packet implements the action specified in the flow
        pkt1 = simple_tcp_packet(dl_src="00:01:01:01:01:01");
        self.dataplane.send(of_ports[0], str(pkt1))
        receive_pkt_check(self.dataplane,pkt1,[yes_ports],no_ports,self)
       
        pkt2 = simple_tcp_packet(dl_dst="00:01:01:01:01:01");    
        self.dataplane.send(of_ports[0], str(pkt2))
        receive_pkt_check(self.dataplane,pkt2,[yes_ports],no_ports,self)
        
        pkt3 = simple_tcp_packet(ip_src="192.168.2.1");
        self.dataplane.send(of_ports[0], str(pkt3))
        receive_pkt_check(self.dataplane,pkt3,[yes_ports],no_ports,self)
        
        pkt4 = simple_tcp_packet(ip_dst="192.168.2.2");
        self.dataplane.send(of_ports[0], str(pkt4))
        receive_pkt_check(self.dataplane,pkt4,[yes_ports],no_ports,self)
        
        pkt5 = simple_tcp_packet(ip_tos=2);
        self.dataplane.send(of_ports[0], str(pkt5))
        receive_pkt_check(self.dataplane,pkt5,[yes_ports],no_ports,self)
       
        pkt6 = simple_tcp_packet(tcp_sport=8080);
        self.dataplane.send(of_ports[0], str(pkt6))
        receive_pkt_check(self.dataplane,pkt6,[yes_ports],no_ports,self)
              
        pkt7 = simple_tcp_packet(tcp_dport=8081);
        self.dataplane.send(of_ports[0], str(pkt7))
        receive_pkt_check(self.dataplane,pkt7,[yes_ports],no_ports,self)



class EthernetSrcAddress(base_tests.SimpleDataPlane):
    
    """Verify match on single header field -- Ethernet Src Address """
    
    def runTest(self):

        logging.info("Running Ethernet Src Address test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        delete_all_flows(self.controller)

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Inserting a flow with match on Ethernet Source Address ")
        logging.info("Sending matching and non-matching ethernet packets")
        logging.info("Verifying only matching packets implements the action specified in the flow")

        #Insert a Match On Ethernet Src Address flow
        (pkt,match) = match_ethernet_src_address(self,of_ports)   

        #Sending packet matching the flow, verify it implements the action
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Sending non matching packet , verify Packetin event gets triggered.
        pkt2 = simple_eth_packet(dl_src='00:01:01:01:01:02');
        self.dataplane.send(of_ports[0], str(pkt2))
        
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packets")

class EthernetDstAddress(base_tests.SimpleDataPlane):
    
    """Verify match on single Header Field Field -- Ethernet Dst Address """

    def runTest(self):

        logging.info("Running Ethernet Dst Address test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear Switch State
        delete_all_flows(self.controller)

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
        
        logging.info("Inserting a flow with match on Ethernet Destination Address ")
        logging.info("Sending matching and non-matching ethernet packets")
        logging.info("Verifying only matching packets implements the action specified in the flow")
        
        #Insert a Match on Destination Address flow   
        (pkt,match) = match_ethernet_dst_address(self,of_ports)
        
        #Send Packet matching the flow 
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)
        
        #Send Non-matching packet
        pkt2 = simple_eth_packet(dl_dst='00:01:01:01:01:02');
        self.dataplane.send(of_ports[0], str(pkt2))
        
        #Verify PacketIn event gets triggered
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")


class EthernetType(base_tests.SimpleDataPlane):
    
    """Verify match on single header field -- Ethernet Type """
    
    def runTest(self):

        logging.info("Running Ethernet Type test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        delete_all_flows(self.controller)

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
        
        logging.info("Inserting a flow with match on Ethernet Type ")
        logging.info("Sending matching and non-matching ethernet packets")
        logging.info("Verifying only matching packets implements the action specified in the flow")

        #Insert a Match on Ethernet-Type flow
        (pkt,match) = match_ethernet_type(self,of_ports)   

        #Sending packet matching the flow 
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Sending non matching packet , 
        pkt2 = simple_eth_packet(dl_type=0x0806);
        self.dataplane.send(of_ports[0], str(pkt2))
        
        #verify Packetin event gets triggered.
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non-matching packet")

            
class IngressPort(base_tests.SimpleDataPlane):
    
    """Verify match on single Header Field Field -- In_port """

    def runTest(self):

        logging.info("Running Ingress Port test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear Switch State
        delete_all_flows(self.controller)

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Inserting a flow with match on Ingress Port ")
        logging.info("Sending matching and non-matching packets")
        logging.info("Verifying only matching packets implements the action specified in the flow")
        
        #Insert a Match on Ingress Port FLow
        (pkt,match) = wildcard_all_except_ingress(self,of_ports,priority=0)
        
        #Send Packet matching the flow i.e on in_port specified in the flow
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Send Non-Matching Packet 
        self.dataplane.send(of_ports[1],str(pkt))

        #Verify PacketIn event gets triggered
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non-matching packet")

class VlanId(base_tests.SimpleDataPlane):

    """Verify match on single Header Field Field -- Vlan Id """

    def runTest(self):

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear Switch State
        delete_all_flows(self.controller)

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Inserting a flow with match on VLAN ID ")
        logging.info("Sending matching and non-matching tagged packets")
        logging.info("Verifying matching packets implements the action specified in the flow")
    
        #Create a flow with match on Vlan Id
        (pkt,match) = match_vlan_id(self,of_ports)

        #Send tagged packet matching the flow i.e packet with same vlan id as in flow
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)
        
        #Send Non-matching packet, i.e packet with different Vlan Id
        pkt2 = simple_tcp_packet(dl_vlan_enable=True,dl_vlan=4);
        self.dataplane.send(of_ports[0], str(pkt2))
        
        #Verify PacketIn event gets triggered
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")

class VlanPCP(base_tests.SimpleDataPlane):

    """"Verify match on single Header Field Field -- Vlan Priority"""

    def runTest(self):

        logging.info("Running VlanPCP1 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        delete_all_flows(self.controller)

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Inserting a flow with match on VLAN Priority ")
        logging.info("Sending matching and non-matching tagged packets")
        logging.info("Verifying matching packet implements the action specified in the flow")

        #Create a flow matching on VLAN Priority
        (pkt,match) = match_vlan_pcp(self,of_ports)

        #Send tagged Packet matching the flow 
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)
        
        #Send tagged packet with same vlan_id but different vlan priority
        pkt2 = simple_tcp_packet(dl_vlan_enable=True,dl_vlan=1,dl_vlan_pcp=20);
        self.dataplane.send(of_ports[0], str(pkt2))

        #Verify Packet_In event gets triggered
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")
       
class MultipleHeaderFieldL2(base_tests.SimpleDataPlane):
    
    """Verify match on multiple header field -- Ethernet Type, Ethernet Source Address, Ethernet Destination Address """
    
    def runTest(self):

        logging.info("Running Multiple Header Field L2 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        delete_all_flows(self.controller)

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Inserting a flow with match on Multiple Header Fields in L2 ")
        logging.info("Sending matching and non-matching packets")
        logging.info("Verifying matching packets implements the action specified in the flow")

        (pkt,match) = match_mul_l2(self,of_ports)   

        #Send eth packet matching the dl_type field, verify it implements the action
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Sending non matching packet (only dl_dst is different) , verify Packetin event gets triggered.
        pkt2 = simple_eth_packet(dl_type=0x88cc,dl_src='00:01:01:01:01:01',dl_dst='00:01:01:02:01:01');
        self.dataplane.send(of_ports[0], str(pkt2))
        
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")

        #Sending non matching packet (only dl_src is different) , verify Packetin event gets triggered.
        pkt2 = simple_eth_packet(dl_type=0x88cc,dl_src='00:01:01:01:01:02',dl_dst='00:01:01:01:01:02');
        self.dataplane.send(of_ports[0], str(pkt2))
        
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")

        #Sending non matching packet (only ether_type is different) , verify Packetin event gets triggered.
        pkt2 = simple_eth_packet(dl_type=0x0806,dl_src='00:01:01:01:01:01',dl_dst='00:01:01:01:01:02');
        self.dataplane.send(of_ports[0], str(pkt2))
        
        #Verify packet_in event gets triggered
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")

class IpTos(base_tests.SimpleDataPlane):

    """"Verify match on single Header Field Field -- Type of service"""

    def runTest(self):

        logging.info("Running Ip_Tos test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        delete_all_flows(self.controller)

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Inserting a flow with match on Ip_Tos ")
        logging.info("Sending matching and non-matching tcp/ip packets")
        logging.info("Verifying only matching packets implements the action specified in the flow")

        #Create a flow matching on VLAN Priority
        (pkt,match) = match_ip_tos(self,of_ports)

        #Send Packet matching the flow 
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)
        
        #Create a non-matching packet , verify packet_in get generated
        pkt2 = simple_tcp_packet(ip_tos=4);
        self.dataplane.send(of_ports[0], str(pkt2))
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")

class IpProtocol(base_tests.SimpleDataPlane):

    """"Verify match on single Header Field Field -- Ip Protocol"""

    def runTest(self):

        logging.info("Running Ip Protocol test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        delete_all_flows(self.controller)

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Inserting a flow with match on Ip Protocol ")
        logging.info("Sending matching and non-matching tcp/ip packets")
        logging.info("Verifying only matching packets implements the action specified in the flow")

        #Create a flow matching on VLAN Priority
        (pkt,match) = match_ip_protocol(self,of_ports)

        #Send Packet matching the flow 
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)
        
        #Create a non-matching packet , verify packet_in get generated
        pkt2 = simple_icmp_packet();
        self.dataplane.send(of_ports[0], str(pkt2))
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")


class TcpSrcPort(base_tests.SimpleDataPlane):
    
    """Verify match on Single header field -- Tcp Source Port,  """
    
    def runTest(self):

        logging.info("Running Tcp Src Port test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        delete_all_flows(self.controller)

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Inserting a flow with match on Tcp Tcp Source Port ")
        logging.info("Sending matching and non-matching tcp packets")
        logging.info("Verifying matching packets implements the action specified in the flow")

        (pkt,match) = match_tcp_src(self,of_ports)   

        #Sending packet matching the tcp_sport, verify it implements the action
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Sending non matching packet , verify Packetin event gets triggered.
        pkt2 = simple_tcp_packet(tcp_sport=540);
        self.dataplane.send(of_ports[0], str(pkt2))
        
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")

class TcpDstPort(base_tests.SimpleDataPlane):
    
    """Verify match on Single header field -- Tcp Destination Port """
    
    def runTest(self):

        logging.info("Running Tcp Destination Port test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        delete_all_flows(self.controller)

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
        
        logging.info("Inserting a flow with match on Tcp Destination Port ")
        logging.info("Sending matching and non-matching packets")
        logging.info("Verifying matching packets implements the action specified in the flow")

        (pkt,match) = match_tcp_dst(self,of_ports)   

        #Sending packet matching the tcp_dport, verify it implements the action
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Sending non matching packet , verify Packetin event gets triggered.
        pkt2 = simple_tcp_packet(tcp_dport=541);
        self.dataplane.send(of_ports[0], str(pkt2))
        
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=10)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")

class UdpSrcPort(base_tests.SimpleDataPlane):
    
    """Verify match on Single header field -- Udp Source Port,  """
    
    def runTest(self):

        logging.info("Running Udp Src Port test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        delete_all_flows(self.controller)

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Inserting a flow with match on Udp Udp Source Port ")
        logging.info("Sending matching and non-matching tcp packets")
        logging.info("Verifying matching packets implements the action specified in the flow")

        (pkt,match) = match_udp_src(self,of_ports)   

        #Sending packet matching the tcp_sport, verify it implements the action
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Sending non matching packet , verify Packetin event gets triggered.
        pkt2 = simple_udp_packet(udp_sport=540);
        self.dataplane.send(of_ports[0], str(pkt2))
        
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")

class UdpDstPort(base_tests.SimpleDataPlane):
    
    """Verify match on Single header field -- Udp Destination Port """
    
    def runTest(self):

        logging.info("Running Udp Destination Port test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        delete_all_flows(self.controller)

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
        
        logging.info("Inserting a flow with match on Udp Destination Port ")
        logging.info("Sending matching and non-matching packets")
        logging.info("Verifying matching packets implements the action specified in the flow")

        (pkt,match) = match_udp_dst(self,of_ports)   

        #Sending packet matching the tcp_dport, verify it implements the action
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Sending non matching packet , verify Packetin event gets triggered.
        pkt2 = simple_udp_packet(udp_dport=541);
        self.dataplane.send(of_ports[0], str(pkt2))
        
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=10)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")

class ICMPType(base_tests.SimpleDataPlane):
    
    """Verify match on Single header field -- ICMP type,  """

    def runTest(self):

        logging.info("Running ICMP type test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        delete_all_flows(self.controller)

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Inserting a flow with match on ICMP type")
        logging.info("Sending matching and non-matching ICMP packets")
        logging.info("Verifying matching packets implements the action specified in the flow")

        (pkt,match) = match_icmp_type(self,of_ports)   

        #Sending packet matching the tcp_sport, verify it implements the action
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Sending non matching packet , verify Packetin event gets triggered.
        pkt2 = simple_icmp_packet(icmp_type=10);
        self.dataplane.send(of_ports[0], str(pkt2))
        
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")

class ICMPCode(base_tests.SimpleDataPlane):
    
    """Verify match on Single header field -- ICMP code,  """

    def runTest(self):

        logging.info("Running ICMP code test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        delete_all_flows(self.controller)

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Inserting a flow with match on ICMP type")
        logging.info("Sending matching and non-matching ICMP packets")
        logging.info("Verifying matching packets implements the action specified in the flow")

        (pkt,match) = match_icmp_code(self,of_ports)   

        #Sending packet matching the tcp_dport, verify it implements the action
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Sending non matching packet , verify Packetin event gets triggered.
        pkt2 = simple_icmp_packet(icmp_code=10);
        self.dataplane.send(of_ports[0], str(pkt2))
        
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")


class ArpSenderIP(base_tests.SimpleDataPlane):

    """"Verify match on single Header Field -- Arp Protocol"""

    def runTest(self):

        logging.info("Running Arp Protocol test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        delete_all_flows(self.controller)

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Inserting a flow with match on Arp Protocol ")
        logging.info("Sending matching and non-matching arp packets")
        logging.info("Verifying only matching packets implements the action specified in the flow")

        #Create a flow matching on ARP sender IP
        (pkt,match) = match_arp_sender(self,of_ports)

        #Send Packet matching the flow 
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)
        
        #Create a non-matching packet , verify packet_in get generated
        pkt2 = simple_arp_packet(ip_snd="10.10.0.10");
        self.dataplane.send(of_ports[0], str(pkt2))
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")

class ArpTargetIP(base_tests.SimpleDataPlane):

    """"Verify match on single Header Field -- Arp Protocol"""

    def runTest(self):

        logging.info("Running Arp Protocol test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        delete_all_flows(self.controller)

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Inserting a flow with match on Arp Protocol ")
        logging.info("Sending matching and non-matching arp packets")
        logging.info("Verifying only matching packets implements the action specified in the flow")

        #Create a flow matching on ARP target IP
        (pkt,match) = match_arp_target(self,of_ports)

        #Send Packet matching the flow 
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)
        
        #Create a non-matching packet , verify packet_in get generated
        pkt2 = simple_arp_packet(ip_tgt="10.10.0.10");
        self.dataplane.send(of_ports[0], str(pkt2))
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")


class ExactMatch(base_tests.SimpleDataPlane):
    
    """Verify match on Single header field -- Exact Match  """
    
    def runTest(self):

        logging.info("Running Tcp Exact Match test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        delete_all_flows(self.controller)

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
        
        logging.info("Inserting a flow with match for Exact Match ")
        logging.info("Sending matching and non-matching packets")
        logging.info("Verifying matching packets implements the action specified in the flow")

        (pkt,match) = exact_match(self,of_ports)   

        #Sending packet matching all the fields of a tcp_packet, verify it implements the action
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Sending non matching packet , verify Packetin event gets triggered.
        pkt2 = simple_tcp_packet(tcp_sport=540);
        self.dataplane.send(of_ports[0], str(pkt2))
        
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")


class MultipleHeaderFieldL4(base_tests.SimpleDataPlane):
    
    """Verify match on multiple header field -- Tcp Source Port, Tcp Destination Port  """
    
    def runTest(self):

        logging.info("Running Multiple Header Field L4 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        delete_all_flows(self.controller)

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
        
        logging.info("Inserting a flow with match on Multiple Header Field L4 ")
        logging.info("Sending matching and non-matching packets")
        logging.info("Verifying matching packets implements the action specified in the flow")

        (pkt,match) = match_mul_l4(self,of_ports)   

        #Sending packet matching the tcp_sport and tcp_dport field, verify it implements the action
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Sending non matching packet (tcp_dport different), verify Packetin event gets triggered.
        pkt2 = simple_tcp_packet(tcp_sport=111,tcp_dport=541);
        self.dataplane.send(of_ports[0], str(pkt2))
        
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")

        #Sending non matching packet (tcp_sport different), verify Packetin event gets triggered.
        pkt2 = simple_tcp_packet(tcp_sport=100,tcp_dport=112);
        self.dataplane.send(of_ports[0], str(pkt2))
        
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")


class ExactMatchPrio(base_tests.SimpleDataPlane):
    
    """Verify that Exact Match has highest priority """
    
    def runTest(self):

        logging.info("Running Exact Match High Priority test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        delete_all_flows(self.controller)

        egress_port=of_ports[2]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = egress_port
    
        logging.info("Inserting a flow with Exact Match (low priority)")
        logging.info("Inserting an overlapping wildcarded flow (higher priority)")
        logging.info("Sending packets matching both the flows ")
        logging.info("Verifying matching packets implements the action specified in the exact match flow")

        #Insert two Overlapping Flows : Exact Match and Wildcard All.
        (pkt,match) = exact_match_with_prio(self,of_ports,priority=10) 
        (pkt2,match2) = wildcard_all(self,of_ports,priority=20);  
        
        #Sending packet matching both the flows , 
        self.dataplane.send(of_ports[0], str(pkt2))

        #verify it implements the action specified in Exact Match Flow
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)


class WildcardMatchPrio(base_tests.SimpleDataPlane):
    
    """Verify that Wildcard Match with highest priority overrides the low priority WildcardMatch """
    
    def runTest(self):

        logging.info("Running Wildcard Match High Priority test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        delete_all_flows(self.controller)

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Inserting two wildcarded flows with priorities ")
        logging.info("Sending packets matching the flows")
        logging.info("Verifying matching packets implements the action specified in the flow with higher priority")

        (pkt,match) = wildcard_all(self,of_ports,priority=20) 
        (pkt1,match1) =  wildcard_all_except_ingress1(self,of_ports,priority=10)  

        #Sending packet matching both the flows , verify it implements the action specified by Higher Priority flow
        self.dataplane.send(of_ports[0], str(pkt1))
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)





