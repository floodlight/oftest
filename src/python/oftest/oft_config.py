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

##@var platform
# A string representing the platform under test.  Tested below
# for determining other variables.

##@var switch_cxn_type
# How does the test framework communicate to the switch?
#
# Options include:
# @arg localhost:   Switch is running on same host as tests
# @arg ssh:         Use paramiko to control ssh connection. Needs switch
# IP and other params
#
# For ssh, additional variables include
# @arg switch_ip = "192.168.2.21"
# @arg switch_username = "root"
# @arg switch_password

##@var switch_init
# A function to be called to initialize the switch.  May be None
# to indicate no such function needs to be called.

##@var switch_connect
# Function to be called to prompt the switch to connect to the
# controller.  The function may need to maintain connection state 
# as it could be called multiple times between disconnects.

##@var switch_disconnect
# Function to be called to force the switch to disconnect from the
# controller. 

##@var controller_ip
# Gives the controller IP address to use

##@var controller_port
# Gives the controller port to use

platform = "sw_userspace"
# platform = "sw_kernelspace"
# platform = "bcm_indigo"
# platform = "stanford_lb4g"

if platform == "sw_userspace":
    interface_ofport_map = {
        1 : "eth2",
        2 : "eth3",
        3 : "eth4",
        4 : "eth5"
        }
    switch_cxn_type = "localhost"
    switch_init = None  # TBD
    switch_connect = None  # TBD
    switch_disconnect = None  # TBD
    controller_ip = "172.27.74.158"
    controller_port = 7000

elif platform == "bcm_indigo":
    switch_cxn_type = "ssh"
    switch_ip = "192.168.2.21"
    switch_username = "root"
    switch_password = "OpenFlow"
    switch_init = None  # TBD
    switch_connect = None  # TBD
    switch_disconnect = None  # TBD
    controller_ip = "172.27.74.158"
    controller_port = 7000
