#!/usr/bin/python
#
# This python script generates action subclasses
#

import re
import sys
sys.path.append("../../src/python/oftest")
from cstruct import *
from class_maps import class_to_members_map

print """
# Python OpenFlow action wrapper classes

from cstruct import *

"""

################################################################
#
# Action subclasses
#
################################################################

action_class_map = {
    'set_output_port' : 'ofp_action_set_output_port',
    'set_vlan_vid' : 'ofp_action_vlan_vid',
    'set_vlan_pcp' : 'ofp_action_vlan_pcp',
    'set_dl_src' : 'ofp_action_dl_addr',
    'set_dl_dst' : 'ofp_action_dl_addr',
    'set_nw_src' : 'ofp_action_nw_addr',
    'set_nw_dst' : 'ofp_action_nw_addr',
    'set_nw_tos' : 'ofp_action_nw_tos',
    'set_tp_src' : 'ofp_action_tp_port',
    'set_tp_dst' : 'ofp_action_tp_port',
    'set_nw_ecn' : 'ofp_action_nw_ecn',
    'copy_ttl_out' : 'ofp_action_header',
    'copy_ttl_in' : 'ofp_action_header',
    'set_mpls_label' : 'ofp_action_mpls_label',
    'set_mpls_tc' : 'ofp_action_mpls_tc',
    'set_mpls_ttl' : 'ofp_action_mpls_ttl',
    'dec_mpls_ttl' : 'ofp_action_header',
    'push_vlan' : 'ofp_action_header',
    'pop_vlan' : 'ofp_action_header',
    'push_mpls' : 'ofp_action_header',
    'pop_mpls' : 'ofp_action_header',
    'set_queue' : 'ofp_action_set_queue',
    'group' : 'ofp_action_group',
    'set_nw_ttl' : 'ofp_action_nw_ttl',
    'dec_nw_ttl' : 'ofp_action_header',
    'experimenter' : 'ofp_action_experimenter_header'
}

template = """
class --OBJ_TYPE--_--TYPE--(--PARENT_TYPE--):
    \"""
    Wrapper class for --TYPE-- --OBJ_TYPE-- object

    --DOC_INFO--
    \"""
    def __init__(self):
        --PARENT_TYPE--.__init__(self)
        self.type = --ACT_INST_NAME--
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "--OBJ_TYPE--_--TYPE--\\n"
        outstr += --PARENT_TYPE--.show(self, prefix)
        return outstr
"""

################################################################
#
# Instruction subclasses
#
################################################################

instruction_class_map = {
    'goto_table' : 'ofp_instruction_goto_table',
    'write_metadata' : 'ofp_instruction_write_metadata',
    'write_actions' : 'ofp_instruction_actions',
    'apply_actions' : 'ofp_instruction_actions',
    'clear_actions' : 'ofp_instruction',
    'experimenter' : 'ofp_instruction_experimenter'
}

def gen_class(t, parent, obj_type):
    if not parent in class_to_members_map.keys():
        doc_info = "Unknown parent action/instruction class: " + parent
    else:
        doc_info = "Data members inherited from " + parent + ":\n"
    for var in class_to_members_map[parent]:
        doc_info += "    @arg " + var + "\n"
    if obj_type == "action":
        name = "OFPAT_" + t.upper()
    else:
        name = "OFPIT_" + t.upper()
    to_print = re.sub('--TYPE--', t, template)
    to_print = re.sub('--OBJ_TYPE--', obj_type, to_print)
    to_print = re.sub('--PARENT_TYPE--', parent, to_print)
    to_print = re.sub('--ACT_INST_NAME--', name, to_print)
    to_print = re.sub('--DOC_INFO--', doc_info, to_print)
    print to_print
    
if __name__ == '__main__':
    for (t, parent) in action_class_map.items():
        gen_class(t, parent, "action")
    for (t, parent) in instruction_class_map.items():
        gen_class(t, parent, "instruction")

    # Generate a list of action classes
    action_list = action_class_map.keys()
    action_list.sort()
    print "action_class_list = ("
    prev = None
    for t in action_list:
        if prev:
            print "    action_" + prev + ","
        prev = t
    print "    action_" + prev + ")\n"

    # Generate a list of instruction classes
    inst_list = instruction_class_map.keys()
    inst_list.sort()
    print "instruction_class_list = ("
    prev = None
    for t in inst_list:
        if prev:
            print "    instruction_" + prev + ","
        prev = t
    print "    instruction_" + prev + ")"


# @todo Add action list to instruction_action_list class
