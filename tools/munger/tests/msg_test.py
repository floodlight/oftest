import sys
sys.path.append('../../../src/python/oftest/protocol')
from message import *
from action import *
from error import *
from class_maps import *

header_fields = ['version', 'xid']
fixed_header_fields = ['type', 'length']

ofmsg_class_map_to_parents = {
    action_enqueue                     : [ofp_action_enqueue],
    action_output                      : [ofp_action_output],
    action_set_dl_dst                  : [ofp_action_dl_addr],
    action_set_dl_src                  : [ofp_action_dl_addr],
    action_set_nw_dst                  : [ofp_action_nw_addr],
    action_set_nw_src                  : [ofp_action_nw_addr],
    action_set_nw_tos                  : [ofp_action_nw_tos],
    action_set_tp_dst                  : [ofp_action_tp_port],
    action_set_tp_src                  : [ofp_action_tp_port],
    action_set_vlan_pcp                : [ofp_action_vlan_pcp],
    action_set_vlan_vid                : [ofp_action_vlan_vid],
    action_strip_vlan                  : [ofp_action_header],
    action_vendor                      : [ofp_action_vendor_header],
    aggregate_stats_reply              : [ofp_stats_reply],
    aggregate_stats_request            : [ofp_stats_request,
                                          ofp_aggregate_stats_request],
    bad_action_error_msg               : [ofp_error_msg],
    bad_request_error_msg              : [ofp_error_msg],
    barrier_reply                      : [],
    barrier_request                    : [],
    desc_stats_reply                   : [ofp_stats_reply],
    desc_stats_request                 : [ofp_stats_request,
                                          ofp_desc_stats_request],
    echo_reply                         : [],
    echo_request                       : [],
    error                              : [ofp_error_msg],
    features_reply                     : [ofp_switch_features],
    features_request                   : [],
    flow_mod                           : [ofp_flow_mod],
    flow_mod_failed_error_msg          : [ofp_error_msg],
    flow_removed                       : [ofp_flow_removed],
    flow_stats_entry                   : [ofp_flow_stats],
    flow_stats_reply                   : [ofp_stats_reply],
    flow_stats_request                 : [ofp_stats_request,
                                          ofp_flow_stats_request],
    get_config_reply                   : [ofp_switch_config],
    get_config_request                 : [],
    hello                              : [],
    hello_failed_error_msg             : [ofp_error_msg],
    ofp_desc_stats_request             : [],
    ofp_table_stats_request            : [],
    packet_in                          : [ofp_packet_in],
    packet_out                         : [ofp_packet_out],
    port_mod                           : [ofp_port_mod],
    port_mod_failed_error_msg          : [ofp_error_msg],
    port_stats_reply                   : [ofp_stats_reply],
    port_stats_request                 : [ofp_stats_request,
                                          ofp_port_stats_request],
    port_status                        : [ofp_port_status],
    queue_get_config_reply             : [ofp_queue_get_config_reply],
    queue_get_config_request           : [ofp_queue_get_config_request],
    queue_op_failed_error_msg          : [ofp_error_msg],
    queue_stats_reply                  : [ofp_stats_reply],
    queue_stats_request                : [ofp_stats_request,
                                          ofp_queue_stats_request],
    set_config                         : [ofp_switch_config],
    stats_reply                        : [ofp_stats_reply],
    stats_request                      : [ofp_stats_request],
    table_stats_reply                  : [ofp_stats_reply],
    table_stats_request                : [ofp_stats_request,
                                          ofp_table_stats_request],
    vendor                             : [ofp_vendor_header]
}

ofmsg_names = {
    action_enqueue                     : 'action_enqueue',
    action_output                      : 'action_output',
    action_set_dl_dst                  : 'action_set_dl_dst',
    action_set_dl_src                  : 'action_set_dl_src',
    action_set_nw_dst                  : 'action_set_nw_dst',
    action_set_nw_src                  : 'action_set_nw_src',
    action_set_nw_tos                  : 'action_set_nw_tos',
    action_set_tp_dst                  : 'action_set_tp_dst',
    action_set_tp_src                  : 'action_set_tp_src',
    action_set_vlan_pcp                : 'action_set_vlan_pcp',
    action_set_vlan_vid                : 'action_set_vlan_vid',
    action_strip_vlan                  : 'action_strip_vlan',
    action_vendor                      : 'action_vendor',
    aggregate_stats_reply              : 'aggregate_stats_reply',
    aggregate_stats_request            : 'aggregate_stats_request',
    bad_action_error_msg               : 'bad_action_error_msg',
    bad_request_error_msg              : 'bad_request_error_msg',
    barrier_reply                      : 'barrier_reply',
    barrier_request                    : 'barrier_request',
    desc_stats_reply                   : 'desc_stats_reply',
    desc_stats_request                 : 'desc_stats_request',
    echo_reply                         : 'echo_reply',
    echo_request                       : 'echo_request',
    error                              : 'error',
    features_reply                     : 'features_reply',
    features_request                   : 'features_request',
    flow_mod                           : 'flow_mod',
    flow_mod_failed_error_msg          : 'flow_mod_failed_error_msg',
    flow_removed                       : 'flow_removed',
    flow_stats_entry                   : 'flow_stats_entry',
    flow_stats_reply                   : 'flow_stats_reply',
    flow_stats_request                 : 'flow_stats_request',
    get_config_reply                   : 'get_config_reply',
    get_config_request                 : 'get_config_request',
    hello                              : 'hello',
    hello_failed_error_msg             : 'hello_failed_error_msg',
    ofp_desc_stats_request             : 'ofp_desc_stats_request',
    ofp_table_stats_request            : 'ofp_table_stats_request',
    packet_in                          : 'packet_in',
    packet_out                         : 'packet_out',
    port_mod                           : 'port_mod',
    port_mod_failed_error_msg          : 'port_mod_failed_error_msg',
    port_stats_reply                   : 'port_stats_reply',
    port_stats_request                 : 'port_stats_request',
    port_status                        : 'port_status',
    queue_get_config_reply             : 'queue_get_config_reply',
    queue_get_config_request           : 'queue_get_config_request',
    queue_op_failed_error_msg          : 'queue_op_failed_error_msg',
    queue_stats_reply                  : 'queue_stats_reply',
    queue_stats_request                : 'queue_stats_request',
    set_config                         : 'set_config',
    stats_reply                        : 'stats_reply',
    stats_request                      : 'stats_request',
    table_stats_reply                  : 'table_stats_reply',
    table_stats_request                : 'table_stats_request',
    vendor                             : 'vendor'
}

keys = ofmsg_class_map_to_parents.keys()
keys.sort()

print "Generating all classes with no data init"
print
for cls in keys:
    print "Creating class " + ofmsg_names[cls]
    obj = cls()
    print ofmsg_names[cls] + " length: " + str(len(obj))
    obj.show("  ")
    print

print "End of class generation"
print
print

print "Generating messages, packing, showing (to verify len)"
print "and calling self unpack"
print
for cls in keys:
    print "Pack/unpack test for class " + ofmsg_names[cls]
    obj = cls()
    packed = obj.pack()
    print "Packed object, length ", len(packed)
    obj.show("  ")
    obj_check = cls()
    string = obj_check.unpack(packed)
    print "Unpacked obj, length ", len(obj_check)
    obj_check.show("  ")
    if string != "":
        print >> sys.stderr, "WARNING: " + ofmsg_names[cls] + \
            ", unpack returned string " + string
    if obj != obj_check:
        print >> sys.stderr, "ERROR: " + ofmsg_names[cls] + \
            ", obj != obj_check"
    print

print "End of class pack check"
print
print


print "Testing message parsing"
print
for cls in keys:
    print "Creating class " + ofmsg_names[cls]
    obj = cls()
    print ofmsg_names[cls] + " length: " + str(len(obj))
    obj.show("  ")
    print

print "End of class generation"
print
print


#
# TO DO
#     Generate varying actions lists and attach to flow_mod,
# packet out and flow_stats_entry objects.
#     Generate varying lists of stats entries for replies in
# flow_stats_reply, table_stats_reply, port_stats_reply and
# queue_stats_reply
#     Create and test packet-to-flow function


f = flow_stats_reply()
ent = flow_stats_entry()


act = action_strip_vlan()
alist = action_list()
alist.add(act)

act = action_set_tp_dst()
act.tp_port = 17

m = ofp_match()
m.wildcards = OFPFW_IN_PORT + OFPFW_DL_VLAN + OFPFW_DL_SRC

#
# Need: Easy reference from action to data members
m.in_port = 12
m.dl_src= [1,2,3,4,5,6]
m.dl_dst= [11,22,23,24,25,26]
m.dl_vlan = 83
m.dl_vlan_pcp = 1
m.dl_type = 0x12
m.nw_tos = 3
m.nw_proto = 0x300
m.nw_src = 0x232323
m.nw_dst = 0x3232123
m.tp_src = 32
m.tp_dst = 2

m.show()

