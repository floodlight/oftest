#!/usr/bin/env python
"""This script fakes as n OpenFlow switch and
load the controller with k packets per second.

(C) Copyright Stanford University
Author ykk
Date January 2010
"""
import sys
import getopt
import struct
import openflow
import time
import output
import of.msg
import of.simu
import of.network
import dpkt.ethernet

def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" <options> controller\n"+\
          "Options:\n"+\
          "-p/--port\n\tSpecify port number\n"+\
          "-v/--verbose\n\tPrint message exchange\n"+\
          "-r/--rate\n\tSpecify rate per switch to send packets (default=1)\n"+\
          "-d/--duration\n\tSpecify duration of load test in seconds (default=5)\n"+\
          "-s/--switch\n\tSpecify number of switches (default=1)\n"+\
          "-h/--help\n\tPrint this usage guide\n"+\
          ""
          
#Parse options and arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hvp:s:d:r:",
                               ["help","verbose","port=",
                                "switch=","duration=","rate="])
except getopt.GetoptError:
    usage()
    sys.exit(2)

#Check there is only controller
if not (len(args) == 1):
    usage()
    sys.exit(2)
    
#Parse options
##Duration
duration = 5
##Rate
rate = 1.0
##Switch number
swno = 1
##Port to connect to
port = 6633
##Set output mode
output.set_mode("INFO")
for opt,arg in opts:
    if (opt in ("-h","--help")):
        usage()
        sys.exit(0)
    elif (opt in ("-v","--verbose")):
        output.set_mode("DBG")
    elif (opt in ("-p","--port")):
        port=int(arg)
    elif (opt in ("-s","--switch")):
        swno=int(arg)
    elif (opt in ("-d","--duration")):
        duration=int(arg)
    elif (opt in ("-r","--rate")):
        rate=float(arg)
    else:
        print "Unhandled option :"+opt
        sys.exit(2)

#Form packet
pkt = dpkt.ethernet.Ethernet()
pkt.type = dpkt.ethernet.ETH_MIN
pkt.dst = '\xFF\xFF\xFF\xFF\xFF\xFF'

#Connect to controller
ofmsg = openflow.messages()
parser = of.msg.parser(ofmsg)
ofnet = of.simu.network()
for i in range(1,swno+1):
    ofsw = of.simu.switch(ofmsg, args[0], port,
                          dpid=i,
                          parser=parser)
    ofnet.add_switch(ofsw)
    ofsw.send_hello()
    
output.info("Running "+str(swno)+" switches at "+str(rate)+\
            " packets per seconds for "+str(duration)+" s")

starttime = time.time()
running = True
interval = 1.0/(rate*swno)
ntime=time.time()+(interval/10.0)
swindex = 0
pcount = 0
rcount = 0
while running:
    ctime = time.time()
    time.sleep(max(0,min(ntime-ctime,interval/10.0)))

    if ((ctime-starttime) <= duration):
        #Send packet if time's up
        if (ctime >= ntime):
            ntime += interval
            pkt.src = struct.pack("Q",pcount)[:6]
            ofnet.switches[swindex].send_packet(1,10,pkt.pack()+'A'*3)
            pcount += 1
            swno += 1
            if (swno >= len(ofnet.switches)):
                swno=0

        #Process any received message
        (ofsw, msg) = ofnet.connections.msgreceive()
        while (msg != None):
            dic = ofmsg.peek_from_front("ofp_header", msg)
            if (dic["type"][0] == ofmsg.get_value("OFPT_FLOW_MOD")):
                output.dbg("Received flow mod")
                rcount += 1
            ofsw.receive_openflow(msg)
            (ofsw, msg) = ofnet.connections.msgreceive()
    else:
        running = False
    
output.info("Sent "+str(pcount)+" packets at rate "+\
            str(float(pcount)/float(duration))+" and received "+\
            str(rcount)+" back")
