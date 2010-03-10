#!/usr/bin/env python
"""This script generate class files for messenger and lavi in NOX, 
specifically it creates a Python class for each data structure.

(C) Copyright Stanford University
Author ykk
Date January 2010
"""
import sys
import os.path
import getopt
import cheader
import lavi.pythonize

def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" <options> nox_dir\n"+\
          "Options:\n"+\
          "-i/--input-dir\n\tSpecify input directory (nox src directory)\n"+\
          "-t/--template\n\tSpecify (non-default) template file\n"+\
          "-n/--no-lavi\n\tSpecify that LAVI's file will not be created\n"+\
          "-h/--help\n\tPrint this usage guide\n"+\
          ""
          
#Parse options and arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hm:n",
                               ["help","messenger-template","no-lavi"])
except getopt.GetoptError:
    usage()
    sys.exit(2)

#Check there is only NOX directory given
if not (len(args) == 1):
    usage()
    sys.exit(2)

#Parse options
##Output LAVI
outputlavi=True
##Template file
templatefile="include/messenger.template.py"
for opt,arg in opts:
    if (opt in ("-h","--help")):
        usage()
        sys.exit(0)
    elif (opt in ("-t","--template")):
        templatefile=arg
    elif (opt in ("-n","--no-lavi")):
        outputlavi=False
    else:
        print "Unhandled option:"+opt
        sys.exit(2)

#Check for header file in NOX directory
if not (os.path.isfile(args[0]+"/src/nox/coreapps/messenger/message.hh")):
    print "Messenger header file not found!"
    sys.exit(2)
if (outputlavi):
    if not (os.path.isfile(args[0]+"/src/nox/netapps/lavi/lavi-message.hh")):
        print "LAVI message header file not found!"
        sys.exit(2)

#Get headerfile and pythonizer
msgheader = cheader.cheaderfile(args[0]+"/src/nox/coreapps/messenger/message.hh")
mpynizer = lavi.pythonize.msgpythonizer(msgheader)
if (outputlavi):
    laviheader = cheader.cheaderfile([args[0]+"/src/nox/coreapps/messenger/message.hh",
                                      args[0]+"/src/nox/netapps/lavi/lavi-message.hh"])
    lpynizer = lavi.pythonize.lavipythonizer(laviheader)
    
#Generate Python code for messenger
fileRef = open(args[0]+"/src/nox/coreapps/messenger/messenger.py", "w")
for x in mpynizer.pycode(templatefile):
    fileRef.write(x+"\n")
fileRef.write("\n")
fileRef.close()

if (outputlavi):
    fileRef = open(args[0]+"/src/nox/netapps/lavi/lavi.py", "w")
    for x in lpynizer.pycode(templatefile):
        fileRef.write(x.replace("def __init__(self,ipAddr,portNo=2603,debug=False):",
                                "def __init__(self,ipAddr,portNo=2503,debug=False):").\
                      replace("def __init__(self, ipAddr, portNo=1304,debug=False):",
                              "def __init__(self, ipAddr, portNo=1305,debug=False):")+\
                      "\n")
    fileRef.write("\n")
    fileRef.close()
