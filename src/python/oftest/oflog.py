# @author Jonathan Stout
from subprocess import Popen, PIPE
import json
import logging
import os
import time
from oftest import config
 
"""
oflog.py
Provides Loggers for oftest cases, and easy to use wireshark
logging.
 
Test case writers use three main functions.
1. get_logger() - Returns a Logger for each testcase or the
default logger if --publish is not passed.
2. @wireshark_capture - Decorator Uses tshark to capture network
traffic while function is being run.
 
oflog is configured using one method.
1. set_config() - Records all logs under directory. directory
*must* end in '/'. Also configures wireshark to log the interface
associated with ctrlAddr and all other data plane interfaces.
"""
 
pubName = ""
wiresharkMap = {}
DEVNULL = None

def wireshark_capture(f):
    """
    Decorator to wrap Testcases. Gives
    a one second buffer for wireshark to
    start and stop if publishing is enabled.
    """
    def pub(*args, **kargs):
        create_log_directory(str(args[0].__class__.__name__))
        start_wireshark()
        time.sleep(3)
        try:
            f(*args, **kargs)
        finally:
            stop_wireshark()
            time.sleep(3)

    if config["publish"] is None:
        return f
    else:
        return pub

def create_log_directory(dirName):
    """
    Creates a directory named dirName. Also save dirName as a
    global variable to inform get_logger() where to log to.
    """
    global pubName
    pubName = dirName
    logDir = "%slogs/%s" % (config["publish"], pubName)
    try:
        Popen(["rm", "-rf", logDir],stdout=None)
        time.sleep(1)
    except:
        pass
    finally:
        os.makedirs(logDir)

def get_logger():
    if config["publish"] is None:
        return logging
    LOG = logging.getLogger(pubName)
    LOG.setLevel(config["dbg_level"])
    logDir = "%slogs/%s" % (config["publish"], pubName)
    h = logging.FileHandler(logDir+"/testcase.log")
    h.setLevel(logging.DEBUG)
    
    f = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    h.setFormatter(f)
    LOG.addHandler(h)
    return LOG
 
def start_wireshark():
    for iface in wiresharkMap:
        fd = "%slogs/%s/%s.pcap" % (config["publish"], pubName, wiresharkMap[iface][1])
        wiresharkMap[iface][0] = Popen(["tshark", "-i", str(iface), "-w", fd, "-q"], stdout=DEVNULL, stderr=DEVNULL)

def stop_wireshark():
    for iface in wiresharkMap:
        wiresharkMap[iface][0].terminate()

def set_config():
    if config["publish"] is None:
        return
    global wiresharkMap
    global DEVNULL
    DEVNULL = open(os.devnull, 'w')

    for k in config["port_map"]:
        iface = config["port_map"][k]
        # [pid, "dataX"]
        wiresharkMap[iface] = [None, "data"+str(k)]
    # Controller's iface is not included in a config. Look it up.
    iface = find_iface(config["controller_host"])
    wiresharkMap[iface] = [None, "ctrl"]

def find_iface(ip="127.0.0.1"):
    """
    Parses ifconfig to return the interface associated with ip.
    """
    p = Popen(["ifconfig | grep 'Link\|inet\|mtu'"], shell=True, stdout=PIPE)
    data = p.communicate()[0]
    data = data.split("\n")[:-1]
    interface = None

    for line in data:
        a = line.strip(" \t").split(" ")
        # Note the interface
        if "Link" in a or "mtu" in a:
            interface = a[0].strip(":")
        # Find the right IP
        if a[0] == "inet" and a[1].strip("addr:") == ip:
            return interface
