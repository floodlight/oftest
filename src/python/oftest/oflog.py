# @author Jonathan Stout
from subprocess import Popen
import logging
import netifaces
import os
 
"""
oflog.py
Provides Loggers for oftest cases, and easy to use wireshark
logging.
 
Test case writers use three main functions.
1. get_logger(name) - Returns a Logger for testcase name.
2. start_wireshark - Starts a tshark capture on each network
interface.
3. stop_wireshark - Terminates each running wireshark capture.
 
oflog is configured using two methods.
1. set_publish_directory(directory) - Records all logs under
directory. directory *must* end in '/'. 
2. set_wireshark_config(ctrlAddr, portMap) - Configures
wireshark to log the interface associated with ctrlAddr and all
other data plane interfaces.
 
oflog also creates a test result summary from the result of
unittest.TextTestRunner(...).run(...). record_summary creates
two files.
1. assert.json - which contains a trace of each failed testcase and
testcase error...
{ "Grp100No160" : "trace..." }
 
2. results.json - which contains a dict of tests_run, skipped, and
failed tests...
{ "Grp100No160" : { "tests_run" : 0 }, { "skipped" : [...] },
{ "failed" : [...] } }
1. record_summary(result)
"""
 
pubDir = ""
pubName = ""
wiresharkMap = {}
 
def get_logger(name):
    global pubName
    pubName = name
    LOG = logging.getLogger(pubName)
    LOG.setLevel(logging.DEBUG)
    
    logDir = "%slogs/%s" % (pubDir, pubName)
    os.makedirs(logDir)
    h = logging.FileHandler(logDir+"/trace.log")
    h.setLevel(logging.DEBUG)
    
    f = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    h.setFormatter(f)
    LOG.addHandler(h)
    return LOG
 
def start_wireshark():
    global wiresharkMap
    global pubDir
    for iface in wiresharkMap:
        fd = "%slogs/%s/%s.pcap" % (pubDir, pubName, iface)
        wiresharkMap[iface] = Popen(["tshark", "-i", iface, "-w", fd, "-q"], stdout=None)
        
def stop_wireshark():
    global wiresharkMap
    for iface in wiresharkMap:
        wiresharkMap[iface].terminate()
 
def find_iface(addy):
    for iface in netifaces.interfaces():
        for a in netifaces.ifaddresses(iface)[netifaces.AF_INET]:
            if a['addr'] == addy:
                return iface
    return None
 
def set_publish_directory(directory):
    global pubDir
    pubDir = directory
 
def set_wireshark_config(ctrlAddr, portMap):
    global wiresharkMap
    for k in portMap:
        iface = portMap[k]
        wireshark[iface] = None
    # Controller's iface is not included in a config. Look it up.
    iface = find_iface(ctrlAddr)
    wireshark[iface] = None
 
def publish_asserts_and_results(res):
    asserts = {"errors" : {}, "failures" : {}, "skipped" : {}}
    results = {}
 
    for e in res.errors():
        asserts["errors"][e[0].__name__] = e[1]
    for f in res.failures():
        asserts["failures"][f[0].__name__] = f[1]
    for s in res.skipped():
        asserts["skipped"][s[0].__name__] = s[1]
    # Publish asserts
 
    results["run"] = res.testsRun()
    results["errors"] = len(res.errors())
    results["failed"] = len(res.failures())
    results["skipped"] = len(res.skipped())
    results["passed"] = results["run"] - (results["errors"]+results["failed"]+results["skipped"])
    # Publish results
