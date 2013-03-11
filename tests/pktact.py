"""
Test cases for testing actions taken on packets

See basic.py for other info.

It is recommended that these definitions be kept in their own
namespace as different groups of tests will likely define 
similar identifiers.

The switch is actively attempting to contact the controller at the address
indicated in config.

"""

import copy
import logging
import time
import unittest
import random
import scapy.all as scapy

from oftest import config
import oftest.controller as controller
import ofp
import oftest.dataplane as dataplane
import oftest.parse as parse
import oftest.base_tests as base_tests
import basic # for IterCases

from oftest.parse import parse_mac, parse_ip

from oftest.testutils import *

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

@group('smoke')
class DirectPacket(base_tests.SimpleDataPlane):
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
        of_ports = config["port_map"].keys()
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
        act = ofp.action.output()

        for idx in range(len(of_ports)):
            delete_all_flows(self.controller)

            ingress_port = of_ports[idx]
            egress_port = of_ports[(idx + 1) % len(of_ports)]
            logging.info("Ingress " + str(ingress_port) + 
                             " to egress " + str(egress_port))

            match.in_port = ingress_port

            request = ofp.message.flow_mod()
            request.match = match

            request.buffer_id = 0xffffffff
            act.port = egress_port
            request.actions.append(act)

            logging.info("Inserting flow")
            self.controller.message_send(request)
            do_barrier(self.controller)

            logging.info("Sending packet to dp port " + 
                           str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))

            exp_pkt_arg = None
            exp_port = None
            if config["relax"]:
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

@group('smoke')
class DirectPacketController(base_tests.SimpleDataPlane):
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
        of_ports = config["port_map"].keys()
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
        act = ofp.action.output()

        delete_all_flows(self.controller)

        ingress_port = of_ports[0]
        match.in_port = ingress_port

        request = ofp.message.flow_mod()
        request.match = match

        request.buffer_id = 0xffffffff
        act.port = ofp.OFPP_CONTROLLER
        act.max_len = 65535
        request.actions.append(act)

        logging.info("Inserting flow")
        self.controller.message_send(request)
        do_barrier(self.controller)

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


class DirectPacketQueue(base_tests.SimpleDataPlane):
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
        for qs in queue_stats.entries:
            if qs.port_no != port_num:
                continue
            result.append(qs.queue_id)
        return result

    def handleFlow(self, pkttype='TCP'):
        of_ports = config["port_map"].keys()
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
        
        request = ofp.message.queue_stats_request()
        request.port_no  = ofp.OFPP_ALL
        request.queue_id = ofp.OFPQ_ALL
        (queue_stats, p) = self.controller.transact(request)
        self.assertNotEqual(queue_stats, None, "Queue stats request failed")

        act = ofp.action.enqueue()

        for idx in range(len(of_ports)):
            ingress_port = of_ports[idx]
            egress_port = of_ports[(idx + 1) % len(of_ports)]

            for egress_queue_id in self.portQueuesGet(queue_stats, egress_port):
                logging.info("Ingress " + str(ingress_port)
                               + " to egress " + str(egress_port)
                               + " queue " + str(egress_queue_id)
                               )

                delete_all_flows(self.controller)

                match.in_port = ingress_port
                
                request = ofp.message.flow_mod()
                request.match = match

                request.buffer_id = 0xffffffff
                act.port     = egress_port
                act.queue_id = egress_queue_id
                request.actions.append(act)

                logging.info("Inserting flow")
                self.controller.message_send(request)
                do_barrier(self.controller)

                # Get current stats for selected egress queue

                request = ofp.message.queue_stats_request()
                request.port_no  = egress_port
                request.queue_id = egress_queue_id
                (qs_before, p) = self.controller.transact(request)
                self.assertNotEqual(qs_before, None, "Queue stats request failed")

                logging.info("Sending packet to dp port " + 
                               str(ingress_port))
                self.dataplane.send(ingress_port, str(pkt))
                
                exp_pkt_arg = None
                exp_port = None
                if config["relax"]:
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

                request = ofp.message.queue_stats_request()
                request.port_no  = egress_port
                request.queue_id = egress_queue_id
                (qs_after, p) = self.controller.transact(request)
                self.assertNotEqual(qs_after, None, "Queue stats request failed")

                # Make sure that tx packet counter for selected egress queue was
                # incremented

                self.assertEqual(qs_after.entries[0].tx_packets, \
                                 qs_before.entries[0].tx_packets + 1, \
                                 "Verification of egress queue tx packet count failed"
                                 )
                    

class DirectPacketControllerQueue(base_tests.SimpleDataPlane):
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
        for qs in queue_stats.entries:
            if qs.port_no != port_num:
                continue
            result.append(qs.queue_id)
        return result

    def handleFlow(self, pkttype='TCP'):
        of_ports = config["port_map"].keys()
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
        
        request = ofp.message.queue_stats_request()
        request.port_no  = ofp.OFPP_CONTROLLER
        request.queue_id = ofp.OFPQ_ALL
        (queue_stats, p) = self.controller.transact(request)
        self.assertNotEqual(queue_stats, None, "Queue stats request failed")
        if queue_stats.type == ofp.OFPT_ERROR:
            skip_message_emit(self, "Enqueue packet to controller")
            return

        act = ofp.action.enqueue()

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

                delete_all_flows(self.controller)

                match.in_port = ingress_port
                
                request = ofp.message.flow_mod()
                request.match = match

                request.buffer_id = 0xffffffff
                act.port     = egress_port
                act.queue_id = egress_queue_id
                request.actions.append(act)

                logging.info("Inserting flow")
                self.controller.message_send(request)
                do_barrier(self.controller)

                # Get current stats for selected egress queue

                request = ofp.message.queue_stats_request()
                request.port_no  = egress_port
                request.queue_id = egress_queue_id
                (qs_before, p) = self.controller.transact(request)
                self.assertNotEqual(qs_before, None, "Queue stats request failed")

                logging.info("Sending packet to dp port " + 
                               str(ingress_port))
                self.dataplane.send(ingress_port, str(pkt))
                
                exp_pkt_arg = None
                exp_port = None

                count = 0
                while True:
                    (response, raw) = self.controller.poll(ofp.OFPT_PACKET_IN)
                    if not response:  # Timeout
                        break
                    if dataplane.match_exp_pkt(pkt, response.data): # Got match
                        break
                    if not config["relax"]:  # Only one attempt to match
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

                request = ofp.message.queue_stats_request()
                request.port_no  = egress_port
                request.queue_id = egress_queue_id
                (qs_after, p) = self.controller.transact(request)
                self.assertNotEqual(qs_after, None, "Queue stats request failed")

                # Make sure that tx packet counter for selected egress queue was
                # incremented

                self.assertEqual(qs_after.entries[0].tx_packets, \
                                 qs_before.entries[0].tx_packets + 1, \
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

class DirectTwoPorts(base_tests.SimpleDataPlane):
    """
    Send packet to two egress ports

    Generate a packet
    Generate and install a matching flow
    Add action to direct the packet to two egress ports
    Send the packet to ingress dataplane port
    Verify the packet is received at the two egress ports
    """
    def runTest(self):
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")

        for idx in range(len(of_ports)):
            delete_all_flows(self.controller)

            ingress_port = of_ports[idx]
            egress_port1 = of_ports[(idx + 1) % len(of_ports)]
            egress_port2 = of_ports[(idx + 2) % len(of_ports)]
            logging.info("Ingress " + str(ingress_port) + 
                           " to egress " + str(egress_port1) + " and " +
                           str(egress_port2))

            match.in_port = ingress_port

            request = ofp.message.flow_mod()
            request.match = match
            request.buffer_id = 0xffffffff
            request.actions.append(ofp.action.output(port=egress_port1))
            request.actions.append(ofp.action.output(port=egress_port2))
            # logging.info(request.show())

            logging.info("Inserting flow")
            self.controller.message_send(request)
            do_barrier(self.controller)

            logging.info("Sending packet to dp port " + 
                           str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            yes_ports = set([egress_port1, egress_port2])
            no_ports = set(of_ports).difference(yes_ports)

            receive_pkt_check(self.dataplane, pkt, yes_ports, no_ports,
                              self)

class DirectMCNonIngress(base_tests.SimpleDataPlane):
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
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")

        for ingress_port in of_ports:
            delete_all_flows(self.controller)

            logging.info("Ingress " + str(ingress_port) + 
                           " all non-ingress ports")
            match.in_port = ingress_port

            request = ofp.message.flow_mod()
            request.match = match
            request.buffer_id = 0xffffffff
            for egress_port in of_ports:
                if egress_port == ingress_port:
                    continue
                request.actions.append(ofp.action.output(port=egress_port))
            logging.debug(request.show())

            logging.info("Inserting flow")
            self.controller.message_send(request)
            do_barrier(self.controller)

            logging.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            yes_ports = set(of_ports).difference([ingress_port])
            receive_pkt_check(self.dataplane, pkt, yes_ports, [ingress_port],
                              self)


class DirectMC(base_tests.SimpleDataPlane):
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
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")

        for ingress_port in of_ports:
            delete_all_flows(self.controller)

            logging.info("Ingress " + str(ingress_port) + " to all ports")
            match.in_port = ingress_port

            request = ofp.message.flow_mod()
            request.match = match
            request.buffer_id = 0xffffffff
            for egress_port in of_ports:
                act = ofp.action.output()
                if egress_port == ingress_port:
                    act.port = ofp.OFPP_IN_PORT
                else:
                    act.port = egress_port
                request.actions.append(act)
            # logging.info(request.show())

            logging.info("Inserting flow")
            self.controller.message_send(request)
            do_barrier(self.controller)

            logging.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            receive_pkt_check(self.dataplane, pkt, of_ports, [], self)

class Flood(base_tests.SimpleDataPlane):
    """
    Flood to all ports except ingress

    Make sure noflood bit is off on all ports
    Generate a packet
    Generate and install a matching flow
    Add action to flood the packet
    Send the packet to ingress dataplane port
    Verify the packet is received at all other ports
    """
    def runTest(self):
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = ofp.action.output()

        for of_port in of_ports:
            # Clear relevant bits that might block ports
            rv = port_config_set(self.controller, of_port, 0,
                                 ofp.OFPPC_NO_FLOOD | ofp.OFPPC_NO_FWD |
                                 ofp.OFPPC_PORT_DOWN)
            self.assertTrue(rv == 0, "Did not set port config")
            logging.debug("Enabled and cleared no-flood for port " + str(of_port))

        for ingress_port in of_ports:
            delete_all_flows(self.controller)

            logging.info("Ingress " + str(ingress_port) + " to all ports")
            match.in_port = ingress_port

            request = ofp.message.flow_mod()
            request.match = match
            request.buffer_id = 0xffffffff
            act.port = ofp.OFPP_FLOOD
            request.actions.append(act)
            logging.info(request.show())

            logging.info("Inserting flow")
            self.controller.message_send(request)
            do_barrier(self.controller)

            logging.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            yes_ports = set(of_ports).difference([ingress_port])
            receive_pkt_check(self.dataplane, pkt, yes_ports, [ingress_port],
                              self)

class FloodPlusIngress(base_tests.SimpleDataPlane):
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
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")

        for ingress_port in of_ports:
            delete_all_flows(self.controller)

            logging.info("Ingress " + str(ingress_port) + " to all ports")
            match.in_port = ingress_port

            request = ofp.message.flow_mod()
            request.match = match
            request.buffer_id = 0xffffffff
            request.actions.append(ofp.action.output(port=ofp.OFPP_FLOOD))
            request.actions.append(ofp.action.output(port=ofp.OFPP_IN_PORT))
            logging.info(request.show())

            logging.info("Inserting flow")
            self.controller.message_send(request)
            do_barrier(self.controller)

            logging.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            receive_pkt_check(self.dataplane, pkt, of_ports, [], self)

class All(base_tests.SimpleDataPlane):
    """
    Send to OFPP_ALL port

    Generate a packet
    Generate and install a matching flow
    Add action to forward to OFPP_ALL
    Send the packet to ingress dataplane port
    Verify the packet is received at all other ports
    """
    def runTest(self):
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = ofp.action.output()

        for ingress_port in of_ports:
            delete_all_flows(self.controller)

            logging.info("Ingress " + str(ingress_port) + " to all ports")
            match.in_port = ingress_port

            request = ofp.message.flow_mod()
            request.match = match
            request.buffer_id = 0xffffffff
            act.port = ofp.OFPP_ALL
            request.actions.append(act)
            logging.info(request.show())

            logging.info("Inserting flow")
            self.controller.message_send(request)
            do_barrier(self.controller)

            logging.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            yes_ports = set(of_ports).difference([ingress_port])
            receive_pkt_check(self.dataplane, pkt, yes_ports, [ingress_port],
                              self)

class AllPlusIngress(base_tests.SimpleDataPlane):
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
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")

        for ingress_port in of_ports:
            delete_all_flows(self.controller)

            logging.info("Ingress " + str(ingress_port) + " to all ports")
            match.in_port = ingress_port

            request = ofp.message.flow_mod()
            request.match = match
            request.buffer_id = 0xffffffff
            request.actions.append(ofp.action.output(port=ofp.OFPP_ALL))
            request.actions.append(ofp.action.output(port=ofp.OFPP_IN_PORT))
            logging.info(request.show())

            logging.info("Inserting flow")
            self.controller.message_send(request)
            do_barrier(self.controller)

            logging.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            receive_pkt_check(self.dataplane, pkt, of_ports, [], self)
            
class FloodMinusPort(base_tests.SimpleDataPlane):
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
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 2, "Not enough ports for test")

        pkt = simple_tcp_packet()
        match = packet_to_flow_match(self, pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        act = ofp.action.output()

        # Clear OFPPC_NO_FLOOD on each port
        for of_port in of_ports:
            rv = port_config_set(self.controller, of_port,
                                 0, ofp.OFPPC_NO_FLOOD)
            self.assertEqual(rv, 0, "Failed to set port config")

        for idx in range(len(of_ports)):
            delete_all_flows(self.controller)

            ingress_port = of_ports[idx]
            no_flood_idx = (idx + 1) % len(of_ports)
            no_flood_port = of_ports[no_flood_idx]
            rv = port_config_set(self.controller, no_flood_port,
                                 ofp.OFPPC_NO_FLOOD, ofp.OFPPC_NO_FLOOD)
            self.assertEqual(rv, 0, "Failed to set port config")

            match.in_port = ingress_port

            request = ofp.message.flow_mod()
            request.match = match
            request.buffer_id = 0xffffffff
            act.port = ofp.OFPP_FLOOD
            request.actions.append(act)
            logging.info(request.show())

            logging.info("Inserting flow")
            self.controller.message_send(request)
            do_barrier(self.controller)

            logging.info("Sending packet to dp port " + str(ingress_port))
            logging.info("No flood port is " + str(no_flood_port))
            self.dataplane.send(ingress_port, str(pkt))
            no_ports = set([ingress_port, no_flood_port])
            yes_ports = set(of_ports).difference(no_ports)
            receive_pkt_check(self.dataplane, pkt, yes_ports, no_ports, self)

            # Turn no flood off again
            rv = port_config_set(self.controller, no_flood_port,
                                 0, ofp.OFPPC_NO_FLOOD)
            self.assertEqual(rv, 0, "Failed to reset port config")
            do_barrier(self.controller)

            # Check that packets are now flooded to no_flood_port
            logging.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))
            no_ports = set([ingress_port])
            yes_ports = set(of_ports).difference(no_ports)
            receive_pkt_check(self.dataplane, pkt, yes_ports, no_ports, self)

            #@todo Should check no other packets received



################################################################

class BaseMatchCase(base_tests.SimpleDataPlane):
    def setUp(self):
        base_tests.SimpleDataPlane.setUp(self)
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
        flow_match_test(self, config["port_map"])

class ExactMatchTagged(BaseMatchCase):
    """
    Exact match for all port pairs with tagged pkts
    """

    def runTest(self):
        vid = test_param_get('vid', default=TEST_VID_DEFAULT)
        flow_match_test(self, config["port_map"], vlan_vid=vid)

@disabled
class ExactMatchTaggedMany(BaseMatchCase):
    """
    ExactMatchTagged with many VLANS
    """

    def runTest(self):
        for vid in range(2,100,10):
            flow_match_test(self, config["port_map"], vlan_vid=vid, max_test=5)
        for vid in range(100,4000,389):
            flow_match_test(self, config["port_map"], vlan_vid=vid, max_test=5)
        flow_match_test(self, config["port_map"], vlan_vid=4094, max_test=5)

class SingleWildcardMatchPriority(BaseMatchCase):
    """
    SingleWildcardMatchPriority
    """

    def _Init(self):
        self.pkt = simple_tcp_packet()
        self.flowMsgs = {}

    def _ClearTable(self):
        delete_all_flows(self.controller)
        do_barrier(self.controller)

    def runTest(self):
        
        self._Init()
        of_ports = config["port_map"].keys()
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
            do_barrier(self.controller)
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

        of_ports = config["port_map"].keys()
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
    2. Add wildcard flow with higher priority, verify packet received
    on port specified by this flow.
    3. Add wildcard flow with lower priority, verify packet received
    on port specified by the highest priority flow.
    """

    def runTest(self):
        
        self._Init()

        of_ports = config["port_map"].keys()
        of_ports.sort()

        self._ClearTable()

        # Install a flow with wildcards
        self.installFlow(999, of_ports[0], of_ports[1], 
                         wildcards=ofp.OFPFW_DL_DST)
        self.verifyFlow(of_ports[0], of_ports[1])
        # Install a flow with wildcards with higher priority
        self.installFlow(1000, of_ports[0], of_ports[2],
                         wildcards=ofp.OFPFW_DL_DST)
        self.verifyFlow(of_ports[0], of_ports[2])
        # Install a flow with wildcards with lower priority
        self.installFlow(999, of_ports[0], of_ports[1],
                         wildcards=ofp.OFPFW_DL_SRC)
        self.verifyFlow(of_ports[0], of_ports[2])
        

@group("smoke")
class WildcardPriorityWithDelete(SingleWildcardMatchPriority):
    """
    1. Add wildcard match flow, verify packet received.
    2. Add wildcard flow with higher priority, verify packet received on port
    specified by this flow.
    3. Add wildcard flow with even higher priority, verify packet received
    on port specified by this flow.
    4. Delete lowest priority flow, verify packet received on port specified
    by highest priority flow.
    5. Delete highest priority flow, verify packet received on port specified
    by remaining flow.
    """

    def runTest(self):
        
        self._Init()

        of_ports = config["port_map"].keys()
        of_ports.sort()

        self._ClearTable()

        # Install a flow with wildcards
        self.installFlow(250, of_ports[0], of_ports[1],
                         wildcards=ofp.OFPFW_DL_DST)
        self.verifyFlow(of_ports[0], of_ports[1])
        # Install a flow with wildcards of higher priority
        self.installFlow(1250, of_ports[0], of_ports[2],
                         wildcards=ofp.OFPFW_DL_DST)
        self.verifyFlow(of_ports[0], of_ports[2])
        # Install a flow with wildcards with even higher priority
        self.installFlow(2001, of_ports[0], of_ports[3],
                         wildcards=ofp.OFPFW_DL_DST)
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
        vid = test_param_get('vid', default=TEST_VID_DEFAULT)
        for wc in WILDCARD_VALUES:
            wc |= required_wildcards(self)
            if wc & ofp.OFPFW_DL_VLAN:
                # Set nonzero VLAN id to avoid sending priority-tagged packet
                vlan_vid = vid
            else:
                vlan_vid = -1
            flow_match_test(self, config["port_map"], wildcards=wc, 
                            vlan_vid=vlan_vid, max_test=10)

class SingleWildcardMatchTagged(BaseMatchCase):
    """
    SingleWildcardMatch with tagged packets
    """
    def runTest(self):
        vid = test_param_get('vid', default=TEST_VID_DEFAULT)
        for wc in WILDCARD_VALUES:
            wc |= required_wildcards(self)
            flow_match_test(self, config["port_map"], wildcards=wc, vlan_vid=vid,
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
        vid = test_param_get('vid', default=TEST_VID_DEFAULT)
        for all_exp_one_wildcard in NO_WILDCARD_VALUES:
            all_exp_one_wildcard |= required_wildcards(self)
            if all_exp_one_wildcard & ofp.OFPFW_DL_VLAN:
                # Set nonzero VLAN id to avoid sending priority-tagged packet
                vlan_vid = vid
            else:
                vlan_vid = -1
            flow_match_test(self, config["port_map"], wildcards=all_exp_one_wildcard,
                            vlan_vid=vlan_vid)

class AllExceptOneWildcardMatchTagged(BaseMatchCase):
    """
    Match one field with tagged packets
    """
    def runTest(self):
        vid = test_param_get('vid', default=TEST_VID_DEFAULT)
        for all_exp_one_wildcard in NO_WILDCARD_VALUES:
            all_exp_one_wildcard |= required_wildcards(self)
            flow_match_test(self, config["port_map"], wildcards=all_exp_one_wildcard,
                            vlan_vid=vid)

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
        flow_match_test(self, config["port_map"], wildcards=ofp.OFPFW_ALL)

class AllWildcardMatchTagged(BaseMatchCase):
    """
    AllWildcardMatch with tagged packets
    """
    def runTest(self):
        vid = test_param_get('vid', default=TEST_VID_DEFAULT)
        flow_match_test(self, config["port_map"], wildcards=ofp.OFPFW_ALL, 
                        vlan_vid=vid)

@group('smoke')
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
                                    vlan_vid=new_vid)
        vid_act = ofp.action.set_vlan_vid()
        vid_act.vlan_vid = new_vid

        flow_match_test(self, config["port_map"], pkt=pkt, 
                        exp_pkt=exp_pkt, action_list=[vid_act])

@disabled
class PacketOnly(base_tests.DataPlaneOnly):
    """
    Just send a packet thru the switch
    """

    def runTest(self):
        pkt = simple_tcp_packet()
        of_ports = config["port_map"].keys()
        of_ports.sort()
        ing_port = of_ports[0]
        logging.info("Sending packet to " + str(ing_port))
        logging.debug("Data: " + str(pkt).encode('hex'))
        self.dataplane.send(ing_port, str(pkt))

@disabled
class PacketOnlyTagged(base_tests.DataPlaneOnly):
    """
    Just send a packet thru the switch
    """

    def runTest(self):
        vid = test_param_get('vid', default=TEST_VID_DEFAULT)
        pkt = simple_tcp_packet(dl_vlan_enable=True, vlan_vid=vid)
        of_ports = config["port_map"].keys()
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

        pkt = simple_tcp_packet(dl_vlan_enable=True, vlan_vid=old_vid)
        exp_pkt = simple_tcp_packet(dl_vlan_enable=True, vlan_vid=new_vid)
        vid_act = ofp.action.set_vlan_vid()
        vid_act.vlan_vid = new_vid

        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt,
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
    With vlan ID and priority wildcarded, perform SET_VLAN_VID ofp.action.
    The same flow should match on both untagged and tagged packets.
    """
    def runTest(self):
        old_vid = 2
        new_vid = 3
        sup_acts = self.supported_actions
        if not (sup_acts & 1 << ofp.OFPAT_SET_VLAN_VID):
            skip_message_emit(self, "ModifyVIDWithTagWildcarded test")
            return

        of_ports = config["port_map"].keys()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        ing_port = of_ports[0]
        egr_ports = of_ports[1]
        
        delete_all_flows(self.controller)

        len_untagged = 100
        len_w_vid = 104
        untagged_pkt = simple_tcp_packet(pktlen=len_untagged)
        tagged_pkt = simple_tcp_packet(pktlen=len_w_vid, 
                                       dl_vlan_enable=True, vlan_vid=old_vid)
        exp_pkt = simple_tcp_packet(pktlen=len_w_vid, dl_vlan_enable=True,
                                    vlan_vid=new_vid)
        wildcards = (required_wildcards(self) | ofp.OFPFW_DL_VLAN |
                     ofp.OFPFW_DL_VLAN_PCP)
        vid_act = ofp.action.set_vlan_vid()
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

        pkt = simple_tcp_packet(dl_vlan_enable=True, vlan_vid=vid, vlan_pcp=old_vlan_pcp)
        exp_pkt = simple_tcp_packet(dl_vlan_enable=True, vlan_vid=vid, vlan_pcp=new_vlan_pcp)
        vid_act = ofp.action.set_vlan_pcp()
        vid_act.vlan_pcp = new_vlan_pcp

        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt,
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
                                vlan_vid=old_vid)
        exp_pkt = simple_tcp_packet(pktlen=len)
        vid_act = ofp.action.strip_vlan()

        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt,
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
                                vlan_vid=old_vid)
        exp_pkt = simple_tcp_packet(pktlen=len_untagged)
        wildcards = (required_wildcards(self) | ofp.OFPFW_DL_VLAN |
                     ofp.OFPFW_DL_VLAN_PCP)
        vid_act = ofp.action.strip_vlan()

        flow_match_test(self, config["port_map"], 
                        wildcards=wildcards,
                        pkt=pkt, exp_pkt=exp_pkt,
                        action_list=[vid_act])

def init_pkt_args():
    """
    Pass back a dictionary with default packet arguments
    """
    args = {}
    args["eth_src"] = '00:23:45:67:89:AB'

    dl_vlan_enable=False
    vlan_vid=-1
    if config["test-params"]["vid"]:
        dl_vlan_enable=True
        vlan_vid = config["test-params"]["vid"]

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

        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['eth_src'],
                                                check_test_params=True)
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt, 
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

        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['eth_dst'],
                                                check_test_params=True)
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt, 
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
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt, 
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
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt, 
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
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)

class ModifyL4SrcUdp(BaseMatchCase):
    """
    Modify the source UDP port of a UDP packet
    """
    def runTest(self):
        sup_acts = self.supported_actions
        if not (sup_acts & 1 << ofp.OFPAT_SET_TP_DST):
            skip_message_emit(self, "ModifyL4SrcUdp test")
            return

        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['udp_sport'],
                                                check_test_params=True, tp="udp")
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt,
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
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)

class ModifyL4DstUdp(BaseMatchCase):
    """
    Modify the dest UDP port of a UDP packet
    """
    def runTest(self):
        sup_acts = self.supported_actions
        if not (sup_acts & 1 << ofp.OFPAT_SET_TP_DST):
            skip_message_emit(self, "ModifyL4DstUdp test")
            return

        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['udp_dport'],
                                                check_test_params=True, tp="udp")
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt,
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
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt, 
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

        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['eth_dst'],
                                                check_test_params=True)
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt, 
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

        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['eth_dst'],
                                                check_test_params=True)
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt, 
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

        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['eth_dst'],
                                                check_test_params=True)
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt, 
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

        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=['eth_src'],
                                                check_test_params=True)
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt, 
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

        mod_fields = ['eth_dst', 'eth_src']
        (pkt, exp_pkt, acts) = pkt_action_setup(self, mod_fields=mod_fields,
                                                check_test_params=True)
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt, 
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

        mod_fields = ['eth_dst', 'vlan_vid']
        (pkt, exp_pkt, acts) = pkt_action_setup(self, 
             start_field_vals={'dl_vlan_enable':True}, mod_fields=mod_fields,
                                                check_test_params=True)
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2, egr_count=-1)

@group("smoke")
class ModifyAll(BaseMatchCase):
    """
    Modify all supported fields and output to a port
    """
    def runTest(self):
        sup_acts = self.supported_actions

        sup_map = {
            "eth_dst" : ofp.OFPAT_SET_DL_DST,
            "eth_src" : ofp.OFPAT_SET_DL_SRC,
            "dl_vlan_enable" : ofp.OFPAT_SET_VLAN_VID,
            "vlan_vid" : ofp.OFPAT_SET_VLAN_VID,
            "vlan_pcp" : ofp.OFPAT_SET_VLAN_PCP,
            "ip_src" : ofp.OFPAT_SET_NW_SRC,
            "ip_dst" : ofp.OFPAT_SET_NW_DST,
            "ip_tos" : ofp.OFPAT_SET_NW_TOS,
            "tcp_sport" : ofp.OFPAT_SET_TP_SRC,
            "tcp_dport" : ofp.OFPAT_SET_TP_DST,
        }

        mod_fields = [field for (field, bit) in sup_map.items() if (sup_acts & 1 << bit)]
        random.shuffle(mod_fields)
        start_field_vals = { "dl_vlan_enable" : True }
        mod_field_vals = { "dl_vlan_enable" : True }
        logging.info("modifying fields: %s" % repr(mod_fields))

        (pkt, exp_pkt, acts) = pkt_action_setup(self,
                                                mod_fields=mod_fields,
                                                start_field_vals=start_field_vals,
                                                mod_field_vals=mod_field_vals,
                                                check_test_params=True)
        flow_match_test(self, config["port_map"], pkt=pkt, exp_pkt=exp_pkt, 
                        action_list=acts, max_test=2)

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
        flow_count = test_param_get('ft_flow_count', default=20)
        iter_count = test_param_get('ft_iter_count', default=10)

        logging.info("Running flow toggle with %d flows, %d iterations" %
                       (flow_count, iter_count))
        acts = []
        acts.append(ofp.action.output())
        acts.append(ofp.action.output())
    
        of_ports = config["port_map"].keys()
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
                msg = ofp.message.flow_mod()
                match = packet_to_flow_match(self, pkt)
                match.in_port = of_ports[2]
                match.wildcards = wildcards
                msg.match = match
                msg.buffer_id = 0xffffffff
                msg.command = ofp.OFPFC_ADD
                msg.actions.append(acts[toggle])
                flows[toggle].append(msg)

        # Show two sample flows
        logging.debug(flows[0][0].show())
        logging.debug(flows[1][0].show())

        # Install the first set of flows
        for f_idx in range(flow_count):
            self.controller.message_send(flows[0][f_idx])
        do_barrier(self.controller)
    
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
                    self.controller.message_send(flows[t_idx][f_idx])
                    updates += 1
                do_barrier(self.controller)

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

@disabled
class IterCases(BaseMatchCase):
    """
    Iterate over a bunch of test cases

    The cases come from the list above
    """

    def runTest(self):
        count = test_param_get('iter_count', default=10)
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

@disabled
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

@group('smoke')
class MatchEach(base_tests.SimpleDataPlane):
    """
    Check that each match field is actually matched on.
    Installs two flows that differ in one field. The flow that should not
    match has a higher priority, so if that field is ignored during matching
    the packet will be sent out the wrong port.

    TODO test UDP, ARP, ICMP, etc.
    """
    def runTest(self):
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        delete_all_flows(self.controller)

        pkt = simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2)
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
                request = ofp.message.flow_mod()
                request.match = match
                request.buffer_id = 0xffffffff
                request.priority = priority
                act = ofp.action.output()
                act.port = output_port
                request.actions.append(act)
                logging.info("Inserting flow")
                self.controller.message_send(request)

            # This flow should match.
            addFlow(matching=True, priority=0, output_port=egress_port)
            # This flow should not match, but it has a higher priority.
            addFlow(matching=False, priority=1, output_port=ofp.OFPP_IN_PORT)

            do_barrier(self.controller)

            logging.info("Sending packet to dp port " + str(ingress_port))
            self.dataplane.send(ingress_port, str(pkt))

            exp_pkt_arg = None
            exp_port = None
            if config["relax"]:
                exp_pkt_arg = pkt
                exp_port = egress_port

            (rcv_port, rcv_pkt, pkt_time) = self.dataplane.poll(port_number=exp_port,
                                                                exp_pkt=exp_pkt_arg)
            self.assertTrue(rcv_pkt is not None, "Did not receive packet")
            logging.debug("Packet len " + str(len(rcv_pkt)) + " in on " + str(rcv_port))
            self.assertEqual(rcv_port, egress_port, "Unexpected receive port")
            self.assertEqual(str(pkt), str(rcv_pkt), 'Response packet does not match send packet')

        wildcards = required_wildcards(self)
        # TODO in_port
        if not (wildcards & ofp.OFPFW_DL_SRC):
            testField("eth_src", [0xff]*6)
        if not (wildcards & ofp.OFPFW_DL_DST):
            testField("eth_dst", [0xff]*6)
        if not (wildcards & ofp.OFPFW_DL_TYPE):
            testField("eth_type", 0xffff)
        if not (wildcards & ofp.OFPFW_DL_VLAN):
            testField("vlan_vid", 0xfff)
        # TODO vlan_pcp
        if not (wildcards & ofp.OFPFW_NW_SRC_ALL):
            testField("ipv4_src", 0xffffffff)
        if not (wildcards & ofp.OFPFW_NW_DST_ALL):
            testField("ipv4_dst", 0xffffffff)
        if not (wildcards & ofp.OFPFW_NW_TOS):
            testField("ip_dscp", 0x3f)
        if not (wildcards & ofp.OFPFW_NW_PROTO):
            testField("ip_proto", 0xff)
        if not (wildcards & ofp.OFPFW_TP_SRC):
            testField("tcp_src", 0xffff)
        if not (wildcards & ofp.OFPFW_TP_DST):
            testField("tcp_dst", 0xffff)

class DirectBadPacketBase(base_tests.SimpleDataPlane):
    """
    Base class for sending single packets with single flow table entries.
    Used to verify matching of unusual packets and parsing/matching of 
    corrupted packets.

    The idea is to generate packets that may either be totally malformed or 
    malformed just enough to trick the flow matcher into making mistakes.

    Generate a 'bad' packet
    Generate and install a matching flow
    Add action to direct the packet to an egress port
    Send the packet to ingress dataplane port
    Verify the packet is received at the egress port only
    """

    RESULT_MATCH = "MATCH"
    RESULT_NOMATCH = "NO MATCH"
    RESULT_ANY = "ANY MATCH"
    
    def runTest(self):
        pass
        # TODO:
        # - ICMP?
        # - VLAN?
        # - action

    def createMatch(self, **kwargs):
        match = ofp.ofp_match()
        match.wildcards = ofp.OFPFW_ALL
        fields = {
            'eth_dst': ofp.OFPFW_DL_DST,
            'eth_src': ofp.OFPFW_DL_SRC,
            'eth_type': ofp.OFPFW_DL_TYPE,
            'vlan_vid': ofp.OFPFW_DL_VLAN,
            'ipv4_src': ofp.OFPFW_NW_SRC_MASK,
            'ipv4_dst': ofp.OFPFW_NW_DST_MASK,
            'ip_dscp': ofp.OFPFW_NW_TOS,
            'ip_proto': ofp.OFPFW_NW_PROTO,
            'tcp_src': ofp.OFPFW_TP_SRC,
            'tcp_dst': ofp.OFPFW_TP_DST,
        }
        for key in kwargs:
            setattr(match, key, kwargs[key])
            match.wildcards &= ~fields[key]
        return match

    def testPktsAgainstFlow(self, pkts, acts, match):
        if type(acts) != list:
            acts = [acts]
        for info in pkts:
            title, pkt, expected_result = info
            self.testPktAgainstFlow(title, pkt, acts, match, expected_result)

    def testPktAgainstFlow(self, title, pkt, acts, match, expected_result):
        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")

        delete_all_flows(self.controller)

        ingress_port = of_ports[0]
        egress_port = of_ports[1]
        
        logging.info("Testing packet '%s', expect result %s" % 
                       (title, expected_result))
        logging.info("Ingress %s to egress %s" % 
                       (str(ingress_port), str(egress_port)))
        logging.info("Packet:")
        logging.info(inspect_packet(pkt))

        match.in_port = ingress_port

        request = ofp.message.flow_mod()
        request.match = match
        request.priority = 1

        request.buffer_id = 0xffffffff
        for act in acts:
            act.port = egress_port
            request.actions.append(act)

        logging.info("Inserting flow")
        self.controller.message_send(request)

        # This flow speeds up negative tests
        logging.info("Inserting catch-all flow")
        request2 = ofp.message.flow_mod()
        request2.match = self.createMatch()
        request2.match.wildcards &= ~ofp.OFPFW_IN_PORT
        request2.match.in_port = ingress_port

        request2.priority = 0
        act = ofp.action.output()
        act.port = ofp.OFPP_IN_PORT
        request2.actions.append(act)
        self.controller.message_send(request2)

        do_barrier(self.controller)

        pkt_str = str(pkt)
        if config["minsize"] > len(str(pkt)):
            pkt_str += '0' * (config["minsize"] - len(str(pkt)))

        logging.info("Sending packet to dp port " + 
                       str(ingress_port))
        self.dataplane.send(ingress_port, pkt_str)

        exp_pkt_arg = None
        exp_port = None
        if config["relax"]:
            exp_pkt_arg = pkt
            exp_port = egress_port

        if expected_result == self.RESULT_MATCH:
            timeout = -1 # default timeout
        else:
            timeout = 1 # short timeout for negative tests

        (rcv_port, rcv_pkt, pkt_time) = self.dataplane.poll(exp_pkt=exp_pkt_arg,
                                                            timeout=timeout)
        if rcv_port == ingress_port:
            logging.debug("Packet matched catch-all flow")
            rcv_pkt = None

        if expected_result == self.RESULT_MATCH:
            self.assertTrue(rcv_pkt is not None, 
                            "Did not receive packet, expected a match")
            logging.debug("Packet len " + str(len(rcv_pkt)) + " in on " + 
                          str(rcv_port))
            self.assertEqual(rcv_port, egress_port, "Unexpected receive port")
            str_pkt = str(pkt)
            str_rcv_pkt = str(rcv_pkt)
            str_rcv_pkt = str_rcv_pkt[0:len(str_pkt)]
            if str_pkt != str_rcv_pkt:
                logging.error("Response packet does not match send packet")
                logging.info("Response:")
                logging.info(inspect_packet(scapy.Ether(rcv_pkt)))
            self.assertEqual(str_pkt, str_rcv_pkt,
                             'Response packet does not match send packet')
        elif expected_result == self.RESULT_NOMATCH:
            self.assertTrue(rcv_pkt is None, "Received packet, expected drop")
        else:
            logging.debug("Match or drop accepted. Result = %s" %
                            ("match" if rcv_pkt is not None else "drop"))


class DirectBadIpTcpPacketsBase(DirectBadPacketBase):
    """
    Base class for TCP and UDP parsing/matching verification under corruptions
    """
    def runTest(self):
        pass

    def runTestWithProto(self, protoName = 'TCP'):
        eth_dst='00:01:02:03:04:05'
        eth_src='00:06:07:08:09:0a'
        ip_src='192.168.0.1'
        ip_dst='192.168.0.2'
        ip_tos=0
        tcp_sport=1234
        tcp_dport=80
        
        # Generate a proper packet for constructing a match
        tp = None
        if protoName == 'TCP':
            tp = scapy.TCP
            proto = 6
        elif protoName == 'UDP':
            tp = scapy.UDP
            proto = 17
        else:
            raise Exception("Passed in unknown proto name")

        match_pkt = scapy.Ether(dst=eth_dst, src=eth_src)/ \
            scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos)/ \
            tp(sport=tcp_sport, dport=tcp_dport)
        match = packet_to_flow_match(self, match_pkt)
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        
        def testPacket(title, pkt, result):
            act = ofp.action.output()
            pkts = [
                [title, pkt, result]
            ]
            self.testPktsAgainstFlow(pkts, act, match)
        
        # Try incomplete IP headers
        testPacket("Incomplete IP header (1 bytes)",
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                str(scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos, proto=proto))[0:1],
            self.RESULT_NOMATCH,
        )
        testPacket("Incomplete IP header (2 bytes)",
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                str(scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos, proto=proto))[0:2],
            self.RESULT_NOMATCH,
        )
        testPacket("Incomplete IP header (3 bytes)",
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                str(scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos, proto=proto))[0:3],
            self.RESULT_NOMATCH,
        )
        testPacket("Incomplete IP header (12 bytes)",
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                str(scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos, proto=proto))[0:12],
            self.RESULT_NOMATCH,
        )
        testPacket("Incomplete IP header (16 bytes)",
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                str(scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos, proto=proto))[0:16],
            self.RESULT_NOMATCH,
        )
        testPacket("Incomplete IP header (19 bytes)",
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                str(scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos, proto=proto))[0:19],
            self.RESULT_NOMATCH,
        )
            
        # Try variations where the TCP header is missing or incomplete. As we 
        # saw bugs before where buffers were reused and lengths weren't honored,
        # we initiatlize once with a non-matching full packet and once with a 
        # matching full packet.
        testPacket("Non-Matching TCP packet, warming buffer",
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos, proto=proto)/ \
                tp(sport=tcp_sport, dport=tcp_dport + 1),
            self.RESULT_NOMATCH,
        )
        testPacket("Missing TCP header, buffer warmed with non-match",
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos, proto=proto),
            self.RESULT_NOMATCH,
        )
        testPacket("Matching TCP packet, warming buffer",
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos, proto=proto)/ \
                tp(sport=tcp_sport, dport=tcp_dport),
            self.RESULT_MATCH,
        )
        testPacket("Missing TCP header, buffer warmed with match",
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos, proto=proto),
            self.RESULT_NOMATCH,
        )
        testPacket("Truncated TCP header: 2 bytes",
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos, proto=proto)/ \
                (str(tp(sport=tcp_sport, dport=tcp_dport))[0:2]),
            self.RESULT_NOMATCH,
        )
            
        # Play with IP header length values that put the start of TCP either
        # inside the generated TCP header or beyond. In some cases it may even
        # be beyond the packet boundary. Also play with IP options and more 
        # importantly IP total length corruptions.
        testPacket("TCP packet, corrupt ihl (0x6)",
            simple_tcp_packet(ip_ihl=6),
            self.RESULT_NOMATCH,
        )
        testPacket("TCP packet, corrupt ihl (0xf)",
            simple_tcp_packet(ip_ihl=0xf), # ihl = 15 * 4 = 60
            self.RESULT_NOMATCH,
        )
        testPacket("TCP packet, corrupt ihl and total length",
            simple_tcp_packet(ip_ihl=0xf, pktlen=56), # ihl = 15 * 4 = 60,
            self.RESULT_NOMATCH,
        )
        testPacket("Corrupt IPoption: First 4 bytes of matching TCP header",
            simple_tcp_packet(
                ip_options=scapy.IPOption('\x04\xd2\x00\x50'), 
                tcp_dport=2, tcp_sport=2
            ),
            self.RESULT_NOMATCH,
        )
        testPacket("Missing TCP header, corrupt ihl",
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos, ihl=0xf, proto=proto),
            self.RESULT_NOMATCH,
        )
        testPacket("Missing TCP header, corrupt total length",
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos, proto=proto, len= 100),
            self.RESULT_NOMATCH,
        )
        testPacket("Missing TCP header, corrupt ihl and total length",
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos, ihl=0xf, proto=proto, len=43),
            self.RESULT_NOMATCH,
        )
        testPacket("Incomplete IP header (12 bytes), corrupt ihl and total length",
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                str(scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos, proto=proto, ihl=10, len=43))[0:12],
            self.RESULT_NOMATCH,
        )
        testPacket("Incomplete IP header (16 bytes), corrupt ihl and total length",
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                str(scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos, proto=proto, ihl=10, len=43))[0:16],
            self.RESULT_NOMATCH,
        )
            
        # Try an incomplete TCP header that has enough bytes to carry source and
        # destination ports. As that is all we care about during matching, some
        # implementations may match and some may drop the packet
        testPacket("Incomplete TCP header: src/dst port present",
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos, proto=proto)/ \
                (str(tp(sport=tcp_sport, dport=tcp_dport))[0:4]),
            self.RESULT_ANY,
        )

        for i in range(1):
            for length in range(40 / 4): # IPv4 options are a maximum of 40 in length
                bytes = "".join([("%c" % random.randint(0, 255)) for x in range(length * 4)])
                eth = scapy.Ether(dst=eth_dst, src=eth_src)
                ip = scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos, ihl=5 + length, proto=proto)
                tcp = tp(sport=tcp_sport, dport=tcp_dport+1)
                pkt = eth / ip
                pkt = pkt / bytes
                pkt = pkt / str(tcp)
                testPacket("Random IP options len = %d - TP match must fail" % length * 4, 
                    pkt, 
                    self.RESULT_NOMATCH
                )

                eth = scapy.Ether(dst=eth_dst, src=eth_src)
                ip = scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos, ihl=5 + length, proto=proto)
                tcp = tp(sport=tcp_sport, dport=tcp_dport)
                pkt = eth / ip
                pkt = pkt / bytes
                pkt = pkt / str(tcp)

                testPacket("Random IP options len = %d - May match", 
                    pkt, 
                    self.RESULT_ANY
                )
        

class DirectBadIpTcpPackets(DirectBadIpTcpPacketsBase):
    """
    Verify IP/TCP parsing and matching. Focus on packet corruptions 
    """
    def runTest(self):
        self.runTestWithProto(protoName = 'TCP')

class DirectBadIpUdpPackets(DirectBadIpTcpPacketsBase):
    """
    Verify IP/UDP parsing and matching. Focus on packet corruptions 
    """
    def runTest(self):
        self.runTestWithProto(protoName = 'UDP')

class DirectBadLlcPackets(DirectBadPacketBase):
    """
    Verify LLC/SNAP parsing and matching. Focus on packet corruptions 
    """
    def runTest(self):
        eth_dst='00:01:02:03:04:05'
        eth_src='00:06:07:08:09:0a'
        ip_src='192.168.0.1'
        ip_dst='192.168.0.2'
        ip_tos=0
        tcp_sport=1234
        tcp_dport=80

        IS_SNAP_IP = 1
        IS_SNAP_IP_CORRUPT = 2
        IS_NOT_SNAP_IP = 3

        def testPacketTcpMatch(title, llc):
            match_pkt = scapy.Ether(dst=eth_dst, src=eth_src)/ \
                scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos)/ \
                scapy.TCP(sport=tcp_sport, dport=tcp_dport)
            match = packet_to_flow_match(self, match_pkt)
            self.assertTrue(match is not None, 
                            "Could not generate flow match from pkt")
            match.wildcards &= ~ofp.OFPFW_IN_PORT
            act = ofp.action.output()
            
            self.testPktsAgainstFlow(
                [[
                    "TCP match - LLC frame correct length - %s" % title,
                    scapy.Ether(dst=eth_dst, src=eth_src, type=len(llc)) / llc,
                    self.RESULT_ANY,
                ]],
                act, match
            )
    
            # Corrupt length field
            ethLen = random.randint(0, 1535)
            self.testPktsAgainstFlow(
                [[
                    "TCP match - LLC frame corrupted length - %s" % title,
                    scapy.Ether(dst=eth_dst, src=eth_src, type=ethLen) / llc,
                    self.RESULT_ANY,
                ]],
                act, match
            )

        def testPacketEthSrcDstMatch(title, llc):
            # Matching based on Ethernet source and destination
            match_pkt = scapy.Ether(dst=eth_dst, src=eth_src)
            match = packet_to_flow_match(self, match_pkt)
            self.assertTrue(match is not None, 
                            "Could not generate flow match from pkt")
            match.wildcards &= ~ofp.OFPFW_IN_PORT
            match.wildcards |= ofp.OFPFW_DL_TYPE
            self.testPktsAgainstFlow(
                [[
                    "Eth addr match - LLC frame correct length- %s" % title,
                    scapy.Ether(dst=eth_dst, src=eth_src, type=len(llc)) / llc,
                    self.RESULT_MATCH,
                ]],
                ofp.action.output(), match
            )
    
            # Corrupt length field
            ethLen = random.randint(0, 1535)
            self.testPktsAgainstFlow(
                [[
                    "Eth addr match - LLC frame corrupted length- %s" % title,
                    scapy.Ether(dst=eth_dst, src=eth_src, type=ethLen) / llc,
                    self.RESULT_ANY,
                ]],
                ofp.action.output(), match
            )
            
        def testPacketEthSrcDstTypeMatch(title, llc, is_snap_ip):
            # Matching based on Ethernet source, destination and type
            match_pkt = scapy.Ether(dst=eth_dst, src=eth_src, type=0x800)
            match = packet_to_flow_match(self, match_pkt)
            self.assertTrue(match is not None, 
                            "Could not generate flow match from pkt")
            match.wildcards &= ~ofp.OFPFW_IN_PORT
            if is_snap_ip == IS_SNAP_IP:
                is_match = self.RESULT_MATCH
            elif is_snap_ip == IS_SNAP_IP_CORRUPT:
                is_match = self.RESULT_ANY
            else:
                is_match = self.RESULT_NOMATCH
            self.testPktsAgainstFlow(
                [[
                    "Eth addr+type match - LLC frame correct length - %s" % title,
                    scapy.Ether(dst=eth_dst, src=eth_src, type=len(llc)) / llc,
                    is_match,
                ]],
                ofp.action.output(), match
            )
    
            # Corrupt length field
            ethLen = random.randint(0, 1535)
            self.testPktsAgainstFlow(
                [[
                    "Eth addr+type match - LLC frame corrupted length - %s" % title,
                    scapy.Ether(dst=eth_dst, src=eth_src, type=ethLen) / llc,
                    self.RESULT_ANY,
                ]],
                ofp.action.output(), match
            )

        def testPacket(title, llc, is_snap_ip):
            testPacketTcpMatch(title, llc)
            testPacketEthSrcDstMatch(title, llc)
            testPacketEthSrcDstTypeMatch(title, llc, is_snap_ip)

        testPacket("LLC - No SNAP - No Payload",
            scapy.LLC(dsap=0x33, ssap=0x44, ctrl=0x03),
            IS_NOT_SNAP_IP,
        )
        testPacket("LLC - No SNAP - Small Payload",
            scapy.LLC(dsap=0x33, ssap=0x44, ctrl=0x03) / ("S" * 10),
            IS_NOT_SNAP_IP,
        )
        testPacket("LLC - No SNAP - Max -1 Payload",
            scapy.LLC(dsap=0x33, ssap=0x44, ctrl=0x03) / ("S" * (1500 - 3 - 1)),
            IS_NOT_SNAP_IP,
        )
        testPacket("LLC - No SNAP - Max Payload",
            scapy.LLC(dsap=0x33, ssap=0x44, ctrl=0x03) / ("S" * (1500 - 3)),
            IS_NOT_SNAP_IP,
        )
        testPacket("LLC - SNAP - Small bogus payload",
            scapy.LLC(dsap=0xaa, ssap=0xaa, ctrl=0x03)/ \
                scapy.SNAP(OUI=0x000000, code=0x800) / ("S" * 10),
            IS_SNAP_IP_CORRUPT,
        )
        testPacket("LLC - SNAP - Max -1 bogus payload",
            scapy.LLC(dsap=0xaa, ssap=0xaa, ctrl=0x03)/ \
                scapy.SNAP(OUI=0x000000, code=0x3) / ("S" * (1500 - 3 - 5 - 1)),
            IS_NOT_SNAP_IP,
        )
        testPacket("LLC - SNAP - Max bogus payload",
            scapy.LLC(dsap=0xaa, ssap=0xaa, ctrl=0x03)/ \
                scapy.SNAP(OUI=0x000000, code=0x3) / ("S" * (1500 - 3 - 5)),
            IS_NOT_SNAP_IP,
        )
        testPacket("LLC - SNAP - IP - TCP",
            scapy.LLC(dsap=0xaa, ssap=0xaa, ctrl=0x03)/ \
                scapy.SNAP(OUI=0x000000, code=0x800)/ \
                scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos, proto=6)/ \
                scapy.TCP(sport=tcp_sport, dport=tcp_dport),
            IS_SNAP_IP,
        )
        

class DirectLlcPackets(DirectBadPacketBase):
    """
    Verify LLC/SNAP parsing (valid and corrupted packets) and matching
    """
    def runTest(self):
        eth_dst='00:01:02:03:04:05'
        eth_src='00:06:07:08:09:0a'
        ip_src='192.168.0.1'
        ip_dst='192.168.0.2'
        ip_tos=0
        tcp_sport=1234
        tcp_dport=80

        # Test ethertype in face of LLC/SNAP and OFP_DL_TYPE_NOT_ETH_TYPE
        IS_SNAP_NOT_IP = 1
        IS_SNAP_AND_IP = 2
        IS_NOT_SNAP = 3

        def testPacketEthTypeIP(title, llc, is_snap):
            match_pkt = scapy.Ether(dst=eth_dst, src=eth_src, type=0x800)
            match = packet_to_flow_match(self, match_pkt)
            self.assertTrue(match is not None, 
                            "Could not generate flow match from pkt")
            match.wildcards &= ~ofp.OFPFW_IN_PORT
            pkts = []
            if is_snap == IS_NOT_SNAP or is_snap == IS_SNAP_NOT_IP:
                result = self.RESULT_NOMATCH
            else:
                result = self.RESULT_MATCH
            pkts.append([
                "Ether type 0x800 match - %s" % title,
                scapy.Ether(dst=eth_dst, src=eth_src, type=len(llc)) / llc,
                result,
            ])
            act = ofp.action.output()
            self.testPktsAgainstFlow(pkts, act, match)
    
        def testPacketEthTypeNotEth(title, llc, is_snap):
            match_pkt = scapy.Ether(dst = eth_dst, src = eth_src, 
                                    type = ofp.OFP_DL_TYPE_NOT_ETH_TYPE)
            match = packet_to_flow_match(self, match_pkt)
            self.assertTrue(match is not None, 
                            "Could not generate flow match from pkt")
            match.wildcards &= ~ofp.OFPFW_IN_PORT
            pkts = []
            if is_snap == IS_NOT_SNAP:
                result = self.RESULT_MATCH
            else:
                result = self.RESULT_NOMATCH
            pkts.append([
                "Ether type OFP_DL_TYPE_NOT_ETH_TYPE match - %s" % title,
                scapy.Ether(dst=eth_dst, src=eth_src, type=len(llc)) / llc,
                result,
            ])
            act = ofp.action.output()
            self.testPktsAgainstFlow(pkts, act, match)
    
        def testPacket(title, llc, is_snap):
            testPacketEthTypeIP(title, llc, is_snap)
            testPacketEthTypeNotEth(title, llc, is_snap)
        
        testPacket("LLC - No SNAP - No Payload",
            scapy.LLC(dsap=0x33, ssap=0x44, ctrl=0x03),
            IS_NOT_SNAP,
        )
        testPacket("LLC (with information field) - No SNAP - No Payload",
            scapy.LLC(dsap=0x33, ssap=0x44, ctrl=0x12) / "S",
            IS_NOT_SNAP,
        )
        testPacket("LLC - No SNAP - Small Payload",
            scapy.LLC(dsap=0x33, ssap=0x44, ctrl=0x03) / ("S" * 10),
            IS_NOT_SNAP,
        )
        testPacket("LLC - No SNAP - Max -1 Payload",
            scapy.LLC(dsap=0x33, ssap=0x44, ctrl=0x03) / ("S" * (1500 - 3 - 1)),
            IS_NOT_SNAP,
        )
        testPacket("LLC - No SNAP - Max Payload",
            scapy.LLC(dsap=0x33, ssap=0x44, ctrl=0x03) / ("S" * (1500 - 3)),
            IS_NOT_SNAP,
        )
        testPacket("LLC - SNAP - Non-default OUI",
            scapy.LLC(dsap=0xaa, ssap=0xaa, ctrl=0x03)/ \
                scapy.SNAP(OUI=0x000001, code=0x800) / ("S" * 10),
            IS_NOT_SNAP,
        )
        testPacket("LLC - SNAP - Default OUI",
            scapy.LLC(dsap=0xaa, ssap=0xaa, ctrl=0x03)/ \
                scapy.SNAP(OUI=0x000000, code=0x800) / ("S" * 10),
            IS_SNAP_AND_IP,
        )
        testPacket("LLC - SNAP - Max -1 bogus payload",
            scapy.LLC(dsap=0xaa, ssap=0xaa, ctrl=0x03)/ \
                scapy.SNAP(OUI=0x000000, code=0x3) / ("S" * (1500 - 3 - 5 - 1)),
            IS_SNAP_NOT_IP,
        )
        testPacket("LLC - SNAP - Max bogus payload",
            scapy.LLC(dsap=0xaa, ssap=0xaa, ctrl=0x03)/ \
                scapy.SNAP(OUI=0x000000, code=0x3) / ("S" * (1500 - 3 - 5)),
            IS_SNAP_NOT_IP,
        )
        testPacket("LLC - SNAP - IP - TCP",
            scapy.LLC(dsap=0xaa, ssap=0xaa, ctrl=0x03)/ \
                scapy.SNAP(OUI=0x000000, code=0x800)/ \
                scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos, proto=6)/ \
                scapy.TCP(sport=tcp_sport, dport=tcp_dport),
            IS_SNAP_AND_IP,
        )


class DirectArpPackets(DirectBadPacketBase):
    """
    Verify ARP parsing (valid and corrupted packets) and ARP matching
    """
    def runTest(self):
        self.testArpHandling()

    def testArpHandling(self):
        eth_dst='00:01:02:03:04:05'
        eth_src='00:06:07:08:09:0a'
        ip_src='192.168.0.1'
        ip_dst='192.168.0.2'
        ip_src2='192.168.1.1'
        ip_dst2='192.168.1.2'
        ip_tos=0
        tcp_sport=1234
        tcp_dport=80

        def testPacket(title, arp_match, arp_pkt, result):
            pkts = []
    
            match_pkt = scapy.Ether(dst=eth_dst, src=eth_src) / arp_match
            match = packet_to_flow_match(self, match_pkt)
            self.assertTrue(match is not None, 
                            "Could not generate flow match from pkt")
            match.wildcards &= ~ofp.OFPFW_IN_PORT
            
            pkts.append([
                title,
                scapy.Ether(dst=eth_dst, src=eth_src) / arp_pkt,
                result,
            ])
    
            act = ofp.action.output()
            self.testPktsAgainstFlow(pkts, act, match)
            
        testPacket("Basic ARP",
            scapy.ARP(psrc=ip_src, pdst=ip_dst, op = 1),
            scapy.ARP(hwdst = '00:00:00:00:00:00', hwsrc = eth_src,
                      psrc = ip_src, pdst = ip_dst, hwlen = 6, plen = 4,
                      ptype = 0x800, hwtype = 1, op = 1),
            self.RESULT_MATCH
        )
        # More stuff:
        # - Non matches on any property
        # - Corrupted hwlen and plen
        # - Other hwtype, ptype
        # - Truncated ARP pkt

    
class DirectVlanPackets(DirectBadPacketBase):
    """
    Verify VLAN parsing (valid and corrupted packets) and ARP matching
    """
    def runTest(self):
        eth_dst='00:01:02:03:04:05'
        eth_src='00:06:07:08:09:0a'
        ip_src='192.168.0.1'
        ip_dst='192.168.0.2'
        ip_src2='192.168.1.1'
        ip_dst2='192.168.1.2'
        ip_tos=0
        tcp_sport=1234
        tcp_dport=80

        def testPacket(title, match, pkt, result):
            pkts = []
    
            self.assertTrue(match is not None, 
                            "Could not generate flow match from pkt")
            match.wildcards &= ~ofp.OFPFW_IN_PORT
            
            pkts.append([
                "%s" % title,
                pkt,
                result,
            ])
    
            act = ofp.action.output()
            self.testPktsAgainstFlow(pkts, act, match)

        testPacket("Basic MAC matching - IPv4 payload",
            self.createMatch(eth_dst=parse_mac(eth_dst), eth_src=parse_mac(eth_src)),
            scapy.Ether(dst=eth_dst, src=eth_src, type=0x800) / scapy.IP(),
            self.RESULT_MATCH
        )
        testPacket("Basic MAC matching - VMware beacon - no payload",
            self.createMatch(eth_dst=parse_mac(eth_dst), eth_src=parse_mac(eth_src)),
            scapy.Ether(dst=eth_dst, src=eth_src, type=0x8922),
            self.RESULT_MATCH
        )
        testPacket("Basic MAC matching - VMware beacon - with payload",
            self.createMatch(eth_dst=parse_mac(eth_dst), eth_src=parse_mac(eth_src)),
            scapy.Ether(dst=eth_dst, src=eth_src, type=0x8922)/ ("X" * 1),
            self.RESULT_MATCH
        )
        testPacket("Basic MAC matching - IPv6 payload",
            self.createMatch(eth_dst=parse_mac(eth_dst), eth_src=parse_mac(eth_src)),
            scapy.Ether(dst=eth_dst, src=eth_src) / scapy.IPv6(),
            self.RESULT_MATCH
        )
        testPacket("Basic MAC matching with VLAN tag present",
            self.createMatch(eth_dst=parse_mac(eth_dst), eth_src=parse_mac(eth_src)),
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                scapy.Dot1Q(prio=5, vlan=1000)/ \
                scapy.IP(),
            self.RESULT_MATCH
        )
        testPacket("Basic MAC matching with VLAN tag present",
            self.createMatch(eth_dst=parse_mac(eth_dst), eth_src=parse_mac(eth_src),
                             eth_type=0x800),
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                scapy.Dot1Q(prio=5, vlan=1000)/ \
                scapy.IP(),
            self.RESULT_MATCH
        )
        testPacket("Ether matching with VLAN tag present - No type match",
            self.createMatch(eth_dst=parse_mac(eth_dst), eth_src=parse_mac(eth_src),
                             eth_type=0x801),
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                scapy.Dot1Q(prio=5, vlan=1000)/ \
                scapy.IP(),
            self.RESULT_NOMATCH
        )
        testPacket("Ether matching with VLAN tag present - No type match 0x8100",
            self.createMatch(eth_dst=parse_mac(eth_dst), eth_src=parse_mac(eth_src),
                             eth_type=0x8100),
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                scapy.Dot1Q(prio=5, vlan=1000)/ \
                scapy.IP(),
            self.RESULT_NOMATCH
        )
        testPacket("IP matching - VLAN tag",
            self.createMatch(eth_dst=parse_mac(eth_dst), eth_src=parse_mac(eth_src),
                             eth_type=0x0800,
                             ipv4_src=parse_ip(ip_src), ipv4_dst=parse_ip(ip_dst)),
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                scapy.Dot1Q(prio=5, vlan=1000)/ \
                scapy.IP(src=ip_src, dst=ip_dst),
            self.RESULT_MATCH
        )
        # XXX:
        # - Matching on VLAN ID and Prio
        # - Actions

@nonstandard
class DirectVlanPacketsDoubleTagged(DirectVlanPackets):
    """
    VLAN parsing for double tagged packets.  Spec is ambiguous about
    the treatment of these cases, so broken out to be non-standard
    """
    def runTest(self):
        eth_dst='00:01:02:03:04:05'
        eth_src='00:06:07:08:09:0a'
        ip_src='192.168.0.1'
        ip_dst='192.168.0.2'
        ip_src2='192.168.1.1'
        ip_dst2='192.168.1.2'
        ip_tos=0
        tcp_sport=1234
        tcp_dport=80

        def testPacket(title, match, pkt, result):
            pkts = []
    
            self.assertTrue(match is not None, 
                            "Could not generate flow match from pkt")
            match.wildcards &= ~ofp.OFPFW_IN_PORT
            
            pkts.append([
                "%s" % title,
                pkt,
                result,
            ])
    
            act = ofp.action.output()
            self.testPktsAgainstFlow(pkts, act, match)
        testPacket("Ether matching with double VLAN tag - Wrong type match",
            self.createMatch(eth_dst=parse_mac(eth_dst), eth_src=parse_mac(eth_src),
                             eth_type=0x800),
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                scapy.Dot1Q(prio=5, vlan=1000)/ \
                scapy.Dot1Q(prio=3, vlan=1005)/ \
                scapy.IP(),
            self.RESULT_NOMATCH
        )
        testPacket("Ether matching with double VLAN tag - Type match",
            self.createMatch(eth_dst=parse_mac(eth_dst), eth_src=parse_mac(eth_src),
                             eth_type=0x8100),
            scapy.Ether(dst=eth_dst, src=eth_src)/ \
                scapy.Dot1Q(prio=5, vlan=1000)/ \
                scapy.Dot1Q(prio=3, vlan=1005)/ \
                scapy.IP(),
            self.RESULT_MATCH
        )

    

if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test_spec=basic"
