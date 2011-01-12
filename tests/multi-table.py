'''
Created on Dec 14, 2010

@author: capveg
'''
import logging


import oftest.cstruct as ofp
import oftest.message as message
import oftest.action as action
import oftest.parse as parse
import oftest.instruction as instruction
import basic

import testutils

def test_set_init(config):
    """
    Set up function for packet action test classes

    @param config The configuration dictionary; see oft
    """

    global pa_port_map
    global pa_logger
    global pa_config

    pa_logger = logging.getLogger("pkt_act")
    pa_logger.info("Initializing test set")
    pa_port_map = config["port_map"]
    pa_config = config
    



class TwoTable1(basic.SimpleDataPlane):
    """
    Simple two table test

    Add two flow entries:
    Table 0 Match IP Src A; send to 1, goto 1
    Table 1 Match TCP port B; send to 2

    Then send in 2 packets:
    IP A, TCP C; expect out port 1
    IP A, TCP B; expect out port 2

    Lots of negative tests are not checked
    """
    def runTest(self):
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        # Clear flow table
        rv = testutils.delete_all_flows(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        # Set up first match
        match = ofp.ofp_match()
        testutils.wildcard_all_set(match)
        match.wildcards -= ofp.OFPFW_DL_TYPE
        match.nw_src_mask = 0 # Match nw_src
        match.dl_type = 0x800
        match.nw_src = parse.parse_ip("192.168.1.10")
        act = action.action_set_output_port()
        act.port = of_ports[0]

        request = message.flow_mod()
        request.match = match
        request.buffer_id = 0xffffffff
        request.table_id = 0
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst1")
        inst = instruction.instruction_goto_table()
        inst.table_id = 1
        self.assertTrue(request.instructions.add(inst), "Could not add inst2")
        pa_logger.info("Inserting flow 1")
        rv = self.controller.message_send(request)
        # pa_logger.debug(request.show())
        self.assertTrue(rv != -1, "Error installing flow mod")

        # Set up second match
        match = ofp.ofp_match()
        testutils.wildcard_all_set(match)
        match.wildcards -= ofp.OFPFW_DL_TYPE
        match.wildcards -= ofp.OFPFW_TP_SRC
        match.dl_type = 0x800
        match.tp_src = 80
        act = action.action_set_output_port()
        act.port = of_ports[1]

        request = message.flow_mod()
        request.match = match
        request.buffer_id = 0xffffffff
        request.table_id = 1
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst3")
        pa_logger.info("Inserting flow 2")
        # pa_logger.debug(request.show())
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")
        testutils.do_barrier(self.controller)

        # Generate a packet matching only flow 1; rcv on port[0]
        pkt = testutils.simple_tcp_packet(ip_src='192.168.1.10', tcp_sport=10)
        self.dataplane.send(of_ports[2], str(pkt))
        (rcv_port, rcv_pkt, _) = self.dataplane.poll(timeout=5)
        self.assertTrue(rcv_pkt is not None, "Did not receive packet")
        pa_logger.debug("Packet len " + str(len(rcv_pkt)) + " in on " + 
                        str(rcv_port))
        self.assertEqual(rcv_port, of_ports[0], "Unexpected receive port")
        
        # Generate a packet matching both flow 1 and flow 2; rcv on port[1]
        pkt = testutils.simple_tcp_packet(ip_src='192.168.1.10', tcp_sport=80)
        self.dataplane.send(of_ports[2], str(pkt))
        (rcv_port, rcv_pkt, _) = self.dataplane.poll(timeout=5)
        self.assertTrue(rcv_pkt is not None, "Did not receive packet")
        pa_logger.debug("Packet len " + str(len(rcv_pkt)) + " in on " + 
                        str(rcv_port))
        self.assertEqual(rcv_port, of_ports[1], "Unexpected receive port")

