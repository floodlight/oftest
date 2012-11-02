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

def exact_match(self,of_ports,priority=0):
# Generate ExactMatch flow .

    #Create a simple tcp packet and generate exact flow match from it.
    pkt_exactflow = simple_tcp_packet()
    match = parse.packet_to_flow_match(pkt_exactflow)
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

    return (pkt_exactflow,match)

def exact_match_with_prio(self,of_ports,priority=0):
    # Generate ExactMatch with action output to port 2

    #Create a simple tcp packet and generate exact flow match from it.
    pkt_exactflow = simple_tcp_packet()
    match = parse.packet_to_flow_match(pkt_exactflow)
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

    return (pkt_exactflow,match)         
       

def match_all_except_source_address(self,of_ports,priority=0):
# Generate Match_All_Except_Source_Address flow
        
    #Create a simple tcp packet and generate match all except src address flow.
    pkt_wildcardsrc= simple_tcp_packet()
    match1 = parse.packet_to_flow_match(pkt_wildcardsrc)
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

    return (pkt_wildcardsrc,match1)

def match_wthernet_src_address(self,of_ports,priority=0):
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
      
def match_ethernet_dst_address(self,of_ports,priority=0):
    #Generate Match_Ethernet_Dst_Address flow

    #Create a simple tcp packet and generate match on ethernet dst address flow
    pkt_matchdst = simple_tcp_packet(dl_dst='00:01:01:01:01:01')
    match = parse.packet_to_flow_match(pkt_matchdst)
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

    return (pkt_matchdst,match)

def wildcard_all(self,of_ports,priority=0):
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
    if priority != 0 :
        msg2.priority = priority

    rv = self.controller.message_send(msg2)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return (pkt_wildcard,match2)

def wildcard_all_except_ingress(self,of_ports,priority=0):
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
       
    act3 = action.action_output()
    act3.port = of_ports[1]
    self.assertTrue(msg3.actions.add(act3), "could not add action")

    if priority != 0 :
        msg3.priority = priority

    rv = self.controller.message_send(msg3)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return (pkt_matchingress,match3)

def wildcard_all_except_ingress1(self,of_ports,priority=0):
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
    if priority != 0 :
        msg3.priority = priority

    rv = self.controller.message_send(msg3)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    return (pkt_matchingress,match3)




def match_vlan_id(self,of_ports,priority=0):
    #Generate Match_Vlan_Id

    #Create a simple tcp packet and generate match on ethernet dst address flow
    pkt_matchvlanid = simple_tcp_packet(dl_vlan_enable=True,dl_vlan=1)
    match = parse.packet_to_flow_match(pkt_matchvlanid)
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

    return (pkt_matchvlanid,match)

def match_vlan_pcp(self,of_ports,priority=0):
    #Generate Match_Vlan_Id

    #Create a simple tcp packet and generate match on ethernet dst address flow
    pkt_matchvlanpcp = simple_tcp_packet(dl_vlan_enable=True,dl_vlan=1,dl_vlan_pcp=10)
    match = parse.packet_to_flow_match(pkt_matchvlanpcp)
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

    return (pkt_matchvlanpcp,match)


def match_mul_l2(self,of_ports,priority=0):
    #Generate Match_Mul_L2 flow

    #Create a simple eth packet and generate match on ethernet protocol flow
    pkt_mulL2 = simple_eth_packet(dl_type=0x88cc,dl_src='00:01:01:01:01:01',dl_dst='00:01:01:01:01:02')
    match = parse.packet_to_flow_match(pkt_mulL2)
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

    return (pkt_mulL2,match)


def match_mul_L4(self,of_ports,priority=0):
    #Generate Match_Mul_L4 flow

        #Create a simple tcp packet and generate match on tcp protocol flow
    pkt_mulL4 = simple_tcp_packet(tcp_sport=111,tcp_dport=112)
    match = parse.packet_to_flow_match(pkt_mulL4)
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

    return (pkt_mulL4,match)  

def match_ip_tos(self,of_ports,priority=0):
    #Generate a Match on IP Type of service flow

        #Create a simple tcp packet and generate match on Type of service 
    pkt_iptos = simple_tcp_packet(ip_tos=3)
    match = parse.packet_to_flow_match(pkt_iptos)
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

    return (pkt_iptos,match)

def match_tcp_src(self,of_ports,priority=0):
    #Generate Match_Tcp_Src

    #Create a simple tcp packet and generate match on tcp source port flow
    pkt_matchtSrc = simple_tcp_packet(tcp_sport=111)
    match = parse.packet_to_flow_match(pkt_matchtSrc)
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

    return (pkt_matchtSrc,match)  

def match_tcp_dst(self,of_ports,priority=0):
    #Generate Match_Tcp_Dst

        #Create a simple tcp packet and generate match on tcp destination port flow
    pkt_Matchtdst = simple_tcp_packet(tcp_dport=112)
    match = parse.packet_to_flow_match(pkt_matchtdst)
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

    return (pkt_matchtdst,match)        





def match_ethernet_type(self,of_ports,priority=0):
    #Generate a Match_Ethernet_Type flow

    #Create a simple tcp packet and generate match on ethernet type flow
    pkt_matchtype = simple_eth_packet(dl_type=0x88cc)
    match = parse.packet_to_flow_match(pkt_matchtype)
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

    return (pkt_matchtype,match)

   
   
def strict_modify_flow_action(self,egress_port,match,priority=0):
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

def modify_flow_action(self,of_ports,match,priority=0):
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

    if priority != 0 :
        msg8.priority = priority

    # Send the flow with action A'
    rv = self.controller.message_send (msg8)
    self.assertTrue(rv != -1, "Error installing flow mod")
    self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

def enqueue(self,ingress_port,egress_port,egress_queue_id):
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



def verify_tablestats(self,expect_lookup=0,expect_match=0,expect_active=0):

    stat_req = message.table_stats_request()

    all_packets_lookedup = 0
    all_packets_matched = 0
    all_entries_active = 0 
    lookedup = 0 
    matched = 0 
    active = 0
        
    for i in range(0,60):

        logging.info("Sending stats request")
        # TODO: move REPLY_MORE handling to controller.transact?
        response, pkt = self.controller.transact(stat_req,
                                                     timeout=5)
        self.assertTrue(response is not None,"No response to stats request")

        for item in response.stats:
            lookedup += item.lookup_count
            matched += item.matched_count
            active += item.active_count

            logging.info("Packets Looked up " + str(lookedup) + " packets")
            if expect_lookup != 0 :
                if lookedup == expect_lookup:
                    all_packets_lookedup = 1
            
            logging.info("Packets matched " + str(matched) + "packets")
            if expect_match != 0 :
                if matched == expect_match:
                    all_packets_matched = 1

            logging.info("Active flow entries" + str(active) + "flows")
            if active != 0 :
                if active == expect_active:
                    all_entries_active = 1

        if all_packets_lookedup == 1 and expect_lookup!= 0 :
            break
        if all_packets_matched== 1 and expect_match !=0 :
            break
        if all_entries_active ==1 and expect_active != 0 :
            break 
        
        sleep(1)

    if expect_lookup != 0 :
        self.assertTrue(all_packets_matched, "lookup counter is not incremented properly")
    if expect_match != 0 :
        self.assertTrue(all_packets_matched, "matched counter is not incremented properly")
    if expect_active != 0 :
        self.assertTrue(all_entries_active, "active counter is not incremented properly")


def verify_flowstats(self,match,byte_count=0,packet_count=0):
    # Verify flow counters : byte_count and packet_count

    stat_req = message.flow_stats_request()
    stat_req.match = match
    stat_req.table_id = 0xff
    stat_req.out_port = ofp.OFPP_NONE

    all_packets_rx = 0
    all_bytes_rx = 0
    packet_counter = 0
    byte_counter = 0 
        
    for i in range(0,60):
        logging.info("Sending stats request")
        # TODO: move REPLY_MORE handling to controller.transact?
        response, pkt = self.controller.transact(stat_req,
                                                     timeout=5)
        self.assertTrue(response is not None,"No response to stats request")

        for item in response.stats:
            packet_counter += item.packet_count
            byte_counter += item.byte_count

            logging.info("Recieved" + str(item.packet_count) + " packets")
            if packet_count != 0 :
                if packet_count == packet_counter:
                    all_packets_rx = 1
            
            logging.info("Received " + str(item.byte_count) + "bytes")
            if byte_count != 0 :
                if byte_counter == byte_count:
                    all_bytes_rx = 1

        if all_packets_rx == 1 and packet_count != 0 :
            break
        if all_bytes_rx == 1 and byte_count !=0 :
            break 
        sleep(1)

    if packet_count != 0 :
        self.assertTrue(all_packets_rx,"packet_count counter is not incremented correctly")

    if byte_count != 0 :   
        self.assertTrue(all_bytes_rx,"byte_count counter is not incremented correctly")


def verify_portstats(self, port,tx_packets=0,rx_packets=0,rx_byte=0,tx_byte=0):

    
    stat_req = message.port_stats_request()
    stat_req.port_no = port
    all_packets_received = 0
    all_packets_sent = 0
    all_bytes_recieved = 0
    all_bytes_sent = 0 
    sentp = recvp = 0
    sentb = recvb = 0
    
    for i in range(0,60):
        logging.info("Sending stats request")
        response, pkt = self.controller.transact(stat_req,
                                                timeout=5)
        self.assertTrue(response is not None, 
                       "No response to stats request")
        self.assertTrue(len(response.stats) == 1,
                       "Did not receive port stats reply")
        for item in response.stats:
            sentp += item.tx_packets
            recvp += item.rx_packets
            sentb += item.tx_bytes
            recvb += item.rx_bytes
            
            logging.info("Sent " + str(sentp) + " packets")
            if tx_packets != 0:
                if item.tx_packets == tx_packets:
                    all_packets_sent = 1
            
            logging.info("Received " + str(recvp) + " packets")
            if rx_packets !=0 :
                if item.rx_packets == rx_packets:
                    all_packets_received = 1

            logging.info("Received " + str(recvb) + "bytes")
            if rx_byte !=0 :
                if item.rx_bytes == rx_byte:
                    all_bytes_received = 1  

            logging.info("Sent" + str(sentb) + "bytes")
            if tx_byte !=0 :
                if item.tx_bytes == tx_byte:
                    all_bytes_sent = 1  
                    
        if rx_packets !=0  and all_packets_received == 1:
            break
        if tx_packets !=0 and all_packets_sent == 1:
            break 
        if rx_byte !=0  and all_bytes_received == 1:
            break
        if tx_byte !=0 and all_bytes_sent == 1:
            break
        
        sleep(1)

    if (rx_packets !=0):
        self.assertTrue(all_packets_received == 1 ,"rx_packets counter is not incremented correctly")
    if (tx_packets !=0):
        self.assertTrue(all_packets_sent == 1,"tx_packets counter is not incremented correctly")
    if (rx_byte !=0):
        self.assertTrue(all_bytes_received == 1 ,"rx_bytes counter is not incremented correctly")
    if (tx_byte !=0):
        self.assertTrue(all_bytes_sent == 1,"tx_bytes counter is not incremented correctly")



############################## Various delete commands #############################################################################################

def strict_delete(self,match,priority=0):
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



def nonstrict_delete(self,match,priority=0):
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

##############################################################################################################################################################

