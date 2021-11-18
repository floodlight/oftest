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
import select
import logging
from threading import Thread
from threading import Lock
from threading import Condition
import ofutils
import netutils
from pcap_writer import PcapWriter

if "linux" in sys.platform:
    import afpacket
else:
    import pcap

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


class DataPlanePortLinux:
    """
    Uses raw sockets to capture and send packets on a network interface.
    """

    RCV_SIZE_DEFAULT = 4096
    ETH_P_ALL = 0x03
    RCV_TIMEOUT = 10000

    def __init__(self, interface_name, port_number):
        """
        @param interface_name The name of the physical interface like eth1
        """
        self.interface_name = interface_name
        self.socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, 0)
        afpacket.enable_auxdata(self.socket)
        self.socket.bind((interface_name, self.ETH_P_ALL))
        netutils.set_promisc(self.socket, interface_name)
        self.socket.settimeout(self.RCV_TIMEOUT)

    def __del__(self):
        if self.socket:
            self.socket.close()

    def fileno(self):
        """
        Return an integer file descriptor that can be passed to select(2).
        """
        return self.socket.fileno()

    def recv(self):
        """
        Receive a packet from this port.
        @retval (packet data, timestamp)
        """
        pkt = afpacket.recv(self.socket, self.RCV_SIZE_DEFAULT)
        return (pkt, time.time())

    def send(self, packet):
        """
        Send a packet out this port.
        @param packet The packet data to send to the port
        @retval The number of bytes sent
        """
        return self.socket.send(packet)

    def down(self):
        """
        Bring the physical link down.
        """
        os.system("ifconfig down %s" % self.interface_name)

    def up(self):
        """
        Bring the physical link up.
        """
        os.system("ifconfig up %s" % self.interface_name)


class DataPlanePortPcap:
    """
    Alternate port implementation using libpcap. This is used by non-Linux
    operating systems.
    """

    def __init__(self, interface_name, port_number):
        self.pcap = pcap.pcap(interface_name)
        self.pcap.setnonblock()

    def fileno(self):
        return self.pcap.fileno()

    def recv(self):
        (timestamp, pkt) = next(self.pcap)
        return (pkt[:], timestamp)

    def send(self, packet):
        if hasattr(self.pcap, "inject"):
            return self.pcap.inject(packet, len(packet))
        else:
           return self.pcap.sendpacket(packet)

    def down(self):
        pass

    def up(self):
        pass

class DataPlane(Thread):
    """
    This class provides methods to send and receive packets on the dataplane.
    It uses the DataPlanePort class, or an alternative implementation of that
    interface, to do IO on a particular port. A background thread is used to
    read packets from the dataplane ports and enqueue them to be read by the
    test. The kill() method must be called to shutdown this thread.
    """

    MAX_QUEUE_LEN = 100

    def __init__(self, config=None):
        Thread.__init__(self)

        # dict from port number to port object
        self.ports = {}

        # dict from port number to list of (timestamp, packet)
        self.packet_queues = {}

        # cvar serves double duty as a regular top level lock and
        # as a condition variable
        self.cvar = Condition()

        # Used to wake up the event loop from another thread
        self.waker = ofutils.EventDescriptor()
        self.killed = False

        self.logger = logging.getLogger("dataplane")
        self.pcap_writer = None

        if config is None:
            self.config = {}
        else:
            self.config = config; 

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
        if "dataplane" in self.config and "portclass" in self.config["dataplane"]:
            self.dppclass = self.config["dataplane"]["portclass"]
        elif "linux" in sys.platform:
            self.dppclass = DataPlanePortLinux
        else:
            self.dppclass = DataPlanePortPcap

        self.start()

    def run(self):
        """
        Activity function for class
        """
        while not self.killed:
            sockets = [self.waker] + self.ports.values()
            try:
                sel_in, sel_out, sel_err = select.select(sockets, [], [], 1)
            except:
                print sys.exc_info()
                self.logger.error("Select error, exiting")
                break

            with self.cvar:
                for port in sel_in:
                    if port == self.waker:
                        self.waker.wait()
                        continue
                    else:
                        # Enqueue packet
                        try:
                            pkt, timestamp = port.recv()
                        except OSError as e:
                            # the afpacket.py will assert except raising OSError if e.errno is ENETDOWN 
                            # remove socket from sel_in
                            self.port_del(port.interface_name, port._port_number)
                            continue

                        port_number = port._port_number
                        self.logger.debug("Pkt len %d in on port %d",
                                          len(pkt), port_number)
                        if self.pcap_writer:
                            self.pcap_writer.write(pkt, timestamp, port_number)
                        queue = self.packet_queues[port_number]
                        if len(queue) >= self.MAX_QUEUE_LEN:
                            # Queue full, throw away oldest
                            queue.pop(0)
                            self.logger.debug("Discarding oldest packet to make room")
                        queue.append((pkt, timestamp))
                self.cvar.notify_all()

        self.logger.info("Thread exit")

    def port_add(self, interface_name, port_number):
        """
        Add a port to the dataplane
        @param interface_name The name of the physical interface like eth1
        @param port_number The port number used to refer to the port
        Stashes the port number on the created port object.
        """
        self.ports[port_number] = self.dppclass(interface_name, port_number)
        self.ports[port_number]._port_number = port_number
        self.packet_queues[port_number] = []
        # Need to wake up event loop to change the sockets being selected on.
        self.waker.notify()

    def port_del(self, interface_name, port_number):
        """
        Del a port from the dataplane
        @param interface_name The name of the physical interface like eth1
        @param port_number The port number used to refer to the port
        """
        del self.ports[port_number]
        # Need to wake up event loop to change the sockets being selected on.
        self.waker.notify()

    def send(self, port_number, packet):
        """
        Send a packet to the given port
        @param port_number The port to send the data to
        @param packet Raw packet data to send to port
        """
        self.logger.debug("Sending %d bytes to port %d" %
                          (len(packet), port_number))
        if self.pcap_writer:
            self.pcap_writer.write(packet, time.time(), port_number)
        bytes = self.ports[port_number].send(packet)
        if bytes != len(packet):
            self.logger.error("Unhandled send error, length mismatch %d != %d" %
                     (bytes, len(packet)))
        return bytes

    def oldest_port_number(self):
        """
        Returns the port number with the oldest packet, or
        None if no packets are queued.
        """
        min_port_number = None
        min_time = float('inf')
        for (port_number, queue) in self.packet_queues.items():
            if queue and queue[0][1] < min_time:
                min_time = queue[0][1]
                min_port_number = port_number
        return min_port_number

    # Dequeues and yields packets in the order they were received.
    # Yields (port number, packet, received time).
    # If port_number is not specified yields packets from all ports.
    def packets(self, port_number=None):
        while True:
            rcv_port_number = port_number or self.oldest_port_number()

            if rcv_port_number == None:
                self.logger.debug("Out of packets on all ports")
                break

            queue = self.packet_queues[rcv_port_number]

            if len(queue) == 0:
                self.logger.debug("Out of packets on port %d", rcv_port_number)
                break

            pkt, time = queue.pop(0)
            yield (rcv_port_number, pkt, time)

    def poll(self, port_number=None, timeout=-1, exp_pkt=None):
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
            for (rcv_port_number, pkt, time) in self.packets(port_number):
                self.logger.debug("Checking packet from port %d", rcv_port_number)
                if not exp_pkt or match_exp_pkt(exp_pkt, pkt):
                    return (rcv_port_number, pkt, time)
            self.logger.debug("Did not find packet")
            return None

        with self.cvar:
            ret = ofutils.timed_wait(self.cvar, grab, timeout=timeout)

        if ret != None:
            return ret
        else:
            self.logger.debug("Poll time out, no packet from " + str(port_number))
            return (None, None, None)

    def kill(self):
        """
        Stop the dataplane thread.
        """
        self.killed = True
        self.waker.notify()
        self.join()
        # Explicitly release ports to ensure we don't run out of sockets
        # even if someone keeps holding a reference to the dataplane.
        del self.ports

    def port_down(self, port_number):
        """Brings the specified port down"""
        self.ports[port_number].down()

    def port_up(self, port_number):
        """Brings the specified port up"""
        self.ports[port_number].up()

    def flush(self):
        """
        Drop any queued packets.
        """
        for port_number in self.packet_queues.keys():
            self.packet_queues[port_number] = []

    def start_pcap(self, filename):
        assert(self.pcap_writer == None)
        self.pcap_writer = PcapWriter(filename)

    def stop_pcap(self):
        if self.pcap_writer:
            self.pcap_writer.close()
            self.pcap_writer = None
