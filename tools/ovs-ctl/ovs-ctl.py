#!/usr/bin/python

import os
import subprocess
import argparse
import sys
import signal
import time
import ConfigParser
import pprint

###############################################################################
#
# Arguments
#
# Arguments can be specified directly, or via config file. 
# TODO -- Make this a separate reusable class
#
################################################################################
gBasename = "ovs-ctl"

gConfigParser = argparse.ArgumentParser(description=gBasename, add_help=False)

gConfigParser.add_argument('-cf', '--config-file', 
                     help="Load settings from the given config file", 
                     nargs='+', metavar="FILE", 
                     default=os.path.expanduser("~/."+gBasename))

gConfigParser.add_argument('-c', '--config', 
                     help="Use the specified configuration section", 
                     default=None)

gConfigParser.add_argument('-d', '--default-config-file', 
                     help="Location of the local default config file", 
                     metavar="FILE", 
                     default="/opt/ovs/%s-default.conf" % (gBasename))

gConfigParser.add_argument('-nd', '--no-default', 
                     help="Do not load the default config file", 
                     action='store_true', default=False)
gConfigParser.add_argument('--dump-config',
                     help="Dump the loaded configuration settings", 
                     action='store_true', default=False)

#
# Parse the config files first, then parse remaining command line arguments
#
gConfig = ConfigParser.SafeConfigParser()
configArgs, remainingArgs = gConfigParser.parse_known_args()

if not configArgs.no_default:
    gConfig.read([configArgs.default_config_file])

if isinstance(configArgs.config_file, str):
    configFiles = [ configArgs.config_file]
else:
    configFiles = configArgs.config_file

configFiles = [ os.path.expanduser(x) if x.startswith('~') else x 
                for x in configFiles ]

gConfig.read(configFiles)

# Dump loaded config if requested
if configArgs.dump_config:
    for section in gConfig.sections():
        print section
        for option in gConfig.options(section):
            print " ", option, "=", gConfig.get(section, option)
    sys.exit()



#
# Functional arguments go here
#

#
# OVS target binaries -- these can all be specified individually. 
# If not specified, they are determined by the base directory settings
#
gParser = argparse.ArgumentParser(parents=[gConfigParser])

gParser.add_argument('--ovs-vswitchd-schema', 
                     help="""Path to the vswitchd.ovsschema file""")
gParser.add_argument('--ovs-vswitchd-log', 
                     help="""Path to the vswitchd log file""")
gParser.add_argument('--ovs-vswitchd', 
                     help="""Path to the target ovs-vswitchd binary""")
gParser.add_argument('--ovs-vsctl', 
                     help="""Path to the target ovs-vsctl binary""")
gParser.add_argument('--ovs-ofctl', 
                     help="""Path to the target ovs-ofctl binary""")
gParser.add_argument('--ovsdb-tool', 
                     help="""Path to the target ovsdb-tool binary""")
gParser.add_argument('--ovsdb-server', 
                     help="""Path to the target ovsdb-server binary""")
gParser.add_argument('--ovs-kmod', 
                     help="""Path to the OVS kernel module""")
gParser.add_argument('--ovs-src-dir',
                     help="""Directory for the OVS Source Files""")

gParser.add_argument('--ovs-log-dir',
                     help="""Directory for the OVS Runtime Log Files""")

gParser.add_argument('--ovs-version')

gParser.add_argument("--ovs-base-dir", help="OVS Base Installation Directory")

gParser.add_argument("--ovs-runtime-dir", 
                     help="OVS Runtime Directory", 
                     default="/var/run/ovs")

gParser.add_argument('--ovs-db-sock', 
                     help="Domain Socket Location")
                     
gParser.add_argument('--ovs-db-file', 
                     help="Location for the OVS database file")


#
# Logging/Debugging/Testing options
#
gParser.add_argument('--dry', 
                     help="""Dry run only. Don't actually do anything""", 
                     action='store_true',  default=False)

gParser.add_argument('--log', 
                     help='Enable logging', 
                     action='store_true', default=False)

gParser.add_argument('--verbose', 
                     help='Enable verbose output information', 
                     action='store_true', default=False)

gParser.add_argument("--kill", help="Kill running OVS", 
                     default=False, action='store_true')

gParser.add_argument("--keep-veths", 
                     help="""By default, all existing veths will be destroyed and
the veth module removed before initializing. If you don't want the veth module
removed, specify this argument. Your mileage may vary if you use this.""", 
                     default=False, action='store_true')

gParser.add_argument("--no-kmod", 
                     help="""Do not attempt to insert or remove the OVS kernel module. 
Your mileage may vary.""", 
                     default=False, action='store_true')

gParser.add_argument("--vlog", 
                     help="""Tail the running vswitch.log file in a new xterm""", 
                     default=False, action='store_true')

#
# Runtime and setup arguments
#
gParser.add_argument('-p', '--port-count', type=int, 
                     help="Number of veth ports to connect.", 
                     default='4')


gParser.add_argument("--bridge", help="Name of OF OVS Bridge", 
                     default="ofbr0")

gParser.add_argument("--cip", help="Controller Connection", 
                     default="127.0.0.1")

gParser.add_argument("--cport", type=int, help="Controller Port", 
                     default=6633)

gParser.add_argument("--max_backoff", help="VSwitchD max backoff value", 
                     default=1000, type=int)


gParser.add_argument("--keep-db", 
                     help="""By default, a new database is initialized at each
execution. If you want to keep and use the old database (if it exists), 
use this option""", 
                     action='store_true', default=False)


gParser.add_argument("--cli", 
                     help="Run the ovs-ctl cli after initialization", 
                     action='store_true', default=False)

gParser.add_argument("--teardown", 
                     help="Kill OVS instance after CLI exits", 
                     action='store_true', default=False)

#
# Reset defaults based on config files and override
#
# Anything in the "Defaults" section gets slurped first:
defaults = {}
if gConfig.has_section('Defaults'):
    defaults = dict(gConfig.items('Defaults'))
    gParser.set_defaults(**defaults)

#
# The configuration to execute might be specified in on the command line, or in the Defaults section(s)
# of the config files. 
#
# If its specified on the command line, it will be present in configArgs.config
# If its specified in the section, it will only be present in the defaults dict. 
# Need to check both. Command line takes precedence. 
#
gConfigSection = None
if configArgs.config != None:
    gConfigSection = configArgs.config
elif defaults.has_key('config'):
    gConfigSection = defaults['config']


if gConfigSection != None:
    if gConfig.has_section(gConfigSection):
        section = dict(gConfig.items(gConfigSection))
        gParser.set_defaults(**section)
    else:
        print >>sys.stderr, "Requestion configuration '%s' does not exist" % (configArgs.config)
        sys.exit()


###############################################################################
# 
# Done with argument setup. Parser remaining arguments
#
###############################################################################
gArgs = gParser.parse_args(remainingArgs)


#
# At the end of all of this, we need the following things to be defined
# or derived:
#
gRequiredOptions = [
    [ 'ovs_vswitchd_schema', 'ovs_src_dir',     '/vswitchd/vswitch.ovsschema', True,  True  ], 
    [ 'ovs_vswitchd',        'ovs_base_dir',    '/sbin/ovs-vswitchd',          True,  True  ], 
    [ 'ovs_vsctl',           'ovs_base_dir',    '/bin/ovs-vsctl',              True,  True  ], 
    [ 'ovs_ofctl',           'ovs_base_dir',    '/bin/ovs-ofctl',              True,  True  ], 
    [ 'ovsdb_tool',          'ovs_base_dir',    '/bin/ovsdb-tool',             True,  True, ], 
    [ 'ovsdb_server',        'ovs_base_dir',    '/sbin/ovsdb-server',          True,  True, ], 
    [ 'ovs_db_file',          'ovs_base_dir',    '/ovs.db',                    False, True, ], 
    [ 'ovs_db_sock',         'ovs_runtime_dir', '/db.sock',                    False, True, ], 
    [ 'ovs_kmod',            'ovs_base_dir',    '/sbin/openvswitch_mod.ko',    True,  not gArgs.no_kmod ], 
]

def __require_option(key, basedir, path, exists=True):
    value = getattr(gArgs, key)
    if value is None:
        # Unspecified -- try to default based on given path
        value = getattr(gArgs, basedir)

        if value is None:
            return False

        value += path

    if exists and not os.path.exists(value):
        return False

    if gArgs.verbose:
        print '--v-- option: %s @ %s' % (key, value)

    setattr(gArgs, key, value)


Validated = True
# Try to validate as many things as we can
for option in gRequiredOptions:
    if option[4]:
        if __require_option(option[0], option[1], option[2], option[3]) == False:
            Validated = False

# If any of them failed, try to be as helpful as possible
if Validated == False:
    print >>sys.stdout, "\nConfiguration problem. One or more required settings are missing or could not be derived:\n"
    for option in gRequiredOptions:
        if option[4] is False:
            continue

        value = getattr(gArgs, option[0])
        if value:
            print >>sys.stdout, " %s: %s" % (option[0], value), 
            if option[3] and not os.path.exists(value):
                print >>sys.stdout, "-- does not exist"
            else:
                print "(OK)"
        else:
            print >>sys.stdout, " %s: Unknown. " % (option[0]), 
            base = getattr(gArgs, option[1])
            if base:
                print >>sys.stdout, "Search path was '%s'." % (base + option[2])
            else:
                print >>sys.stdout, "Could not derive path because '%s' was also unspecified." % (option[1])
    print >>sys.stdout
    sys.exit()




#
# If we aren't in a dry run, you must execute as root to accompish anything
#
if not os.geteuid() == 0 and gArgs.dry == False:
    print >>sys.stderr, "Must run as root to accomplish any of this."
    sys.exit()


###############################################################################
#
# Helpers 
#
###############################################################################

def createVeths(count):
    for idx in range(0, count):
        lcall(["/sbin/ip", "link", "add", "type", "veth"])

def vethsUp(count):
    for idx in range(0, count*2):
        lcall(["/sbin/ifconfig", 'veth%s' % (idx), "up"])

def lcall(cmd, log=gArgs.log, dry=gArgs.dry, popen=False, 
          pidFile=None):
    
    if log or gArgs.verbose:
        print "%s: %s" % ('popen' if popen else 'call', cmd)
    
    if not dry:
        if not popen:
            subprocess.call(cmd)
        else:
            p = subprocess.Popen(cmd)
            if pidFile != None:
                pidf = open(pidFile, "w"); 
                print >>pidf, p.pid
                pidf.close()

    

def vsctl(argsList):
    argsList.insert(0, "--db=unix:%s" % (gArgs.ovs_db_sock))
    argsList.insert(0, gArgs.ovs_vsctl)
    lcall(argsList)

def ofctl(argsList):
    argsList.insert(0, gArgs.ovs_ofctl)
    lcall(argsList)

def killpid(pid):
    try:
        os.kill(pid, signal.SIGTERM)
        return False
    except OSError, e:
        return True


def killp(pidfile):
    if os.path.exists(pidfile):
        pid=int(open(pidfile).read())
        print "Killing %s, pid=%s..." % (pidfile, pid),
        if not gArgs.dry:
            while not killpid(pid):
                time.sleep(1)
                pass
        print "dead"


###############################################################################
#
# main
#
###############################################################################

gServerPid = gArgs.ovs_runtime_dir + "/ovsdb-server.pid"
gSwitchPid = gArgs.ovs_runtime_dir + "/ovs-vswitchd.pid"
gLogPid=     gArgs.ovs_runtime_dir + "/ovs-vswitchd-tail.pid"

# Kill previous execution based on contents of the runtime dir
if os.path.exists(gServerPid):
    print gServerPid
    vsctl(["del-br", gArgs.bridge])


def killall():
    # Kill existing DB/vswitchd
    killp(gSwitchPid)
    killp(gServerPid)
    killp(gLogPid)

    # Remove old logpid file, since this does not happen automagically
    if os.path.exists(gLogPid):
        os.remove(gLogPid)

    if gArgs.keep_veths == False:
        lcall(['/sbin/rmmod', 'veth'])
        lcall(['/sbin/modprobe', 'veth'])

    # Remove kmod
    lcall(['/sbin/rmmod', gArgs.ovs_kmod])


killall()
if gArgs.kill == True:
    # Don't do anything else
    sys.exit()


# Remove bridge module
lcall(['/sbin/rmmod', 'bridge'])
# Insert openvswitch module
lcall(['/sbin/insmod', gArgs.ovs_kmod])

createVeths(gArgs.port_count)
vethsUp(gArgs.port_count)

if not os.path.exists(gArgs.ovs_db_file) or gArgs.keep_db == False:
    print "Initializing DB @ %s" % (gArgs.ovs_db_file)
    if os.path.exists(gArgs.ovs_db_file) and not gArgs.dry:
        os.remove(gArgs.ovs_db_file)

    lcall([gArgs.ovsdb_tool, "create", gArgs.ovs_db_file, 
           gArgs.ovs_vswitchd_schema])
else:
    print "Keeping existing DB @ %s" % (gArgs.ovs_db_file)


if not os.path.exists(gArgs.ovs_runtime_dir):
    os.makedirs(gArgs.ovs_runtime_dir)

# Start dbserver
lcall([gArgs.ovsdb_server, gArgs.ovs_db_file, 
       "--remote=punix:%s" % (gArgs.ovs_db_sock), 
       "--detach", "--pidfile=%s" % (gServerPid)])

# Init db
vsctl(["--no-wait", "init"])

# Start vswitchd
startV = [ gArgs.ovs_vswitchd, 
          "unix:%s" % (gArgs.ovs_db_sock), 
          "--verbose", "--detach",
          "--pidfile=%s" % (gSwitchPid) ]

if gArgs.ovs_vswitchd_log:
    startV.append("--log-file=%s" % (gArgs.ovs_vswitchd_log))

lcall(startV)

if gArgs.vlog:
    lcall(["xterm", "-T", "vswitchd-log", "-e", "tail", "-f", 
           gArgs.ovs_vswitchd_log], 
          popen=True, pidFile=gLogPid)


# Add a bridge
vsctl(["add-br", gArgs.bridge])
ofctl(["show", gArgs.bridge])

# Add Veths to bridge
for idx in range(0, gArgs.port_count):
    vsctl(["add-port", gArgs.bridge, "veth%s" % (idx*2)])


# Set controller
vsctl(["set-controller", gArgs.bridge, "tcp:%s:%s" % (
        gArgs.cip, gArgs.cport)])

# Minimize default backoff for controller connections
vsctl(["set", "Controller", gArgs.bridge, 
       "max_backoff=%s" % (gArgs.max_backoff)])


ofctl(["show", gArgs.bridge])


if gArgs.cli:
    while True:
        cmd = raw_input("[%s] ovs-ctl> " % gConfigSection)
        if cmd and cmd != "":
            args = cmd.split(" ")
            if args[0] == "vsctl" or args[0] == "ovs-vsctl":
                vsctl(args[1:])
            elif args[0] == "ofctl" or args[0] == "ovs-ofctl":
                ofctl(args[1:])
            elif args[0] == "exit" or args[0] == "quit":
                break; 
            elif args[0] == "kill":
                gArgs.teardown = True
                break
            else:
                print "unknown command '%s'" % args[0]
            

if gArgs.teardown:
    print "Killing OVS"
    killall()




                        
            
