""" Defined Some common functions used by Conformance tests -- OF-SWITCH 1.0.0 Testcases """

import sys
import copy
import random

import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action
import oftest.parse as parse
import logging
import types

import oftest.base_tests as base_tests
from oftest.testutils import *
from time import sleep

#################### Functions for various types of flow_mod  ##########################################################################################

def exact_match(self,of_ports,priority=None):
    '''
    Generates and installs a flow message with all match fields
    set that are defined for the current conformance profile.
    The conformance profile is defined as oft optional argument
    --conformance ["l2", "l3", "full"]
    '''

    pkt_exactflow = simple_tcp_packet()
    match = parse.packet_to_flow_match(pkt_exactflow)
    self.assertTrue(match is not None, "Could not generate flow match from pkt")
    # in_port is not automatically set in parse.packet_to_flow_match
    match.in_port = of_ports[0]
    match.wildcards &= ~ofp.OFPFW_IN_PORT
    #match.nw_src = 1
    #match.wildcards=0
    msg = message.flow_mod()
    msg.out_port = ofp.OFPP_NONE
    msg.command = ofp.OFPFC_ADD
    msg.buffer_id = 0xffffffff
    msg.match = match
    if priority != None :
        msg.priority = priority

    act = action.action_output()
    act.port = of_ports[1]
    self.assertTrue(msg.actions.add(act), "could not add action")

    rv = self.controller.message_send(msg)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return (pkt_exactflow,match)

def exact_match_with_prio(self,of_ports,priority=None):
    # Generate ExactMatch with action output to port 2

    #Create a simple tcp packet and generate exact flow match from it.
    pkt_exactflow = simple_tcp_packet()
    match = parse.packet_to_flow_match(pkt_exactflow, exact=True)
    self.assertTrue(match is not None, "Could not generate flow match from pkt")
    match.in_port = of_ports[0]
    #match.nw_src = 1
    match.wildcards=0
    msg = message.flow_mod()
    msg.out_port = ofp.OFPP_NONE
    msg.command = ofp.OFPFC_ADD
    msg.buffer_id = 0xffffffff
    msg.match = match
    if priority != None :
        msg.priority = priority

    act = action.action_output()
    act.port = of_ports[2]
    self.assertTrue(msg.actions.add(act), "could not add action")

    rv = self.controller.message_send(msg)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return (pkt_exactflow,match)         
       
def match_arp(self, of_ports, srcb=0, dstb=0, priority=None):
    arp_pkt = simple_arp_packet()
    match = parse.packet_to_flow_match(arp_pkt, match_on_arp=True)
    self.assertTrue(match is not None, "Could not create a match from the packet")
    if srcb==1:
        match.wildcards = ofp.OFPFW_ALL ^ofp.OFPFW_DL_TYPE ^(63<<ofp.OFPFW_NW_SRC_SHIFT)
    elif dstb==1:
        match.wildcards = ofp.OFPFW_ALL ^ofp.OFPFW_DL_TYPE ^(63<<ofp.OFPFW_NW_DST_SHIFT)
    else :
        match.wildcards = ofp.OFPFW_ALL ^ofp.OFPFW_DL_TYPE
    msg = message.flow_mod()
    msg.outport = ofp.OFPP_NONE
    msg.command = ofp.OFPFC_ADD
    msg.buffer_id = 0xffffffff
    msg.match=match
    if priority != None:
        msg.priority = priority
    act = action.action_output()
    act.port = of_ports[1]
    self.assertTrue(msg.actions.add(act), "could not add action")

    rv = self.controller.message_send(msg)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return (arp_pkt,match)

def match_icmp_type(self,of_ports,priority=None):
    #Generate Match on icmp type

        #Create a simple icmp packet and generate match on icmp type
    pkt = simple_icmp_packet(icmp_type=8)
    match = parse.packet_to_flow_match(pkt)
    self.assertTrue(match is not None, "Could not generate flow match from pkt")

    match.wildcards = ofp.OFPFW_ALL ^ofp.OFPFW_DL_TYPE^ofp.OFPFW_NW_PROTO^ofp.OFPFW_TP_SRC 
    msg = message.flow_mod()
    msg.out_port = ofp.OFPP_NONE
    msg.command = ofp.OFPFC_ADD
    msg.buffer_id = 0xffffffff
    msg.match = match
    if priority != None :
        msg.priority = priority
    act = action.action_output()
    act.port = of_ports[1]
    self.assertTrue(msg.actions.add(act), "could not add action")

    rv = self.controller.message_send(msg)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return (pkt,match)

def match_icmp_code(self,of_ports,priority=None):
    #Generate Match on icmp code

        #Create a simple icmp packet and generate match on icmp type
    pkt = simple_icmp_packet(icmp_type=3,icmp_code=0)
    match = parse.packet_to_flow_match(pkt)
    self.assertTrue(match is not None, "Could not generate flow match from pkt")

    match.wildcards = ofp.OFPFW_ALL ^ofp.OFPFW_DL_TYPE^ofp.OFPFW_NW_PROTO^ofp.OFPFW_TP_SRC^ofp.OFPFW_TP_DST
    msg = message.flow_mod()
    msg.out_port = ofp.OFPP_NONE
    msg.command = ofp.OFPFC_ADD
    msg.buffer_id = 0xffffffff
    msg.match = match
    if priority != None :
        msg.priority = priority
    act = action.action_output()
    act.port = of_ports[1]
    self.assertTrue(msg.actions.add(act), "could not add action")

    rv = self.controller.message_send(msg)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return (pkt,match)

def match_all_except_source_address(self,of_ports,priority=None):
    '''
    Generates and installs a flow message with all match fields
    set except for the source address defined for the current
    conformance profile, and fields not defined for this profile.
    For l2 and full profiles the source mac is wildcarded; For
    the l3 profile source ip address is wildcarded. The
    conformance profile is defined as oft optional argument
    --conformance ["l2", "l3", "full"]
    '''
    if config['conformance'] == None:
        profile = ['l2']
    else:
        profile = config['conformance'].split('+')

    pkt_wildcardsrc = simple_tcp_packet()
    match = parse.packet_to_flow_match(pkt_wildcardsrc)
    self.assertTrue(match is not None, "Could not generate flow match from pkt")
    # in_port is not automatically set in parse.packet_to_flow_match
    match.in_port = of_ports[0]
    match.wildcards &= ~ ofp.OFPFW_IN_PORT

    if 'l3' in profile:
        match.wildcards |= ofp.OFPFW_NW_SRC_MASK
    else:
        match.wildcards |= ofp.OFPFW_DL_SRC

    msg = message.flow_mod()
    msg.out_port = ofp.OFPP_NONE
    msg.command = ofp.OFPFC_ADD
    msg.buffer_id = 0xffffffff
    msg.match = match
    if priority != None :
        msg.priority = priority

    act = action.action_output()
    act.port = of_ports[1]
    self.assertTrue(msg.actions.add(act), "could not add action")

    rv = self.controller.message_send(msg)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return pkt_wildcardsrc, match


def match_ethernet_src_address(self,of_ports,priority=None):
    #Generate Match_Ethernet_SrC_Address flow

    #Create a simple tcp packet and generate match on ethernet src address flow
    pkt_MatchSrc = simple_eth_packet(dl_src='08:00:27:00:d0:07',dl_dst ='78:84:3c:89:fb:5a', dl_type = 0x88cc)
    match = parse.packet_to_flow_match(pkt_MatchSrc)
    self.assertTrue(match is not None, "Could not generate flow match from pkt")

    match.wildcards = ofp.OFPFW_ALL ^ofp.OFPFW_DL_SRC
        
    msg = message.flow_mod()
    msg.out_port = ofp.OFPP_NONE
    msg.command = ofp.OFPFC_ADD
    msg.buffer_id = 0xffffffff
    msg.match = match
    if priority != None :
        msg.priority = priority

    act = action.action_output()
    act.port = of_ports[1]
    self.assertTrue(msg.actions.add(act), "could not add action")

    rv = self.controller.message_send(msg)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return (pkt_MatchSrc,match)
      
def match_ethernet_dst_address(self,of_ports,priority=None):
    #Generate Match_Ethernet_Dst_Address flow

    #Create a simple tcp packet and generate match on ethernet dst address flow
    pkt_matchdst = simple_eth_packet(dl_src='08:00:27:00:d0:07',dl_dst ='78:84:3c:89:fb:5a', dl_type = 0x88cc)
    match = parse.packet_to_flow_match(pkt_matchdst)
    self.assertTrue(match is not None, "Could not generate flow match from pkt")

    match.wildcards = ofp.OFPFW_ALL ^ofp.OFPFW_DL_DST
    msg = message.flow_mod()
    msg.out_port = ofp.OFPP_NONE
    msg.command = ofp.OFPFC_ADD
    msg.buffer_id = 0xffffffff
    msg.match = match
    if priority != None :
        msg.priority = priority

    act = action.action_output()
    act.port = of_ports[1]
    self.assertTrue(msg.actions.add(act), "could not add action")

    rv = self.controller.message_send(msg)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return (pkt_matchdst,match)

def wildcard_all(self,of_ports,priority=None):
# Generate a Wildcard_All Flow 

    #Create a simple tcp packet and generate wildcard all flow match from it.  
    pkt_wildcard = simple_tcp_packet()
    match2 = parse.packet_to_flow_match(pkt_wildcard)
    self.assertTrue(match2 is not None, "Could not generate flow match from pkt")
    match2.wildcards=ofp.OFPFW_ALL
    match2.in_port = of_ports[0]

    msg2 = message.flow_mod()
    msg2.out_port = ofp.OFPP_NONE
    msg2.command = ofp.OFPFC_ADD
    msg2.buffer_id = 0xffffffff
    msg2.match = match2
    act2 = action.action_output()
    act2.port = of_ports[1]
    self.assertTrue(msg2.actions.add(act2), "could not add action")
    if priority != None :
        msg2.priority = priority

    rv = self.controller.message_send(msg2)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return (pkt_wildcard,match2)

def wildcard_all_except_ingress(self,of_ports,priority=None):
# Generate Wildcard_All_Except_Ingress_port flow
        
    #Create a simple tcp packet and generate wildcard all except ingress_port flow.
    pkt_matchingress = simple_tcp_packet()
    match3 = parse.packet_to_flow_match(pkt_matchingress)
    self.assertTrue(match3 is not None, "Could not generate flow match from pkt")
    match3.wildcards = ofp.OFPFW_ALL-ofp.OFPFW_IN_PORT
    match3.in_port = of_ports[0]

    msg3 = message.flow_mod()
    msg3.command = ofp.OFPFC_ADD
    msg3.match = match3
    msg3.out_port = of_ports[2] # ignored by flow add,flow modify 
    msg3.cookie = random.randint(0,9007199254740992)
    msg3.buffer_id = 0xffffffff
    msg3.idle_timeout = 0
    msg3.hard_timeout = 0
    msg3.buffer_id = 0xffffffff

    cookie = msg3.cookie   
    act3 = action.action_output()
    act3.port = of_ports[1]
    self.assertTrue(msg3.actions.add(act3), "could not add action")

    if priority != None :
        msg3.priority = priority

    rv = self.controller.message_send(msg3)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return (pkt_matchingress,match3)

def wildcard_all_except_ingress1(self,of_ports,priority=None):
# Generate Wildcard_All_Except_Ingress_port flow with action output to port egress_port 2 
        

    #Create a simple tcp packet and generate wildcard all except ingress_port flow.
    pkt_matchingress = simple_tcp_packet()
    match3 = parse.packet_to_flow_match(pkt_matchingress)
    self.assertTrue(match3 is not None, "Could not generate flow match from pkt")
    match3.wildcards = ofp.OFPFW_ALL-ofp.OFPFW_IN_PORT
    match3.in_port = of_ports[0]

    msg3 = message.flow_mod()
    msg3.command = ofp.OFPFC_ADD
    msg3.match = match3
    msg3.out_port = of_ports[2] # ignored by flow add,flow modify 
    msg3.cookie = random.randint(0,9007199254740992)
    msg3.buffer_id = 0xffffffff
    msg3.idle_timeout = 0
    msg3.hard_timeout = 0
    msg3.buffer_id = 0xffffffff
       
    act3 = action.action_output()
    act3.port = of_ports[2]
    self.assertTrue(msg3.actions.add(act3), "could not add action")
    if priority != None :
        msg3.priority = priority

    rv = self.controller.message_send(msg3)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return (pkt_matchingress,match3)


def match_vlan_id(self,of_ports,priority=None):
    #Generate Match_Vlan_Id

    #Create a simple tcp packet and generate match on ethernet dst address flow
    pkt_matchvlanid = simple_tcp_packet(dl_vlan_enable=True,dl_vlan=3)
    match = parse.packet_to_flow_match(pkt_matchvlanid)
    self.assertTrue(match is not None, "Could not generate flow match from pkt")

    match.wildcards = ofp.OFPFW_ALL^ofp.OFPFW_DL_TYPE ^ofp.OFPFW_DL_VLAN
    msg = message.flow_mod()
    msg.out_port = ofp.OFPP_NONE
    msg.command = ofp.OFPFC_ADD
    msg.buffer_id = 0xffffffff
    msg.match = match
    if priority != None :
        msg.priority = priority

    act = action.action_output()
    act.port = of_ports[1]
    self.assertTrue(msg.actions.add(act), "could not add action")

    rv = self.controller.message_send(msg)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return (pkt_matchvlanid,match)

def match_vlan_pcp(self,of_ports,priority=None):
    #Generate Match_Vlan_Priority

    #Create a simple tcp packet and generate match on ethernet dst address flow
    pkt_matchvlanpcp = simple_tcp_packet(dl_vlan_enable=True,dl_vlan=3,dl_vlan_pcp=1)
    match = parse.packet_to_flow_match(pkt_matchvlanpcp)
    self.assertTrue(match is not None, "Could not generate flow match from pkt")

    match.wildcards = ofp.OFPFW_ALL ^ofp.OFPFW_DL_TYPE^ofp.OFPFW_DL_VLAN^ofp.OFPFW_DL_VLAN_PCP 
    msg = message.flow_mod()
    msg.out_port = ofp.OFPP_NONE
    msg.command = ofp.OFPFC_ADD
    msg.buffer_id = 0xffffffff
    msg.match = match
    if priority != None :
        msg.priority = priority

    act = action.action_output()
    act.port = of_ports[1]
    self.assertTrue(msg.actions.add(act), "could not add action")

    rv = self.controller.message_send(msg)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return (pkt_matchvlanpcp,match)


def match_mul_l2(self,of_ports,priority=None):
    #Generate Match_Mul_L2 flow

    #Create a simple eth packet and generate match on ethernet protocol flow
    pkt_mulL2 = simple_tcp_packet(dl_vlan_enable=True, dl_src= '00:00:00:01:01:01', dl_dst= '00:00:00:01:01:02', dl_vlan=3)
    match = parse.packet_to_flow_match(pkt_mulL2)
    self.assertTrue(match is not None, "Could not generate flow match from pkt")

    match.wildcards = ofp.OFPFW_ALL ^ofp.OFPFW_IN_PORT ^ofp.OFPFW_DL_TYPE ^ofp.OFPFW_DL_DST ^ofp.OFPFW_DL_SRC ^ofp.OFPFW_DL_VLAN
    match.in_port=of_ports[0]
    msg = message.flow_mod()
    msg.out_port = ofp.OFPP_NONE
    msg.command = ofp.OFPFC_ADD
    msg.buffer_id = 0xffffffff
    msg.match = match
    if priority != None :
        msg.priority = priority

    act = action.action_output()
    act.port = of_ports[1]
    self.assertTrue(msg.actions.add(act), "could not add action")

    rv = self.controller.message_send(msg)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return (pkt_mulL2,match)


def match_mul_l4(self,of_ports,priority=None):
    #Generate Match_Mul_L4 flow

        #Create a simple tcp packet and generate match on tcp protocol flow
    pkt_mulL4 = simple_tcp_packet(tcp_sport=111,tcp_dport=112)
    match = parse.packet_to_flow_match(pkt_mulL4)
    self.assertTrue(match is not None, "Could not generate flow match from pkt")
    match.wildcards = ofp.OFPFW_ALL^ofp.OFPFW_DL_TYPE ^ofp.OFPFW_NW_PROTO^ofp.OFPFW_TP_SRC ^ofp.OFPFW_TP_DST 
    msg = message.flow_mod()
    msg.out_port = ofp.OFPP_NONE
    msg.command = ofp.OFPFC_ADD
    msg.buffer_id = 0xffffffff
    msg.match = match
    if priority != None :
        msg.priority = priority

    act = action.action_output()
    act.port = of_ports[1]
    self.assertTrue(msg.actions.add(act), "could not add action")

    rv = self.controller.message_send(msg)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return (pkt_mulL4,match)  

def match_ip_tos(self,of_ports,priority=None):
    #Generate a Match on IP Type of service flow

        #Create a simple tcp packet and generate match on Type of service 
    pkt_iptos = simple_tcp_packet(ip_tos=30)
    match = parse.packet_to_flow_match(pkt_iptos)
    self.assertTrue(match is not None, "Could not generate flow match from pkt")

    match.wildcards = ofp.OFPFW_ALL^ofp.OFPFW_DL_TYPE^ofp.OFPFW_NW_PROTO ^ofp.OFPFW_NW_TOS
    msg = message.flow_mod()
    msg.out_port = ofp.OFPP_NONE
    msg.command = ofp.OFPFC_ADD
    msg.buffer_id = 0xffffffff
    msg.match = match
    if priority != None :
        msg.priority = priority
    act = action.action_output()
    act.port = of_ports[1]
    self.assertTrue(msg.actions.add(act), "could not add action")

    rv = self.controller.message_send(msg)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return (pkt_iptos,match)

def match_ip_protocol(self,of_ports,priority=None):
    #Generate a Match on IP Protocol

    #Create a simple tcp packet and generate match on Type of service 
    pkt_iptos = simple_tcp_packet()
    match = parse.packet_to_flow_match(pkt_iptos)
    self.assertTrue(match is not None, "Could not generate flow match from pkt")

    match.wildcards = ofp.OFPFW_ALL^ofp.OFPFW_DL_TYPE^ofp.OFPFW_NW_PROTO 
    msg = message.flow_mod()
    msg.out_port = ofp.OFPP_NONE
    msg.command = ofp.OFPFC_ADD
    msg.buffer_id = 0xffffffff
    msg.match = match
    if priority != None :
        msg.priority = priority
    act = action.action_output()
    act.port = of_ports[1]
    self.assertTrue(msg.actions.add(act), "could not add action")

    rv = self.controller.message_send(msg)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return (pkt_iptos,match)


def match_tcp_src(self,of_ports,priority=None):
    #Generate Match_Tcp_Src

    #Create a simple tcp packet and generate match on tcp source port flow
    pkt_matchtSrc = simple_tcp_packet(tcp_sport=111)
    match = parse.packet_to_flow_match(pkt_matchtSrc)
    self.assertTrue(match is not None, "Could not generate flow match from pkt")

    match.wildcards = ofp.OFPFW_ALL^ofp.OFPFW_DL_TYPE ^ofp.OFPFW_NW_PROTO ^ofp.OFPFW_TP_SRC  
    msg = message.flow_mod()
    msg.out_port = ofp.OFPP_NONE
    msg.command = ofp.OFPFC_ADD
    msg.buffer_id = 0xffffffff
    msg.match = match
    if priority != None :
        msg.priority = priority

    act = action.action_output()
    act.port = of_ports[1]
    self.assertTrue(msg.actions.add(act), "could not add action")

    rv = self.controller.message_send(msg)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return (pkt_matchtSrc,match)  

def match_tcp_dst(self,of_ports,priority=None):
    #Generate Match_Tcp_Dst

        #Create a simple tcp packet and generate match on tcp destination port flow
    pkt_matchdst = simple_tcp_packet(tcp_dport=112)
    match = parse.packet_to_flow_match(pkt_matchdst)
    self.assertTrue(match is not None, "Could not generate flow match from pkt")

    match.wildcards = ofp.OFPFW_ALL ^ofp.OFPFW_DL_TYPE^ofp.OFPFW_NW_PROTO^ofp.OFPFW_TP_DST  
    msg = message.flow_mod()
    msg.out_port = ofp.OFPP_NONE
    msg.command = ofp.OFPFC_ADD
    msg.buffer_id = 0xffffffff
    msg.match = match
    if priority != None :
        msg.priority = priority
    act = action.action_output()
    act.port = of_ports[1]
    self.assertTrue(msg.actions.add(act), "could not add action")

    rv = self.controller.message_send(msg)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return (pkt_matchdst,match)        


def match_ethernet_type(self,of_ports,priority=None):
    #Generate a Match_Ethernet_Type flow
    #Create a simple tcp packet and generate match on ethernet type flow
    pkt_matchtype = simple_eth_packet(dl_dst='AC:81:12:99:47:0F',dl_src ='da:c9:f1:19:72:cf',dl_type = 0x88cc)
    match = parse.packet_to_flow_match(pkt_matchtype)
    self.assertTrue(match is not None, "Could not generate flow match from pkt")

    match.wildcards = ofp.OFPFW_ALL ^ofp.OFPFW_DL_TYPE
    msg = message.flow_mod()
    msg.out_port = ofp.OFPP_NONE
    msg.command = ofp.OFPFC_ADD
    msg.buffer_id = 0xffffffff
    msg.match = match
    if priority != None :
        msg.priority = priority

    act = action.action_output()
    act.port = of_ports[1]
    self.assertTrue(msg.actions.add(act), "could not add action")

    rv = self.controller.message_send(msg)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
    return (pkt_matchtype,match)

def strict_modify_flow_action(self,egress_port,match,priority=None):
# Strict Modify the flow Action 
        
    #Create a flow_mod message , command MODIFY_STRICT
    msg5 = message.flow_mod()
    msg5.match = match
    msg5.cookie = random.randint(0,9007199254740992)
    msg5.command = ofp.OFPFC_MODIFY_STRICT
    msg5.buffer_id = 0xffffffff
    act5 = action.action_output()
    act5.port = egress_port
    self.assertTrue(msg5.actions.add(act5), "could not add action")

    if priority != None :
        msg5.priority = priority

    # Send the flow with action A'
    rv = self.controller.message_send (msg5)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

def modify_flow_action(self,of_ports,match,priority=None):
# Modify the flow action
        
    #Create a flow_mod message , command MODIFY 
    msg8 = message.flow_mod()
    msg8.match = match
    msg8.cookie = random.randint(0,9007199254740992)
    msg8.command = ofp.OFPFC_MODIFY
    #out_port will be ignored for flow adds and flow modify (here for test-case Add_Modify_With_Outport)
    msg8.out_port = of_ports[3]
    msg8.buffer_id = 0xffffffff
    act8 = action.action_output()
    act8.port = of_ports[2]
    self.assertTrue(msg8.actions.add(act8), "could not add action")

    if priority != None :
        msg8.priority = priority

    # Send the flow with action A'
    rv = self.controller.message_send (msg8)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

def enqueue(self,ingress_port,egress_port,egress_queue_id):
#Generate a flow with enqueue action i.e output to a queue configured on a egress_port

    pkt = simple_tcp_packet()
    match = parse.packet_to_flow_match(pkt)
    match.wildcards &= ~ofp.OFPFW_IN_PORT
    self.assertTrue(match is not None, 
            "Could not generate flow match from pkt")
    
    match.in_port = ingress_port
    request = message.flow_mod()
    request.match = match
    request.buffer_id = 0xffffffff
    act = action.action_enqueue()
    act.port     = egress_port
    act.queue_id = egress_queue_id
    self.assertTrue(request.actions.add(act), "Could not add action")
    
    logging.info("Inserting flow")
    rv = self.controller.message_send(request)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
    return (pkt,match)


###########################   Verify Stats Functions   ###########################################################################################
def get_flowstats(self,match):
    # Generate flow_stats request
    
    stat_req = message.flow_stats_request()
    stat_req.match = match
    stat_req.table_id = 0xff
    stat_req.out_port = ofp.OFPP_NONE

    logging.info("Sending stats request")
    response, pkt = self.controller.transact(stat_req,
                                                     timeout=5)
    self.assertTrue(response is not None,"No response to stats request")


def get_aggstats(self,match):
    # Generate aggregate flow_stats request

    stats_req =  message.aggregate_stats_request()
    stat_req.match = match
    stat_req.table_id = 0xff
    stat_req.out_port = ofp.OFPP_NONE

    logging.info("Sending stats request")
    (response, pkt) = self.controller.transact(stat_req,
                                                     timeout=5)
    self.assertTrue(response is not None,"No response to stats request")
    return (response,pkt)


def get_portstats(self,port_num):

# Return all the port counters in the form a tuple 
    port_stats_req = message.port_stats_request()
    port_stats_req.port_no = port_num  
    response,pkt = self.controller.transact(port_stats_req)
    self.assertTrue(response is not None,"No response received for port stats request") 
    rx_pkts=0
    tx_pkts=0
    rx_byts=0
    tx_byts=0
    rx_drp =0
    tx_drp = 0
    rx_err=0
    tx_err =0 
    rx_fr_err=0
    rx_ovr_err=0
    rx_crc_err=0
    collisions = 0
    tx_err=0


    for obj in response.stats:
        rx_pkts += obj.rx_packets
        tx_pkts += obj.tx_packets
        rx_byts += obj.rx_bytes
        tx_byts += obj.tx_bytes
        rx_drp += obj.rx_dropped
        tx_drp += obj.tx_dropped
        rx_err += obj.rx_errors
        rx_fr_err += obj.rx_frame_err
        rx_ovr_err += obj.rx_over_err
        rx_crc_err += obj.rx_crc_err
        collisions+= obj.collisions
        tx_err += obj.tx_errors

    return (rx_pkts,tx_pkts,rx_byts,tx_byts,rx_drp,tx_drp,rx_err,tx_err,rx_fr_err,rx_ovr_err,rx_crc_err,collisions,tx_err)

def get_queuestats(self,port_num,queue_id):
#Generate Queue Stats request 

    request = message.queue_stats_request()
    request.port_no  = port_num
    request.queue_id = queue_id
    (queue_stats, p) = self.controller.transact(request)
    self.assertNotEqual(queue_stats, None, "Queue stats request failed")
    self.assertNotEqual(queue_stats.header.type, ofp.OFPT_ERROR, ' Cannot retreive the queue_stats: Check if the switch supports queue_stats request')
    return (queue_stats,p)

def get_tablestats(self):
# Send Table_Stats request (retrieve current table counters )

    stat_req = message.table_stats_request()
    response, pkt = self.controller.transact(stat_req,
                                                     timeout=5)
    self.assertTrue(response is not None, 
                            "No response to stats request")
    current_lookedup = 0
    current_matched = 0
    current_active = 0 

    for obj in response.stats:
        current_lookedup += obj.lookup_count
        current_matched  += obj.matched_count
        current_active += obj.active_count

    return (current_lookedup,current_matched,current_active)



def verify_tablestats(self,expect_lookup=None,expect_match=None,expect_active=None):

    stat_req = message.table_stats_request()
    
    for i in range(0,60):

        logging.info("Sending stats request")
        # TODO: move REPLY_MORE handling to controller.transact?
        response, pkt = self.controller.transact(stat_req,
                                                     timeout=5)
        self.assertTrue(response is not None,"No response to stats request")

        lookedup = 0 
        matched = 0 
        active = 0

        sleep(1)
        
        for item in response.stats:
            lookedup += item.lookup_count
            matched += item.matched_count
            active += item.active_count

            logging.info("Packets Looked up " + str(lookedup) + " packets")
            logging.info("Packets matched " + str(matched) + "packets")
            logging.info("Active flow entries" + str(active) + "flows")
        
        if expect_lookup != None and expect_lookup != lookedup:continue
        if expect_match != None and expect_match != matched:continue
        if expect_active != None and expect_active != active:continue
        break

        

    if expect_lookup != None :
        self.assertEqual(expect_lookup,item.lookup_count,"lookup counter is not incremented properly")
    if expect_match != None :
        self.assertEqual(expect_match,item.matched_count, "matched counter is not incremented properly")
    if expect_active != None :
        self.assertEqual(expect_active,item.active_count,"active counter is not incremented properly")


def verify_flowstats(self,match,byte_count=None,packet_count=None):
    '''
    Ensures that packet_count packets and byte_count bytes have
    been recorded and are advertised by dut.
    '''
    stat_req = message.flow_stats_request()
    stat_req.match = match
    stat_req.table_id = 0xff
    stat_req.out_port = ofp.OFPP_NONE
    
    for i in range(0,60):
        logging.info("Sending stats request")
        # TODO: move REPLY_MORE handling to controller.transact?
        response, pkt = self.controller.transact(stat_req,
                                                     timeout=5)
        self.assertTrue(response is not None,"No response to stats request")

        packet_counter = 0
        byte_counter = 0 

        sleep(1)

        for item in response.stats:
            packet_counter += item.packet_count
            byte_counter += item.byte_count

            logging.info("packet_counter " + str(item.packet_count) + " packets")
            logging.info("byte_counter " + str(item.byte_count) + " bytes")
           
        if packet_count != None  and  packet_count != packet_counter: continue
        if byte_count != None  and  byte_count != byte_counter: continue
        break
    counter=[byte_counter,byte_counter+20]
    if packet_count != None :
        self.assertEqual(packet_count, packet_counter, "Expected packet count of {0} recived {1} instead.".format(packet_count, packet_counter))

    if byte_count != None :   
        self.assertIn(byte_count, counter, "Expected byte count of {0} received {1} instead.".format(byte_count, counter))


def verify_portstats(self, port,tx_packets=None,rx_packets=None,rx_byte=None,tx_byte=None):

    
    stat_req = message.port_stats_request()
    stat_req.port_no = port
    
    for i in range(0,60):
        logging.info("Sending stats request")
        response, pkt = self.controller.transact(stat_req,
                                                timeout=5)
        self.assertTrue(response is not None, 
                       "No response to stats request")

        sentp = recvp = 0
        sentb = recvb = 0

        sleep(1)
        
        for item in response.stats:
            sentp += item.tx_packets
            recvp += item.rx_packets
            recvb += item.rx_bytes
            sentb += item.tx_bytes
           
            
            logging.info("Tx_packet counter " + str(sentp) + " packets")
            logging.info("Rx_packet counter " + str(recvp) + " packets")
            logging.info("Rx_byte counter" + str(recvb) + "bytes")
            logging.info("Tx_byte counter" + str(sentb) + "bytes")
    
        if tx_packets != None  and  tx_packets != sentp: continue
        if rx_packets != None  and  rx_packets != recvp: continue 
        if rx_byte != None  and  rx_byte != recvb: continue
        if tx_byte != None  and  tx_byte != sentb: continue
        
        break
        
    if (tx_packets != None):
        self.assertEqual(tx_packets,sentp,"tx_packets counter is not incremented correctly")
    if (rx_packets != None):
        self.assertEqual(rx_packets,recvp,"rx_packets counter is not incremented correctly")
    if (rx_byte != None):
        self.assertEqual(rx_byte,recvb,"rx_bytes counter is not incremented correctly")
    if (tx_byte != None):
        self.assertEqual(tx_byte,sentb,"tx_bytes counter is not incremented correctly")


def verify_queuestats(self,port_num,queue_id,expect_packet=None,expect_byte=None):
    
    # Verify queue counters : tx_packets and tx_bytes

    request = message.queue_stats_request()
    request.port_no  = port_num
    request.queue_id = queue_id
    
    for i in range(0,60):

        logging.info("Sending stats request")
     
        (queue_stats, p) = self.controller.transact(request)
        self.assertNotEqual(queue_stats, None, "Queue stats request failed")
        packet_counter = 0
        byte_counter = 0 

        sleep(1)
        
        for item in queue_stats.stats:
            packet_counter += item.tx_packets
            byte_counter += item.tx_bytes

            logging.info("Transmitted" + str(packet_counter) + " packets")
            logging.info("Transmitted" + str(byte_counter) + "bytes")
           
        if expect_packet != None  and  packet_counter != expect_packet: continue
        if expect_byte != None  and  byte_counter != expect_byte: continue
        break

        
    
    if expect_packet != None :
        self.assertEqual(packet_counter,expect_packet,"tx_packets counter is not incremented correctly")

    if expect_byte != None :   
        self.assertEqual(byte_counter,expect_byte,"tx_bytes counter is not incremented correctly")


############################## Various delete commands #############################################################################################

def strict_delete(self,match,priority=None):
# Issue Strict Delete 
        
    #Create flow_mod message, command DELETE_STRICT
    msg = message.flow_mod()
    msg.out_port = ofp.OFPP_NONE
    msg.command = ofp.OFPFC_DELETE_STRICT
    msg.buffer_id = 0xffffffff
    msg.match = match

    if priority != None :
        msg.priority = priority
    rv = self.controller.message_send(msg)
    self.assertTrue(rv!= -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")



def nonstrict_delete(self,match,priority=None):
# Issue Non_Strict Delete 
        
    #Create flow_mod message, command DELETE
    msg6 = message.flow_mod()
    msg6.out_port = ofp.OFPP_NONE
    msg6.command = ofp.OFPFC_DELETE
    msg6.buffer_id = 0xffffffff
    msg6.match = match

    if priority != None :
        msg6.priority = priority

    rv = self.controller.message_send(msg6)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller),0, "Barrier failed")


def nonstrict_delete_emer(self,match,priority=None):
# Issue Non_Strict Delete Emer
        
    #Create flow_mod message, command DELETE for an emergency flow
    msg6 = message.flow_mod()
    msg6.out_port = ofp.OFPP_NONE
    msg6.command = ofp.OFPFC_DELETE
    msg6.buffer_id = 0xffffffff
    msg6.match = match
    msg6.flags = msg6.flags | ofp.OFPFF_EMERG
    
    if priority != None :
        msg6.priority = priority

    rv = self.controller.message_send(msg6)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller),0, "Barrier failed")


def delete_all_flows_emer(ctrl):
    """
    Delete all emergency flows on the switch
    @param ctrl The controller object for the test
    """

    logging.info("Deleting all emergency flows")
    msg = message.flow_mod()
    msg.match.wildcards = ofp.OFPFW_ALL
    msg.out_port = ofp.OFPP_NONE
    msg.command = ofp.OFPFC_DELETE
    msg.flags = msg.flags | ofp.OFPFF_EMERG
    msg.buffer_id = 0xffffffff
    return ctrl.message_send(msg)

###########################################################################################################################################################

def send_packet(obj, pkt, ingress_port, egress_port):
#Send Packets on a specified ingress_port and verify if its recieved on correct egress_port.

    obj.dataplane.send(ingress_port, str(pkt))
    exp_pkt_arg = pkt
    exp_port = egress_port

    (rcv_port, rcv_pkt, pkt_time) = obj.dataplane.poll(timeout=2, 
                                                       port_number=exp_port,
                                                       exp_pkt=exp_pkt_arg)
    obj.assertTrue(rcv_pkt is not None,
                   "Packet not received on port " + str(egress_port))
    obj.assertEqual(rcv_port, egress_port,
                    "Packet received on port " + str(rcv_port) +
                    ", expected port " + str(egress_port))
    obj.assertEqual(str(pkt), str(rcv_pkt),
                    'Response packet does not match send packet')


def sw_supported_actions(parent,use_cache=False):
#Returns the switch's supported actions

    cache_supported_actions = None
    if cache_supported_actions is None or not use_cache:
        request = message.features_request()
        (reply, pkt) = parent.controller.transact(request)
        parent.assertTrue(reply is not None, "Did not get response to ftr req")
        cache_supported_actions = reply.actions
    return cache_supported_actions





    
   
 
   




