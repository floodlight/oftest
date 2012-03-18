"""This module implements output printing.

Output are divided into 4 levels and
can be configured for different verbosity

Copyright(C) 2009, Stanford University
Date August 2009
Created by ykk
"""

##Various output modes
MODE = {}
MODE["ERR"] = 0
MODE["WARN"] = 1
MODE["INFO"] = 2
MODE["DBG"] = 3

#Global mode
global output_mode
output_mode = None

def set_mode(msg_mode, who=None):
    """Set the message mode for who
    If who is None, set global mode
    """
    global output_mode
    if (output_mode == None):
        output_mode = {}
        output_mode["global"] = MODE["WARN"]
        output_mode["DBG"] = []
        output_mode["INFO"] = []
        output_mode["WARN"] = []

    #Set global mode
    if (who == None):
        output_mode["global"] = MODE[msg_mode]
        return
    
    #Individual mode
    if (msg_mode == "ERR"):
        return
    for mode in ["WARN","INFO","DBG"]:
        if (not (who in mode[mode])):
            mode[mode].append(who)
        if (msg_mode == mode):
            return
    
def output(msg_mode, msg, who=None):
    """Print message
    """
    global output_mode
    if (output_mode == None):
        raise RuntimeException("Output mode is not set")

    #Indicate who string
    if (who == None):
        whostr = ""
    else:
        whostr = who+":"

    #Print output 
    if (MODE[msg_mode] <= output_mode["global"]):
        print msg_mode.ljust(4, ' ')+"|"+whostr+msg
    elif (who in output_mode[msg_mode]):
        print msg_mode.ljust(4, ' ')+"|"+whostr+msg
        
def err(msg, who=None):
    """Print error messages
    """
    output("ERR", msg, who)

def warn(msg, who=None):
    """Print warning messages
    """
    output("WARN", msg, who)

def info(msg, who=None):
    """Print informational messages
    """
    output("INFO", msg, who)

def dbg(msg, who=None):
    """Print debug messages
    """
    output("DBG", msg, who)
