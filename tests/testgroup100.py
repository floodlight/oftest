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

from oftest.oflog import *
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
    @wireshark_capture
    def setUp(self):
        logging = get_logger()
        #This is almost same as setUp in SimpleProtocol except that intial hello is set to false
        self.controller = controller.Controller(
            host=config["controller_host"],
            port=config["controller_port"])
        time_out = config["controller_timeout"]

        # clean_shutdown should be set to False to force quit app
        self.clean_shutdown = True
        #set initial hello to False
        self.controller.initial_hello=False
        self.controller.start()

        self.controller.connect(timeout=time_out)
        # By default, respond to echo requests
        self.controller.keep_alive = True
        if not self.controller.active:
            raise Exception("Controller startup failed")
        if self.controller.switch_addr is None: 
            raise Exception("Controller startup failed (no switch addr)")
        logging.info("Connected " + str(self.controller.switch_addr))

        logging.info("Sending Hello message with incorrect version..")
        request = message.hello()                                               
        logging.info("Change hello message version to 0 and send it to control plane")
        request.header.version=0
        rv = self.controller.message_send(request)
        
    def runTest(self):

        logging.info("Running Grp100No10 HelloFailed Test")  

        logging.info("Waiting for OFPT_ERROR message..")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=5)
        self.assertTrue(response is not None, 
                               'Switch did not reply with error message') 
        self.assertTrue(response.type==ofp.OFPET_HELLO_FAILED, 
                               'Error type is not HELLO_FAILED') 
        self.assertTrue(response.code==ofp.OFPHFC_INCOMPATIBLE, 
                               'Error code is not OFPHFC_INCOMPATIBLE')
    

class Grp100No30(base_tests.SimpleProtocol):
    """When the header in the request msg  
    contains a version field which is not supported by the switch , 
    it generates OFPT_ERROR_msg with Type field OFPET_BAD_REQUEST 
    and code field OFPBRC_BAD_VERSION
    """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
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


class Grp100No40(base_tests.SimpleProtocol):
    """When the header in the request msg contains a type field which is not 
   supported by the switch ,it generates an OFPT_ERROR msg with the Type Field OFPET_BAD_REQUEST
   and code field OFPBRC_BAD_TYPE
    """ 
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
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

class Grp100No50(base_tests.SimpleProtocol):
    """
    Unknown vendor id specified. 
    If a switch does not understand a vendor extension, it must send an OFPT_ERROR
    message with a OFPBRC_BAD_VENDOR error code and OFPET_BAD_REQUEST error
    type.
    """
    @wireshark_capture
    def runTest(self):  
        logging = get_logger()
        logging.info("Running Grp100No50 BadRequestBadVendor test")      
             
        request = message.vendor()  
        request.vendor = 400  
        
        (response, pkt) = self.controller.transact(request)
        self.assertEqual(response.header.type,ofp.OFPT_ERROR,'response is not error message') 
        self.assertEqual(response.type, ofp.OFPET_BAD_REQUEST,'Error type not as expected')
        self.assertTrue(response.code == ofp.OFPBRC_BAD_VENDOR or response.code == ofp.OFPBRC_EPERM, "Error code is not as expected")

class Grp100No80(base_tests.SimpleProtocol):  
  
    """When the length field in the header of the stats request is wrong , 
    switch generates an OFPT_ERROR msg with type field OFPET BAD_REQUEST 
    and code field OFPBRC_BAD_LEN
    """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp100No80 BadRequestBadLength test")
        #In Message module at pack time the length is computed
        #avoid this by using cstruct module
        logging.info("Sending barrier_request message..")
        stats_request = message.barrier_request()
        header=ofp.ofp_header() 
        header.type = ofp.OFPT_BARRIER_REQUEST
        # normal the header length is 12bytes changed it to 18bytes
        header.length=5;
        packed=header.pack()+stats_request.pack()
        sleep(2)
        rv=self.controller.message_send(packed)
        sleep(2)
        self.assertTrue(rv != -1,"Unable to send the message")
        logging.info("Waiting for OFPT_ERROR message..")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=10)
        self.assertTrue(response is not None, 
                               'Switch did not reply with an error message')
        self.assertTrue(response.type==ofp.OFPET_BAD_REQUEST, 
                               'Error type is not OFPET_BAD_REQUEST') 
        self.assertTrue(response.code==ofp.OFPBRC_BAD_LEN, 
                               'Error code is not OFPBRC_BAD_LEN got {0}'.format(response.code))   

class Grp100No90(base_tests.SimpleDataPlane):
    """
    Specified buffer is empty. 

    When the buffer specified by the controller is empty , the switch
    replies back with OFPT_ERROR msg with type fiels OFPET_BAD_REQUEST

    """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp100No90 BadRequestBufferUnknown test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
 
        #Setting the max_len parameter
        pkt=simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        self.assertTrue(match is not None, "Could not generate flow match from pkt")
        flow_mod_msg = message.flow_mod()
        flow_mod_msg.match = match
        flow_mod_msg.command = ofp.OFPFC_ADD
        act=action.action_output()       
        act.port = ofp.OFPP_CONTROLLER
        act.max_len = 128
        logging.info("Sending flow_mod message..")
        self.assertTrue(flow_mod_msg.actions.add(act), 'Could not add action to msg')

        logging.info("PacketOut to: " + str(of_ports[1]))
        rv = self.controller.message_send(flow_mod_msg)
        self.assertTrue(rv == 0, "Error sending out message")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
      
        #Sending a big packet to create a buffer
        pkt = simple_tcp_packet(pktlen=400,ip_dst="192.168.0.2")
        data_len = len(pkt)

        self.dataplane.send(of_ports[1], str(pkt))
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_PACKET_IN,
                                               timeout=5)

        if response.buffer_id == 0xffffffff:
            logging.info("Device was unable to buffer packet.")
            self.assertEqual(data_len, len(response.data), "PacketIn data field was not equal to original packet. Expected {0}, received {1}".format(data_len, len(response.data)))
            return
       
        #Creating packet out to clear the buffer 
        msg = message.packet_out()
        msg.buffer_id = response.buffer_id
        msg.in_port = ofp.OFPP_CONTROLLER  
        act = action.action_output()
        act.port = of_ports[2]
        self.assertTrue(msg.actions.add(act), 'Could not add action to msg')
        logging.info("PacketOut to: " + str(of_ports[2]))
        rv1 = self.controller.message_send(msg)
        self.assertTrue(rv1 == 0, "Error sending out message")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        #Verifying packet out message recieved on the expected dataplane port. 
        (of_port, pkt, pkt_time) = self.dataplane.poll(port_number=of_ports[2],
                                                             timeout=5)
        self.assertTrue(pkt is not None, 'Packet not received')
        
        #Creating packet out to generate the buffer 
        msg1 = message.packet_out()
        msg1.buffer_id = response.buffer_id
        msg1.in_port = ofp.OFPP_CONTROLLER  
        act1 = action.action_output()
        act1.port = of_ports[2]
        self.assertTrue(msg1.actions.add(act1), 'Could not add action to msg')
        logging.info("PacketOut to: " + str(of_ports[2]))
        rv1 = self.controller.message_send(msg1)
        self.assertTrue(rv1 == 0, "Error sending out message")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        #Sending the packet out second time to generate Buffer Empty message
        logging.info("Waiting for OFPT_ERROR message...")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,
                                               timeout=5)
        self.assertTrue(response is not None,
                                'Switch did not reply with error messge')
        self.assertTrue(response.type==ofp.OFPET_BAD_REQUEST,
                               'Message field type is not OFPET_BAD_REQUEST')
        self.assertTrue(response.code==ofp.OFPBRC_BUFFER_EMPTY or response.code==ofp.OFPBRC_BUFFER_UNKNOWN,
                               'Message field code is not OFPBRC_BUFFER_EMPTY')

class Grp100No100(base_tests.SimpleProtocol):
    """
    Specified buffer does not exist. 

    When the buffer specified by the controller does not exit , the switch
    replies back with OFPT_ERROR msg with type fiels OFPET_BAD_REQUEST

    """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp100No100 BadRequestBufferUnknown test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        msg = message.packet_out()
        msg.in_port = ofp.OFPP_CONTROLLER
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


class Grp100No110(base_tests.SimpleDataPlane): 

    """When the type field in the action header specified by the controller is unknown , 
    the switch generates an OFPT_ERROR msg with type field OFPBET_BAD_ACTION and code field OFPBAC_BAD_TYPE
    """
    @wireshark_capture
    def runTest(self):  
        logging = get_logger()
        logging.info("Running Grp100No110 test")
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


class Grp100No120(base_tests.SimpleDataPlane):   
    """When the length field in the action header specified by the controller is wrong ,
    the switch replies back with an OFPT_ERROR msg with Type Field OFPBAC_BAD_LEN"""
    
    @wireshark_capture
    def runTest(self):  
        logging = get_logger()
        logging.info("Running Grp100No120 BadActionBadLen test")
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



class Grp100No150(base_tests.SimpleProtocol):
    
    """When the output to switch port action refers to a port that does not exit ,
    the switch generates an OFPT_ERROR msg , with type field OFPT_BAD_ACTION and code field OFPBAC_BAD_OUT_PORT
    
    Some switches may generate an OFPT_ERROR , with error type  FLOW_MOD_FAILED and error code OFPFMFC_EPERM
    (this is also acceptable)
    """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp100No150 BadActionBadPort test")

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

        (res, raw) = self.controller.poll(ofp.OFPT_ERROR, timeout=10)
        self.assertTrue(res is not None,"Did not receive an error")
        self.assertTrue(res.type==ofp.OFPET_BAD_ACTION or res.type==ofp.OFPET_FLOW_MOD_FAILED,"Unexpected Error type. Expected ofp.OFPET_BAD_ACTION | ofp.OFPET_FLOW_MOD_FAILED error type. Got {0}".format(res.type))
        if res.type == ofp.OFPET_BAD_ACTION:
            self.assertTrue(res.code == ofp.OFPBAC_BAD_OUT_PORT," Unexpected error code, Expected ofp.OFPBAC_BAD_OUT_PORT, got {0}".format(res.type))
        elif res.type == ofp.OFPET_FLOW_MOD_FAILED:
            self.assertTrue(res.code == ofp.OFPFMFC_EPERM," Unexpected error code, Expected ofp.OFPFMFC_EPERM, got {0}".format(res.type))
        else:
            print "This shouldn't have happened."


class Grp100No160(base_tests.SimpleProtocol):
    """
    Bad action argument.

    If the arguments specified in the action are wrong,
    then the switch reponds back with an OFPT_ERROR msg
    with type field OFPT_BAD_ACTION and code field OFPBAC_BAD_ARGUMENT

    Error code OFPBAC_EPERM error is also acceptable
    """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp100No160 BadActionBadArgument test")

        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        of_ports=config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports)>1, "not enough ports for test")


        # flow with modifed arguments
        flow_mod_msg = message.flow_mod()
        flow_mod_msg.match.in_port = of_ports[0]
        flow_mod_msg.match.wildcards = ofp.OFPFW_ALL^ofp.OFPFW_DL_SRC
        act = action.action_set_vlan_vid()
        act.type = ofp.OFPAT_SET_VLAN_VID
        act.len = 8 
        act.port = of_ports[1]
        act.vlan_vid = 5000 # incorrect vid 
        act.pad = [0, 0]
        self.assertTrue(flow_mod_msg.actions.add(act), "Could not add action")

        rv = self.controller.message_send(flow_mod_msg.pack())
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        (response, raw) = self.controller.poll(ofp.OFPT_ERROR, timeout=10)
        self.assertTrue(response is not None,"Did not receive an error")
        self.assertTrue(response.type==ofp.OFPET_BAD_ACTION,"Unexpected Error type {0}. Expected OFPET_BAD_ACTION error type" .format(response.type))
        self.assertTrue(response.code==ofp.OFPBAC_BAD_ARGUMENT or response.code == ofp.OFPBAC_EPERM," Unexpected error code, Expected ofp.OFPBAC_BAD_ARGUMENT or ofp.OFPBAC_EPERM error code got {0}" .format(response.code))
        

class Grp100No180(base_tests.SimpleProtocol):
    """
    If the actions specified by the controller are more than that
    switch can support, the switch responds back with an OFPT_ERROR msg,
    with type field OFPT_BAD_ACTION and code field OFPBAC_TOO_MANY
    """

    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running BadActionTooMany Grp100No180 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")
        self.assertEqual(do_barrier(self.controller),0, "Barrier Failed")

        #Create flow_mod message with lot of actions
        flow_mod_msg = message.flow_mod()
        flow_mod_msg.match.in_port=of_ports[0]
        # add a lot of actions
        no = 1500
        for i in range(2, no):
            act1 = action.action_set_vlan_vid()
            act1.vlan_vid=i
            self.assertTrue(flow_mod_msg.actions.add(act1), "Could not add action")
            act = action.action_output()
            act.port = of_ports[1]
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
                               'Error type is not OFPET_BAD_ACTION got {0}' .format(response.type))
        self.assertTrue(response.code==ofp.OFPBAC_TOO_MANY,
                               'Error code is not OFPBAC_TOO_MANY')



class Grp100No190(base_tests.SimpleDataPlane):
    """
    If the switch is not able to process the Enqueue action specified by the controller then 
    the switch should generate an OFPT_ERROR msg ,type field OFPT_BAD_ACTION and code field OFPBAC_BAD_QUEUE"""
   
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running BadActionQueue Grp100No190 test")

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
        act.queue_id = 4294967290  #Invalid queue_id
        self.assertTrue(request.actions.add(act), "Could not add action")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        count = 0
        logging.info("Waiting for OFPT_ERROR message...")
        
        (response, raw) = self.controller.poll(ofp.OFPT_ERROR, timeout=10)
        self.assertTrue(response is not None,"Did not receive an error")
        self.assertTrue(response.type==ofp.OFPET_BAD_ACTION,"Unexpected Error type. Expected OFPET_BAD_ACTION error type")
        self.assertTrue(response.code==ofp.OFPBAC_BAD_QUEUE," Unexpected error code, Expected ofp.OFPBAC_BAD_QUEUE error code")
       



class Grp100No210(base_tests.SimpleDataPlane):
    
    """Verify that if overlap check flag is set in the flow entry and an
        overlapping flow is inserted then an error 
        type OFPET_FLOW_MOD_FAILED code OFPFMFC_OVERLAP"""
    
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running FlowModFailedOverlap Grp100No210 test")
       
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


class Grp100No230(base_tests.SimpleProtocol): 

    """When the emergency flows are added by the controller they should have a zero idle/hard timeout.
        Otherwise , should switch should respond with an OFPT ERROR msg , 
        type field OFPET_FLOW_MOD_FAILED, code field OFPFMFC_BAD_EMERG_TIMEOUT"""

    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running FlowModFailedBadEmer Grp100No230 test")
        
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
                               'Error type is not flow mod failed, got {0}'.format(response.type)) 
        self.assertTrue(response.code==ofp.OFPFMFC_BAD_EMERG_TIMEOUT, 
                               'Error code is not bad emergency timeout, got {0}'.format(response.code))


class Grp100No240(base_tests.SimpleProtocol):   
    """
    Unknown command.
    When the flow_mod msg request is sent by the controller with 
    some invalid command , the switch responds with an OFPT_ERROR msg , 
    type field OFPET_FLOW_MOD_FAILED and code field OFPFMFC_BAD_COMMAND """
    
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running FlowModFailedBadCommand Grp100No240 test")
        msg = message.flow_mod()
        msg.match.in_port = 1
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
                               'Error code is not OFPFMFC_BAD_COMMAND got {0}' .format(response.code))


class Grp100No250(base_tests.SimpleProtocol):   
    """
    Unsupported action list - cannot process in order specified
    If a switch cannot process the action list for any  flow mod message in the order specied, 
    it must return an Error with error.type OFPET_FLOW_MOD_FAILED and error.code OFPFMFC_UNSUPPORTED or OFPFMFC_EPERM error and reject the flow """
    
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
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
          
       
        (response, raw) = self.controller.poll(ofp.OFPT_ERROR, timeout=10)
        self.assertTrue(response is not None,"Did not receive an error")
        self.assertTrue(response.type==ofp.OFPET_FLOW_MOD_FAILED,"Unexpected Error type. Expected OFPET_FLOW_MOD_FAILED error type")
        self.assertTrue(response.code==ofp.OFPFMFC_UNSUPPORTED or response.code==ofp.OFPFMFC_EPERM," Unexpected error code, Expected ofp.OFPFMFC_UNSUPPORTED or ofp.OFPFMFC_EPERM error code got{0}" .format(response.code))
       
       

class Grp100No260(base_tests.SimpleProtocol):
    """
    Modify a bit in port config on an invalid port and verify
    error message is received.
    """

    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running PortModFailedBadPort Grp100No260 test")
        
        # pick a random bad port number
        bad_port=ofp.OFPP_MAX
        rv = port_config_set(self.controller, bad_port,
                             ofp.OFPPC_NO_FLOOD, ofp.OFPPC_NO_FLOOD)
        self.assertTrue(rv != -1, "Error sending port mod")

        # poll for error message
        (response, raw) = self.controller.poll(ofp.OFPT_ERROR, timeout=10)
        self.assertTrue(response is not None,"Did not receive an error")
        self.assertTrue(response.type==ofp.OFPET_PORT_MOD_FAILED,"Unexpected Error type. Expected OFPET_PORT_MOD_FAILED error type")
        self.assertTrue(response.code==ofp.OFPPMFC_BAD_PORT," Unexpected error code, Expected OFPPMFC_BAD_PORT error code")
       


class Grp100No270(base_tests.SimpleProtocol):    
    """If the controller sends a port_mod request for any port  with a hardware address that is different 
    from one returned in ofp_phy_port struct.,the switch will respond back with an OFPT_ERROR msg , 
    type field OFPET_PORT_MOD_FAILED and code field OFPPMFC_BAD_HW_ADDR
    """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running PortModFailedBadHwAdd Grp100No270 test")

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
        (response, raw) = self.controller.poll(ofp.OFPT_ERROR, timeout=10)
        self.assertTrue(response is not None,"Did not receive an error")
        self.assertTrue(response.type==ofp.OFPET_PORT_MOD_FAILED,"Unexpected Error type. Expected OFPET_PORT_MOD_FAILED error type")
        self.assertTrue(response.code==ofp.OFPPMFC_BAD_HW_ADDR," Unexpected error code, Expected OFPPMFC_BAD_HW_ADDR error code")

       

class Grp100No280(base_tests.SimpleDataPlane):

    """If the port specifed for any queue operation (like enqeue --output to queue or retrieving queue stats )
     is an invalid port , then the switch responds back with an error msg OFPT_ERROR msg , 
     type field OFPET_QUEUE_OP_FAILED , code field OFPQOFC_BAD_PORT"""
    
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp100No280 QueueOpFailedBadPort test")

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

        (response, raw) = self.controller.poll(ofp.OFPT_ERROR, timeout=10)
        self.assertTrue(response is not None,"Did not receive an error")
        self.assertTrue(response.type==ofp.OFPET_QUEUE_OP_FAILED,"Unexpected Error type. Expected OFPET_QUEUE_OP_FAILED error type")
        self.assertTrue(response.code==ofp.OFPQOFC_BAD_PORT, " Unexpected error code, Expected OFPQOFC_BAD_PORT error code")




class Grp100No290(base_tests.SimpleDataPlane):

    """If the queue_id specifed for any queue operation (like enqeue --output to queue or retrieving queue stats ) 
    is an invalid queue ,then the switch responds back with an error msg OFPT_ERROR msg , 
    type field OFPET_QUEUE_OP_FAILED , code field OFPQOFC_BAD_QUEUE"""
    
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running QueueOpFailedBadQueue Grp100No290 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        logging.info("Sending queue_stats request ..")
        request = message.queue_stats_request()
        request.port_no  = of_ports[0]
        request.queue_id = 4294967290 #Invalid queue_id
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1,"Unable to send the message")

        logging.info("Waiting for OFPT_ERROR message...")
        (response, raw) = self.controller.poll(ofp.OFPT_ERROR, timeout=10)
        self.assertTrue(response is not None,"Did not receive an error")
        self.assertTrue(response.type==ofp.OFPET_QUEUE_OP_FAILED,"Unexpected Error type. Expected OFPET_QUEUE_OP_FAILED error type")
        self.assertTrue(response.code==ofp.OFPQOFC_BAD_QUEUE," Unexpected error code, Expected OFPQOFC_BAD_QUEUE error code")
                
    
                










