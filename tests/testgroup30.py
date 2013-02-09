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
    
    """Modify the behavior of physical port using Port Modification Messages
    Change OFPPC_PORT_DOWN flag  and verify change takes place by Port_Status Message"""

    def runTest(self):

        logging.info("Running Grp30No40 PortMod PortDown Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        #Retrieve Port Configuration --- 
        logging.info("Sends Features Request and retrieve Port Configuration from reply")
        (hw_addr, port_config, advert) = \
            port_config_get(self.controller, of_ports[1])
        self.assertTrue(port_config is not None, "Did not get port config")

        logging.debug("Port Down bit " + str(of_ports[1]) + " is now " + 
                           str(port_config & ofp.OFPPC_PORT_DOWN))
        
        #Modify Port Configuration 
        logging.info("Modify Port Configuration using Port Modification Message:OFPPC_PORT_DOWN")
        rv = port_config_set(self.controller, of_ports[1],
                             port_config ^ ofp.OFPPC_PORT_DOWN, ofp.OFPPC_PORT_DOWN)
        self.assertTrue(rv != -1, "Error sending port mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        #Verify Port Status message is recieved 
        logging.info("Verify Port Status Up message is received")
        (response, raw) = self.controller.poll(ofp.OFPT_PORT_STATUS, timeout=15)
        
        self.assertTrue(response is not None,
                        'Port Status Message not generated. Please note ports could not be configured')
        
        # Verify change took place with features request
        logging.info("Verify the change and then set it back")
        (hw_addr, port_config2, advert) = port_config_get(self.controller, of_ports[1])
        
        logging.debug("No flood bit port " + str(of_ports[1]) + " is now " + 
                           str(port_config2 & ofp.OFPPC_PORT_DOWN))
        self.assertTrue(port_config2 is not None, "Did not get port config2")
        self.assertTrue(port_config2 & ofp.OFPPC_PORT_DOWN !=
                        port_config & ofp.OFPPC_PORT_DOWN,
                        "Bit change did not take")
        # Set it back
        rv = port_config_set(self.controller, of_ports[1],port_config,
                             ofp.OFPPC_PORT_DOWN)
        self.assertTrue(rv != -1, "Error sending port mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        #Verify Port Status message is recieved 
        logging.info("Verify Port Status Up message is received")
        (response, raw) = self.controller.poll(ofp.OFPT_PORT_STATUS, timeout=15)
        
        self.assertTrue(response is not None,
                        'Port Status Message not generated,Please note: Port config could not be set back to default ')
        


class Grp30No90(base_tests.SimpleDataPlane):
    """ 
    Modify the behavior of physical port using Port Modification Messages
    Change OFPPC_NO_FWD flag and verify change took place with Features Request"""

    def runTest(self):

        logging.info("Running Grp30No90 PortModFwd Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        #Retrieve Port Configuration
        logging.info("Sends Features Request and retrieve Port Configuration from reply")
        (hw_addr, port_config, advert) = \
            port_config_get(self.controller, of_ports[1])
        self.assertTrue(port_config is not None, "Did not get port config")
        logging.debug("No flood bit port " + str(of_ports[1]) + " is now " + 
                           str(port_config & ofp.OFPPC_NO_FWD))

		#Modify Port Configuration 
        logging.info("Modify Port Configuration using Port Modification Message:OFPPC_NO_FWD")
        rv = port_config_set(self.controller, of_ports[1],
                             port_config ^ ofp.OFPPC_NO_FWD, ofp.OFPPC_NO_FWD)
        self.assertTrue(rv != -1, "Error sending port mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        sleep(15)

        #TBD: Remove sleep with continous Features Requests being sent 

		# Verify change took place with features request
        logging.info("Verify the change and then set it back")
        (hw_addr, port_config2, advert) = port_config_get(self.controller, of_ports[1])
        
        logging.debug("No flood bit port " + str(of_ports[1]) + " is now " + str(port_config2 & ofp.OFPPC_NO_FWD))
        self.assertTrue(port_config2 is not None, "Did not get port config2")
        self.assertTrue(port_config2 & ofp.OFPPC_NO_FWD !=
                        port_config & ofp.OFPPC_NO_FWD,
                        "Bit change did not take")

        #Insert an All Wildcarded flow.
        (pkt,match) = wildcard_all(self,of_ports)
        #Send matching packet 
        self.dataplane.send(of_ports[1], str(pkt))
		
		#Verify packet does not implement the action specified in the flow
        yes_ports=[]
        no_ports = set(of_ports)
        receive_pkt_check(self.dataplane,pkt,yes_ports,no_ports,self)

		# Set it back
        rv = port_config_set(self.controller, of_ports[1],port_config,
                             ofp.OFPPC_NO_FWD)
        self.assertTrue(rv != -1, "Error sending port mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        sleep(15)
        #TBD: Remove sleep with continous Features Requests being sent 

        # Verify change took place with features request
        logging.info("Verify the change and then set it back")
        (hw_addr, port_config2, advert) = port_config_get(self.controller, of_ports[1])
        
        logging.debug("No flood bit port " + str(of_ports[1]) + " is now " + 
                           str(port_config2 & ofp.OFPPC_NO_FWD))

        self.assertTrue(port_config2 is not None, "Did not get port config2")
        self.assertTrue(port_config2 & ofp.OFPPC_NO_FWD !=
                        port_config & ofp.OFPPC_NO_FWD,
                        "Bit change did not take")

        #Send matching packet 
        self.dataplane.send(of_ports[1], str(pkt))

		#Verify packet implements the action specified in the flow
        yes_ports= of_ports[1]
        no_ports = set(of_ports).difference(yes_ports)
        receive_pkt_check(self.dataplane,pkt,yes_ports,no_ports,self)



class Grp30No100(base_tests.SimpleDataPlane):
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
        logging.info("Modify Port Configuration using Port Modification Message:OFPPC_NO_PACKET_IN")
        rv = port_config_set(self.controller, of_ports[0],
                             port_config ^ ofp.OFPPC_NO_PACKET_IN, ofp.OFPPC_NO_PACKET_IN)
        self.assertTrue(rv != -1, "Error sending port mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
	
		# Verify change took place with features request
        logging.info("Verify the change and then set it back")
        sleep(15)
        (hw_addr, port_config2, advert) = port_config_get(self.controller, of_ports[0])
        
        logging.debug("No flood bit port " + str(of_ports[0]) + " is now " + 
                           str(port_config2 & ofp.OFPPC_NO_PACKET_IN))

        self.assertTrue(port_config2 is not None, "Did not get port config2")
        self.assertTrue(port_config2 & ofp.OFPPC_NO_PACKET_IN !=
                        port_config & ofp.OFPPC_NO_PACKET_IN,
                        "Bit change did not take")

        #Send Test_packet
        pkt = simple_tcp_packet()
        self.dataplane.send(of_ports[0], str(pkt))
        #Verify PacketIn event gets triggered
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is None, "PacketIn received,even though NO_PACKET_IN flag is set")
        
        # Set it back
        rv = port_config_set(self.controller, of_ports[0],port_config,
                             ofp.OFPPC_NO_PACKET_IN)
        self.assertTrue(rv != -1, "Error sending port mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        sleep(15)

        #Send Test_packet
        pkt = simple_tcp_packet()
        self.dataplane.send(of_ports[0], str(pkt))
        #Verify PacketIn event gets triggered
        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        self.assertTrue(response is not None, "PacketIn not received, please check port_config and NO_PACKET_IN flag ")