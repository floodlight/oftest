"""
OpenFlow Test Framework

DataPlane and DataPlanePort classes

Provide the interface to the control the set of ports being used
to stimulate the switch under test.

See the class dataplaneport for more details.  This class wraps
a set of those objects allowing general calls and parsing 
configuration.

@todo Add "filters" for matching packets.  Actions supported
for filters should include a callback or a counter
"""

import sys
import os
import socket
import time
import promisc
from threading import Thread
from threading import Lock

#@todo Move these identifiers into config
ETH_P_ALL = 0x03
RCV_TIMEOUT = 10000
RCV_SIZE = 4096

class DataPlanePort(Thread):
    """
    Class defining a port monitoring object.

    Control a dataplane port connected to the switch under test.
    Creates a promiscuous socket on a physical interface.
    Queues the packets received on that interface with time stamps.
    Inherits from Thread class as meant to run in background.  Also
    supports polling.
    Use accessors to dequeue packets for proper synchronization.
    """

    def __init__(self, interface_name, max_pkts=1024):
        """
        Set up a port monitor object
        @param interface_name The name of the physical interface like eth1
        @param max_pkts Maximum number of pkts to keep in queue
        """
        Thread.__init__(self)
        self.interface_name = interface_name
        self.max_pkts = max_pkts
        self.packets_pending = 0
        self.packets_total = 0
        self.packets = []
        self.packet_times = []
        self.sync = Lock()
        self.socket = self.interface_open(interface_name)
        print "Openned port monitor socket " + interface_name

    def interface_open(self, interface_name):
        """
        Open a socket in a promiscuous mode for a data connection.
        @param interface_name port name as a string such as 'eth1'
        @retval s socket
        """
        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, 
                          socket.htons(ETH_P_ALL))
        s.bind((interface_name, 0))
        promisc.set_promisc(s, interface_name)
        s.settimeout(RCV_TIMEOUT)
        return s

    def kill(self):
        """
        Terminate the running thread
        """
        self.running = False
        self.socket.close()
        print "Port monitor for " + self.interface_name + " exiting"

    def run(self):
        """
        Activity function for class
        """
        self.running = True
        while self.running:
            try:
                rcvmsg = self.socket.recv(RCV_SIZE)
                rcvtime = time.clock()

                self.sync.acquire()
                self.packets.append(rcvmsg)
                self.packet_times.append(rcvtime)
                self.packets_pending += 1
                self.packets_total += 1
                self.sync.release()

            except socket.timeout:
                print "Socket timeout for " + self.interface_name
            except socket.error:
                print "Socket closed for " + self.interface_name
                if self.running:
                    self.kill()
                break

    def dequeue(self):
        """
        Get the oldest packet in the queue
        """
        self.sync.acquire()
        pkt = self.packets.pop(0)
        pkt_time = self.packet_times.pop(0)
        self.packets_pending -= 1
        self.sync.release()
        return pkt, pkt_time

    def timestamp_head(self):
        """
        Return the timestamp of the head of queue or None if empty
        """
        if self.packets_pending:
            return self.packet_times[0]
        return None

    def flush(self):
        """
        Clear the packet queue
        """
        self.sync.acquire()
        self.packets = []
        self.packet_times = []
        self.packets_pending = 0
        self.sync.release()


    def send(self, packet):
        """
        Send a packet to the dataplane port
        @param packet The packet data to send to the port
        @retval The number of bytes sent
        """
        return self.socket.send(packet)


    def register(self, handler):
        """
        Register a callback function to receive packets from this
        port.  The callback will be passed the packet, the 
        interface name and the port number (if set) on which the 
        packet was received.

        To be implemented
        """
        pass


class DataPlane:
    """
    Class defining access primitives to the data plane
    Controls a list of DataPlanePort objects
    """
    def __init__(self):
        self.port_list = {}

    def port_add(self, interface_name, port_number):
        """
        Add a port to the dataplane
        TBD:  Max packets for queue?
        @param interface_name The name of the physical interface like eth1
        @param port_number The port number used to refer to the port
        """
        
        self.port_list[port_number] = DataPlanePort(interface_name)
        self.port_list[port_number].start()

    def send(self, port_number, packet):
        """
        Send a packet to the given port
        @param port_number The port to send the data to
        @param packet Raw packet data to send to port
        """
        bytes = self.port_list[port_number].send(packet)
        if bytes != len(packet):
            print "Unhandled send error, length mismatch %d != %d" % \
                (bytes, len(packet))
        return bytes

    def flood(self, packet):
        """
        Send a packet to all ports
        @param packet Raw packet data to send to port
        """
        for port_number in self.port_list.keys():
            bytes = self.port_list[port_number].send(packet)
            if bytes != len(packet):
                print "Unhandled send error" + \
                    ", port %d, length mismatch %d != %d" % \
                    (port_number, bytes, len(packet))

    def packet_get(self, port_number=None):
        """
        Get a packet from the data plane
        If port_number is given, get the packet from that port.
        Otherwise, find the port with the oldest packet and return
        that packet.
        @param port_number If set, get packet from this port
        @retval The triple port_number, packet, pkt_time where packet 
        is received from port_number at time pkt_time.  
        """

        if port_number:
            if self.port_list[port_number].packets_pending != 0:
                pkt, time = self.port_list[port_number].dequeue()
                return port_number, pkt, time
            else:
                return None, None, None

        # Find port with oldest packet
        min_time = 0
        min_port = -1
        for port_number in self.port_list.keys():
            ptime = self.port_list[port_number].timestamp_head()
            if ptime:
                if (min_port == -1) or (ptime < min_time):
                    min_time = ptime 
                    min_port = port_number

        if min_port == -1:
            return None, None, None

        pkt, time = self.port_list[min_port].dequeue()
        return min_port, pkt, time

    def kill(self):
        for port_number in self.port_list.keys():
            self.port_list[port_number].kill()

        print "DataPlane shutdown"
