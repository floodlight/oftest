"""
Platform configuration file
platform == veth_inject
"""

###############################################################################
#
# This platform assumes the loopback configuration file is specified
# on the command line. 
#
###############################################################################

import sys
import os
import argparse
import subprocess
import json

# The loopback port specification is passed via the "--platform-args"
# option to OFTest. 
# Note that we must guard against abbreviations supported by argparse
if not "--platform-args" in " ".join(sys.argv):
    raise Exception("--platform-args must be specified")

ap = argparse.ArgumentParser("veth_inject")
ap.add_argument("--platform-args")
(ops, rest) = ap.parse_known_args()

###############################################################################
# --platform-args=cfgfile[,reverse]

"""
sample config file specifying loopback connections between the given interfaces
{
   "ethernet29": "ethernet30",
   "ethernet19": "ethernet20",
   "ethernet21": "ethernet22",
   "ethernet15": "ethernet16",
   "ethernet23": "ethernet24",
   "ethernet31": "ethernet32",
   "ethernet25": "ethernet26",
   "ethernet11": "ethernet12",
   "ethernet27": "ethernet28",
   "ethernet13": "ethernet14",
   "ethernet9": "ethernet10",
   "ethernet3": "ethernet4",
   "ethernet1": "ethernet2",
   "ethernet7": "ethernet8",
   "ethernet5": "ethernet6",
   "ethernet17": "ethernet18"
}
"""

args = ops.platform_args.split(",")
# 1 arg: cfg file
# 2 or more args: cfg file, 'reverse' keyword, rest ignored
if len(args) == 0:
    raise Exception("No config file specified")
if len(args) == 1:
    cfgfile = args[0]
    reverse = False
else:
    cfgfile = args[0]
    reverse = (args[1] == 'reverse')

# read config file
if os.path.isfile(cfgfile):
    with open(cfgfile) as f:
        cfg = json.load(f)
else:
    cfg = {}

# set up injection ports based on keys or values
basename = 'ethernet'
# 'reverse' swaps key with value
if reverse:
    port_map = { int(v[len(basename):]):
                 'vet'+k[len(basename):].encode('ascii','ignore')+'j'
                 for k,v in cfg.iteritems() if v.startswith(basename)}
else:
    port_map = { int(k[len(basename):]):
                 'vet'+v[len(basename):].encode('ascii','ignore')+'j'
                 for k,v in cfg.iteritems() if k.startswith(basename)}
    
print port_map

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
