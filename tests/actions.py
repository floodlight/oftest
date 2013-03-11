
"""These tests fall under Conformance Test-Suite (OF-SWITCH-1.0.0 TestCases).
    Refer Documentation -- Detailed testing methodology 
    <Some of test-cases are directly taken from oftest> """

"Test Suite 6  ---> Actions "


import logging

import unittest
import random
import time

from oftest import config
import oftest.controller as controller
import ofp
import oftest.dataplane as dataplane
import oftest.parse as parse
import oftest.base_tests as base_tests

from oftest.testutils import *
from time import sleep
from FuncUtils import *

class NoAction(base_tests.SimpleDataPlane):

    """NoActionDrop : no action added to flow , drops the packet."""

    def runTest(self):
        
        logging.info("Running No_Action test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        delete_all_flows(self.controller)
        
        logging.info("Install a flow without action")
        logging.info("Send packets matching that flow")
        logging.info("Expecting switch to drop all packets")

        # Insert a flow wildcard all without any action 
        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        self.assertTrue(match is not None, "Could not generate flow match from pkt")
        match.wildcards=ofp.OFPFW_ALL
        match.in_port = of_ports[0]
        
        msg = ofp.message.flow_mod()
        msg.out_port = ofp.OFPP_NONE
        msg.command = ofp.OFPFC_ADD
        msg.buffer_id = 0xffffffff
        msg.match = match
        self.controller.message_send(msg)
        do_barrier(self.controller)

        #Sending N packets matching the flow inserted
        for pkt_cnt in range(5):
            self.dataplane.send(of_ports[0],str(pkt))
        
        #Verify packets not recieved on any of the dataplane ports 
        (rcv_port, rcv_pkt, pkt_time) = self.dataplane.poll(timeout=1,exp_pkt=pkt)
        self.assertTrue(rcv_pkt is None,
                "Packet received on port " + str(rcv_port))

        #Verify packets not sent on control plane either
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN, timeout=1)
        self.assertTrue(response is None,
                        'Packets not received on control plane')


class Announcement(base_tests.SimpleDataPlane):
    
    """Announcement : Get all supported actions by the switch.
    Send OFPT_FEATURES_REQUEST to get features supported by sw."""

    def runTest(self):

        logging.info("Running Announcement test")

        logging.info("Sending Features_Request")
        logging.info("Expecting Features Reply with supported actions")

        # Sending Features_Request
        request = ofp.message.features_request()
        (reply, pkt) = self.controller.transact(request)
        self.assertTrue(reply is not None, "Failed to get any reply")
        self.assertEqual(reply.type, ofp.OFPT_FEATURES_REPLY,'Response is not Features_reply')
        
        supported_actions =[]
        if(reply.actions &1<<ofp.OFPAT_OUTPUT):
            supported_actions.append('OFPAT_OUTPUT')
        if(reply.actions &1<<ofp.OFPAT_SET_VLAN_VID):
            supported_actions.append('OFPAT_SET_VLAN_VID')
        if(reply.actions &1<<ofp.OFPAT_SET_VLAN_PCP):
            supported_actions.append('OFPAT_SET_VLAN_PCP')
        if(reply.actions &1<<ofp.OFPAT_STRIP_VLAN):
            supported_actions.append('OFPAT_STRIP_VLAN')
        if(reply.actions &1<<ofp.OFPAT_SET_DL_SRC):
            supported_actions.append('OFPAT_SET_DL_SRC')
        if(reply.actions &1<<ofp.OFPAT_SET_DL_DST):
            supported_actions.append('OFPAT_SET_NW_SRC')
        if(reply.actions &1<<ofp.OFPAT_SET_NW_DST):
            supported_actions.append('OFPAT_SET_NW_DST')
        if(reply.actions &1<<ofp.OFPAT_SET_NW_TOS):
            supported_actions.append('OFPAT_SET_NW_TOS')
        if(reply.actions &1<<ofp.OFPAT_SET_TP_SRC):
            supported_actions.append('OFPAT_SET_TP_SRC')
        if(reply.actions &1<<ofp.OFPAT_SET_TP_DST):
            supported_actions.append('OFPAT_SET_TP_DST')
        if(reply.actions &1<<ofp.OFPAT_VENDOR):
            supported_actions.append('OFPAT_VENDOR')
        if(reply.actions &1<<ofp.OFPAT_ENQUEUE):
            supported_actions.append('OFPAT_ENQUEUE')
        
        logging.info(supported_actions)
        

class ForwardAll(base_tests.SimpleDataPlane):
    
    """ForwardAll : Packet is sent to all dataplane ports
    except ingress port when output action.port = OFPP_ALL"""

    def runTest(self):

        logging.info("Running Forward_All test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        delete_all_flows(self.controller)
        
        logging.info("Insert a flow with output action port OFPP_ALL")
        logging.info("Send packet matching the flow")
        logging.info("Expecting packet on all dataplane ports except ingress_port")
        
        #Create a packet
        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        act = ofp.action.output()

        #Delete all flows 
        delete_all_flows(self.controller)
        ingress_port=of_ports[0]
        match.in_port = ingress_port

        #Create a flow mod with action.port = OFPP_ALL
        request = ofp.message.flow_mod()
        request.match = match
        request.match.wildcards = ofp.OFPFW_ALL&~ofp.OFPFW_IN_PORT
        act.port = ofp.OFPP_ALL
        request.actions.append(act)
        
        logging.info("Inserting flow")
        self.controller.message_send(request)
        do_barrier(self.controller)

        #Send Packet matching the flow
        logging.info("Sending packet to dp port " + str(ingress_port))
        self.dataplane.send(ingress_port, str(pkt))

        #Verifying packets recieved on expected dataplane ports
        yes_ports = set(of_ports).difference([ingress_port])
        receive_pkt_check(self.dataplane, pkt, yes_ports, [ingress_port],
                      self)


class ForwardController(base_tests.SimpleDataPlane):
    
    """ForwardController : Packet is sent to controller 
    output.port = OFPP_CONTROLLER"""

    def runTest(self):
        
        logging.info("Running Forward_Controller test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        delete_all_flows(self.controller)
        
        logging.info("Insert a flow with output action port OFPP_CONTROLLER")
        logging.info("Send packet matching the flow")
        logging.info("Expecting packet on the control plane")
        
        #Create packet
        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        act = ofp.action.output()

        for ingress_port in of_ports:
            #Delete all flows 
            delete_all_flows(self.controller)

            match.in_port = ingress_port
            
            #Create a flow mod message
            request = ofp.message.flow_mod()
            request.match = match
            act.port = ofp.OFPP_CONTROLLER
            request.actions.append(act)

            logging.info("Inserting flow")
            self.controller.message_send(request)
            do_barrier(self.controller)
            
            #Send packet matching the flow
            logging.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))

            #Verifying packet recieved on the control plane port
            (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN, timeout=10)
            self.assertTrue(response is not None,
                        'Packet in message not received by controller')
    


class ForwardLocal(base_tests.SimpleDataPlane):
   
    """ForwardLocal : Packet is sent to  OFPP_LOCAL port . 
        TBD : To verify packet recieved in the local networking stack of switch"""

    def runTest(self):

        logging.info("Running Forward_Local test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        delete_all_flows(self.controller)
        
        logging.info("Insert a flow with output action port OFPP_LOCAL")
        logging.info("Send packet matching the flow")
        logging.info("Expecting packet in the local networking stack of switch")
        
        #Clear switch state
        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        act = ofp.action.output()

        for ingress_port in of_ports:
            #Delete the flows
            delete_all_flows(self.controller)

            match.in_port = ingress_port
            #Create flow mod message
            request = ofp.message.flow_mod()
            request.match = match
            act.port = ofp.OFPP_LOCAL
            request.actions.append(act)

            logging.info("Inserting flow")
            self.controller.message_send(request)
            do_barrier(self.controller)

            #Send packet matching the flow
            logging.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))

            #TBD: Verification of packets being recieved.


class ForwardFlood(base_tests.SimpleDataPlane):
    
    """Forward:Flood : Packet is sent to all dataplane ports
    except ingress port when output action.port = OFPP_FLOOD 
    TBD : Verification---Incase of STP being implemented, flood the packet along the minimum spanning tree,
             not including the incoming interface. """
    
    def runTest(self):

        logging.info("Running Forward_Flood test")
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        delete_all_flows(self.controller)
        
        logging.info("Insert a flow with output action port OFPP_FORWARD")
        logging.info("Send packet matching the flow")
        logging.info("Expecting packet on all the ports except the input port")
        
        #Create a packet
        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        act = ofp.action.output()

        #Delete all flows 
        delete_all_flows(self.controller)
        ingress_port=of_ports[0]
        match.in_port = ingress_port

        #Create a flow mod with action.port = OFPP_ALL
        request = ofp.message.flow_mod()
        request.match = match
        request.match.wildcards = ofp.OFPFW_ALL&~ofp.OFPFW_IN_PORT
        act.port = ofp.OFPP_FLOOD
        request.actions.append(act)
        
        logging.info("Inserting flow")
        self.controller.message_send(request)
        do_barrier(self.controller)

        #Send Packet matching the flow
        logging.info("Sending packet to dp port " + str(ingress_port))
        self.dataplane.send(ingress_port, str(pkt))

        #Verifying packets recieved on expected dataplane ports
        yes_ports = set(of_ports).difference([ingress_port])
        receive_pkt_check(self.dataplane, pkt, yes_ports, [ingress_port],
                      self)

class ForwardInport(base_tests.SimpleDataPlane):
    
    """ ForwardInPort : Packet sent to virtual port IN_PORT
    If the output.port = OFPP.INPORT then the packet is sent to the input port itself"""

    def runTest(self):

        logging.info("Running Forward_Inport test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        delete_all_flows(self.controller)
        
        logging.info("Insert a flow with output action port OFPP_INPORT")
        logging.info("Send packet matching the flow")
        logging.info("Expecting packet on the input port")
        
        #Create a packet
        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        act = ofp.action.output()

        #Delete the flows
        delete_all_flows(self.controller)
        ingress_port=of_ports[0]
        match.in_port = ingress_port

        # Create a flow mod message
        request = ofp.message.flow_mod()
        request.match = match
        act.port = ofp.OFPP_IN_PORT
            
        request.actions.append(act)
        logging.info("Inserting flow")
        self.controller.message_send(request)
        do_barrier(self.controller)

        #Send packet matching the flow
        logging.info("Sending packet to dp port " + str(ingress_port))
        self.dataplane.send(ingress_port, str(pkt))
        yes_ports = [ingress_port]

        #Verfying packet recieved on expected dataplane ports
        receive_pkt_check(self.dataplane, pkt, yes_ports,set(of_ports).difference([ingress_port]),
                          self)

class ForwardTable(base_tests.SimpleDataPlane):
   
    """ForwardTable : Perform actions in flow table. Only for packet-out messages.
        If the output action.port in the packetout message = OFP.TABLE , then 
        the packet implements the action specified in the matching flow of the FLOW-TABLE"""

    def runTest(self):

        logging.info("Running Forward_Table test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        delete_all_flows(self.controller)
        
        logging.info("Insert a flow F with output action port set to some egress_port")
        logging.info("Send packet out message (matching flow F) with action.port = OFP.TABLE")
        logging.info("Expecting packet on the egress_port")
        
        #Insert a all wildcarded flow
        (pkt,match) = wildcard_all(self,of_ports)
        
        #Create a packet out message
        pkt_out =ofp.message.packet_out();
        pkt_out.data = str(pkt)
        pkt_out.in_port = of_ports[0]
        act = ofp.action.output()
        act.port = ofp.OFPP_TABLE
        pkt_out.actions.append(act)
        self.controller.message_send(pkt_out)

        #Verifying packet out message recieved on the expected dataplane port. 
        (of_port, pkt, pkt_time) = self.dataplane.poll(port_number=of_ports[1],
                                                             exp_pkt=pkt,timeout=3)
        self.assertTrue(pkt is not None, 'Packet not received')


class AddVlanTag(base_tests.SimpleDataPlane):
    
    """AddVlanTag : Adds VLAN Tag to untagged packet."""

    def runTest(self):

        logging.info("Running Add_vlan_tag test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        delete_all_flows(self.controller)

        logging.info("Verify if switch supports the action -- set vlan id, if not skip the test")
        logging.info("Insert a flow with set vid action")
        logging.info("Send packet matching the flow , verify recieved packet has vid set")
        
        #Verify set_vlan_id is a supported action
        sup_acts = sw_supported_actions(self)
        if not(sup_acts & 1<<ofp.OFPAT_SET_VLAN_VID):
           skip_message_emit(self, "Add VLAN tag test skipped")
           return
        
        #Create packet to be sent and an expected packet with vid set
        new_vid = 2
        len_wo_vid = 100
        len_w_vid = 104
        pkt = simple_tcp_packet(pktlen=len_wo_vid)
        exp_pkt = simple_tcp_packet(pktlen=len_w_vid, dl_vlan_enable=True, 
                                    vlan_vid=new_vid,vlan_pcp=0)
        vid_act = ofp.action.set_vlan_vid()
        vid_act.vlan_vid = new_vid

        #Insert flow with action -- set vid , Send packet matching the flow, Verify recieved packet is expected packet
        flow_match_test(self, config["port_map"], pkt=pkt, 
                        exp_pkt=exp_pkt, action_list=[vid_act])

class ModifyVlanTag(base_tests.SimpleDataPlane):

    """ModifyVlanTag : Modifies VLAN Tag to tagged packet."""
    
    def runTest(self):

        logging.info("Running Modify_Vlan_Tag test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        delete_all_flows(self.controller)

        logging.info("Verify if switch supports the action -- modify vlan id, if not skip the test")
        logging.info("Insert a flow with action --set vid ")
        logging.info("Send tagged packet matching the flow , verify recieved packet has vid rewritten")
        
        #Verify set_vlan_id is a supported action
        sup_acts = sw_supported_actions(self)
        if not (sup_acts & 1 << ofp.OFPAT_SET_VLAN_VID):
            skip_message_emit(self, "Modify VLAN tag test skipped")
            return

        #Create a tagged packet with old_vid to be sent, and expected packet with new_vid
        old_vid = 2
        new_vid = 3
        pkt = simple_tcp_packet(dl_vlan_enable=True, vlan_vid=old_vid)
        exp_pkt = simple_tcp_packet(dl_vlan_enable=True, vlan_vid=new_vid)
        vid_act = ofp.action.set_vlan_vid()
        vid_act.vlan_vid = new_vid
        
        #Insert flow with action -- set vid , Send packet matching the flow.Verify recieved packet is expected packet.
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt,
                        action_list=[vid_act])
        
class VlanPrio1(base_tests.SimpleDataPlane):
   
    """AddVlanPrioUntaggedPkt : Add VLAN priority to untagged packet."""
    
    def runTest(self):

        logging.info("Running vlan_Prio_1 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        delete_all_flows(self.controller)

        logging.info("Verify if switch supports the action -- set vlan priority, if not skip the test")
        logging.info("Insert a flow with action -- set vlan priority ")
        logging.info("Send untagged packet matching the flow , verify recieved packet has specified VLAN priority and has vid set tO 0 ")
        
        #Verify set_vlan_priority is a supported action
        sup_acts = sw_supported_actions(self)
        if not (sup_acts & 1 << ofp.OFPAT_SET_VLAN_PCP):
            skip_message_emit(self, "Set VLAN priority test skipped")
            return
        
        #Create a untagged packet to be sent and an expected packet with vid = 0 , vlan_priority set. 
        vlan_id = 0
        vlan_pcp = 1
        pktlen = 64 if config["minsize"] < 64 else config["minsize"]
        pkt = simple_tcp_packet(pktlen=pktlen)
        exp_pkt = simple_tcp_packet(dl_vlan_enable=True, vlan_vid=vlan_id,vlan_pcp=vlan_pcp, pktlen=pktlen + 4)
        act = ofp.action.set_vlan_pcp()
        act.vlan_pcp = vlan_pcp

        #Insert flow with action -- set vLAN priority, Send packet matching the flow, Verify recieved packet is expected packet
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt,
                                action_list=[act])


class VlanPrio2(base_tests.SimpleDataPlane):
    
    """ModifyVlanPrio : Modify VLAN priority to tagged packet."""
    
    def runTest(self):
        
        logging.info("Running Vlan_Prio_2 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        delete_all_flows(self.controller)

        logging.info("Verify if switch supports the action -- set vlan priority, if not skip the test")
        logging.info("Insert a flow with action -- set vlan priority ")
        logging.info("Send tagged packet matching the flow, verify recieved packet has vlan priority rewritten")
        
        #Verify set_vlan_priority is a supported action
        sup_acts = sw_supported_actions(self,"true")
        if not (sup_acts & 1 << ofp.OFPAT_SET_VLAN_PCP):
            skip_message_emit(self, "modify_vlan_prio test skipped")
            return
        
        #Create a tagged packet , and an expected packet with vlan_priority set to specified value
        vid          = 123
        old_vlan_pcp = 2
        new_vlan_pcp = 3
        pkt = simple_tcp_packet(dl_vlan_enable=True, vlan_vid=vid, vlan_pcp=old_vlan_pcp)
        exp_pkt = simple_tcp_packet(dl_vlan_enable=True, vlan_vid=vid, vlan_pcp=new_vlan_pcp)
        vid_act = ofp.action.set_vlan_pcp()
        vid_act.vlan_pcp = new_vlan_pcp

        #Insert flow with action -- set vLAN priority, Send tagged packet matching the flow, Verify recieved packet is expected packet
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt,
                        action_list=[vid_act])


class ModifyL2Src(base_tests.SimpleDataPlane):
    
    """ModifyL2Src :Modify the source MAC address"""

    def runTest(self):

        logging.info("Running Modify_L2_Src test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        delete_all_flows(self.controller)

        logging.info("Verify if switch supports the action -- modify_l2_src, if not skip the test")
        logging.info("Insert a flow with action -- set etherent src address")
        logging.info("Send packet matching the flow, verify recieved packet src address rewritten ")

        #Verify set_dl_src is a supported action
        sup_acts = sw_supported_actions(self,use_cache="true")
        if not (sup_acts & 1 << ofp.OFPAT_SET_DL_SRC):
            skip_message_emit(self, "modify_l2_src test skipped")
            return

        #Create packet to be sent and expected packet with eth_src set to specified value
        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['eth_src'],
                                                check_test_params=True)
        
        #Insert flow with action -- set src address, Send packet matching the flow, Verify recieved packet is expected packet
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)


class ModifyL2Dst(base_tests.SimpleDataPlane):
    
    """ModifyL2SDSt :Modify the dest MAC address"""

    def runTest(self):

        logging.info("Running Modify_L2_Dst test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        delete_all_flows(self.controller)

        logging.info("Verify if switch supports the action -- modify_l2_dst, if not skip the test")
        logging.info("Insert a flow with action -- set etherent dst address ")
        logging.info("Send packet matching the flow, verify recieved packet dst address rewritten ")

        #Verify set_dl_dst is a supported action
        sup_acts = sw_supported_actions(self)
        if not (sup_acts & 1 << ofp.OFPAT_SET_DL_DST):
            skip_message_emit(self, "modify_l2_dst test skipped")
            return

        #Create packet to be sent and expected packet with eth_src set to specified value
        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['eth_dst'],
                                                check_test_params=True)
        
        #Insert flow with action -- set dst address, Send packet matching the flow, Verify recieved packet is expected packet
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)

class ModifyL3Src(base_tests.SimpleDataPlane):
    
    """ModifyL3Src : Modify the source IP address of an IP packet """

    def runTest(self):

        logging.info("Running Modify_L3_Src test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        delete_all_flows(self.controller)

        logging.info("Verify if switch supports the action -- modify_l3_src, if not skip the test")
        logging.info("Insert a flow with action -- set network src address ")
        logging.info("Send packet matching the flow, verify recieved packet network src address rewritten ")
        
        #Verify set_nw_src is a supported action
        sup_acts = sw_supported_actions(self)
        if not (sup_acts & 1 << ofp.OFPAT_SET_NW_SRC):
            skip_message_emit(self, "modify_l3_src test")
            return

        #Create packet to be sent and expected packet with ipv4_src set to specified value
        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['ip_src'],
                                                check_test_params=True)
        
        #Insert flow with action -- set nw src address, Send packet matching the flow, Verify recieved packet is expected packet
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)

class ModifyL3Dst(base_tests.SimpleDataPlane):
    
    """ModifyL3Dst :Modify the dest IP address of an IP packet"""
    
    def runTest(self):

        logging.info("Running Modify_L3_Dst test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        delete_all_flows(self.controller)

        logging.info("Verify if switch supports the action -- modify_l3_dst, if not skip the test")
        logging.info("Insert a flow with action -- set network dst address ")
        logging.info("Send packet matching the flow, verify recieved packet network dst address rewritten ")

        #Verify set_nw_dst is a supported action
        sup_acts = sw_supported_actions(self,use_cache="true")
        if not (sup_acts & 1 << ofp.OFPAT_SET_NW_DST):
            skip_message_emit(self, "modify_l3_dst test skipped")
            return
        
        #Create packet to be sent and expected packet with ipv4_dst set to specified value
        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['ip_dst'],
                                                check_test_params=True)
        
        #Insert flow with action -- set nw dst address, Send packet matching the flow, Verify recieved packet is expected packet
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)


class ModifyL4Src(base_tests.SimpleDataPlane):
    
    """ModifyL4Src : Modify the source TCP port of a TCP packet"""
    
    def runTest(self):

        logging.info("Running Modify_L4_Src test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        delete_all_flows(self.controller)

        logging.info("Verify if switch supports the action -- modify_l4_src, if not skip the test")
        logging.info("Insert a flow with action -- set src tcp port")
        logging.info("Send packet matching the flow, verify recieved packet src tcp port is rewritten ")
        
        #Verify set_tp_src is a supported action
        sup_acts = sw_supported_actions(self,use_cache="true")
        if not (sup_acts & 1 << ofp.OFPAT_SET_TP_SRC):
            skip_message_emit(self, "modify_l4_src test skipped")
            return

        #Create packet to be sent and expected packet with tcp_src set to specified value
        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['tcp_sport'],
                                                check_test_params=True)
        
        #Insert flow with action -- set tcp src port, Send packet matching the flow, Verify recieved packet is expected packet
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)

class ModifyL4Dst(base_tests.SimpleDataPlane):
    
    """ ModifyL4Dst: Modify the dest TCP port of a TCP packet """

    def runTest(self):

        logging.info("Running Modify_L4_Dst test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        delete_all_flows(self.controller)

        logging.info("Verify if switch supports the action -- modify_l4_dst, if not skip the test")
        logging.info("Insert a flow with action -- set dst tcp port")
        logging.info("Send packet matching the flow, verify recieved packet dst tcp port is rewritten ")
       
        #Verify set_tp_dst is a supported action
        sup_acts = sw_supported_actions(self,use_cache="true")
        if not (sup_acts & 1 << ofp.OFPAT_SET_TP_DST):
            skip_message_emit(self, "ModifyL4Dst test")
            return

        #Create packet to be sent and expected packet with tcp_dst set to specified value
        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['tcp_dport'],
                                                check_test_params=True)
        
        #Insert flow with action -- set tcp dst port, Send packet matching the flow, Verify recieved packet is expected packet
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)

class ModifyTos(base_tests.SimpleDataPlane):
    
    """ModifyTOS :Modify the IP type of service of an IP packet"""
   
    def runTest(self):

        logging.info("Running Modify_Tos test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        delete_all_flows(self.controller)

        logging.info("Verify if switch supports the action -- modify_tos, if not skip the test")
        logging.info("Insert a flow with action -- set type of service ")
        logging.info("Send packet matching the flow, verify recieved packet has TOS rewritten ")
       
        #Verify set_tos is a supported action
        sup_acts = sw_supported_actions(self,use_cache="true")
        if not (sup_acts & 1 << ofp.OFPAT_SET_NW_TOS):
            skip_message_emit(self, "ModifyTOS test")
            return

        #Create packet to be sent and expected packet with TOS set to specified value
        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['ip_tos'],
                                                check_test_params=True)
        
        #Insert flow with action -- set TOS, Send packet matching the flow, Verify recieved packet is expected packet
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2, egr_count=-1)
