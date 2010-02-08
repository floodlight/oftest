"""
OpenFlow Test Framework

Dataplane Port class

Control a dataplane port connected to the switch under test.

Class inherits from thread so as to run in background allowing
asynchronous callbacks (if needed, not required).  Also supports
polling.

The port object thread maintains a queue.  Incoming packets that
are not handled by a callback function are placed in this queue for 
poll calls.  

"""

import sys
sys.path.append("../packet")  # Needed?
import os
import socket
import time
import promisc
from threading import Thread
from threading import Lock

ETH_P_ALL = 0x03
RCV_TIMEOUT = 10000
RCV_SIZE = 4096

class DataPlanePort(Thread):
    """
    Class defining a port monitoring object.
    Creates a promiscuous socket on a physical interface
    Queues the packets received on that interface with time stamps
    Inherits from Thread class as meant to run in background
    Use accessors to dequeue packets for proper synchronization
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

