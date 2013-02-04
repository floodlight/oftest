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

from oftest.testutils import *
from time import sleep
from FuncUtils import *



class Grp90No10(base_tests.SimpleDataPlane):

    """Verify Port Status Messages are sent to the controller 
    whenever physical ports are added, modified or deleted"""

    priority = -1
    
    def runTest(self):
        
        logging.info("Running Grp90No10 PortStatusMessage Test")
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
            self.assertEqual(response.reason,ofp.OFPPR_DELETE,"The reason field of Port Status Message is incorrect")

        #Bring up the port by starting the interface connected
        finally:
            logging.info("Bringing up the interface ...")
            self.dataplane.port_up(of_ports[num])

        #Verify Port Status message is recieved with reason-- Port Added
        logging.info("Verify Port Status Up message is received")
        (response, raw) = self.controller.poll(ofp.OFPT_PORT_STATUS, timeout=15)
        
        self.assertTrue(response is not None,
                        'Port Status Message not generated')
        self.assertEqual(response.reason,ofp.OFPPR_ADD,"The reason field of Port Status Message is incorrect")


class Grp90No20(base_tests.SimpleDataPlane):
    
    """ Modify the behavior of physical port using Port Modification Messages
    Change OFPPC_NO_FLOOD flag  and verify change takes place with features request """

    def runTest(self):

        logging.info("Running Grp90No20 PortModFlood Test")
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


class Grp90No30a(base_tests.SimpleDataPlane):
    
    """ 
    Modify the behavior of physical port using Port Modification Messages
    Change OFPPC_NO_FWD flag and verify change took place with Features Request"""

    def runTest(self):

        logging.info("Running PortModFwd Test")
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


class Grp90No30b(base_tests.SimpleDataPlane):
    """ 
    Modify the behavior of physical port using Port Modification Messages
    Change OFPPC_NO_PACKET_IN flag and verify change took place with Features Request"""

    def runTest(self):

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


class Grp90No40(base_tests.SimpleDataPlane):
    
    """Verify Description Stats message body """
    
    def runTest(self):
        logging.info("Running DescStatsGet test")
        
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



class Grp90No110(base_tests.SimpleProtocol):

    """Verify Queue Configuration Reply message body """

      
    def runTest(self):
        
        logging.info("Running QueueConfigRequest")

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

