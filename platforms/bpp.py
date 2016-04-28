"""
Platform configuration file
platform == bpp
"""

###############################################################################
#
# This platform assumes BPP VPI specifications on the command line. 
#
###############################################################################

import sys
import os
import argparse
import subprocess
import dppv

# The port specification is passed via the "--platform-args" option to OFTest. 
# Note that we must guard against abbreviations supported by argparse
if not "--platform-args" in " ".join(sys.argv):
    raise Exception("--platform-args must be specified")

ap = argparse.ArgumentParser("bpp")
ap.add_argument("--platform-args")
(ops, rest) = ap.parse_known_args()

if not "@" in ops.platform_args:
    # Assume it is just a device name. Get the ports from the track database. 
    if "," in ops.platform_args:
        (type_, d) = ops.platform_args.split(",")
    else:
        (type_, d) = ("udp", ops.platform_args)

    trackScript = "/usr/bin/track"
    if not os.path.exists(trackScript):
        raise Exception("Cannot find the track script (looked at %s" % trackScript)

    ports = eval("[" + subprocess.check_output([trackScript, "getports", d]) + "]")
    ops.platform_args = type_ + "," + ",".join( "%s@%s:%s" % (p, d, p) for p in ports)

    print "new platform_args: ", ops.platform_args
    exit;
#
###############################################################################

vpi_port_map = {}
ports = ops.platform_args.split(",")
bpptype = "udp"
if ports[0] == "udp" or ports[0] == "tcp":
    bpptype = ports.pop(0)

for ps in ports:
    (p, vpi) = ps.split("@")
    vpi_port_map[int(p)] = "bpp|%s|%s" % (bpptype, vpi)

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
