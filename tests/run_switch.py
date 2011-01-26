#!/usr/bin/env python
#
# Create veth pairs and start up switch daemons
#

from __future__ import absolute_import
from __future__ import with_statement

import time
from optparse import OptionParser
import sys

import Managers


def parse_args():
    parser = OptionParser(version="%prog 0.1")
    parser.set_defaults(switch="ofps")
    parser.set_defaults(port_count=4)
    parser.set_defaults(of_dir=None)
    parser.set_defaults(port=6633)
    parser.set_defaults(wait=2)
    parser.add_option("-n", "--port_count", type="int",
                      help="Number of veth pairs to create")
    parser.add_option("-o", "--of_dir", help="OpenFlow root directory for host")
    parser.add_option("-p", "--port", type="int",
                      help="Port for OFP to listen on")
    parser.add_option("-N", "--no_wait", action="store_true",
                      help="Do not wait to start daemons")
    parser.add_option("-s","--switch",help="Which OpenFlow Switch to run: 'reference', 'ofps', 'ovs'")
    parser.add_option("-w","--wait",type="int",
                      help="Duration to wait before starting daemons")
    (options, args) = parser.parse_args()

    return options


if __name__ == '__main__':
    options = parse_args()

    with Managers.Platform(options) as driver:
        with Managers.Switch(options, driver) as switch:
            print "Running self test for switch " + switch.Name    
            if not switch.test():
                print "Failed switch self test: exiting..."
                sys.exit(1)    
            
            if not options.no_wait:
                print "Starting %s switch in %d seconds; ^C to quit" % (options.switch, options.wait)
                time.sleep(options.wait)
            else:
                print "Starting %s switch; ^C to quit" % (options.switch)
            
            print "Starting switch"    
            switch.start()   #### This should block until killed externally

