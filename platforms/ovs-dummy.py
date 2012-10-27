"""
Dummy platform

This platform uses Open vSwitch dummy interfaces.
"""

import logging
import os
import select
import socket
import struct
import sys
import time
from threading import Thread
from threading import Lock

RCV_TIMEOUT = 10000
RUN_DIR = os.environ.get("OVS_RUNDIR", "/var/run/openvswitch")

class DataPlanePortOVSDummy(Thread):
    """
    Class defining a port monitoring object that uses Unix domain
    sockets for ports, intended for connecting to Open vSwitch "dummy"
    netdevs.
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
        self.txq = []
        self.txq_lock = Lock()
        logname = "dp-" + interface_name
        self.logger = logging.getLogger(logname)
        try:
            self.socket = DataPlanePortOVSDummy.interface_open(interface_name)
        except:
            self.logger.info("Could not open socket")
            raise
        self.logger.info("Opened port monitor (class %s)", type(self).__name__)
        self.parent = parent

    @staticmethod
    def interface_open(interface_name):
        """
        Open a Unix domain socket interface.
        @param interface_name port name as a string such as 'eth1'
        @retval s socket
        """
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(RCV_TIMEOUT)
        s.setblocking(0)
        s.connect("%s/%s" % (RUN_DIR, interface_name))
        return s

    def run(self):
        """
        Activity function for class
        """
        self.running = True
        rxbuf = ""
        while self.running:
            try:
                self.txq_lock.acquire()
                if self.txq:
                    wlist = [self.socket]
                else:
                    wlist = []
                self.txq_lock.release()

                rout, wout, eout = select.select([self.socket], wlist, [], 1)
            except:
                print sys.exc_info()
                self.logger.error("Select error, exiting")
                break

            if not self.running:
                break

            if wout:
                self.txq_lock.acquire()
                if self.txq:
                    retval = self.socket.send(self.txq[0])
                    if retval > 0:
                        self.txq[0] = self.txq[0][retval:]
                        if len(self.txq[0]) == 0:
                            self.txq = self.txq[1:]
                self.txq_lock.release()

            if rout:
                if len(rxbuf) < 2:
                    n = 2 - len(rxbuf)
                else:
                    frame_len = struct.unpack('>h', rxbuf[:2])[0]
                    n = (2 + frame_len) - len(rxbuf)

                data = self.socket.recv(n)
                rxbuf += data
                if len(data) == n and len(rxbuf) > 2:
                    rcvtime = time.clock()
                    self.logger.debug("Pkt len " + str(len(rxbuf)) +
                             " in at " + str(rcvtime) + " on port " +
                             str(self.port_number))

                    # Enqueue packet
                    with self.parent.pkt_sync:
                        if len(self.packets) >= self.max_pkts:
                            # Queue full, throw away oldest
                            self.packets.pop(0)
                            self.packets_discarded += 1
                            self.logger.debug("Discarding oldest packet to make room")
                        self.packets.append((rxbuf[2:], rcvtime))
                        self.packets_total += 1
                        self.parent.pkt_sync.notify_all()

                    rxbuf = ''

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

        self.txq_lock.acquire()
        if len(self.txq) < self.max_pkts:
            self.txq.append(struct.pack('>h', len(packet)) + packet)
            retval = len(packet)
        else:
            retval = 0
        self.txq_lock.release()

        return retval

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

# Update this dictionary to suit your environment.
dummy_port_map = {
    1 : "p1",
    2 : "p2",
    3 : "p3",
    4 : "p4"
}

def platform_config_update(config):
    """
    Update configuration for the dummy platform

    @param config The configuration dictionary to use/update
    """
    global dummy_port_map
    config["port_map"] = dummy_port_map.copy()
    config["caps_table_idx"] = 0
    config["dataplane"] = {"portclass": DataPlanePortOVSDummy}
    config["allow_user"] = True
