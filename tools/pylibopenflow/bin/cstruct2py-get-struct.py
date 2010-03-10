#!/usr/bin/env python
"""This script reads struct from C/C++ header file and output query

Author ykk
Date June 2009
"""
import sys
import getopt
import cheader
import c2py


def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" <options> header_files... struct_name\n"+\
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

#Check there is at least 1 input file and struct name
if (len(args) < 2):
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
        print "Unhandled option :"+opt
        sys.exit(1)

headerfile = cheader.cheaderfile(args[:-1])
cstruct = headerfile.structs[args[-1].strip()]
cs2p = c2py.cstruct2py()
pattern = cs2p.get_pattern(cstruct)

#Print C struct
if (printc):
    print cstruct

#Print pattern
print "Python pattern = "+pattern

#Print name
if (printname):
    print cstruct.get_names()

#Print size
if (printsize):
    print "Size = "+str(cs2p.get_size(pattern))
