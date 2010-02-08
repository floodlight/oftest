"""
OpenFlow Test Framework

Dataplane class

Provide the interface to the control the set of ports being used
to stimulate the switch under test.

See the class dataplaneport for more details.  This class wraps
a set of those objects allowing general calls and parsing 
configuration.

"""

from dataplaneport import *

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
