import sys
sys.path.append('../../../src/python/oftest')

from parse import of_message_parse
from parse import of_header_parse

from defs import *

def error_out(string):
    print >> sys.stderr, string
    print string

def obj_comp(orig, new, objname, errstr=None):
    """
    Compare two objects
    """
    dump = False        
    if not errstr:
        errstr = "(unknown)"
    errstr += " " + objname
    if not new:
        error_out("ERROR: obj comp, new is None for " + errstr)
        dump = True
    elif type(orig) != type(new):
        error_out("ERROR: type mismatch for " + errstr + " ")
        dump = True
    elif orig != new:
        error_out("ERROR: " + errstr + " orig != new")
        dump = True
    if dump:
        print "Dump of mismatch for " + errstr
        print "type orig " + str(type(orig))
        print "orig length ", len(orig)
        orig.show("  ")
        if new:
            print "type new" + str(type(new))
            print "new length ", len(new)
            new.show("  ")
        print


# Generate a long action list

def action_list_create(n=10):
    """
    Create an action list

    @param n The number of actions to put in the list

    Cycle through the list of all actions, adding each type
    """

    al = action_list()
    for i in range(n):
        idx = i % len(action_class_list)
        cls = action_class_list[idx]()
        al.add(cls)
    return al

# Test classes with action lists
def class_action_test():
    """
    Test objects that use action lists
    """

    print "Testing action lists:  flow mod, packet out, flow stats"
    for acount in [0, 1, 5, 16, 34]:
        print "  " + str(acount) + " actions in list"
        obj = flow_mod()
        obj.actions = action_list_create(acount)
        packed = obj.pack()
        header = of_header_parse(packed)
        obj_check = flow_mod()
        if obj_check.unpack(packed) != "":
            error_out("ERROR: flow mod action list test extra " +
                      "string on unpack")
        obj_comp(obj, obj_check, 'flow_mod', "unpack test " + str(acount))
        obj_check = of_message_parse(packed)
        obj_comp(obj, obj_check, 'flow_mod', "parse test " + str(acount))
        # obj.show()

        # packet out with and without data
        obj = packet_out()
        obj.actions = action_list_create(acount)
        packed = obj.pack()
        header = of_header_parse(packed)
        obj_check = packet_out()
        if obj_check.unpack(packed) != "":
            error_out("ERROR: packet out packet_out test extra " +
                      "string on unpack")
        obj_comp(obj, obj_check, 'packet_out', "unpack test " + str(acount))
        obj_check = of_message_parse(packed)
        obj_comp(obj, obj_check, 'packet_out', "parse test " + str(acount))
        # obj.show()

        obj = packet_out()
        obj.actions = action_list_create(acount)
        obj.data = "short test string for packet data"
        packed = obj.pack()
        header = of_header_parse(packed)
        obj_check = packet_out()
        if obj_check.unpack(packed) != "":
            error_out("ERROR: packet out packet_out test extra " +
                      "string on unpack")
        obj_comp(obj, obj_check, 'packet_out', "unpack test " + str(acount))
        obj_check = of_message_parse(packed)
        obj_comp(obj, obj_check, 'packet_out', "parse test " + str(acount))
        # obj.show()

        # flow stats entry (not a message)
        obj = flow_stats_entry()
        obj.actions = action_list_create(acount)
        packed = obj.pack()
        obj_check = flow_stats_entry()
        if obj_check.unpack(packed) != "":
            error_out("ERROR: packet out flow stats test extra " +
                      "string on unpack")
        obj_comp(obj, obj_check, 'packet_out', "unpack test " + str(acount))
        # obj.show()

print "Generating all classes with no data init"
print
for cls in all_objs:
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
for cls in all_objs:
    print "Pack/unpack test for class " + ofmsg_names[cls]
    obj = cls()
    packed = obj.pack()
    obj_check = cls()
    string = obj_check.unpack(packed)
    if string != "":
        print >> sys.stderr, "WARNING: " + ofmsg_names[cls] + \
            ", unpack returned string " + string
    obj_comp(obj, obj_check, ofmsg_names[cls], "pack/unpack")

print "End of class pack check"
print
print


print "Testing message parsing"
print
for cls in all_objs:
    # Can only parse real messages
    if not cls in of_messages:
        print "Not testing " + ofmsg_names[cls]
        continue
    print "Parse test for class " + ofmsg_names[cls]
    obj = cls()
    packed = obj.pack()
    header = of_header_parse(packed)
    obj_check = of_message_parse(packed)
    obj_comp(obj, obj_check, ofmsg_names[cls], "parse test")

print "End of parse testing"
print
print

class_action_test()
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

