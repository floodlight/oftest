"""
OpenFlow Test Framework

Configuration fragment

This file contains Python code to specify the configuration
of the system under test.

This is a work in progress.  The code below is for illustration only.

The configuration information is extensible in that any 
Python code may be added to this file (or its imports) and will 
be available to test cases.  

A platform identifier is given at the top of the file and most
other information is determined by testing this value.  Additional
files may also be imported based on the platform.

The configuration must specify a mapping from system interfaces
available to the test framework to OpenFlow port numbers on the
switch under test.  This is done in the interface_ofport_map
dictionary.  Future extensions may include specifying a driver
for the port (so as to allow remote packet generation) and to
specify a switch instance (to allow multiple switches to be
tested together).

Currently, the assumption is that ports are bidirectional, so
specifying "OF port 1 is connnected to eth2" implies this is so
for both TX and RX.

"""

import sys

##@var platform
# A string representing the platform under test.  Tested below
# for determining other variables.

##@var controller_host
# Gives the controller host address to use

##@var controller_port
# Gives the controller port to use

# platform = "sw_userspace"
# platform = "sw_kernelspace"
platform = "bcm_indigo"
# platform = "stanford_lb4g"


if platform == "sw_userspace":
    interface_ofport_map = {
        1 : "eth2",
        2 : "eth3",
        3 : "eth4",
        4 : "eth5"
        }
    controller_host = "172.27.74.158"
    controller_port = 7000

elif platform == "bcm_indigo":
    interface_ofport_map = {
        23 : "eth2",
        24 : "eth3",
        25 : "eth4",
        26 : "eth5"
        }
    # For SSH connections to switch
    controller_host = "192.168.2.2"
#    controller_host = "172.27.74.26"
    controller_port = 6634



# Debug levels
DEBUG_ALL = 0
DEBUG_VERBOSE = 1
DEBUG_INFO = 2
DEBUG_WARN = 3
DEBUG_ERROR = 4
DEBUG_CRITICAL = 5
DEBUG_NONE = 6 # For current setting only; not for string level

debug_level_default = DEBUG_WARN

dbg_string = [
    "DBG ALL  ",
    "VERBOSE  ",
    "INFO     ",
    "WARN     ",
    "ERROR    ",
    "CRITICAL "
    ]


# These can be moved into platform specific code if needed

RCV_TIMEOUT_DEFAULT = 10
RCV_SIZE_DEFAULT = 4096
CONTROLLER_HOST_DEFAULT = ''
CONTROLLER_PORT_DEFAULT = 6633

# Timeout in seconds for initial connection
INIT_CONNECT_TIMEOUT = 4

# Number of switch connection requests to queue
LISTEN_QUEUE_SIZE = 1

def debug_log(module, cur_level, level, string):
    """
    Log a debug message

    Compare the debug level to the current level and display
    the string if appropriate.
    @param module String representing the module reporting the info/error
    @param cur_level The module's current debug level
    @param level The level of the error message
    @param string String to report

    @todo Allow file logging options, etc
    @todo Add timestamps
    @todo Consider using the native Python logging module
    """

    if level >= cur_level:
        #@todo Support output redirection based on debug level
        print module + ":" + dbg_string[level] + ":" + string


def oft_assert(condition, string):
    """
    Test framework assertion check

    @param condition The boolean condition to check
    @param string String to print if error

    If condition is not true, it is considered a test framework
    failure and exit is called.

    This assert is meant to represent a violation in the 
    assumptions of how the test framework is supposed to work
    (for example, an inconsistent packet queue state) rather than
    a test failure.
    """
    if not condition:
        debug_log("OFT", debug_level_default, DEBUG_CRITICAL, 
                  "Internal error: " + string)
        sys.exit(1)

