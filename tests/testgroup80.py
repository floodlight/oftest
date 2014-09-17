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

from oftest.oflog import *
from oftest.testutils import *
from time import sleep
from FuncUtils import*

class Grp80No10(base_tests.SimpleDataPlane):

    """Verify switch should be able to receive OFPT_HELLO messages without body"""

    def setUp(self):
        logging = get_logger()
        #This is almost same as setUp in SimpleProtcocol except that intial hello is set to false
        self.controller = controller.Controller(
            host=config["controller_host"],
            port=config["controller_port"])
        time_out = config["controller_timeout"]

        # clean_shutdown should be set to False to force quit app
        self.clean_shutdown = True
        #set initial hello to False
        self.controller.initial_hello=False
        self.controller.start()
        #@todo Add an option to wait for a pkt transaction to ensure version
        # compatibilty?
        self.controller.connect(timeout=time_out)
        # By default, respond to echo requests
        self.controller.keep_alive = True
        if not self.controller.active:
            raise Exception("Controller startup failed")
        if self.controller.switch_addr is None: 
            raise Exception("Controller startup failed (no switch addr)")
        logging.info("Connected " + str(self.controller.switch_addr))
        
        
    @wireshark_capture 
    def runTest(self):

        logging.info("Running Grp80No10 HelloWithoutBody Test")            
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_HELLO,         
                                              timeout=5)
        request = message.hello()                                          
        rv = self.controller.message_send(request)      
        
        logging.info("Verify switch does not generate an error")
        (response, pkt) = self.controller.poll(exp_msg=ofp.OFPT_ERROR,         
                                               timeout=5)
        self.assertTrue(response is None, 
                               'Switch generated ERROR in response to our Hello message')  



class Grp80No20(base_tests.SimpleDataPlane):

    """Verify switch should be able to receive OFPT_HELLO messages with body , 
        but it should ignore the contents of the body"""

    def setUp(self):
        logging = get_logger()
        #This is almost same as setUp in SimpleProtcocol except that intial hello is set to false
        self.controller = controller.Controller(
            host=config["controller_host"],
            port=config["controller_port"])
        time_out = config["controller_timeout"]

        # clean_shutdown should be set to False to force quit app
        self.clean_shutdown = True
        #set initial hello to False
        self.controller.initial_hello=False
        self.controller.start()
        #@todo Add an option to wait for a pkt transaction to ensure version
        # compatibilty?
        self.controller.connect(timeout=time_out)
        # By default, respond to echo requests
        self.controller.keep_alive = True
        if not self.controller.active:
            raise Exception("Controller startup failed")
        if self.controller.switch_addr is None: 
            raise Exception("Controller startup failed (no switch addr)")
        logging.info("Connected " + str(self.controller.switch_addr))
        
        
    @wireshark_capture 
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
    @wireshark_capture 
    def runTest(self):
        logging = get_logger()
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
    
    """Verify if OFPT_ECHO_REQUEST without body. """

    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp80No40 EchoWithoutData test")
        
        #Send Echo Request 
        logging.info("Sending Echo Without Data ...")
        request = message.echo_request()
        (response, pkt) = self.controller.transact(request)

        #Verify Echo Reply is recieved 
        self.assertTrue(response is not None,
                        "Did not get echo reply (without data)")
        self.assertEqual(response.header.type, ofp.OFPT_ECHO_REPLY,
                         'Response is not echo_reply')
        self.assertEqual(request.header.xid, response.header.xid,
                         'Response xid does not match the request Xid')

class Grp80No50(base_tests.SimpleProtocol):
    
    """Verify if OFPT_ECHO_REQUEST has data field,
    switch responds back with OFPT_ECHO_REPLY with data field copied into it. """

    @wireshark_capture
    def runTest(self):
        logging = get_logger()
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
    """
    Verify OFPT_FEATURES_REQUEST / REPLY dialogue.
    """

    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp80No60: Features Request-Reply")
        
        logging.info("Sending features_request.")
        req = message.features_request()
        (res, pkt) = self.controller.transact(req)
        self.assertIsNotNone(res,
                             "Did not receive response to features_request.")
        logging.info("Verifying response's essential fields.")
        self.assertEqual(res.header.type, ofp.OFPT_FEATURES_REPLY,
                         "Response type was %d, but expected %d." %
                         (res.header.type, ofp.OFPT_FEATURES_REPLY))
        self.assertEqual(res.header.xid,req.header.xid,
                         ("Transaction ID of response did not match the "
                          "transaction ID of the request."))


class Grp80No70(base_tests.SimpleProtocol):
    """
    Verify OFPT_FEATURES_REPLY contains complete feature information.
    """

    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp80No70 Features Reply Body test")

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
        #Grp80No180
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
            supported_actions.append('OFPAT_SET_DL_DST')
        if(reply.actions &1<<ofp.OFPAT_SET_NW_SRC):
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

        logging.info("Capabilities bitmap: {0}".format(bin(reply.capabilities)))
        supported_capabilities = []
        mandatory=0
        #Grp80No110
        if(reply.capabilities & ofp.OFPC_FLOW_STATS):
            supported_capabilities.append('OFPC_FLOW_STATS')
        else:
            mandatory = 1
        #Grp80No120
        if(reply.capabilities & ofp.OFPC_TABLE_STATS):
            supported_capabilities.append('OFPC_TABLE_STATS')
        else:
            mandatory = 1
        #Grp80No130
        if(reply.capabilities & ofp.OFPC_PORT_STATS):
            supported_capabilities.append('OFPC_PORT_STATS')
        else:
            mandatory = 1
        #Grp80No140
        if(reply.capabilities & ofp.OFPC_STP):
            supported_capabilities.append('OFPC_STP')
        #Grp80N0150 - Reserved, must be Zero
        if(reply.capabilities & ofp.OFPC_RESERVED):
            mandatory = 1
        #Grp80No160
        if(reply.capabilities & ofp.OFPC_IP_REASM):
            supported_capabilities.append('OFPC_IP_REASM')

        if(reply.capabilities & ofp.OFPC_QUEUE_STATS):
            supported_capabilities.append('OFPC_QUEUE_STATS')
        #Grp80No170 - Match on IP src and IP dst are Optional
        if(reply.capabilities & ofp.OFPC_ARP_MATCH_IP):
            supported_capabilities.append('OFPC_ARP_MATCH_IP')

        logging.info("Supported Capabilities: " +  str(supported_capabilities))
        self.assertTrue(mandatory == 0, "Switch does not support all mandatory capabilities") 
        #Grp80No80
        self.assertTrue(reply.datapath_id != 0 , "Features Reply did not contain datapath of the sw")
        logging.info("Datapath Id: " + str(reply.datapath_id))
        #Grp80No90
        logging.info("Buffer Size: " + str(reply.n_buffers))
        #Grp80No100
        self.assertTrue(reply.n_tables != 0 , "Features Reply does not contain no. of tables supported by datapath")
        logging.info("No of tables: " + str(reply.n_tables))

        #Grp80No190
        ports=0
        ports = len(reply.ports)
        self.assertTrue(ports != 0, "Features Reply does not contain no. of ports and their ports definitions")
        self.assertTrue(ports >= len(of_ports),"No. of openflow ports in the features Reply is incorrect")
        logging.info("No. of openflow ports: " + str(ports))


class Grp80No200(base_tests.SimpleProtocol):

    """Verify the body of OFPT_GET_CONFIG_REPLY message """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp80No200 GetConfigReply Test")
       
        #Send get_config_request
        logging.info("Sending Get Config Request...")
        request = message.get_config_request()
        (reply, pkt) = self.controller.transact(request)

        #Verify get_config_reply is recieved
        logging.info("Expecting GetConfigReply ")
        self.assertTrue(reply is not None, "Failed to get any reply")
        self.assertEqual(reply.header.type, ofp.OFPT_GET_CONFIG_REPLY,'Response is not Config Reply')
        self.assertEqual(reply.header.xid,request.header.xid,'Transaction id does not match')
        
        #Grp80No250
        if reply.miss_send_len == 0 :
           logging.info ("the switch must send zero-size packet_in message")
        else :
            logging.info("miss_send_len: " + str(reply.miss_send_len))
        #Grp80No220
        if reply.flags == 1 :
            logging.info("OFPC_FRAG_DROP:Drop fragments.")
        #Grp80No230
        elif reply.flags == 2 :
            logging.info("OFPC_FRAG_REASM:ReasSsemble")
        #Grp80No240
        elif reply.flags == 3:
            logging.info("OFPC_FRAG_MASK")

class Grp80No210(base_tests.SimpleDataPlane):
    

    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info('Running Grp80No210 OFPC_FRAG_NORMAL')

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        rc = delete_all_flows(self.controller)
        self.assertTrue(rc != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        egress_port=of_ports[1]
        no_ports=set(of_ports).difference([egress_port])
        yes_ports = of_ports[1]

        #Send get_config_request
        logging.info("Sending Get Config Request...")
        request = message.get_config_request()
        (reply, pkt) = self.controller.transact(request)

        #Verify get_config_reply is recieved
        logging.info("Expecting GetConfigReply ")
        self.assertTrue(reply is not None, "Failed to get any reply")
        self.assertEqual(reply.header.type, ofp.OFPT_GET_CONFIG_REPLY,'Response is not Config Reply')
        self.assertEqual(reply.header.xid,request.header.xid,'Transaction id does not match')
        
        if reply.flags == 0 :
            logging.info("OFPC_FRAG_NORMAL:No special handling for fragments.")

            logging.info("Installing a flow with match on Ingress port")
            (pkt, match) = wildcard_all_except_ingress(self, of_ports, priority=0)

            frag_pkts = simple_frag_packets()

            for pkt in frag_pkts:
                self.dataplane.send(of_ports[0], str(pkt))
                receive_pkt_check(self.dataplane, pkt,[yes_ports], no_ports, self)

class Grp80No260(base_tests.SimpleProtocol):

    """Verify OFPT_SET_CONFIG is implemented"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp80No260 SetConfigRequest Test")
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
        

        rv=self.controller.message_send(req)
        self.assertTrue(rv is not None,"Unable to send the message")

        #Send get_config_request -- verify change came into effect
        logging.info("Sending Get Config Request...")
        request = message.get_config_request()

        (rep, pkt) = self.controller.transact(request)
        self.assertTrue(rep is not None, "Failed to get any reply")
        self.assertEqual(rep.header.type, ofp.OFPT_GET_CONFIG_REPLY,'Response is not Config Reply')
        self.assertEqual(rep.miss_send_len,new_miss_send_len, "miss_send_len configuration parameter could not be set")
        #self.assertEqual(rep.flags,new_flags, "frag flags could not be set expected {0} got {1}" .format(new_flags, rep.flags))
      
class Grp80No270(base_tests.SimpleProtocol):

    """Verify OFPT_SET_CONFIG is implemented"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp80No270 Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()


        logging.info("Sending Get Config Request ")
        request = message.get_config_request()
        (reply, pkt) = self.controller.transact(request)
        self.assertTrue(reply is not None, "Failed to get any reply")
        self.assertEqual(reply.header.type, ofp.OFPT_GET_CONFIG_REPLY,'Response is not Config Reply')

        old_flags = 0
        old_flags = reply.flags


        logging.info("Sending Set Config Request...")
        req = message.set_config()
        if old_flags != 0 :
            req.flags = 0
            new_flags = req.flags
            rv=self.controller.message_send(req)
            self.assertTrue(rv is not None,"Unable to send the message")

             #Send get_config_request -- verify change came into effect                                                                                                                                                                      
            logging.info("Sending Get Config Request...")
            request = message.get_config_request()

            (rep, pkt) = self.controller.transact(request)
            self.assertTrue(rep is not None, "Failed to get any reply")
            self.assertEqual(rep.header.type, ofp.OFPT_GET_CONFIG_REPLY,'Response is not Config Reply')

            try :
                self.assertEqual(rep.flags,new_flags, "frag flags could not be set expected {0} got {1}" .format(new_flags, rep.flags))
            finally :
                logging.info("Reverting the changes")
                req=message.set_config()
                req.flags=old_flags
                rv=None
                rv=self.controller.message_send(req)
                self.assertTrue(rv is not None, " Unable to send the set_config message")

                request = message.get_config_request()
                rep1=None
                (rep1, pkt) = self.controller.transact(request)
                self.assertTrue(rep1 is not None, "Failed to get a reply")
                self.assertTrue(rep1.header.type==ofp.OFPT_GET_CONFIG_REPLY, 'Response is not config Reply')
                self.assertTrue(rep1.flags==old_flags, "Changes could not be reverted")
        else :
            logging.info("The Flag already set to OFPC_FRAG_NORMAL")

class Grp80No280(base_tests.SimpleProtocol):

    """Verify OFPT_SET_CONFIG is implemented"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp80No280 Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

       
        logging.info("Sending Get Config Request ")
        request = message.get_config_request()
        (reply, pkt) = self.controller.transact(request)
        self.assertTrue(reply is not None, "Failed to get any reply")
        self.assertEqual(reply.header.type, ofp.OFPT_GET_CONFIG_REPLY,'Response is not Config Reply')

        old_flags = 0
        old_flags = reply.flags

       
        logging.info("Sending Set Config Request...")
        req = message.set_config()
        if old_flags != 1 :
            req.flags = 1
            new_flags = req.flags
            rv=self.controller.message_send(req)
            self.assertTrue(rv is not None,"Unable to send the message")

       
            logging.info("Sending Get Config Request...")
            request = message.get_config_request()

            (rep, pkt) = self.controller.transact(request)
            self.assertTrue(rep is not None, "Failed to get any reply")
            self.assertEqual(rep.header.type, ofp.OFPT_GET_CONFIG_REPLY,'Response is not Config Reply')
            try :
                self.assertEqual(rep.flags,new_flags, "frag flags could not be set expected {0} got {1}" .format(new_flags, rep.flags)) 
            finally :
                logging.info("Reverting the changes")
                req=message.set_config()
                req.flags=old_flags
                rv=None
                rv=self.controller.message_send(req)
                self.assertTrue(rv is not None, " Unable to send the set_config message")
                
                request = message.get_config_request()
                rep1=None
                (rep1, pkt) = self.controller.transact(request)
                self.assertTrue(rep1 is not None, "Failed to get a reply")
                self.assertTrue(rep1.header.type==ofp.OFPT_GET_CONFIG_REPLY, 'Response is not config Reply')
                self.assertTrue(rep1.flags==old_flags, "Changes could not be reverted")
        else :
            logging.info("The Flag already set to OFPC_FRAG_DROP")


class Grp80No290(base_tests.SimpleProtocol):

    """Verify OFPT_SET_CONFIG is implemented"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp80No290 Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

                                                                                                                                                                    
        logging.info("Sending Get Config Request ")
        request = message.get_config_request()
        (reply, pkt) = self.controller.transact(request)
        self.assertTrue(reply is not None, "Failed to get any reply")
        self.assertEqual(reply.header.type, ofp.OFPT_GET_CONFIG_REPLY,'Response is not Config Reply')

        old_flags = 0
        old_flags = reply.flags

                                                                                                                                                             
        logging.info("Sending Set Config Request...")
        req = message.set_config()
        if old_flags != 2 :
            req.flags = 2
            new_flags = req.flags
            rv=self.controller.message_send(req)
            self.assertTrue(rv is not None,"Unable to send the message")

             #Send get_config_request -- verify change came into effect
            logging.info("Sending Get Config Request...")
            request = message.get_config_request()

            (rep, pkt) = self.controller.transact(request)
            self.assertTrue(rep is not None, "Failed to get any reply")
            self.assertEqual(rep.header.type, ofp.OFPT_GET_CONFIG_REPLY,'Response is not Config Reply')

            try :
                self.assertEqual(rep.flags,new_flags, "frag flags could not be set expected {0} got {1}" .format(new_flags, rep.flags))
            finally :
                logging.info("Reverting the changes")
                req=message.set_config()
                req.flags=old_flags
                rv=None
                rv=self.controller.message_send(req)
                self.assertTrue(rv is not None, " Unable to send the set_config message")

                request = message.get_config_request()
                rep1=None
                (rep1, pkt) = self.controller.transact(request)
                self.assertTrue(rep1 is not None, "Failed to get a reply")
                self.assertTrue(rep1.header.type==ofp.OFPT_GET_CONFIG_REPLY, 'Response is not config Reply')
                self.assertTrue(rep1.flags==old_flags, "Changes could not be reverted")
        else :
            logging.info("The Flag already set to OFPC_FRAG_REASM")


class Grp80No300(base_tests.SimpleProtocol):

    """Verify OFPT_SET_CONFIG is implemented"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp80No300 Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()


        logging.info("Sending Get Config Request ")
        request = message.get_config_request()
        (reply, pkt) = self.controller.transact(request)
        self.assertTrue(reply is not None, "Failed to get any reply")
        self.assertEqual(reply.header.type, ofp.OFPT_GET_CONFIG_REPLY,'Response is not Config Reply')

        old_flags = 0
        old_flags = reply.flags


        logging.info("Sending Set Config Request...")
        req = message.set_config()
        if old_flags != 3 :
            req.flags = 3
            new_flags = req.flags
            rv=self.controller.message_send(req)
            self.assertTrue(rv is not None,"Unable to send the message")

             #Send get_config_request -- verify change came into effect                                                                                                                                                                      
            logging.info("Sending Get Config Request...")
            request = message.get_config_request()

            (rep, pkt) = self.controller.transact(request)
            self.assertTrue(rep is not None, "Failed to get any reply")
            self.assertEqual(rep.header.type, ofp.OFPT_GET_CONFIG_REPLY,'Response is not Config Reply')

            try :
                self.assertEqual(rep.flags,new_flags, "frag flags could not be set expected {0} got {1}" .format(new_flags, rep.flags))
            finally :
                logging.info("Reverting the changes")
                req=message.set_config()
                req.flags=old_flags
                rv=None
                rv=self.controller.message_send(req)
                self.assertTrue(rv is not None, " Unable to send the set_config message")

                request = message.get_config_request()
                rep1=None
                (rep1, pkt) = self.controller.transact(request)
                self.assertTrue(rep1 is not None, "Failed to get a reply")
                self.assertTrue(rep1.header.type==ofp.OFPT_GET_CONFIG_REPLY, 'Response is not config Reply')
                self.assertTrue(rep1.flags==old_flags, "Changes could not be reverted")
        else :
            logging.info("The Flag already set to OFPC_FRAG_MASK")
