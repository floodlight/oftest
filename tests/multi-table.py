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
        rv = testutils.initialize_table_config(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to initialize table config")
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


def make_match(dl_type = 0x800, nw_src = "192.168.1.10"):
    """
    Making simple packet

    @param dl_type Data_link type
    @param nw_src Source IP address
    """
    match = ofp.ofp_match()
    testutils.wildcard_all_set(match)
    match.wildcards -= ofp.OFPFW_DL_TYPE
    match.nw_src_mask = 0 # Match nw_src
    match.dl_type = dl_type
    match.nw_src = parse.parse_ip(nw_src)
    return match

class MultiTableGoto(basic.SimpleDataPlane):
    """
    Simple three table test for "goto"

    Lots of negative tests are not checked
    """
    def scenario3(self, first_table = 0, second_table = 1, third_table = 2):
        """
        Add three flow entries:
        First Table; Match IP Src A; goto Second Table
        Second Table; Match IP Src A; send to 1, goto Third Table
        Third Table; Match TCP port B; send to 2

        Then send in 2 packets:
        IP A, TCP C; expect out port 1
        IP A, TCP B; expect out port 2

        @param self object instance
        @param first_table first table
        @param second_table second table
        @param third_table third table
        """
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        # Clear flow table
        rv = testutils.initialize_table_config(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to initialize table config")

        testutils.do_barrier(self.controller)

        rv = testutils.delete_all_flows(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        testutils.do_barrier(self.controller)

        # Set up first match
        request = message.flow_mod()
        request.match = make_match()
        request.buffer_id = 0xffffffff
        request.table_id = first_table
        inst = instruction.instruction_goto_table()
        inst.table_id = second_table
        self.assertTrue(request.instructions.add(inst), "Could not add inst1")
        pa_logger.info("Inserting flow 1")
        rv = self.controller.message_send(request)
        # pa_logger.debug(request.show())
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Set up second match
        act = action.action_set_output_port()
        act.port = of_ports[0]

        request = message.flow_mod()
        request.match = make_match()
        request.buffer_id = 0xffffffff
        request.table_id = second_table
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst2")
        inst = instruction.instruction_goto_table()
        inst.table_id = third_table
        self.assertTrue(request.instructions.add(inst), "Could not add inst3")
        pa_logger.info("Inserting flow 2")
        rv = self.controller.message_send(request)
        # pa_logger.debug(request.show())
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Set up third match
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
        request.table_id = third_table
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst4")
        pa_logger.info("Inserting flow 3")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Generate a packet matching only flow 1 and flow 2; rcv on port[0]
        pkt = testutils.simple_tcp_packet(ip_src='192.168.1.10', tcp_sport=10)
        self.dataplane.send(of_ports[2], str(pkt))
        (rcv_port, rcv_pkt, _) = self.dataplane.poll(timeout=5)
        self.assertTrue(rcv_pkt is not None, "Did not receive packet")
        pa_logger.debug("Packet len " + str(len(rcv_pkt)) + " in on " + 
                        str(rcv_port))
        self.assertEqual(rcv_port, of_ports[0], "Unexpected receive port")
        
        # Generate a packet matching both flow 1, 2 and 3; rcv on port[1]
        pkt = testutils.simple_tcp_packet(ip_src='192.168.1.10', tcp_sport=80)
        self.dataplane.send(of_ports[2], str(pkt))
        (rcv_port, rcv_pkt, _) = self.dataplane.poll(timeout=5)
        self.assertTrue(rcv_pkt is not None, "Did not receive packet")
        pa_logger.debug("Packet len " + str(len(rcv_pkt)) + " in on " + 
                        str(rcv_port))
        self.assertEqual(rcv_port, of_ports[1], "Unexpected receive port")

    def runTest(self):
        self.scenario3(0, 1, 2)
        self.scenario3(0, 1, 3)
        self.scenario3(0, 2, 3)
#        self.scenario3(1, 2, 3)


class MultiTableNoGoto(basic.SimpleDataPlane):
    """
    Simple four table test for "No-goto"

    Lots of negative tests are not checked
    """
    def scenario4(self, first_table = 0, second_table = 1, third_table = 2, fourth_table = 3):
        """
        Add four flow entries:
        First Table; Match IP Src A; goto Second Table
        Second Table; Match IP Src A; send to 1, goto Third Table
        Third Table; Match IP Src A; do nothing // match but stop pipeline
        Fourth Table; Match IP Src A; send to 2  // not match, just a fake

        Then send in 2 packets:
        IP A, TCP C; expect out port 1
        IP A, TCP B; expect out port 1

        @param self object instance
        @param first_table first table
        @param second_table second table
        @param third_table third table
        @param fourth_table fourth table
        """
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        # Clear flow table
        rv = testutils.initialize_table_config(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to initialize table config")

        testutils.do_barrier(self.controller)

        rv = testutils.delete_all_flows(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        testutils.do_barrier(self.controller)

        # Set up first match
        request = message.flow_mod()
        request.match = make_match()
        request.buffer_id = 0xffffffff
        request.table_id = first_table
        inst = instruction.instruction_goto_table()
        inst.table_id = second_table
        self.assertTrue(request.instructions.add(inst), "Could not add inst1")
        pa_logger.info("Inserting flow 1")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Set up second match
        act = action.action_set_output_port()
        act.port = of_ports[0]

        request = message.flow_mod()
        request.match = make_match()
        request.buffer_id = 0xffffffff
        request.table_id = second_table
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst2")
        inst = instruction.instruction_goto_table()
        inst.table_id = third_table
        self.assertTrue(request.instructions.add(inst), "Could not add inst3")
        pa_logger.info("Inserting flow 2")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Set up third match
        request = message.flow_mod()
        request.match = make_match()
        request.buffer_id = 0xffffffff
        request.table_id = third_table
        pa_logger.info("Inserting flow 3")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Set up fourth match
        act = action.action_set_output_port()
        act.port = of_ports[1]

        request = message.flow_mod()
        request.match = make_match()
        request.buffer_id = 0xffffffff
        request.table_id = fourth_table
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst4")
        pa_logger.info("Inserting flow 4")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Generate a packet matching flow 1, 2, and 3; rcv on port[0]
        pkt = testutils.simple_tcp_packet(ip_src='192.168.1.10', tcp_sport=10)
        self.dataplane.send(of_ports[2], str(pkt))
        (rcv_port, rcv_pkt, _) = self.dataplane.poll(timeout=5)
        self.assertTrue(rcv_pkt is not None, "Did not receive packet")
        pa_logger.debug("Packet len " + str(len(rcv_pkt)) + " in on " + 
                        str(rcv_port))
        self.assertEqual(rcv_port, of_ports[0], "Unexpected receive port")
        
        # Generate a packet matching flow 1, 2, and 3; rcv on port[0]
        pkt = testutils.simple_tcp_packet(ip_src='192.168.1.10', tcp_sport=80)
        self.dataplane.send(of_ports[2], str(pkt))
        (rcv_port, rcv_pkt, _) = self.dataplane.poll(timeout=5)
        self.assertTrue(rcv_pkt is not None, "Did not receive packet")
        pa_logger.debug("Packet len " + str(len(rcv_pkt)) + " in on " + 
                        str(rcv_port))
        self.assertEqual(rcv_port, of_ports[0], "Unexpected receive port")

    def runTest(self):
        self.scenario4(0,1,2,3)


class MultiTableClearAction(basic.SimpleDataPlane):
    """
    Simple four table test for "ClearAction"

    Lots of negative tests are not checked
    """
    def scenario4(self, first_table = 0, second_table = 1, third_table = 2, fourth_table = 3):
        """
        Add four flow entries:
        First Table; Match IP Src A; goto Second Table
        Second Table; Match IP Src A; send to 1, goto Third Table
        Third Table; Match IP Src A; clear action, goto Fourth Table
        Fourth Table; Match IP Src A; send to 2

        Then send in 2 packets:
        IP A, TCP C; expect out port 1
        IP A, TCP B; expect out port 1

        @param self object instance
        @param first_table first table
        @param second_table second table
        @param third_table third table
        @param fourth_table fourth table
        """
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        # Clear flow table
        rv = testutils.initialize_table_config(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to initialize table config")

        testutils.do_barrier(self.controller)

        rv = testutils.delete_all_flows(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        testutils.do_barrier(self.controller)

        # Set up first match
        request = message.flow_mod()
        request.match = make_match()
        request.buffer_id = 0xffffffff
        request.table_id = first_table
        inst = instruction.instruction_goto_table()
        inst.table_id = second_table
        self.assertTrue(request.instructions.add(inst), "Could not add inst1")
        pa_logger.info("Inserting flow 1")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Set up second match
        act = action.action_set_output_port()
        act.port = of_ports[0]

        request = message.flow_mod()
        request.match = make_match()
        request.buffer_id = 0xffffffff
        request.table_id = second_table
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst2")
        inst = instruction.instruction_goto_table()
        inst.table_id = third_table
        self.assertTrue(request.instructions.add(inst), "Could not add inst3")
        pa_logger.info("Inserting flow 2")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Set up third match
        request = message.flow_mod()
        request.match = make_match()
        request.buffer_id = 0xffffffff
        request.table_id = third_table
        inst = instruction.instruction_clear_actions()
        self.assertTrue(request.instructions.add(inst), "Could not add inst3")
        inst = instruction.instruction_goto_table()
        inst.table_id = fourth_table
        self.assertTrue(request.instructions.add(inst), "Could not add inst4")
        pa_logger.info("Inserting flow 3")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Set up fourth match
        act = action.action_set_output_port()
        act.port = of_ports[1]

        request = message.flow_mod()
        request.match = make_match()
        request.buffer_id = 0xffffffff
        request.table_id = fourth_table
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst5")
        pa_logger.info("Inserting flow 4")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Generate a packet matching flow 1, 2, and 3; rcv on port[0]
        pkt = testutils.simple_tcp_packet(ip_src='192.168.1.10', tcp_sport=10)
        self.dataplane.send(of_ports[2], str(pkt))
        (rcv_port, rcv_pkt, _) = self.dataplane.poll(timeout=5)
        self.assertTrue(rcv_pkt is not None, "Did not receive packet")
        pa_logger.debug("Packet len " + str(len(rcv_pkt)) + " in on " + 
                        str(rcv_port))
        self.assertEqual(rcv_port, of_ports[1], "Unexpected receive port")
        
        # Generate a packet matching flow 1, 2, and 3; rcv on port[0]
        pkt = testutils.simple_tcp_packet(ip_src='192.168.1.10', tcp_sport=80)
        self.dataplane.send(of_ports[2], str(pkt))
        (rcv_port, rcv_pkt, _) = self.dataplane.poll(timeout=5)
        self.assertTrue(rcv_pkt is not None, "Did not receive packet")
        pa_logger.debug("Packet len " + str(len(rcv_pkt)) + " in on " + 
                        str(rcv_port))
        self.assertEqual(rcv_port, of_ports[1], "Unexpected receive port")

    def runTest(self):
        self.scenario4(0,1,2,3)


class MultiTableMetadata(basic.SimpleDataPlane):
    """
    Simple four table test for writing and matching "Metdata"

    Lots of negative tests are not checked
    """
    def scenario4(self, first_table = 0, second_table = 1, third_table = 2, fourth_table = 3):
        """
        Add four flow entries:
        First Table; Match IP Src A; send to 1, goto Second Table
        Second Table; Match IP Src A; write metadata, goto Third Table
        Third Table; Match IP Src A and metadata; send to 2 // stop, do action
        Fourth Table; Match IP Src A; send to 1 // not match, just a trap

        Then send in 2 packets:
        IP A, TCP C; expect out port 2
        IP A, TCP B; expect out port 2

        @param self object instance
        @param first_table first table
        @param second_table second table
        @param third_table third table
        @param fourth_table fourth table
        """
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        # Clear flow table
        rv = testutils.initialize_table_config(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to initialize table config")

        testutils.do_barrier(self.controller)

        rv = testutils.delete_all_flows(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        testutils.do_barrier(self.controller)

        # Set up first match
        act = action.action_set_output_port()
        act.port = of_ports[0]

        request = message.flow_mod()
        request.match = make_match()
        request.buffer_id = 0xffffffff
        request.table_id = first_table
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst1")
        inst = instruction.instruction_goto_table()
        inst.table_id = second_table
        self.assertTrue(request.instructions.add(inst), "Could not add inst2")
        pa_logger.info("Inserting flow 1")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Set up second match
        request = message.flow_mod()
        request.match = make_match()
        request.buffer_id = 0xffffffff
        request.table_id = second_table
        inst = instruction.instruction_write_metadata()
        inst.metadata =      0xfedcba9876543210
        inst.metadata_mask = 0xffffffffffffffff
        self.assertTrue(request.instructions.add(inst), "Could not add inst3")
        inst = instruction.instruction_goto_table()
        inst.table_id = third_table
        self.assertTrue(request.instructions.add(inst), "Could not add inst4")
        pa_logger.info("Inserting flow 2")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Set up third match
        match = ofp.ofp_match()
        testutils.wildcard_all_set(match)
        match.wildcards -= ofp.OFPFW_DL_TYPE
        match.nw_src_mask = 0 # Match nw_src
        match.dl_type = 0x800
        match.nw_src = parse.parse_ip("192.168.1.10")
        match.metadata =      0xfedcba9876543210
        match.metadata_mask = 0xffffffffffffffff
        act = action.action_set_output_port()
        act.port = of_ports[1]

        request = message.flow_mod()
        request.match = match
        request.buffer_id = 0xffffffff
        request.table_id = third_table
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst5")
        pa_logger.info("Inserting flow 3")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Set up fourth match
        act = action.action_set_output_port()
        act.port = of_ports[0]

        request = message.flow_mod()
        request.match = make_match()
        request.buffer_id = 0xffffffff
        request.table_id = fourth_table
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst6")
        pa_logger.info("Inserting flow 4")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Generate a packet matching flow 1, 2, and 3; rcv on port[0]
        pkt = testutils.simple_tcp_packet(ip_src='192.168.1.10', tcp_sport=10)
        self.dataplane.send(of_ports[2], str(pkt))
        (rcv_port, rcv_pkt, _) = self.dataplane.poll(timeout=5)
        self.assertTrue(rcv_pkt is not None, "Did not receive packet")
        pa_logger.debug("Packet len " + str(len(rcv_pkt)) + " in on " + 
                        str(rcv_port))
        self.assertEqual(rcv_port, of_ports[1], "Unexpected receive port")
        
        # Generate a packet matching flow 1, 2, and 3; rcv on port[0]
        pkt = testutils.simple_tcp_packet(ip_src='192.168.1.10', tcp_sport=80)
        self.dataplane.send(of_ports[2], str(pkt))
        (rcv_port, rcv_pkt, _) = self.dataplane.poll(timeout=5)
        self.assertTrue(rcv_pkt is not None, "Did not receive packet")
        pa_logger.debug("Packet len " + str(len(rcv_pkt)) + " in on " + 
                        str(rcv_port))
        self.assertEqual(rcv_port, of_ports[1], "Unexpected receive port")
    def runTest(self):
        self.scenario4(0,1,2,3)


class MultiTableEmptyInstruction(basic.SimpleDataPlane):
    """
    Simple four table test for "Empty Instruction"

    Lots of negative tests are not checked
    """
    def scenario4(self, first_table = 0, second_table = 1, third_table = 2, fourth_table = 3):
        """
        ** Currently, same scenario with "NoGoto" **

        Add four flow entries:
        First Table; Match IP Src A; goto Second Table
        Second Table; Match IP Src A; send to 1, goto Third Table
        Third Table; Match IP Src A; do nothing // match but stop pipeline
        Fourth Table; Match IP Src A; send to 2  // not match, just a fake

        Then send in 2 packets:
        IP A, TCP C; expect out port 1
        IP A, TCP B; expect out port 1

        @param self object instance
        @param first_table first table
        @param second_table second table
        @param third_table third table
        @param fourth_table fourth table
        """
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        # Clear flow table
        rv = testutils.initialize_table_config(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to initialize table config")

        testutils.do_barrier(self.controller)

        rv = testutils.delete_all_flows(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        testutils.do_barrier(self.controller)

        # Set up first match
        request = message.flow_mod()
        request.match = make_match()
        request.buffer_id = 0xffffffff
        request.table_id = first_table
        inst = instruction.instruction_goto_table()
        inst.table_id = second_table
        self.assertTrue(request.instructions.add(inst), "Could not add inst1")
        pa_logger.info("Inserting flow 1")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Set up second match
        act = action.action_set_output_port()
        act.port = of_ports[0]

        request = message.flow_mod()
        request.match = make_match()
        request.buffer_id = 0xffffffff
        request.table_id = second_table
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst2")
        inst = instruction.instruction_goto_table()
        inst.table_id = third_table
        self.assertTrue(request.instructions.add(inst), "Could not add inst3")
        pa_logger.info("Inserting flow 2")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Set up third match
        request = message.flow_mod()
        request.match = make_match()
        request.buffer_id = 0xffffffff
        request.table_id = third_table
        pa_logger.info("Inserting flow 3")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Set up fourth match
        act = action.action_set_output_port()
        act.port = of_ports[1]

        request = message.flow_mod()
        request.match = make_match()
        request.buffer_id = 0xffffffff
        request.table_id = fourth_table
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst4")
        pa_logger.info("Inserting flow 4")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Generate a packet matching flow 1, 2, and 3; rcv on port[0]
        pkt = testutils.simple_tcp_packet(ip_src='192.168.1.10', tcp_sport=10)
        self.dataplane.send(of_ports[2], str(pkt))
        (rcv_port, rcv_pkt, _) = self.dataplane.poll(timeout=5)
        self.assertTrue(rcv_pkt is not None, "Did not receive packet")
        pa_logger.debug("Packet len " + str(len(rcv_pkt)) + " in on " + 
                        str(rcv_port))
        self.assertEqual(rcv_port, of_ports[0], "Unexpected receive port")
        
        # Generate a packet matching flow 1, 2, and 3; rcv on port[0]
        pkt = testutils.simple_tcp_packet(ip_src='192.168.1.10', tcp_sport=80)
        self.dataplane.send(of_ports[2], str(pkt))
        (rcv_port, rcv_pkt, _) = self.dataplane.poll(timeout=5)
        self.assertTrue(rcv_pkt is not None, "Did not receive packet")
        pa_logger.debug("Packet len " + str(len(rcv_pkt)) + " in on " + 
                        str(rcv_port))
        self.assertEqual(rcv_port, of_ports[0], "Unexpected receive port")

    def runTest(self):
        self.scenario4(0,1,2,3)


class MultiTableMiss(basic.SimpleDataPlane):
    """
    Simple four table test for all miss (not match)

    Lots of negative tests are not checked
    """
    def scenario4(self, first_table = 0, second_table = 1, third_table = 2, fourth_table = 3):
        """
        Add five flow entries:
        First Table; Match IP Src A; send to 1
        Second Table; Match IP Src B; send to 1
        Third Table; Match IP Src C; send to 1
        Fourth Table; Match IP Src D; send to 1

        Then send in 2 packets:
        IP F, TCP C; expect packet_in
        IP G, TCP B; expect packet_in

        @param self object instance
        @param first_table first table
        @param second_table second table
        @param third_table third table
        @param fourth_table fourth table
        """
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        # Clear flow table
        rv = testutils.initialize_table_config(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to initialize table config")

        testutils.do_barrier(self.controller)

        rv = testutils.delete_all_flows(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        testutils.do_barrier(self.controller)

        # Set up first match
        act = action.action_set_output_port()
        act.port = of_ports[0]

        request = message.flow_mod()
        request.match = make_match()
        request.buffer_id = 0xffffffff
        request.table_id = first_table
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst1")
        pa_logger.info("Inserting flow 1")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Set up second match
        act = action.action_set_output_port()
        act.port = of_ports[0]

        request = message.flow_mod()
        request.match = make_match(nw_src = "192.168.1.20")
        request.buffer_id = 0xffffffff
        request.table_id = second_table
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst1")
        pa_logger.info("Inserting flow 1")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Set up third match
        act = action.action_set_output_port()
        act.port = of_ports[0]

        request = message.flow_mod()
        request.match = make_match(nw_src = "192.168.1.30")
        request.buffer_id = 0xffffffff
        request.table_id = third_table
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst2")
        pa_logger.info("Inserting flow 1")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Set up fourth match
        act = action.action_set_output_port()
        act.port = of_ports[0]

        request = message.flow_mod()
        request.match = make_match(nw_src = "192.168.1.40")
        request.buffer_id = 0xffffffff
        request.table_id = fourth_table
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst3")
        pa_logger.info("Inserting flow 1")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)


        # Generate a packet not matching to any flow, then packet_in
        pkt = testutils.simple_tcp_packet(ip_src='192.168.1.70', tcp_sport=10)
        self.dataplane.send(of_ports[2], str(pkt))
        (response, _) = self.controller.poll(ofp.OFPT_PACKET_IN, 2)
        self.assertTrue(response is not None, 
            'Packet in message not received for port ' + str(of_ports[2]))
        pa_logger.debug("Packet In")
        if str(pkt) != response.data:
            pa_logger.debug("pkt  len " + str(len(str(pkt))) +
                               ": " + str(pkt))
            pa_logger.debug("resp len " + str(len(str(response.data))) +
                               ": " + str(response.data))
        self.assertEqual(str(pkt), response.data,
                         'Response packet does not match send packet' +
                         ' for port ' + str(of_ports[2]))
    def runTest(self):
        self.scenario4(0,1,2,3)


class MultiTableConfigContinue(basic.SimpleDataPlane):
    """
    Simple table config test for "continue"

    Lots of negative tests are not checked
    """
    def scenario2(self, first_table = 0, second_table = 1):
        """
        Set table config as "Send to Controller" and add flow entry:
        First Table; Match IP Src A; send to 1 // not match then continue
        Second Table; Match IP Src B; send to 2 // do execution

        Then send in 2 packets:
        IP B; expect out port 2
        """
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        rv = testutils.initialize_table_config(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to initialize table config")

        testutils.do_barrier(self.controller)

        # Set table config as "send to controller"
        request = message.table_mod()
        request.table_id = 0
        request.config = ofp.OFPTC_TABLE_MISS_CONTINUE
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error configuring table")
        testutils.do_barrier(self.controller)

        # Clear flow table
        rv = testutils.delete_all_flows(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        testutils.do_barrier(self.controller)

        # Set up first match
        act = action.action_set_output_port()
        act.port = of_ports[0]

        request = message.flow_mod()
        request.match = make_match()
        request.buffer_id = 0xffffffff
        request.table_id = first_table
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst1")
        pa_logger.info("Inserting flow 1")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Set up second match
        act = action.action_set_output_port()
        act.port = of_ports[1]

        request = message.flow_mod()
        request.match = make_match(nw_src = "192.168.1.70")
        request.buffer_id = 0xffffffff
        request.table_id = second_table
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst2")
        pa_logger.info("Inserting flow 2")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Generate a packet not matching in the first table, but in the second
        pkt = testutils.simple_tcp_packet(ip_src='192.168.1.70', tcp_sport=10)
        self.dataplane.send(of_ports[2], str(pkt))

        (rcv_port, rcv_pkt, _) = self.dataplane.poll(timeout=5)
        self.assertTrue(rcv_pkt is not None, "Did not receive packet")
        pa_logger.debug("Packet len " + str(len(rcv_pkt)) + " in on " + 
                        str(rcv_port))
        self.assertEqual(rcv_port, of_ports[1], "Unexpected receive port")

    def runTest(self):
        self.scenario2(0,1)


class MultiTableConfigController(basic.SimpleDataPlane):
    """
    Simple table config test for "controller"

    Lots of negative tests are not checked
    """
    def scenario2(self, first_table = 0, second_table = 1):
        """
        Set the first table config as "Send to Controller" and the second
        table as "Drop", add flow entries:
        First Table; Match IP Src A; send to 1 // if not match, packet_in
        Second Table; Match IP Src B; send to 2 // if not match, drop

        Then send a packet:
        IP B; expect packet_in
        """
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        rv = testutils.initialize_table_config(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to initialize table config")

        testutils.do_barrier(self.controller)

        # Set table config as "send to controller"
        request = message.table_mod()
        request.table_id = first_table
        request.config = ofp.OFPTC_TABLE_MISS_CONTROLLER
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error configuring table")

        testutils.do_barrier(self.controller)

        # Set table config as "drop"
        request = message.table_mod()
        request.table_id = second_table
        request.config = ofp.OFPTC_TABLE_MISS_DROP
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error configuring table")

        testutils.do_barrier(self.controller)

        # Clear flow table
        rv = testutils.delete_all_flows(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        testutils.do_barrier(self.controller)

        # Set up first match
        act = action.action_set_output_port()
        act.port = of_ports[0]

        request = message.flow_mod()
        request.match = make_match()
        request.buffer_id = 0xffffffff
        request.table_id = first_table
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst1")
        pa_logger.info("Inserting flow 1")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Set up second match
        act = action.action_set_output_port()
        act.port = of_ports[1]

        request = message.flow_mod()
        request.match = make_match(nw_src = "192.168.1.70")
        request.buffer_id = 0xffffffff
        request.table_id = second_table
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst2")
        pa_logger.info("Inserting flow 2")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Generate a packet not matching to any flow entry in the first table
        pkt = testutils.simple_tcp_packet(ip_src='192.168.1.70', tcp_sport=10)
        self.dataplane.send(of_ports[2], str(pkt))
        (response, _) = self.controller.poll(ofp.OFPT_PACKET_IN, 2)
        self.assertTrue(response is not None, 
            'Packet in message not received for port ' + str(of_ports[2]))
        pa_logger.debug("Packet In")
        if str(pkt) != response.data:
            pa_logger.debug("pkt  len " + str(len(str(pkt))) +
                            ": " + str(pkt))
            pa_logger.debug("resp len " + str(len(str(response.data))) +
                            ": " + str(response.data))
        self.assertEqual(str(pkt), response.data,
                         'Response packet does not match send packet' +
                         ' for port ' + str(of_ports[2]))

    def runTest(self):
        self.scenario2(0,1)


class MultiTableConfigDrop(basic.SimpleDataPlane):
    """
    Simple table config test for "drop"

    Lots of negative tests are not checked
    """
    def scenario2(self, first_table = 0, second_table = 1):
        """
        Set the first table config as "Drop" and second table as "Controller"
        add flow entry:
        First Table; Match IP Src A; send to 1 // if not match, then drop
        Second Table; Match IP Src B; send to 2 // if not match, controller

        Then send in a packet:
        IP B; expect drop
        """
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        rv = testutils.initialize_table_config(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to initialize table config")

        testutils.do_barrier(self.controller)

        # Set table config as "drop"
        request = message.table_mod()
        request.table_id = first_table
        request.config = ofp.OFPTC_TABLE_MISS_DROP
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error configuring table")

        testutils.do_barrier(self.controller)

        # Set table config as "send to controller"
        request = message.table_mod()
        request.table_id = second_table
        request.config = ofp.OFPTC_TABLE_MISS_CONTROLLER
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error configuring table")

        testutils.do_barrier(self.controller)

        # Clear flow table
        rv = testutils.delete_all_flows(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        testutils.do_barrier(self.controller)

        # Set up first match
        act = action.action_set_output_port()
        act.port = of_ports[0]

        request = message.flow_mod()
        request.match = make_match()
        request.buffer_id = 0xffffffff
        request.table_id = first_table
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst1")
        pa_logger.info("Inserting flow 1")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Set up second match
        act = action.action_set_output_port()
        act.port = of_ports[1]

        request = message.flow_mod()
        request.match = make_match(nw_src = "192.168.1.70")
        request.buffer_id = 0xffffffff
        request.table_id = second_table
        inst = instruction.instruction_write_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(request.instructions.add(inst), "Could not add inst2")
        pa_logger.info("Inserting flow 2")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")

        testutils.do_barrier(self.controller)

        # Generate a packet not matching to any flow, then drop
        pkt = testutils.simple_tcp_packet(ip_src='192.168.1.70', tcp_sport=10)
        self.dataplane.send(of_ports[2], str(pkt))
        # checks no response from controller and dataplane
        (response, _) = self.controller.poll(ofp.OFPT_PACKET_IN, 2)
        # self.assertIsNone() is preferable for newer python
        self.assertFalse(response is not None, "PacketIn message is received")
        (_, rcv_pkt, _) = self.dataplane.poll(timeout=5)
        self.assertFalse(rcv_pkt is not None, "Packet on dataplane")

    def runTest(self):
        self.scenario2(0,1)

class TwoTableApplyActGenericSimple(basic.SimpleDataPlane):
    """
    Test if apply_action on one table is effective to the next table
    Table0: Modify one field and apply
    Table1: Match against modified pkt and send out to a port
    Expect packet with a modification
    """
    def __init__(self):
        basic.SimpleDataPlane.__init__(self)

        self.base_pkt_params = {}
        self.base_pkt_params['pktlen'] = 100
        self.base_pkt_params['dl_dst'] = '00:DE:F0:12:34:56'
        self.base_pkt_params['dl_src'] = '00:23:45:67:89:AB'
        self.base_pkt_params['dl_vlan_enable'] = True
        self.base_pkt_params['dl_vlan'] = 2
        self.base_pkt_params['dl_vlan_pcp'] = 0
        self.base_pkt_params['ip_src'] = '192.168.0.1'
        self.base_pkt_params['ip_dst'] = '192.168.0.2'
        self.base_pkt_params['ip_tos'] = 0
        self.base_pkt_params['tcp_sport'] = 1234
        self.base_pkt_params['tcp_dport'] = 80

        self.start_pkt_params = self.base_pkt_params.copy()
        del self.start_pkt_params['dl_vlan_enable']
        del self.start_pkt_params['pktlen']

        self.mod_pkt_params = {}
        self.mod_pkt_params['pktlen'] = 100
        self.mod_pkt_params['dl_dst'] = '00:21:0F:ED:CB:A9'
        self.mod_pkt_params['dl_src'] = '00:ED:CB:A9:87:65'
        self.mod_pkt_params['dl_vlan'] = 3
        self.mod_pkt_params['dl_vlan_pcp'] = 7
        self.mod_pkt_params['ip_src'] = '10.20.30.40'
        self.mod_pkt_params['ip_dst'] = '50.60.70.80'
        self.mod_pkt_params['ip_tos'] = 0xf0
        self.mod_pkt_params['tcp_sport'] = 4321
        self.mod_pkt_params['tcp_dport'] = 8765

    def runTest(self):
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        # For making the test simpler...
        ing_port = of_ports[0]
        egr_port = of_ports[1]
        check_expire_tbl0 = False
        check_expire_tbl1 = False

        # Clear flow table
        rv = testutils.initialize_table_config(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to initialize table config")
        rv = testutils.delete_all_flows(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        # Build the ingress packet
        pkt = testutils.simple_tcp_packet(**self.base_pkt_params)

        # Set action for the first table
        for item_tbl0 in self.start_pkt_params:
            tbl0_pkt_params = self.base_pkt_params.copy()
            tbl0_pkt_params[item_tbl0] = self.mod_pkt_params[item_tbl0]
            act = testutils.action_generate(self, item_tbl0, tbl0_pkt_params)
            action_list = [act]

            inst_1 = instruction.instruction_apply_actions()
            inst_2 = instruction.instruction_goto_table()
            inst_2.table_id = 1
            inst_list = [inst_1, inst_2]
            request0 = testutils.flow_msg_create(self, pkt,
                              ing_port=ing_port,
                              instruction_list=inst_list,
                              action_list=action_list,
                              check_expire=check_expire_tbl0,
                              table_id=0)

            exp_pkt = testutils.simple_tcp_packet(**tbl0_pkt_params)

            request1 = testutils.flow_msg_create(self, exp_pkt,
                              ing_port=ing_port,
                              check_expire=check_expire_tbl1,
                              table_id=1,
                              egr_port=egr_port)

            # Insert two flows
            self.logger.debug("Inserting flows: Modify-field: " + item_tbl0)
            testutils.flow_msg_install(self, request0)
            testutils.flow_msg_install(self, request1)

            # Send pkt
            self.logger.debug("Send packet: " + str(ing_port) +
                              " to " + str(egr_port))
            self.dataplane.send(ing_port, str(pkt))

            #@todo Not all HW supports both pkt and byte counters
            #@todo We shouldn't expect the order of coming response..
            if check_expire_tbl0:
                flow_removed_verify(self, request0, pkt_count=1,
                                    byte_count=pktlen)
            if check_expire_tbl1:
                flow_removed_verify(self, request1, pkt_count=1,
                                    byte_count=exp_pktlen)
            # Receive and verify pkt
            testutils.receive_pkt_verify(self, egr_port, exp_pkt)

class TwoTableApplyActGeneric2Mod(TwoTableApplyActGenericSimple):
    """
    Test if apply_action on one table is effective to the next table
    Table0: Modify one field and apply
    Table1: Match against modified pkt, modify another field and send out
    Expect packet with two modifications
    """
    def runTest(self):
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        # For making the test simpler...
        ing_port = of_ports[0]
        egr_port = of_ports[1]
        check_expire_tbl0 = False
        check_expire_tbl1 = False

        # Clear flow table
        rv = testutils.initialize_table_config(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to initialize table config")
        rv = testutils.delete_all_flows(self.controller, pa_logger)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        # Build the ingress packet
        pkt = testutils.simple_tcp_packet(**self.base_pkt_params)

        # Set action for the first table
        for item_tbl0 in self.start_pkt_params:
            tbl0_pkt_params = self.base_pkt_params.copy()
            tbl0_pkt_params[item_tbl0] = self.mod_pkt_params[item_tbl0]
            act = testutils.action_generate(self, item_tbl0, tbl0_pkt_params)
            action_list = [act]

            inst_1 = instruction.instruction_apply_actions()
            inst_2 = instruction.instruction_goto_table()
            inst_2.table_id = 1
            inst_list = [inst_1, inst_2]
            request0 = testutils.flow_msg_create(self, pkt,
                              ing_port=ing_port,
                              instruction_list=inst_list,
                              action_list=action_list,
                              check_expire=check_expire_tbl0,
                              table_id=0)

            mod_pkt = testutils.simple_tcp_packet(**tbl0_pkt_params)

            for item_tbl1 in self.start_pkt_params:
                if item_tbl1 == item_tbl0:
                    continue
                tbl1_pkt_params = tbl0_pkt_params.copy()
                tbl1_pkt_params[item_tbl1] = self.mod_pkt_params[item_tbl1]
                act = testutils.action_generate(self, item_tbl1,
                                                tbl1_pkt_params)
                self.assertTrue(act is not None, "Action not available")
                action_list = [act]

                request1 = testutils.flow_msg_create(self, mod_pkt,
                              ing_port=ing_port,
                              action_list=action_list,
                              check_expire=check_expire_tbl1,
                              table_id=1,
                              egr_port=egr_port)

                exp_pkt = testutils.simple_tcp_packet(**tbl1_pkt_params)

                # Insert two flows
                self.logger.debug("Inserting flows: Modify-fields: TBL0= " +
                                  item_tbl0 + ", TBL1= " + item_tbl1)
                testutils.flow_msg_install(self, request0)
                testutils.flow_msg_install(self, request1)

                # Send pkt
                self.logger.debug("Send packet: " + str(ing_port) +
                                  " to " + str(egr_port))
                self.dataplane.send(ing_port, str(pkt))

                #@todo Not all HW supports both pkt and byte counters
                #@todo We shouldn't expect the order of coming response..
                if check_expire_tbl0:
                    flow_removed_verify(self, request0, pkt_count=1,
                                        byte_count=pktlen)
                if check_expire_tbl1:
                    flow_removed_verify(self, request1, pkt_count=1,
                                        byte_count=exp_pktlen)
                # Receive and verify pkt
                testutils.receive_pkt_verify(self, egr_port, exp_pkt)
