# @author Jonathan Stout
from subprocess import Popen
import json
import logging
import netifaces
import os
import time
 
"""
oflog.py
Provides Loggers for oftest cases, and easy to use wireshark
logging.
 
Test case writers use three main functions.
1. get_logger() - Returns a Logger for each testcase.
2. @wireshark_capture decorator Uses tshark to capture network
traffic while function is being run.
 
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

def wireshark_capture(f):
    """
    Decorator to wrap Testcases. Gives
    a one second buffer for wireshark to
    start and stop if publishing is enabled.
    """
    def pub(*args, **kargs):
        create_log_directory(str(args[0].__class__.__name__))
        start_wireshark()
        time.sleep(1)
        f(*args, **kargs)
        stop_wireshark()
        time.sleep(1)
    global pubResults
    if pubResults:
        return pub
    else:
        return f

def create_log_directory(dirName):
    global pubDir
    global pubName
    pubName = dirName
    logDir = "%sresult/logs/%s" % (pubDir, pubName)
    try:
        Popen(["rm", "-rf", logDir],stdout=None)
        time.sleep(1)
    except:
        pass
    finally:
        os.makedirs(logDir)

def get_logger():
    LOG = logging.getLogger(pubName)
    LOG.setLevel(logging.DEBUG)
    
    h = logging.FileHandler("oft.log")
    if should_publish():
        logDir = "%sresult/logs/%s" % (pubDir, pubName)
        h = logging.FileHandler(logDir+"/trace.log")
    h.setLevel(logging.DEBUG)
    
    f = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    h.setFormatter(f)
    LOG.addHandler(h)
    return LOG
 
def start_wireshark():
    for iface in wiresharkMap:
        fd = "%sresult/logs/%s/%s.pcap" % (pubDir, pubName, wiresharkMap[iface][1])
        wiresharkMap[iface][0] = Popen(["tshark", "-i", str(iface), "-w", fd, "-q"], stdout=None)

def stop_wireshark():
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
    return pubResults
 
def set_config(ctrlAddr, portMap):
    global wiresharkMap
    for k in portMap:
        iface = portMap[k]
        # [pid, "dataX"]
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
    write_json_tofile(asserts, "asserts.json")
 
    results["run"] = res.testsRun
    results["errors"] = len(res.errors)
    results["failed"] = len(res.failures)
    results["passed"] = results["run"] - (results["errors"]+results["failed"])
    results["skipped"] = results["run"] - (results["errors"]+results["failed"]+results["passed"])
    # Publish results
    write_json_tofile(results, "results.json")

def write_json_tofile(data, fd):
    f = open(pubDir+"result/"+fd, "w")
    json.dump(data, f)
    f.close()
