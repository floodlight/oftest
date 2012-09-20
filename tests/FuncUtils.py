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
import basic
from testutils import *
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


###########################   Verify Stats Functions   ###########################################################################################

def Verify_TableStats(self,active_entries=0,):
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


def Verify_FlowStats(self,match,byte_count=0,packet_count=0):
# Verify flow counters : byte_count and packet_count

        stat_req = message.flow_stats_request()
        stat_req.match = match
        stat_req.table_id = 0xff
        stat_req.out_port = ofp.OFPP_NONE
        test_timeout = 10
        all_packets_received = 0
        for i in range(0,test_timeout):
            
            response, pkt = self.controller.transact(stat_req,
                                                     timeout=test_timeout)
            self.assertTrue(response is not None, 
                            "No response to stats request")
            for obj in response.stats:
                if ( obj.packet_count == packet_count and obj.byte_count == byte_count ) :
                    all_packets_received = 1

            if all_packets_received:
                break
            sleep(1)

        self.assertTrue(all_packets_received,
                        "Flow counters are incorrect")


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
