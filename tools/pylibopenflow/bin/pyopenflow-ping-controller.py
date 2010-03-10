#!/usr/bin/env python
"""This script fakes as an OpenFlow switch to the controller

(C) Copyright Stanford University
Author ykk
Date October 2009
"""
import sys
import getopt
import openflow
import time
import output
import of.msg
import of.simu

def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" <options> controller\n"+\
          "Options:\n"+\
          "-p/--port\n\tSpecify port number\n"+\
          "-v/--verbose\n\tPrint message exchange\n"+\
          "-h/--help\n\tPrint this usage guide\n"+\
          ""
          
#Parse options and arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hvp:",
                               ["help","verbose","port="])
except getopt.GetoptError:
    usage()
    sys.exit(2)

#Check there is only controller
if not (len(args) == 1):
    usage()
    sys.exit(2)
    
#Parse options
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
    else:
        assert (False,"Unhandled option :"+opt)

#Connect to controller
ofmsg = openflow.messages()
parser = of.msg.parser(ofmsg)
ofsw = of.simu.switch(ofmsg, args[0], port,
                      dpid=int("0xcafecafe",16),
                      parser=parser)
ofsw.send_hello()
#Send echo and wait
xid = 22092009
running = True
ofsw.send_echo(xid)
starttime = time.time()
while running:
    msg = ofsw.connection.msgreceive(True, 0.00001)
    pkttime = time.time()
    dic = ofmsg.peek_from_front("ofp_header", msg)
    if (dic["type"][0] == ofmsg.get_value("OFPT_ECHO_REPLY") and
        dic["xid"][0] == xid):
        #Check reply for echo request
        output.info("Received echo reply after "+\
                    str((pkttime-starttime)*1000)+" ms", "ping-controller")
        running = False
    else:
        ofsw.receive_openflow(msg)
