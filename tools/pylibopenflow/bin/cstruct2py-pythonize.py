#!/usr/bin/env python
"""This script reads struct

Author ykk
Date Jan 2010
"""
import sys
import getopt
import cpythonize
import cheader

def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" <options> header_files... output_file\n"+\
          "Options:\n"+\
          "-h/--help\n\tPrint this usage guide\n"+\
          ""

#Parse options and arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "h",
                               ["help"])
except getopt.GetoptError:
    usage()
    sys.exit(2)
   
#Parse options
for opt,arg in opts:
    if (opt in ("-h","--help")):
        usage()
        sys.exit(0)
    else:
        print "Unhandled option :"+opt
        sys.exit(2)

#Check there is at least 1 input file with 1 output file
if (len(args) < 2):
    usage()
    sys.exit(2)

ch = cheader.cheaderfile(args[:-1])
py = cpythonize.pythonizer(ch)
fileRef = open(args[len(args)-1], "w")
for l in py.pycode():
    fileRef.write(l+"\n")
fileRef.close()

