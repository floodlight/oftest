# @author Jonathan Stout
from subprocess import Popen
import json
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
pubResults = False
 
def get_logger(name):
    global pubName
    pubName = name
    LOG = logging.getLogger(pubName)
    LOG.setLevel(logging.DEBUG)
    
    h = logging.FileHandler("oft.log")
    if should_publish():
        logDir = "%sresult/logs/%s" % (pubDir, pubName)
        os.makedirs(logDir)
        if should_publish():
            h = logging.FileHandler(logDir+"/trace.log")
    h.setLevel(logging.DEBUG)
    
    f = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    h.setFormatter(f)
    LOG.addHandler(h)
    return LOG
 
def start_wireshark():
    global wiresharkMap
    global pubDir
    global pubName
    if should_publish():
        for iface in wiresharkMap:
            fd = "%sresult/logs/%s/%s.pcap" % (pubDir, pubName, wiresharkMap[iface][1])
            wiresharkMap[iface][0] = Popen(["tshark", "-i", str(iface), "-w", fd, "-q"], stdout=None)
        
def stop_wireshark():
    global wiresharkMap
    if should_publish():
        for iface in wiresharkMap:
            wiresharkMap[iface][0].terminate()
 
def find_iface(addy):
    for iface in netifaces.interfaces():
        try:
            for a in netifaces.ifaddresses(iface)[netifaces.AF_INET]:
                if a['addr'] == addy:
                    return iface
        except KeyError:
            pass
    return None
 
def set_publish_directory(directory):
    global pubResults
    global pubDir
    pubResults = True
    pubDir = directory

def should_publish():
    global pubResults
    return pubResults
 
def set_wireshark_config(ctrlAddr, portMap):
    global wiresharkMap
    for k in portMap:
        iface = portMap[k]
        # [pid, dataX]
        wiresharkMap[iface] = [None, "data"+str(k)]
    # Controller's iface is not included in a config. Look it up.
    iface = find_iface(ctrlAddr)
    wiresharkMap[iface] = [None, "ctrl"]
 
def publish_asserts_and_results(res):
    asserts = {"errors" : {}, "failures" : {}, "skipped" : {}}
    results = {}
 
    for e in res.errors:
        asserts["errors"][e[0].__class__.__name__] = e[1]
    for f in res.failures:
        asserts["failures"][f[0].__class__.__name__] = f[1]
    # New in python 2.7
    #for s in res.skipped:
    #    asserts["skipped"][s[0].__class__.__name__] = s[1]
    # Publish asserts
    write_json_tofile(asserts, "asserts.json")
 
    results["run"] = res.testsRun
    results["errors"] = len(res.errors)
    results["failed"] = len(res.failures)
    # New in python 2.7
    #results["skipped"] = len(res.skipped)
    results["passed"] = results["run"] - (results["errors"]+results["failed"])
    # Publish results
    write_json_tofile(results, "results.json")

def write_json_tofile(data, fd):
    f = open(pubDir+"result/"+fd, "w")
    json.dump(data, f)
    f.close()

