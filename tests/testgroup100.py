"""These tests fall under Conformance Test-Suite (OF-SWITCH-1.0.0 TestCases).
    Refer Documentation -- Detailed testing methodology 
    <Some of test-cases are directly taken from oftest> """

"Test Suite 9 --> Error Messages "

import logging
import time
import sys

import unittest
import random

import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action
import oftest.parse as parse
import oftest.base_tests as base_tests

from oftest.testutils import *
from time import sleep
from FuncUtils import *
import basic
import oftest.illegal_message as illegal_message


class Grp100No10(base_tests.SimpleProtocol):
    """
    When the switch fails a successful hello-exchange with the controller ,
    it generates an OFPT_ERROR msg with Type Field OFPET_HELLO_FAILED
    code field OFPHFC_INCOMPATIBLE    
    """
    def setUp(self):

        #This is almost same as setUp in SimpleProtocol except that intial hello is set to false
        self.controller = controller.Controller(
            host=config["controller_host"],
            port=config["controller_port"])
        # clean_shutdown should be set to False to force quit app
        self.clean_shutdown = True
        #set initial hello to False
        self.controller.initial_hello=False
        self.controller.start()
        self.controller.connect(timeout=20)
        # By default, respond to echo requests
        self.controller.keep_alive = True
        if not self.controller.active:
            raise Exception("Controller startup failed")
        if self.controller.switch_addr is None: 
            raise Exception("Controller startup failed (no switch addr)")
        logging.info("Connected " + str(self.controller.switch_addr))
        
    def runTest(self):

        logging.info("Running Grp100No10 HelloFailed Test")  

        #Send a hello message with incorrect version
        logging.info("Sending Hello message with incorrect version..")
        request = message.hello()                                               
        logging.info("Change hello message version to 0 and send it to control plane")
        request.header.version=0
        rv = self.controller.message_send(request)      
        
        logging.info("Waiting for OFPT_ERROR message..")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=5)
        self.assertTrue(response is not None, 
                               'Switch did not reply with error message') 
        self.assertTrue(response.type==ofp.OFPET_HELLO_FAILED, 
                               'Error type is not HELLO_FAILED') 
        self.assertTrue(response.code==ofp.OFPHFC_INCOMPATIBLE, 
                               'Error code is not OFPHFC_INCOMPATIBLE')
    

class Grp100No20(base_tests.SimpleProtocol):
    """When the header in the request msg  
    contains a version field which is not supported by the switch , 
    it generates OFPT_ERROR_msg with Type field OFPET_BAD_REQUEST 
    and code field OFPBRC_BAD_VERSION
    """
    
    def runTest(self):
        
        logging.info("Running Grp100No20 BadRequestBadVersion Test") 

        #Send a flow_stats request , with incorrect version
        logging.info("Sending flow_mod request.. ")
        request=message.flow_stats_request();
        request.header.version=0        
        rv = self.controller.message_send(request)
        
        logging.info("Waiting for OFPT_ERROR message..")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=5)
        self.assertTrue(response is not None, 
                               'Switch did not reply with error message')
        self.assertTrue(response.type==ofp.OFPET_BAD_REQUEST, 
                               'Error type is not OFPET_BAD_REQUEST') 
        self.assertTrue(response.code==ofp.OFPBRC_BAD_VERSION, 
                               'Error code is not OFPBRC_BAD_VERSION')


class Grp100No30(base_tests.SimpleProtocol):
    """When the header in the request msg contains a type field which is not 
   supported by the switch ,it generates an OFPT_ERROR msg with the Type Field OFPET_BAD_REQUEST
   and code field OFPBRC_BAD_TYPE
    """ 
    def runTest(self):

        logging.info("Running Grp100No30 BadRequestBadType test")

        #Send a request with unsupported type field
        logging.info("Send a request with bad type ..")
        request = illegal_message.illegal_message_type()
        (reply, pkt) = self.controller.transact(request)

        logging.info("Expecting OFPT_ERROR message...")
        self.assertTrue(reply is not None, "Did not get response to bad req")
        self.assertTrue(reply.header.type == ofp.OFPT_ERROR,
                        "reply not an error message")
        self.assertTrue(reply.type == ofp.OFPET_BAD_REQUEST,
                        "Error type is not bad request")
        self.assertTrue(reply.code == ofp.OFPBRC_BAD_TYPE,
                        "Error code is not bad type")

class Grp100No60(base_tests.SimpleProtocol):
    """
    Unknown vendor id specified. 
    If a switch does not understand a vendor extension, it must send an OFPT_ERROR
    message with a OFPBRC_BAD_VENDOR error code and OFPET_BAD_REQUEST error
    type.
    """
    
    def runTest(self):  
        logging.info("Running Grp100No60 BadRequestBadVendor test")      
             
        request = message.vendor()  
        request.vendor = 400  
        
        (response, pkt) = self.controller.transact(request)
        self.assertEqual(response.header.type,ofp.OFPT_ERROR,'response is not error message') 
        self.assertEqual(response.type, ofp.OFPET_BAD_REQUEST,'Error type not as expected')
        if not response.code == ofp.OFPBAC_BAD_VENDOR | ofp.OFPBRC_EPERM :
            logging.info("Error code is not as expected")

class Grp100No90(base_tests.SimpleProtocol):  
  
    """When the length field in the header of the stats request is wrong , 
    switch generates an OFPT_ERROR msg with type field OFPET BAD_REQUEST 
    and code field OFPBRC_BAD_LEN
    """
    def runTest(self):

        logging.info("Running Grp100No60 BadRequestBadLength test")
        #In Message module at pack time the length is computed
        #avoid this by using cstruct module
        logging.info("Sending stats_request message..")
        stats_request = ofp.ofp_stats_request()
        header=ofp.ofp_header() 
        header.type = ofp.OFPT_STATS_REQUEST
        # normal the header length is 12bytes changed it to 18bytes
        header.length=180;
        packed=header.pack()+stats_request.pack()
        rv=self.controller.message_send(packed)
        self.assertTrue(rv != -1,"Unable to send the message")

        logging.info("Waiting for OFPT_ERROR message..")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=5)
        self.assertTrue(response is not None, 
                               'Switch did not reply with expected error messge')
        self.assertTrue(response.type==ofp.OFPET_BAD_REQUEST, 
                               'Error type is not OFPET_BAD_REQUEST') 
        self.assertTrue(response.type==ofp.OFPBRC_BAD_LEN, 
                               'Error code is not OFPBRC_BAD_LEN')   


class Grp100No110(base_tests.SimpleProtocol):
    """
    Specified buffer does not exist. 

    When the buffer specified by the controller does not exit , the switch
    replies back with OFPT_ERROR msg with type fiels OFPET_BAD_REQUEST

    """
    def runTest(self):

        logging.info("Running Grp100No110 BadRequestBufferUnknown test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        msg = message.packet_out()
        msg.buffer_id = 173 #Random buffer_id 
        act = action.action_output()
        act.port = of_ports[1]
        self.assertTrue(msg.actions.add(act), 'Could not add action to msg')

        logging.info("PacketOut to: " + str(of_ports[1]))
        rv = self.controller.message_send(msg)
        self.assertTrue(rv == 0, "Error sending out message")

        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,
                                               timeout=5)
        self.assertTrue(response is not None,
                                'Switch did not reply with error messge')
        self.assertTrue(response.type==ofp.OFPET_BAD_REQUEST,
                               'Message field type is not OFPET_BAD_REQUEST')
        self.assertTrue(response.code==ofp.OFPBRC_BUFFER_UNKNOWN,
                               'Message field code is not OFPBRC_BUFFER_UNKNOWN')       


class Grp100No120(base_tests.SimpleDataPlane): 

    """When the type field in the action header specified by the controller is unknown , 
    the switch generates an OFPT_ERROR msg with type field OFPBET_BAD_ACTION and code field OFPBAC_BAD_TYPE
    """
    def runTest(self):  
        
        logging.info("Running Grp100No120 test")
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Sending a flow with output action s.t type field in the action header is unknown
        logging.info("Sending flow_mod message..")
        pkt=simple_tcp_packet()
        act=action.action_output()       
        request = flow_msg_create(self, pkt, ing_port=of_ports[0], egr_ports=of_ports[1])
        request.actions.actions[0].type=67
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1,"Unable to send the message")

        logging.info("Waiting for OFPT_ERROR message...")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=5)
        self.assertTrue(response is not None, 
                                'Switch did not reply with error messge')                                       
        self.assertTrue(response.type==ofp.OFPET_BAD_ACTION, 
                               'Error type is not OFPET_BAD_ACTION') 
        self.assertTrue(response.code==ofp.OFPBAC_BAD_TYPE, 
                               'Error code is not OFPBAC_BAD_TYPE')      


class Grp100No130(base_tests.SimpleDataPlane):   
    """When the length field in the action header specified by the controller is wrong ,
    the switch replies back with an OFPT_ERROR msg with Type Field OFPBAC_BAD_LEN"""
    
    def runTest(self):  
        
        logging.info("Running Grp100No130 BadActionBadLen test")
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Sending a flow with output action s.t length field in the action header is incorrect
        logging.info("Sending flow_mod message..")
        pkt=simple_tcp_packet()
        act=action.action_output()       
        request = flow_msg_create(self, pkt, ing_port=of_ports[0], egr_ports=of_ports[1])
        #Actual Length is 8 bytes, changed it to 7 bytes
        request.actions.actions[0].len=7
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1,"Unable to send the message")

        logging.info("Waiting for OFPT_ERROR message...")

        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=5)
        self.assertTrue(response is not None, 
                                'Switch did not reply with error messge')                                       
        self.assertTrue(response.type==ofp.OFPET_BAD_ACTION, 
                               'Error type is not OFPET_BAD_ACTION') 
        self.assertTrue(response.code==ofp.OFPBAC_BAD_LEN, 
                               'Error code is not OFPBAC_BAD_LEN')      



class Grp100No160(base_tests.SimpleProtocol):
    
    """When the output to switch port action refers to a port that does not exit ,
    the switch generates an OFPT_ERROR msg , with type field OFPT_BAD_ACTION and code field OFPBAC_BAD_OUT_PORT
    
    Some switches may generate an OFPT_ERROR , with type field FLOW_MOD_FAILED and code permission errors 
    (this is also acceptable)
    """

    def runTest(self):

        logging.info("Running Grp100No160 BadActionBadPort test")

        # pick a random bad port number
        bad_port=ofp.OFPP_MAX
        pkt=simple_tcp_packet()
        act=action.action_output()   

        #Send flow_mod message
        logging.info("Sending flow_mod message..")   
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

class Grp100No170(base_tests.SimpleProtocol):
    """
    Bad action argument.

    If the arguments specified in the action are wrong,
    then the switch reponds back with an OFPT_ERROR msg
    with type field OFPT_BAD_ACTION and code field OFPBAC_BAD_ARGUMENT

    Error code permission error is also acceptable
    """
    def runTest(self):

        logging.info("Running Grp100No170 BadActionBadArgument test")

        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        flow_mod_msg = message.flow_mod()
        act = action.action_enqueue()
        act.type = ofp.OFPAT_ENQUEUE
        act.port = ofp.OFPP_ALL
        act.queue_id = 1
        self.assertTrue(flow_mod_msg.actions.add(act), "Could not add action")

        rv = self.controller.message_send(flow_mod_msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        # flow with modifed arguments
        flow_mod_msg = message.flow_mod()
        act = action.action_set_vlan_vid()
        act.type = ofp.OFPAT_SET_VLAN_VID
        act.len = 8 
        act.port = ofp.OFPP_ALL
        act.vlan_vid = -2 # incorrect vid 
        act.pad = [0, 0]
        self.assertTrue(flow_mod_msg.actions.add(act), "Could not add action")

        rv = self.controller.message_send(flow_mod_msg.pack())
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        count = 0
        while True:
            (response, raw) = self.controller.poll(ofp.OFPT_ERROR)
            if not response:  # Timeout
                break
            if not response.type == ofp.OFPET_BAD_ACTION:
                logging.info("Error type not as expected")
                break
            if not response.code == ofp.OFPBAC_BAD_ARGUMENT | ofp.OFPBAC_EPERM:
                logging.info("Error code is not as expected")
                break
            if not config["relax"]:  # Only one attempt to match
                break
            count += 1
            if count > 10:   # Too many tries
               break

class Grp100No190(base_tests.SimpleProtocol):
    """
    If the actions specified by the controller are more than that
    switch can support, the switch responds back with an OFPT_ERROR msg,
    with type field OFPT_BAD_ACTION and code field OFPBAC_TOO_MANY
    """

    def runTest(self):
        
        logging.info("Running BadActionTooMany Grp100No190 test")
        
        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        #Create flow_mod message with lot of actions
        flow_mod_msg = message.flow_mod()
        # add a lot of actions
        no = random.randint(2000, 4000)
        for i in range(0, no):
            act = action.action_enqueue()
            self.assertTrue(flow_mod_msg.actions.add(act), "Could not add action")

        logging.info("Sending flow_mod message...")
        rv = self.controller.message_send(flow_mod_msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        logging.info("Waiting for OFPT_ERROR message...")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR, timeout=5)
        self.assertTrue(response is not None,
                               'Switch did not replay with error messge')
        self.assertTrue(response.type==ofp.OFPET_BAD_ACTION,
                               'Error type is not OFPET_BAD_ACTION')
        self.assertTrue(response.code==ofp.OFPBAC_TOO_MANY,
                               'Error code is not OFPBAC_TOO_MANY')



class Grp100No200(base_tests.SimpleDataPlane):
    """
    If the switch is not able to process the Enqueue action specified by the controller then 
    the switch should generate an OFPT_ERROR msg ,type field OFPT_BAD_ACTION and code field OFPBAC_BAD_QUEUE"""
   
    def runTest(self):

        logging.info("Running BadActionQueue Grp100No200 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        #Create a flow with enqueue action 
        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                "Could not generate flow match from pkt")
        match.in_port = of_ports[0]

        logging.info("Sending flow_mod message...")
        request = message.flow_mod()
        request.match = match
        act = action.action_enqueue()
        act.port     = of_ports[1]
        act.queue_id = -1  #Invalid queue_id
        self.assertTrue(request.actions.add(act), "Could not add action")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        count = 0
        logging.info("Waiting for OFPT_ERROR message...")
        while True:
            (response, raw) = self.controller.poll(ofp.OFPT_ERROR)
            if not response:  # Timeout
                break
            if not response.type == ofp.OFPET_BAD_ACTION:
                logging.info("Error type not as expected")
                break
            if not response.code == ofp.OFPQOFC_BAD_QUEUE:
                logging.info("Error code is not as expected")
                break
            if not config["relax"]:  # Only one attempt to match
                break
            count += 1
            if count > 10:   # Too many tries
                break



class Grp100No220(base_tests.SimpleDataPlane):
    
    """Verify that if overlap check flag is set in the flow entry and an
        overlapping flow is inserted then an error 
        type OFPET_FLOW_MOD_FAILED code OFPFMFC_OVERLAP"""
    
    def runTest(self):
        
        logging.info("Running FlowModFailedOverlap Grp100No200 test")
       
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear Switch State
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        #Insert a flow F with wildcarded all fields
        (pkt,match) = wildcard_all(self,of_ports)

        #Verify flow is active  
        verify_tablestats(self,expect_active=1)
        
        # Build a overlapping flow F'-- Wildcard All except ingress with check overlap bit set
        pkt_matchingress = simple_tcp_packet()
        match3 = parse.packet_to_flow_match(pkt_matchingress)
        self.assertTrue(match3 is not None, "Could not generate flow match from pkt")
        match3.wildcards = ofp.OFPFW_ALL-ofp.OFPFW_IN_PORT
        match3.in_port = of_ports[0]

        logging.info("Sending flow_mod message...")
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
        verify_tablestats(self,expect_active=1)

        #Verify OFPET_FLOW_MOD_FAILED/OFPFMFC_OVERLAP error is recieved on the control plane
        logging.info("Waiting for OFPT_ERROR message...")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=5)
        self.assertTrue(response is not None, 
                               'Switch did not reply with error message') 
        self.assertTrue(response.type==ofp.OFPET_FLOW_MOD_FAILED, 
                               'Error type is not flow mod failed ') 
        self.assertTrue(response.code==ofp.OFPFMFC_OVERLAP, 
                               'Error code is not overlap')


class Grp100No240(base_tests.SimpleProtocol): 

    """When the emergency flows are added by the controller they should have a zero idle/hard timeout.
        Otherwise , should switch should respond with an OFPT ERROR msg , 
        type field OFPET_FLOW_MOD_FAILED, code field OFPFMFC_BAD_EMERG_TIMEOUT"""

    def runTest(self):

        logging.info("Running FlowModFailedBadEmer Grp100No240 test")
        
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        #Insert an emergency flow 
        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        match.in_port = of_ports[0]
        
        logging.info("Sending flow_mod message...")
        request = message.flow_mod()
        request.match = match
        request.command = ofp.OFPFC_ADD
        request.flags = request.flags|ofp.OFPFF_EMERG
        request.hard_timeout =9
        request.idle_timeout =9
        act = action.action_output()
        act.port = of_ports[1]
        request.actions.add(act)
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Flow addition did not fail.")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        #Verify OFPET_FLOW_MOD_FAILED/OFPFMFC_BAD_EMERG_TIMEOUT error is recieved on the control plane
        logging.info("Waiting for OFPT_ERROR message...")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=5)
        self.assertTrue(response is not None, 
                               'Switch did not reply with error message') 
        self.assertTrue(response.type==ofp.OFPET_FLOW_MOD_FAILED, 
                               'Error type is not flow mod failed ') 
        self.assertTrue(response.code==ofp.OFPFMFC_BAD_EMERG_TIMEOUT, 
                               'Error code is not bad emergency timeout')


class Grp100No250(base_tests.SimpleProtocol):   
    """
    Unknown command.
    When the flow_mod msg request is sent by the controller with 
    some invalid command , the switch responds with an OFPT_ERROR msg , 
    type field OFPET_FLOW_MOD_FAILED and code field OFPFMFC_BAD_COMMAND """
    
    def runTest(self):

        logging.info("Running FlowModFailedBadCommand Grp100No250 test")
        msg = message.flow_mod()
        msg.command = 8

        packed=msg.pack()

        rv=self.controller.message_send(packed)
        self.assertTrue(rv==0,"Unable to send the message")      
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=5)
        self.assertTrue(response is not None, 
                                'Switch did not reply with error messge')                                       
        self.assertTrue(response.type==ofp.OFPET_FLOW_MOD_FAILED, 
                               'Error type is not OFPET_FLOW_MOD_FAILED') 
        self.assertTrue(response.code==ofp.OFPFMFC_BAD_COMMAND, 
                               'Error code is not OFPFMFC_BAD_COMMAND')


class Grp100No260(base_tests.SimpleProtocol):   
    """
    Unsupported action list - cannot process in order specified
    If a switch cannot process the action list for any  flow mod message in the order specied, 
    it must immediately return an OFPET_FLOW_MOD_FAILED :OFPFMFC_UNSUPPORTED error and reject the flow """
    
    def runTest(self):
        logging.info("Running FlowModFailed Unsupported action list Grp100No250 test")

        msg = message.flow_mod()
        act1 = action.action_output()
        act2 = action.action_set_dl_src()
        act1.port = 99
        act2.dl_addr = [11, 11, 11, 11, 11, 11]

        self.assertTrue(msg.actions.add(act1), "Could not add action")
        self.assertTrue(msg.actions.add(act2), "Could not add action")

        packed=msg.pack()

        rv=self.controller.message_send(packed)
        self.assertTrue(rv==0,"Unable to send the message")      
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR)        
        
        count = 0
        while True:
            (response, raw) = self.controller.poll(ofp.OFPT_ERROR)
            if not response:  # Timeout
                break
            if not response.type == ofp.OFPET_FLOW_MOD_FAILED:
                logging.info("Error Type is not as expected")
                break
            if response.code == ofp.OFPFMFC_UNSUPPORTED | ofp.OFPFMFC_EPERM:
                logging.info("Error Code is not as expected")
                break
            if not config["relax"]:  # Only one attempt to match
                break
            count += 1
            if count > 10:   # Too many tries
                break                                    
       

class Grp100No270(base_tests.SimpleProtocol):
    """
    Modify a bit in port config on an invalid port and verify
    error message is received.
    """

    def runTest(self):
        
        logging.info("Running PortModFailedBadPort Grp100No270 test")
        
        # pick a random bad port number
        bad_port=ofp.OFPP_MAX
        rv = port_config_set(self.controller, bad_port,
                             ofp.OFPPC_NO_FLOOD, ofp.OFPPC_NO_FLOOD)
        self.assertTrue(rv != -1, "Error sending port mod")

        # poll for error message
        count = 0
        while True:
            (response, raw) = self.controller.poll(ofp.OFPT_ERROR)
            if not response:  # Timeout
                break
            if not response.type == ofp.OFPET_PORT_MOD_FAILED:
                logging.info("Error Type is not as expected")
                break
            if response.code == ofp.OFPPMFC_BAD_PORT:
                logging.info("Error Code is not as expected")
                break
            if not config["relax"]:  # Only one attempt to match
                break
            count += 1
            if count > 10:   # Too many tries
                break


class Grp100No280(base_tests.SimpleProtocol):    
    """If the controller sends a port_mod request for any port  with a hardware address that is different 
    from one returned in ofp_phy_port struct.,the switch will respond back with an OFPT_ERROR msg , 
    type field OFPET_PORT_MOD_FAILED and code field OFPPMFC_BAD_HW_ADDR
    """
    def runTest(self):

        logging.info("Running PortModFailedBadHwAdd Grp100No280 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Send features request
        request = message.features_request()
        reply, pkt = self.controller.transact(request, timeout=2)
        self.assertTrue(reply is not None, "Features Reply not recieved")
        for idx in range(len(reply.ports)):
            if reply.ports[idx].port_no == of_ports[0]:
                break
        self.assertTrue(idx <= len(reply.ports), "Error in the ports information")

        logging.info("Sending port_mod request ..")
        mod = message.port_mod()
        mod.port_no = of_ports[0]
        mod.hw_addr = [0,0,0,0,0,0]
        mod.config = ofp.OFPPC_NO_FLOOD
        mod.mask = ofp.OFPPC_NO_FLOOD
        mod.advertise = reply.ports[idx].advertised
        rv = self.controller.message_send(mod)
        self.assertTrue(rv != -1,"Unable to send the message")
        
        logging.info("Waiting for OFPT_ERROR message...")
        count = 0
        while True:
            (response, raw) = self.controller.poll(ofp.OFPT_ERROR)
            if not response:  # Timeout
                break
            if not response.type == ofp.OFPET_PORT_MOD_FAILED:
                logging.info("Error type is not as expected")
                break
            if not response.code == ofp.OFPPMFC_BAD_HW_ADDR:
                logging.info("Error Code is not as expected")
                break
            if not config["relax"]:  # Only one attempt to match
                break
            count += 1
            if count > 10:   # Too many tries
                break  


class Grp100No300(base_tests.SimpleDataPlane):

    """If the port specifed for any queue operation (like enqeue --output to queue or retrieving queue stats )
     is an invalid port , then the switch responds back with an error msg OFPT_ERROR msg , 
     type field OFPET_QUEUE_OP_FAILED , code field OFPQOFC_BAD_PORT"""
    
    def runTest(self):

        logging.info("Running Grp100No300 QueueOpFailedBadPort test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        logging.info("Sending queue_stats request ..")
        request = message.queue_stats_request()
        request.port_no  = ofp.OFPP_MAX
        request.queue_id = ofp.OFPQ_ALL
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1,"Unable to send the message")

        logging.info("Waiting for OFPT_ERROR message...")

        count = 0
        while True:
            (response, raw) = self.controller.poll(ofp.OFPT_ERROR)
            if not response:  # Timeout
                break
            if not response.type == ofp.OFPET_QUEUE_OP_FAILED:
                logging.info("Error Type is not as expected")
                break
            if not response.code == ofp.OFPQOFC_BAD_PORT:
                logging.info("Error Code is not as expected")
                break
            if not config["relax"]:  # Only one attempt to match
                break
            count += 1
            if count > 10:   # Too many tries
                break  



class Grp100No310(base_tests.SimpleDataPlane):

    """If the queue_id specifed for any queue operation (like enqeue --output to queue or retrieving queue stats ) 
    is an invalid queue ,then the switch responds back with an error msg OFPT_ERROR msg , 
    type field OFPET_QUEUE_OP_FAILED , code field OFPQOFC_BAD_QUEUE"""
    
    def runTest(self):

        logging.info("Running QueueOpFailedBadQueue Grp100No310 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        logging.info("Sending queue_stats request ..")
        request = message.queue_stats_request()
        request.port_no  = of_ports[0]
        request.queue_id = -1 #Invalid queue_id
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1,"Unable to send the message")

        logging.info("Waiting for OFPT_ERROR message...")
        
        count = 0
        while True:

            (response, raw) = self.controller.poll(ofp.OFPT_ERROR)
            if not response:  # Timeout
                break
            if not response.type == ofp.OFPET_QUEUE_OP_FAILED:
                logging.info("Error Type is not as expected")
                break
            if not response.code == ofp.OFPQOFC_BAD_QUEUE:
                logging.info("Error Code is not as expected")
                break
            if not config["relax"]:  # Only one attempt to match
                break
            count += 1
            if count > 10:   # Too many tries
                break












