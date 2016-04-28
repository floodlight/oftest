"""
Platform configuration file
platform == vpi
"""

###############################################################################
#
# This platform module allows VPI port specifications on the command line. 
#
###############################################################################

import sys
import os
import argparse
import dppv

# The port specification is passed via the "--platform-args" option to OFTest. 
# Note that we must guard against abbreviations supported by argparse
if not "--platform-args" in " ".join(sys.argv):
    raise Exception("--platform-args must be specified")

ap = argparse.ArgumentParser("vpi")
ap.add_argument("--platform-args")
(ops, rest) = ap.parse_known_args()

vpi_port_map = {}
ports = ops.platform_args.split(",")
for ps in ports:
    (p, vpi) = ps.split("@")
    vpi_port_map[int(p)] = vpi

print vpi_port_map; 

def platform_config_update(config):
    """
    Update configuration for the remote platform

    @param config The configuration dictionary to use/update
    This routine defines the port map used for this configuration
    """

    global vpi_port_map
    config["port_map"] = vpi_port_map.copy()
    config["caps_table_idx"] = 0
    #
    # The class for DataPlanePorts must be specified here:
    #
    config['dataplane'] = { 'portclass': dppv.DataPlanePortVPI }
    config['allow_user'] = True
