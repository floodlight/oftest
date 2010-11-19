#!/usr/bin/env python
#
# Create veth pairs and start up switch daemons
#

import os
import time
from subprocess import Popen,PIPE,call,check_call
from optparse import OptionParser

print("Modified for use with OVS")
parser = OptionParser(version="%prog 0.1")
parser.set_defaults(port_count=4)
parser.set_defaults(port=6633)
parser.add_option("-n", "--port_count", type="int",
                  help="Number of veth pairs to create")
parser.add_option("-p", "--port", help="Port number for connection to ctrl")
parser.add_option("-o", "--of_dir", help="Directory with ovs-openflowd")
parser.add_option("-N", "--no_wait", action="store_true",
                  help="Do not wait 2 seconds to start daemons")
(options, args) = parser.parse_args()

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

veths = "veth0"
for idx in range(1, options.port_count):
    veths += ",veth" + str(2 * idx)

ofd = "ovs-openflowd"
if options.of_dir is not None:
    ofd = options.of_dir + "/" + ofd

try:
    check_call(["ls", ofd])
except:
    print "Could not find datapath daemon: " + ofd
    sys.exit(1)

if not options.no_wait:
    print "Starting ofprotocol in 2 seconds; ^C to quit"
    time.sleep(2)
else:
    print "Starting ofprotocol; ^C to quit"

ofd_op = call([ofd, "netdev@br0", "--ports=" + veths, "--max-backoff=1", 
               "tcp:127.0.0.1:" + str(options.port)])
