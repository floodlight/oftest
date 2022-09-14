"""
Solaris platform uses dlpi

This platform uses Solaris dlpi python interface.
"""
import sys
import time
import argparse

if "sunos" in sys.platform:
    import dlpi
    if not hasattr(dlpi, "DL_PROMISC_NOLOOP"):
        dlpi.DL_PROMISC_NOLOOP = 0x10000000
else:
    raise Exception("system platform need be solaris")

class DataPlanePortSolaris:
    """
    Uses libdlpi to capture and send packets on a network interface.
    """

    RCV_SIZE_DEFAULT = 4096
    RCV_TIMEOUT = 10000

    def __init__(self, interface_name, port_number):
        """
        @param interface_name The name of the physical interface like net1
        """
        self.interface_name = interface_name
        self.socket = dlpi.link(interface_name,dlpi.RAW)
        self.socket.bind(dlpi.ANY_SAP)
        self.socket.promiscon(dlpi.PROMISC_PHYS|dlpi.DL_PROMISC_NOLOOP)
        # self.socket.promiscon(dlpi.PROMISC_SAP|dlpi.DL_PROMISC_NOLOOP)
        # self.socket.promiscon(dlpi.PROMISC_MULTI|dlpi.DL_PROMISC_NOLOOP)
        self.socket.set_timeout(self.RCV_TIMEOUT)
        
    def __del__(self):
        if self.socket:
            self.socket.unbind()
            del self.socket

    def fileno(self):
        """
        Return an integer file descriptor that can be passed to select(2).
        """
        return self.socket.get_fd()

    def recv(self):
        """
        Receive a packet from this port.
        @retval (packet data, timestamp)
        """
        src, pkt = self.socket.recv(self.RCV_SIZE_DEFAULT)
        return (pkt, time.time())

    def send(self, packet):
        """
        Send a packet out this port.
        @param packet The packet data to send to the port
        @retval The number of bytes sent
        """
        addr = self.socket.get_physaddr(dlpi.CURR_PHYS_ADDR)
        self.socket.send(addr,packet)
        return len(packet)


    def down(self):
        """
        Bring the physical link down.
        """
        pass

    def up(self):
        """
        Bring the physical link up.
        """
        pass


if not "--platform-args" in " ".join(sys.argv):
    # Update this dictionary to suit your environment.
    solaris_port_map = {
        21 : "net1",
        22 : "net2",
        23 : "net3",
        24 : "net4"
    }
else:
    ap = argparse.ArgumentParser("solaris")
    ap.add_argument("--platform-args")
    (ops, rest) = ap.parse_known_args()
    solaris_port_map = {}
    ports = ops.platform_args.split(",")
    for ps in ports:
        (p, vpi) = ps.split("@")
        solaris_port_map[int(p)] = vpi



def platform_config_update(config):
    """
    Update configuration for the Solaris platform

    @param config The configuration dictionary to use/update
    """
    global solaris_port_map
    port_map = {}
    for (ofport, interface) in config["interfaces"]:
        port_map[ofport] = interface
    if not port_map:
        port_map= solaris_port_map

    config["port_map"] = port_map.copy()
    config["caps_table_idx"] = 0
    config["dataplane"] = {"portclass": DataPlanePortSolaris}
    config["allow_user"] = True
