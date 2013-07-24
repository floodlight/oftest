"""
These tests fall under Conformance Test-Suite (OF-SWITCH-1.0.0 TestCases).
Refer Documentation -- Detailed testing methodology 
    <Some of test-cases are directly taken from oftest> """

"Test Suite 1 --> Basic Sanity Tests"


import time
import sys

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
import oftest.illegal_message as illegal_message

from oftest.oflog import *
from oftest.testutils import *
from time import sleep
from FuncUtils import *

class Grp10No10(base_tests.SimpleDataPlane):
    """
    Switch Startup behaviour without estabilished control channel. 
    Make sure no dataplane packets are forwarded (since there are no flows)
    i.e switch does not behave like a learning switch
    """

    @wireshark_capture
    def runTest(self):
        
        logging = get_logger()
        logging.info("Running TestNo10 SwStartup test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        ingress_port=of_ports[0]

        #Clear Switch State
        logging.info("Clearing all flows from the switch")
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        #Shutdown the control channel
        logging.info("Shutting Down the Controller")
        self.controller.shutdown()
        
        # Keep sending the packets till the control plane gets shutdown

        pkt = simple_tcp_packet()
        
        assertionerr = False
        logging.info("Checking for Control channel connection status")

        try :
            for x in range(15):
        	self.dataplane.send(ingress_port, str(pkt))
                (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN, timeout=5)
                self.assertTrue(response is not None,
                                'PacketIn is not generated--Control plane is down')
        
        except AssertionError :
        
            #Send a simple tcp packet on ingress_port
            logging.info("Control  Channel Connection not present")
            logging.info("Sending simple tcp packet ...")
            self.dataplane.send(ingress_port, str(pkt))
        

            #Verify dataplane packet should not be forwarded
            logging.info("Packet should not be forwarded to any dataplane port")
            no_ports=set(of_ports)
            yes_ports=[]
            receive_pkt_check(self.dataplane,pkt,yes_ports,no_ports,self)
            assertionerr = True
        
        else :

            self.assertTrue(assertionerr is True, "Failed to shutdown the control plane")
            
      
	

class Grp10No20(base_tests.SimpleProtocol):
    """
    Configure control channel on switch

    @ controller_host = Host specified in the command line , default 127.0.0.1
    @ controller_port = Tcp port number specified in the command line, default 6633
    Note : If tcp port is other than 6633, make sure sw is also configured to listen on the alternate port
    """
    
    @wireshark_capture
    def runTest(self):
        # Send echo_request to verify connection
        logging = get_logger()
        logging.info("Running TestNo20 UserConfigPort test")

        request = message.echo_request()
        logging.info("Sending an Echo request message")
        (response, pkt) = self.controller.transact(request)
        self.assertEqual(response.header.type, ofp.OFPT_ECHO_REPLY,'response is not echo_reply')
        logging.info("Received message type is echo_reply")
        self.assertEqual(request.header.xid, response.header.xid,
                         'response xid != request xid')
        self.assertTrue(response.header.version == 0x01, 'switch openflow-version field is not 1.0')
        logging.info("Configured host : " + str(config["controller_host"]) + "Configured port : " + str(config["controller_port"]))


class Grp10No30(base_tests.SimpleDataPlane):
    """
    Verify HELLO has proper openflow version reported.
    
    @of_version can be passed from command line , default is 0x01
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

    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Test Grp10No30 Version Announcement test")
        of_version = test_param_get('version',default = 0x01)
        
        # Waiting for switch to send Hello . Initial Hello from our side is set to False.
        # TBD: What if switch does not send Hello for the first time ?
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_HELLO,         
                                               timeout=5)
        self.assertTrue(response is not None, 
                               'Switch did not exchange hello message in return')
        logging.info("Received a Hello message from the Switch") 
        self.assertTrue(response.header.version == of_version, 'switch openflow-version field is not correct') 
        logging.info("The Switch reported the correct openflow version")

class Grp10No40(base_tests.SimpleProtocol):
    """
    Verify switch negotiates on the correct version.
    Upon receipt of the Hello message, the recipient may calculate the OpenFlow protocol version
    to be used as the smaller of the version number that it sent and the one that it received. 

    """
    def setUp(self):
        #This is almost same as setUp in SimpleProtcocol except that intial hello is set to false
        self.controller = controller.Controller(
            host=config["controller_host"],
            port=config["controller_port"])
        # clean_shutdown should be set to False to force quit app
        self.clean_shutdown = True
        #set initial hello to False
        self.controller.initial_hello=False
        self.controller.start()
        #@todo Add an option to wait for a pkt transaction to ensure version
        # compatibilty?
        self.controller.connect(timeout=20)
        # By default, respond to echo requests
        self.controller.keep_alive = True
        if not self.controller.active:
            raise Exception("Controller startup failed")
        if self.controller.switch_addr is None: 
            raise Exception("Controller startup failed (no switch addr)")
        logging.info("Connected " + str(self.controller.switch_addr))
        
    @wireshark_capture 
    def runTest(self):
        logging = get_logger()

        logging.info("Running TestNo40 VersionNegotiation Test") 
        of_version = test_param_get('version',default = 0x01)               
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_HELLO,         
                                               timeout=5)
        request = message.hello()                                               
        request.header.version=2
        rv = self.controller.message_send(request)      
          
        logging.info("Verifying switch does not generate an error message for a hello message with different version type")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=5)
        self.assertTrue(response is None, 
                               'Switch did not negotiate on the version')  


class Grp10No50(base_tests.SimpleProtocol):
    """
    No common version negotiated
    Verify the switch reports correct error message and terminates the connection, 
    if no common version can be negotiated
    """
    def setUp(self):
        #This is almost same as setUp in SimpleProtcocol except that intial hello is set to false
        self.controller = controller.Controller(
            host=config["controller_host"],
        # clean_shutdown should be set to False to force quit app
            port=config["controller_port"])
        self.clean_shutdown = True
        #set initial hello to False
        self.controller.initial_hello=False
        self.controller.start()
        #@todo Add an option to wait for a pkt transaction to ensure version
        # compatibilty?
        self.controller.connect(timeout=20)

        # By default, respond to echo requests
        self.controller.keep_alive = True
        if not self.controller.active:
            raise Exception("Controller startup failed")
        if self.controller.switch_addr is None: 
            raise Exception("Controller startup failed (no switch addr)")
        #logging.info("Connected " + str(self.controller.switch_addr))
        
    @wireshark_capture    
    def runTest(self):
        logging = get_logger()

        logging.info("Running TestNo50 No Common Version Test")                
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_HELLO,         
                                               timeout=5)
        request = message.hello()                                               
        logging.info("Changing hello message version to 0 and sending it to control plane")
        request.header.version=0
        rv = self.controller.message_send(request)      
          
        logging.info("Expecting OFPT_ERROR message")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=5)
                
        self.assertTrue(response is not None, 
                               'Switch did not reply with error message')
        logging.info("Error message received") 
        self.assertTrue(response.type==ofp.OFPET_HELLO_FAILED, 
                               'Message field type is not HELLO_FAILED')
        logging.info("Received message is of type HELLO_FAILED") 
        self.assertTrue(response.code==ofp.OFPHFC_INCOMPATIBLE, 
                        'Message field code is not OFPHFC_INCOMPATIBLE')        


class Grp10No80(base_tests.SimpleProtocol):
    """
    Verify Echo timeout causes connection to the controller to drop
    """ 
    def setUp(self):

        #This is almost same as setUp in SimpleProtcocol except that Echo response is set to false
        self.controller = controller.Controller(
            host=config["controller_host"],
            port=config["controller_port"])
        # clean_shutdown should be set to False to force quit app
        self.clean_shutdown = False
        self.controller.initial_hello=True
        self.controller.start()
        #@todo Add an option to wait for a pkt transaction to ensure version
        # compatibilty?
        self.controller.connect(timeout=20)
        # Here, Echo response is set to False, this would trigger connection to drop and hence switch will 
        # start sending Hello messages to start a new connection
        self.controller.keep_alive = False
        if not self.controller.active:
            raise Exception("Controller startup failed")
        if self.controller.switch_addr is None: 
            raise Exception("Controller startup failed (no switch addr)")
        logging.info("Connected " + str(self.controller.switch_addr))
    
    def tearDown(self):
        logging.info("** END TEST CASE " + str(self))
        self.controller.shutdown()
        if self.clean_shutdown:
            self.controller.join()    
    @wireshark_capture    
    def runTest(self):
        logging = get_logger()
        logging.info("Running TestNo80 EchoTimeout ")
        # When the switch loses control channel , it would start retries for control channel connection by sending Hello messages
        # Hence , Polling for Echo request and then Hello Messages to verify control channel disconnection
    	(response0, pkt0) = self.controller.poll(exp_msg=ofp.OFPT_HELLO,
                                               timeout=1)
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ECHO_REQUEST,
                                               timeout=20)
        self.assertTrue(response is not None, 
                               'Switch is not generating Echo-Requests') 
        logging.info("Received an Echo request, waiting for echo timeout")
        (response1, pkt1) = self.controller.poll(exp_msg=ofp.OFPT_HELLO,
                                               timeout=20)
        self.assertTrue(response1 is not None, 
                               'Switch did not drop connection due to Echo Timeout') 
        logging.info("Received an OFPT_HELLO message after echo timeout")

class Grp10No110(base_tests.SimpleDataPlane):
    """
    Verify if the emergency flows stay even after control channel reconencts
    Testcase unstable framework issues.
    """
   
    @wireshark_capture
    def runTest(self):
        logging = get_logger()

        logging.info("Running Grp10No110 test ") 

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 0, "Not enough ports for test")

        #Clear switch state
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")
        rc = delete_all_flows_emer(self.controller) 
        self.assertEqual(rc, 0, "Failed to send delete-emergency flow")
        
        response, pkt = self.controller.poll(ofp.OFPT_ERROR, timeout=5)
        self.assertTrue(response is None, "Emergency flow cannot be deleted: Check if the Switch supports Emergency Mode")

        #Insert an emergency flow entry 
        test_packet = simple_tcp_packet()
        match = parse.packet_to_flow_match(test_packet)
        e_flow_mod = message.flow_mod()
        match = parse.packet_to_flow_match(test_packet)
        e_flow_mod.match = match
        e_flow_mod.flags = e_flow_mod.flags | ofp.OFPFF_EMERG
        e_flow_mod.in_port = of_ports[0]
        act = action.action_output()
        act.port = of_ports[1]
        self.assertTrue(e_flow_mod.actions.add(act), "Failed to add action")
        
        rv = self.controller.message_send(e_flow_mod)
        response=None
        response, pkt = self.controller.poll(ofp.OFPT_ERROR, timeout=5)
        self.assertTrue(response is None, "Unable to add emergency flows")
        self.assertTrue(rv != -1, "Unable to send a flow_mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
            
        #Shutdown the controller 
        self.controller.initial_hello = False
        self.controller.disconnect()
        #waiting for the switch to recognize the connection drop.
        sleep(2)
        
        assertionerr=False
        
        pkt=simple_tcp_packet()
        logging.info("checking for control channel status")
        try :
            for x in range(15):
                logging.info("Sending an unmatched packet")
                self.dataplane.send(of_ports[1], str(pkt))
                (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN, timeout=10)
                self.assertTrue(response is not None,
                                'PacketIn is not generated--Control plane is down')	
        except AssertionError :
        
          #Send a simple tcp packet on ingress_port
          logging.info("Control channel is down")
          logging.info("Sending simple tcp packet ...")
          logging.info("Checking for Emergency flows status after controller shutdown")
          self.dataplane.send(of_ports[0], str(test_packet))

          #Verify dataplane packet should not be forwarded
          
          yes_ports=[of_ports[1]]
          no_ports = set(of_ports).difference(yes_ports)
          receive_pkt_check(self.dataplane,test_packet,yes_ports,no_ports,self)
          logging.info("Emergency flows are active after control channel is disconnected")
          assertionerr = True	
        
        else :
	       self.assertTrue(assertionerr is True, "Failed to shutdown the control plane")

        self.controller.initial_hello=True
        self.controller.connect()
        sleep(3)
        features = message.features_request()
        rv = self.controller.message_send(features)
       # for i in range(10):
       # sleep(2)
        (response, raw) = self.controller.poll(ofp.OFPT_FEATURES_REPLY, timeout=5)
       
        self.assertTrue(response is not None, "Control channel connection could not be established")
        
        logging.info("Control channel is up")
        logging.info("Sending simple tcp packet ...")
        logging.info("Checking for Emergency flows status after controller reconnection")
        self.dataplane.send(of_ports[0], str(test_packet))

        #Verify dataplane packet should not be forwarded
        yes_ports=[of_ports[1]]
        no_ports = set(of_ports).difference(yes_ports)
        receive_pkt_check(self.dataplane,test_packet,yes_ports,no_ports,self)
        logging.info("Emergency flows are active after control channel is reconnected")
        
        logging.info("Cleaning up emergency flows")
        rc = delete_all_flows_emer(self.controller) 
        self.assertEqual(rc, 0, "Failed to send delete-emergency flow")
        res, pkt = self.controller.poll(ofp.OFPT_ERROR, timeout=5)
        self.assertTrue(res is None, "Emergency flows could not be deleted.")



class Grp10No100(base_tests.SimpleDataPlane):

    """
    If the switch supports Emergency-Mode,
    then verify 
    1. Emergency mode removes standard flow entries after the control channel disconnection
    """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        (response, pkt)=self.controller.poll(ofp.OFPT_HELLO, timeout=15)
        self.assertTrue(response is not None, "No hello message")
        logging.info("Running TestNo120 EmergencyMode test") 

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 0, "Not enough ports for test")
        
        ingress_port=of_ports[0]
        
        #Clear switch state
        logging.info("Deleting all standard flows from the switch")
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all standard flows")
        logging.info("Deleting all emergency flows from the switch")
        rv = delete_all_flows_emer(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all emergency flows")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        #Insert any standard flow entry 
        (pkt,match) = wildcard_all_except_ingress(self,of_ports)

        #Ensure switch reports back with only one flow entry , ensure the flow entry is not some stray flow entry
        rv = all_stats_get(self)
        self.assertTrue(rv["flows"] == 1 , "Inserted one flow from our side , but there are more than one flow in the switch")
        logging.info("Sending simple tcp packet ...")
        
        self.dataplane.send(ingress_port, str(pkt))
        egress_port = of_ports[1]
        yes_ports=[egress_port]
        no_ports = set(of_ports).difference(yes_ports)
        receive_pkt_check(self.dataplane,pkt,yes_ports,no_ports,self)

        #Shutdown the controller 
        self.controller.shutdown()
        
        assertionerr=False
        
        try :
            for x in range(15):
                self.dataplane.send(of_ports[1], str(pkt))
                (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN, timeout=5)
                self.assertTrue(response is not None,
                                'PacketIn is not generated--Control plane is down')	
        except AssertionError :
        
          #Send a simple tcp packet on ingress_port
          logging.info("Sending simple tcp packet ...")
          self.dataplane.send(ingress_port, str(pkt))

          #Verify dataplane packet should not be forwarded
          logging.info("Packet should not be forwarded to any dataplane port")
          no_ports=set(of_ports)
          yes_ports=[]
          try:
          	receive_pkt_check(self.dataplane,pkt,yes_ports,no_ports,self)
          except AssertionError : 
         	self.assertTrue(0!=0, "Control channel disconnection did not delete Standard flow entries:Check if the switch supports Emergency Mode")
          assertionerr = True	
        
        else :
	       self.assertTrue(assertionerr is True, "Failed to shutdown the control plane")	          
        # Keep sending continous packets to verify standard flow entry being removed 

class Grp10No90(base_tests.SimpleDataPlane):
    """
    If the switch supports Emergency-Mode
    then verify 
    1. Emergency flows can be added , they are active after control channel gets disconnected 
    """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()

        logging.info("Running EmergencyMode2 test ") 

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 0, "Not enough ports for test")

        #Clear switch state
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")
        
        #Insert an emergency flow entry 
        test_packet = simple_tcp_packet()
        match = parse.packet_to_flow_match(test_packet)
        e_flow_mod = message.flow_mod()
        match = parse.packet_to_flow_match(test_packet)
        e_flow_mod.match = match
        e_flow_mod.flags = e_flow_mod.flags | ofp.OFPFF_EMERG
        e_flow_mod.in_port = of_ports[0]
        act = action.action_output()
        act.port = of_ports[1]
        self.assertTrue(e_flow_mod.actions.add(act), "Failed to add action")
        
        rv = self.controller.message_send(e_flow_mod)
        self.assertTrue(rv != -1, "Error Cannot Send flow_mod")
        response, pkt = self.controller.poll(ofp.OFPT_ERROR, timeout=5)
        self.assertTrue(response is None, "Unable to add emergency flows")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
            
        #Shutdown the controller 
        self.controller.shutdown()
        
        assertionerr=False
        
        pkt=simple_tcp_packet()
        logging.info("checking for control channel status")
        try :
            for x in range(15):
                self.dataplane.send(of_ports[1], str(pkt))
                (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN, timeout=15)
                self.assertTrue(response is not None,
                                'PacketIn is not generated--Control plane is down')	
        except AssertionError :
        
          #Send a simple tcp packet on ingress_port
          logging.info("Control channel is down")
          logging.info("Sending simple tcp packet ...")
          logging.info("Checking for Emergency flows status after controller shutdown")
          self.dataplane.send(of_ports[0], str(test_packet))

          #Verify dataplane packet should not be forwarded
          
          yes_ports=[of_ports[1]]
          no_ports = set(of_ports).difference(yes_ports)
          receive_pkt_check(self.dataplane,test_packet,yes_ports,no_ports,self)
          logging.info("Emergency flows are active after control channel is disconnected")
          assertionerr = True	
        
        else :
	       self.assertTrue(assertionerr is True, "Failed to shutdown the control plane")
        
        
class Grp10No120(base_tests.SimpleDataPlane):
    """If switch does not support Emergency mode , it should support fail-secure mode
    (refer spec 1.0.1).
    Verify even after the control channel disconnection, the standard flows timeout normally"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()

        logging.info("Running FailSecureMode test ") 

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 0, "Not enough ports for test")

        #Clear switch state 
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")
        
        #Insert flow entry with hard_timeout set
        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        self.assertTrue(match is not None, "Could not generate flow match from pkt")
        match.wildcards = ofp.OFPFW_ALL-ofp.OFPFW_IN_PORT
        match.in_port = of_ports[0]

        msg = message.flow_mod()
        msg.command = ofp.OFPFC_ADD
        msg.match = match
        msg.hard_timeout = 15       
        msg.buffer_id = 0xffffffff
        act = action.action_output()
        act.port = of_ports[1]
        self.assertTrue(msg.actions.add(act), "could not add action")
        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        #Ensure switch reports back with only one flow entry , ensure the flow entry is not some stray flow entry
        logging.info("Sending simple tcp packet ...")
        logging.info("Checking whether the flow we inserted is working")
        self.dataplane.send(of_ports[0], str(pkt))
        egress_port = of_ports [1]
        yes_ports=[egress_port]
        no_ports = set(of_ports).difference(yes_ports)
        receive_pkt_check(self.dataplane,pkt,yes_ports,no_ports,self)
        logging.info("The inserted standard flow is working fine")

        #Shutdown the controller 
        self.controller.shutdown()
        
        assertionerr= False
        #checking control plane connection
        logging.info("Checking for control plane connection")
        try:
            for x in range(15):
                self.dataplane.send(of_ports[1], str(pkt))
                (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN, timeout=5)
                self.assertTrue(response is not None,
                            'PacketIn not generated--Control plane is down')
        
        except AssertionError :

            logging.info("Control plane connection Disconnected")
	
            #Send matching packet 
            logging.info("sending matching packet to verify standard flows are working correctly")
            self.dataplane.send(of_ports[0], str(pkt))

            #Verify packet implements the action specified in the flow
            egress_port = of_ports[1]
            yes_ports=[egress_port]
            no_ports = set(of_ports).difference(yes_ports)
            receive_pkt_check(self.dataplane,pkt,yes_ports,no_ports,self)
            logging.info("All standard flows working fine even after control channel shutdown")
            assertionerr=True

        else :
            self.assertTrue(assertionerr is True, "Error Control Channel is Not Down")
        
        #Sleeping for flow to timeout 
        logging.info("Waiting for flows to time out")
        sleep(16)

        #Send matching packet 
        logging.info("Verifying if the standard flows have been deleted after timeout")
        logging.info("Sending simple tcp packet ...")
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet does not implement the action specified in the flow
        #flow should have timed out
        egress_port = of_ports[1]
        yes_ports=[]
        no_ports = set(of_ports)
        receive_pkt_check(self.dataplane,pkt,yes_ports,no_ports,self)
        logging.info("All the standard flows are deleted after time out")
