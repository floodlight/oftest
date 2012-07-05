#!/usr/bin/env python
"""This script reads struct from OpenFlow header file and output query

(C) Copyright Stanford University
Author ykk
Date October 2009
"""
import sys
import getopt
import openflow

def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" <options> struct_name\n"+\
          "Options:\n"+\
          "-h/--help\n\tPrint this usage guide\n"+\
          "-c/--cstruct\n\tPrint C struct\n"+\
          "-n/--name\n\tPrint names of struct\n"+\
          "-s/--size\n\tPrint size of struct\n"+\
          ""
          
#Parse options and arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hcsn",
                               ["help","cstruct","size","names"])
except getopt.GetoptError:
    usage()
    sys.exit(2)

#Check there is only struct name
if not (len(args) == 1):
    usage()
    sys.exit(2)
    
#Parse options
##Print C struct
printc = False
##Print names
printname = False
##Print size
printsize = False
for opt,arg in opts:
    if (opt in ("-h","--help")):
        usage()
        sys.exit(0)
    elif (opt in ("-s","--size")): 
        printsize = True
    elif (opt in ("-c","--cstruct")): 
        printc = True
    elif (opt in ("-n","--names")): 
        printname = True
    else:
        assert (False,"Unhandled option :"+opt)

pyopenflow = openflow.messages()
cstruct = pyopenflow.structs[args[0].strip()]
pattern = pyopenflow.get_pattern(cstruct)

#Print C struct
if (printc):
    print cstruct

#Print pattern
print "Python pattern = "+str(pattern)

#Print name
if (printname):
    print cstruct.get_names()

#Print size
if (printsize):
    print "Size = "+str(pyopenflow.get_size(pattern))

