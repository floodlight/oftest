"""These tests fall under Conformance Test-Suite (OF-SWITCH-1.0.0 TestCases).
    Refer Documentation -- Detailed testing methodology 
    <Some of test-cases are directly taken from oftest> """

"Test Suite 6 --> Flow Matches"


import logging

import unittest
import random

import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action
import oftest.parse as parse
import oftest.base_tests as base_tests
import time

from oftest.oflog import *
from oftest.testutils import *
from time import sleep
from FuncUtils import *



class Grp50No10(base_tests.SimpleDataPlane):

    """Verify for an all wildcarded flow all the injected packets would match that flow"""
    @wireshark_capture
    
    def runTest(self):
        logging = get_logger()
        logging.info("Running All Wildcard Match Grp50No10 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear Switch State
        rc = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        logging.info("Installing an all wildcarded flow")
        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]

        #Insert an All Wildcarded flow.
        wildcard_all(self,of_ports)

        #check for different  match fields and verify packet implements the action specified in the flow
        logging.info("Sending packets with different match fields and verifying that all packets match the flow entry")
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


class Grp50No20(base_tests.SimpleDataPlane):
    
    """Verify match on single Header Field Field -- In_port """

    @wireshark_capture
    
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp50No20 Ingress Port test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear Switch State
        rc = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Installing a flow with match on Ingress Port ")
        
        #Insert a Match on Ingress Port FLow
        (pkt,match) = wildcard_all_except_ingress(self,of_ports,priority=0)
        
        #Send Packet matching the flow i.e on in_port specified in the flow
        logging.info("Sending a packet that matches the flow entry")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Send Non-Matching Packet 
        logging.info("Sending a packet on a different port")
        self.dataplane.send(of_ports[1],str(pkt))

        #Verify PacketIn event gets triggered
        logging.info("Waiting for a Packet_in message from the Switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non-matching packet")
        logging.info("Packet_in received")

class Grp50No30(base_tests.SimpleDataPlane):
    
    """Verify match on single header field -- Ethernet Src Address  """
    @wireshark_capture
    
    def runTest(self):
        logging = get_logger()
        logging.info("Running Ethernet Src Address Grp50No30 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        rc = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Installing a flow entry with match on ETH_SRC ")

        #Insert a Match On Ethernet Src Address flow
        (pkt,match) = match_ethernet_src_address(self,of_ports)   

        #Sending packet matching the flow, verify it implements the action
        
        logging.info("Sending a Packet which matches the flow entry")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Sending non matching packet , verify Packetin event gets triggered.
        logging.info("Sending a non matching packet")
        pkt2 = simple_eth_packet(dl_src='AC:81:12:99:47:0F', dl_dst='AC:81:12:99:47:0F',dl_type = 0x88cc);
        self.dataplane.send(of_ports[0], str(pkt2))
        
        logging.info("Waiting for a packet_in message from the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packets")
        logging.info("Packet_in recevied")


class Grp50No40(base_tests.SimpleDataPlane):
    
    """Verify match on single Header Field Field -- Ethernet Dst Address """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp50No40 Ethernet Dst Address test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear Switch State
        rv = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
        
        logging.info("Installing a flow entry with match on ETH_DST ")
        
        #Insert a Match on Destination Address flow   
        (pkt,match) = match_ethernet_dst_address(self,of_ports)
        
        #Send Packet matching the flow 
        logging.info("Sending a matching packet")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)
        
        #Send Non-matching packet
        logging.info("Sending a non matching packet")
        pkt2 = simple_eth_packet(dl_dst='AC:81:12:99:47:0F',dl_src ='da:c9:f1:19:72:cf',dl_type = 0x88cc);
        self.dataplane.send(of_ports[0], str(pkt2))
        
        #Verify PacketIn event gets triggered
        logging.info("Waiting for packet_in message from the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=10)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")
        logging.info("Packet_in Received")

class Grp50No50(base_tests.SimpleDataPlane):
    
    """Verify match on single header field -- Ethernet Type """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp50No50 Ethernet Type test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        rc = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
        
        logging.info("Installing a flow entry with match on Ethernet Type ")
        
        #Insert a Match on Ethernet-Type flow
        (pkt,match) = match_ethernet_type(self,of_ports)   

        #Sending packet matching the flow 
        logging.info("Sending a matching packet")
        self.dataplane.send(of_ports[0], str(pkt))
        sleep(1)

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)
        
        #Send non-matching packet 
        logging.info("Sending a non matching packet")
        pkt3 = simple_eth_packet(dl_dst='AC:81:12:99:47:0F',dl_src ='da:c9:f1:19:72:cf',dl_type = 0x0805)
        self.dataplane.send(of_ports[0],str(pkt3))

        #verify Packetin event gets triggered.
        logging.info("Waiting for a packet_in message from the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non-matching packet")
        logging.info("Packet_in Received")
            

class Grp50No60(base_tests.SimpleDataPlane):

    """Verify match on single Header Field Field -- Vlan Id """

    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp50No60 Match on Vlan Id  test")
        
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear Switch State
        rc = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Installing a flow entry with match on VLAN ID ")
          
        #Create a flow with match on Vlan Id
        (pkt,match) = match_vlan_id(self,of_ports)

        #Send tagged packet matching the flow i.e packet with same vlan id as in flow
        logging.info("Sending a tagged matching packet")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)
        
        #Send Non-matching packet, i.e packet with different Vlan Id
        logging.info("Sending a non matching packet")
        pkt2 = simple_tcp_packet(dl_vlan_enable=True,dl_vlan=4);
        self.dataplane.send(of_ports[0], str(pkt2))
        
        #Verify PacketIn event gets triggered
        logging.info("waiting for a packet_in message from the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")
        logging.info("Packet_in Received")


class Grp50No70(base_tests.SimpleDataPlane):

    """"Verify match on single Header Field Field -- Vlan Priority"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp50No70 VlanPCP test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        rv = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
	
	egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Installing a flow entry with match on VLAN Priority ")

        #Create a flow matching on VLAN Priority
        (pkt,match) = match_vlan_pcp(self,of_ports)

        #Send tagged Packet matching the flow 
        logging.info("Sending a tagged matching packet")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)
        
        #Send tagged packet with same vlan_id but different vlan priority
        logging.info("Sending a non matching packet")
        pkt2 = simple_tcp_packet(dl_vlan_enable=True,dl_vlan=1,dl_vlan_pcp=2);
        self.dataplane.send(of_ports[0], str(pkt2))

        #Verify Packet_In event gets triggered
        logging.info("Waiting for a packet_in message from the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")
        logging.info("Packet_in Received")


class Grp50No80a(base_tests.SimpleDataPlane):

    """"Verify match on single Header Field Field -- IP_SRC_ADDRESS 
    Generates an exact match here"""
    @wireshark_capture
    def runTest(self):

        logging = get_logger()
        logging.info("Running Grp50No80a exact Matching on IP_SRC test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        rv = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]

        #Create a simple tcp packet and generate match on ip src address , exact match 
        logging.info("Installing a flow entry with match on IP_SRC address")
        pkt = simple_tcp_packet(ip_src='192.168.100.100')
        match = parse.packet_to_flow_match(pkt)
        #Wildcards -- 
        match.wildcards = 0xffffc0cf 
        msg = message.flow_mod()
        msg.match = match
        act = action.action_output()
        act.port = of_ports[1]
        rv = msg.actions.add(act)
        self.assertTrue(rv, "Could not add output action " + 
                        str(of_ports[1]))
        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")  

        #Send Packet matching the flow 
        logging.info("Sending a matching packet")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Send a non-matching packet , verify packet_in gets triggered
        logging.info("Sending a non matching packet")
        pkt2 = simple_tcp_packet(ip_src='149.165.130.66')
        self.dataplane.send(of_ports[0], str(pkt2))
        logging.info("Waiting for a packet_in message from the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")
	logging.info("Packet_in received")

class Grp50No80b(base_tests.SimpleDataPlane):

    """"Verify match on single Header Field Field -- IP_SRC_ADDRESS 
    Wildcards all bits in ip_src_address here"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp50No80b widlcard Matching on IP_SRC test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        rv = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
   	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
        
        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]

        #Create a simple tcp packet and generate match on ip src address
        logging.info("Installing a flow entry with match on wildcard IP_SRC")
        pkt = simple_tcp_packet(ip_src='192.168.100.100')
        match = parse.packet_to_flow_match(pkt)
        match.wildcards = 0xffffffcf
        msg = message.flow_mod()
        msg.match = match
        act = action.action_output()
        act.port = of_ports[1]
        rv = msg.actions.add(act)
        self.assertTrue(rv, "Could not add output action " + 
                            str(of_ports[1]))
        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed") 
        
        #Send Packet matching the flow 
        logging.info("sending a matching packet")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)
        #Send a non-matching packet , verify it also matches the flow_entry
        logging.info("sending a non matching packet")
        pkt2 = simple_tcp_packet(ip_src='149.165.130.66')
        self.dataplane.send(of_ports[0], str(pkt2))
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt2,[yes_ports],no_ports,self)


class Grp50No80c(base_tests.SimpleDataPlane):

    """"Verify match on single Header Field Field -- IP_SRC_ADDRESS 
    Generates an match with wildcarding certain number of bits in ip_address"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Ip_Src test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        rv = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]

        #Create a simple tcp packet and generate match on ip src address
        logging.info("Installing a flow entry with match on MSB in the IP_SRC")
        pkt = simple_tcp_packet(ip_src='192.168.100.100')
        match = parse.packet_to_flow_match(pkt)
        match.wildcards = 0x3fffd9cf
        msg = message.flow_mod()
        msg.match = match
        act = action.action_output()
        act.port = of_ports[1]
        rv = msg.actions.add(act)
        self.assertTrue(rv, "Could not add output action " + 
                            str(of_ports[1]))
        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed") 

        #Send Packet matching the flow 
        logging.info("Sending a Matching Packet")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Send a matching packet , with only LSB different than the ip-address matched against
        logging.info("Sending another matching packet with different IP_SRC(same MSB)")
        pkt2 = simple_tcp_packet(ip_src='192.170.100.101')
        self.dataplane.send(of_ports[0], str(pkt2))

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt2,[yes_ports],no_ports,self)
        
        #Send a non-matching packet , verify packet_in gets triggered
        logging.info("Sending a non matching packet")
        pkt3 = simple_tcp_packet(ip_src='200.168.100.100')
        self.dataplane.send(of_ports[0], str(pkt3))
        logging.info("Waiting for a packet_in from the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")
        logging.info("Received a Packet_in")

class Grp50No90a(base_tests.SimpleDataPlane):

    """"Verify match on single Header Field Field -- IP_DST_ADDRESS 
    Generates an exact match here"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp50No90a IP_DST test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        rv = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
        
        #Create a flow for match on ip_dst_address (exact match)
        logging.info("Installing a flow entry with exact match on IP_DST")
        pkt = simple_tcp_packet(ip_src='192.168.100.100')
        match = parse.packet_to_flow_match(pkt)
        match.wildcards = 0x3ff03fcf
        msg = message.flow_mod()
        msg.match = match
        act = action.action_output()
        act.port = of_ports[1]
        rv = msg.actions.add(act)
        self.assertTrue(rv, "Could not add output action " + 
                            str(of_ports[1]))
        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed") 
        
        #Send Packet matching the flow 
        logging.info("Sending a Matching Packet")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Send a non-matching packet , verify packet_in gets triggered
        logging.info("Sending a non matching packet")
        pkt2 = simple_tcp_packet(ip_dst='149.165.130.66')
        self.dataplane.send(of_ports[0], str(pkt2))
        logging.info("Waiting for packet_in from the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")
        logging.info("Packet_in Received")



class Grp50No90b(base_tests.SimpleDataPlane):

    """"Verify match on single Header Field Field -- IP_DST_ADDRESS 
    Generates an wildcard match here"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp50No90b Ip_Dst test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        rv = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]

        #Create a flow for match on ip_dst_address (wildcard match))
        logging.info("Installing a flow entry with wildcard IP_DST matching")
        pkt = simple_tcp_packet(ip_src='192.168.100.100')
        match = parse.packet_to_flow_match(pkt)
        match.wildcards = 0x3fffffcf
        msg = message.flow_mod()
        msg.match = match
        act = action.action_output()
        act.port = of_ports[1]
        rv = msg.actions.add(act)
        self.assertTrue(rv, "Could not add output action " + 
                            str(of_ports[1]))
        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed") 
        
        #Send Packet matching the flow 
        logging.info("Sending a mathcing packet")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)
	
        #Send a non-matching packet , verify it also matches the flow_entry
 	logging.info("Sending a matching packet with a different IP_DST")
        pkt2 = simple_tcp_packet(ip_src='149.165.130.66')
        self.dataplane.send(of_ports[0], str(pkt2))
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt2,[yes_ports],no_ports,self)



class Grp50No90c(base_tests.SimpleDataPlane):

    """"Verify match on single Header Field Field -- IP_SRC_ADDRESS 
    Generates an match with wildcarding certain number of bits in ip_address"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp50No90c Ip_Src test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        rv = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
	
	#Create a flow for match on ip_dst_address (MSB bits))
        logging.info("Installing a Flow entry with matching on MSB in IP_DST")
        pkt = simple_tcp_packet(ip_src='192.168.100.100')
        match = parse.packet_to_flow_match(pkt)
        match.wildcards = 0x3ff67fcf
        msg = message.flow_mod()
        msg.match = match
        act = action.action_output()
        act.port = of_ports[1]
        rv = msg.actions.add(act)
        self.assertTrue(rv, "Could not add output action " + 
                            str(of_ports[1]))
        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed") 

        #Send Packet matching the flow 
        logging.info("Sending a Matching Packet")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Send a non-matching packet , with only LSB different than the ip-address matched against
        logging.info("Sending a matching packet with different IP_DST(same MSB)")
        pkt2 = simple_tcp_packet(ip_dst='192.156.100.101')
        self.dataplane.send(of_ports[0], str(pkt2))

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the Packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt2,[yes_ports],no_ports,self)
        
        #Send a non-matching packet , verify packet_in gets triggered
        logging.info("Sending a non matching packet")
        pkt3 = simple_tcp_packet(ip_dst='200.168.100.100')
        self.dataplane.send(of_ports[0], str(pkt3))
        logging.info("Waiting for a Packet_in message from the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")
	logging.info("Packet_in received")

class Grp50No100(base_tests.SimpleDataPlane):

    """"Verify match on single Header Field Field -- Ip Protocol"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp50No100 Ip Protocol test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        rv = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Installing a flow entry with match on Ip Protocol ")
               

        #Create a flow matching on VLAN Priority
        (pkt,match) = match_ip_protocol(self,of_ports)

        #Send Packet matching the flow 
        logging.info("Sending a matching packet")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)
        
        #Create a non-matching packet , verify packet_in get generated
        logging.info("Sending a non matching packet")
        pkt2 = simple_icmp_packet();
        self.dataplane.send(of_ports[0], str(pkt2))
        logging.info("Waiting for a packet_in message from the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")
	logging.info("Packet_in received")


class Grp50No110(base_tests.SimpleDataPlane):

    """"Verify match on single Header Field Field -- Type of service"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp50No110 Ip_Tos test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        rv = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Installing a flow entry with match on Ip_Tos ")
        
        #Create a flow matching on VLAN Priority
        (pkt,match) = match_ip_tos(self,of_ports)

        #Send Packet matching the flow 
        logging.info("Sending a Matching packet")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)
        
        #Create a non-matching packet , verify packet_in get generated
        logging.info("Sending a non matching packet")
        pkt2 = simple_tcp_packet(ip_tos=2);
        self.dataplane.send(of_ports[0], str(pkt2))
        logging.info("Waiting for a packet_in message from the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")
	logging.info("Packet_in received")
	
	
class Grp50No120a(base_tests.SimpleDataPlane):
    
    """Verify match on Single header field -- Tcp Source Port"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp50No120a Tcp Src Port test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        rc = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
     
        logging.info("Installing a flow entry with match on Tcp Source Port ")
        
        (pkt,match) = match_tcp_src(self,of_ports)   

        #Sending packet matching the tcp_sport, verify it implements the action
        logging.info("Sending a matching packet")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        logging.info("verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Sending non matching packet , verify Packetin event gets triggered.
        logging.info("Sending a non matching packet")
        pkt2 = simple_tcp_packet(tcp_sport=540);
        self.dataplane.send(of_ports[0], str(pkt2))
        logging.info("Waiting for a Packet_in message from the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")
	logging.info("Packet_in received")
	
	
class Grp50No120b(base_tests.SimpleDataPlane):
    
    """Verify match on Single header field --Match on Tcp Source Port/IcmpType  """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running IcmpType test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        rc = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
        
        logging.info("Installing a flow entry with match on tcp source port/IcmpType")
        (pkt,match) = match_icmp_type(self,of_ports)   

        #Sending packet matching the tcp_sport, verify it implements the action
        logging.info("Sending a matching packet")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Sending non matching packet , verify Packetin event gets triggered.
        logging.info("Sending a non matching packet")
        pkt2 = simple_icmp_packet(icmp_type=11);
        self.dataplane.send(of_ports[0], str(pkt2))
        
        logging.info("Waiting for a packet_in message form the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")
	logging.info("Pakcet_in received")
	
	
class Grp50No130a(base_tests.SimpleDataPlane):
    
    """Verify match on Single header field -- Tcp Destination Port """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp50No130 Tcp Destination Port test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        rc = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
        
        logging.info("Installing a flow entry with match on Tcp Destination Port")
        
        (pkt,match) = match_tcp_dst(self,of_ports)   

        #Sending packet matching the tcp_dport, verify it implements the action
        logging.info("Sending a matching packet")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        logging.info ("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Sending non matching packet , verify Packetin event gets triggered.
        logging.info("Sending a non matching packet")
        pkt2 = simple_tcp_packet(tcp_dport=541);
        self.dataplane.send(of_ports[0], str(pkt2))
        
        logging.info("Waiting for a packet_in message from the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=10)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")
	logging.info("packet_in received")

class Grp50No130b(base_tests.SimpleDataPlane):
    
    """Verify match on Single header field -- Tcp Destination Port/IcmpCode  """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp50No130b test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        rc = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
	
	logging.info("Installing a flow entry with matching on TCP destination port/ICMPCode")
        (pkt,match) = match_icmp_code(self,of_ports)   

        #Sending packet matching the tcp_sport, verify it implements the action
        logging.info("Sending a matching packet")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Sending non matching packet , verify Packetin event gets triggered.
        logging.info("Sending a non matching packet")
        pkt2 = simple_icmp_packet(icmp_type=3,icmp_code=1);
        self.dataplane.send(of_ports[0], str(pkt2))
        
        logging.info("Waiting for a packet_in message from the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")
	logging.info("Packet_in received")

class Grp50No140(base_tests.SimpleDataPlane):
    
    """Verify match on multiple header field -- Ethernet Type, Ethernet Source Address, Ethernet Destination Address """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp50No140 Multiple Header Field L2 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        rc = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Installing a flow entry with match on L2 Header Fields")
        (pkt,match) = match_mul_l2(self,of_ports)   

        #Send eth packet matching the dl_type field, verify it implements the action
        logging.info("Sending a matching packet")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Sending non matching packet (only dl_dst is different) , verify Packetin event gets triggered.
        logging.info("Sending a non matching(only DL_DST mismatch) packet")
        pkt2 = simple_eth_packet(dl_type=0x0806,dl_src='00:01:01:01:01:01',dl_dst='00:01:01:02:01:01');
        self.dataplane.send(of_ports[0], str(pkt2))
	
        
        logging.info("Waiting for a Packet_in message from the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")
	logging.info("Packet_in received")

        #Sending non matching packet (only dl_src is different) , verify Packetin event gets triggered.
        logging.info("Sending a non matching(only DL_SRC mismatch) packet")
        pkt2 = simple_eth_packet(dl_type=0x0806,dl_src='00:01:01:01:01:02',dl_dst='00:01:01:01:01:02');
        self.dataplane.send(of_ports[0], str(pkt2))
        
        logging.info("Waiting for a Packet_in message from the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")
	logging.info("Packet_in received")
	
        #Sending non matching packet (only ether_type is different) , verify Packetin event gets triggered.
        logging.info("Sending a non matching(only ether type mismatch) packet")
        pkt2 = simple_eth_packet(dl_type=0x0805,dl_src='00:01:01:01:01:01',dl_dst='00:01:01:01:01:02');
        self.dataplane.send(of_ports[0], str(pkt2))
        
        #Verify packet_in event gets triggered
        logging.info("Waiting for a Packet_in message from the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")
	logging.info("Packet_in received")

class Grp50No150(base_tests.SimpleDataPlane):

    """"Verify match on multiple Header Fielda -- L3 
    Generates a wildcard match here"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp50No150 L3 matching test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        rv = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]

        #Create a flow for match on ip_dst_address & ip_src_address (exact match))
        logging.info("Installing a Flow entry with match on L3 header fields")
        pkt = simple_tcp_packet(ip_src='192.168.100.100',ip_dst='192.168.100.200')
        match = parse.packet_to_flow_match(pkt)
        match.wildcards = 0x3ff000cf
        msg = message.flow_mod()
        msg.match = match
        act = action.action_output()
        act.port = of_ports[1]
        rv = msg.actions.add(act)
        self.assertTrue(rv, "Could not add output action " + 
                            str(of_ports[1]))
        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed") 
        
        #Send Packet matching the flow 
        logging.info("Sending a matching packet")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Send a non-matching packet , verify it doesnt matches the flow_entry
        logging.info("Sending a non matching packet")
        pkt2 = simple_tcp_packet(ip_src='200.168.100.100',ip_dst='192.168.100.200')
        self.dataplane.send(of_ports[0], str(pkt2))
        
        #Verify packet_in event gets triggered
        logging.info("Waiting for a packet_in message from the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")
	logging.info("Packet_in received")




class Grp50No160(base_tests.SimpleDataPlane):
    
    """Verify match on multiple header field -- Tcp Source Port, Tcp Destination Port  """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp50No160 Multiple Header Field L4 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        rc = delete_all_flows(self.controller)
       	self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
    	
    	egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
        
        logging.info("Installing a flow with match on Multiple Header Field L4 ")
        (pkt,match) = match_mul_l4(self,of_ports)   

        #Sending packet matching the tcp_sport and tcp_dport field, verify it implements the action
        logging.info("Sending a matching packet")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Sending non matching packet (tcp_dport different), verify Packetin event gets triggered.
        logging.info("Sending a non matching(only tcp_dst_port mismatch) packet")
        pkt2 = simple_tcp_packet(tcp_sport=111,tcp_dport=541);
        self.dataplane.send(of_ports[0], str(pkt2))
        
        logging.info("waiting for a packet_in message from the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")
	logging.info("Packet_in received")
        #Sending non matching packet (tcp_sport different), verify Packetin event gets triggered.
        logging.info("Sending a non matching(only tcp_src_port mis match) packet")
        pkt2 = simple_tcp_packet(tcp_sport=100,tcp_dport=112);
        self.dataplane.send(of_ports[0], str(pkt2))
        
        logging.info("Waiting for a packet_in message from the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")
	logging.info("Packet_in received")

class Grp50No170(base_tests.SimpleDataPlane):
    
    """Verify match on All header fields -- Exact Match  """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp50No170 Exact Match test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        rc = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
        
        logging.info("Installing a flow entry with match on all header fields")
        (pkt,match) = exact_match(self,of_ports)   

        #Sending packet matching all the fields of a tcp_packet, verify it implements the action
        logging.info("Sending a matching packet")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        logging.info("Verifying whether the packet matches the flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)

        #Sending non matching packet , verify Packetin event gets triggered.
        logging.info("Sending a non matching packet")
        pkt2 = simple_tcp_packet(tcp_sport=540);
        self.dataplane.send(of_ports[0], str(pkt2))
        
        logging.info("Waiting for a packet_in message from the switch")
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received for non matching packet")
	logging.info("Packet_in received")

class Grp50No180(base_tests.SimpleDataPlane):
    
    """Verify that Exact Match has highest priority """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp50No180a Exact Match High Priority test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        rc = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
    	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
        
	egress_port=of_ports[2]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[2]
           
        #Insert two Overlapping Flows : Exact Match and Wildcard All.
  	logging.info("Installing a flow entry with Exact Match (low priority)")      
        (pkt,match) = exact_match_with_prio(self,of_ports,priority=10) 
        
	logging.info("Installing an overlapping wildcarded flow (higher priority)")
        (pkt2,match2) = wildcard_all(self,of_ports,priority=20)
        
        #Sending packet matching both the flows , 
        logging.info("Sending a packet matching both the flows")
        self.dataplane.send(of_ports[0], str(pkt2))

        #verify it implements the action specified in Exact Match Flow
        logging.info("Verifying whether the switch implements the actions specified in the highest priority flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)
	



class Grp50No190(base_tests.SimpleDataPlane):
    
    """Verify that Wildcard Match with highest priority overrides the low priority WildcardMatch """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp50No190 Wildcard Match High Priority test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    
        #Clear Switch State
        rc = delete_all_flows(self.controller)
        self.assertTrue(rv != -1, "Error installing flow mod")
   	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    	egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]
    
        logging.info("Installing two overlapping flow entries with different priorities ")
       
        (pkt,match) = wildcard_all(self,of_ports,priority=20) 
        (pkt1,match1) =  wildcard_all_except_ingress1(self,of_ports,priority=10)  

        #Sending packet matching both the flows , verify it implements the action specified by Higher Priority flow
       	logging.info("Sending a packet matching on both the flows")
        self.dataplane.send(of_ports[0], str(pkt1))
        
        logging.info("Verifying whether the switch implements the actions specified in the highest priority flow entry")
        receive_pkt_check(self.dataplane,pkt,[yes_ports],no_ports,self)






       
