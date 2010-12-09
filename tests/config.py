'''
Created on Dec 8, 2010

@author: capveg
'''

import logging

import basic
import testutils
import oftest.cstruct as ofp

class BlockPacketInByPort(basic.SimpleDataPlane):
    """
    Test ability to BLOCK packet ins via port_mod

    Send a packet to each dataplane port and verify that a packet
    in message is received from the controller for each
    """
    def runTest(self):
        # Construct packet to send to dataplane
        # Send packet to dataplane, once to each port
        # Poll controller with expect message type packet in

        rc = testutils.delete_all_flows(self.controller, config_logger)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        of_port=config_port_map.keys()[0]
        rv = testutils.port_config_set(self.controller, of_port,
                         ofp.OFPPC_NO_PACKET_IN, ofp.OFPPC_NO_PACKET_IN,
                         config_logger)
        self.assertTrue(rv != -1, "Error sending port mod")
        config_logger.info("NO PKT IN test, port " + str(of_port))
        pkt = testutils.simple_tcp_packet()
        self.dataplane.send(of_port, str(pkt))
        #@todo Check for unexpected messages?
        (response, _) = self.controller.poll(ofp.OFPT_PACKET_IN, 2)

        self.assertTrue(response is None, 
                        'OFPPC_NO_PACKET_IN flag is ignored on port (got a packet when we asked not to) ' + 
                        str(of_port))
            



def test_set_init(config):
    """
    Set up function for config test classes

    @param config The configuration dictionary; see oft
    """

    global config_port_map
    global config_logger
    global config_config

    config_logger = logging.getLogger("config")
    config_logger.info("Initializing test set")
    config_port_map = config["port_map"]
    config_config = config

if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test_spec=config"