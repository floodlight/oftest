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
import netutils
from threading import Thread
from threading import Lock
from oft_config import *
import select

#@todo Move these identifiers into config
ETH_P_ALL = 0x03
RCV_TIMEOUT = 10000
RCV_SIZE = 4096

# class packet_queue:
#     """
#     Class defining a packet queue across multiple ports

#     Items in the queue are stored as a triple (port number, pkt, pkt in time)
#     """

#     def __init__(self, max_pkts=1024):
#         self.sync = Lock()
#         self.debug_level = debug_level_default
#         self.packets = []
#         self.max_pkts = max_pkts
#         self.packets_total = 0
#         self.packets_discarded = 0

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
        self.debug_level = debug_level_default
        self.max_pkts = max_pkts
        self.packets_total = 0
        self.packets = []
        self.packets_discarded = 0
        self.sync = Lock()
        self.socket = self.interface_open(interface_name)
        self.dbg(DEBUG_INFO, "Openned port monitor socket")

    def dbg(self, level, string):
        debug_log("DPLANE", self.debug_level, level, 
                  self.interface_name + ": " + string)

    def interface_open(self, interface_name):
        """
        Open a socket in a promiscuous mode for a data connection.
        @param interface_name port name as a string such as 'eth1'
        @retval s socket
        """
        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, 
                          socket.htons(ETH_P_ALL))
        s.bind((interface_name, 0))
        netutils.set_promisc(s, interface_name)
        s.settimeout(RCV_TIMEOUT)
        return s

    def run(self):
        """
        Activity function for class
        """
        self.running = True
        self.socs = [self.socket]
        error_warned = False # Have we warned about error?
        while self.running:
            try:
                sel_in, sel_out, sel_err = \
                    select.select(self.socs, [], [], 1)
            except:
                print sys.exc_info()
                self.dbg(DEBUG_ERROR, "Select error, exiting")
                sys.exit(1)

            #if not sel_err is None:
            #    self.dbg(DEBUG_VERBOSE, "Socket error from select set")

            if not self.running:
                break

            if sel_in is None:
                continue

            try:
                rcvmsg = self.socket.recv(RCV_SIZE)
            except socket.error:
                if not error_warned:
                    self.dbg(DEBUG_INFO, "Socket error on recv")
                    error_warned = True
                continue

            if len(rcvmsg) == 0:
                self.dbg(DEBUG_INFO, "Zero len pkt rcvd")
                self.kill()
                break

            rcvtime = time.clock()
            self.dbg(DEBUG_VERBOSE, "Pkt len " + str(len(rcvmsg)) + 
                     " in at " + str(rcvtime))

            self.sync.acquire()
            if len(self.packets) >= self.max_pkts:
                self.packets.pop(0)
                self.packets_discarded += 1
            self.packets.append((rcvmsg, rcvtime))
            self.packets_total += 1
            self.sync.release()

        self.dbg(DEBUG_INFO, "Thread exit ")

    def kill(self):
        """
        Terminate the running thread
        """
        self.running = False
        try:
            self.socket.close()
        except:
            self.dbg(DEBUG_INFO, "Ignoring dataplane soc shutdown error")
        self.dbg(DEBUG_INFO, 
                 "Port monitor exiting")

    def dequeue(self):
        """
        Get the oldest packet in the queue
        """
        self.sync.acquire()
        pkt, pkt_time = self.packets.pop(0)
        self.sync.release()
        return pkt, pkt_time

    def timestamp_head(self):
        """
        Return the timestamp of the head of queue or None if empty
        """
        rv = None
        self.sync.acquire()
        if len(self.packets) > 0:
            rv = self.packets[0][1]
        self.sync.release()
        return rv

    def flush(self):
        """
        Clear the packet queue
        """
        self.sync.acquire()
        self.packets_discarded += len(self.packets)
        self.packets = []
        self.packet_times = []
        self.sync.release()


    def send(self, packet):
        """
        Send a packet to the dataplane port
        @param packet The packet data to send to the port
        @retval The number of bytes sent
        """
        self.dbg(DEBUG_VERBOSE,
                 "port sending " + str(len(packet)) + " bytes")
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

    def show(self, prefix=''):
        print prefix + "Name:          " + self.interface_name
        print prefix + "Pkts pending:  " + str(len(self.packets))
        print prefix + "Pkts total:    " + str(self.packets_total)
        print prefix + "socket:        " + str(self.socket)
        

class DataPlane:
    """
    Class defining access primitives to the data plane
    Controls a list of DataPlanePort objects
    """
    def __init__(self):
        self.port_list = {}
        self.debug_level = debug_level_default

    def dbg(self, level, string):
        debug_log("DPORT", self.debug_level, level, string)

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
        self.dbg(DEBUG_VERBOSE,
                 "Sending %d bytes to port %d" % (len(packet), port_number))
        bytes = self.port_list[port_number].send(packet)
        if bytes != len(packet):
            self.dbg(DEBUG_ERROR,"Unhandled send error, " + 
                     "length mismatch %d != %d" %
                     (bytes, len(packet)))
        return bytes

    def flood(self, packet):
        """
        Send a packet to all ports
        @param packet Raw packet data to send to port
        """
        for port_number in self.port_list.keys():
            bytes = self.port_list[port_number].send(packet)
            if bytes != len(packet):
                self.dbg(DEBUG_ERROR, "Unhandled send error" +
                         ", port %d, length mismatch %d != %d" %
                         (port_number, bytes, len(packet)))

    def packet_get(self, port_number=None):
        """
        Get a packet from the data plane

        If port_number is given, get the oldest packet from that port.
        Otherwise, find the port with the oldest packet and return
        that packet.
        @param port_number If set, get packet from this port
        @retval The triple port_number, packet, pkt_time where packet 
        is received from port_number at time pkt_time.  
        """

        if port_number:
            if len(self.port_list[port_number].packets) != 0:
                pkt, time = self.port_list[port_number].dequeue()
                return port_number, pkt, time
            else:
                return None, None, None

        # Find port with oldest packet
        #@todo Consider using a single queue for all ports
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

    def kill(self, join_threads=False):
        """
        Close all sockets for dataplane
        @param join_threads If True call join on each thread
        """
        for port_number in self.port_list.keys():
            self.port_list[port_number].kill()
            if join_threads:
                self.dbg(DEBUG_INFO, "Joining " + str(port_number))
                self.port_list[port_number].join()

        self.dbg(DEBUG_INFO, "DataPlane shutdown")

    def show(self, prefix=''):
        print prefix + "Dataplane Controller"
        for pnum, port in self.port_list.items():
            print prefix + "OpenFlow Port Number " + str(pnum)
            port.show(prefix + '  ')

