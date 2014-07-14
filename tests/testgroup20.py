"""These tests fall under Conformance Test-Suite (OF-SWITCH-1.0.0 TestCases).
    Refer Documentation -- Detailed testing methodology 
    <Some of test-cases are directly taken from oftest> """

"Test Suite 2 --> Openflow Protocol messages"


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

class Grp20No10(base_tests.SimpleProtocol): 

    """Verify Features_Request-Reply is implemented 
    a) Send OFPT_FEATURES_REQUEST
	b) Verify OFPT_FEATURES_REPLY is received"""
    
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp20No10 Features_Request test")
        
        of_ports = config["port_map"].keys()
        of_ports.sort()
        
        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")
        
        logging.info("Sending OFPT_FEATURES_REQUEST")

        request = message.features_request()
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Not able to send features request.")
        
        logging.info("Expecting  OFPT_FEATURES_REPLY")
        
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_FEATURES_REPLY,
                                               timeout=2)
        self.assertTrue(response is not None, 
                        'Did not receive OFPT_FEATURES_REPLY')
        logging.info("Received OFPT_FEATURES_REPLY")


class Grp20No20(base_tests.SimpleProtocol):
    
    """Check basic Get Config request is implemented
    a) Send OFPT_GET_CONFIG_REQUEST
    b) Verify OFPT_GET_CONFIG_REPLY is received"""
    
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp20No20 Configuration_Request test ")
        
        of_ports = config["port_map"].keys()
        of_ports.sort()

        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Sending OFPT_GET_CONFIG_REQUEST ")
        
        request = message.get_config_request()
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, " Not able to send get_config request.")

        logging.info("Expecting OFPT_GET_CONFIG_REPLY ")
 
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_GET_CONFIG_REPLY,
                                               timeout=2)
        self.assertTrue(response is not None, 
                        'Did not receive OFPT_GET_CONFIG_REPLY')
	logging.info("Received OFPT_GET_CONFIG_REPLY ")
class Grp20No30(base_tests.SimpleProtocol):
    
    """Check basic Flow Add request is implemented
    a) Send  OFPT_FLOW_MOD , command = OFPFC_ADD 
    c) Send ofp_aggregate_stats_request , verify flows=1 in reply"""
    
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp20No30 Modify_State_Add test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        
        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Inserting a flow entry")

        #Insert a flow entry matching on ingress_port
        (pkt,match) = wildcard_all_except_ingress(self,of_ports)

        sleep(1)
        
        logging.info("Expecting aggregate_stats[flows]==1")

        # Send Table_Stats_Request and verify flow gets inserted.
        rv = all_stats_get(self)
        self.assertTrue(rv["flows"] == 1 , "Flow count not equal to number of flows inserted")
	logging.info("aggregate_stats[flows]==1")

class Grp20No40(base_tests.SimpleProtocol):
    
    """Check Basic Flow Delete request is implemented
    a) Send OFPT_FLOW_MOD, command = OFPFC_ADD
    b) Send ofp_table_stats request , verify active_count=1 in reply
    c) Send OFPT_FLOW_MOD, command = OFPFC_DELETE
    c) Send ofp_table_stats request , verify active_count=0 in reply"""
    
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp20No40 Modify_State_Delete test")

        of_ports = config["port_map"].keys()
        of_ports.sort()

        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Inserting a flow entry")
        logging.info("Expecting the Flow count=1 in aggregate_stats_reply")

        #Insert a flow matching on ingress_port 
        (pkt,match) = wildcard_all_except_ingress(self,of_ports)

        #Verify Flow inserted.
        rv = all_stats_get(self)
        self.assertTrue(rv["flows"] == 1 , "Flow count not equal to number of flows inserted")
	logging.info("aggregate_stats[flows]==1")

        #Delete the flow 
        logging.info("Deleting the flows inserted")
        nonstrict_delete(self,match)
	logging.info("Expecting the Flow count=0 in aggregate_stats_reply")
        # Send Table_Stats_Request and verify flow deleted.
	rv = all_stats_get(self)
        self.assertTrue(rv["flows"] == 0 , "Flow count not equal to the expecd number of flows")
	logging.info("aggregate_stats[flows]==0")

      

class Grp20No50(base_tests.SimpleDataPlane):
    
    """Verify basic Flow Modify request is implemented
    a) Send OFPT_FLOW_MOD, command = OFPFC_ADD, Action A 
    b) Send OFPT_FLOW_MOD, command = OFPFC_MODIFY , with output action A'
    c) Send a packet matching the flow, verify packet implements action A' """
    
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp20No50 Modify_State_Modify test")

        of_ports = config["port_map"].keys()
        of_ports.sort()

        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Inserting a flow entry")
        

        # Insert a flow matching on ingress_port with action A (output to of_port[1])    
        (pkt,match) = wildcard_all_except_ingress(self,of_ports)
  
        # Modify the flow action (output to of_port[2])
        logging.info("Modifying the output action of the flow entry")
        modify_flow_action(self,of_ports,match)
        
        logging.info("Expecting the Test Packet to implement the modified action")
        # Send the Test Packet and verify action implemented is A' (output to of_port[2])
        send_packet(self,pkt,of_ports[0],of_ports[2])
        logging.info("Modified Action implemented")               

class Grp20No60(base_tests.SimpleProtocol):
    
    """Test that a basic Read state request (like flow_stats_get request) does not generate an error
    a) Send OFPT_FLOW_MOD, command = OFPFC_ADD
    b) Send ofp_flow_stats request
    b) Verify switch replies with a ofp_flow_stats"""
    
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp20No60 Read_State test")

        of_ports = config["port_map"].keys()
        of_ports.sort()

        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Inserting a flow entry and then sending flow_stats request")
        # Insert a flow with match on ingress_port
        (pkt,match ) = wildcard_all_except_ingress(self,of_ports)
        
        logging.info("Expecting the a flow_stats reply")
        #Verify Flow_Stats request does not generate errors
        get_flowstats(self,match)
        logging.info("Received ofp_flow_stats reply")
        
        
class Grp20No70(base_tests.SimpleDataPlane):
    
    """Test packet out function
    a) Send packet out message for each dataplane port.
    b) Verify the packet appears on the appropriate dataplane port"""
    
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp20No70 Packet_Out test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
       
        #Clear Switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Sending a packet-out for each dataplane port")
        logging.info("Expecting the packet on appropriate dataplane port")

        for dp_port in of_ports:
            
            for outpkt, opt in [
                (simple_tcp_packet(), "simple TCP packet"),
                (simple_eth_packet(), "simple Ethernet packet"),
                (simple_eth_packet(pktlen=40), "tiny Ethernet packet")]:
            
                msg = message.packet_out()
                msg.in_port = ofp.OFPP_NONE
                msg.data = str(outpkt)
                act = action.action_output()
                act.port = dp_port
                self.assertTrue(msg.actions.add(act), 'Could not add action to msg')
                
                logging.info("PacketOut to: port " + str(dp_port))
                rv =self.controller.message_send(msg)
                self.assertTrue(rv == 0, "Error sending out message")
                error, _= self.controller.poll(exp_msg=ofp.OFPT_ERROR)
                if error: 
                    msg.in_port = ofp.OFPP_CONTROLLER
                    self.controller.message_send(msg)
                    error, _ =self.controller.poll(exp_msg=ofp.OFPT_ERROR)
                    self.assertIsNone(error, "Could Not send packet out message.got OFPT_ERROR")
                    logging.info("Packet out with in_port OFPP.CONTROLLER")

                exp_pkt_arg = None
                exp_port = None
                if config["relax"]:
                    exp_pkt_arg = outpkt
                    exp_port = dp_port
                (of_port, pkt, pkt_time) = self.dataplane.poll(timeout=2, 
                                                                port_number=exp_port,
                                                                exp_pkt=exp_pkt_arg)
                
                self.assertTrue(pkt is not None, 'Packet not received on the dataplane port')
                
                logging.info("PacketOut: got %s pkt on port " % opt + str(of_port))
                if of_port is not None:
                    self.assertEqual(of_port, dp_port, "Unexpected receive port")
                if not dataplane.match_exp_pkt(outpkt, pkt):
                    logging.debug("Sent %s" % format_packet(outpkt))
                    logging.debug("Resp %s" % format_packet(
                            str(pkt)[:len(str(outpkt))]))
                self.assertEqual(str(outpkt), str(pkt)[:len(str(outpkt))],
                                    'Response packet does not match send packet')


class Grp20No80(base_tests.SimpleProtocol):

    """ Check basic Barrier request is implemented
    a) Send OFPT_BARRIER_REQUEST
    c) Verify OFPT_BARRIER_REPLY is recieved"""
    
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp20No80 Barrier_Request_Reply test")

        logging.info("Sending OFPT_BARRIER_REQUEST")
        
        #Send Barrier Request
        request = message.barrier_request()
        (response,pkt) = self.controller.transact(request)
      
        logging.info("Expecting a OFPT_BARRIER_REPLY with same header and xid")
        self.assertEqual(response.header.type, ofp.OFPT_BARRIER_REPLY,'response is not barrier_reply')
        self.assertEqual(request.header.xid, response.header.xid,
                         'response xid != request xid')
	logging.info("received OFPT_BARRIER_REPLY with same header and xid")

        
class Grp20No90(base_tests.SimpleDataPlane):
    
    """Test basic packet_in function
    a) Send a simple tcp packet to a dataplane port, without any flow-entry 
    b) Verify that a packet_in event is sent to the controller"""
    
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp20No90 Packet_In test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        ingress_port = of_ports[3]

        #Clear Switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        logging.info("Sending a Simple tcp packet a dataplane port")
        logging.info("Expecting a packet_in event on the control plane")

        # Send  packet on dataplane port and verify packet_in event gets generated.
        pkt = simple_tcp_packet()
        self.dataplane.send(ingress_port, str(pkt))
        logging.info("Sending packet to dp port " + str(ingress_port) +
                   ", expecting packet_in on control plane" )
      
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_PACKET_IN,
                                               timeout=2)
        self.assertTrue(response is not None, 
                               'Packet in event is not sent to the controller')
        logging.info("Received packet_in from the switch")


class Grp20No100(base_tests.SimpleDataPlane):
    
    """Test Hello messages are implemented
    a) Create Hello messages from controller
    b) Verify switch also exchanges hello message -- (Poll the control plane)
    d) Verify the version field in the hello messages is openflow 1.0.0 """
    
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp20No100 Hello test")

        logging.info("Expecting a Hello on the control plane with version--1.0.0")
        
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_HELLO,
                                               timeout=1)
        self.assertTrue(response is not None, 
                               'Switch did not exchange hello message in return') 
        self.assertTrue(response.header.version == 0x01, 'switch openflow-version field is not 1.0.0')
	logging.info("Received a Hello on the control plane with version--1.0.0")


class Grp20No110(base_tests.SimpleProtocol):
    
    """Test basic echo-reply is implemented
    a)  Send echo-request from the controller side, note echo body is empty here.
    b)  Verify switch responds back with echo-reply with same xid """
    
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp20No110 Echo_Without_Body test")

        logging.info("Sending Echo Request")
        

        # Send echo_request
        request = message.echo_request()
        (response, pkt) = self.controller.transact(request)
        logging.info("Expecting a OFPT_ECHO_REPLY with version--1.0.0 and same xid")
        self.assertEqual(response.header.type, ofp.OFPT_ECHO_REPLY,'response is not echo_reply')
        self.assertEqual(request.header.xid, response.header.xid,
                         'response xid != request xid')
        self.assertTrue(response.header.version == 0x01, 'switch openflow-version field is not 1.0.1')
        self.assertEqual(len(response.data), 0, 'response data non-empty')
	logging.info("Received a OFPT_ECHO_REPLY with version set to 0x01 and same xid")        






