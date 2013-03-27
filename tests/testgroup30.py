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

from oftest.oflog import *
from oftest.testutils import *
from time import sleep
from FuncUtils import *

class Grp30No40(base_tests.SimpleDataPlane):
    
    """Modify the behavior of physical port using Port Modification Messages
    Change OFPPC_PORT_DOWN flag  and verify change takes place by Port_Status Message"""

    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp30No40 PortMod PortDown Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        #Retrieve Port Configuration --- 
        logging.info("Sending Features Request")
        (hw_addr, port_config, advert) = \
            port_config_get(self.controller, of_ports[1])
        logging.info("Extracting the port configuration from the reply")
        self.assertTrue(port_config is not None, "Did not get port config")

        logging.debug("Port Down bit " + str(of_ports[1]) + " is now " + 
                           str(port_config & ofp.OFPPC_PORT_DOWN))
        
        #Modify Port Configuration 
        logging.info("Bringing port %s using Port Modification Message:OFPPC_PORT_DOWN" %str(of_ports[1]))
        rv = port_config_set(self.controller, of_ports[1],
                             port_config ^ ofp.OFPPC_PORT_DOWN, ofp.OFPPC_PORT_DOWN)
        self.assertTrue(rv != -1, "Error sending port mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        #Verify Port Status message is recieved 
        logging.info("Waiting for the port status change message")
        (response, raw) = self.controller.poll(ofp.OFPT_PORT_STATUS, timeout=15)
        
        self.assertTrue(response is not None,
                        'Port Status Message not generated. Please note ports could not be configured')
        
        # Verify change took place with features request
        logging.info("Verifying that port %s is Down" %str(of_ports[1]))
        (hw_addr, port_config2, advert) = port_config_get(self.controller, of_ports[1])
        
        logging.debug("No flood bit port " + str(of_ports[1]) + " is now " + 
                           str(port_config2 & ofp.OFPPC_PORT_DOWN))
        self.assertTrue(port_config2 is not None, "Did not get port config2")
        self.assertTrue(port_config2 & ofp.OFPPC_PORT_DOWN !=
                        port_config & ofp.OFPPC_PORT_DOWN,
                        "Port status Bit did not change")
        # Set it back
        logging.info("Reverting the settings")
        rv = port_config_set(self.controller, of_ports[1],port_config,
                             ofp.OFPPC_PORT_DOWN)
        self.assertTrue(rv != -1, "Error sending port mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        #Verify Port Status message is recieved 
        logging.info("Waiting for port status change message")
        (response, raw) = self.controller.poll(ofp.OFPT_PORT_STATUS, timeout=15)
        
        self.assertTrue(response is not None,
                        'Port Status Message not generated.\n PLEASE NOTE: Port config could not be set back to default ')
        


class Grp30No90(base_tests.SimpleDataPlane):
    """ 
    Modify the behavior of physical port using Port Modification Messages
    Change OFPPC_NO_FWD flag and verify change took place with Features Request"""

    @wireshark_capture
    def runTest(self):

        logging = get_logger()
        logging.info("Running Grp30No90 PortModFwd Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        #Retrieve Port Configuration
        logging.info("Sending Features Request")
        (hw_addr, port_config, advert) = \
            port_config_get(self.controller, of_ports[1])
        logging.info("Extracting Port configuration for the reply")
        self.assertTrue(port_config is not None, "Did not get port config")
        logging.debug("No flood bit port " + str(of_ports[1]) + " is now " + 
                           str(port_config & ofp.OFPPC_NO_FWD))
	print port_config                           
        #making sure that the switch in expected default state
        if port_config & ofp.OFPPC_NO_FWD != 0:
        	logging.info("making sure the switch has the expected default state i.e no_fwd_flag==0")
		rv = port_config_set(self.controller, of_ports[1],
                             port_config ^ ofp.OFPPC_NO_FWD, ofp.OFPPC_NO_FWD)
                self.assertTrue(rv != -1, "Error sending port mod")
        	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
        	logging.info("Sending Features Request")
        	(hw_addr, port_config, advert) = \
            	port_config_get(self.controller, of_ports[1])
        	logging.info("Extracting Port configuration for the reply")
        	self.assertTrue(port_config is not None, "Did not get port config")
        	logging.debug("No flood bit port " + str(of_ports[1]) + " is now " + 
                           str(port_config & ofp.OFPPC_NO_FWD))        		
		print port_config
		
		#Modify Port Configuration 
        logging.info("Changing the behavior of port %s using Port Modification Message:OFPPC_NO_FWD" %str(of_ports[1]))
        rv = port_config_set(self.controller, of_ports[1],
                             port_config ^ ofp.OFPPC_NO_FWD, ofp.OFPPC_NO_FWD)
        self.assertTrue(rv != -1, "Error sending port mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        sleep(5)

        #TBD: Remove sleep with continous Features Requests being sent 

		# Verify change took place with features request
        logging.info("Verifying whether port %s has been modified in the switch" %str(of_ports[1]))
        (hw_addr, port_config2, advert) = port_config_get(self.controller, of_ports[1])
        
        logging.debug("No flood bit port " + str(of_ports[1]) + " is now " + str(port_config2 & ofp.OFPPC_NO_FWD))
        self.assertTrue(port_config2 is not None, "Did not get port config2")
        self.assertTrue(port_config2 & ofp.OFPPC_NO_FWD !=
                        port_config & ofp.OFPPC_NO_FWD,
                        "Port status Bit did not change")

        #Insert an All Wildcarded flow.
        (pkt,match) = wildcard_all(self,of_ports)
        #Send matching packet 
        self.dataplane.send(of_ports[0], str(pkt))
	fail=0
		
		#Verify packet does not implement the action specified in the flow
	try:
		
        	logging.info("verifying that packets on port %s are dropped" %str(of_ports[1]))
        	yes_ports=[]
        	no_ports = set(of_ports)
        	receive_pkt_check(self.dataplane,pkt,yes_ports,no_ports,self)
		logging.info("The switch successfully drops packets on port " +str(of_port[1]))
		

	except:
		fail=1
    
        finally:
                #setting it back
                logging.info("Reverting the changes we made")
        	rv = port_config_set(self.controller, of_ports[1],port_config,
                             ofp.OFPPC_NO_FWD)
        	self.assertTrue(rv != -1, "Error sending port mod")
        	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        	sleep(5)
        	#TBD: Remove sleep with continous Features Requests being sent 
	
        	# Verify change took place with features request
        	logging.info("Verifying whether port %s is back to its default settings" %str(of_ports[1]))
        	(hw_addr, port_config3, advert) = port_config_get(self.controller, of_ports[1])
        
        	logging.debug("No forward bit port " + str(of_ports[1]) + " is now " + 
                           str(port_config3 & ofp.OFPPC_NO_FWD))

        	self.assertTrue(port_config3 is not None, "Did not get port config2")
        	self.assertTrue(port_config2 & ofp.OFPPC_NO_FWD !=
                        port_config3 & ofp.OFPPC_NO_FWD,
                        "Could not change the port behavior to default")

        	#Send matching packet 
        	self.dataplane.send(of_ports[0], str(pkt))
	
		#Verify packet implements the action specified in the flow
		logging.info("verifying that packets on port %s are forwarded" %str(of_ports[1]))
        	yes_ports= [of_ports[1]]
        	no_ports = set(of_ports).difference(yes_ports)
        	receive_pkt_check(self.dataplane,pkt,yes_ports,no_ports,self)
        	logging.info("Successfully recieved packet on port" +str(of_ports[1]))
		self.assertTrue(fail==0,"The packets on port %s are forwarded even when the no_fwd_flag is set(before reverting)" %str(of_ports[1]))
	


class Grp30No100(base_tests.SimpleDataPlane):
    """ 
    Modify the behavior of physical port using Port Modification Messages
    Change OFPPC_NO_PACKET_IN flag and verify change took place with Features Request"""

    @wireshark_capture
    def runTest(self):
    

        logging = get_logger()
        logging.info("Running Grp90No30b PortModPacketIn Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

    	rc=delete_all_flows(self.controller)
    	self.assertTrue(rc==0,"Cannot delet all flows")
        #Retrieve Port Configuration
        logging.info("Sending Features Request")
        (hw_addr, port_config, advert) = \
            port_config_get(self.controller, of_ports[0])
        logging.info("Extracting port configurtions form the reply")
        self.assertTrue(port_config is not None, "Did not get port config")
        logging.debug("No flood bit port " + str(of_ports[0]) + " is now " + 
                           str(port_config & ofp.OFPPC_NO_PACKET_IN))
        
        
        if port_config & ofp.OFPPC_NO_PACKET_IN != 0:
        	logging.info("making sure the switch has the expected default state i.e no_packet_in_flag==0")
		rv = port_config_set(self.controller, of_ports[0],
                             port_config ^ ofp.OFPPC_NO_PACKET_IN, ofp.OFPPC_NO_PACKET_IN)
                self.assertTrue(rv != -1, "Error sending port mod")
        	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
        	logging.info("Sending Features Request")
        	(hw_addr, port_config, advert) = \
            	port_config_get(self.controller, of_ports[0])
        	logging.info("Extracting Port configuration for the reply")
        	self.assertTrue(port_config is not None, "Did not get port config")
        	logging.debug("No flood bit port " + str(of_ports[0]) + " is now " + 
                           str(port_config & ofp.OFPPC_NO_PACKET_IN))        		
		print port_config

        #Modify Port Configuration 
        logging.info("Changing the behavior of port %s using Port Modification Message:OFPPC_NO_PACKET_IN" %str(of_ports[0])) 
        rv = port_config_set(self.controller, of_ports[0],
                             port_config ^ ofp.OFPPC_NO_PACKET_IN, ofp.OFPPC_NO_PACKET_IN)
        self.assertTrue(rv != -1, "Error sending port mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
	
		# Verify change took place with features request
        logging.info("Verifying whether port %s has been modified in the switch" %str(of_ports[0]))
        sleep(5)
        (hw_addr, port_config2, advert) = port_config_get(self.controller, of_ports[0])
        
        logging.debug("No flood bit port " + str(of_ports[0]) + " is now " + 
                           str(port_config2 & ofp.OFPPC_NO_PACKET_IN))

        self.assertTrue(port_config2 is not None, "Did not get port config2")
        self.assertTrue(port_config2 & ofp.OFPPC_NO_PACKET_IN !=
                        port_config & ofp.OFPPC_NO_PACKET_IN,
                        "Bit change did not take")

	fail=0
        #Send Test_packet
        try:
        	logging.info("Verifying that any packet on port %s does not generate a PACKET_IN" %str(of_ports[0]))
        	pkt = simple_tcp_packet()
        	self.dataplane.send(of_ports[0], str(pkt))
        	#Verify PacketIn event gets triggered
        	(response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
        	self.assertTrue(response is None, "PacketIn received,even though NO_PACKET_IN flag is set")
	except:
		fail=1        
        # Set it back
        finally:
        	logging.info("Reverting the settings")
        	rv = port_config_set(self.controller, of_ports[0],port_config,
                             ofp.OFPPC_NO_PACKET_IN)
        	self.assertTrue(rv != -1, "Error sending port mod")
        	self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
        	sleep(5)

	        #Send Test_packet
		logging.info("Verfying whether packet on port %s generates PACKET_IN" %str(of_ports[0]))
		pkt = simple_tcp_packet()
		self.dataplane.send(of_ports[0], str(pkt))
		#Verify PacketIn event gets triggered
		(response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN,timeout=4)
		self.assertTrue(response is not None, "PacketIn not received, please check port_config and NO_PACKET_IN flag ")	
		logging.info("packetIn generated")
		self.assertTrue(fail==0,"PacketIn recieved,even Though NO_PACKRT_IN flag is set(before reverting)")
