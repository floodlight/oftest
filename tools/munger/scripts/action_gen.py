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

action_structs = [
    'set_output_port',
    'vlan_vid',
    'vlan_pcp',
    'dl_addr',
    'nw_addr',
    'tp_port',
    'nw_tos',
    'experimenter_header']
# FIXME:  ADD ACTION STRUCTURES

action_types = [
    'set_output_port',
    'set_vlan_vid',
    'set_vlan_pcp',
    'set_dl_src',
    'set_dl_dst',
    'set_nw_src',
    'set_nw_dst',
    'set_nw_tos',
    'set_tp_src',
    'set_tp_dst',
    'experimenter'
]
action_types.sort()
# FIXME:  ADD ACTION TYPES

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
    'experimenter' : 'ofp_action_experimenter_header'
}

template = """
class action_--TYPE--(--PARENT_TYPE--):
    \"""
    Wrapper class for --TYPE-- action object

    --DOC_INFO--
    \"""
    def __init__(self):
        --PARENT_TYPE--.__init__(self)
        self.type = --ACTION_NAME--
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_--TYPE--\\n"
        outstr += --PARENT_TYPE--.show(self, prefix)
        return outstr
"""

if __name__ == '__main__':
    for (t, parent) in action_class_map.items():
        if not parent in class_to_members_map.keys():
            doc_info = "Unknown parent action class: " + parent
        else:
            doc_info = "Data members inherited from " + parent + ":\n"
            for var in class_to_members_map[parent]:
                doc_info += "    @arg " + var + "\n"
        action_name = "OFPAT_" + t.upper()
        to_print = re.sub('--TYPE--', t, template)
        to_print = re.sub('--PARENT_TYPE--', parent, to_print)
        to_print = re.sub('--ACTION_NAME--', action_name, to_print)
        to_print = re.sub('--DOC_INFO--', doc_info, to_print)
        print to_print

    # Generate a list of action classes
    print "action_class_list = ("
    prev = None
    for (t, parent) in action_class_map.items():
        if prev:
            print "    action_" + prev + ","
        prev = t
    print "    action_" + prev + ")"
