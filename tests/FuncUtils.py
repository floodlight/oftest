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

def Exact_Match(self,of_ports,priority=0):
# Generate ExactMatch flow .

        #Create a simple tcp packet and generate exact flow match from it.
        Pkt_ExactFlow = simple_tcp_packet()
        match = parse.packet_to_flow_match(Pkt_ExactFlow)
        self.assertTrue(match is not None, "Could not generate flow match from pkt")
        match.in_port = of_ports[0]
        #match.nw_src = 1
        match.wildcards=0
        msg = message.flow_mod()
        msg.out_port = ofp.OFPP_NONE
        msg.command = ofp.OFPFC_ADD
        msg.buffer_id = 0xffffffff
        msg.match = match
        if priority != 0 :
                msg.priority = priority

        act = action.action_output()
        act.port = of_ports[1]
        self.assertTrue(msg.actions.add(act), "could not add action")

        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        return (Pkt_ExactFlow,match)

def Exact_Match_With_Prio(self,of_ports,priority=0):
    # Generate ExactMatch With Prority flow .

        #Create a simple tcp packet and generate exact flow match from it.
        Pkt_ExactFlow = simple_tcp_packet()
        match = parse.packet_to_flow_match(Pkt_ExactFlow)
        self.assertTrue(match is not None, "Could not generate flow match from pkt")
        match.in_port = of_ports[0]
        #match.nw_src = 1
        match.wildcards=0
        msg = message.flow_mod()
        msg.out_port = ofp.OFPP_NONE
        msg.command = ofp.OFPFC_ADD
        msg.buffer_id = 0xffffffff
        msg.match = match
        if priority != 0 :
                msg.priority = priority

        act = action.action_output()
        act.port = of_ports[2]
        self.assertTrue(msg.actions.add(act), "could not add action")

        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        return (Pkt_ExactFlow,match)         
       

def Match_All_Except_Source_Address(self,of_ports,priority=0):
# Generate Match_All_Except_Source_Address flow
        
        #Create a simple tcp packet and generate match all except src address flow.
        Pkt_WildcardSrc= simple_tcp_packet()
        match1 = parse.packet_to_flow_match(Pkt_WildcardSrc)
        self.assertTrue(match1 is not None, "Could not generate flow match from pkt")
        match1.in_port = of_ports[0]
        #match1.nw_src = 1
        match1.wildcards = ofp.OFPFW_DL_SRC
        msg1 = message.flow_mod()
        msg1.out_port = ofp.OFPP_NONE
        msg1.command = ofp.OFPFC_ADD
        msg1.buffer_id = 0xffffffff
        msg1.match = match1
        if priority != 0 :
                msg1.priority = priority

        act1 = action.action_output()
        act1.port = of_ports[1]
        self.assertTrue(msg1.actions.add(act1), "could not add action")

        rv = self.controller.message_send(msg1)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        return (Pkt_WildcardSrc,match1)

def Match_Ethernet_Src_Address(self,of_ports,priority=0):
    #Generate Match_Ethernet_SrC_Address flow

        #Create a simple tcp packet and generate match on ethernet src address flow
        pkt_MatchSrc = simple_tcp_packet(dl_src='00:01:01:01:01:01')
        match = parse.packet_to_flow_match(pkt_MatchSrc)
        self.assertTrue(match is not None, "Could not generate flow match from pkt")

        match.wildcards = ofp.OFPFW_ALL ^ofp.OFPFW_DL_SRC
        
        msg = message.flow_mod()
        msg.out_port = ofp.OFPP_NONE
        msg.command = ofp.OFPFC_ADD
        msg.buffer_id = 0xffffffff
        msg.match = match
        if priority != 0 :
                msg.priority = priority

        act = action.action_output()
        act.port = of_ports[1]
        self.assertTrue(msg.actions.add(act), "could not add action")

        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        return (pkt_MatchSrc,match)
      
def Match_Ethernet_Dst_Address(self,of_ports,priority=0):
    #Generate Match_Ethernet_Dst_Address flow

        #Create a simple tcp packet and generate match on ethernet dst address flow
        pkt_MatchDst = simple_tcp_packet(dl_dst='00:01:01:01:01:01')
        match = parse.packet_to_flow_match(pkt_MatchDst)
        self.assertTrue(match is not None, "Could not generate flow match from pkt")

        match.wildcards = ofp.OFPFW_ALL ^ofp.OFPFW_DL_DST
        msg = message.flow_mod()
        msg.out_port = ofp.OFPP_NONE
        msg.command = ofp.OFPFC_ADD
        msg.buffer_id = 0xffffffff
        msg.match = match
        if priority != 0 :
                msg.priority = priority

        act = action.action_output()
        act.port = of_ports[1]
        self.assertTrue(msg.actions.add(act), "could not add action")

        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        return (pkt_MatchDst,match)

def Wildcard_All(self,of_ports,priority=0):
# Generate a Wildcard_All Flow 

        #Create a simple tcp packet and generate wildcard all flow match from it.  
        Pkt_Wildcard = simple_tcp_packet()
        match2 = parse.packet_to_flow_match(Pkt_Wildcard)
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
        if priority != 0 :
                msg2.priority = priority

        rv = self.controller.message_send(msg2)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        return (Pkt_Wildcard,match2)

def Wildcard_All_Except_Ingress(self,of_ports,priority=0):
# Generate Wildcard_All_Except_Ingress_port flow
        

        #Create a simple tcp packet and generate wildcard all except ingress_port flow.
        Pkt_MatchIngress = simple_tcp_packet()
        match3 = parse.packet_to_flow_match(Pkt_MatchIngress)
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
        act3.port = of_ports[1]
        self.assertTrue(msg3.actions.add(act3), "could not add action")

        if priority != 0 :
                msg3.priority = priority

        rv = self.controller.message_send(msg3)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        return (Pkt_MatchIngress,match3)

def Wildcard_All_Except_Ingress1(self,of_ports,priority=0):
# Generate Wildcard_All_Except_Ingress_port flow with action output to port egress_port 2 
        

        #Create a simple tcp packet and generate wildcard all except ingress_port flow.
        Pkt_MatchIngress = simple_tcp_packet()
        match3 = parse.packet_to_flow_match(Pkt_MatchIngress)
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

        if priority != 0 :
                msg3.priority = priority

        rv = self.controller.message_send(msg3)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        return (Pkt_MatchIngress,match3)




def Match_Vlan_Id(self,of_ports,priority=0):
    #Generate Match_Vlan_Id

        #Create a simple tcp packet and generate match on ethernet dst address flow
        pkt_MatchVlanId = simple_tcp_packet(dl_vlan_enable=True,dl_vlan=1)
        match = parse.packet_to_flow_match(pkt_MatchVlanId)
        self.assertTrue(match is not None, "Could not generate flow match from pkt")

        match.wildcards = ofp.OFPFW_ALL ^ofp.OFPFW_DL_VLAN
        msg = message.flow_mod()
        msg.out_port = ofp.OFPP_NONE
        msg.command = ofp.OFPFC_ADD
        msg.buffer_id = 0xffffffff
        msg.match = match
        if priority != 0 :
                msg.priority = priority

        act = action.action_output()
        act.port = of_ports[1]
        self.assertTrue(msg.actions.add(act), "could not add action")

        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        return (pkt_MatchVlanId,match)

def Match_Vlan_Pcp(self,of_ports,priority=0):
    #Generate Match_Vlan_Id

        #Create a simple tcp packet and generate match on ethernet dst address flow
        pkt_MatchVlanPcp = simple_tcp_packet(dl_vlan_enable=True,dl_vlan=1,dl_vlan_pcp=10)
        match = parse.packet_to_flow_match(pkt_MatchVlanPcp)
        self.assertTrue(match is not None, "Could not generate flow match from pkt")

        match.wildcards = ofp.OFPFW_ALL ^ofp.OFPFW_DL_VLAN_PCP 
        msg = message.flow_mod()
        msg.out_port = ofp.OFPP_NONE
        msg.command = ofp.OFPFC_ADD
        msg.buffer_id = 0xffffffff
        msg.match = match
        if priority != 0 :
                msg.priority = priority

        act = action.action_output()
        act.port = of_ports[1]
        self.assertTrue(msg.actions.add(act), "could not add action")

        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        return (pkt_MatchVlanPcp,match)


def Match_Mul_L2(self,of_ports,priority=0):
    #Generate Match_Mul_L2 flow

        #Create a simple eth packet and generate match on ethernet protocol flow
        pkt_MulL2 = simple_eth_packet(dl_type=0x88cc,dl_src='00:01:01:01:01:01',dl_dst='00:01:01:01:01:02')
        match = parse.packet_to_flow_match(pkt_MulL2)
        self.assertTrue(match is not None, "Could not generate flow match from pkt")

        match.wildcards = ofp.OFPFW_ALL ^ofp.OFPFW_DL_TYPE ^ofp.OFPFW_DL_DST ^ofp.OFPFW_DL_SRC
        msg = message.flow_mod()
        msg.out_port = ofp.OFPP_NONE
        msg.command = ofp.OFPFC_ADD
        msg.buffer_id = 0xffffffff
        msg.match = match
        if priority != 0 :
                msg.priority = priority

        act = action.action_output()
        act.port = of_ports[1]
        self.assertTrue(msg.actions.add(act), "could not add action")

        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        return (pkt_MulL2,match)


def Match_Mul_L4(self,of_ports,priority=0):
    #Generate Match_Mul_L4 flow

        #Create a simple tcp packet and generate match on tcp protocol flow
        pkt_MulL4 = simple_tcp_packet(tcp_sport=111,tcp_dport=112)
        match = parse.packet_to_flow_match(pkt_MulL4)
        self.assertTrue(match is not None, "Could not generate flow match from pkt")

        match.wildcards = ofp.OFPFW_ALL ^ofp.OFPFW_TP_SRC ^ofp.OFPFW_TP_DST 
        msg = message.flow_mod()
        msg.out_port = ofp.OFPP_NONE
        msg.command = ofp.OFPFC_ADD
        msg.buffer_id = 0xffffffff
        msg.match = match
        if priority != 0 :
                msg.priority = priority

        act = action.action_output()
        act.port = of_ports[1]
        self.assertTrue(msg.actions.add(act), "could not add action")

        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        return (pkt_MulL4,match)  

def Match_Ip_Tos(self,of_ports,priority=0):
    #Generate a Match on IP Type of service flow

        #Create a simple tcp packet and generate match on Type of service 
        pkt_IpTos = simple_tcp_packet(ip_tos=3)
        match = parse.packet_to_flow_match(pkt_IpTos)
        self.assertTrue(match is not None, "Could not generate flow match from pkt")

        match.wildcards = ofp.OFPFW_ALL ^ofp.OFPFW_NW_TOS
        msg = message.flow_mod()
        msg.out_port = ofp.OFPP_NONE
        msg.command = ofp.OFPFC_ADD
        msg.buffer_id = 0xffffffff
        msg.match = match
        if priority != 0 :
                msg.priority = priority

        act = action.action_output()
        act.port = of_ports[1]
        self.assertTrue(msg.actions.add(act), "could not add action")

        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        return (pkt_IpTos,match)

def Match_Tcp_Src(self,of_ports,priority=0):
    #Generate Match_Tcp_Src

        #Create a simple tcp packet and generate match on tcp source port flow
        pkt_MatchTSrc = simple_tcp_packet(tcp_sport=111)
        match = parse.packet_to_flow_match(pkt_MatchTSrc)
        self.assertTrue(match is not None, "Could not generate flow match from pkt")

        match.wildcards = ofp.OFPFW_ALL ^ofp.OFPFW_TP_SRC  
        msg = message.flow_mod()
        msg.out_port = ofp.OFPP_NONE
        msg.command = ofp.OFPFC_ADD
        msg.buffer_id = 0xffffffff
        msg.match = match
        if priority != 0 :
                msg.priority = priority

        act = action.action_output()
        act.port = of_ports[1]
        self.assertTrue(msg.actions.add(act), "could not add action")

        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        return (pkt_MatchTSrc,match)  

def Match_Tcp_Dst(self,of_ports,priority=0):
    #Generate Match_Tcp_Dst

        #Create a simple tcp packet and generate match on tcp destination port flow
        pkt_MatchTDst = simple_tcp_packet(tcp_dport=112)
        match = parse.packet_to_flow_match(pkt_MatchTDst)
        self.assertTrue(match is not None, "Could not generate flow match from pkt")

        match.wildcards = ofp.OFPFW_ALL ^ofp.OFPFW_TP_DST  
        msg = message.flow_mod()
        msg.out_port = ofp.OFPP_NONE
        msg.command = ofp.OFPFC_ADD
        msg.buffer_id = 0xffffffff
        msg.match = match
        if priority != 0 :
                msg.priority = priority

        act = action.action_output()
        act.port = of_ports[1]
        self.assertTrue(msg.actions.add(act), "could not add action")

        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        return (pkt_MatchTDst,match)        





def Match_Ethernet_Type(self,of_ports,priority=0):
    #Generate a Match_Ethernet_Type flow

        #Create a simple tcp packet and generate match on ethernet type flow
        pkt_MatchType = simple_eth_packet(dl_type=0x88cc)
        match = parse.packet_to_flow_match(pkt_MatchType)
        self.assertTrue(match is not None, "Could not generate flow match from pkt")

        match.wildcards = ofp.OFPFW_ALL ^ofp.OFPFW_DL_TYPE
        msg = message.flow_mod()
        msg.out_port = ofp.OFPP_NONE
        msg.command = ofp.OFPFC_ADD
        msg.buffer_id = 0xffffffff
        msg.match = match
        if priority != 0 :
                msg.priority = priority

        act = action.action_output()
        act.port = of_ports[1]
        self.assertTrue(msg.actions.add(act), "could not add action")

        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        return (pkt_MatchType,match)

   
   
def Strict_Modify_Flow_Action(self,egress_port,match,priority=0):
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

        if priority != 0 :
                msg5.priority = priority

        # Send the flow with action A'
        rv = self.controller.message_send (msg5)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

def Modify_Flow_Action(self,of_ports,match,priority=0):
# Modify the flow action
        
        #Create a flow_mod message , command MODIFY 
        msg8 = message.flow_mod()
        msg8.match = match
        msg8.cookie = random.randint(0,9007199254740992)
        msg8.command = ofp.OFPFC_MODIFY
        #Will be ignored for flow adds and flow modify (here for test-case Add_Modify_With_Outport)
        msg8.out_port = of_ports[3]
        msg8.buffer_id = 0xffffffff
        act8 = action.action_output()
        act8.port = of_ports[2]
        self.assertTrue(msg8.actions.add(act8), "could not add action")

        if priority != 0 :
                msg8.priority = priority

        # Send the flow with action A'
        rv = self.controller.message_send (msg8)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

def Enqueue(self,ingress_port,egress_port,egress_queue_id):
#Generate a flow with enqueue action i.e output to a queue configured on a egress_port

        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
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


def Get_QueueStats(self,port_num,queue_id):
#Generate Queue Stats request 

    request = message.queue_stats_request()
    request.port_no  = port_num
    request.queue_id = queue_id
    (queue_stats, p) = self.controller.transact(request)
    self.assertNotEqual(queue_stats, None, "Queue stats request failed")

    return (queue_stats,p)

def Verify_TableStats(self,active_entries=0):
#Verify Table_Stats
        
        #Send Table_Stats_Request        
        request = message.table_stats_request()
        response, pkt = self.controller.transact(request, timeout=1)
        self.assertTrue(response is not None, "Did not get response")
        active_count=0

        #Verify active_count in the reply
        for stat in response.stats:
            active_count += stat.active_count
        self.assertTrue(active_entries == active_count,"Incorrect no. of flows in Table")

def Verify_TableStats1(self,current_lookedup,current_matched,expect_lookup,expect_match):
       
        stat_req = message.table_stats_request()
        response, pkt = self.controller.transact(stat_req,
                                                     timeout=5)
        self.assertTrue(response is not None, 
                            "No response to stats request")
        lookedup = 0
        matched = 0 
            
        for obj in response.stats:
            lookedup += obj.lookup_count
            matched += obj.matched_count
        
        lookedup_counter = lookedup-current_lookedup
        matched_counter = matched-current_matched
        
        self.assertTrue(lookedup_counter==expect_lookup, "lookup counter is not incremented properly")
        self.assertTrue(matched_counter==expect_lookup, "matched counter is not incremented properly")

def Verify_FlowStats(self,match,byte_count=0,packet_count=0):
    # Verify flow counters : byte_count and packet_count

        stat_req = message.flow_stats_request()
        stat_req.match = match
        stat_req.table_id = 0xff
        stat_req.out_port = ofp.OFPP_NONE
        response, pkt = self.controller.transact(stat_req,
                                                     timeout=4)
        self.assertTrue(response is not None, 
                            "No response to stats request")
        packetcounter=0
        bytecounter=0
        for obj in response.stats:
            packetcounter += obj.packet_count
            bytecounter += obj.byte_count

        self.assertTrue(packetcounter==packet_count, "packet counter is not incremented properly")
        self.assertTrue(bytecounter==byte_count, "byte counter is not incremented properly")


def Verify_PortStats(self,in_port,rx_dropped):
#Verify Port counters like rx_dropped

        port_stats_req = message.port_stats_request()
        port_stats_req.port_no = in_port   
        resp,pkt = self.controller.transact(port_stats_req)
        self.assertTrue(resp is not None,"No response received for port stats request")        
        self.assertTrue(resp.rx_dropped == rx_dropped, "Packets not dropped")

def Verify_PortStats1(self,out_port,current_counter,rx_packets):
#Verify Port counters like rx_packets

        port_stats_req = message.port_stats_request()
        port_stats_req.port_no = out_port     
        response,pkt = self.controller.transact(port_stats_req)
        self.assertTrue(response is not None,"No response received for port stats request") 
        rxpackets=0
       
        for obj in response.stats:
            rxpackets += obj.rx_packets
        rx_packet_counter = rxpackets-current_counter    
        self.assertEqual(rx_packets,rx_packet_counter,"recieved packet counter is not incremented properly")

def Verify_PortStats2(self,out_port,current_counter,tx_packets):
#Verify Port counters like tx_packets

        port_stats_req = message.port_stats_request()
        port_stats_req.port_no = out_port     
        response,pkt = self.controller.transact(port_stats_req)
        self.assertTrue(response is not None,"No response received for port stats request") 
        txpackets=0
       
        for obj in response.stats:
            txpackets += obj.tx_packets
        tx_packet_counter = txpackets-current_counter    
        self.assertEqual(tx_packets,tx_packet_counter,"Transmitted packet counter is not incremented properly")    


def Verify_PortStats3(self,out_port,current_counter,rx_bytes):
#Verify Port counters like rx_bytes

        port_stats_req = message.port_stats_request()
        port_stats_req.port_no = out_port     
        response,pkt = self.controller.transact(port_stats_req)
        self.assertTrue(response is not None,"No response received for port stats request") 
        rxbytes=0
       
        for obj in response.stats:
            rxbytes += obj.rx_bytes
        rx_byte_counter = rxbytes-current_counter    
        self.assertEqual(rx_bytes,rx_byte_counter,"Recieved byte counter is not incremented properly")   

def Verify_PortStats4(self,out_port,current_counter,tx_bytes):
#Verify Port counters like tx_bytes

        port_stats_req = message.port_stats_request()
        port_stats_req.port_no = out_port     
        response,pkt = self.controller.transact(port_stats_req)
        self.assertTrue(response is not None,"No response received for port stats request") 
        txbytes=0
       
        for obj in response.stats:
            txbytes += obj.tx_bytes
        tx_byte_counter = txbytes-current_counter    
        self.assertEqual(tx_bytes,tx_byte_counter,"Transmitted byte counter is not incremented properly")  

############################## Various delete commands #############################################################################################

def Strict_Delete(self,match,priority=0):
# Issue Strict Delete 
        
        #Create flow_mod message, command DELETE_STRICT
        msg4 = message.flow_mod()
        msg4.out_port = ofp.OFPP_NONE
        msg4.command = ofp.OFPFC_DELETE_STRICT
        msg4.buffer_id = 0xffffffff
        msg4.match = match

        if priority != 0 :
                msg4.priority = priority

        rv = self.controller.message_send(msg4)
        self.assertTrue(rv!= -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")



def NonStrict_Delete(self,match,priority=0):
# Issue Non_Strict Delete 
        
        #Create flow_mod message, command DELETE
        msg6 = message.flow_mod()
        msg6.out_port = ofp.OFPP_NONE
        msg6.command = ofp.OFPFC_DELETE
        msg6.buffer_id = 0xffffffff
        msg6.match = match

        if priority != 0 :
                msg6.priority = priority

        rv = self.controller.message_send(msg6)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller),0, "Barrier failed")


###########################################################################################################################################################

def SendPacket(obj, pkt, ingress_port, egress_port):
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

##############################################################################################################################################################

