""" 
Test cases to verify a black box L3 router, e.g. ORC, FBOSS, etc.

Simple dataplane things like 
* "can you ping the interfaces"
* "does the router arp correctly for end points"
* "does the router correctly change MACs and dec TTL"


"""

import copy
import logging
import time
import unittest
import random
import pdb

import scapy.all as scapy

import ofp
from oftest import config
import oftest.controller as controller
import oftest.base_tests as base_tests
import oftest.testutils as testutils



class BasicL3Test(base_tests.DataPlaneOnly):
    """
        Bottom of inheritance stack
    """
    
    # port # --> L3 interface mapping
    Interfaces = {
         1 : "172.31.1.1",
         2 : "172.31.2.1",
         3 : "172.31.3.1",
         4 : "172.31.4.1",
         5 : "172.31.5.1",
         6 : "172.31.6.1",
    }


    def pkt_smart_cmp(self, expected=None, recv=None, ttl=True):
        """
        @param expected  an Ether() object from scapy
        @param recv  an Ether() object from scapy
        @return boolean true iff the relevant fields of 
            the packet match, e.g., ignoring IP.ID
            IP.chksum, IP.ttl and if there are weird trailers
            NOTE: ignoring IP.ttl seems weird, but routers are 
                non-standard for whether they decrement ttl for
                ICMP echo packets to the ingress interface
            (including checksum) match between the two packets
        """
        if expected is None or recv is None:
            self.fail("Error: pkt_cmp_no_id() called with None parameters")
        p1 = scapy.Ether(str(expected))     # make duplicate copies of pkts
        p2 = scapy.Ether(str(recv))
        if p1.type != p2.type:
            return False    # not same ethertype
        if p1.src != p2.src:
            return False
        if p1.dst != p2.dst:
            return False
        #pdb.set_trace()
        if p1.type == 0x0800:   # if IP, remove ID, chksum
            ip1 = p1.payload
            ip2 = p2.payload
            del ip1.id
            del ip2.id
            del ip1.chksum
            del ip2.chksum
            if not ttl:
                del ip1.ttl
                del ip2.ttl
        return str(p1)[:ip1.len] == str(p2)[:ip2.len]


    def same_slash24_subnet(self, ip):
        """
        @param ip is a string of the form 'w.x.y.z', e.g. "192.168.1.1"
        @return the ip 'w.x.y.z+1' , e.g., "192.168.1.2"
        """
        quad = ip.split('.')
        return "%s.%s.%s.%d" % ( quad[0], quad[1], quad[2], int(quad[3])+1)

    def arpForMac(self,
                src_mac = None,
                src_ip = None,
                dst_ip = None, 
                port = None,
                maxtimeout=3):
        """
            Send out ARP requests for the given dst_ip
        """
        if src_mac == None or src_ip == None or \
                dst_ip == None or port == None:
            raise "Missing args for arpForMac()"
        arp = testutils.simple_arp_packet(
                                eth_src = src_mac,
                                hw_snd = src_mac,
                                ip_snd = src_ip, 
                                ip_tgt = dst_ip)

        logging.info("ARP request packet for %s out port %d " % 
                    ( dst_ip, port))
        logging.debug("Data: " + str(arp).encode('hex'))
        self.dataplane.send(port, str(arp))
        arp_found = False
        start_time = time.time()
        while not arp_found:
            timeout = (start_time + maxtimeout) - time.time()  # timeout after 3ish seconds total
            if timeout <= 0:
                logging.error("Timeout on ARP reply for port %d" % port)
                self.fail("Timeout on ARP for port %d" % port)
            (rcv_port, pkt, t)  = self.dataplane.poll(port_number = port, timeout = timeout)
            if pkt is not None:       # if is none, then we will loop and immediately timeout
                parsed_pkt = scapy.Ether(pkt)
                if (parsed_pkt is not None and 
                        type(parsed_pkt.payload) == scapy.ARP and
                        parsed_pkt.payload.op ==  2):        # 2 == reply
                    arp_found = True
                    dst_mac = parsed_pkt.payload.hwsrc
                    logging.info("Learned via ARP: MAC %s neighbor to port %d" %
                            ( dst_mac, port))
                    return dst_mac
    def getPrunedPorts(self):
        all_ports = config["port_map"].keys()
        all_ports.sort()
        ports = []
        for port in all_ports : 
            if port not in self.Interfaces:
                logging.info("Skipping port %d -- not IP interface defined" % port)
            else:
                ports.append(port)
        return ports

class PingEgressInterfacesL3(BasicL3Test):
    """ For each interface i
            verify we can ping each interface j"""
    def runTest(self):
        ports = self.getPrunedPorts()
        if len(ports) < 2 :
            self.fail("Need at least two ports to run this test")
        for src_port in ports:
            for dst_port in ports:
                if src_port == dst_port:
                    continue
            gateway_ip = self.Interfaces[src_port]
            dst_ip = self.Interfaces[dst_port]
            src_ip = self.same_slash24_subnet(self.Interfaces[src_port])
            src_mac = "00:11:22:33:44:%2d" % src_port
            # first arp for the gateway interface
            gateway_mac = self.arpForMac(
                            src_mac=src_mac,
                            src_ip=src_ip,
                            dst_ip=gateway_ip,
                            port=src_port)
            ping = testutils.simple_icmp_packet(        # request
                                    ip_dst = dst_ip,  
                                    ip_src = src_ip,
                                    eth_dst = gateway_mac,
                                    eth_src = src_mac
                                    )
            pong = testutils.simple_icmp_packet(        # reply
                                    ip_dst = src_ip,   
                                    ip_src = dst_ip,
                                    eth_dst = src_mac,
                                    eth_src = gateway_mac,
                                    ip_ttl = 64,
                                    icmp_type = 0,       # type = echo reply
                                    icmp_code = 0        # echo reply
                                    )
            logging.info("Sending ping to %s out port %d" % (dst_ip, src_port))
            logging.debug("Data: " + str(ping).encode('hex'))
            logging.debug("Expecting: " + str(ping).encode('hex'))
            #scapy.hexdump(pong)
            self.dataplane.send(src_port, str(ping))
            start_time = time.time()
            pong_found = False
            while not pong_found:
                timeout = (start_time + 3) - time.time()
                if timeout <= 0:
                    logging.error("Timeout on PING reply from port %d to port %d" % (src_port,dst_port))
                    self.fail("Timeout on PING from port %d to port %d" % (src_port, dst_port))
                (rcv_port, rcv_pkt, t) = self.dataplane.poll(port_number = src_port, timeout=timeout)
                if rcv_pkt is not None:
                    pong_found = self.pkt_smart_cmp(expected=pong, recv=scapy.Ether(rcv_pkt))

class PingAllHosts(BasicL3Test):
    """ For each interface i
            for each interface j
        fake a host A off of interface i
        fake a host B off of interface j
            send a ping from A to B
            verify that B receives the ping
            don't reply
    """
    def runTest(self):
        ports = self.getPrunedPorts()
        if len(ports) < 2 :
            self.fail("Need at least two ports to run this test")
        for src_port in ports:
            for dst_port in ports:
                if src_port == dst_port:
                    continue
            ingress_gateway_ip = self.Interfaces[src_port]
            egress_gateway_ip = self.Interfaces[dst_port]
            dst_ip = self.same_slash24_subnet(self.Interfaces[dst_port])
            src_ip = self.same_slash24_subnet(self.Interfaces[src_port])
            src_mac = "00:11:22:33:44:%2d" % src_port
            dst_mac = "00:11:22:33:44:%2d" % dst_port
            # first arp for the gateway interface
            ingress_gateway_mac = self.arpForMac(
                            src_mac=src_mac,
                            src_ip=src_ip,
                            dst_ip=ingress_gateway_ip,
                            port=src_port)
            egress_gateway_mac = self.arpForMac(
                            src_mac=dst_mac,
                            src_ip=dst_ip,
                            dst_ip=egress_gateway_ip,
                            port=dst_port)
            ping = testutils.simple_icmp_packet(        # request
                                    ip_dst = dst_ip,  
                                    ip_src = src_ip,
                                    eth_dst = ingress_gateway_mac,
                                    eth_src = src_mac
                                    )
            recv_ping = testutils.simple_icmp_packet(        # reply
                                    ip_dst = dst_ip,   
                                    ip_src = src_ip,
                                    eth_dst = dst_mac,
                                    eth_src = egress_gateway_mac,
                                    ip_ttl = 63
                                    )
            logging.info("Sending ping to %s out port %d" % (dst_ip, src_port))
            logging.debug("Data: " + str(ping).encode('hex'))
            logging.debug("Expecting: " + str(ping).encode('hex'))
            #scapy.hexdump(pong)
            self.dataplane.send(src_port, str(ping))
            start_time = time.time()
            pong_found = False
            while not pong_found:
                timeout = (start_time + 3) - time.time()
                if timeout <= 0:
                    logging.error("Timeout on PING reply from port %d to port %d" % (src_port,dst_port))
                    self.fail("Timeout on PING from port %d to port %d" % (src_port, dst_port))
                (rcv_port, rcv_pkt, t) = self.dataplane.poll(port_number = dst_port, timeout=timeout)
                if rcv_pkt is not None:
                    pong_found = self.pkt_smart_cmp(expected=recv_ping, recv=scapy.Ether(rcv_pkt))
                
        

class PingIngressInterfacesL3(BasicL3Test):
    """ For each interface, try to ping it """
    def runTest(self):
        for port in self.getPrunedPorts() : 
            dst_ip = self.Interfaces[port]
            src_ip = self.same_slash24_subnet(dst_ip)
            src_mac = "00:11:22:33:44:%2d" % port
            # first arp for the interface
            dst_mac = self.arpForMac(
                            src_mac=src_mac,
                            src_ip=src_ip,
                            dst_ip=dst_ip,
                            port=port)
            ping = testutils.simple_icmp_packet(        # request
                                    ip_dst = dst_ip,  
                                    ip_src = src_ip,
                                    eth_dst = dst_mac,
                                    eth_src = src_mac
                                    )
            pong = testutils.simple_icmp_packet(        # reply
                                    ip_dst = src_ip,   
                                    ip_src = dst_ip,
                                    eth_dst = src_mac,
                                    eth_src = dst_mac,
                                    ip_ttl = 64,
                                    icmp_type = 0,       # type = echo reply
                                    icmp_code = 0        # echo reply
                                    )
            logging.info("Sending ping to %s out port %d" % (dst_ip, port))
            logging.debug("Data: " + str(ping).encode('hex'))
            logging.debug("Expecting: " + str(ping).encode('hex'))
            #scapy.hexdump(pong)
            self.dataplane.send(port, str(ping))
            start_time = time.time()
            pong_found = False
            while not pong_found:
                timeout = (start_time + 3) - time.time()
                if timeout <= 0:
                    logging.error("Timeout on PING reply for port %d" % port)
                    self.fail("Timeout on PING for port %d" % port)
                (rcv_port, rcv_pkt, t) = self.dataplane.poll(port_number = port, timeout=timeout)
                if rcv_pkt is not None:
                    pong_found = self.pkt_smart_cmp(expected=pong, recv=scapy.Ether(rcv_pkt))

