#!/usr/bin/env python
#
# This python script generates action subclasses
#

import sys
sys.path.append("../../src/python/oftest")
from cstruct import *
from common_gen import *

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
    'output' : 'ofp_action_output',
    'set_field' : 'ofp_action_set_field',
    'copy_ttl_out' : 'ofp_action_header',
    'copy_ttl_in' : 'ofp_action_header',
    'set_mpls_ttl' : 'ofp_action_mpls_ttl',
    'dec_mpls_ttl' : 'ofp_action_header',
    'push_vlan' : 'ofp_action_push',
    'pop_vlan' : 'ofp_action_header',
    'push_mpls' : 'ofp_action_push',
    'pop_mpls' : 'ofp_action_pop_mpls',
    'set_queue' : 'ofp_action_set_queue',
    'group' : 'ofp_action_group',
    'set_nw_ttl' : 'ofp_action_nw_ttl',
    'dec_nw_ttl' : 'ofp_action_header',
    'experimenter' : 'ofp_action_experimenter_header'
}

if __name__ == '__main__':
    for (t, parent) in action_class_map.items():
        gen_class(t, parent, "action")
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

