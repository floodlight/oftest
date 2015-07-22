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


def installDefaultVlan(controller, vlan=1, priority=0, port=ofp.OFPP_ALL):
    """ Insert a rule that maps all untagged traffic to vlan $vlan

    In OFDPA, table 10 (the vlan table) requires that all traffic be
    mapped to an internal vlan else the packets be dropped.  This sets
    up a default vlan mapping for all traffic.

    The 'controller' variable is self.controller from a test
    """
    # OFDPA seems to be dumb and wants each port set individually
    if port == ofp.OFPP_ALL:
        ports = sorted(config["port_map"].keys())
    else:
        ports = [port]

    for port in ports:
        match = ofp.match([
                ofp.oxm.in_port(port),
                ofp.oxm.vlan_vid(0)
                ])

        request = ofp.message.flow_add(
            table_id = VLAN_TABLE.table_id,
            cookie = 42,
            match = match,
            instructions = [
                ofp.instruction.apply_actions(
                    actions=[
                        ofp.action.push_vlan(ethertype=0x8100),
                        ofp.action.set_field(ofp.oxm.vlan_vid(ofp.OFPVID_PRESENT | vlan))
                    ]),
                ofp.instruction.goto_table(MACTERM_TABLE.table_id)   
                    ],
            buffer_id = ofp.OFP_NO_BUFFER,
            priority = priority)

        logging.info("Inserting default vlan sending all untagged traffic to vlan %d" % vlan)
        controller.message_send(request)
        do_barrier(controller)
