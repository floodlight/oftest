"""
A set of inter-test utility functions for dealing with OF-DPA


"""

import logging
import ofp

from oftest import config
from oftest.testutils import *



class table(object):
    """ Metadata on each OFDPA table """
    def __init__(self, table_id, table_name):
        self.table_id = table_id
        self.table_name = table_name
    # TODO consider adding type checking verification here

INGRESS_TABLE           = table(0, "Ingress")
VLAN_TABLE              = table(10, "VLAN")
MACTERM_TABLE           = table(20, "MacTerm")
UNICAST_ROUTING_TABLE   = table(30, "Unicast Routing")
MULTICAST_ROUTING_TABLE = table(40, "Multicast Routing")
BRIDGING_TABLE          = table(50, "Bridging Table")
ACL_TABLE               = table(60, "ACL Policy Table")
#.... FIXME add all tables

DEFAULT_VLAN = 1

def enableVlanOnPort(controller, vlan, port=ofp.OFPP_ALL, priority=0):
    if port == ofp.OFPP_ALL:
        ports = sorted(config["port_map"].keys())
    else:
        ports = [port]
    for port in ports:
        tagged_match = ofp.match([
                ofp.oxm.in_port(port),
                ofp.oxm.vlan_vid(vlan | ofp.OFPVID_PRESENT)
                ])

        request = ofp.message.flow_add(
            table_id = VLAN_TABLE.table_id,
            cookie = 0xdead,
            match = tagged_match,
            instructions = [
                ofp.instruction.goto_table(MACTERM_TABLE.table_id),
#                 ofp.instruction.apply_actions(
#                     actions=[
#                         ofp.action.push_vlan(ethertype=0x8100), # DO NOT PUT THIS FOR OF-DPA 2.0 EA1 - seems to not matter for EA2
#                         ofp.action.set_field(ofp.oxm.vlan_vid( ofp.OFPVID_PRESENT | vlan))
#                     ]),
                    ],
            buffer_id = ofp.OFP_NO_BUFFER,
            priority = priority)

        logging.info("Inserting vlan rule allowing tagged vlan %d on port %d" % (vlan, port))
        controller.message_send(request)
        do_barrier(controller)
        verify_no_errors(controller)


def installDefaultVlan(controller, vlan=DEFAULT_VLAN, port=ofp.OFPP_ALL, priority=0):
    """ Insert a rule that maps all untagged traffic to vlan $vlan

    In OFDPA, table 10 (the vlan table) requires that all traffic be
    mapped to an internal vlan else the packets be dropped.  This function
    sets up a default vlan mapping all untagged traffic to an internal VLAN.

    With OF-DPA, before you can insert a 'untagged to X' rule on a
    port, you must first insert a 'X --> X' rule for the same port.

    Further, the 'X --> X' rule must set ofp.OFPVID_PRESENT even
    though 'X' is non-zero.

    The 'controller' variable is self.controller from a test
    """
    # OFDPA seems to be dumb and wants each port set individually
    #       Can't set all ports by using OFPP_ALL
    if port == ofp.OFPP_ALL:
        ports = sorted(config["port_map"].keys())
    else:
        ports = [port]

    for port in ports:
        # enable this vlan on this port before we can map untagged packets to the vlan
        enableVlanOnPort(controller, vlan, port)

        untagged_match = ofp.match([
                ofp.oxm.in_port(port),
                # OFDPA 2.0 says untagged is vlan_id=0, mask=ofp.OFPVID_PRESENT
                ofp.oxm.vlan_vid_masked(0,ofp.OFPVID_PRESENT)    # WTF OFDPA 2.0EA2 -- really!?
                ])

        request = ofp.message.flow_add(
            table_id = VLAN_TABLE.table_id,
            cookie = 0xbeef,
            match = untagged_match,
            instructions = [
                ofp.instruction.apply_actions(
                    actions=[
                        #ofp.action.push_vlan(ethertype=0x8100),
                        ofp.action.set_field(ofp.oxm.vlan_vid(ofp.OFPVID_PRESENT | vlan))
                    ]),
                ofp.instruction.goto_table(MACTERM_TABLE.table_id)   
                    ],
            buffer_id = ofp.OFP_NO_BUFFER,
            priority = priority)

        logging.info("Inserting default vlan sending all untagged traffic to vlan %d on port %d" % (vlan, port))
        controller.message_send(request)
        do_barrier(controller)
        verify_no_errors(controller)


_group_types = {
    "L2 Interface": 0,
    "L2 Rewrite" : 1,
    "L3 Unicast" : 2,
    "L2 Multicast" : 3,
    "L2 Flood" : 4,
    "L3 Interface" : 5,
    "L3 Multicast": 6,
    "L3 ECMP": 7,
    "L2 Data Center Overlay": 8,
    "MPLS Label" : 9,
    "MPLS Forwarding" :10,
    "L2 Unfiltered Interface": 11,
    "L2 Loopback": 12,
}


def makeGroupID(groupType, local_id):
    """ Group IDs in OF-DPA have rich meaning

    @param groupType is a key in _group_types
    @param local_id is an integer 0<= local_id < 2**27,
        but it may have more semantic meaning depending on the
        groupType


    Read Section 4.3 of the OF-DPA manual on groups for 
    details
    """
    if groupType not in _group_types:
        raise KeyError("%s not a valid OF-DPA group type" % groupType)
    if local_id < 0 or local_id >=134217728:
        raise ValueError("local_id %d must be  0<= local_id < 2**27" % local_id)
    return (_group_types[groupType] << 28) + local_id


def delete_all_recursive_groups(controller):
    pass
