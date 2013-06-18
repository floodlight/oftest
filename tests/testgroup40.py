"""These tests fall under Conformance Test-Suite (OF-SWITCH-1.0.0 TestCases).
    Refer Documentation -- Detailed testing methodology 
    <Some of test-cases are directly taken from oftest> """

"Test Suite 3 --> Detailed Controller to switch messages"

import logging

import unittest
import random

from oftest import config
import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action
import oftest.parse as parse
import oftest.base_tests as base_tests

from oftest.oflog import *
from oftest.testutils import *
from time import sleep
from FuncUtils import *

class Grp40No10(base_tests.SimpleDataPlane):
    
    """Verify that if overlap check flag is set in the flow entry and an overlapping flow is inserted then an error 
        is generated and switch refuses flow entry"""
    
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp40No10 Overlap_Checking test")
       
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear Switch State
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Installing an all wildcarded flow")
        

        #Insert a flow F with wildcarded all fields
        (pkt,match) = wildcard_all(self,of_ports)

        #Verify flow is active  
        #verify_tablestats(self,expect_active=1)
        
        # Build a overlapping flow F'-- Wildcard All except ingress with check overlap bit set
        logging.info("Installing a overlapping flow with check_overlap bit set")
        pkt_matchingress = simple_tcp_packet()
        match3 = parse.packet_to_flow_match(pkt_matchingress)
        self.assertTrue(match3 is not None, "Could not generate flow match from pkt")
        match3.wildcards = ofp.OFPFW_ALL-ofp.OFPFW_IN_PORT
        match3.in_port = of_ports[0]

        msg3 = message.flow_mod()
        msg3.command = ofp.OFPFC_ADD
        msg3.match = match3
        msg3.flags |= ofp.OFPFF_CHECK_OVERLAP
        msg3.cookie = random.randint(0,9007199254740992)
        msg3.buffer_id = 0xffffffff
       
        act3 = action.action_output()
        act3.port = of_ports[1]
        self.assertTrue(msg3.actions.add(act3), "could not add action")
        rv = self.controller.message_send(msg3)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        # Verify Flow does not get inserted 
        #verify_tablestats(self,expect_active=1)

        #Verify OFPET_FLOW_MOD_FAILED/OFPFMFC_OVERLAP error is recieved on the control plane
        logging.info("waiting for the switch to respond with an error")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=5)
        self.assertTrue(response is not None, 
                               'Switch did not reply with error message') 
        self.assertTrue(response.type==ofp.OFPET_FLOW_MOD_FAILED, 
                               'Error message type is not flow mod failed ') 
        self.assertTrue(response.code==ofp.OFPFMFC_OVERLAP, 
                               'Error Message code is not overlap')
        logging.info("Flow_mod error received")

class Grp40No20(base_tests.SimpleDataPlane):

    """Verify that without overlap check flag set, Grp40No20overlapping flows can be created."""  
    
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp40No20 No_Overlap_Checking test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear Switch State
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Installing an all wildcarded flow") 
        

        #Build a flow F with wildcarded all fields.
        (pkt,match) = wildcard_all(self,of_ports)
        
        #Verify flow is active  
        #verify_tablestats(self,expect_active=1)
        
        # Build a overlapping flow F' without check overlap bit set.
        logging.info("Installing an overlapping flow with check_overlap bit unset")
        wildcard_all_except_ingress(self,of_ports)

        rv=all_stats_get(self)
        print rv["flows"]
        self.assertTrue(rv["flows"]==2, "Could not Install overlapping flows")
        logging.info("Successfully installed two overlapping flows")


class Grp40No30(base_tests.SimpleDataPlane):
    
    """Verify that adding two identical flows overwrites the existing one and clears counters"""

    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp40No30 Identical_Flows test ")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Installing an all wildcarded flow")
        
        
        # Create and add flow-1, check on dataplane it is active.
        (pkt,match) = wildcard_all(self,of_ports)

        # Verify active_entries in table_stats_request =1 
        #verify_tablestats(self,expect_active=1)
        
        # Send Packet (to increment counters like byte_count and packet_count)
        logging.info("Sending a matching packet to increase the counters")
        send_packet(self,pkt,of_ports[0],of_ports[1])

        # Verify Flow counters have incremented 
        logging.info("Verifying whether the flow counters have increased")
        stat_req = message.flow_stats_request()
        stat_req.match = match
        stat_req.table_id = 0xff
        stat_req.out_port = ofp.OFPP_NONE
    
        for i in range(0,60):
            logging.info("Sending stats request")
            response, pkt = self.controller.transact(stat_req,
                                                     timeout=5)
            self.assertTrue(response is not None,"No response to stats request")
            packet_counter = 0
            byte_counter = 0 
            sleep(1)
            
            for item in response.stats:
                packet_counter += item.packet_count
                byte_counter += item.byte_count
                logging.info("Recieved" + str(item.packet_count) + " packets")
                logging.info("Received " + str(item.byte_count) + "bytes")
            
            if packet_counter == None : continue
            if byte_counter == None : continue
            break

        if packet_counter == None :
            self.assertEqual(packet_count,item.packet_count,"packet_count counter did not increment")
        if byte_counter == None :   
            self.assertEqual(byte_count,item.byte_count,"byte_count counter did not increment")
        
        #Send Identical flow 
        logging.info("Installing an identical flow")
        (pkt1,match1) = wildcard_all(self,of_ports)

        # Verify active_entries in table_stats_request =1 
        #verify_tablestats(self,expect_active=1)

        # Verify Flow counters reset
        logging.info("Verifying whether the flow counter have reset")
        verify_flowstats(self,match,byte_count=0,packet_count=0)

class Grp40No40(base_tests.SimpleProtocol):
    """
    verify whether the switch sends an error message when the flow table is full
    """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp40No490 testcase")
        
        #clearing switch
        rv = delete_all_flows(self.controller)
        self.assertTrue(rv!=-1,"failed to delete all flows")
        rv = delete_all_flows_emer(self.controller)
        self.assertTrue(rv!=-1,"failed to delete all flows")
        self.assertEqual(do_barrier(self.controller),0, "barrier failed")

        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        self.assertTrue(match is not None, "Could not create a Match")
        match.in_port = 3
        flowmod = message.flow_mod()
        flowmod.match=match
        flowmod.match.wildcards = ofp.OFPFW_ALL^ofp.OFPFW_IN_PORT
        flowmod.buffer_id = 0xffffffff
        flowmod.command = ofp.OFPFC_ADD
        act = action.action_output()
        act.port = 2
        self.assertTrue(flowmod.actions.add(act), "Could not add actions")

        i=11
        logging.info("installing flow entries with different priorities")
        while 1:
            flowmod.priority = i
            logging.info("installing a flow number {0}" .format(i-10))
            rv = self.controller.message_send(flowmod)
            self.assertTrue(rv != -1, "Error sending the Flow mod")
            self.assertEqual(do_barrier(self.controller),0, "barrier failed")
                    
            response, raw = self.controller.poll(ofp.OFPT_ERROR, timeout=3)
            try :
                self.assertTrue(response is None, "Got an error message")
            except :
                self.assertTrue(response.type == ofp.OFPET_FLOW_MOD_FAILED, "Expected response type is ofp.OFPET_FLOW_MOD_FAILED got {0}" .format(response.type))
                self.assertTrue(response.code == ofp.OFPFMFC_ALL_TABLES_FULL, "Expected response code is ofp.OFPFMFC_ALL_TABLES_FULL got {0}" .format(response.code))
                logging.info("Installed {0} flows before getting an error" .format(i-11))
                logging.info("Got the expected Error message")
                return 0
            stats = all_stats_get(self)
            self.assertTrue(stats["flows"]==(i-10), "Didnot add the flow entry:Verify the reason")
            i+=1
            
    
            
class Grp40No50(base_tests.SimpleProtocol):
    
    """When the output to switch port action refers to a port that will never be valid ,
    the switch generates an OFPT_ERROR msg , with type field OFPT_BAD_ACTION and code field OFPBAC_BAD_OUT_PORT
    
    Some switches may generate an OFPT_ERROR , with type field FLOW_MOD_FAILED and code permission errors 
    (this is also acceptable)
    """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp40No50 NeverValidPort test")

        # pick a random bad port number
        bad_port=ofp.OFPP_MAX
        pkt=simple_tcp_packet()
        act=action.action_output()   

        #Send flow_mod message
        logging.info("Sending flow_mod message with output action to an invalid port..")   
        request = flow_msg_create(self, pkt, ing_port=1, egr_ports=bad_port)
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1 ,"Unable to send the message")
        count = 0
        # poll for error message
        logging.info("Waiting for OFPT_ERROR message...")
        while True:
            (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=5)
            if not response:  # Timeout
                break
            if not response.type == ofp.OFPET_BAD_ACTION | ofp.OFPET_FLOW_MOD_FAILED:
                logging.info("Error type is not as expected")
                break
            if not response.code == ofp.OFPPMFC_BAD_PORT | ofp.OFPFMFC_EPERM:
                logging.info("Error field code is not as expected")
                break
            if not config["relax"]:  # Only one attempt to match
                break
            count += 1
            if count > 10:   # Too many tries
                break
        self.assertTrue(count<10,"Did not receive any error message")
        logging.info("Received the expected OFPT_ERROR message")


class Grp40No70(base_tests.SimpleProtocol): 

    """Timeout values are not allowed for emergency flows"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp40No80 Emergency_Flow_Timeout test")
        
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Installing an emergency flow with timeout values")
        
        
        #Insert an emergency flow 
        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        match.in_port = of_ports[0]
        request = message.flow_mod()
        request.match = match
        request.command = ofp.OFPFC_ADD
        request.flags = request.flags | ofp.OFPFF_EMERG
        request.hard_timeout =9
        request.idle_timeout =9
        
        act = action.action_output()
        act.port = of_ports[1]
        request.actions.add(act)
       
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Flow addition did not fail.")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        #Verify OFPET_FLOW_MOD_FAILED/BAD_EMER_TIMEOUT error is recieved on the control plane
        logging.info("waiting for an OFPR_ERROR message")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=5)
        self.assertTrue(response is not None, 
                               'Switch did not reply with error message') 
        self.assertTrue(response.type==ofp.OFPET_FLOW_MOD_FAILED, 
                               'Error message type is not flow mod failed ') 
        self.assertTrue(response.code==ofp.OFPFMFC_BAD_EMERG_TIMEOUT, 
                               'Error Message code is not bad emergency timeout, please verify if the switch supports emergency mode')
        logging.info("Recieved the expected OFPT_ERROR message")

class Grp40No80(base_tests.SimpleDataPlane):

    """If a modify does not match an existing flow, the flow gets added """
    
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp40No90 Missing_Modify_Add test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear Switch State
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        #Generate a flow-mod,command OFPC_MODIFY 
        logging.info("Sending a flow_mod message to the switch")
        request = message.flow_mod()
        request.command = ofp.OFPFC_MODIFY
        request.match.wildcards = ofp.OFPFW_ALL-ofp.OFPFW_IN_PORT
        request.match.in_port = of_ports[0]
        request.cookie = random.randint(0,9007199254740992)
        request.buffer_id = 0xffffffff
        act3 = action.action_output()
        act3.port = of_ports[1]
        self.assertTrue(request.actions.add(act3), "could not add action")

        rv = self.controller.message_send(request)
        logging.info("expecting the fow_mod to add a flow in the absence of a matching flow entry")
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed") 

        logging.info("Verifying whether the flow_mod message has added a flow")
        
        rv=all_stats_get(self)
        self.assertTrue(rv["flows"]==1,"Flow_mod message did not install the flow in the absence of a matching flow entry")


class Grp40No90(base_tests.SimpleDataPlane):

    """A modified flow preserves counters"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp40No90 Modify_Action test ")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Installing a flow")
           
        #Create and add flow-1 Match on all, except one wildcarded (src adddress).Action A , output to of_port[1]
        (pkt,match) = match_all_except_source_address(self,of_ports)

        #Send Packet matching the flow thus incrementing counters like packet_count,byte_count
        logging.info("Sending a matching packet to increment the flow counters")
        self.dataplane.send(of_ports[0], str(pkt))
        
	    #Verify flow counters
        logging.info("Verifying whether the flow counters have been modified")
        verify_flowstats(self,match,packet_count=1)

        #Modify flow- 1 
        logging.info("Sending a flow_mod message")
        modify_flow_action(self,of_ports,match)
        
        # Send Packet matching the flow-1 i.e ingress_port=port[0] and verify it is recieved on corret dataplane port i.e port[2]
        logging.info("Verifying whether the modified action is being implemented")
        self.dataplane.send(of_ports[0],str(pkt))
        
        #Verify flow counters are preserved
        logging.info("Verifying if the flow counters have been preserved")
        verify_flowstats(self,match,packet_count=2)

class Grp40No100(base_tests.SimpleDataPlane):

    """Strict Modify Flow also changes action preserves counters"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp40No100 Strict_Modify_Action test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        sleep(2)
        logging.info("Installing a Flow")
        
        #Create and add flow-1 Match on all, except one wildcarded (src adddress).Action A
        (pkt,match) = match_all_except_source_address(self,of_ports,priority=100)
        
        #Create and add flow-2 , Match on ingress_port only, Action A
        logging.info("Installing another flow")
        (pkt1,match1) = wildcard_all_except_ingress(self,of_ports,priority=10)
        
        # Verify both the flows are active
        #verify_tablestats(self,expect_active=2)

        #Send a packet matching the flows, thus incrementing flow-counters (packet matches the flow F-1 with higher priority)
        logging.info("Sending a packet  to increase the packet counter")
        self.dataplane.send(of_ports[0],str(pkt))

        # Verify flow counters of the flow-1
        logging.info("Verfiying the flow counter value")
        verify_flowstats(self,match,packet_count=1)

        # Strict-Modify flow- 1 
        logging.info("Sending a Strict_flow_mod message to modify the action")
        strict_modify_flow_action(self,of_ports[2],match,priority=100)
        
        # Send Packet matching the flow-1 i.e ingress_port=port[0] and verify it is recieved on corret dataplane port i.e port[2]
        #send_packet(self,pkt,of_ports[0],of_ports[2])
        
        # Verify flow counters are preserved
        logging.info("Verifying counters are preserved")
        verify_flowstats(self,match,packet_count=1)


class Grp40No110(base_tests.SimpleDataPlane):
    
    """Request deletion of non-existing flow"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Delete_NonExisting_Flow Grp40No120 test begins")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Deleting a non-existing flow")
        

        # Issue a delete command 
        msg = message.flow_mod()
        msg.match.wildcards = ofp.OFPFW_ALL
        msg.out_port = ofp.OFPP_NONE
        msg.command = ofp.OFPFC_DELETE
        msg.buffer_id = 0xffffffff
        rv=self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Flow deletion message could not be sent.")
        # Verify no message or error is generated by polling the the control plane
        logging.info("Verifying the Controller doesnt receive any ERROR message")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=2)
        self.assertTrue(response is None, 
                        'Recieved Error for deleting non-exiting flow ')


        
class Grp40No120(base_tests.SimpleDataPlane):
    
    """Check deletion of flows happens and generates messages as configured.
    If Send Flow removed message Flag is set in the flow entry, the flow deletion of that respective flow should generate the flow removed message, 
    vice versa also exists """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp40No130 Send_Flow_Rem test ")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear swicth state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Installing flows F1 without send_flow_removed_message flag set ")

        # Insert flow-1 with F without OFPFF_SEND_FLOW_REM flag set.
        (pkt,match) = wildcard_all_except_ingress(self,of_ports)

        # Verify flow is inserted 
        #verify_tablestats(self,expect_active=1)

        #Delete the flow-1
        logging.info("Deleting the flow inserted")
        nonstrict_delete(self,match,priority=0)

        # Verify no flow removed message is generated for the FLOW-1
        logging.info("Verifying the switch does not generate any FLOW_REMOVED messages")
        (response1, pkt1) = self.controller.poll(exp_msg=ofp.OFPT_FLOW_REMOVED,
                                               timeout=2)
        self.assertTrue(response1 is None, 
                        'Received flow removed message for the flow with flow_rem flag not set')
        
        # Insert another flow F' with OFPFF_SEND_FLOW_REM flag set.
        msg9 = message.flow_mod()
        msg9.match.wildcards = ofp.OFPFW_ALL
        msg9.cookie = random.randint(0,9007199254740992)
        msg9.buffer_id = 0xffffffff
        msg9.idle_timeout = 1
        msg9.flags |= ofp.OFPFF_SEND_FLOW_REM
        logging.info("Installing flolw F2 with send_flow_removed_message set")
        rv1 = self.controller.message_send(msg9)
        self.assertTrue(rv1 != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        # Delete the flow-2
        rc2 = delete_all_flows(self.controller)
        self.assertEqual(rc2, 0, "Failed to delete all flows")

        # Verify flow removed message is generated for the FLOW-2
        logging.info("Verifying the switch generates the Flow removed message")
        (response2, pkt2) = self.controller.poll(exp_msg=ofp.OFPT_FLOW_REMOVED,
                                               timeout=2)
        self.assertTrue(response2 is not None, 
                        'Did not receive flow removed message for this flow')


class Grp40No130(base_tests.SimpleProtocol):

    """Delete emergency flow and verify no message is generated.An emergency flow deletion will not generate flow-removed messages even if 
    Send Flow removed message flag was set during the emergency flow entry"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp40No130 Delete_Emer_Flow")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        
        #Clear switch state        
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Installing an emergency flow with send_flow_removed flag set")
        
        
        # Insert a flow with emergency bit set.
        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        match.in_port = of_ports[0]
        request = message.flow_mod()
        request.match = match
        request.command = ofp.OFPFC_ADD
        request.flags = request.flags|ofp.OFPFF_EMERG
        act = action.action_output()
        act.port = of_ports[1]
        request.actions.add(act)

        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Emergency Flow addition failed.")
        
        # Delete the emergency flow
        logging.info("Deleting the emergency flow installed")
        nonstrict_delete_emer(self,match)
        nonstrict_delete(self,match)
	logging.info("verifying the switch does not send a flow removed message")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_FLOW_REMOVED ,
                                               timeout=2)
        self.assertTrue(response is None, 
                        'Recevied a Flow removed message')


class Grp40No140(base_tests.SimpleDataPlane):

    """Delete and verify strict and non-strict behaviors
    This test compares the behavior of delete strict and non-strict"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Grp40No140 test begins")
        
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")
        
        #####Grp40No140#####
        logging.info("Installing an exact match flow")
             
        
        #Insert F with an exact Match 
        (pkt,match) = exact_match(self,of_ports)  
        #verify_tablestats(self,expect_active=1)

        #Issue Strict Delete Command , verify F gets deleted.
        logging.info("sending a strict delete message")
        strict_delete(self,match)
        rv=all_stats_get(self)
        self.assertTrue(rv["flows"]==0,"could not delete the flow flows")
        #verify_tablestats(self,expect_active=0)
	#####Grp40No160#####
        logging.info("Inserting two overlapping flows")
        
        #Insert Flow T with match on all , except one wildcarded ( say src adddress ). 
        (pkt,match) = match_all_except_source_address(self,of_ports)

        #Insert another flow T' with match on ingress_port , wildcarded rest.  
        (pkt1,match1) = wildcard_all_except_ingress(self,of_ports)
        #verify_tablestats(self,expect_active=2)

        rv=all_stats_get(self)
        self.assertTrue(rv["flows"]==2,"could not install two overlapping flows")

        #Issue Strict Delete matching on ingress_port. Verify only T' gets deleted
        logging.info("Sending a Strict delete message")
        strict_delete(self,match1)
        #verify_tablestats(self,expect_active=1) 
        rv=all_stats_get(self)
        self.assertTrue(rv["flows"]==1,"The switch did not perform the required action")
 
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")
        
	#####Grp40No150#####
        logging.info("Installing two overlapping flows")
        
        #Insert T and T' again . 
        (pkt,match) = match_all_except_source_address(self,of_ports)
        (pkt1,match1) = wildcard_all_except_ingress(self,of_ports)
        #verify_tablestats(self,expect_active=2)

        rv=all_stats_get(self)
        self.assertTrue(rv["flows"]==2,"Could not install 2 overlapping flows")
        #Issue Non-strict Delete with match on ingress_port.Verify T+T' gets deleted . 

        logging.info("Sending a non_strict delete message")
        nonstrict_delete(self,match1)

        #verify_tablestats(self,expect_active=0)
        rv=all_stats_get(self)
        self.assertTrue(rv["flows"]==0, "The non_strict_delete message did not delete all the flows")


	#####Grp40No170#####
        logging.info("Inserting three overlapping flows with different priorities")
          
  
        #Insert T , add Priority P (say 100 ) 
        (pkt,match) = match_all_except_source_address(self,of_ports,priority=100)

        #Insert T' add priority (200).
        (pkt1,match1) = wildcard_all_except_ingress(self,of_ports,priority=200)
        
        #Insert T' again add priority 300 --> T" . 
        (pkt2,match2) = wildcard_all_except_ingress(self,of_ports,priority=300)
        #verify_tablestats(self,expect_active=3)

        #Issue Non-Strict Delete and verify all getting deleted
        logging.info("Sending a non_strict_delete message")
        nonstrict_delete(self,match1,priority=200)
        #verify_tablestats(self,expect_active=0)
        logging.info("Verifying all the flow entries have been deleted")
        rv=all_stats_get(self)
        self.assertTrue(rv["flows"]==0,"Non strict delete message did not delete all the flo entries")

        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")
        
        #####Grp40No180#####
        logging.info("Inserting three overlapping flows with different priorities")
        #Issue Strict-Delete and verify only T'' gets deleted. 
        (pkt,match) = match_all_except_source_address(self,of_ports,priority=100)
        (pkt1,match1) = wildcard_all_except_ingress(self,of_ports,priority=200)
        (pkt2,match2) = wildcard_all_except_ingress(self,of_ports,priority=300)
        
        logging.info("Sending a strict delete message")
        strict_delete(self,match1,priority=200)
        #verify_tablestats(self,expect_active=2)
        
        logging.info("Verifying that only the expected flows are deleted")
        rv=all_stats_get(self)
   	self.assertTrue(rv["flows"]==2, "The switch did not perform the required action")
   	
   	
class Grp40No190(base_tests.SimpleDataPlane):

    """Delete flows filtered by action outport.If the out_port field in the delete command contains a value other than OFPP_NONE,
    it introduces a constraint when matching. This constraint is that the rule must contain an output action directed at that port."""

    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Outport1 Grp40No160 test begins")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Inserting a flow with output action --> of_port[1]")
        
        
        #Build and send Flow-1 with action output to of_port[1]
        (pkt,match) = wildcard_all_except_ingress(self,of_ports)

        # Verify active_entries in table_stats_request = 1
        #verify_tablestats(self,expect_active=1)
	rv=all_stats_get(self)
	self.assertTrue(rv["flows"]==1,"Could not install the flow entry")
        #Send delete command matching the flow-1 but with contraint out_port = of_port[2]
        msg7 = message.flow_mod()
        msg7.out_port = of_ports[2]
        msg7.command = ofp.OFPFC_DELETE
        msg7.buffer_id = 0xffffffff
        msg7.match = match
	logging.info("Sendind a Delete flow_mod with output constraint output = of_port[2]")
        rv = self.controller.message_send(msg7)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        # Verify flow will not get deleted, active_entries in table_stats_request = 1
        #verify_tablestats(self,expect_active=1)

        logging.info("Sendind a delete flow_mod output_port=of_port[1]")
        

        #Send Delete command with contraint out_port = of_ports[1]
        msg7 = message.flow_mod()
        msg7.out_port = of_ports[1]
        msg7.command = ofp.OFPFC_DELETE
        msg7.buffer_id = 0xffffffff
        msg7.match = match

        rv = self.controller.message_send(msg7)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
        logging.info("Expecting switch to delete the flow")
        #Verify flow gets deleted.
        #verify_tablestats(self,expect_active=0)
	rv=all_stats_get(self)
	self.assertTrue(rv["flows"]==0,"Switch did not delete the flow")



class Grp40No200(base_tests.SimpleDataPlane):

    """Add, modify flows with outport set. This field is ignored by ADD, MODIFY, and MODIFY STRICT messages."""

    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp40No170 Outport2 test ")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Adding and modifying flow with out_port fields set")
        logging.info("Expecting switch to ignore out_port")

        # Create and add flow-1,Action A ,output to port of_port[1], out_port set to of_ports[2]
        (pkt,match) = wildcard_all_except_ingress(self,of_ports)

        # Verify flow is active
        #verify_tablestats(self,expect_active=1)
                
        # Send Packet matching the flow
        send_packet(self,pkt,of_ports[0],of_ports[1])
        
        # Insert Flow-Modify matching flow F-1 ,action A', output to port[2], out_port set to port[3]
        modify_flow_action(self,of_ports,match)

        # Again verify active_entries in table_stats_request =1 
        #verify_tablestats(self,expect_active=1)

        #Verify action is modified
        send_packet(self,pkt,of_ports[0],of_ports[2])



class Grp40No220(base_tests.SimpleDataPlane):

    """ Verify that idle timeout is implemented"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp40No180 Idle_Timeout test ")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Inserting flow entry with idle_timeout set. Also send_flow_removed_message flag set")

        #Insert a flow entry with idle_timeout=2.Send_Flow_Rem flag set
        msg9 = message.flow_mod()
        msg9.match.wildcards = ofp.OFPFW_ALL
        msg9.cookie = random.randint(0,9007199254740992)
        msg9.buffer_id = 0xffffffff
        msg9.idle_timeout = 2
        msg9.flags |= ofp.OFPFF_SEND_FLOW_REM
        rv1 = self.controller.message_send(msg9)
        self.assertTrue(rv1 != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        # Verify flow removed message is recieved.
        logging.info("Verifying whether OFPT_FLOW_REMOVED message is received") 
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_FLOW_REMOVED,
                                               timeout=5)
        self.assertTrue(response is not None, 
                        'Did not receive flow removed message ')
        self.assertEqual(ofp.OFPRR_IDLE_TIMEOUT, response.reason,
                         'Flow table entry removal reason is not idle_timeout')
        self.assertEqual(2, response.duration_sec,
                         'Flow was not alive for 1 sec')





class Grp40No230(base_tests.SimpleDataPlane):

    """ Verify that hard timeout is implemented """

    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Hard_Timeout test ")
        
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Inserting flow entry with hard_timeout set. Also send_flow_removed_message flag set")
        

        sleep(2)

        # Insert a flow entry with hardtimeout=1 and send_flow_removed flag set
        msg9 = message.flow_mod()
        msg9.match.wildcards = ofp.OFPFW_ALL
        msg9.cookie = random.randint(0,9007199254740992)
        msg9.buffer_id = 0xffffffff
        msg9.hard_timeout = 3
        msg9.flags |= ofp.OFPFF_SEND_FLOW_REM
        rv1 = self.controller.message_send(msg9)
        self.assertTrue(rv1 != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        #Verify flow gets inserted
        #verify_tablestats(self,expect_active=1)

        # Verify flow removed message is recieved.
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_FLOW_REMOVED,
                                               timeout=7)
        logging.info("Verifying whether OFPT_FLOW_REMOVED message is received")
        self.assertTrue(response is not None, 
                        'Did not receive flow removed message ')
        self.assertEqual(ofp.OFPRR_HARD_TIMEOUT, response.reason,
                         'Flow table entry removal reason is not hard_timeout')
        self.assertTrue(2<=response.duration_sec and response.duration_sec<=4,
                         'Flow was not alive for 3 sec')


class Grp40No210(base_tests.SimpleDataPlane):
  
    """Verify that Flow removed messages are generated as expected
    Flow removed messages being generated when flag is set, is already tested in the above tests 
    So here, we test the vice-versa condition"""

    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Flow_Timeout test ")
        
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Inserting flow entry with hard_timeout set and send_flow_removed_message flag not set")
	   
        # Insert a flow with hard_timeout = 1 but no Send_Flow_Rem flag set
        pkt = simple_tcp_packet()
        match3 = parse.packet_to_flow_match(pkt)
        self.assertTrue(match3 is not None, "Could not generate flow match from pkt")
        match3.wildcards = ofp.OFPFW_ALL-ofp.OFPFW_IN_PORT
        match3.in_port = of_ports[0]
        msg3 = message.flow_mod()
        msg3.out_port = of_ports[2] # ignored by flow add,flow modify 
        msg3.command = ofp.OFPFC_ADD
        msg3.cookie = random.randint(0,9007199254740992)
        msg3.buffer_id = 0xffffffff
        msg3.hard_timeout = 1
        msg3.buffer_id = 0xffffffff
        msg3.match = match3
        act3 = action.action_output()
        act3.port = of_ports[1]
        self.assertTrue(msg3.actions.add(act3), "could not add action")

        rv = self.controller.message_send(msg3)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        #Verify no flow removed message is generated
        logging.info("Verifying that there is no OFPT_FLOW_REMOVED message received")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_FLOW_REMOVED,
                                               timeout=3)
        self.assertTrue(response is None, 
                        'Recieved flow removed message ')

        # Verify no entries in the table
        #verify_tablestats(self,expect_active=0)
        logging.info("Verifying if the flow was removed after the time out")
        rv=all_stats_get(self)
        self.assertTrue(rv["flows"]==0, "Flows were not deleted even after the flow timedout")
