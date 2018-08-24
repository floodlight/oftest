"""
Platform configuration file
platform == veth_inject
"""

###############################################################################
#
# This platform assumes the loopback configuration file
# and the interface name to openflow port number configuration file
# are specified on the command line.
# Both files are expected to be in yaml format.
# The intent is to generate port_map dictionary, whose keys are
# openflow port numbers and whose values are interface names.
# Packets written to a specific interface will be seen on the corresponding
# openflow port.
# The loopback connections in the loopback configuration file are assumed
# to be unique; i.e. if interfaceA is connected to interfaceB, there is no
# configuration stating interfaceB is connected to interfaceA.
#
###############################################################################

import sys
import os
import argparse
import subprocess
import yaml

# The loopback port specification is passed via the "--platform-args"
# option to OFTest. 
# Note that we must guard against abbreviations supported by argparse
if not "--platform-args" in " ".join(sys.argv):
    raise Exception("--platform-args must be specified")

ap = argparse.ArgumentParser("veth_inject")
ap.add_argument("--platform-args")
(ops, rest) = ap.parse_known_args()

###############################################################################
# --platform-args=<loopback-cfgfile>,<ifname2ofport-cfgfile>

"""
sample config file specifying loopback connections ;
note no duplicate loopback configuration
ethernet11: ethernet12
ethernet9: ethernet10
ethernet3: ethernet4
ethernet1: ethernet2
ethernet7: ethernet8
ethernet5: ethernet6

sample config file specifying ifname2ofport mapping ;
each interface appearing as a key in the loopback configuration
must have a corresponding entry in the ifname2ofport mapping
ethernet1 : 1
ethernet2 : 2
ethernet3 : 3
ethernet4 : 4
ethernet5 : 5
ethernet6 : 6
ethernet7 : 7
ethernet8 : 8
ethernet9 : 9
ethernet10 : 10
ethernet11 : 11
ethernet12 : 12
"""

args = ops.platform_args.split(",")
# first arg: loopback cfg file
# second arg: ifname to ofport number mapping cfg file
if len(args) != 2:
    raise Exception("Expecting <loopback-cfgfile>,<ifname2ofport-cfgfile>")
lbcfgfile = args[0]
if2numcfgfile = args[1]

# read config files
if os.path.isfile(lbcfgfile):
    print(lbcfgfile)
    with open(lbcfgfile) as f:
        lbcfg = yaml.load(f)
else:
    lbcfg = {}
if os.path.isfile(if2numcfgfile):
    print(if2numcfgfile)
    with open(if2numcfgfile) as f:
        if2numcfg = yaml.load(f)
else:
    if2numcfg = {}

# lbcfg sanity check: keys and values should have no overlap
if set(lbcfg.keys()) != ( set(lbcfg.keys()) - set(lbcfg.values()) ):
    raise Exception("Loopback configuration keys and values overlap")

# set up injection ports
# keys are mapped from interface name to ofport number
# values are mapped from interface name to veth injection port name
def inj_port(x):
    basename = 'ethernet'
    if x.startswith(basename):
        return 'vet' + x[len(basename):].replace('/', ',') + 'j'
    else:
        raise Exception("Injection port name does not start with '%s'"
                        % basename)

port_map = { if2numcfg[k]: inj_port(v)
             for k,v in lbcfg.iteritems() if k in if2numcfg }
    
port_map1 = { if2numcfg[k]: if2numcfg[v]
             for k, v in lbcfg.iteritems() if k in if2numcfg }

def platform_config_update(config):
    """
    Update configuration for the remote platform

    @param config The configuration dictionary to use/update
    This routine defines the port map used for this configuration
    """

    global port_map
    config["port_map"] = port_map.copy()
    config["caps_table_idx"] = 0
    config['allow_user'] = True
    config['loopback'] = True
    config["port_map1"] = port_map1.copy()
