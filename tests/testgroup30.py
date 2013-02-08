"""These tests fall under Conformance Test-Suite (OF-SWITCH-1.0.0 TestCases).
    Refer Documentation -- Detailed testing methodology 
    <Some of test-cases are directly taken from oftest> """

"Test Suite 3 "


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

class Grp30No40(base_tests.SimpleDataPlane):
    
    """ Modify the behavior of physical port using Port Modification Messages
    Change OFPPC_PORT_DOWN flag  and verify change takes place by Port_Status Message"""

    def runTest(self):

        logging.info("Running Grp0No40 PortMod PortDown Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        #Retrieve Port Configuration
        logging.info("Sends Features Request and retrieve Port Configuration from reply")
        (hw_addr, port_config, advert) = \
            port_config_get(self.controller, of_ports[0])
        self.assertTrue(port_config is not None, "Did not get port config")

        logging.debug("Port Down bit " + str(of_ports[0]) + " is now " + 
                           str(port_config & ofp.OFPPC_PORT_DOWN))
        
        #Modify Port Configuration 
        logging.info("Modify Port Configuration using Port Modification Message:OFPPC_PORT_DOWN")
        rv = port_config_set(self.controller, of_ports[0],
                             port_config ^ ofp.OFPPC_PORT_DOWN, ofp.OFPPC_PORT_DOWN)
        self.assertTrue(rv != -1, "Error sending port mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        #Verify Port Status message is recieved 
        logging.info("Verify Port Status Up message is received")
        (response, raw) = self.controller.poll(ofp.OFPT_PORT_STATUS, timeout=15)
        
        self.assertTrue(response is not None,
                        'Port Status Message not generated')
        
        # Verify change took place with features request
        logging.info("Verify the change and then set it back")
        (hw_addr, port_config2, advert) = port_config_get(self.controller, of_ports[0])
        
        logging.debug("No flood bit port " + str(of_ports[0]) + " is now " + 
                           str(port_config2 & ofp.OFPPC_PORT_DOWN))
        self.assertTrue(port_config2 is not None, "Did not get port config2")
        self.assertTrue(port_config2 & ofp.OFPPC_PORT_DOWN !=
                        port_config & ofp.OFPPC_PORT_DOWN,
                        "Bit change did not take")
        # Set it back
        rv = port_config_set(self.controller, of_ports[0],port_config,
                             ofp.OFPPC_PORT_DOWN)
        self.assertTrue(rv != -1, "Error sending port mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        #Verify Port Status message is recieved 
        logging.info("Verify Port Status Up message is received")
        (response, raw) = self.controller.poll(ofp.OFPT_PORT_STATUS, timeout=15)
        
        self.assertTrue(response is not None,
                        'Port Status Message not generated')
        
class Grp30No90(base_tests.SimpleDataPlane):
    
    """ 
    Modify the behavior of physical port using Port Modification Messages
    Change OFPPC_NO_FWD flag and verify change took place with Features Request"""

    def runTest(self):

        logging.info("Running Grp30No90a Drop all packets Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        #Retrieve Port Configuration
        logging.info("Sends Features Request and retrieve Port Configuration from reply")
        (hw_addr, port_config, advert) = \
            port_config_get(self.controller, of_ports[0])
        self.assertTrue(port_config is not None, "Did not get port config")
       
        #Modify Port Configuration 
        logging.info("Modify Port Configuration using Port Modification Message:OFPT_PORT_MOD")
        ofp.OFPPC_NO_FWD = 1 
        rv = port_config_set(self.controller, of_ports[0],
                             port_config | ofp.OFPPC_NO_FWD, ofp.OFPPC_NO_FWD)
        self.assertTrue(rv != -1, "Error sending port mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
	
        # Insert a flow matching on ingress_port with action A (output to of_port[1])  
        logging.info("Verify change took place by sending packets to port[0]")  
        (pkt,match) = wildcard_all_except_ingress(self,of_ports)

        # Send the Test Packet and packet dropped. 
        logging.info("Packet should not be forwarded to any dataplane port")
        no_ports=set(of_ports)
        yes_ports=[]
        receive_pkt_check(self.dataplane,pkt,yes_ports,no_ports,self)
                       
		#Set it back
        logging.info("Modify Port Configuration using Port Modification Message:OFPT_PORT_MOD")
        ofp.OFPPC_NO_FWD = 0 
        rv = port_config_set(self.controller, of_ports[0],
                             port_config | ofp.OFPPC_NO_FWD, ofp.OFPPC_NO_FWD)
        self.assertTrue(rv != -1, "Error sending port mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
		
		# Insert a flow matching on ingress_port with action A (output to of_port[1])  
        logging.info("Verify change took place by sending packets to port[0]")  
        (pkt,match) = wildcard_all_except_ingress(self,of_ports)

        # Send the Test Packet and verify packet recieved
        logging.info("Packet should be forwarded to egress_port")
        egress_port=of_ports[1]
        no_ports=set(of_ports).difference(egress_port)
        yes_ports=of_ports[1]
        receive_pkt_check(self.dataplane,pkt,yes_ports,no_ports,self)
                       