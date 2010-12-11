"""
Test cases for testing actions taken on packets

See basic.py for other info.

It is recommended that these definitions be kept in their own
namespace as different groups of tests will likely define 
similar identifiers.

  The function test_set_init is called with a complete configuration
dictionary prior to the invocation of any tests from this file.

  The switch is actively attempting to contact the controller at the address
indicated oin oft_config

"""



import logging


import oftest.cstruct as ofp
import oftest.message as message
import oftest.action as action
import oftest.parse as parse
import oftest.instruction as instruction
import basic

import testutils

#@var port_map Local copy of the configuration map from OF port
# numbers to OS interfaces
pa_port_map = None
#@var pa_logger Local logger object
pa_logger = None
#@var pa_config Local copy of global configuration data
pa_config = None

# For test priority
#@var test_prio Set test priority for local tests
test_prio = {}

WILDCARD_VALUES = [ofp.OFPFW_IN_PORT,
                   ofp.OFPFW_DL_VLAN,
                   ofp.OFPFW_DL_TYPE,
                   ofp.OFPFW_NW_PROTO,
                   ofp.OFPFW_DL_VLAN_PCP,
                   ofp.OFPFW_NW_TOS]

MODIFY_ACTION_VALUES =  [ofp.OFPAT_SET_VLAN_VID,
                         ofp.OFPAT_SET_VLAN_PCP,
                         ofp.OFPAT_SET_DL_SRC,
                         ofp.OFPAT_SET_DL_DST,
                         ofp.OFPAT_SET_NW_SRC,
                         ofp.OFPAT_SET_NW_DST,
                         ofp.OFPAT_SET_NW_TOS,
                         ofp.OFPAT_SET_TP_SRC,
                         ofp.OFPAT_SET_TP_DST]

# Cache supported features to avoid transaction overhead
cached_supported_actions = None

TEST_VID_DEFAULT = 2

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

class DirectPacket(basic.SimpleDataPlane):
    """
    Send packet to single egress port

    Generate a packet
    Generate and install a matching flow
    Add action to direct the packet to an egress port
    Send the packet to ingress dataplane port
    Verify the packet is received at the egress port only
    """
    def runTest(self):
        self.handleFlow()

    def handleFlow(self, pkttype='TCP'):
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        if (pkttype == 'ICMP'):
            pkt = testutils.simple_icmp_packet()
        else:
            pkt = testutils.simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        act = action.action_set_output_port()

        for idx in range(len(of_ports)):
            rv = testutils.delete_all_flows(self.controller, pa_logger)
            self.assertEqual(rv, 0, "Failed to delete all flows")

            ingress_port = of_ports[idx]
            egress_port = of_ports[(idx + 1) % len(of_ports)]
            pa_logger.info("Ingress " + str(ingress_port) + 
                             " to egress " + str(egress_port))

            match.in_port = ingress_port

            request = message.flow_mod()
            request.command = ofp.OFPFC_ADD
            request.match = match
            request.buffer_id = 0xffffffff
            inst = instruction.instruction_apply_actions()
            act.port = egress_port
            self.assertTrue(inst.actions.add(act), "Could not add action")
            self.assertTrue(request.instructions.add(inst),
                            "Could not add instruction")
            pa_logger.info("Inserting flow")
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Error installing flow mod")
            testutils.do_barrier(self.controller)

            pa_logger.info("Sending packet to dp port " + 
                           str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            (rcv_port, rcv_pkt, _) = self.dataplane.poll(timeout=1)
            self.assertTrue(rcv_pkt is not None, "Did not receive packet")
            pa_logger.debug("Packet len " + str(len(rcv_pkt)) + " in on " + 
                         str(rcv_port))
            self.assertEqual(rcv_port, egress_port, "Unexpected receive port")
            self.assertEqual(str(pkt), str(rcv_pkt),
                             'Response packet does not match send packet')

class DirectPacketICMP(DirectPacket):
    """
    Send ICMP packet to single egress port

    Generate a ICMP packet
    Generate and install a matching flow
    Add action to direct the packet to an egress port
    Send the packet to ingress dataplane port
    Verify the packet is received at the egress port only
    Difference from DirectPacket test is that sent packet is ICMP
    """
    def runTest(self):
        self.handleFlow(pkttype='ICMP')

class DirectTwoPorts(basic.SimpleDataPlane):
    """
    Send packet to two egress ports

    Generate a packet
    Generate and install a matching flow
    Add action to direct the packet to two egress ports
    Send the packet to ingress dataplane port
    Verify the packet is received at the two egress ports
    """
    def runTest(self):
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        pkt = testutils.simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_set_output_port()

        for idx in range(len(of_ports)):
            rv = testutils.delete_all_flows(self.controller, pa_logger)
            self.assertEqual(rv, 0, "Failed to delete all flows")

            ingress_port = of_ports[idx]
            egress_port1 = of_ports[(idx + 1) % len(of_ports)]
            egress_port2 = of_ports[(idx + 2) % len(of_ports)]
            pa_logger.info("Ingress " + str(ingress_port) + 
                           " to egress " + str(egress_port1) + " and " +
                           str(egress_port2))

            match.in_port = ingress_port

            request = message.flow_mod()
            request.match = match
            request.buffer_id = 0xffffffff
            act.port = egress_port1
            self.assertTrue(request.actions.add(act), "Could not add action1")
            act.port = egress_port2
            self.assertTrue(request.actions.add(act), "Could not add action2")
            # pa_logger.info(request.show())

            pa_logger.info("Inserting flow")
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Error installing flow mod")
            testutils.do_barrier(self.controller)

            pa_logger.info("Sending packet to dp port " + 
                           str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            yes_ports = set([egress_port1, egress_port2])
            no_ports = set(of_ports).difference(yes_ports)

            testutils.receive_pkt_check(self.dataplane, pkt, yes_ports, no_ports,
                              self, pa_logger)

class DirectMCNonIngress(basic.SimpleDataPlane):
    """
    Multicast to all non-ingress ports

    Generate a packet
    Generate and install a matching flow
    Add action to direct the packet to all non-ingress ports
    Send the packet to ingress dataplane port
    Verify the packet is received at all non-ingress ports

    Does not use the flood action
    """
    def runTest(self):
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        pkt = testutils.simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_set_output_port()

        for ingress_port in of_ports:
            rv = testutils.delete_all_flows(self.controller, pa_logger)
            self.assertEqual(rv, 0, "Failed to delete all flows")

            pa_logger.info("Ingress " + str(ingress_port) + 
                           " all non-ingress ports")
            match.in_port = ingress_port

            request = message.flow_mod()
            request.match = match
            request.buffer_id = 0xffffffff
            for egress_port in of_ports:
                if egress_port == ingress_port:
                    continue
                act.port = egress_port
                self.assertTrue(request.actions.add(act), 
                                "Could not add output to " + str(egress_port))
            pa_logger.debug(request.show())

            pa_logger.info("Inserting flow")
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Error installing flow mod")
            testutils.do_barrier(self.controller)

            pa_logger.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            yes_ports = set(of_ports).difference([ingress_port])
            testutils.receive_pkt_check(self.dataplane, pkt, yes_ports, [ingress_port],
                              self, pa_logger)


class DirectMC(basic.SimpleDataPlane):
    """
    Multicast to all ports including ingress

    Generate a packet
    Generate and install a matching flow
    Add action to direct the packet to all non-ingress ports
    Send the packet to ingress dataplane port
    Verify the packet is received at all ports

    Does not use the flood action
    """
    def runTest(self):
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        pkt = testutils.simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_set_output_port()

        for ingress_port in of_ports:
            rv = testutils.delete_all_flows(self.controller, pa_logger)
            self.assertEqual(rv, 0, "Failed to delete all flows")

            pa_logger.info("Ingress " + str(ingress_port) + " to all ports")
            match.in_port = ingress_port

            request = message.flow_mod()
            request.match = match
            request.buffer_id = 0xffffffff
            for egress_port in of_ports:
                if egress_port == ingress_port:
                    act.port = ofp.OFPP_IN_PORT
                else:
                    act.port = egress_port
                self.assertTrue(request.actions.add(act), 
                                "Could not add output to " + str(egress_port))
            # pa_logger.info(request.show())

            pa_logger.info("Inserting flow")
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Error installing flow mod")
            testutils.do_barrier(self.controller)

            pa_logger.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            testutils.receive_pkt_check(self.dataplane, pkt, of_ports, [], self,
                              pa_logger)

class All(basic.SimpleDataPlane):
    """
    Send to OFPP_ALL port

    Generate a packet
    Generate and install a matching flow
    Add action to forward to OFPP_ALL
    Send the packet to ingress dataplane port
    Verify the packet is received at all other ports
    """
    def runTest(self):
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        pkt = testutils.simple_tcp_packet()
#        match = parse.packet_to_flow_match(pkt)
#        match.wildcards &= ~ofp.OFPFW_IN_PORT
#        self.assertTrue(match is not None, 
#                        "Could not generate flow match from pkt")
#        act = action.action_set_output_port()

        for ingress_port in of_ports:
            rv = testutils.delete_all_flows(self.controller, pa_logger)
            self.assertEqual(rv, 0, "Failed to delete all flows")

            pa_logger.info("Ingress " + str(ingress_port) + " to all ports")
#            match.in_port = ingress_port
#
#            request = message.flow_mod()
#            request.match = match
#            request.buffer_id = 0xffffffff
#            act.port = ofp.OFPP_ALL
#            self.assertTrue(request.actions.add(act), 
#                            "Could not add ALL port action")
            request = testutils.flow_msg_create(self, pkt, ing_port=ingress_port, 
                                                egr_port=ofp.OFPP_ALL)
            # already done in flow_msg_create
            #pa_logger.info(request.show())

            pa_logger.info("Inserting flow")
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Error installing flow mod")
            testutils.do_barrier(self.controller)

            pa_logger.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            yes_ports = set(of_ports).difference([ingress_port])
            testutils.receive_pkt_check(self.dataplane, pkt, yes_ports, [ingress_port],
                              self, pa_logger)

class AllPlusIngress(basic.SimpleDataPlane):
    """
    Send to OFPP_ALL port and ingress port

    Generate a packet
    Generate and install a matching flow
    Add action to forward to OFPP_ALL
    Add action to forward to ingress port
    Send the packet to ingress dataplane port
    Verify the packet is received at all other ports
    """
    def runTest(self):
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        pkt = testutils.simple_tcp_packet()
        
        act_all = action.action_set_output_port()
        act_all.port = ofp.OFPP_ALL
        act_ing = action.action_set_output_port()
        act_ing.port = ofp.OFPP_IN_PORT
        actions = [ act_all, act_ing]

        for ingress_port in of_ports:
            rv = testutils.delete_all_flows(self.controller, pa_logger)
            self.assertEqual(rv, 0, "Failed to delete all flows")

            pa_logger.info("Ingress " + str(ingress_port) + " to all ports")
        
            flow_mod = testutils.flow_msg_create(self, pkt, 
                                                 ing_port=ingress_port, 
                                                 action_list=actions, 
                                                 wildcards=~ofp.OFPFW_IN_PORT)
            flow_mod.buffer_id = 0xffffffff
            pa_logger.info(flow_mod.show())

            pa_logger.info("Inserting flow")
            rv = self.controller.message_send(flow_mod)
            self.assertTrue(rv != -1, "Error installing flow mod")
            testutils.do_barrier(self.controller)

            pa_logger.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            testutils.receive_pkt_check(self.dataplane, pkt, of_ports, [], self,
                              pa_logger)
            


################################################################

class BaseMatchCase(basic.SimpleDataPlane):
    def setUp(self):
        basic.SimpleDataPlane.setUp(self)
        self.logger = pa_logger
    def runTest(self):
        self.logger.info("BaseMatchCase")

class ExactMatch(BaseMatchCase):
    """
    Exercise exact matching for all port pairs

    Generate a packet
    Generate and install a matching flow without wildcard mask
    Add action to forward to a port
    Send the packet to the port
    Verify the packet is received at all other ports (one port at a time)
    """

    def runTest(self):
        testutils.flow_match_test(self, pa_port_map)

class ExactMatchTagged(BaseMatchCase):
    """
    Exact match for all port pairs with tagged pkts
    """

    def runTest(self):
        vid = testutils.test_param_get(self.config, 'vid', default=TEST_VID_DEFAULT)
        testutils.flow_match_test(self, pa_port_map, dl_vlan=vid)

class ExactMatchTaggedMany(BaseMatchCase):
    """
    ExactMatchTagged with many VLANS
    """

    def runTest(self):
        for vid in range(2,100,10):
            testutils.flow_match_test(self, pa_port_map, dl_vlan=vid, max_test=5)
        for vid in range(100,4000,389):
            testutils.flow_match_test(self, pa_port_map, dl_vlan=vid, max_test=5)
        testutils.flow_match_test(self, pa_port_map, dl_vlan=4094, max_test=5)

# Don't run by default
test_prio["ExactMatchTaggedMany"] = -1


class SingleWildcardMatch(BaseMatchCase):
    """
    Exercise wildcard matching for all ports

    Generate a packet
    Generate and install a matching flow with wildcard mask
    Add action to forward to a port
    Send the packet to the port
    Verify the packet is received at all other ports (one port at a time)
    Verify flow_expiration message is correct when command option is set
    """
    def runTest(self):
        for wc in WILDCARD_VALUES:
            testutils.flow_match_test(self, pa_port_map, wildcards=wc, max_test=10)

class SingleWildcardMatchTagged(BaseMatchCase):
    """
    SingleWildcardMatch with tagged packets
    """
    def runTest(self):
        vid = testutils.test_param_get(self.config, 'vid', default=TEST_VID_DEFAULT)
        for wc in WILDCARD_VALUES:
            testutils.flow_match_test(self, pa_port_map, wildcards=wc, dl_vlan=vid,
                            max_test=10)

class AllExceptOneWildcardMatch(BaseMatchCase):
    """
    Match exactly one field

    Generate a packet
    Generate and install a matching flow with wildcard all except one filed
    Add action to forward to a port
    Send the packet to the port
    Verify the packet is received at all other ports (one port at a time)
    Verify flow_expiration message is correct when command option is set
    """
    def runTest(self):
        for wc in WILDCARD_VALUES:
            all_exp_one_wildcard = ofp.OFPFW_ALL ^ wc
            testutils.flow_match_test(self, pa_port_map, wildcards=all_exp_one_wildcard)

class AllExceptOneWildcardMatchTagged(BaseMatchCase):
    """
    Match one field with tagged packets
    """
    def runTest(self):
        vid = testutils.test_param_get(self.config, 'vid', default=TEST_VID_DEFAULT)
        for wc in WILDCARD_VALUES:
            all_exp_one_wildcard = ofp.OFPFW_ALL ^ wc
            testutils.flow_match_test(self, pa_port_map, wildcards=all_exp_one_wildcard,
                            dl_vlan=vid)

class AllWildcardMatch(BaseMatchCase):
    """
    Create Wildcard-all flow and exercise for all ports

    Generate a packet
    Generate and install a matching flow with wildcard-all
    Add action to forward to a port
    Send the packet to the port
    Verify the packet is received at all other ports (one port at a time)
    Verify flow_expiration message is correct when command option is set
    """
    def runTest(self):
        testutils.flow_match_test(self, pa_port_map, wildcards=ofp.OFPFW_ALL)

class AllWildcardMatchTagged(BaseMatchCase):
    """
    AllWildcardMatch with tagged packets
    """
    def runTest(self):
        vid = testutils.test_param_get(self.config, 'vid', default=TEST_VID_DEFAULT)
        testutils.flow_match_test(self, pa_port_map, wildcards=ofp.OFPFW_ALL, 
                        dl_vlan=vid)

class TwoTable1(basic.SimpleDataPlane):
    """
    Simple two table test

    Add two flow entries:
    Table 1 Match IP Src A; send to 1, goto 2
    Table 2 Match TCP port B; send to 2

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


class AddVLANTag(BaseMatchCase):
    """
    Add a VLAN tag to an untagged packet
    """
    def runTest(self):
        new_vid = 2
        sup_acts = supported_actions_get(self)
        if not(sup_acts & 1<<ofp.OFPAT_SET_VLAN_VID):
            testutils.skip_message_emit(self, "Add VLAN tag test")
            return

        len = 100
        len_w_vid = 104
        pkt = testutils.simple_tcp_packet(pktlen=len)
        exp_pkt = testutils.simple_tcp_packet(pktlen=len_w_vid, dl_vlan_enable=True, 
                                    dl_vlan=new_vid)
        vid_act = action.action_set_vlan_vid()
        vid_act.vlan_vid = new_vid

        testutils.flow_match_test(self, pa_port_map, pkt=pkt, 
                        exp_pkt=exp_pkt, action_list=[vid_act])

class PacketOnly(basic.DataPlaneOnly):
    """
    Just send a packet thru the switch
    """
    def runTest(self):
        pkt = testutils.simple_tcp_packet()
        of_ports = pa_port_map.keys()
        of_ports.sort()
        ing_port = of_ports[0]
        pa_logger.info("Sending packet to " + str(ing_port))
        pa_logger.debug("Data: " + str(pkt).encode('hex'))
        self.dataplane.send(ing_port, str(pkt))

class PacketOnlyTagged(basic.DataPlaneOnly):
    """
    Just send a packet thru the switch
    """
    def runTest(self):
        vid = testutils.test_param_get(self.config, 'vid', default=TEST_VID_DEFAULT)
        pkt = testutils.simple_tcp_packet(dl_vlan_enable=True, dl_vlan=vid)
        of_ports = pa_port_map.keys()
        of_ports.sort()
        ing_port = of_ports[0]
        pa_logger.info("Sending packet to " + str(ing_port))
        pa_logger.debug("Data: " + str(pkt).encode('hex'))
        self.dataplane.send(ing_port, str(pkt))

test_prio["PacketOnly"] = -1
test_prio["PacketOnlyTagged"] = -1

class ModifyVID(BaseMatchCase):
    """
    Modify the VLAN ID in the VLAN tag of a tagged packet
    """
    def runTest(self):
        old_vid = 2
        new_vid = 3
        sup_acts = supported_actions_get(self)
        if not (sup_acts & 1 << ofp.OFPAT_SET_VLAN_VID):
            testutils.skip_message_emit(self, "Modify VLAN tag test")
            return

        pkt = testutils.simple_tcp_packet(dl_vlan_enable=True, dl_vlan=old_vid)
        exp_pkt = testutils.simple_tcp_packet(dl_vlan_enable=True, dl_vlan=new_vid)
        vid_act = action.action_set_vlan_vid()
        vid_act.vlan_vid = new_vid

        testutils.flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt,
                        action_list=[vid_act])

class StripVLANTag(BaseMatchCase):
    """
    Strip the VLAN tag from a tagged packet
    """
    def runTest(self):
        old_vid = 2
        sup_acts = supported_actions_get(self)
        if not (sup_acts & 1 << ofp.OFPAT_STRIP_VLAN):
            testutils.skip_message_emit(self, "Strip VLAN tag test")
            return

        len_w_vid = 104
        len = 100
        pkt = testutils.simple_tcp_packet(pktlen=len_w_vid, dl_vlan_enable=True, 
                                dl_vlan=old_vid)
        exp_pkt = testutils.simple_tcp_packet(pktlen=len)
        vid_act = action.action_strip_vlan()

        testutils.flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt,
                        action_list=[vid_act])

def init_pkt_args():
    """
    Pass back a dictionary with default packet arguments
    """
    args = {}
    args["dl_src"] = '00:23:45:67:89:AB'

    dl_vlan_enable=False
    dl_vlan=-1
    if pa_config["test-params"]["vid"]:
        dl_vlan_enable=True
        dl_vlan = pa_config["test-params"]["vid"]

# Unpack operator is ** on a dictionary

    return args

class ModifyL2Src(BaseMatchCase):
    """
    Modify the source MAC address (TP1)
    """
    def runTest(self):
        sup_acts = supported_actions_get(self)
        if not (sup_acts & 1 << ofp.OFPAT_SET_DL_SRC):
            testutils.skip_message_emit(self, "ModifyL2Src test")
            return

        (pkt, exp_pkt, acts) = testutils.pkt_action_setup(self, mod_fields=['dl_src'],
                                                check_test_params=True)
        testutils.flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)

class ModifyL2Dst(BaseMatchCase):
    """
    Modify the dest MAC address (TP1)
    """
    def runTest(self):
        sup_acts = supported_actions_get(self)
        if not (sup_acts & 1 << ofp.OFPAT_SET_DL_DST):
            testutils.skip_message_emit(self, "ModifyL2dst test")
            return

        (pkt, exp_pkt, acts) = testutils.pkt_action_setup(self, mod_fields=['dl_dst'],
                                                check_test_params=True)
        testutils.flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)

class ModifyL3Src(BaseMatchCase):
    """
    Modify the source IP address of an IP packet (TP1)
    """
    def runTest(self):
        sup_acts = supported_actions_get(self)
        if not (sup_acts & 1 << ofp.OFPAT_SET_NW_SRC):
            testutils.skip_message_emit(self, "ModifyL3Src test")
            return

        (pkt, exp_pkt, acts) = testutils.pkt_action_setup(self, mod_fields=['ip_src'],
                                                check_test_params=True)
        testutils.flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)

class ModifyL3Dst(BaseMatchCase):
    """
    Modify the dest IP address of an IP packet (TP1)
    """
    def runTest(self):
        sup_acts = supported_actions_get(self)
        if not (sup_acts & 1 << ofp.OFPAT_SET_NW_DST):
            testutils.skip_message_emit(self, "ModifyL3Dst test")
            return

        (pkt, exp_pkt, acts) = testutils.pkt_action_setup(self, mod_fields=['ip_dst'],
                                                check_test_params=True)
        testutils.flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)

class ModifyL4Src(BaseMatchCase):
    """
    Modify the source TCP port of a TCP packet (TP1)
    """
    def runTest(self):
        sup_acts = supported_actions_get(self)
        if not (sup_acts & 1 << ofp.OFPAT_SET_TP_SRC):
            testutils.skip_message_emit(self, "ModifyL4Src test")
            return

        (pkt, exp_pkt, acts) = testutils.pkt_action_setup(self, mod_fields=['tcp_sport'],
                                                check_test_params=True)
        testutils.flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)

class ModifyL4Dst(BaseMatchCase):
    """
    Modify the dest TCP port of a TCP packet (TP1)
    """
    def runTest(self):
        sup_acts = supported_actions_get(self)
        if not (sup_acts & 1 << ofp.OFPAT_SET_TP_DST):
            testutils.skip_message_emit(self, "ModifyL4Dst test")
            return

        (pkt, exp_pkt, acts) = testutils.pkt_action_setup(self, mod_fields=['tcp_dport'],
                                                check_test_params=True)
        testutils.flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)

class ModifyTOS(BaseMatchCase):
    """
    Modify the IP type of service of an IP packet (TP1)
    """
    def runTest(self):
        sup_acts = supported_actions_get(self)
        if not (sup_acts & 1 << ofp.OFPAT_SET_NW_TOS):
            testutils.skip_message_emit(self, "ModifyTOS test")
            return

        (pkt, exp_pkt, acts) = testutils.pkt_action_setup(self, mod_fields=['ip_tos'],
                                                check_test_params=True)
        testutils.flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)

#@todo Need to implement tagged versions of the above tests
#
#@todo Implement a test case that strips tag 2, adds tag 3
# and modifies tag 4 to tag 5.  Then verify (in addition) that
# tag 6 does not get modified.

class MixedVLAN(BaseMatchCase):
    """
    Test mixture of VLAN tag actions

    Strip tag 2 on port 1, send to port 2
    Add tag 3 on port 1, send to port 2
    Modify tag 4 to 5 on port 1, send to port 2
    All other traffic from port 1, send to port 3
    All traffic from port 2 sent to port 4
    Use exact matches with different packets for all mods
    Verify the following:  (port, vid)
        (port 1, vid 2) => VLAN tag stripped, out port 2
        (port 1, no tag) => tagged packet w/ vid 2 out port 2
        (port 1, vid 4) => tagged packet w/ vid 5 out port 2
        (port 1, vid 5) => tagged packet w/ vid 5 out port 2
        (port 1, vid 6) => tagged packet w/ vid 6 out port 2
        (port 2, no tag) => untagged packet out port 4
        (port 2, vid 2-6) => unmodified packet out port 4

    Variation:  Might try sending VID 5 to port 3 and check.
    If only VID 5 distinguishes pkt, this will fail on some platforms
    """   

test_prio["MixedVLAN"] = -1
 
def supported_actions_get(parent, use_cache=True):
    """
    Get the bitmap of supported actions from the switch
    If use_cache is false, the cached value will be updated
    """
    global cached_supported_actions
    if cached_supported_actions is None or not use_cache:
        request = message.table_stats_request()
        (reply, _) = parent.controller.transact(request, timeout=2)
        parent.assertTrue(reply is not None, "Did not get response to tbl stats req")
        cached_supported_actions = reply.stats[0].apply_actions
        pa_logger.info("Supported actions: " + hex(cached_supported_actions))

    return cached_supported_actions

if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test-spec=pktact"
