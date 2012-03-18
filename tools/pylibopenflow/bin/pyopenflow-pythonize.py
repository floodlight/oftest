#!/usr/bin/env python
"""This script generate openflow-packets.py which
creates Python class for each data structure in openflow.h.

(C) Copyright Stanford University
Author ykk
Date December 2009
"""
import sys
#@todo Fix this include path mechanism
sys.path.append('./bin')
sys.path.append('./pylib')
import getopt
import openflow
import time
import output
import of.pythonize

def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" <options> output_file\n"+\
          "Options:\n"+\
          "-i/--input\n\tSpecify (non-default) OpenFlow header\n"+\
          "-t/--template\n\tSpecify (non-default) template file\n"+\
          "-h/--help\n\tPrint this usage guide\n"+\
          ""
          
#Parse options and arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hi:t:",
                               ["help","input","template"])
except getopt.GetoptError:
    usage()
    sys.exit(2)

#Check there is only output file
if not (len(args) == 1):
    usage()
    sys.exit(2)

#Parse options
##Input
headerfile=None
##Template file
templatefile=None
for opt,arg in opts:
    if (opt in ("-h","--help")):
        usage()
        sys.exit(0)
    elif (opt in ("-i","--input")):
        headerfile=arg
    elif (opt in ("-t","--template")):
        templatefile=arg
    else:
        print "Unhandled option:"+opt
        sys.exit(2)

#Generate Python code
ofmsg = openflow.messages(headerfile)
pynizer = of.pythonize.pythonizer(ofmsg)

fileRef = open(args[0], "w")
for x in pynizer.pycode(templatefile):
    fileRef.write(x+"\n")
fileRef.write("\n")
fileRef.close()
