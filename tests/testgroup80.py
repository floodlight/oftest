"""These tests fall under Conformance Test-Suite (OF-SWITCH-1.0.0 TestCases).
    Refer Documentation -- Detailed testing methodology 
    <Some of test-cases are directly taken from oftest> """

"Test Suite 8 --> Message Types "

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
import time

from oftest.testutils import *
from time import sleep
from FuncUtils import*



class Grp80No20(base_tests.SimpleDataPlane):

    """Verify switch should be able to receive OFPT_HELLO messages with body , 
        but it should ignore the contents of the body"""

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
        
        
    def runTest(self):

        logging.info("Running Grp80No20 HelloWithBody Test")            
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_HELLO,         
                                              timeout=5)
        request = message.hello()   
        request.data = "Openflow rules the world"                                            
        rv = self.controller.message_send(request)      
        
        logging.info("Verify switch does not generate an error")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=5)
        self.assertTrue(response is None, 
                               'Switch did not ignore the body of the Hello message')  


class Grp80No30(base_tests.SimpleProtocol):

    """
    Verify OFPT_ERROR msg is implemented

    When the header in the  request msg  
    contains a version field which is not supported by the switch , 
    it generates OFPT_ERROR_msg with Type field OFPET_BAD_REQUEST 
    and code field OFPBRC_BAD_VERSION
    """
    
    def runTest(self):

        logging.info("Running Grp80No30 Error Msg test")

        #Send Echo Request
        logging.info("Sending a Echo request with a version which is not supported by the switch")
        request=message.echo_request()
        request.header.version=0  
        rv=self.controller.message_send(request)
        self.assertTrue(rv is not None,"Unable to send the message")

        logging.info("Waiting for a OFPT_ERROR msg on the control plane...") 
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=5)
        self.assertTrue(response is not None, 
                               'Switch did not reply with error message')
        self.assertTrue(response.type==ofp.OFPET_BAD_REQUEST, 
                               'Message field type is not OFPET_BAD_REQUEST') 
        self.assertTrue(response.code==ofp.OFPBRC_BAD_VERSION, 
                               'Message field code is not OFPBRC_BAD_VERSION')



class Grp80No40(base_tests.SimpleProtocol):
    
    """Verify if OFPT_ECHO_REQUEST has data field,
    switch responds back with OFPT_ECHO_REPLY with data field copied into it. """

    def runTest(self):

        logging.info("Running Grp80No40 EchoWithData test")
        
        #Send Echo Request 
        logging.info("Sending Echo With Data ...")
        request = message.echo_request()
        request.data = 'OpenFlow Will Rule The World'
        rv=self.controller.message_send(request)
        self.assertTrue(rv is not None,"Unable to send the message")

        #Verify Echo Reply is recieved 
        logging.info("Waiting for Echo Reply with data field copied from Echo Request")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ECHO_REPLY,
                                               timeout=1)
        self.assertTrue(response is not None,
                        "Did not get echo reply (with data)")
        self.assertEqual(response.header.type, ofp.OFPT_ECHO_REPLY,
                         'Response is not echo_reply')
        self.assertEqual(request.header.xid, response.header.xid,
                         'Response xid does not match the request Xid')
        self.assertEqual(request.data, response.data,
                         'Response data does not match request data')



class Grp80No60(base_tests.SimpleProtocol):
    """Verify the body of Features Reply message"""

    def runTest(self):
        
        logging.info("Running Grp80No60 Features Reply Body test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        # Sending Features_Request
        logging.info("Sending Features_Request...")
        request = message.features_request()
        (reply, pkt) = self.controller.transact(request)
        self.assertTrue(reply is not None, "Failed to get any reply")
        self.assertEqual(reply.header.type, ofp.OFPT_FEATURES_REPLY,'Response is not Features_reply')
        self.assertEqual(reply.header.xid,request.header.xid,'Transaction id does not match')
        
        supported_actions =[]
        if(reply.actions &1<<ofp.OFPAT_OUTPUT):
            supported_actions.append('OFPAT_OUTPUT')
        if(reply.actions &1<<ofp.OFPAT_SET_VLAN_VID):
            supported_actions.append('OFPAT_SET_VLAN_VID')
        if(reply.actions &1<<ofp.OFPAT_SET_VLAN_PCP):
            supported_actions.append('OFPAT_SET_VLAN_PCP')
        if(reply.actions &1<<ofp.OFPAT_STRIP_VLAN):
            supported_actions.append('OFPAT_STRIP_VLAN')
        if(reply.actions &1<<ofp.OFPAT_SET_DL_SRC):
            supported_actions.append('OFPAT_SET_DL_SRC')
        if(reply.actions &1<<ofp.OFPAT_SET_DL_DST):
            supported_actions.append('OFPAT_SET_NW_SRC')
        if(reply.actions &1<<ofp.OFPAT_SET_NW_DST):
            supported_actions.append('OFPAT_SET_NW_DST')
        if(reply.actions &1<<ofp.OFPAT_SET_NW_TOS):
            supported_actions.append('OFPAT_SET_NW_TOS')
        if(reply.actions &1<<ofp.OFPAT_SET_TP_SRC):
            supported_actions.append('OFPAT_SET_TP_SRC')
        if(reply.actions &1<<ofp.OFPAT_SET_TP_DST):
            supported_actions.append('OFPAT_SET_TP_DST')
        if(reply.actions &1<<ofp.OFPAT_VENDOR):
            supported_actions.append('OFPAT_VENDOR')
        if(reply.actions &1<<ofp.OFPAT_ENQUEUE):
            supported_actions.append('OFPAT_ENQUEUE')

        self.assertTrue(len(supported_actions) != 0,"Features Reply did not contain actions supported by sw")
        #Verify switch supports the Required Actions i.e Forward 
        self.assertTrue('OFPAT_OUTPUT' in supported_actions,"Required Action--Forward is not supported ")
        logging.info("Supported Actions: " + str(supported_actions))

        supported_capabilities = []
        if(reply.capabilities &1<<ofp.OFPC_FLOW_STATS):
            supported_capabilities.append('OFPC_FLOW_STATS')
        if(reply.capabilities &1<<ofp.OFPC_TABLE_STATS):
            supported_capabilities.append('OFPC_TABLE_STATS')
        if(reply.capabilities &1<<ofp.OFPC_PORT_STATS):
            supported_capabilities.append('OFPC_PORT_STATS')
        if(reply.capabilities &1<<ofp.OFPC_STP):
            supported_capabilities.append('OFPC_STP')
        if(reply.capabilities &1<<ofp.OFPC_RESERVED):
            supported_capabilities.append('OFPC_RESERVED')
        if(reply.capabilities &1<<ofp.OFPC_IP_REASM):
            supported_capabilities.append('OFPC_IP_REASM')
        if(reply.capabilities &1<<ofp.OFPC_QUEUE_STATS):
            supported_capabilities.append('OFPC_QUEUE_STATS')
        if(reply.capabilities &1<<ofp.OFPC_ARP_MATCH_IP):
            supported_capabilities.append('OFPC_ARP_MATCH_IP')

        logging.info("Supported Capabilities: " +  str(supported_capabilities))

        self.assertTrue(reply.datapath_id != 0 , "Features Reply did not contain datapath of the sw")
        logging.info("Datapath Id: " + str(reply.datapath_id))
        
        logging.info("Buffer Size: " + str(reply.n_buffers))

        self.assertTrue(reply.n_tables != 0 , "Features Reply does not contain no. of tables supported by datapath")
        logging.info("No of tables: " + str(reply.n_tables))
        
        ports=0
        ports = len(reply.ports)
        self.assertTrue(ports != 0, "Features Reply does not contain no. of ports and their ports definitions")
        self.assertTrue(ports >= len(of_ports),"No. of openflow ports in the features Reply is incorrect")
        logging.info("No. of openflow ports: " + str(ports))


class Grp80No210(base_tests.SimpleProtocol):

    """Verify the body of OFPT_GET_CONFIG_REPLY message """

    def runTest(self):

        logging.info("Running Grp80No220 GetConfigReply Test")
       
        #Send get_config_request
        logging.info("Sending Get Config Request...")
        request = message.get_config_request()
        (reply, pkt) = self.controller.transact(request)

        #Verify get_config_reply is recieved
        logging.info("Expecting GetConfigReply ")
        self.assertTrue(reply is not None, "Failed to get any reply")
        self.assertEqual(reply.header.type, ofp.OFPT_GET_CONFIG_REPLY,'Response is not Config Reply')
        self.assertEqual(reply.header.xid,request.header.xid,'Transaction id does not match')

        if reply.miss_send_len == 0 :
           logging.info ("the switch must send zero-size packet_in message")
        else :
            logging.info("miss_send_len: " + str(reply.miss_send_len))
        
        if reply.flags == 0 :
            logging.info("OFPC_FRAG_NORMAL:No special handling for fragments.")
        elif reply.flags == 1 :
            logging.info("OFPC_FRAG_DROP:Drop fragments.")
        elif reply.flags == 2 :
            logging.info("OFPC_FRAG_REASM:ReasSsemble")
        elif reply.flags == 3:
            logging.info("OFPC_FRAG_MASK")


class Grp80No270(base_tests.SimpleProtocol):

    """Verify OFPT_SET_CONFIG is implemented"""

    def runTest(self):

        logging.info("Running Grp80No270 SetConfigRequest Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        #Send get_config_request -- retrive miss_send_len field
        logging.info("Sending Get Config Request ")
        request = message.get_config_request()
        (reply, pkt) = self.controller.transact(request)
        self.assertTrue(reply is not None, "Failed to get any reply")
        self.assertEqual(reply.header.type, ofp.OFPT_GET_CONFIG_REPLY,'Response is not Config Reply')

        miss_send_len = 0
        miss_send_len = reply.miss_send_len
        old_flags = 0 
        old_flags = reply.flags

        #Send set_config_request --- set a different miss_sen_len field and flag
        logging.info("Sending Set Config Request...")
        req = message.set_config()
        
        if miss_send_len < 65400 :# Max miss_send len is 65535
            req.miss_send_len = miss_send_len + 100
            new_miss_send_len = req.miss_send_len
        else :
            req.miss_send_len = miss_send_len - 100
            new_miss_send_len = req.miss_send_len
        
        if old_flags > 0 :
            req.flags = old_flags-1
            new_flags = req.flags
        else :
            req.flags = old_flags+1 
            new_flags = req.flags

        rv=self.controller.message_send(req)
        self.assertTrue(rv is not None,"Unable to send the message")

        #Send get_config_request -- verify change came into effect
        logging.info("Sending Get Config Request...")
        request = message.get_config_request()

        (rep, pkt) = self.controller.transact(request)
        self.assertTrue(rep is not None, "Failed to get any reply")
        self.assertEqual(rep.header.type, ofp.OFPT_GET_CONFIG_REPLY,'Response is not Config Reply')
        self.assertEqual(rep.miss_send_len,new_miss_send_len, "miss_send_len configuration parameter could not be set")
        self.assertEqual(rep.flags,new_flags, "frag flags could not be set")
      


class Grp80No280a(base_tests.SimpleDataPlane):

    """ When packet_in is triggered due to a flow table miss,
        verify the data sent in packet_in varies in accordance with the
        miss_send_len field set in OFPT_SET_CONFIG"""

    def runTest(self):

        logging.info("Running Grp80No280a PacketInSizeMiss Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        #Clear switch state      
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        #Send a set_config_request message 
        miss_send_len = [0 ,32 ,64,100]
        
        for bytes in miss_send_len :
            req = message.set_config()
            req.miss_send_len = bytes
            rv=self.controller.message_send(req)
            self.assertTrue(rv is not None,"Unable to send the message")
            sleep(1)

            # Send packet to trigger packet_in event
            pkt = simple_tcp_packet()
            match = parse.packet_to_flow_match(pkt)
            self.assertTrue(match is not None, "Could not generate flow match from pkt")
            match.wildcards=ofp.OFPFW_ALL
            match.in_port = of_ports[0]
            self.dataplane.send(of_ports[0],str(pkt))

            #Verify packet_in generated
            (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN, timeout=3)
            self.assertTrue(response is not None,
                        'Packet In not received on control plane')

            #Verify buffer_id field and data field
            if response.buffer_id == 0xFFFFFFFF:
                self.assertTrue(len(response.data)==len(str(pkt)),"Buffer None here but packet_in is not a complete packet")
            elif (bytes==0):
                self.assertEqual(len(response.data),bytes,"PacketIn Size is not equal to miss_send_len") 
            else:
                self.assertTrue(len(response.data)>=bytes,"PacketIn Size is not atleast miss_send_len bytes") 
                

class Grp80No280b(base_tests.SimpleDataPlane):

    """When the packet is sent because of a "send to controller" action, 
        verify the data sent in packet_in varies in accordance with the
        max_len field set in action_output"""

    
    def runTest(self):

        logging.info("Running PacketInSizeAction Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        #Clear switch state      
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        #Create a simple tcp packet
        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        self.assertTrue(match is not None, "Could not generate flow match from pkt")
        match.wildcards=ofp.OFPFW_ALL
        match.in_port = of_ports[0]


        max_len = [0 ,32 ,64,100]
        
        for bytes in max_len :

            #Insert a flow entry with action --output to controller
            request = message.flow_mod()
            request.match = match
            request.buffer_id = 0xffffffff
            act = action.action_output()
            act.port = ofp.OFPP_CONTROLLER
            act.max_len = bytes 
            request.actions.add(act)
            
            logging.info("Inserting flow....")
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Error installing flow mod")
            self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
            
            #Send packet matching the flow
            logging.debug("Sending packet to dp port " + str(of_ports[0]))
            self.dataplane.send(of_ports[0], str(pkt))

            #Verifying packet_in recieved on the control plane 
            (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN, timeout=10)
            self.assertTrue(response is not None,
                        'Packet in message not received by controller')

            #Verify the reason field is OFPR_ACTION
            self.assertEqual(response.reason,ofp.OFPR_ACTION,"PacketIn reason field is incorrect")

            #Verify buffer_id field and data field
            if response.buffer_id != 0xFFFFFFFF :
                self.assertTrue(len(response.data)<=bytes,"Packet_in size is greater than max_len field")
            else:
                self.assertTrue(len(response.data)==len(str(pkt)),"Buffer None here but packet_in is not a complete packet")

           
class Grp80No300a(base_tests.SimpleDataPlane):

    """Verify the packet_in message body, 
    when packet_in is triggered due to a flow table miss"""

    def runTest(self):

        logging.info("Running Grp80No300a PacketInBodyMiss Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        #Clear switch state      
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        #Set miss_send_len field 
        logging.info("Sending  set_config_request to set miss_send_len... ")
        req = message.set_config()
        req.miss_send_len = 65535
        rv=self.controller.message_send(req)
        self.assertTrue(rv is not None,"Unable to send the message")
        sleep(1)

        # Send packet to trigger packet_in event
        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        self.assertTrue(match is not None, "Could not generate flow match from pkt")
        match.wildcards=ofp.OFPFW_ALL
        match.in_port = of_ports[0]
        self.dataplane.send(of_ports[0],str(pkt))

        #Verify packet_in generated
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN, timeout=3)
        self.assertTrue(response is not None,
                        'Packet In not received on control plane')

        #Verify Frame Total Length Field in Packet_in 
        self.assertEqual(response.total_len,len(str(pkt)), "PacketIn total_len field is incorrect")

        #Verify in_port field in Packet_in
        self.assertEqual(response.in_port,of_ports[0],"PacketIn in_port or recieved port field is incorrect")

        #Verify the reason field in Packet_in is OFPR_NO_MATCH
        self.assertEqual(response.reason,ofp.OFPR_NO_MATCH,"PacketIn reason field is incorrect")

        #Verify data field 
        self.assertTrue(len(response.data) == len(str(pkt)), "Complete Data packet was not sent")


class Grp80No300b(base_tests.SimpleDataPlane):

    """Verify the packet_in message body, when packet_in is generated due to action output to controller"""

    def runTest(self):

        logging.info("Running Grp80No300a PacketInBodyAction Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        #Clear switch state      
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        # Create a simple tcp packet
        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        self.assertTrue(match is not None, "Could not generate flow match from pkt")
        match.wildcards=ofp.OFPFW_ALL
        match.in_port = of_ports[0]

        #Insert a flow entry with action output to controller 
        request = message.flow_mod()
        request.match = match
        act = action.action_output()
        act.port = ofp.OFPP_CONTROLLER
        act.max_len = 65535 # Send the complete packet and do not buffer
        request.actions.add(act)

        logging.info("Inserting flow....")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
            
        #Send packet matching the flow
        logging.debug("Sending packet to dp port " + str(of_ports[0]))
        self.dataplane.send(of_ports[0], str(pkt))

        #Verifying packet_in recieved on the control plane 
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN, timeout=10)
        self.assertTrue(response is not None,
                    'Packet in message not received by controller')

        #Verify the reason field is OFPR_ACTION
        self.assertEqual(response.reason,ofp.OFPR_ACTION,"PacketIn reason field is incorrect")

        #Verify Frame Total Length Field in Packet_in 
        self.assertEqual(response.total_len,len(str(pkt)), "PacketIn total_len field is incorrect")

        #verify the data field
        self.assertEqual(len(response.data),len(str(pkt)),"Complete Data Packet was not sent")

        #Verify in_port field in Packet_in
        self.assertEqual(response.in_port,of_ports[0],"PacketIn in_port or recieved port field is incorrect")
