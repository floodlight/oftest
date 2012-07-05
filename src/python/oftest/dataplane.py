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
import time
import socket
try:
    import pcap
except:
    sys.exit("Need to install pypcap (apt-get install python-pypcap).")
from threading import Thread
from threading import Condition
import select
import logging
from oft_assert import oft_assert

##@todo Find a better home for these identifiers (dataplane)
RCV_SIZE_DEFAULT = 4096
RCV_TIMEOUT = 10000

class DataPlanePort(Thread):
    """
    Class defining a port monitoring object.

    Control a dataplane port connected to the switch under test.
    Creates a promiscuous socket on a physical interface.
    Queues the packets received on that interface with time stamps.
    Inherits from Thread class as meant to run in background.  Also
    supports polling.
    Use accessors to dequeue packets for proper synchronization.

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
            self.pcap = pcap.pcap(interface_name, RCV_SIZE_DEFAULT, True, RCV_TIMEOUT)
 #           self.pcap.setnonblock()
        except OSError, msg:
            self.logger.info("Could not open interface: " + msg)
            sys.exit(1)
        self.logger.info("Opened interface")
        self.parent = parent
        self.pkt_sync = self.parent.pkt_sync
        self.pkt_handler = None

    def pcap_cb(self, ts, pkt):
        self.logger.debug("Pkt len " + str(len(pkt)) +
             " in at " + str(ts))

        # Enqueue packet
        self.pkt_sync.acquire()
        if len(self.packets) >= self.max_pkts:
            # Queue full, throw away oldest
            self.packets.pop(0)
            self.packets_discarded += 1
        else:
            self.parent.packets_pending += 1
        # Check if parent is waiting on this (or any) port
        if self.parent.want_pkt:
            if (not self.parent.want_pkt_port or
                    self.parent.want_pkt_port == self.port_number):
                self.parent.got_pkt_port = self.port_number
                self.parent.want_pkt = False
#                    self.parent.pkt_sync.notify()
        self.packets.append((pkt, ts))
        self.packets_total += 1
        self.pkt_sync.release()

    def run(self):
        """
        Activity function for class
        """
        self.running = True
        self.socs = [self.pcap.fd]
        while self.running:
            try:
                sel_in, sel_out, sel_err = \
                    select.select(self.socs, [], [], 1)
            except StandardError, socket.error:
                self.logger.error("Select error: " + sys.exc_info())
                break
            
            if not self.running:
                break
            
            if (sel_in is None) or (len(sel_in) == 0):
                continue

            self.pcap.dispatch(1, self.pcap_cb)

        self.logger.info("Thread exit ")
        self.pcap.close()

    def kill(self):
        """
        Terminate the running thread
        """
        self.logger.debug("Port monitor kill")
        self.running = False
        

    def dequeue(self, use_lock=True):
        """
        Get the oldest packet in the queue
        @param use_lock If True, acquires the packet sync lock (which is
        really the parent's lock)
        @return The pair packet, packet time-stamp
        """
        if use_lock:
            self.pkt_sync.acquire()
        if len(self.packets) > 0:
            pkt, pkt_time = self.packets.pop(0)
            self.parent.packets_pending -= 1
        else:
            pkt = pkt_time = None
        if use_lock:
            self.pkt_sync.release()
        return pkt, pkt_time

    def timestamp_head(self):
        """
        Return the timestamp of the head of queue or None if empty
        """
        rv = None
        try:
            rv = self.packets[0][1]
        except StandardError:
            rv = None
        return rv

    def flush(self):
        """
        Clear the packet queue
        """
        self.pkt_sync.acquire()
        self.packets_discarded += len(self.packets)
        self.parent.packets_pending -= len(self.packets)
        self.packets = []
        self.packet_times = []
        self.pkt_sync.release()


    def send(self, packet, queue_id=0):
        """
        Send a packet to the dataplane port
        @param packet The packet data to send to the port
        @param queue_id The queue to send to (to be implemented)
        @retval The number of bytes sent
        """
        self.logger.debug("Pkt len " + str(len(packet)) +
             " out")
        try:
            ret = self.pcap.inject(packet, len(packet))
        except OSError, msg:
            self.logger.info("Could not inject packet: " + msg)
            sys.exit(1)
        return ret


    def register(self, pkt_handler):
        """
        Register a callback function to receive packets from this
        port.  The callback will be passed the packet, the
        interface name and the port number (if set) on which the
        packet was received.
        """
        self.pkt_handler = pkt_handler

    def show(self, prefix=''):
        print prefix + "Name:          " + self.interface_name
        print prefix + "Pkts pending:  " + str(len(self.packets))
        print prefix + "Pkts total:    " + str(self.packets_total)
        print prefix + "pcap:        " + str(self.pcap)


class DataPlane:
    """
    Class defining access primitives to the data plane
    Controls a list of DataPlanePort objects
    """
    def __init__(self):
        self.port_list = {}
        # pkt_sync serves double duty as a regular top level lock and
        # as a condition variable
        self.pkt_sync = Condition()

        # These are used to signal async pkt arrival for polling
        self.want_pkt = False
        self.want_pkt_port = None # What port required (or None)
        self.got_pkt_port = None # On what port received?
        self.packets_pending = 0 # Total pkts in all port queues
        self.logger = logging.getLogger("dataplane")
        self.pkt_handler = None

    def port_add(self, interface_name, port_number):
        """
        Add a port to the dataplane
        TBD:  Max packets for queue?
        @param interface_name The name of the physical interface like eth1
        @param port_number The port number used to refer to the port
        """

        self.port_list[port_number] = DataPlanePort(interface_name,
                                                    port_number, self)
        self.port_list[port_number].start()
        if self.pkt_handler is not None:
            self.port_list[port_number].register(self.pkt_handler)

    def register(self, pkt_handler):
        """
        Register pkt_handler for all ports
        """
        self.pkt_handler = pkt_handler
        for port_number in self.port_list.keys():
            self.port_list[port_number].register(pkt_handler)
        
    def send(self, port_number, packet, queue_id=0):
        """
        Send a packet to the given port
        @param port_number The port to send the data to
        @param packet Raw packet data to send to port
        @param queue_id The queue to send to (to be implemented)
        """
        #@todo Verify port_number is in keys of port_list
        self.logger.debug("Sending %d bytes to port %d" %
                          (len(packet), port_number))
        bytes = self.port_list[port_number].send(packet, queue_id=queue_id)
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
        min_time = 0
        min_port = -1
        for port_number in self.port_list.keys():
            ptime = self.port_list[port_number].timestamp_head()
            if ptime:
                if (min_port == -1) or (ptime < min_time):
                    min_time = ptime
                    min_port = port_number
        oft_assert(min_port != -1, "Could not find port when pkts pending")

        return min_port

    def poll(self, port_number=None, timeout=None):
        """
        Poll one or all dataplane ports for a packet

        If port_number is given, get the oldest packet from that port.
        Otherwise, find the port with the oldest packet and return
        that packet.
        @param port_number If set, get packet from this port
        @param timeout If positive and no packet is available, block
        until a packet is received or for this many seconds
        @return The triple port_number, packet, pkt_time where packet
        is received from port_number at time pkt_time.  If a timeout
        occurs, return None, None, None
        """

        self.pkt_sync.acquire()

        # Check if requested specific port and it has a packet
        if port_number and len(self.port_list[port_number].packets) != 0:
            pkt, time = self.port_list[port_number].dequeue(use_lock=False)
            self.pkt_sync.release()
            oft_assert(pkt, "Poll: packet not found on port " +
                       str(port_number))
            return port_number, pkt, time

        # Check if requested any port and some packet pending
        if not port_number and self.packets_pending != 0:
            port = self._oldest_packet_find()
            pkt, time = self.port_list[port].dequeue(use_lock=False)
            self.pkt_sync.release()
            oft_assert(pkt, "Poll: oldest packet not found")
            return port, pkt, time

        # No packet pending; blocking call requested?
        if not timeout:
            self.pkt_sync.release()
            return None, None, None

        # Desired packet isn't available and timeout is specified
        # Already holding pkt_sync; wait on pkt_sync variable
        self.want_pkt = True
        self.want_pkt_port = port_number
        self.got_pkt_port = None
        self.pkt_sync.wait(timeout)
        self.want_pkt = False
        if self.got_pkt_port:
            pkt, time = \
                self.port_list[self.got_pkt_port].dequeue(use_lock=False)
            self.pkt_sync.release()
            oft_assert(pkt, "Poll: pkt reported, but not found at " +
                       str(self.got_pkt_port))
            return self.got_pkt_port, pkt, time

        self.pkt_sync.release()
        self.logger.debug("Poll time out, no packet from " + str(port_number))

        return None, None, None

    def kill(self, join_threads=True):
        """
        Close all devices for dataplane
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

