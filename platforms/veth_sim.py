"""
Platform configuration file
platform == veth_sim
"""

###############################################################################
#
###############################################################################

import os
import sys
import argparse
import yaml

if not "--platform-args" in " ".join(sys.argv):
    raise Exception("--platform-args must be specified")

ap = argparse.ArgumentParser("veth_sim")
ap.add_argument("--platform-args")
(ops, rest) = ap.parse_known_args()

"""
sample veth-cfgfile:
eth1: eth1_oft
eth2: eth2_oft
eth3: eth3_oft

sample ifname2ofport-cfgfile:
eth1: 1
eth2: 2
eth3: 3
"""

args = ops.platform_args.split(",")
# first arg: veth mapping cfg file
# second arg: ifname to ofport number mapping cfg file
if len(args) != 2:
    raise Exception("Expecting <veth-cfgfile>,<ifname2ofport-cfgfile>")
vethcfgfile = args[0]
if2numcfgfile = args[1]

vethcfg = {}
if os.path.isfile(vethcfgfile):
    print(vethcfgfile)
    with open(vethcfgfile) as f:
        vethcfg = yaml.load(f)

if2numcfg = {}
if os.path.isfile(if2numcfgfile):
    print(if2numcfgfile)
    with open(if2numcfgfile) as f:
        if2numcfg = yaml.load(f)

port_map = { int(v) : vethcfg[k]
             for k, v in if2numcfg.items() if k in vethcfg}

print "Veth-sim port mapping"
print port_map

def platform_config_update(config):
    global port_map
    config["port_map"] = port_map.copy()
