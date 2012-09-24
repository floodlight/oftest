"""These tests fall under Conformance Test-Suite (OF-SWITCH-1.0.0 TestCases).
    Refer Documentation -- Detailed testing methodology 
    <Some of test-cases are directly taken from oftest> """

"Test Suite 3 --> Detailed Controller to switch messages"

import logging

import unittest
import random

import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action
import oftest.parse as parse
import basic

from testutils import *
from time import sleep
from FuncUtils import *

cs_port_map = None
cs_logger = None
cs_config = None

def test_set_init(config):
   

    basic.test_set_init(config)

    global cs_port_map
    global cs_logger
    global cs_config

    cs_logger = logging.getLogger("Detailed controller to switch messages")
    cs_logger.info("Initializing test set")
    cs_port_map = config["port_map"]
    cs_config = config


class Overlap_Checking(basic.SimpleDataPlane):
    
    """Verify that if overlap check flag is set in the flow entry and an overlapping flow is inserted then an error 
        is generated and switch refuses flow entry"""
    
    def runTest(self):
        
        cs_logger.info("Running Overlap_Checking test")
       
        of_ports = cs_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear Switch State
        rc = delete_all_flows(self.controller, cs_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        cs_logger.info("Inserting two overlapping flows")
        cs_logger.info("Expecting switch to return an error")

        #Insert a flow F with wildcarded all fields
        (pkt,match) = Wildcard_All(self,of_ports)

        #Verify flow is active  
        Verify_TableStats(self,active_entries=1)
        
        # Build a overlapping flow F'-- Wildcard All except ingress with check overlap bit set
        Pkt_MatchIngress = simple_tcp_packet()
        match3 = parse.packet_to_flow_match(Pkt_MatchIngress)
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
        Verify_TableStats(self,active_entries=1)

        #Verify OFPET_FLOW_MOD_FAILED/OFPFMFC_OVERLAP error is recieved on the control plane
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=5)
        self.assertTrue(response is not None, 
                               'Switch did not reply with error message') 
        self.assertTrue(response.type==ofp.OFPET_FLOW_MOD_FAILED, 
                               'Error message type is not flow mod failed ') 
        self.assertTrue(response.code==ofp.OFPFMFC_OVERLAP, 
                               'Error Message code is not overlap')


class No_Overlap_Checking(basic.SimpleDataPlane):

    """Verify that without overlap check flag set, overlapping flows can be created."""  
    
    def runTest(self):
     
        cs_logger.info("Running No_Overlap_Checking test")

        of_ports = cs_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear Switch State
        rc = delete_all_flows(self.controller, cs_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        cs_logger.info("Inserting two overlapping flows")
        cs_logger.info("Expecting switch to insert the flows without generating errors")

        #Build a flow F with wildcarded all fields.
        (pkt,match) = Wildcard_All(self,of_ports)
        
        #Verify flow is active  
        Verify_TableStats(self,active_entries=1)
        
        # Build a overlapping flow F' without check overlap bit set.
        Wildcard_All_Except_Ingress(self,of_ports)

        # Verify Flow gets inserted 
        Verify_TableStats(self,active_entries=2)


class Identical_Flows(basic.SimpleDataPlane):
    
    """Verify that adding two identical flows overwrites the existing one and clears counters"""

    def runTest(self):
        
        cs_logger.info("Running Identical_Flows test ")

        of_ports = cs_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear switch state
        rc = delete_all_flows(self.controller, cs_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        cs_logger.info("Inserting two identical flows one by one")
        cs_logger.info("Expecting switch to overwrite the first flow and clear the counters associated with it ")
        
        # Create and add flow-1, check on dataplane it is active.
        (pkt,match) = Wildcard_All(self,of_ports)

        # Verify active_entries in table_stats_request =1 
        Verify_TableStats(self,active_entries=1)
        
        # Send Packet (to increment counters like byte_count and packet_count)
        SendPacket(self,pkt,of_ports[0],of_ports[1])

        # Verify Flow counters have incremented
        Verify_FlowStats(self,match,byte_count=len(str(pkt)),packet_count=1)
        
        #Send Identical flow 
        (pkt1,match1) = Wildcard_All(self,of_ports)

        # Verify active_entries in table_stats_request =1 
        Verify_TableStats(self,active_entries=1)

        # Verify Flow counters reset
        Verify_FlowStats(self,match,byte_count=0,packet_count=0)

   
class Emer_Flow_With_Timeout(basic.SimpleProtocol): 

    """Timeout values are not allowed for emergency flows"""

    def runTest(self):

        cs_logger.info("Running Emergency flow with timeout values test")
        
        of_ports = cs_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear switch state
        rc = delete_all_flows(self.controller, cs_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        cs_logger.info("Inserting an emergency flow with timeout values")
        cs_logger.info("Expecting switch to generate error ")
        
        #Insert an emergency flow 
        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        match.in_port = of_ports[0]
        
        request = message.flow_mod()
        request.match = match
        request.command = ofp.OFPFC_ADD
        request.flags = request.flags|ofp.OFPFF_EMERG
        request.hard_timeout =9
        request.idle_timeout =9
        
        act = action.action_output()
        act.port = of_ports[1]
        
        request.actions.add(act)
        cs_logger.info("Inserting flow")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Flow addition did not fail.")

        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        #Verify OFPET_FLOW_MOD_FAILED/OFPFMFC_OVERLAP error is recieved on the control plane
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=5)
        self.assertTrue(response is not None, 
                               'Switch did not reply with error message') 
        self.assertTrue(response.type==ofp.OFPET_FLOW_MOD_FAILED, 
                               'Error message type is not flow mod failed ') 
        self.assertTrue(response.code==ofp.OFPFMFC_BAD_EMERG_TIMEOUT, 
                               'Error Message code is not bad emergency timeout')


class Missing_Modify_Add(basic.SimpleDataPlane):

    """If a modify does not match an existing flow, the flow gets added """
    
    def runTest(self):
        
        cs_logger.info("Running Missing_Modify_Add test")

        of_ports = cs_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        cs_logger.info("Inserting a flow-modify that does not match an existing flow")
        cs_logger.info("Expecting flow to get added i.e OFPFC_MODIFY command should be taken as OFPFC_ADD ")

        #Clear Switch State
        rc = delete_all_flows(self.controller, cs_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        #Generate a flow-mod,command OFPC_MODIFY 

        request = message.flow_mod()
        request.command = ofp.OFPFC_MODIFY
        request.match.wildcards = ofp.OFPFW_ALL-ofp.OFPFW_IN_PORT
        request.match.in_port = of_ports[0]
        request.cookie = random.randint(0,9007199254740992)
        request.buffer_id = 0xffffffff
        act3 = action.action_output()
        act3.port = of_ports[1]
        self.assertTrue(request.actions.add(act3), "could not add action")

        cs_logger.info("Inserting flow")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed") 

        #Verify the flow gets added i.e. active_count= 1
        Verify_TableStats(self,active_entries=1)


class Modify_Action(basic.SimpleDataPlane):

    """A modified flow preserves counters"""
    
    def runTest(self):
        
        cs_logger.info("Running Modify_Action test ")

        of_ports = cs_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear switch state
        rc = delete_all_flows(self.controller, cs_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        cs_logger.info("Inserting a Flow and incrementing flow counters. Modifying the flow action")
        cs_logger.info("Expecting the flow action to be modified , but the flow-counters should be preserved")
           
        #Create and add flow-1 Match on all, except one wildcarded (src adddress).Action A , output to of_port[1]
        (pkt,match) = Match_All_Except_Source_Address(self,of_ports)

        #Send Packet matching the flow thus incrementing counters like packet_count,byte_count
        SendPacket(self,pkt,of_ports[0],of_ports[1])

        #Verify flow counters
        Verify_FlowStats(self,match,byte_count=len(str(pkt)),packet_count=1)

        #Modify flow- 1 
        Modify_Flow_Action(self,of_ports,match)
        
        # Send Packet matching the flow-1 i.e ingress_port=port[0] and verify it is recieved on corret dataplane port i.e port[2]
        SendPacket(self,pkt,of_ports[0],of_ports[2])
        
        #Verify flow counters are preserved
        Verify_FlowStats(self,match,byte_count=(2*len(str(pkt))),packet_count=2)


class Strict_Modify_Action(basic.SimpleDataPlane):

    """Strict Modify Flow also changes action preserves counters"""

    def runTest(self):
        
        cs_logger.info("Running Strict_Modify_Action test")

        of_ports = cs_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear switch state
        rc = delete_all_flows(self.controller, cs_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        cs_logger.info("Inserting Flows and incrementing flow counters. Strict Modify the flow action ")
        cs_logger.info("Expecting the flow action to be modified , but the flow-counters should be preserved")
        
        #Create and add flow-1 Match on all, except one wildcarded (src adddress).Action A
        (pkt,match) = Match_All_Except_Source_Address(self,of_ports,priority=100)
        
        #Create and add flow-2 , Match on ingress_port only, Action A
        (pkt1,match1) = Wildcard_All_Except_Ingress(self,of_ports,priority=10)
        
        # Verify both the flows are active
        Verify_TableStats(self,active_entries=2)

        #Send a packet matching the flows, thus incrementing flow-counters (packet matches the flow F-1 with higher priority)
        SendPacket(self,pkt,of_ports[0],of_ports[1])

        # Verify flow counters of the flow-1
        Verify_FlowStats(self,match,byte_count=len(str(pkt)),packet_count=1)

        # Strict-Modify flow- 1 
        Strict_Modify_Flow_Action(self,of_ports[2],match,priority=100)
        
        # Send Packet matching the flow-1 i.e ingress_port=port[0] and verify it is recieved on corret dataplane port i.e port[2]
        SendPacket(self,pkt,of_ports[0],of_ports[2])
        
        # Verify flow counters are preserved
        Verify_FlowStats(self,match,byte_count=(2*len(str(pkt))),packet_count=2)


class Delete_NonExisting_Flow(basic.SimpleDataPlane):
    
    """Request deletion of non-existing flow"""
    
    def runTest(self):
        
        cs_logger.info("Delete_NonExisting_Flow test begins")

        of_ports = cs_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear switch state
        rc = delete_all_flows(self.controller, cs_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        cs_logger.info("Deleting a non-existing flow")
        cs_logger.info("Expecting switch to ignore the command , without generating errors")

        # Issue a delete command 
        msg = message.flow_mod()
        msg.match.wildcards = ofp.OFPFW_ALL
        msg.out_port = ofp.OFPP_NONE
        msg.command = ofp.OFPFC_DELETE
        msg.buffer_id = 0xffffffff

        # Verify no message or error is generated by polling the the control plane
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=2)
        self.assertTrue(response is None, 
                        'Recieved Error for deleting non-exiting flow ')


        
class Send_Flow_Rem(basic.SimpleDataPlane):
    
    """Check deletion of flows happens and generates messages as configured.
    If Send Flow removed message Flag is set in the flow entry, the flow deletion of that respective flow should generate the flow removed message, 
    vice versa also exists """

    def runTest(self):

        cs_logger.info("Running Send Flow removed message test begins")

        of_ports = cs_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear swicth state
        rc = delete_all_flows(self.controller, cs_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        cs_logger.info("Inserting flows F1 and F2 without and with send_flow_removed_message flag set ")
        cs_logger.info("Deleting the flows")
        cs_logger.info("Expecting flow removed message only for F2")

        # Insert flow-1 with F without OFPFF_SEND_FLOW_REM flag set.
        (pkt,match) = Wildcard_All_Except_Ingress(self,of_ports)

        # Verify flow is inserted 
        Verify_TableStats(self,active_entries=1)

        #Delete the flow-1
        NonStrict_Delete(self,match,priority=0)

        # Verify no flow removed message is generated for the FLOW-1

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
        rv1 = self.controller.message_send(msg9)
        self.assertTrue(rv1 != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        # Delete the flow-2
        rc2 = delete_all_flows(self.controller, cs_logger)
        self.assertEqual(rc2, 0, "Failed to delete all flows")

        # Verify flow removed message is generated for the FLOW-2

        (response2, pkt2) = self.controller.poll(exp_msg=ofp.OFPT_FLOW_REMOVED,
                                               timeout=2)
        self.assertTrue(response2 is not None, 
                        'Did not receive flow removed message for this flow')


class Delete_Emer_Flow(basic.SimpleProtocol):

    """Delete emergency flow and verify no message is generated.An emergency flow deletion will not generate flow-removed messages even if 
    Send Flow removed message flag was set during the emergency flow entry"""

    def runTest(self):

        cs_logger.info("Running Delete Emergency flow")

        of_ports = cs_port_map.keys()
        of_ports.sort()
        
        #Clear switch state        
        rc = delete_all_flows(self.controller, cs_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        cs_logger.info("Inserting a emergency flow with send_flow_removed flag set")
        cs_logger.info("Expecting no flow_removed_message on the deletion of the emergency flow")
        
        # Insert a flow with emergency bit set.
        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        match.in_port = of_ports[0]
        request = message.flow_mod()
        request.match = match
        request.command = ofp.OFPFC_ADD
        request.flags = request.flags|ofp.OFPFF_EMERG|ofp.OFPFF_SEND_FLOW_REM
        act = action.action_output()
        act.port = of_ports[1]
        request.actions.add(act)

        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Flow addition failed.")
        
        # Delete the emergency flow
        
        NonStrict_Delete(self,match)
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPFF_SEND_FLOW_REM ,
                                               timeout=2)
        self.assertTrue(response is None, 
                        'Test Failed ')


class Delete_Strict_NonStrict(basic.SimpleDataPlane):

    """Delete and verify strict and non-strict behaviors
    This test compares the behavior of delete strict and non-strict"""

    def runTest(self):
        
        cs_logger.info("Delete_Strict_NonStrict test begins")
        
        of_ports = cs_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear switch state
        rc = delete_all_flows(self.controller, cs_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")
        
        cs_logger.info("Inserting a flow with exact match")
        cs_logger.info("Issue Strict Delete command , verify it gets deleted")     
        
        #Insert F with an exact Match 
        (pkt,match) = Exact_Match(self,of_ports)  
        Verify_TableStats(self,active_entries=1)

        #Issue Strict Delete Command , verify F gets deleted.
        Strict_Delete(self,match)
        Verify_TableStats(self,active_entries=0)

        cs_logger.info("Inserting two overlapping flows")
        cs_logger.info("Issue Strict Delete command ")
        cs_logger.info("Expecting only one flow gets deleted , because Strict Delete matches on wildcards as well")     
        
        #Insert Flow T with match on all , except one wildcarded ( say src adddress ). 
        (pkt,match) = Match_All_Except_Source_Address(self,of_ports)

        #Insert another flow T' with match on ingress_port , wildcarded rest.  
        (pkt1,match1) = Wildcard_All_Except_Ingress(self,of_ports)
        Verify_TableStats(self,active_entries=2)

        #Issue Strict Delete matching on ingress_port. Verify only T' gets deleted
        Strict_Delete(self,match1)
        Verify_TableStats(self,active_entries=1) 

        cs_logger.info("Inserting two overlapping flows")
        cs_logger.info("Issue Non-Strict Delete command ")
        cs_logger.info("Expecting both the flow gets deleted , because wildcards are active")    

        #Insert T and T' again . 
        (pkt,match) = Match_All_Except_Source_Address(self,of_ports)
        (pkt1,match1) = Wildcard_All_Except_Ingress(self,of_ports)
        Verify_TableStats(self,active_entries=2)

        #Issue Non-strict Delete with match on ingress_port.Verify T+T' gets deleted . 
        NonStrict_Delete(self,match1)
        Verify_TableStats(self,active_entries=0)

        cs_logger.info("Inserting three overlapping flows with different priorities")
        cs_logger.info("Issue Non-Strict Delete command ")
        cs_logger.info("Expecting all the flows to get deleted")  
  
        #Insert T , add Priority P (say 100 ) 
        (pkt,match) = Match_All_Except_Source_Address(self,of_ports,priority=100)

        #Insert T' add priority (200).
        (pkt1,match1) = Wildcard_All_Except_Ingress(self,of_ports,priority=200)
        
        #Insert T' again add priority 300 --> T" . 
        (pkt2,match2) = Wildcard_All_Except_Ingress(self,of_ports,priority=300)
        Verify_TableStats(self,active_entries=3)

        #Issue Non-Strict Delete and verify all getting deleted
        NonStrict_Delete(self,match1,priority=200)
        Verify_TableStats(self,active_entries=0)

        cs_logger.info("Inserting three overlapping flows with different priorities")
        cs_logger.info("Issue Strict Delete command ")
        cs_logger.info("Expecting only one to get deleted because here priorities & wildcards are being matched")  

        #Issue Strict-Delete and verify only T'' gets deleted. 
        (pkt,match) = Match_All_Except_Source_Address(self,of_ports,priority=100)
        (pkt1,match1) = Wildcard_All_Except_Ingress(self,of_ports,priority=200)
        (pkt2,match2) = Wildcard_All_Except_Ingress(self,of_ports,priority=300)
        Strict_Delete(self,match1,priority=200)
        Verify_TableStats(self,active_entries=2)

        
   
class Delete_With_Outport(basic.SimpleDataPlane):

    """Delete flows filtered by action outport.If the out_port field in the delete command contains a value other than OFPP_NONE,
    it introduces a constraint when matching. This constraint is that the rule must contain an output action directed at that port."""

    def runTest(self):
        
        cs_logger.info("Delete_Filter_Outport test begins")

        of_ports = cs_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear switch state
        rc = delete_all_flows(self.controller, cs_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        cs_logger.info("Inserting a flow with output action --> of_port[1]")
        cs_logger.info("Deleting the flow but with out_port set to of_port[2]")
        cs_logger.info("Expecting switch to filter the delete command")
        
        #Build and send Flow-1 with action output to of_port[1]
        (pkt,match) = Wildcard_All_Except_Ingress(self,of_ports)

        # Verify active_entries in table_stats_request = 1
        Verify_TableStats(self,active_entries=1)

        #Send delete command matching the flow-1 but with contraint out_port = of_port[2]
        msg7 = message.flow_mod()
        msg7.out_port = of_ports[2]
        msg7.command = ofp.OFPFC_DELETE
        msg7.buffer_id = 0xffffffff
        msg7.match = match

        rv = self.controller.message_send(msg7)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        # Verify flow will not get deleted, active_entries in table_stats_request = 1
        Verify_TableStats(self,active_entries=1)

        cs_logger.info("Deleting the flow with out_port set to of_port[1]")
        cs_logger.info("Expecting switch to delete the flow")

        #Send Delete command with contraint out_port = of_ports[1]
        msg7 = message.flow_mod()
        msg7.out_port = of_ports[1]
        msg7.command = ofp.OFPFC_DELETE
        msg7.buffer_id = 0xffffffff
        msg7.match = match

        rv = self.controller.message_send(msg7)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
        
        #Verify flow gets deleted.
        Verify_TableStats(self,active_entries=0)


class Idle_Timeout(basic.SimpleDataPlane):

    """ Verify that idle timeout is implemented"""

    def runTest(self):
        
        cs_logger.info("Running Idle_Timeout test ")

        of_ports = cs_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        rc = delete_all_flows(self.controller, cs_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        cs_logger.info("Inserting flow entry with idle_timeout set. Also send_flow_removed_message flag set")
        cs_logger.info("Expecting the flow entry to delete with given idle_timeout")

        #Insert a flow entry with idle_timeout=1.Send_Flow_Rem flag set
        msg9 = message.flow_mod()
        msg9.match.wildcards = ofp.OFPFW_ALL
        msg9.cookie = random.randint(0,9007199254740992)
        msg9.buffer_id = 0xffffffff
        msg9.idle_timeout = 1
        msg9.flags |= ofp.OFPFF_SEND_FLOW_REM
        rv1 = self.controller.message_send(msg9)
        self.assertTrue(rv1 != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        #Verify flow gets inserted
        Verify_TableStats(self,active_entries=1)
        
        # Verify flow removed message is recieved.
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_FLOW_REMOVED,
                                               timeout=5)
        self.assertTrue(response is not None, 
                        'Did not receive flow removed message ')
        self.assertEqual(ofp.OFPRR_IDLE_TIMEOUT, response.reason,
                         'Flow table entry removal reason is not idle_timeout')
        self.assertEqual(1, response.duration_sec,
                         'Flow was not alive for 1 sec')


class Add_Modify_With_Outport(basic.SimpleDataPlane):

    """Add, modify flows with outport set. This field is ignored by ADD, MODIFY, and MODIFY STRICT messages."""

    def runTest(self):
        
        cs_logger.info("Running Add_Modify_With_Outport ")

        of_ports = cs_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear switch state
        rc = delete_all_flows(self.controller, cs_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        cs_logger.info("Adding and modifying flow with out_port fields set")
        cs_logger.info("Expecting switch to ignore out_port")

        # Create and add flow-1,Action A ,output to port of_port[1], out_port set to of_ports[2]
        (pkt,match) = Wildcard_All_Except_Ingress(self,of_ports)

        # Verify flow is active
        Verify_TableStats(self,active_entries=1)
        
        # Send Packet matching the flow
        SendPacket(self,pkt,of_ports[0],of_ports[1])
        
        # Insert Flow-Modify matching flow F-1 ,action A', output to port[2], out_port set to port[3]
        Modify_Flow_Action(self,of_ports,match)

        # Again verify active_entries in table_stats_request =1 
        Verify_TableStats(self,active_entries=1)

        #Verify action is modified
        SendPacket(self,pkt,of_ports[0],of_ports[2])




class Hard_Timeout(basic.SimpleDataPlane):

    """ Verify that hard timeout is implemented """

    def runTest(self):

        cs_logger.info("Running Idle_Timeout test ")
        
        of_ports = cs_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear switch state
        rc = delete_all_flows(self.controller, cs_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        cs_logger.info("Inserting flow entry with hard_timeout set. Also send_flow_removed_message flag set")
        cs_logger.info("Expecting the flow entry to delete with given hard_timeout")

        # Insert a flow entry with hardtimeout=1 and send_flow_removed flag set
        msg9 = message.flow_mod()
        msg9.match.wildcards = ofp.OFPFW_ALL
        msg9.cookie = random.randint(0,9007199254740992)
        msg9.buffer_id = 0xffffffff
        msg9.hard_timeout = 1
        msg9.flags |= ofp.OFPFF_SEND_FLOW_REM
        rv1 = self.controller.message_send(msg9)
        self.assertTrue(rv1 != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        #Verify flow gets inserted
        Verify_TableStats(self,active_entries=1)

        # Verify flow removed message is recieved.
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_FLOW_REMOVED,
                                               timeout=5)
        self.assertTrue(response is not None, 
                        'Did not receive flow removed message ')
        self.assertEqual(ofp.OFPRR_HARD_TIMEOUT, response.reason,
                         'Flow table entry removal reason is not hard_timeout')
        self.assertEqual(1, response.duration_sec,
                         'Flow was not alive for 1 sec')


class Flow_Timeout(basic.SimpleDataPlane):
  
    """Verify that Flow removed messages are generated as expected
    Flow removed messages being generated when flag is set, is already tested in the above tests 
    So here, we test the vice-versa condition"""

    
    def runTest(self):

        cs_logger.info("Running Flow_Timeout test ")
        
        of_ports = cs_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear switch state
        rc = delete_all_flows(self.controller, cs_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        cs_logger.info("Inserting flow entry with hard_timeout set and send_flow_removed_message flag not set")
        cs_logger.info("Expecting the flow entry to delete, but no flow removed message")

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
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_FLOW_REMOVED,
                                               timeout=3)
        self.assertTrue(response is None, 
                        'Recieved flow removed message ')

        # Verify no entries in the table
        Verify_TableStats(self,active_entries=0)



        




       














