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

from oftest.oflog import *
from oftest.testutils import *
from time import sleep
from FuncUtils import *


class Grp90No10(base_tests.SimpleDataPlane):

    """Verify the packet_in message body, 
    when packet_in is triggered due to a flow table miss"""

    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp90No10 PacketInBodyMiss Test")
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

        #Grp90No50
        #Verify Frame Total Length Field in Packet_in 
        self.assertEqual(response.total_len,len(str(pkt)), "PacketIn total_len field is incorrect")

        #Grp90No40
        #Verify in_port field in Packet_in
        self.assertEqual(response.in_port,of_ports[0],"PacketIn in_port or recieved port field is incorrect")

        #Verify the reason field in Packet_in is OFPR_NO_MATCH
        self.assertEqual(response.reason,ofp.OFPR_NO_MATCH,"PacketIn reason field is incorrect")

        #Verify data field 
        self.assertTrue(len(response.data) == len(str(pkt)), "Complete Data packet was not sent")

class Grp90No20(base_tests.SimpleDataPlane):

    """ When packet_in is triggered due to a flow table miss,
        verify the data sent in packet_in varies in accordance with the
        miss_send_len field set in OFPT_SET_CONFIG"""
    
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp90No20 PacketInSizeMiss Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        #Clear switch state      
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        #Send a set_config_request message 
        miss_send_len = [0 ,32 ,64,100]
        
        #Grp90No20 and Grp90No30 are tested in a loop
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
            self.assertEqual(response.reason, ofp.OFPR_NO_MATCH, 'PacketIn received for reason other than OFPR_NO_MATCH. Reason was {0}.'.format(response.reason))

            #Verify buffer_id field and data field
            if response.buffer_id == 0xFFFFFFFF:
                self.assertTrue(len(response.data)==len(str(pkt)),"buffer_id of packet_in is -1, however data field of packet_in was the wrong size. Expected {0}, but received {1}".format(len(str(pkt)), len(response.data)))
            elif (bytes==0):
                self.assertEqual(len(response.data),bytes,"PacketIn Size is not equal to miss_send_len") 
            else:
                self.assertTrue(len(response.data)>=bytes,"PacketIn Size is not atleast miss_send_len bytes") 


class Grp90No60(base_tests.SimpleDataPlane):

    """Verify the packet_in message body, when packet_in is generated due to action output to controller"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp90No60 PacketInBodyAction Test")
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
        
        #Grp90No100
        #Verify Frame Total Length Field in Packet_in 
        self.assertEqual(response.total_len,len(str(pkt)), "PacketIn total_len field is incorrect")

        #verify the data field
        self.assertEqual(len(response.data),len(str(pkt)),"Complete Data Packet was not sent")

        #Grp90No90
        #Verify in_port field in Packet_in
        self.assertEqual(response.in_port,of_ports[0],"PacketIn in_port or recieved port field is incorrect")               

class Grp90No70(base_tests.SimpleDataPlane):

    """When the packet is sent because of a "send to controller" action, 
        verify the data sent in packet_in varies in accordance with the
        max_len field set in action_output"""

    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp90No70 PacketInSizeAction Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        #Clear switch state      
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        sleep(2)

        #Create a simple tcp packet
        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        self.assertTrue(match is not None, "Could not generate flow match from pkt")
        match.wildcards=ofp.OFPFW_ALL
        match.in_port = of_ports[0]
        
        max_len = [0 ,32 ,64,100]
        
        #Grp90No70 and Grp90No80 are tested in a loop
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
                self.assertTrue(len(response.data)==len(str(pkt)),"buffer_id of packet_in is -1, however data field in packet_in was the wrong size. Expected {0} bytes, but received {1}".format(len(str(pkt)), len(str(response.data))))

           
class Grp90No110(base_tests.SimpleDataPlane):

    """Verify Port Status Messages are sent to the controller 
    whenever physical ports are added, modified or deleted"""

    #priority = -1 #This would skip the set
    
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp90No110 PortStatusMessage Test")
        of_ports = config["port_map"].keys()
        
        #Clear switch state      
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        #Bring down the port by shutting the interface connected 
        try:
            logging.info("Bringing down the interface ..")
            default_port_num = 0
            num = test_param_get('port',default=default_port_num)
            self.dataplane.port_down(of_ports[num])  
        
            #Verify Port Status message is recieved with reason-- Port Deleted
            logging.info("Verify PortStatus-Down message is recieved on the control plane ")
            (response, raw) = self.controller.poll(ofp.OFPT_PORT_STATUS, timeout=15)
            self.assertTrue(response is not None,
                        'Port Status Message not generated')
            self.assertEqual(response.reason,ofp.OFPPR_MODIFY,"The reason field of Port Status Message is incorrect  expected {0} got {1}" .format (ofp.OFPPR_MODIFY, response.reason))
            
        #Bring up the port by starting the interface connected
        finally:
            logging.info("Bringing up the interface ...")
            self.dataplane.port_up(of_ports[num])

        #Verify Port Status message is recieved with reason-- Port Added
        logging.info("Verify Port Status Up message is received")
        (response, raw) = self.controller.poll(ofp.OFPT_PORT_STATUS, timeout=15)
        
        self.assertTrue(response is not None,
                        'Port Status Message not generated')
        self.assertEqual(response.reason,ofp.OFPPR_MODIFY,"The reason field of Port Status Message is incorrect expected {0} got {1}" .format (ofp.OFPPR_MODIFY, response.reason))
        self.assertTrue(response.desc.state and 1 == 1, "Port state is not correct")

class Grp90No120(base_tests.SimpleDataPlane):
    
    """ Modify the behavior of physical port using Port Modification Messages
    Change OFPPC_NO_FLOOD flag  and verify change takes place with features request """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp90No120 PortModFlood Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        #Retrieve Port Configuration
        logging.info("Sends Features Request and retrieve Port Configuration from reply")
        (hw_addr, port_config, advert) = \
            port_config_get(self.controller, of_ports[0])
        self.assertTrue(port_config is not None, "Did not get port config")

        logging.debug("No flood bit port " + str(of_ports[0]) + " is now " + 
                           str(port_config & ofp.OFPPC_NO_FLOOD))
        
        #Modify Port Configuration 
        logging.info("Modify Port Configuration using Port Modification Message:OFPT_PORT_MOD")
        rv = port_config_set(self.controller, of_ports[0],
                             port_config ^ ofp.OFPPC_NO_FLOOD, ofp.OFPPC_NO_FLOOD)
        self.assertTrue(rv != -1, "Error sending port mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        # Verify change took place with features request
        logging.info("Verify the change and then set it back")
        (hw_addr, port_config2, advert) = port_config_get(self.controller, of_ports[0])
        
        logging.debug("No flood bit port " + str(of_ports[0]) + " is now " + 
                           str(port_config2 & ofp.OFPPC_NO_FLOOD))
        self.assertTrue(port_config2 is not None, "Did not get port config2")
        self.assertTrue(port_config2 & ofp.OFPPC_NO_FLOOD !=
                        port_config & ofp.OFPPC_NO_FLOOD,
                        "Bit change did not take")
        # Set it back
        rv = port_config_set(self.controller, of_ports[0],port_config,
                             ofp.OFPPC_NO_FLOOD)
        self.assertTrue(rv != -1, "Error sending port mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")


class Grp90No130(base_tests.SimpleDataPlane):
    
    """ 
    Modify the behavior of physical port using Port Modification Messages
    Change OFPPC_NO_FWD flag and verify change took place with Features Request"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp90No130 PortModFwd Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        #Retrieve Port Configuration
        logging.info("Sends Features Request and retrieve Port Configuration from reply")
        (hw_addr, port_config, advert) = \
            port_config_get(self.controller, of_ports[0])
        self.assertTrue(port_config is not None, "Did not get port config")
        logging.debug("No flood bit port " + str(of_ports[0]) + " is now " + 
                           str(port_config & ofp.OFPPC_NO_FWD))

        #Modify Port Configuration 
        logging.info("Modify Port Configuration using Port Modification Message:OFPT_PORT_MOD")
        rv = port_config_set(self.controller, of_ports[0],
                             port_config ^ ofp.OFPPC_NO_FWD, ofp.OFPPC_NO_FWD)
        self.assertTrue(rv != -1, "Error sending port mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        # Verify change took place with features request
        logging.info("Verify the change and then set it back")
        (hw_addr, port_config2, advert) = port_config_get(self.controller, of_ports[0])
        
        logging.debug("No flood bit port " + str(of_ports[0]) + " is now " + 
                           str(port_config2 & ofp.OFPPC_NO_FWD))

        self.assertTrue(port_config2 is not None, "Did not get port config2")
        self.assertTrue(port_config2 & ofp.OFPPC_NO_FWD !=
                        port_config & ofp.OFPPC_NO_FWD,
                        "Bit change did not take")
        # Set it back
        rv = port_config_set(self.controller, of_ports[0],port_config,
                             ofp.OFPPC_NO_FWD)
        self.assertTrue(rv != -1, "Error sending port mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")


class Grp90No140(base_tests.SimpleDataPlane):
    """ 
    Modify the behavior of physical port using Port Modification Messages
    Change OFPPC_NO_PACKET_IN flag and verify change took place with Features Request"""
    @wireshark_capture
    def runTest(self):

        logging = get_logger()
        logging.info("Running Grp90No30b PortModPacketIn Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        #Retrieve Port Configuration
        logging.info("Sends Features Request and retrieve Port Configuration from reply")
        (hw_addr, port_config, advert) = \
            port_config_get(self.controller, of_ports[0])
        self.assertTrue(port_config is not None, "Did not get port config")
        logging.debug("No flood bit port " + str(of_ports[0]) + " is now " + 
                           str(port_config & ofp.OFPPC_NO_PACKET_IN))

        #Modify Port Configuration 
        logging.info("Modify Port Configuration using Port Modification Message:OFPT_PORT_MOD")
        rv = port_config_set(self.controller, of_ports[0],
                             port_config ^ ofp.OFPPC_NO_PACKET_IN, ofp.OFPPC_NO_PACKET_IN)
        self.assertTrue(rv != -1, "Error sending port mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        # Verify change took place with features request
        logging.info("Verify the change and then set it back")
        (hw_addr, port_config2, advert) = port_config_get(self.controller, of_ports[0])
        
        logging.debug("No flood bit port " + str(of_ports[0]) + " is now " + 
                           str(port_config2 & ofp.OFPPC_NO_PACKET_IN))

        self.assertTrue(port_config2 is not None, "Did not get port config2")
        self.assertTrue(port_config2 & ofp.OFPPC_NO_PACKET_IN !=
                        port_config & ofp.OFPPC_NO_PACKET_IN,
                        "Bit change did not take")
        # Set it back
        rv = port_config_set(self.controller, of_ports[0],port_config,
                             ofp.OFPPC_NO_PACKET_IN)
        self.assertTrue(rv != -1, "Error sending port mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")


class Grp90No150(base_tests.SimpleDataPlane):
    """Verify that the Controller is able to use the Packet_out message"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Runnign Grp90No150 testcase")
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports)>=1,"Not enough ports for test")
        
        msg = message.packet_out()
        msg.bufer_id = -1
        msg.in_port = ofp.OFPP_NONE
        act = action.action_output()
        act.port = of_ports[0]
        msg.actions.add(act)
        pkt = simple_tcp_packet()
        msg.data = str(pkt)
        self.controller.message_send(msg)
        error, _=self.controller.poll(exp_msg=ofp.OFPT_ERROR)
        if error:
            msg.in_port=ofp.OFPP_CONTROLLER
            self.controller.message_send(msg)
            error, _ = self.controller.poll(exp_msg=ofp.OFPT_ERROR)
            self.assertIsNone(error, "Error sending out packet out message.Got OFPT_ERROR")
            logging.info("Packet Out sent with in_port as OFPP_CONTROLLER")
        receive_pkt_check(self.dataplane,pkt,[of_ports[0]], set(of_ports).difference([of_ports[0]]),self)

class Grp90No160(base_tests.SimpleDataPlane):
    
    """Verify Description Stats message body """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp90No160 DescStatsGet test")
        
        logging.info("Sending stats request")
        request = message.desc_stats_request()
        response, pkt = self.controller.transact(request)
        self.assertTrue(response is not None,
                        "Did not get reply for desc stats")
        
        mfr_desc = ""
        hw_desc = ""
        sw_dec = ""
        serial_num = ""
        dp_decription = ""

        for stats in response.stats:

            mfr_desc += stats.mfr_desc
            hw_desc += stats.hw_desc
            sw_dec += stats.sw_desc
            serial_num += stats.serial_num
            dp_decription += stats.dp_desc

        logging.info("Manufacture Description :" + mfr_desc)
        logging.info("Hardware description : " + hw_desc)
        logging.info("Software Description :" + sw_dec)
        logging.info("Serial number :" + serial_num)
        logging.info("Human readable description of datapath :" + dp_decription)



class Grp90No170(base_tests.SimpleProtocol):

    """Verify Queue Configuration Reply message body """

    @wireshark_capture  
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp90No170 QueueConfigRequest")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        
        logging.info("Sending Queue Config Request ...")
        request = message.queue_get_config_request()
        request.port = of_ports[0]
        response, pkt = self.controller.transact(request)
        self.assertTrue(response is not None,
                        "Did not get reply ")
        self.assertTrue(response.header.type == ofp.OFPT_QUEUE_GET_CONFIG_REPLY, "Reply is not Queue Config Reply")

        #Verify Reply Body
        self.assertEqual(response.header.xid, request.header.xid , "Transaction Id in reply is not same as request")
        self.assertEqual(response.port,request.port , "Port queried does not match ")
        queues = []
        queues = response.queues
        logging.info ("Queues Configured for port " + str(of_ports[0]) + str(queues))

