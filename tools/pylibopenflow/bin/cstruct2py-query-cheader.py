#!/usr/bin/env python
"""This script reads C/C++ header file and output query

Author ykk
Date June 2009
"""
import sys
import getopt
import cheader

def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" <options> header_file_1 header_file_2 ...\n"+\
          "Options:\n"+\
          "-h/--help\n\tPrint this usage guide\n"+\
          "-E/--enums\n\tPrint all enumerations\n"+\
          "-e/--enum\n\tPrint specified enumeration\n"+\
          "-M/--macros\n\tPrint all macros\n"+\
          "-m/--macro\n\tPrint value of macro\n"+\
          "-S/--structs\n\tPrint all structs\n"+\
          "-s/--struct\n\tPrint struct\n"+\
          "-n/--name-only\n\tPrint names only\n"+\
          "-P/--print-no-comment\n\tPrint with comment removed only\n"+\
          ""
          
#Parse options and arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hMm:Ee:Ss:nP",
                               ["help","macros","macro=","enums","enum=",
                                "structs","struct="
                                "name-only","print-no-comment"])
except getopt.GetoptError:
    usage()
    sys.exit(2)

#Check there is at least input file
if (len(args) < 1):
    usage()
    sys.exit(2)

#Parse options
##Print names only
nameOnly = False
##Print all structs?
allStructs = False
##Query specific struct
struct=""
##Print all enums?
allEnums = False
##Query specific enum
enum=""
##Print all macros?
allMacros = False
##Query specific macro
macro=""
##Print without comment
printNoComment=False
for opt,arg in opts:
    if (opt in ("-h","--help")):
        usage()
        sys.exit(0)
    elif (opt in ("-S","--structs")): 
        allStructs = True
    elif (opt in ("-s","--struct")): 
        struct = arg
    elif (opt in ("-M","--macros")): 
        allMacros = True
    elif (opt in ("-m","--macro")): 
        macro=arg
    elif (opt in ("-E","--enums")): 
        allEnums = True
    elif (opt in ("-e","--enum")): 
        enum = arg
    elif (opt in ("-n","--name-only")): 
        nameOnly = True
    elif (opt in ("-P","--print-no-comment")): 
        printNoComment = True
    else:
        assert (False,"Unhandled option :"+opt)

headerfile = cheader.cheaderfile(args)
if (printNoComment):
    for line in headerfile.content:
        print line
    sys.exit(0)
    
#Print all macros
if (allMacros):
    for (macroname, value) in headerfile.macros.items():
        if (nameOnly):
            print macroname
        else:
            print macroname+"\t=\t"+str(value)
#Print specified macro
if (macro != ""):
    try:
        print macro+"="+headerfile.macros[macro]
    except KeyError:
        print "Macro "+macro+" not found!"

#Print all structs
if (allStructs):
    for (structname, value) in headerfile.structs.items():
        if (nameOnly):
            print structname
        else:
            print str(value)+"\n"

#Print specified struct
if (struct != ""):
    try:
        print str(headerfile.structs[struct])
    except KeyError:
        print "Struct "+struct+" not found!"

#Print all enumerations
if (allEnums):
    for (enumname, values) in headerfile.enums.items():
        print enumname
        if (not nameOnly):
            for enumval in values:
                try:
                    print "\t"+enumval+"="+\
                          str(headerfile.enum_values[enumval])
                except KeyError:
                    print enumval+" not found in enum!";

#Print specifed enum
if (enum != ""):
    try:
        for enumval in headerfile.enums[enum]:
            try:
                print enumval+"="+str(headerfile.enum_values[enumval])
            except KeyError:
                print enumval+" not found in enum!";
    except KeyError:
        print "Enumeration "+enum+" not found!"
