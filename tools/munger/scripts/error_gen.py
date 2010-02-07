#!/usr/bin/python
#
# This python script generates error subclasses
#

import re
import sys
sys.path.append("../../src/python/oftest/ofmsg")
from ofp import *
from ofp_aux import class_to_members_map

print """
# Python OpenFlow error wrapper classes

from ofp import *

# This will never happen; done to avoid lint warning
if __name__ == '__main__':
    def of_message_parse(msg):
        print "ERROR: of_msg_parse in error.py called"
        return None

"""

################################################################
#
# Error message subclasses
#
################################################################

# Template for error subclasses

template = """
class --TYPE--_error_msg(ofp_error_msg):
    \"""
    Wrapper class for --TYPE-- error message class

    Data members inherited from ofp_error_msg:
    @arg type
    @arg code
    @arg data: Binary string following message members
    
    \"""
    def __init__(self):
        ofp_error_msg.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_ERROR
        self.type = --ERROR_NAME--
        self.data = ""

    def pack(self, assertstruct=True):
        self.header.length = self.__len__()
        packed = ofp_error_msg.pack(self)
        packed += self.data

    def unpack(self, binary_string):
        binary_string = ofp_error_msg.unpack(self, binary_string)
        self.data = binary_string
        return []

    def __len__(self):
        return OFP_HEADER_BYTES + OFP_ERROR_MSG_BYTES + len(self.data)

    def show(self, prefix=''):
        print prefix + "--TYPE--_error_msg"
        ofp_error_msg.show(self)
        print prefix + "data is of length " + len(self.data)
        obj = of_message_parse(self.data)
        if obj != None:
            obj.show()
        else:
            print prefix + "Unable to parse data"
"""

error_types = [
    'hello_failed',
    'bad_request',
    'bad_action',
    'flow_mod_failed',
    'port_mod_failed',
    'queue_op_failed']

for t in error_types:
    error_name = "OFPET_" + t.upper()
    to_print = re.sub('--TYPE--', t, template)
    to_print = re.sub('--ERROR_NAME--', error_name, to_print)
    print to_print
