"""
These tests fall under Conformance Test-Suite (OF-SWITCH-1.0.0 TestCases).
Refer Documentation -- Detailed testing methodology 
    <Some of test-cases are directly taken from oftest> """

"Test Suite 1 --> Basic Sanity Tests"


import time
import sys
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
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        #Shutdown the control channel
        self.controller.shutdown()
        
        # Keep sending the packets till the control plane gets shutdown
        pkt = simple_tcp_packet()
        try :
            for x in range (0,20) :
                self.dataplane.send(ingress_port, str(pkt))
                yes_ports=set(of_ports)
                no_ports = []
                receive_pkt_check(self.dataplane,pkt,yes_ports,no_ports,self)

        finally : 
        
            #Send a simple tcp packet on ingress_port
            logging.info("Sending simple tcp packet ...")
            self.dataplane.send(ingress_port, str(pkt))
        
            #Verify packet_in should be not generated 
            logging.info("No packet_in should be generated")
            (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN, timeout=10)
            self.assertTrue(response is None,
                         'PacketIn is generated')

            #Verify dataplane packet should not be forwarded
            logging.info("Packet should not be forwarded to any dataplane port")
            no_ports=set(of_ports)
            yes_ports=[]
            receive_pkt_check(self.dataplane,pkt,yes_ports,no_ports,self)


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
        (response, pkt) = self.controller.transact(request)
        self.assertEqual(response.header.type, ofp.OFPT_ECHO_REPLY,'response is not echo_reply')
        self.assertEqual(request.header.xid, response.header.xid,
                         'response xid != request xid')
        self.assertTrue(response.header.version == 0x01, 'switch openflow-version field is not 1.0.1')
        self.assertEqual(len(response.data), 0, 'response data non-empty')

        logging.info("Configured host : " + str(config["controller_host"]) + "Configured port : " + str(config["controller_port"]))

class Grp10No60(base_tests.SimpleDataPlane):
    """
    Verify HELLO response has proper openflow version reported.
    
    @of_version can be passed from command line , default is 0x01
    """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running TestNo60 Version Announcement test")
        
        of_version = test_param_get('version',default = 0x01)
        request = message.hello()  
        rv = self.controller.message_send(request)  
        self.assertTrue(rv != -1, "Error sending Hello message")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_HELLO,         
                                               timeout=5)
        self.assertTrue(response is not None, 
                               'Switch did not exchange hello message in return') 
        self.assertTrue(response.header.version == of_version, 'switch openflow-version field is not 1.0.0') 


class Grp10No70(base_tests.SimpleProtocol):
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
        #logging.info("Connected " + str(self.controller.switch_addr))
        
    @wireshark_capture 
    def runTest(self):
        logging = get_logger()

        logging.info("Running TestNo70 VersionNegotiation Test") 
        of_version = test_param_get('version',default = 0x01)               
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_HELLO,         
                                               timeout=5)
        request = message.hello()                                               
        logging.info("Change hello message version to 2 and send it to control plane")
        request.header.version=2
        rv = self.controller.message_send(request)      
          
        logging.info("Verify switch does not generate an error")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=5)
                
        self.assertTrue(response is None, 
                               'Switch did not negotiate on the version')  


class Grp10No80(base_tests.SimpleProtocol):
    """
    No common version negotiated
    Verify the switch reports correct error message and terminates the connection, 
    if no common version can be negotiated
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
        #logging.info("Connected " + str(self.controller.switch_addr))
        
    @wireshark_capture    
    def runTest(self):
        logging = get_logger()

        logging.info("Running TestNo80 No Common Version Test")                
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_HELLO,         
                                               timeout=5)
        request = message.hello()                                               
        logging.info("Change hello message version to 0 and send it to control plane")
        request.header.version=0
        rv = self.controller.message_send(request)      
          
        logging.info("Expecting OFPT_ERROR message")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=5)
                
        self.assertTrue(response is not None, 
                               'Switch did not reply with error message') 
        self.assertTrue(response.type==ofp.OFPET_HELLO_FAILED, 
                               'Message field type is not HELLO_FAILED') 
        self.assertTrue(response.code==ofp.OFPHFC_INCOMPATIBLE, 
                        'Message field code is not OFPHFC_INCOMPATIBLE')        


class Grp10No90(unittest.TestCase):
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

        # By default, respond to echo requests
        self.controller.keep_alive = False
        if not self.controller.active:
            raise Exception("Controller startup failed")
        if self.controller.switch_addr is None: 
            raise Exception("Controller startup failed (no switch addr)")
        #logging.info("Connected " + str(self.controller.switch_addr))
    
    def tearDown(self):
        #logging.info("** END TEST CASE " + str(self))
        self.controller.shutdown()
        if self.clean_shutdown:
            self.controller.join()    
    
    @wireshark_capture    
    def runTest(self):
        logging = get_logger()

        logging.info("Running TestNo90 EchoTimeout ")
        sleep(10)
        # When the switch loses control channel , it starts retries for control channel connection by sending Hello messages
        # Polling for Hello Messages 
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_HELLO,
                                               timeout=30)
        self.assertTrue(response is not None, 
                               'Switch did not Lose connection due to Echo timeouts') 


class Grp10No120(base_tests.SimpleDataPlane):
    """
    If the switch supports Emergency-Mode,
    then verify 
    1. Emergency mode removes standard flow entries after the control channel disconnection
    """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()

        logging.info("Running TestNo120 EmergencyMode test ") 

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 0, "Not enough ports for test")
        
        #Clear switch state
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        rv = delete_all_flows_emer(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")
        
        #Insert any standard flow entry 
        (pkt,match) = wildcard_all_except_ingress(self,of_ports)

        # Send Table_Stats_Request and verify flow gets inserted.
        verify_tablestats(self,expect_active=1)

        #Shutdown the controller 
        self.controller.shutdown()
        sleep(15)
        # Remove sleep and send continous packets to verify control channel disconnection

        #Send matching packet 
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet does not implement the action specified in the flow
        yes_ports=[]
        no_ports = set(of_ports)
        receive_pkt_check(self.dataplane,pkt,yes_ports,no_ports,self)


class Grp10No140(base_tests.SimpleDataPlane):
    """
    If the switch supports Emergency-Mode,
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
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
            
        #Shutdown the controller 
        self.controller.shutdown()
        sleep(15) #For connection retries from the switch to exhaust 

        #Send matching packet 
        self.dataplane.send(of_ports[0], str(test_packet))

        #Verify packet implements the action specified in the emergency flow
        egress_port = of_ports[1]
        yes_ports=[egress_port]
        no_ports = set(of_ports).difference(yes_ports)
        receive_pkt_check(self.dataplane,test_packet,yes_ports,no_ports,self)


class Grp10No150(base_tests.SimpleDataPlane):
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
        msg.hard_timeout = 25       
        act = action.action_output()
        act.port = of_ports[1]
        self.assertTrue(msg.actions.add(act), "could not add action")

        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        # Send Table_Stats_Request and verify flow gets inserted.
        verify_tablestats(self,expect_active=1)

        #Shutdown the controller 
        self.controller.shutdown()
        sleep(15)

        #TBD remove sleeps with continous packet sending 

        #Send matching packet 
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet implements the action specified in the flow
        egress_port = of_ports[1]
        yes_ports=[egress_port]
        no_ports = set(of_ports).difference([egress_port])
        receive_pkt_check(self.dataplane,pkt,yes_ports,no_ports,self)

        #Sleeping for flow to timeout 
        sleep(10)

        #Send matching packet 
        self.dataplane.send(of_ports[0], str(pkt))

        #Verify packet does not implement the action specified in the flow
        #flow should have timed out
        egress_port = of_ports[1]
        yes_ports=[]
        no_ports = set(of_ports)
        receive_pkt_check(self.dataplane,pkt,yes_ports,no_ports,self)
