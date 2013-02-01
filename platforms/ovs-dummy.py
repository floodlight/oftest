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

class DataPlanePortOVSDummy:
    """
    Class defining a port monitoring object that uses Unix domain
    sockets for ports, intended for connecting to Open vSwitch "dummy"
    netdevs.
    """

    def __init__(self, interface_name, port_number, max_pkts=1024):
        """
        Set up a port monitor object
        @param interface_name The name of the physical interface like eth1
        @param port_number The port number associated with this port
        @param max_pkts Maximum number of pkts to keep in queue
        """
        self.interface_name = interface_name
        self.max_pkts = max_pkts
        self.port_number = port_number
        self.txq = []
        self.rxbuf = ""
        logname = "dp-" + interface_name
        self.logger = logging.getLogger(logname)
        try:
            self.socket = DataPlanePortOVSDummy.interface_open(interface_name)
        except:
            self.logger.info("Could not open socket")
            raise
        self.logger.info("Opened port monitor (class %s)", type(self).__name__)

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

    def __del__(self):
        if self.socket:
            self.socket.close()

    def fileno(self):
        """
        Return an integer file descriptor that can be passed to select(2).
        """
        return self.socket.fileno()

    def recv(self):
        while True:
            rout, wout, eout = select.select([self.socket], [], [], 0)
            if not rout:
                return

            if len(self.rxbuf) < 2:
                n = 2 - len(self.rxbuf)
            else:
                frame_len = struct.unpack('>h', self.rxbuf[:2])[0]
                n = (2 + frame_len) - len(self.rxbuf)

            data = self.socket.recv(n)
            self.rxbuf += data
            if len(data) == n and len(self.rxbuf) > 2:
                rcvtime = time.time()
                packet = self.rxbuf[2:]
                self.logger.debug("Pkt len " + str(len(packet)) +
                         " in at " + str(rcvtime) + " on port " +
                         str(self.port_number))
                self.rxbuf = ""
                return (packet, rcvtime)

    def send(self, packet):
        if len(self.txq) < self.max_pkts:
            self.txq.append(struct.pack('>h', len(packet)) + packet)
            retval = len(packet)
        else:
            retval = 0
        self.__run_tx()
        return retval

    def __run_tx(self):
        while self.txq:
            rout, wout, eout = select.select([], [self.socket], [], 0)
            if not wout:
                return

            retval = self.socket.send(self.txq[0])
            if retval > 0:
                self.txq[0] = self.txq[0][retval:]
                if len(self.txq[0]) == 0:
                    self.txq = self.txq[1:]
        
    def down(self):
        pass

    def up(self):
        pass

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
