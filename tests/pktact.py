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

import copy

import logging

import unittest

import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action
import oftest.parse as parse
import basic

from testutils import *

#@var port_map Local copy of the configuration map from OF port
# numbers to OS interfaces
pa_port_map = None
#@var pa_logger Local logger object
pa_logger = None
#@var pa_config Local copy of global configuration data
pa_config = None

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

        global pa_port_map
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        if (pkttype == 'ICMP'):
            pkt = simple_icmp_packet()
        else:
            pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        for idx in range(len(of_ports)):
            rv = delete_all_flows(self.controller, pa_logger)
            self.assertEqual(rv, 0, "Failed to delete all flows")

            ingress_port = of_ports[idx]
            egress_port = of_ports[(idx + 1) % len(of_ports)]
            pa_logger.info("Ingress " + str(ingress_port) + 
                        " to egress " + str(egress_port))

            match.in_port = ingress_port

            request = message.flow_mod()
            request.match = match
            request.buffer_id = 0xffffffff
            act.port = egress_port
            self.assertTrue(request.actions.add(act), "Could not add action")

            pa_logger.info("Inserting flow")
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Error installing flow mod")
            do_barrier(self.controller)

            pa_logger.info("Sending packet to dp port " + 
                           str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            (rcv_port, rcv_pkt, pkt_time) = self.dataplane.poll(timeout=1)
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
        global pa_port_map
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        for idx in range(len(of_ports)):
            rv = delete_all_flows(self.controller, pa_logger)
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
            do_barrier(self.controller)

            pa_logger.info("Sending packet to dp port " + 
                           str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            yes_ports = set([egress_port1, egress_port2])
            no_ports = set(of_ports).difference(yes_ports)

            receive_pkt_check(self.dataplane, pkt, yes_ports, no_ports,
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
        global pa_port_map
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        for ingress_port in of_ports:
            rv = delete_all_flows(self.controller, pa_logger)
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
            do_barrier(self.controller)

            pa_logger.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            yes_ports = set(of_ports).difference([ingress_port])
            receive_pkt_check(self.dataplane, pkt, yes_ports, [ingress_port],
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
        global pa_port_map
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        for ingress_port in of_ports:
            rv = delete_all_flows(self.controller, pa_logger)
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
            do_barrier(self.controller)

            pa_logger.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            receive_pkt_check(self.dataplane, pkt, of_ports, [], self,
                              pa_logger)

class Flood(basic.SimpleDataPlane):
    """
    Flood to all ports except ingress

    Generate a packet
    Generate and install a matching flow
    Add action to flood the packet
    Send the packet to ingress dataplane port
    Verify the packet is received at all other ports
    """
    def runTest(self):
        global pa_port_map
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        for ingress_port in of_ports:
            rv = delete_all_flows(self.controller, pa_logger)
            self.assertEqual(rv, 0, "Failed to delete all flows")

            pa_logger.info("Ingress " + str(ingress_port) + " to all ports")
            match.in_port = ingress_port

            request = message.flow_mod()
            request.match = match
            request.buffer_id = 0xffffffff
            act.port = ofp.OFPP_FLOOD
            self.assertTrue(request.actions.add(act), 
                            "Could not add flood port action")
            pa_logger.info(request.show())

            pa_logger.info("Inserting flow")
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Error installing flow mod")
            do_barrier(self.controller)

            pa_logger.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            yes_ports = set(of_ports).difference([ingress_port])
            receive_pkt_check(self.dataplane, pkt, yes_ports, [ingress_port],
                              self, pa_logger)

class FloodPlusIngress(basic.SimpleDataPlane):
    """
    Flood to all ports plus send to ingress port

    Generate a packet
    Generate and install a matching flow
    Add action to flood the packet
    Add action to send to ingress port
    Send the packet to ingress dataplane port
    Verify the packet is received at all other ports
    """
    def runTest(self):
        global pa_port_map
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        for ingress_port in of_ports:
            rv = delete_all_flows(self.controller, pa_logger)
            self.assertEqual(rv, 0, "Failed to delete all flows")

            pa_logger.info("Ingress " + str(ingress_port) + " to all ports")
            match.in_port = ingress_port

            request = message.flow_mod()
            request.match = match
            request.buffer_id = 0xffffffff
            act.port = ofp.OFPP_FLOOD
            self.assertTrue(request.actions.add(act), 
                            "Could not add flood port action")
            act.port = ofp.OFPP_IN_PORT
            self.assertTrue(request.actions.add(act), 
                            "Could not add ingress port for output")
            pa_logger.info(request.show())

            pa_logger.info("Inserting flow")
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Error installing flow mod")
            do_barrier(self.controller)

            pa_logger.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            receive_pkt_check(self.dataplane, pkt, of_ports, [], self,
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
        global pa_port_map
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        for ingress_port in of_ports:
            rv = delete_all_flows(self.controller, pa_logger)
            self.assertEqual(rv, 0, "Failed to delete all flows")

            pa_logger.info("Ingress " + str(ingress_port) + " to all ports")
            match.in_port = ingress_port

            request = message.flow_mod()
            request.match = match
            request.buffer_id = 0xffffffff
            act.port = ofp.OFPP_ALL
            self.assertTrue(request.actions.add(act), 
                            "Could not add ALL port action")
            pa_logger.info(request.show())

            pa_logger.info("Inserting flow")
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Error installing flow mod")
            do_barrier(self.controller)

            pa_logger.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            yes_ports = set(of_ports).difference([ingress_port])
            receive_pkt_check(self.dataplane, pkt, yes_ports, [ingress_port],
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
        global pa_port_map
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        for ingress_port in of_ports:
            rv = delete_all_flows(self.controller, pa_logger)
            self.assertEqual(rv, 0, "Failed to delete all flows")

            pa_logger.info("Ingress " + str(ingress_port) + " to all ports")
            match.in_port = ingress_port

            request = message.flow_mod()
            request.match = match
            request.buffer_id = 0xffffffff
            act.port = ofp.OFPP_ALL
            self.assertTrue(request.actions.add(act), 
                            "Could not add ALL port action")
            act.port = ofp.OFPP_IN_PORT
            self.assertTrue(request.actions.add(act), 
                            "Could not add ingress port for output")
            pa_logger.info(request.show())

            pa_logger.info("Inserting flow")
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Error installing flow mod")
            do_barrier(self.controller)

            pa_logger.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            receive_pkt_check(self.dataplane, pkt, of_ports, [], self,
                              pa_logger)
            
class FloodMinusPort(basic.SimpleDataPlane):
    """
    Config port with No_Flood and test Flood action

    Generate a packet
    Generate a matching flow
    Add action to forward to OFPP_ALL
    Set port to no-flood
    Send the packet to ingress dataplane port
    Verify the packet is received at all other ports except
    the ingress port and the no_flood port
    """
    def runTest(self):
        global pa_port_map
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        for idx in range(len(of_ports)):
            rv = delete_all_flows(self.controller, pa_logger)
            self.assertEqual(rv, 0, "Failed to delete all flows")

            ingress_port = of_ports[idx]
            no_flood_idx = (idx + 1) % len(of_ports)
            no_flood_port = of_ports[no_flood_idx]
            rv = port_config_set(self.controller, no_flood_port,
                                 ofp.OFPPC_NO_FLOOD, ofp.OFPPC_NO_FLOOD,
                                 pa_logger)
            self.assertEqual(rv, 0, "Failed to set port config")

            match.in_port = ingress_port

            request = message.flow_mod()
            request.match = match
            request.buffer_id = 0xffffffff
            act.port = ofp.OFPP_FLOOD
            self.assertTrue(request.actions.add(act), 
                            "Could not add flood port action")
            pa_logger.info(request.show())

            pa_logger.info("Inserting flow")
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Error installing flow mod")
            do_barrier(self.controller)

            pa_logger.info("Sending packet to dp port " + str(ingress_port))
            pa_logger.info("No flood port is " + str(no_flood_port))
            self.dataplane.send(ingress_port, str(pkt))
            no_ports = set([ingress_port, no_flood_port])
            yes_ports = set(of_ports).difference(no_ports)
            receive_pkt_check(self.dataplane, pkt, yes_ports, no_ports, self,
                              pa_logger)

            # Turn no flood off again
            rv = port_config_set(self.controller, no_flood_port,
                                 0, ofp.OFPPC_NO_FLOOD, pa_logger)
            self.assertEqual(rv, 0, "Failed to reset port config")

            #@todo Should check no other packets received

class SimpleExactMatch(basic.SimpleDataPlane):
    """
    Exercise exact matching for all ports

    Generate a packet
    Generate and install a matching flow without wildcard mask
    Add action to forward to a port
    Send the packet to the port
    Verify the packet is received at all other ports (one port at a time)
    Verify flow_expiration message is correct when command option is set
    """
    IP_ETHTYPE = 0x800
    TCP_PROTOCOL = 0x6
    UDP_PROTOCOL = 0x11

    def runTest(self):
        self.flowMatchTest()

    def flowMatchTest(self, wildcards=0, check_expire=False):
        global pa_port_map
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        self.assertTrue(match is not None,
                        "Could not generate flow match from pkt")
        match.dl_vlan = ofp.OFP_VLAN_NONE
        match.nw_proto = self.TCP_PROTOCOL
        match.wildcards = wildcards

        for idx in range(len(of_ports)):
            ingress_port = of_ports[idx]
            pa_logger.info("Ingress " + str(ingress_port) + " to all the other ports")
            match.in_port = ingress_port

            for egr_idx in range(len(of_ports)):
                if egr_idx == idx:
                    continue

                rc = delete_all_flows(self.controller, pa_logger)
                self.assertEqual(rc, 0, "Failed to delete all flows")
                do_barrier(self.controller)

                request = message.flow_mod()
                request.match = match
                request.buffer_id = 0xffffffff
                #@todo Need UI to setup FLAGS parameter for flow_mod
                if(check_expire):
                    request.flags |= ofp.OFPFF_SEND_FLOW_REM
                    request.hard_timeout = 1

                act = action.action_output()
                act.port = of_ports[egr_idx]
                self.assertTrue(request.actions.add(act),
                                "Could not add output action")
                pa_logger.info(request.show())

                pa_logger.info("Inserting flow")
                rv = self.controller.message_send(request)
                self.assertTrue(rv != -1, "Error installing flow mod")
                do_barrier(self.controller)

                pa_logger.info("Sending packet to dp port " +str(ingress_port))
                self.dataplane.send(ingress_port, str(pkt))

                ofport = of_ports[egr_idx]
                self.verifPkt(ofport, pkt)

                #@todo Need UI for enabling response-verification
                if(check_expire):
                    self.verifFlowRemoved(request)

    def verifPkt(self, ofport, exp_pkt):
        (rcv_port, rcv_pkt, pkt_time) = self.dataplane.poll(
                    port_number=ofport, timeout=1)
        self.assertTrue(rcv_pkt is not None,
                    "Did not receive packet port " + str(ofport))
        pa_logger.debug("Packet len " + str(len(rcv_pkt)) + " in on "
                    + str(rcv_port))

        self.assertEqual(str(exp_pkt), str(rcv_pkt),
            'Response packet does not match send packet ' +
            "on port " + str(ofport))

    def verifFlowRemoved(self, request):
        (response, raw) = self.controller.poll(ofp.OFPT_FLOW_REMOVED, 2)
        self.assertTrue(response is not None,
            'Flow removed message not received')

        req_match = request.match
        res_match = response.match
        if(req_match != res_match):
            self.verifMatchField(req_match, res_match)

        self.assertEqual(request.cookie, response.cookie,
            self.matchErrStr('cookie'))
        if (req_match.wildcards != 0):
            self.assertEqual(request.priority, response.priority,
                self.matchErrStr('priority'))
            self.assertEqual(response.reason, ofp.OFPRR_HARD_TIMEOUT,
                'Reason is not HARD TIMEOUT')
            self.assertEqual(response.packet_count, 1,
                'Packet count is not correct')
            self.assertEqual(response.byte_count, len(pkt),
                'Packet length is not correct')

    def verifMatchField(self, req_match, res_match):
        self.assertEqual(str(req_match.wildcards), str(res_match.wildcards),
            self.matchErrStr('wildcards'))
        self.assertEqual(str(req_match.in_port), str(res_match.in_port),
            self.matchErrStr('in_port'))
        self.assertEqual(str(req_match.dl_src), str(res_match.dl_src),
            self.matchErrStr('dl_src'))
        self.assertEqual(str(req_match.dl_dst), str(res_match.dl_dst),
            self.matchErrStr('dl_dst'))
        self.assertEqual(str(req_match.dl_vlan), str(res_match.dl_vlan),
            self.matchErrStr('dl_vlan'))
        self.assertEqual(str(req_match.dl_vlan_pcp), str(res_match.dl_vlan_pcp),
            self.matchErrStr('dl_vlan_pcp'))
        self.assertEqual(str(req_match.dl_type), str(res_match.dl_type),
            self.matchErrStr('dl_type'))
        if(not(req_match.wildcards & ofp.OFPFW_DL_TYPE)
           and (req_match.dl_type == self.IP_ETHERTYPE)):
            self.assertEqual(str(req_match.nw_tos), str(res_match.nw_tos),
                self.matchErrStr('nw_tos'))
            self.assertEqual(str(req_match.nw_proto), str(res_match.nw_proto),
                self.matchErrStr('nw_proto'))
            self.assertEqual(str(req_match.nw_src), str(res_match.nw_src),
                self.matchErrStr('nw_src'))
            self.assertEqual(str(req_match.nw_dst), str(res_match.nw_dst),
                self.matchErrStr('nw_dst'))
            if(not(req_match.wildcards & ofp.OFPFW_NW_PROTO)
               and ((req_match.nw_proto == self.TCP_PROTOCOL)
                    or (req_match.nw_proto == self.UDP_PROTOCOL))):
                self.assertEqual(str(req_match.tp_src), str(res_match.tp_src),
                    self.matchErrStr('tp_src'))
                self.assertEqual(str(req_match.tp_dst), str(res_match.tp_dst),
                    self.matchErrStr('tp_dst'))

    def matchErrStr(self, field):
        return ('Response Match_' + field + ' does not match send message')

class SingleWildcardMatch(SimpleExactMatch):
    """
    Exercise wildcard matching for all ports

    Generate a packet
    Generate and install a matching flow with wildcard mask
    Add action to forward to a port
    Send the packet to the port
    Verify the packet is received at all other ports (one port at a time)
    Verify flow_expiration message is correct when command option is set
    """
    def __init__(self):
        SimpleExactMatch.__init__(self)
        self.wildcards = [ofp.OFPFW_IN_PORT,
                          ofp.OFPFW_DL_VLAN,
                          ofp.OFPFW_DL_SRC,
                          ofp.OFPFW_DL_DST,
                          ofp.OFPFW_DL_TYPE,
                          ofp.OFPFW_NW_PROTO,
                          ofp.OFPFW_TP_SRC,
                          ofp.OFPFW_TP_DST,
                          0x3F << ofp.OFPFW_NW_SRC_SHIFT,
                          0x3F << ofp.OFPFW_NW_DST_SHIFT,
                          ofp.OFPFW_DL_VLAN_PCP,
                          ofp.OFPFW_NW_TOS]

    def runTest(self):
        for exec_wildcard in range(len(self.wildcards)):
            self.flowMatchTest(exec_wildcard)

class AllExceptOneWildcardMatch(SingleWildcardMatch):
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
        for exec_wildcard in range(len(self.wildcards)):
            all_exp_one_wildcard = ofp.OFPFW_ALL ^ self.wildcards[exec_wildcard]
            self.flowMatchTest(all_exp_one_wildcard)

class AllWildcardMatch(SingleWildcardMatch):
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
        self.flowMatchTest(ofp.OFPFW_ALL)

class ExactModifyAction(SimpleExactMatch):
    """
    Perform Modify action with exact matching for all ports

    Generate a packet for transmit
    Generate the expected packet
    Generate and install a matching flow with a modify action and
    an output action without wildcard mask
    Send the packet to the port
    Verify the expected packet is received at all other ports
    (one port at a time)
    Verify flow_expiration message is correct when command option is set
    """
    def __init__(self):
        SimpleExactMatch.__init__(self)
        self.modify_act = [ofp.OFPAT_SET_VLAN_VID,
                           ofp.OFPAT_SET_VLAN_PCP,
                           ofp.OFPAT_STRIP_VLAN,
                           ofp.OFPAT_SET_DL_SRC,
                           ofp.OFPAT_SET_DL_DST,
                           ofp.OFPAT_SET_NW_SRC,
                           ofp.OFPAT_SET_NW_DST,
                           ofp.OFPAT_SET_NW_TOS,
                           ofp.OFPAT_SET_TP_SRC,
                           ofp.OFPAT_SET_TP_DST]

    def runTest(self):
        self.flowMatchModTest()

    def flowMatchModTest(self, wildcards=0, check_expire=False):
        global pa_port_map
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        mod_dl_dst = '43:21:0F:ED:CB:A9'
        mod_dl_src = '7F:ED:CB:A9:87:65'
        mod_dl_vlan = 4094
        mod_dl_vlan_pcp = 7
        mod_ip_src = '10.20.30.40'
        mod_ip_dst = '50.60.70.80'
        mod_ip_tos = 0xf0
        mod_tcp_sport = 4321
        mod_tcp_dport = 8765

        request = message.features_request()
        (reply, pkt) = self.controller.transact(request, timeout=2)
        self.assertTrue(reply is not None, "Did not get response to ftr req")
        supported_act = reply.actions

        for idx in range(len(of_ports)):
            ingress_port = of_ports[idx]
            pa_logger.info("Ingress " + str(ingress_port) + " to all the other ports")

            for egr_idx in range(len(of_ports)):
                if egr_idx == idx:
                    continue

                for exec_mod in range(len(self.modify_act)):
                    pkt_len = 100
                    dl_dst = '0C:DE:F0:12:34:56'
                    dl_src = '01:23:45:67:89:AB'
                    dl_vlan_enable = False
                    dl_vlan = 0
                    dl_vlan_pcp = 0
                    ip_src = '192.168.0.1'
                    ip_dst = '192.168.0.2'
                    ip_tos = 0
                    tcp_sport = 1234
                    tcp_dport = 80

                    rc = delete_all_flows(self.controller, pa_logger)
                    self.assertEqual(rc, 0, "Failed to delete all flows")
                    do_barrier(self.controller)

                    pkt = simple_tcp_packet(pktlen=pkt_len,
                        dl_dst=dl_dst,
                        dl_src=dl_src,
                        dl_vlan_enable=dl_vlan_enable,
                        dl_vlan=dl_vlan,
                        dl_vlan_pcp=dl_vlan_pcp,
                        ip_src=ip_src,
                        ip_dst=ip_dst,
                        ip_tos=ip_tos,
                        tcp_sport=tcp_sport,
                        tcp_dport=tcp_dport)

                    match = parse.packet_to_flow_match(pkt)
                    self.assertTrue(match is not None,
                        "Could not generate flow match from pkt")
                    match.in_port = ingress_port
                    match.dl_vlan = ofp.OFP_VLAN_NONE
                    match.nw_proto = self.TCP_PROTOCOL
                    match.wildcards = wildcards

                    request = message.flow_mod()
                    request.match = match
                    request.buffer_id = 0xffffffff
                    #@todo Need UI to setup FLAGS parameter for flow_mod
                    if(check_expire):
                        request.flags |= ofp.OFPFF_SEND_FLOW_REM
                        request.hard_timeout = 1

                    exec_act = self.modify_act[exec_mod]
                    if exec_act == ofp.OFPAT_SET_VLAN_VID:
                        if not(supported_act & 1<<ofp.OFPAT_SET_VLAN_VID):
                            continue
                        pkt_len = pkt_len + 4
                        dl_vlan_enable = True
                        dl_vlan = mod_dl_vlan
                        mod_act = action.action_set_vlan_vid()
                        mod_act.vlan_vid = mod_dl_vlan
                    elif exec_act == ofp.OFPAT_SET_VLAN_PCP:
                        if not(supported_act & 1<<ofp.OFPAT_SET_VLAN_PCP):
                            continue
                        pkt_len = pkt_len + 4
                        dl_vlan_enable = True
                        dl_vlan_pcp = mod_dl_vlan_pcp
                        mod_act = action.action_set_vlan_pcp()
                        mod_act.vlan_pcp = mod_dl_vlan_pcp
                    elif exec_act == ofp.OFPAT_STRIP_VLAN:
                        if not(supported_act & 1<<ofp.OFPAT_STRIP_VLAN):
                            continue
                        dl_vlan_enable = False
                        mod_act = action.action_strip_vlan()
                    elif exec_act == ofp.OFPAT_SET_DL_SRC:
                        if not(supported_act & 1<<ofp.OFPAT_SET_DL_SRC):
                            continue
                        dl_src = mod_dl_src
                        mod_act = action.action_set_dl_src()
                        mod_act.dl_addr = parse.parse_mac(mod_dl_src)
                    elif exec_act == ofp.OFPAT_SET_DL_DST:
                        if not(supported_act & 1<<ofp.OFPAT_SET_DL_DST):
                            continue
                        dl_dst = mod_dl_dst
                        mod_act = action.action_set_dl_dst()
                        mod_act.dl_addr = parse.parse_mac(mod_dl_dst)
                    elif exec_act == ofp.OFPAT_SET_NW_SRC:
                        if not(supported_act & 1<<ofp.OFPAT_SET_NW_SRC):
                            continue
                        ip_src = mod_ip_src
                        mod_act = action.action_set_nw_src()
                        mod_act.nw_addr = parse.parse_ip(mod_ip_src)
                    elif exec_act == ofp.OFPAT_SET_NW_DST:
                        if not(supported_act & 1<<ofp.OFPAT_SET_NW_DST):
                            continue
                        ip_dst = mod_ip_dst
                        mod_act = action.action_set_nw_dst()
                        mod_act.nw_addr = parse.parse_ip(mod_ip_dst)
                    elif exec_act == ofp.OFPAT_SET_NW_TOS:
                        if not(supported_act & 1<<ofp.OFPAT_SET_NW_TOS):
                            continue
                        ip_tos = mod_ip_tos
                        mod_act = action.action_set_nw_tos()
                        mod_act.nw_tos = mod_ip_tos
                    elif exec_act == ofp.OFPAT_SET_TP_SRC:
                        if not(supported_act & 1<<ofp.OFPAT_SET_TP_SRC):
                            continue
                        tcp_sport = mod_tcp_sport
                        mod_act = action.action_set_tp_src()
                        mod_act.tp_port = mod_tcp_sport
                    elif exec_act == ofp.OFPAT_SET_TP_DST:
                        if not(supported_act & 1<<ofp.OFPAT_SET_TP_DST):
                            continue
                        tcp_dport = mod_tcp_dport
                        mod_act = action.action_set_tp_dst()
                        mod_act.tp_port = mod_tcp_dport
                    else:
                        continue

                    self.assertTrue(request.actions.add(mod_act),
                            "Could not add output action")
                    pa_logger.info(request.show())

                    exp_pkt = simple_tcp_packet(pktlen=pkt_len,
                        dl_dst=dl_dst,
                        dl_src=dl_src,
                        dl_vlan_enable=dl_vlan_enable,
                        dl_vlan=dl_vlan,
                        dl_vlan_pcp=dl_vlan_pcp,
                        ip_src=ip_src,
                        ip_dst=ip_dst,
                        ip_tos=ip_tos,
                        tcp_sport=tcp_sport,
                        tcp_dport=tcp_dport)

                    act = action.action_output()
                    act.port = of_ports[egr_idx]
                    self.assertTrue(request.actions.add(act),
                                    "Could not add output action")
                    pa_logger.info(request.show())

                    pa_logger.info("Inserting flow")
                    rv = self.controller.message_send(request)
                    self.assertTrue(rv != -1, "Error installing flow mod")
                    do_barrier(self.controller)

                    pa_logger.info("Sending packet to dp port " +str(ingress_port))
                    self.dataplane.send(ingress_port, str(pkt))

                    ofport = of_ports[egr_idx]
                    self.verifPkt(ofport, exp_pkt)

                    #@todo Need UI for enabling response-verification
                    if(check_expire):
                        self.verifFlowRemoved(request)

if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test_spec=basic"
