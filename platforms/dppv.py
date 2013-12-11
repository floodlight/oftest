###############################################################################
#
# DataPlanePort implementation for VPI platforms. 
#
# The VPI-based platforms available here (bpp and vpi) depend upon
# this module for the implementation of the OFTest DataPlanePort interface. 
#
###############################################################################
import sys
import os
import logging
import time

from oftest import config

# Requires the libvpi and pyvpi packages
from vpi import vpi

class DataPlanePortVPI:
    """
    Class defining a port monitoring VPI object.

    """
    
    #
    # OFTest creates and destroys DataPlanePorts for each test. 
    # We just cache them here. 
    cachedVPIs = {}
    
    def vpiInit(self, interface_name, port_number, pcap_dir="."):
        self.vpiSpec = interface_name; 
        if self.vpiSpec in self.cachedVPIs:
            self.vpi = self.cachedVPIs[self.vpiSpec]
        else:
            self.vpi = vpi.Vpi(self.vpiSpec)
            pcapspec = "pcapdump|%s/oft-port%.2d.pcap|mpls|PORT%d" % (pcap_dir, port_number, port_number)
            self.vpi.AddSendRecvListener(pcapspec); 
            self.cachedVPIs[self.vpiSpec] = self.vpi

        return self.vpi

    
    def __init__(self, interface_name, port_number):
        """
        Set up a port monitor object
        @param interface_name The name of the physical interface like eth1
        @param port_number The port number associated with this port
        """
        self.interface_name = interface_name
        self.port_number = port_number
        logname = "VPI:" + interface_name
        self.logger = logging.getLogger(logname)
        
        path = "."
        if config['log_file']:
            path = config['log_file']

        if self.vpiInit(interface_name, port_number, 
                        os.path.dirname(os.path.abspath(path))) == None:
            raise Exception("Could not create VPI interface %s" % interface_name)

        self.logger.info("VPI: %s:%d\n" % (interface_name, port_number))

    def fileno(self):
        return self.vpi.DescriptorGet()

    def recv(self):
        pkt = self.vpi.Recv(False) 
        return (pkt, time.time())

    def send(self, packet):
        """
        Send a packet to the dataplane port
        @param packet The packet data to send to the port
        @retval The number of bytes sent
        """
        _len = len(packet); 
        self.vpi.Send(packet)
        return _len; 
