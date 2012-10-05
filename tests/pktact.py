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
import time

from oftest.testutils import *

#@var port_map Local copy of the configuration map from OF port
# numbers to OS interfaces
pa_port_map = None
#@var pa_config Local copy of global configuration data
pa_config = None

WILDCARD_VALUES = [ofp.OFPFW_IN_PORT,
                   ofp.OFPFW_DL_VLAN | ofp.OFPFW_DL_VLAN_PCP,
                   ofp.OFPFW_DL_SRC,
                   ofp.OFPFW_DL_DST,
                   (ofp.OFPFW_DL_TYPE | ofp.OFPFW_NW_SRC_ALL |
                    ofp.OFPFW_NW_DST_ALL | ofp.OFPFW_NW_TOS | ofp.OFPFW_NW_PROTO |
                    ofp.OFPFW_TP_SRC | ofp.OFPFW_TP_DST),
                   (ofp.OFPFW_NW_PROTO | ofp.OFPFW_TP_SRC | ofp.OFPFW_TP_DST),
                   ofp.OFPFW_TP_SRC,
                   ofp.OFPFW_TP_DST,
                   ofp.OFPFW_NW_SRC_MASK,
                   ofp.OFPFW_NW_DST_MASK,
                   ofp.OFPFW_DL_VLAN_PCP,
                   ofp.OFPFW_NW_TOS]

NO_WILDCARD_VALUES = [(ofp.OFPFW_ALL ^ ofp.OFPFW_IN_PORT),
                      (ofp.OFPFW_ALL ^ ofp.OFPFW_DL_VLAN),
                      (ofp.OFPFW_ALL ^ ofp.OFPFW_DL_SRC),
                      (ofp.OFPFW_ALL ^ ofp.OFPFW_DL_DST),
                      (ofp.OFPFW_ALL ^ ofp.OFPFW_DL_TYPE),
                      (ofp.OFPFW_ALL ^ ofp.OFPFW_DL_TYPE ^ ofp.OFPFW_NW_PROTO),
                      (ofp.OFPFW_ALL ^ ofp.OFPFW_DL_TYPE ^ ofp.OFPFW_NW_PROTO ^
                       ofp.OFPFW_TP_SRC),
                      (ofp.OFPFW_ALL ^ ofp.OFPFW_DL_TYPE ^ ofp.OFPFW_NW_PROTO ^
                       ofp.OFPFW_TP_DST),
                      (ofp.OFPFW_ALL ^ ofp.OFPFW_DL_TYPE ^ ofp.OFPFW_NW_PROTO ^
                       ofp.OFPFW_NW_SRC_MASK),
                      (ofp.OFPFW_ALL ^ ofp.OFPFW_DL_TYPE ^ ofp.OFPFW_NW_PROTO ^
                       ofp.OFPFW_NW_DST_MASK),
                      (ofp.OFPFW_ALL ^ ofp.OFPFW_DL_VLAN ^ ofp.OFPFW_DL_VLAN_PCP),
                      (ofp.OFPFW_ALL ^ ofp.OFPFW_DL_TYPE ^ ofp.OFPFW_NW_PROTO ^
                       ofp.OFPFW_NW_TOS)]

MODIFY_ACTION_VALUES =  [ofp.OFPAT_SET_VLAN_VID,
                         ofp.OFPAT_SET_VLAN_PCP,
                         ofp.OFPAT_STRIP_VLAN,
                         ofp.OFPAT_SET_DL_SRC,
                         ofp.OFPAT_SET_DL_DST,
                         ofp.OFPAT_SET_NW_SRC,
                         ofp.OFPAT_SET_NW_DST,
                         ofp.OFPAT_SET_NW_TOS,
                         ofp.OFPAT_SET_TP_SRC,
                         ofp.OFPAT_SET_TP_DST]

TEST_VID_DEFAULT = 2

def test_set_init(config):
    """
    Set up function for packet action test classes

    @param config The configuration dictionary; see oft
    """

    basic.test_set_init(config)

    global pa_port_map
    global pa_config

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
            pkt = simple_icmp_packet()
        else:
            pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        for idx in range(len(of_ports)):
            rv = delete_all_flows(self.controller)
            self.assertEqual(rv, 0, "Failed to delete all flows")

            ingress_port = of_ports[idx]
            egress_port = of_ports[(idx + 1) % len(of_ports)]
            logging.info("Ingress " + str(ingress_port) + 
                             " to egress " + str(egress_port))

            match.in_port = ingress_port

            request = message.flow_mod()
            request.match = match

            request.buffer_id = 0xffffffff
            act.port = egress_port
            self.assertTrue(request.actions.add(act), "Could not add action")

            logging.info("Inserting flow")
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Error installing flow mod")
            self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

            logging.info("Sending packet to dp port " + 
                           str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))

            exp_pkt_arg = None
            exp_port = None
            if pa_config["relax"]:
                exp_pkt_arg = pkt
                exp_port = egress_port

            (rcv_port, rcv_pkt, pkt_time) = self.dataplane.poll(port_number=exp_port,
                                                                exp_pkt=exp_pkt_arg)
            self.assertTrue(rcv_pkt is not None, "Did not receive packet")
            logging.debug("Packet len " + str(len(rcv_pkt)) + " in on " + 
                         str(rcv_port))
            self.assertEqual(rcv_port, egress_port, "Unexpected receive port")
            self.assertEqual(str(pkt), str(rcv_pkt),
                             'Response packet does not match send packet')

class DirectPacketController(basic.SimpleDataPlane):
    """
    Send packet to the controller port

    Generate a packet
    Generate and install a matching flow
    Add action to direct the packet to the controller port
    Send the packet to ingress dataplane port
    Verify the packet is received at the controller port
    """
    def runTest(self):
        self.handleFlow()

    def handleFlow(self, pkttype='TCP'):
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 0, "Not enough ports for test")

        if (pkttype == 'ICMP'):
            pkt = simple_icmp_packet()
        else:
            pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None,
                        "Could not generate flow match from pkt")
        act = action.action_output()

        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        ingress_port = of_ports[0]
        match.in_port = ingress_port

        request = message.flow_mod()
        request.match = match

        request.buffer_id = 0xffffffff
        act.port = ofp.OFPP_CONTROLLER
        act.max_len = 65535
        self.assertTrue(request.actions.add(act), "Could not add action")

        logging.info("Inserting flow")
        rv = self.controller.message_send(request)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

        logging.info("Sending packet to dp port " +
                        str(ingress_port))
        self.dataplane.send(ingress_port, str(pkt))

        (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN)

        self.assertTrue(response is not None,
                        'Packet in message not received by controller')
        if not dataplane.match_exp_pkt(pkt, response.data):
            logging.debug("Sent %s" % format_packet(pkt))
            logging.debug("Resp %s" % format_packet(response.data))
            self.assertTrue(False,
                            'Response packet does not match send packet' +
                             ' for controller port')


class DirectPacketQueue(basic.SimpleDataPlane):
    """
    Send packet to single queue on single egress port

    Generate a packet
    Generate and install a matching flow
    Add action to direct the packet to an egress port and queue
    Send the packet to ingress dataplane port
    Verify the packet is received at the egress port only
    """
    def runTest(self):
        self.handleFlow()

    def portQueuesGet(self, queue_stats, port_num):
        result = []
        for qs in queue_stats.stats:
            if qs.port_no != port_num:
                continue
            result.append(qs.queue_id)
        return result

    def handleFlow(self, pkttype='TCP'):
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        if (pkttype == 'ICMP'):
            pkt = simple_icmp_packet()
        else:
            pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")

        # Get queue stats from switch
        
        request = message.queue_stats_request()
        request.port_no  = ofp.OFPP_ALL
        request.queue_id = ofp.OFPQ_ALL
        (queue_stats, p) = self.controller.transact(request)
        self.assertNotEqual(queue_stats, None, "Queue stats request failed")

        act = action.action_enqueue()

        for idx in range(len(of_ports)):
            ingress_port = of_ports[idx]
            egress_port = of_ports[(idx + 1) % len(of_ports)]

            for egress_queue_id in self.portQueuesGet(queue_stats, egress_port):
                logging.info("Ingress " + str(ingress_port)
                               + " to egress " + str(egress_port)
                               + " queue " + str(egress_queue_id)
                               )

                rv = delete_all_flows(self.controller)
                self.assertEqual(rv, 0, "Failed to delete all flows")

                match.in_port = ingress_port
                
                request = message.flow_mod()
                request.match = match

                request.buffer_id = 0xffffffff
                act.port     = egress_port
                act.queue_id = egress_queue_id
                self.assertTrue(request.actions.add(act), "Could not add action")

                logging.info("Inserting flow")
                rv = self.controller.message_send(request)
                self.assertTrue(rv != -1, "Error installing flow mod")
                self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

                # Get current stats for selected egress queue

                request = message.queue_stats_request()
                request.port_no  = egress_port
                request.queue_id = egress_queue_id
                (qs_before, p) = self.controller.transact(request)
                self.assertNotEqual(qs_before, None, "Queue stats request failed")

                logging.info("Sending packet to dp port " + 
                               str(ingress_port))
                self.dataplane.send(ingress_port, str(pkt))
                
                exp_pkt_arg = None
                exp_port = None
                if pa_config["relax"]:
                    exp_pkt_arg = pkt
                    exp_port = egress_port
                    
                    (rcv_port, rcv_pkt, pkt_time) = self.dataplane.poll(port_number=exp_port,
                                                                        exp_pkt=exp_pkt_arg)
                    self.assertTrue(rcv_pkt is not None, "Did not receive packet")
                    logging.debug("Packet len " + str(len(rcv_pkt)) + " in on " + 
                                    str(rcv_port))
                    self.assertEqual(rcv_port, egress_port, "Unexpected receive port")
                    self.assertEqual(str(pkt), str(rcv_pkt),
                                     'Response packet does not match send packet')

                # FIXME: instead of sleeping, keep requesting queue stats until
                # the expected queue counter increases or some large timeout is
                # reached
                time.sleep(2)

                # Get current stats for selected egress queue again

                request = message.queue_stats_request()
                request.port_no  = egress_port
                request.queue_id = egress_queue_id
                (qs_after, p) = self.controller.transact(request)
                self.assertNotEqual(qs_after, None, "Queue stats request failed")

                # Make sure that tx packet counter for selected egress queue was
                # incremented

                self.assertEqual(qs_after.stats[0].tx_packets, \
                                 qs_before.stats[0].tx_packets + 1, \
                                 "Verification of egress queue tx packet count failed"
                                 )
                    

class DirectPacketControllerQueue(basic.SimpleDataPlane):
    """
    Send a packet from each of the openflow ports
    to each of the queues configured on the controller port.
    If no queues have been configured, no packets are sent.

    Generate a packet
    Generate and install a matching flow
    Add action to direct the packet to one of the controller port queues
    Send the packet to ingress dataplane port
    Verify the packet is received on the controller port queue
    """
    def runTest(self):
        self.handleFlow()

    def portQueuesGet(self, queue_stats, port_num):
        result = []
        for qs in queue_stats.stats:
            if qs.port_no != port_num:
                continue
            result.append(qs.queue_id)
        return result

    def handleFlow(self, pkttype='TCP'):
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        if (pkttype == 'ICMP'):
            pkt = simple_icmp_packet()
        else:
            pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")

        # Get queue stats from switch
        
        request = message.queue_stats_request()
        request.port_no  = ofp.OFPP_CONTROLLER
        request.queue_id = ofp.OFPQ_ALL
        (queue_stats, p) = self.controller.transact(request)
        self.assertNotEqual(queue_stats, None, "Queue stats request failed")

        act = action.action_enqueue()

        for idx in range(len(of_ports)):
            ingress_port = of_ports[idx]
            egress_port = ofp.OFPP_CONTROLLER

            logging.info("Ingress port " + str(ingress_port)
                           + ", controller port queues " 
                           + str(self.portQueuesGet(queue_stats, egress_port)))

            for egress_queue_id in self.portQueuesGet(queue_stats, egress_port):
                logging.info("Ingress " + str(ingress_port)
                               + " to egress " + str(egress_port)
                               + " queue " + str(egress_queue_id)
                               )

                rv = delete_all_flows(self.controller)
                self.assertEqual(rv, 0, "Failed to delete all flows")

                match.in_port = ingress_port
                
                request = message.flow_mod()
                request.match = match

                request.buffer_id = 0xffffffff
                act.port     = egress_port
                act.queue_id = egress_queue_id
                self.assertTrue(request.actions.add(act), "Could not add action")

                logging.info("Inserting flow")
                rv = self.controller.message_send(request)
                self.assertTrue(rv != -1, "Error installing flow mod")
                self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

                # Get current stats for selected egress queue

                request = message.queue_stats_request()
                request.port_no  = egress_port
                request.queue_id = egress_queue_id
                (qs_before, p) = self.controller.transact(request)
                self.assertNotEqual(qs_before, None, "Queue stats request failed")

                logging.info("Sending packet to dp port " + 
                               str(ingress_port))
                self.dataplane.send(ingress_port, str(pkt))
                
                exp_pkt_arg = None
                exp_port = None

                while True:
                    (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN)
                    if not response:  # Timeout
                        break
                    if dataplane.match_exp_pkt(pkt, response.data): # Got match
                        break
                    if not basic_config["relax"]:  # Only one attempt to match
                        break
                    count += 1
                    if count > 10:   # Too many tries
                        break

                self.assertTrue(response is not None, 
                               'Packet in message not received by controller')
                if not dataplane.match_exp_pkt(pkt, response.data):
                    logging.debug("Sent %s" % format_packet(pkt))
                    logging.debug("Resp %s" % format_packet(response.data))
                    self.assertTrue(False,
                                    'Response packet does not match send packet' +
                                    ' for controller port')

                # FIXME: instead of sleeping, keep requesting queue stats until
                # the expected queue counter increases or some large timeout is
                # reached
                time.sleep(2)

                # Get current stats for selected egress queue again

                request = message.queue_stats_request()
                request.port_no  = egress_port
                request.queue_id = egress_queue_id
                (qs_after, p) = self.controller.transact(request)
                self.assertNotEqual(qs_after, None, "Queue stats request failed")

                # Make sure that tx packet counter for selected egress queue was
                # incremented

                self.assertEqual(qs_after.stats[0].tx_packets, \
                                 qs_before.stats[0].tx_packets + 1, \
                                 "Verification of egress queue tx packet count failed"
                                 )
                    

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

        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        for idx in range(len(of_ports)):
            rv = delete_all_flows(self.controller)
            self.assertEqual(rv, 0, "Failed to delete all flows")

            ingress_port = of_ports[idx]
            egress_port1 = of_ports[(idx + 1) % len(of_ports)]
            egress_port2 = of_ports[(idx + 2) % len(of_ports)]
            logging.info("Ingress " + str(ingress_port) + 
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
            # logging.info(request.show())

            logging.info("Inserting flow")
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Error installing flow mod")
            self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

            logging.info("Sending packet to dp port " + 
                           str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            yes_ports = set([egress_port1, egress_port2])
            no_ports = set(of_ports).difference(yes_ports)

            receive_pkt_check(self.dataplane, pkt, yes_ports, no_ports,
                              self, pa_config)

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

        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        for ingress_port in of_ports:
            rv = delete_all_flows(self.controller)
            self.assertEqual(rv, 0, "Failed to delete all flows")

            logging.info("Ingress " + str(ingress_port) + 
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
            logging.debug(request.show())

            logging.info("Inserting flow")
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Error installing flow mod")
            self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

            logging.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            yes_ports = set(of_ports).difference([ingress_port])
            receive_pkt_check(self.dataplane, pkt, yes_ports, [ingress_port],
                              self, pa_config)


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

        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        for ingress_port in of_ports:
            rv = delete_all_flows(self.controller)
            self.assertEqual(rv, 0, "Failed to delete all flows")

            logging.info("Ingress " + str(ingress_port) + " to all ports")
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
            # logging.info(request.show())

            logging.info("Inserting flow")
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Error installing flow mod")
            self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

            logging.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            receive_pkt_check(self.dataplane, pkt, of_ports, [], self, pa_config)

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
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        for ingress_port in of_ports:
            rv = delete_all_flows(self.controller)
            self.assertEqual(rv, 0, "Failed to delete all flows")

            logging.info("Ingress " + str(ingress_port) + " to all ports")
            match.in_port = ingress_port

            request = message.flow_mod()
            request.match = match
            request.buffer_id = 0xffffffff
            act.port = ofp.OFPP_FLOOD
            self.assertTrue(request.actions.add(act), 
                            "Could not add flood port action")
            logging.info(request.show())

            logging.info("Inserting flow")
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Error installing flow mod")
            self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

            logging.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            yes_ports = set(of_ports).difference([ingress_port])
            receive_pkt_check(self.dataplane, pkt, yes_ports, [ingress_port],
                              self, pa_config)

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
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        for ingress_port in of_ports:
            rv = delete_all_flows(self.controller)
            self.assertEqual(rv, 0, "Failed to delete all flows")

            logging.info("Ingress " + str(ingress_port) + " to all ports")
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
            logging.info(request.show())

            logging.info("Inserting flow")
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Error installing flow mod")
            self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

            logging.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            receive_pkt_check(self.dataplane, pkt, of_ports, [], self, pa_config)

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

        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        for ingress_port in of_ports:
            rv = delete_all_flows(self.controller)
            self.assertEqual(rv, 0, "Failed to delete all flows")

            logging.info("Ingress " + str(ingress_port) + " to all ports")
            match.in_port = ingress_port

            request = message.flow_mod()
            request.match = match
            request.buffer_id = 0xffffffff
            act.port = ofp.OFPP_ALL
            self.assertTrue(request.actions.add(act), 
                            "Could not add ALL port action")
            logging.info(request.show())

            logging.info("Inserting flow")
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Error installing flow mod")
            self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

            logging.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            yes_ports = set(of_ports).difference([ingress_port])
            receive_pkt_check(self.dataplane, pkt, yes_ports, [ingress_port],
                              self, pa_config)

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

        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        for ingress_port in of_ports:
            rv = delete_all_flows(self.controller)
            self.assertEqual(rv, 0, "Failed to delete all flows")

            logging.info("Ingress " + str(ingress_port) + " to all ports")
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
            logging.info(request.show())

            logging.info("Inserting flow")
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Error installing flow mod")
            self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

            logging.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            receive_pkt_check(self.dataplane, pkt, of_ports, [], self, pa_config)
            
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
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = action.action_output()

        for idx in range(len(of_ports)):
            rv = delete_all_flows(self.controller)
            self.assertEqual(rv, 0, "Failed to delete all flows")

            ingress_port = of_ports[idx]
            no_flood_idx = (idx + 1) % len(of_ports)
            no_flood_port = of_ports[no_flood_idx]
            rv = port_config_set(self.controller, no_flood_port,
                                 ofp.OFPPC_NO_FLOOD, ofp.OFPPC_NO_FLOOD)
            self.assertEqual(rv, 0, "Failed to set port config")

            match.in_port = ingress_port

            request = message.flow_mod()
            request.match = match
            request.buffer_id = 0xffffffff
            act.port = ofp.OFPP_FLOOD
            self.assertTrue(request.actions.add(act), 
                            "Could not add flood port action")
            logging.info(request.show())

            logging.info("Inserting flow")
            rv = self.controller.message_send(request)
            self.assertTrue(rv != -1, "Error installing flow mod")
            self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

            logging.info("Sending packet to dp port " + str(ingress_port))
            logging.info("No flood port is " + str(no_flood_port))
            self.dataplane.send(ingress_port, str(pkt))
            no_ports = set([ingress_port, no_flood_port])
            yes_ports = set(of_ports).difference(no_ports)
            receive_pkt_check(self.dataplane, pkt, yes_ports, no_ports, self, pa_config)

            # Turn no flood off again
            rv = port_config_set(self.controller, no_flood_port,
                                 0, ofp.OFPPC_NO_FLOOD)
            self.assertEqual(rv, 0, "Failed to reset port config")

            #@todo Should check no other packets received



################################################################

class BaseMatchCase(basic.SimpleDataPlane):
    def setUp(self):
        basic.SimpleDataPlane.setUp(self)
    def runTest(self):
        logging.info("BaseMatchCase")

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
        flow_match_test(self, pa_port_map)

class ExactMatchTagged(BaseMatchCase):
    """
    Exact match for all port pairs with tagged pkts
    """

    def runTest(self):
        vid = test_param_get(self.config, 'vid', default=TEST_VID_DEFAULT)
        flow_match_test(self, pa_port_map, dl_vlan=vid)

class ExactMatchTaggedMany(BaseMatchCase):
    """
    ExactMatchTagged with many VLANS
    """

    priority = -1

    def runTest(self):
        for vid in range(2,100,10):
            flow_match_test(self, pa_port_map, dl_vlan=vid, max_test=5)
        for vid in range(100,4000,389):
            flow_match_test(self, pa_port_map, dl_vlan=vid, max_test=5)
        flow_match_test(self, pa_port_map, dl_vlan=4094, max_test=5)

class SingleWildcardMatchPriority(BaseMatchCase):
    """
    SingleWildcardMatchPriority
    """

    def _Init(self):
        self.pkt = simple_tcp_packet()
        self.flowMsgs = {}

    def _ClearTable(self):
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

    def runTest(self):
        
        self._Init()
        of_ports = pa_port_map.keys()
        of_ports.sort()

        # Delete the initial flow table
        self._ClearTable()

        # Run several combinations, each at lower priority settings. 
        # At the end of each call to runPrioFlows(), the table should
        # be empty. If its not, we'll catch it as the priorities decreases
        portA = of_ports[0]
        portB = of_ports[1]
        portC = of_ports[2]

        # TODO -- these priority numbers should be validated somehow?
        self.runPrioFlows(portA, portB, portC, 1000, 999)
        self.runPrioFlows(portB, portC, portA, 998, 997)
        self.runPrioFlows(portC, portA, portB, 996, 995)
        self.runPrioFlows(portA, portC, portB, 994, 993)


    
    def runPrioFlows(self, portA, portB, portC, prioHigher, prioLower, 
                     clearTable=False):

        if clearTable:
            self._ClearTable()

        # Sanity check flow at lower priority from pA to pB
        logging.info("runPrioFlows(pA=%d,pB=%d,pC=%d,ph=%d,pl=%d"
                         % (portA, portB, portC, prioHigher, prioLower))

        # Sanity check flow at lower priority from pA to pC
        self.installFlow(prioLower, portA, portC)
        self.verifyFlow(portA, portC)
        self.removeFlow(prioLower)

        # Install and verify pA->pB @ prioLower
        self.installFlow(prioLower, portA, portB)
        self.verifyFlow(portA, portB)

        # Install and verify pA->pC @ prioHigher, should override pA->pB
        self.installFlow(prioHigher, portA, portC)
        self.verifyFlow(portA, portC)
        # remove pA->pC
        self.removeFlow(prioHigher)
        # Old flow pA -> pB @ prioLower should still be active
        self.verifyFlow(portA, portB)
        self.removeFlow(prioLower)

        # Table should be empty at this point, leave it alone as
        # an assumption for future test runs



    def installFlow(self, prio, inp, egp,
                    wildcards=ofp.OFPFW_DL_SRC):
        wildcards |= required_wildcards(self)
        request = flow_msg_create(self, self.pkt, ing_port=inp, 
                                  wildcards=wildcards,
                                  egr_ports=egp)
        request.priority = prio
        logging.debug("Install flow with priority " + str(prio))
        flow_msg_install(self, request, clear_table_override=False)
        self.flowMsgs[prio] = request
        
    def removeFlow(self, prio):
        if self.flowMsgs.has_key(prio):
            msg = self.flowMsgs[prio]
            msg.command = ofp.OFPFC_DELETE_STRICT
            # This *must* be set for DELETE
            msg.out_port = ofp.OFPP_NONE
            logging.debug("Remove flow with priority " + str(prio))
            self.controller.message_send(msg)
            self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
        else:
            raise Exception("Not initialized")


    def verifyFlow(self, inp, egp, pkt=None):
        if pkt == None:
            pkt = self.pkt

        logging.info("Pkt match test: " + str(inp) + " to " + str(egp))
        logging.debug("Send packet: " + str(inp) + " to " + str(egp))
        self.dataplane.send(inp, str(pkt))
        receive_pkt_verify(self, egp, pkt, inp)


       
class SingleWildcardMatchPriorityInsertModifyDelete(SingleWildcardMatchPriority):

    def runTest(self):

        self._Init()

        of_ports = pa_port_map.keys()
        of_ports.sort()

        # Install an entry from 0 -> 1 @ prio 1000
        self._ClearTable()
        self.installFlow(1000, of_ports[0], of_ports[1])
        self.verifyFlow(of_ports[0], of_ports[1])
        self.installFlow(1000, of_ports[1], of_ports[0])
        self.verifyFlow(of_ports[1], of_ports[0])
        self.installFlow(1001, of_ports[0], of_ports[1])
        self.verifyFlow(of_ports[0], of_ports[1])
        self.installFlow(1001, of_ports[1], of_ports[0])
        self.verifyFlow(of_ports[1], of_ports[0])
        self.removeFlow(1001)
        self.verifyFlow(of_ports[0], of_ports[1])
        self.removeFlow(1000)



class WildcardPriority(SingleWildcardMatchPriority):
    """
    1. Add wildcard flow, verify packet received.
    2. Add exact match flow with higher priority, verify packet received 
    on port specified by this flow.
    3. Add wildcard flow with even higher priority, verify packet received
    on port specified by this flow.
    """

    def runTest(self):
        
        self._Init()

        of_ports = pa_port_map.keys()
        of_ports.sort()

        self._ClearTable()

        # Install a flow with wildcards
        self.installFlow(999, of_ports[0], of_ports[1], 
                         wildcards=ofp.OFPFW_DL_DST)
        self.verifyFlow(of_ports[0], of_ports[1])
        # Install a flow with no wildcards for our packet
        self.installFlow(1000, of_ports[0], of_ports[2], wildcards=0)
        self.verifyFlow(of_ports[0], of_ports[2])
        # Install a flow with wildcards for our packet with higher
        # priority
        self.installFlow(1001, of_ports[0], of_ports[3])
        self.verifyFlow(of_ports[0], of_ports[3])
        

class WildcardPriorityWithDelete(SingleWildcardMatchPriority):
    """
    1. Add exact match flow, verify packet received.
    2. Add wildcard flow with higher priority, verify packet received on port
    specified by this flow.
    3. Add exact match flow with even higher priority, verify packet received
    on port specified by this flow.
    4. Delete lowest priority flow, verify packet received on port specified
    by highest priority flow.
    5. Delete highest priority flow, verify packet received on port specified
    by remaining flow.
    """

    def runTest(self):
        
        self._Init()

        of_ports = pa_port_map.keys()
        of_ports.sort()

        self._ClearTable()

        # Install an exact match flow
        self.installFlow(250, of_ports[0], of_ports[1], wildcards=0)
        self.verifyFlow(of_ports[0], of_ports[1])
        # Install a flow with wildcards of higher priority
        self.installFlow(1250, of_ports[0], of_ports[2],
                         wildcards=ofp.OFPFW_DL_DST)
        self.verifyFlow(of_ports[0], of_ports[2])
        # Install an exact match flow with even higher priority
        self.installFlow(2001, of_ports[0], of_ports[3], wildcards=0)
        self.verifyFlow(of_ports[0], of_ports[3])
        # Delete lowest priority flow
        self.removeFlow(250)
        self.verifyFlow(of_ports[0], of_ports[3])
        # Delete highest priority flow
        self.removeFlow(2001)
        self.verifyFlow(of_ports[0], of_ports[2])
        

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
        vid = test_param_get(self.config, 'vid', default=TEST_VID_DEFAULT)
        for wc in WILDCARD_VALUES:
            wc |= required_wildcards(self)
            if wc & ofp.OFPFW_DL_VLAN:
                # Set nonzero VLAN id to avoid sending priority-tagged packet
                dl_vlan = vid
            else:
                dl_vlan = -1
            flow_match_test(self, pa_port_map, wildcards=wc, 
                            dl_vlan=dl_vlan, max_test=10)

class SingleWildcardMatchTagged(BaseMatchCase):
    """
    SingleWildcardMatch with tagged packets
    """
    def runTest(self):
        vid = test_param_get(self.config, 'vid', default=TEST_VID_DEFAULT)
        for wc in WILDCARD_VALUES:
            wc |= required_wildcards(self)
            flow_match_test(self, pa_port_map, wildcards=wc, dl_vlan=vid,
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
        vid = test_param_get(self.config, 'vid', default=TEST_VID_DEFAULT)
        for all_exp_one_wildcard in NO_WILDCARD_VALUES:
            all_exp_one_wildcard |= required_wildcards(self)
            if all_exp_one_wildcard & ofp.OFPFW_DL_VLAN:
                # Set nonzero VLAN id to avoid sending priority-tagged packet
                dl_vlan = vid
            else:
                dl_vlan = -1
            flow_match_test(self, pa_port_map, wildcards=all_exp_one_wildcard,
                            dl_vlan=dl_vlan)

class AllExceptOneWildcardMatchTagged(BaseMatchCase):
    """
    Match one field with tagged packets
    """
    def runTest(self):
        vid = test_param_get(self.config, 'vid', default=TEST_VID_DEFAULT)
        for all_exp_one_wildcard in NO_WILDCARD_VALUES:
            all_exp_one_wildcard |= required_wildcards(self)
            flow_match_test(self, pa_port_map, wildcards=all_exp_one_wildcard,
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
        flow_match_test(self, pa_port_map, wildcards=ofp.OFPFW_ALL)

class AllWildcardMatchTagged(BaseMatchCase):
    """
    AllWildcardMatch with tagged packets
    """
    def runTest(self):
        vid = test_param_get(self.config, 'vid', default=TEST_VID_DEFAULT)
        flow_match_test(self, pa_port_map, wildcards=ofp.OFPFW_ALL, 
                        dl_vlan=vid)

    
class AddVLANTag(BaseMatchCase):
    """
    Add a VLAN tag to an untagged packet
    """
    def runTest(self):
        new_vid = 2
        sup_acts = self.supported_actions
        if not(sup_acts & 1<<ofp.OFPAT_SET_VLAN_VID):
            skip_message_emit(self, "Add VLAN tag test")
            return

        len = 100
        len_w_vid = 104
        pkt = simple_tcp_packet(pktlen=len)
        exp_pkt = simple_tcp_packet(pktlen=len_w_vid, dl_vlan_enable=True, 
                                    dl_vlan=new_vid)
        vid_act = action.action_set_vlan_vid()
        vid_act.vlan_vid = new_vid

        flow_match_test(self, pa_port_map, pkt=pkt, 
                        exp_pkt=exp_pkt, action_list=[vid_act])

class PacketOnly(basic.DataPlaneOnly):
    """
    Just send a packet thru the switch
    """

    priority = -1

    def runTest(self):
        pkt = simple_tcp_packet()
        of_ports = pa_port_map.keys()
        of_ports.sort()
        ing_port = of_ports[0]
        logging.info("Sending packet to " + str(ing_port))
        logging.debug("Data: " + str(pkt).encode('hex'))
        self.dataplane.send(ing_port, str(pkt))

class PacketOnlyTagged(basic.DataPlaneOnly):
    """
    Just send a packet thru the switch
    """

    priority = -1

    def runTest(self):
        vid = test_param_get(self.config, 'vid', default=TEST_VID_DEFAULT)
        pkt = simple_tcp_packet(dl_vlan_enable=True, dl_vlan=vid)
        of_ports = pa_port_map.keys()
        of_ports.sort()
        ing_port = of_ports[0]
        logging.info("Sending packet to " + str(ing_port))
        logging.debug("Data: " + str(pkt).encode('hex'))
        self.dataplane.send(ing_port, str(pkt))

class ModifyVID(BaseMatchCase):
    """
    Modify the VLAN ID in the VLAN tag of a tagged packet
    """
    def setUp(self):
        BaseMatchCase.setUp(self)
        self.ing_port=False

    def runTest(self):
        old_vid = 2
        new_vid = 3
        sup_acts = self.supported_actions
        if not (sup_acts & 1 << ofp.OFPAT_SET_VLAN_VID):
            skip_message_emit(self, "Modify VLAN tag test")
            return

        pkt = simple_tcp_packet(dl_vlan_enable=True, dl_vlan=old_vid)
        exp_pkt = simple_tcp_packet(dl_vlan_enable=True, dl_vlan=new_vid)
        vid_act = action.action_set_vlan_vid()
        vid_act.vlan_vid = new_vid

        flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt,
                        action_list=[vid_act], ing_port=self.ing_port)

class ModifyVIDToIngress(ModifyVID):
    """
    Modify the VLAN ID in the VLAN tag of a tagged packet and send to
    ingress port
    """
    def setUp(self):
        BaseMatchCase.setUp(self)
        self.ing_port=True

class ModifyVIDWithTagMatchWildcarded(BaseMatchCase):
    """
    With vlan ID and priority wildcarded, perform SET_VLAN_VID action.
    The same flow should match on both untagged and tagged packets.
    """
    def runTest(self):
        old_vid = 2
        new_vid = 3
        sup_acts = self.supported_actions
        if not (sup_acts & 1 << ofp.OFPAT_SET_VLAN_VID):
            skip_message_emit(self, "ModifyVIDWithTagWildcarded test")
            return

        of_ports = pa_port_map.keys()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        ing_port = of_ports[0]
        egr_ports = of_ports[1]
        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        len_untagged = 100
        len_w_vid = 104
        untagged_pkt = simple_tcp_packet(pktlen=len_untagged)
        tagged_pkt = simple_tcp_packet(pktlen=len_w_vid, 
                                       dl_vlan_enable=True, dl_vlan=old_vid)
        exp_pkt = simple_tcp_packet(pktlen=len_w_vid, dl_vlan_enable=True,
                                    dl_vlan=new_vid)
        wildcards = (required_wildcards(self) | ofp.OFPFW_DL_VLAN |
                     ofp.OFPFW_DL_VLAN_PCP)
        vid_act = action.action_set_vlan_vid()
        vid_act.vlan_vid = new_vid
        request = flow_msg_create(self, untagged_pkt, ing_port=ing_port, 
                                  wildcards=wildcards, egr_ports=egr_ports,
                                  action_list=[vid_act])
        flow_msg_install(self, request)

        logging.debug("Send untagged packet: " + str(ing_port) + " to " + 
                        str(egr_ports))
        self.dataplane.send(ing_port, str(untagged_pkt))
        receive_pkt_verify(self, egr_ports, exp_pkt, ing_port)

        logging.debug("Send tagged packet: " + str(ing_port) + " to " + 
                        str(egr_ports))
        self.dataplane.send(ing_port, str(tagged_pkt))
        receive_pkt_verify(self, egr_ports, exp_pkt, ing_port)

class ModifyVlanPcp(BaseMatchCase):
    """
    Modify the priority field of the VLAN tag of a tagged packet
    """
    def runTest(self):
        vid          = 123
        old_vlan_pcp = 2
        new_vlan_pcp = 3
        sup_acts = self.supported_actions
        if not (sup_acts & 1 << ofp.OFPAT_SET_VLAN_PCP):
            skip_message_emit(self, "Modify VLAN priority test")
            return

        pkt = simple_tcp_packet(dl_vlan_enable=True, dl_vlan=vid, dl_vlan_pcp=old_vlan_pcp)
        exp_pkt = simple_tcp_packet(dl_vlan_enable=True, dl_vlan=vid, dl_vlan_pcp=new_vlan_pcp)
        vid_act = action.action_set_vlan_pcp()
        vid_act.vlan_pcp = new_vlan_pcp

        flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt,
                        action_list=[vid_act])

class StripVLANTag(BaseMatchCase):
    """
    Strip the VLAN tag from a tagged packet
    """
    def runTest(self):
        old_vid = 2
        sup_acts = self.supported_actions
        if not (sup_acts & 1 << ofp.OFPAT_STRIP_VLAN):
            skip_message_emit(self, "Strip VLAN tag test")
            return

        len_w_vid = 104
        len = 100
        pkt = simple_tcp_packet(pktlen=len_w_vid, dl_vlan_enable=True, 
                                dl_vlan=old_vid)
        exp_pkt = simple_tcp_packet(pktlen=len)
        vid_act = action.action_strip_vlan()

        flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt,
                        action_list=[vid_act])

class StripVLANTagWithTagMatchWildcarded(BaseMatchCase):
    """
    Strip the VLAN tag from a tagged packet.
    Differs from StripVLANTag in that VID and PCP are both wildcarded.
    """
    def runTest(self):
        old_vid = 2
        sup_acts = self.supported_actions
        if not (sup_acts & 1 << ofp.OFPAT_STRIP_VLAN):
            skip_message_emit(self, "StripVLANTagWithTagWildcarded test")
            return

        len_w_vid = 104
        len_untagged = 100
        pkt = simple_tcp_packet(pktlen=len_w_vid, dl_vlan_enable=True, 
                                dl_vlan=old_vid)
        exp_pkt = simple_tcp_packet(pktlen=len_untagged)
        wildcards = (required_wildcards(self) | ofp.OFPFW_DL_VLAN |
                     ofp.OFPFW_DL_VLAN_PCP)
        vid_act = action.action_strip_vlan()

        flow_match_test(self, pa_port_map, 
                        wildcards=wildcards,
                        pkt=pkt, exp_pkt=exp_pkt,
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
        sup_acts = self.supported_actions
        if not (sup_acts & 1 << ofp.OFPAT_SET_DL_SRC):
            skip_message_emit(self, "ModifyL2Src test")
            return

        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['dl_src'],
                                                check_test_params=True)
        flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)

class ModifyL2Dst(BaseMatchCase):
    """
    Modify the dest MAC address (TP1)
    """
    def runTest(self):
        sup_acts = self.supported_actions
        if not (sup_acts & 1 << ofp.OFPAT_SET_DL_DST):
            skip_message_emit(self, "ModifyL2dst test")
            return

        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['dl_dst'],
                                                check_test_params=True)
        flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)

class ModifyL3Src(BaseMatchCase):
    """
    Modify the source IP address of an IP packet (TP1)
    """
    def runTest(self):
        sup_acts = self.supported_actions
        if not (sup_acts & 1 << ofp.OFPAT_SET_NW_SRC):
            skip_message_emit(self, "ModifyL3Src test")
            return

        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['ip_src'],
                                                check_test_params=True)
        flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)

class ModifyL3Dst(BaseMatchCase):
    """
    Modify the dest IP address of an IP packet (TP1)
    """
    def runTest(self):
        sup_acts = self.supported_actions
        if not (sup_acts & 1 << ofp.OFPAT_SET_NW_DST):
            skip_message_emit(self, "ModifyL3Dst test")
            return

        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['ip_dst'],
                                                check_test_params=True)
        flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)

class ModifyL4Src(BaseMatchCase):
    """
    Modify the source TCP port of a TCP packet (TP1)
    """
    def runTest(self):
        sup_acts = self.supported_actions
        if not (sup_acts & 1 << ofp.OFPAT_SET_TP_SRC):
            skip_message_emit(self, "ModifyL4Src test")
            return

        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['tcp_sport'],
                                                check_test_params=True)
        flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)

class ModifyL4Dst(BaseMatchCase):
    """
    Modify the dest TCP port of a TCP packet (TP1)
    """
    def runTest(self):
        sup_acts = self.supported_actions
        if not (sup_acts & 1 << ofp.OFPAT_SET_TP_DST):
            skip_message_emit(self, "ModifyL4Dst test")
            return

        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['tcp_dport'],
                                                check_test_params=True)
        flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)

class ModifyTOS(BaseMatchCase):
    """
    Modify the IP type of service of an IP packet (TP1)
    """
    def runTest(self):
        sup_acts = self.supported_actions
        if not (sup_acts & 1 << ofp.OFPAT_SET_NW_TOS):
            skip_message_emit(self, "ModifyTOS test")
            return

        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['ip_tos'],
                                                check_test_params=True)
        flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2, egr_count=-1)

class ModifyL2DstMC(BaseMatchCase):
    """
    Modify the L2 dest and send to 2 ports
    """
    def runTest(self):
        sup_acts = self.supported_actions
        if not (sup_acts & 1 << ofp.OFPAT_SET_DL_DST):
            skip_message_emit(self, "ModifyL2dstMC test")
            return

        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['dl_dst'],
                                                check_test_params=True)
        flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2, egr_count=-1)

class ModifyL2DstIngress(BaseMatchCase):
    """
    Modify the L2 dest and send to the ingress port
    """
    def runTest(self):
        sup_acts = self.supported_actions
        if not (sup_acts & 1 << ofp.OFPAT_SET_DL_DST):
            skip_message_emit(self, "ModifyL2dstIngress test")
            return

        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['dl_dst'],
                                                check_test_params=True)
        flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2, egr_count=0,
                        ing_port=True)

class ModifyL2DstIngressMC(BaseMatchCase):
    """
    Modify the L2 dest and send to the ingress port
    """
    def runTest(self):
        sup_acts = self.supported_actions
        if not (sup_acts & 1 << ofp.OFPAT_SET_DL_DST):
            skip_message_emit(self, "ModifyL2dstMC test")
            return

        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['dl_dst'],
                                                check_test_params=True)
        flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2, egr_count=-1,
                        ing_port=True)

class ModifyL2SrcMC(BaseMatchCase):
    """
    Modify the source MAC address (TP1) and send to multiple
    """
    def runTest(self):
        sup_acts = self.supported_actions
        if not (sup_acts & 1 << ofp.OFPAT_SET_DL_SRC):
            skip_message_emit(self, "ModifyL2SrcMC test")
            return

        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['dl_src'],
                                                check_test_params=True)
        flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2, egr_count=-1)

class ModifyL2SrcDstMC(BaseMatchCase):
    """
    Modify the L2 source and dest and send to 2 ports
    """
    def runTest(self):
        sup_acts = self.supported_actions
        if (not (sup_acts & 1 << ofp.OFPAT_SET_DL_DST) or
                not (sup_acts & 1 << ofp.OFPAT_SET_DL_SRC)):
            skip_message_emit(self, "ModifyL2SrcDstMC test")
            return

        mod_fields = ['dl_dst', 'dl_src']
        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=mod_fields,
                                                check_test_params=True)
        flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2, egr_count=-1)

class ModifyL2DstVIDMC(BaseMatchCase):
    """
    Modify the L2 dest and send to 2 ports
    """
    def runTest(self):
        sup_acts = self.supported_actions
        if (not (sup_acts & 1 << ofp.OFPAT_SET_DL_DST) or
                not (sup_acts & 1 << ofp.OFPAT_SET_VLAN_VID)):
            skip_message_emit(self, "ModifyL2DstVIDMC test")
            return

        mod_fields = ['dl_dst', 'dl_vlan']
        (pkt, exp_pkt, acts) = pkt_action_setup(self, 
             start_field_vals={'dl_vlan_enable':True}, mod_fields=mod_fields,
                                                check_test_params=True)
        flow_match_test(self, pa_port_map, pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2, egr_count=-1)

class FlowToggle(BaseMatchCase):
    """
    Add flows to the table and modify them repeatedly

    This is done by using only "add" flow messages.  Since the check overlap
    flag is not set, the switch is supposed to modify the existing flow if
    the match already exists.

    Would probably be better to exercise more of the flow modify commands
    (add, modify, delete +/- strict).
    """
    def runTest(self):
        flow_count = test_param_get(self.config, 'ft_flow_count', default=20)
        iter_count = test_param_get(self.config, 'ft_iter_count', default=10)

        logging.info("Running flow toggle with %d flows, %d iterations" %
                       (flow_count, iter_count))
        acts = []
        acts.append(action.action_output())
        acts.append(action.action_output())
    
        of_ports = pa_port_map.keys()
        if len(of_ports) < 3:
            self.assertTrue(False, "Too few ports for test")
    
        for idx in range(2):
            acts[idx].port = of_ports[idx]
    
        flows = []
        flows.append([])
        flows.append([])
    
        wildcards = (required_wildcards(self) | ofp.OFPFW_DL_SRC |
                     ofp.OFPFW_DL_DST)
        # Create up the flows in an array
        for toggle in range(2):
            for f_idx in range(flow_count):
                pkt = simple_tcp_packet(tcp_sport=f_idx)
                msg = message.flow_mod()
                match = packet_to_flow_match(self, pkt)
                match.in_port = of_ports[2]
                match.wildcards = wildcards
                msg.match = match
                msg.buffer_id = 0xffffffff
                msg.command = ofp.OFPFC_ADD
                msg.actions.add(acts[toggle])
                flows[toggle].append(msg)

        # Show two sample flows
        logging.debug(flows[0][0].show())
        logging.debug(flows[1][0].show())

        # Install the first set of flows
        for f_idx in range(flow_count):
            rv = self.controller.message_send(flows[0][f_idx])
            self.assertTrue(rv != -1, "Error installing flow %d" % f_idx)
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
    
        logging.info("Installed %d flows" % flow_count)
    
        # Repeatedly modify all the flows back and forth
        updates = 0
        # Report status about 5 times
        mod_val = (iter_count / 4) + 1
        start = time.time()
        for iter_idx in range(iter_count):
            if not iter_idx % mod_val:
                logging.info("Flow Toggle: iter %d of %d. " %
                               (iter_idx, iter_count) + 
                               "%d updates in %d secs" %
                               (updates, time.time() - start))
            for toggle in range(2):
                t_idx = 1 - toggle
                for f_idx in range(flow_count):
                    rv = self.controller.message_send(flows[t_idx][f_idx])
                    updates += 1
                    self.assertTrue(rv != -1, "Error modifying flow %d" % 
                                    f_idx)
                self.assertEqual(do_barrier(self.controller), 0,
                                 "Barrier failed")

        end = time.time()
        divisor = end - start or (end - start + 1)
        logging.info("Flow toggle: %d iterations" % iter_count)
        logging.info("   %d flow mods in %d secs, %d mods/sec" %
                       (updates, end - start, updates/divisor))
            

# You can pick and choose these by commenting tests in or out
iter_classes = [
    basic.PacketIn,
    basic.PacketOut,
    DirectPacket,
    FlowToggle,
    DirectTwoPorts,
    DirectMCNonIngress,
    AllWildcardMatch,
    AllWildcardMatchTagged,
    SingleWildcardMatch,
    SingleWildcardMatchTagged,
    ExactMatch,
    ExactMatchTagged,
    SingleWildcardMatch,
    ModifyL2Src,
    ModifyL2Dst,
    ModifyL2SrcMC,
    ModifyL2DstMC,
    ModifyL2SrcDstMC
    ]

class IterCases(BaseMatchCase):
    """
    Iterate over a bunch of test cases

    The cases come from the list above
    """

    priority = -1

    def runTest(self):
        count = test_param_get(self.config, 'iter_count', default=10)
        tests_done = 0
        logging.info("Running iteration test " + str(count) + " times")
        start = time.time()
        last = start
        for idx in range(count):
            logging.info("Iteration " + str(idx + 1))
            for cls in iter_classes:
                test = cls()
                test.inheritSetup(self)
                test.runTest()
                tests_done += 1
                # Report update about every minute, between tests
                if time.time() - last > 60:
                    last = time.time()
                    logging.info(
                        "IterCases: Iter %d of %d; Ran %d tests in %d " %
                        (idx, count, tests_done, last - start) + 
                        "seconds so far")
        stats = all_stats_get(self)
        last = time.time()
        logging.info("\nIterCases ran %d tests in %d seconds." %
                       (tests_done, last - start))
        logging.info("    flows: %d. packets: %d. bytes: %d" %
                       (stats["flows"], stats["packets"], stats["bytes"]))
        logging.info("    active: %d. lookups: %d. matched %d." %
                       (stats["active"], stats["lookups"], stats["matched"]))

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

    priority = -1

class MatchEach(basic.SimpleDataPlane):
    """
    Check that each match field is actually matched on.
    Installs two flows that differ in one field. The flow that should not
    match has a higher priority, so if that field is ignored during matching
    the packet will be sent out the wrong port.

    TODO test UDP, ARP, ICMP, etc.
    """
    def runTest(self):
        of_ports = pa_port_map.keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        delete_all_flows(self.controller)

        pkt = simple_tcp_packet()
        ingress_port = of_ports[0]
        egress_port = of_ports[1]

        def testField(field, mask):
            logging.info("Testing field %s" % field)

            def addFlow(matching, priority, output_port):
                match = packet_to_flow_match(self, pkt)
                self.assertTrue(match is not None, "Could not generate flow match from pkt")
                match.wildcards &= ~ofp.OFPFW_IN_PORT
                match.in_port = ingress_port
                if not matching:
                    # Make sure flow doesn't match
                    orig = getattr(match, field)
                    if isinstance(orig, list):
                        new = map(lambda a: ~a[0] & a[1], zip(orig, mask))
                    else:
                        new = ~orig & mask
                    setattr(match, field, new)
                request = message.flow_mod()
                request.match = match
                request.buffer_id = 0xffffffff
                request.priority = priority
                act = action.action_output()
                act.port = output_port
                self.assertTrue(request.actions.add(act), "Could not add action")
                logging.info("Inserting flow")
                self.controller.message_send(request)

            # This flow should match.
            addFlow(matching=True, priority=0, output_port=egress_port)
            # This flow should not match, but it has a higher priority.
            addFlow(matching=False, priority=1, output_port=ofp.OFPP_IN_PORT)

            self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")

            logging.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))

            exp_pkt_arg = None
            exp_port = None
            if pa_config["relax"]:
                exp_pkt_arg = pkt
                exp_port = egress_port

            (rcv_port, rcv_pkt, pkt_time) = self.dataplane.poll(port_number=exp_port,
                                                                exp_pkt=exp_pkt_arg)
            self.assertTrue(rcv_pkt is not None, "Did not receive packet")
            logging.debug("Packet len " + str(len(rcv_pkt)) + " in on " + str(rcv_port))
            self.assertEqual(rcv_port, egress_port, "Unexpected receive port")
            self.assertEqual(str(pkt), str(rcv_pkt), 'Response packet does not match send packet')

        # TODO in_port
        testField("dl_src", [0xff]*6)
        testField("dl_dst", [0xff]*6)
        testField("dl_type", 0xffff)
        testField("dl_vlan", 0xfff)
        # TODO dl_vlan_pcp
        testField("nw_src", 0xffffffff)
        testField("nw_dst", 0xffffffff)
        testField("nw_tos", 0x3f)
        testField("nw_proto", 0xff)
        testField("tp_src", 0xffff)
        testField("tp_dst", 0xffff)

if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test_spec=basic"
