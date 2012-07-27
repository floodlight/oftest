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
from threading import Condition
import select
import logging
from oft_assert import oft_assert
from ofutils import *

##@todo Find a better home for these identifiers (dataplane)
RCV_SIZE_DEFAULT = 4096
ETH_P_ALL = 0x03
RCV_TIMEOUT = 10000

def match_exp_pkt(exp_pkt, pkt):
    """
    Compare the string value of pkt with the string value of exp_pkt,
    and return True iff they are identical.  If the length of exp_pkt is
    less than the minimum Ethernet frame size (60 bytes), then padding
    bytes in pkt are ignored.
    """
    e = str(exp_pkt)
    p = str(pkt)
    if len(e) < 60:
        p = p[:len(e)]
    return e == p


class DataPlanePort(Thread):
    """
    Class defining a port monitoring object.

    Control a dataplane port connected to the switch under test.
    Creates a promiscuous socket on a physical interface.
    Queues the packets received on that interface with time stamps.
    Inherits from Thread class as meant to run in background.  Also
    supports polling.

    Currently assumes a controlling 'parent' which maintains a
    common Lock object and a total packet-pending count.  May want
    to decouple that some day.
    """

    def __init__(self, interface_name, port_number, parent, max_pkts=1024):
        """
        Set up a port monitor object
        @param interface_name The name of the physical interface like eth1
        @param port_number The port number associated with this port
        @param parent The controlling dataplane object; for pkt wait CV
        @param max_pkts Maximum number of pkts to keep in queue
        """
        Thread.__init__(self)
        self.interface_name = interface_name
        self.max_pkts = max_pkts
        self.packets_total = 0
        self.packets = []
        self.packets_discarded = 0
        self.port_number = port_number
        logname = "dp-" + interface_name
        self.logger = logging.getLogger(logname)
        try:
            self.socket = self.interface_open(interface_name)
        except:
            self.logger.info("Could not open socket")
            sys.exit(1)
        self.logger.info("Openned port monitor socket")
        self.parent = parent

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
                self.logger.error("Select error, exiting")
                break

            if not self.running:
                break

            if (sel_in is None) or (len(sel_in) == 0):
                continue

            try:
                rcvmsg = self.socket.recv(RCV_SIZE_DEFAULT)
            except socket.error:
                if not error_warned:
                    self.logger.info("Socket error on recv")
                    error_warned = True
                continue

            if len(rcvmsg) == 0:
                self.logger.info("Zero len pkt rcvd")
                self.kill()
                break

            rcvtime = time.clock()
            self.logger.debug("Pkt len " + str(len(rcvmsg)) +
                     " in at " + str(rcvtime) + " on port " +
                     str(self.port_number))

            # Enqueue packet
            with self.parent.pkt_sync:
                if len(self.packets) >= self.max_pkts:
                    # Queue full, throw away oldest
                    self.packets.pop(0)
                    self.packets_discarded += 1
                    self.logger.debug("Discarding oldest packet to make room")
                self.packets.append((rcvmsg, rcvtime))
                self.packets_total += 1
                self.parent.pkt_sync.notify_all()

        self.logger.info("Thread exit")

    def kill(self):
        """
        Terminate the running thread
        """
        self.logger.debug("Port monitor kill")
        self.running = False
        try:
            self.socket.close()
        except:
            self.logger.info("Ignoring dataplane soc shutdown error")

    def timestamp_head(self):
        """
        Return the timestamp of the head of queue or None if empty
        """
        rv = None
        try:
            rv = self.packets[0][1]
        except:
            rv = None
        return rv

    def flush(self):
        """
        Clear the packet queue
        """
        with self.parent.pkt_sync:
            self.packets_discarded += len(self.packets)
            self.packets = []

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
    def __init__(self, config=None):
        self.port_list = {}
        # pkt_sync serves double duty as a regular top level lock and
        # as a condition variable
        self.pkt_sync = Condition()

        # These are used to signal async pkt arrival for polling
        self.want_pkt = False
        self.exp_pkt = None
        self.want_pkt_port = None # What port required (or None)
        self.got_pkt_port = None # On what port received?
        self.packets_pending = 0 # Total pkts in all port queues
        self.logger = logging.getLogger("dataplane")

        if config is None:
            self.config = {}
        else:
            self.config = config; 

        ############################################################
        #
        # We use the DataPlanePort class defined here by 
        # default for all port traffic:
        #
        self.dppclass = DataPlanePort

        ############################################################
        #
        # The platform/config can provide a custom DataPlanePort class
        # here if you have a custom implementation with different
        # behavior. 
        #
        # Set config.dataplane.portclass = MyDataPlanePortClass
        # where MyDataPlanePortClass has the same interface as the class
        # DataPlanePort defined here. 
        #
        if "dataplane" in self.config:
            if "portclass" in self.config["dataplane"]:
                self.dppclass = self.config["dataplane"]["portclass"]

        if self.dppclass == None:
            raise Exception("Problem determining DataPlanePort class.")


    def port_add(self, interface_name, port_number):
        """
        Add a port to the dataplane
        TBD:  Max packets for queue?
        @param interface_name The name of the physical interface like eth1
        @param port_number The port number used to refer to the port
        """

        self.port_list[port_number] = self.dppclass(interface_name, 
                                                    port_number, self); 

        self.port_list[port_number].start()



    def send(self, port_number, packet):
        """
        Send a packet to the given port
        @param port_number The port to send the data to
        @param packet Raw packet data to send to port
        """
        self.logger.debug("Sending %d bytes to port %d" %
                          (len(packet), port_number))
        bytes = self.port_list[port_number].send(packet)
        if bytes != len(packet):
            self.logger.error("Unhandled send error, length mismatch %d != %d" %
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
                self.logger.error("Unhandled send error" +
                         ", port %d, length mismatch %d != %d" %
                         (port_number, bytes, len(packet)))

    def _oldest_packet_find(self):
        # Find port with oldest packet
        oft_assert(min_port != -1, "Could not find port when pkts pending")

        return min_port

    # Returns the port with the oldest packet, or None if no packets are queued.
    def oldest_port(self):
        min_port = None
        min_time = float('inf')
        for port in self.port_list.values():
            ptime = port.timestamp_head()
            if ptime and ptime < min_time:
                min_time = ptime
                min_port = port
        return min_port

    # Dequeues and yields packets in the order they were received.
    # Yields (port, packet, received time).
    # If port_number is not specified yields packets from all ports.
    def packets(self, port_number=None):
        while True:
            if port_number == None:
                port = self.oldest_port()
            else:
                port = self.port_list[port_number]

            if port == None or len(port.packets) == 0:
                self.logger.debug("Out of packets for port %s" % str(port_number))
                # Out of packets
                break

            pkt, time = port.packets.pop(0)
            yield (port, pkt, time)

    def poll(self, port_number=None, timeout=None, exp_pkt=None):
        """
        Poll one or all dataplane ports for a packet

        If port_number is given, get the oldest packet from that port.
        Otherwise, find the port with the oldest packet and return
        that packet.

        If exp_pkt is true, discard all packets until that one is found

        @param port_number If set, get packet from this port
        @param timeout If positive and no packet is available, block
        until a packet is received or for this many seconds
        @param exp_pkt If not None, look for this packet and ignore any
        others received.  Note that if port_number is None, all packets
        from all ports will be discarded until the exp_pkt is found
        @return The triple port_number, packet, pkt_time where packet
        is received from port_number at time pkt_time.  If a timeout
        occurs, return None, None, None
        """

        if exp_pkt and not port_number:
            self.logger.warn("Dataplane poll with exp_pkt but no port number")

        # Retrieve the packet. Returns (port number, packet, time).
        def grab():
            self.logger.debug("Grabbing packet")
            for (port, pkt, time) in self.packets(port_number):
                self.logger.debug("Checking packet from port %d" % port.port_number)
                if not exp_pkt or match_exp_pkt(exp_pkt, pkt):
                    return (port, pkt, time)
            self.logger.debug("Did not find packet")
            return None

        with self.pkt_sync:
            ret = timed_wait(self.pkt_sync, grab, timeout=timeout)

        if ret != None:
            (port, pkt, time) = ret
            return (port.port_number, pkt, time)
        else:
            self.logger.debug("Poll time out, no packet from " + str(port_number))
            return (None, None, None)

    def kill(self, join_threads=True):
        """
        Close all sockets for dataplane
        @param join_threads If True call join on each thread
        """
        for port_number in self.port_list.keys():
            self.port_list[port_number].kill()
            if join_threads:
                self.logger.debug("Joining " + str(port_number))
                self.port_list[port_number].join()

        self.logger.info("DataPlane shutdown")

    def show(self, prefix=''):
        print prefix + "Dataplane Controller"
        print prefix + "Packets pending" + str(self.packets_pending)
        for pnum, port in self.port_list.items():
            print prefix + "OpenFlow Port Number " + str(pnum)
            port.show(prefix + '  ')

