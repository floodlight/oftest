"""These tests fall under Conformance Test-Suite (OF-SWITCH-1.0.0 TestCases).
    Refer Documentation -- Detailed testing methodology 
    <Some of test-cases are directly taken from oftest> """

"Test Suite 2 --> Openflow Protocol messages"


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


of_port_map = None
of_logger = None
of_config = None

def test_set_init(config):
   

    basic.test_set_init(config)

    global of_port_map
    global of_logger
    global of_config

    of_logger = logging.getLogger("Start Openflow_Protocol_Messages Conformance Test-suite")
    of_logger.info("Initializing test set")
    of_port_map = config["port_map"]
    of_config = config


class Features_Request(basic.SimpleProtocol): 

    """Verify Features_Request-Reply is implemented 
    a) Send OFPT_FEATURES_REQUEST
	b) Verify OFPT_FEATURES_REPLY is received without errors"""

    def runTest(self):
        of_logger.info("Running Features_Request test")
        
        of_ports = of_port_map.keys()
        of_ports.sort()
        
        #Clear switch state
        rc = delete_all_flows(self.controller, of_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")
        
        of_logger.info("Sending Features_Request")
        of_logger.info("Expecting Features_Reply")

        request = message.features_request()
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Not able to send features request.")
        
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_FEATURES_REPLY,
                                               timeout=2)
        self.assertTrue(response is not None, 
                        'Did not receive Features Reply')


class Configuration_Request(basic.SimpleProtocol):
    
    """Check basic Get Config request is implemented
    a) Send OFPT_GET_CONFIG_REQUEST
    b) Verify OFPT_GET_CONFIG_REPLY is received without errors"""

    def runTest(self):

        of_logger.info("Running Configuration_Request test ")
        
        of_ports = of_port_map.keys()
        of_ports.sort()

        #Clear switch state
        rc = delete_all_flows(self.controller, of_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        of_logger.info("Sending OFPT_GET_CONFIG_REQUEST ")
        of_logger.info("Expecting OFPT_GET_CONFIG_REPLY ")

        request = message.get_config_request()
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, " Not able to send get_config request.")
        
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_GET_CONFIG_REPLY,
                                               timeout=2)
        self.assertTrue(response is not None, 
                        'Did not receive OFPT_GET_CONFIG_REPLY')

class Modify_State_Add(basic.SimpleProtocol):
    
    """Check basic Flow Add request is implemented
    a) Send  OFPT_FLOW_MOD , command = OFPFC_ADD 
    c) Send ofp_table_stats request , verify active_count=1 in reply"""

    def runTest(self):

        of_logger.info("Running Modify_State_Add test")

        of_ports = of_port_map.keys()
        of_ports.sort()
        
        #Clear switch state
        rc = delete_all_flows(self.controller,of_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        of_logger.info("Inserting a flow entry")
        of_logger.info("Expecting active_count=1 in table_stats_reply")

        #Insert a flow entry matching on ingress_port
        (Pkt,match) = Wildcard_All_Except_Ingress(self,of_ports)

        # Send Table_Stats_Request and verify flow gets inserted.
        Verify_TableStats(self,active_entries=1)


class Modify_State_Delete(basic.SimpleProtocol):
    
    """Check Basic Flow Delete request is implemented
    a) Send OFPT_FLOW_MOD, command = OFPFC_ADD
    b) Send ofp_table_stats request , verify active_count=1 in reply
    c) Send OFPT_FLOW_MOD, command = OFPFC_DELETE
    c) Send ofp_table_stats request , verify active_count=0 in reply"""

    def runTest(self):

        of_logger.info("Running Modify_State_Delete test")

        of_ports = of_port_map.keys()
        of_ports.sort()

        #Clear switch state
        rc = delete_all_flows(self.controller,of_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        of_logger.info("Inserting a flow entry and then deleting it")
        of_logger.info("Expecting the active_count=0 in table_stats_reply")

        #Insert a flow matching on ingress_port 
        (Pkt,match) = Wildcard_All_Except_Ingress(self,of_ports)

        #Verify Flow inserted.
        Verify_TableStats(self,active_entries=1)

        #Delete the flow 
        NonStrict_Delete(self,match)

        # Send Table_Stats_Request and verify flow deleted.
        Verify_TableStats(self,active_entries=0)

      

class Modify_State_Modify(basic.SimpleDataPlane):
    
    """Verify basic Flow Modify request is implemented
    a) Send OFPT_FLOW_MOD, command = OFPFC_ADD, Action A 
    b) Send OFPT_FLOW_MOD, command = OFPFC_MODIFY , with output action A'
    c) Send a packet matching the flow, verify packet implements action A' """

    def runTest(self):

        of_logger.info("Running Modify_State_modify test")

        of_ports = of_port_map.keys()
        of_ports.sort()

        #Clear switch state
        rc = delete_all_flows(self.controller, of_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        of_logger.info("Inserting a flow entry and then modifying it")
        of_logger.info("Expecting the Test Packet to implement the modified action")

        # Insert a flow matching on ingress_port with action A (output to of_port[1])    
        (pkt,match) = Wildcard_All_Except_Ingress(self,of_ports)
  
        # Modify the flow action (output to of_port[2])
        Modify_Flow_Action(self,of_ports,match)
        
        # Send the Test Packet and verify action implemented is A' (output to of_port[2])
        SendPacket(self, pkt, of_ports[0],of_ports[2])
                       

class Read_State(basic.SimpleProtocol):
    
    """Test that a basic Read state request (like flow_stats_get request) does not generate an error
    a) Send OFPT_FLOW_MOD, command = OFPFC_ADD
    b) Send ofp_flow_stats request
    b) Verify switch replies without errors"""

    def runTest(self):

        of_logger.info("Running Read_State test")

        of_ports = of_port_map.keys()
        of_ports.sort()

        #Clear switch state
        rc = delete_all_flows(self.controller, of_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        of_logger.info("Inserting a flow entry and then sending flow_stats request")
        of_logger.info("Expecting the a flow_stats_reply without errors")

        # Insert a flow with match on ingress_port
        (pkt,match ) = Wildcard_All_Except_Ingress(self,of_ports)
        
        #Verify Flow_Stats request does not generate errors
        Verify_FlowStats(self,match)
        
class Send_Packet(basic.SimpleDataPlane):
    
    """Test packet out function
    a) Send packet out message for each dataplane port.
    b) Verify the packet appears on the appropriate dataplane port"""
    
    def runTest(self):

        of_logger.info("Running Send_Packet test")

        of_ports = of_port_map.keys()
        of_ports.sort()
       
        #Clear Switch state
        rc = delete_all_flows(self.controller, of_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        of_logger.info("Sending a packet-out for each dataplane port")
        of_logger.info("Expecting the packet on appropriate dataplane port")

        for dp_port in of_ports:
            for outpkt, opt in [
                (simple_tcp_packet(), "simple TCP packet"),
                (simple_eth_packet(), "simple Ethernet packet"),
                (simple_eth_packet(pktlen=40), "tiny Ethernet packet")]:
            
                msg = message.packet_out()
                msg.data = str(outpkt)
                act = action.action_output()
                act.port = dp_port
                self.assertTrue(msg.actions.add(act), 'Could not add action to msg')

                of_logger.info("PacketOut to: " + str(dp_port))
                rv = self.controller.message_send(msg)
                self.assertTrue(rv == 0, "Error sending out message")

                exp_pkt_arg = None
                exp_port = None
                if of_config["relax"]:
                    exp_pkt_arg = outpkt
                    exp_port = dp_port
                (of_port, pkt, pkt_time) = self.dataplane.poll(timeout=2, 
                                                                port_number=exp_port,
                                                                exp_pkt=exp_pkt_arg)
                
                self.assertTrue(pkt is not None, 'Packet not received')
                of_logger.info("PacketOut: got pkt from " + str(of_port))
                if of_port is not None:
                    self.assertEqual(of_port, dp_port, "Unexpected receive port")
                if not dataplane.match_exp_pkt(outpkt, pkt):
                    of_logger.debug("Sent %s" % format_packet(outpkt))
                    of_logger.debug("Resp %s" % format_packet(
                            str(pkt)[:len(str(outpkt))]))
                self.assertEqual(str(outpkt), str(pkt)[:len(str(outpkt))],
                                    'Response packet does not match send packet')

        
class Packet_In(basic.SimpleDataPlane):
    
    """Test basic packet_in function
    a) Send a simple tcp packet to a dataplane port, without any flow-entry 
    b) Verify that a packet_in event is sent to the controller"""
    
    def runTest(self):
        
        of_logger.info("Running Packet_In test")

        of_ports = of_port_map.keys()
        of_ports.sort()
        ingress_port = of_ports[0]

        #Clear Switch state
        rc = delete_all_flows(self.controller, of_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        of_logger.info("Sending a Simple tcp packet a dataplane port")
        of_logger.info("Expecting a packet_in event on the control plane")

        # Send  packet on dataplane port and verify packet_in event gets generated.
        pkt = simple_tcp_packet()
        self.dataplane.send(ingress_port, str(pkt))
        of_logger.info("Sending packet to dp port " + str(ingress_port) +
                   ", expecting packet_in on control plane" )
      
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_PACKET_IN,
                                               timeout=2)
        self.assertTrue(response is not None, 
                               'Packet in event is not sent to the controller') 


class Hello(basic.SimpleDataPlane):
    
    """Test Hello messages are implemented
    a) Create Hello messages from controller
    b) Verify switch also exchanges hello message -- (Poll the control plane)
    d) Verify the version field in the hello messages is openflow 1.0.0 """

    def runTest(self):
        
        of_logger.info("Running Hello test")

        of_logger.info("Sending Hello")
        of_logger.info("Expecting a Hello on the control plane with version--1.0.0")
        
        #Send Hello message
        request = message.hello()
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_HELLO,
                                               timeout=1)
        self.assertTrue(response is not None, 
                               'Switch did not exchange hello message in return') 
        self.assertTrue(response.header.version == 0x01, 'switch openflow-version field is not 1.0.0')



class EchoWithoutBody(basic.SimpleProtocol):
    
    """Test basic echo-reply is implemented
    a)  Send echo-request from the controller side, note echo body is empty here.
    b)  Verify switch responds back with echo-reply with same xid """
    
    def runTest(self):

        of_logger.info("Running EchoWithoutBody test")

        of_logger.info("Sending Echo Request")
        of_logger.info("Expecting a Echo Reply with version--1.0.0 and same xid")

        # Send echo_request
        request = message.echo_request()
        (response, pkt) = self.controller.transact(request)
        self.assertEqual(response.header.type, ofp.OFPT_ECHO_REPLY,'response is not echo_reply')
        self.assertEqual(request.header.xid, response.header.xid,
                         'response xid != request xid')
        self.assertTrue(response.header.version == 0x01, 'switch openflow-version field is not 1.0.1')
        self.assertEqual(len(response.data), 0, 'response data non-empty')


class BarrierRequestReply(basic.SimpleProtocol):

    """ Check basic Barrier request is implemented
    a) Send OFPT_BARRIER_REQUEST
    c) Verify OFPT_BARRIER_REPLY is recieved"""
    
    def runTest(self):

        of_logger.info("Running BarrierRequestReply test")

        of_logger.info("Sending Barrier Request")
        of_logger.info("Expecting a Barrier Reply with same xid")

        #Send Barrier Request
        request = message.barrier_request()
        (response, pkt) = self.controller.transact(request)
        self.assertEqual(response.header.type, ofp.OFPT_BARRIER_REPLY,'response is not barrier_reply')
        self.assertEqual(request.header.xid, response.header.xid,
                         'response xid != request xid')





