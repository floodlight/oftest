#!/usr/bin/env python
#
# Create veth pairs and start up switch daemons
#

import os
import sys
import time
import signal
from subprocess import Popen,PIPE,call,check_call
from optparse import OptionParser

class OFSwitch:
    """
    Base class for running OpenFlow switches
    Not sure if this is useful; putting it here preemptively
    """
    Name="none"
    def __init__(self,interfaces,config):
        self.interfaces = interfaces
        self.port = config.port
    def start(self):
        ''' 
        Start up all the various parts of a switch:
            should block 
        '''    
        pass
    def test(self):
        ''' 
        Run a self test to make sure the switch is runnable
        '''
        return True
    def stop(self):
        '''
        Stop any parts of the switch that could be still running
        '''
        pass
   
class OFReferenceSwitch(OFSwitch):
    """
    Start up an OpenFlow reference switch
    """
    Name="reference"
    def __init__(self,interfaces,config):
        OFSwitch.__init__(self,interfaces,config)
        if config.of_dir:
            self.of_dir=config.of_dir
        else:
            self.of_dir = "../../openflow"
        self.ofd = self.of_dir + "/udatapath/ofdatapath"
        self.ofp = self.of_dir + "/secchan/ofprotocol"
        self.ofd_op = None
    def test(self):
        if not OFSwitch.test(self):
            return False
        try:
            check_call(["ls", self.ofd])
        except:
            print "Could not find datapath daemon: " + self.ofd
            return False
        try:
            check_call(["ls", self.ofp])
        except:
            print "Could not find protocol daemon: " + self.ofp
            return False
        return True

    def start(self):
        ints = ','.join(self.interfaces)
        self.ofd_op = Popen([self.ofd, "-i", ints, "punix:/tmp/ofd"])
        print "Started ofdatapath on IFs " + ints + " with pid " + str(self.ofd_op.pid)        
        call([self.ofp, "unix:/tmp/ofd", "tcp:127.0.0.1:" + str(options.port),
              "--fail=closed", "--max-backoff=1"])
    def stop(self):
        if self.ofd_op:
            print "Killing ofdatapath on pid: %d" % (self.ofd_op.pid)
            os.kill(self.ofd_op.pid,signal.SIGTERM)
            #self.ofd_op.kill()   ### apparently Popen.kill() requires python 2.6

class OFPS(OFSwitch):
    """
    Start up an OpenFlow reference switch
    """
    Name="ofps"
    def __init__(self,interfaces,config):
        OFSwitch.__init__(self,interfaces,config)
        if config.of_dir:
            self.of_dir=config.of_dir
        else:
            self.of_dir = "../src/python/ofps"
        self.ofps = self.of_dir + "/ofps.py"
        
    def test(self):
        if not OFSwitch.test(self):
            return False
        try:
            check_call(["ls", self.ofps])
        except:
            print "Could not find datapath daemon: " + self.ofd
            return False
        return True

    def start(self):
        ints = ','.join(self.interfaces)
        cmd =[self.ofps, "-c", "127.0.0.1", '-i', ints, '-p', str(options.port),
              ] 
        call(cmd)
        print "Started %s" % (' '.join(cmd))
        
    def stop(self):
        pass

def setup_veths(options):
    print "Setting up %d virtual ethernet pairs" % (options.port_count)
    call(["/sbin/modprobe", "veth"])
    for idx in range(0, options.port_count):
        print "Creating veth pair " + str(idx)
        call(["/sbin/ip", "link", "add", "type", "veth"])
    
    for idx in range(0, 2 * options.port_count):
        cmd = ["/sbin/ifconfig", 
               "veth" + str(idx), 
               "192.168.1" + str(idx) + ".1", 
               "netmask", 
               "255.255.255.0"]
        print "Cmd: " + str(cmd)
        call(cmd)
    veths = [ "veth0"]
    for idx in range(1, options.port_count):
        veths.append("veth" + str(2 * idx))
    return veths

def teardown_veths(options):
    print "Tearing down virtual ethernet pairs"
    call(["/sbin/rmmod","veth"])



parser = OptionParser(version="%prog 0.1")
parser.set_defaults(switch="reference")
parser.set_defaults(port_count=4)
parser.set_defaults(of_dir=None)
parser.set_defaults(port=6633)
parser.add_option("-n", "--port_count", type="int",
                  help="Number of veth pairs to create")
parser.add_option("-o", "--of_dir", help="OpenFlow root directory for host")
parser.add_option("-p", "--port", type="int",
                  help="Port for OFP to listen on")
parser.add_option("-N", "--no_wait", action="store_true",
                  help="Do not wait 2 seconds to start daemons")
parser.add_option("-s","--switch",help="Which OpenFlow Switch to run: 'reference', 'ofps', 'ovs'")
(options, args) = parser.parse_args()


switch = None

try:

    veths = setup_veths(options)
    
    if options.switch == OFReferenceSwitch.Name :
        switch = OFReferenceSwitch(veths, options)
    elif options.switch == OFPS.Name :
        switch = OFPS(veths, options)
    #########
    ### Add more switch types here
    #########
    
    if switch == None:
        print "Failed to run unknown switch: " + options.switch
        sys.exit(1)
 
    print "Running self test for switch " + switch.Name    
    if not switch.test():
        print "Failed switch self test: exiting..."
        sys.exit(1)    
    
    if not options.no_wait:
        print "Starting %s switch in 2 seconds; ^C to quit" % ( options.switch )
        time.sleep(2)
    else:
        print "Starting %s switch; ^C to quit" % (options.switch)
    
    print "Starting switch"    
    switch.start()   #### This should block until killed externally

finally:
    teardown_veths(options)
    if switch:
        switch.stop()






