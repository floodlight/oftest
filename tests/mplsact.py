"""
Test cases for testing actions taken on packets

See basic.py for other info.

It is recommended that these definitions be kept in their own
namespace as different groups of tests will likely define 
similar identifiers.

  The function test_set_init is called with a complete configuration
dictionary prior to the invocation of any tests from this file.

  The switch is actively attempting to contact the controller at the address
indicated oin oft_config

"""

import copy

import logging

import unittest

import random
import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action
import oftest.parse as parse
import basic
import pktact

from testutils import *

#@var port_map Local copy of the configuration map from OF port
# numbers to OS interfaces
pa_port_map = None
#@var pa_logger Local logger object
pa_logger = None
#@var pa_config Local copy of global configuration data
pa_config = None

# For test priority
#@var test_prio Set test priority for local tests
test_prio = {}

WILDCARD_VALUES = [ofp.OFPFW_IN_PORT,
                   ofp.OFPFW_DL_VLAN,
                   ofp.OFPFW_DL_TYPE,
                   ofp.OFPFW_NW_PROTO,
                   ofp.OFPFW_DL_VLAN_PCP,
                   ofp.OFPFW_NW_TOS,
                   ofp.OFPFW_MPLS_LABEL,
                   ofp.OFPFW_MPLS_TC]

MODIFY_ACTION_VALUES =  [ofp.OFPAT_COPY_TTL_OUT,
                         ofp.OFPAT_COPY_TTL_IN,
                         ofp.OFPAT_SET_MPLS_LABEL,
                         ofp.OFPAT_SET_MPLS_TC,
                         ofp.OFPAT_SET_MPLS_TTL,
                         ofp.OFPAT_DEC_MPLS_TTL,
                         ofp.OFPAT_PUSH_MPLS,
                         ofp.OFPAT_POP_MPLS]

# Cache supported features to avoid transaction overhead
cached_supported_actions = None

def test_set_init(config):
    """
    Set up function for packet action test classes

    @param config The configuration dictionary; see oft
    """

    global pa_port_map
    global pa_logger
    global pa_config

    pa_logger = logging.getLogger("pkt_act")
    pa_logger.info("Initializing test set")
    pa_port_map = config["port_map"]
    pa_config = config

################################################################

class MplsActNonTagPop(pktact.BaseMatchCase):
    """
    MPLS action test with untagged pkts
    Excercise various test_conditions with pop action
    Test on one pair of ports
    """
    def __init__(self):
        pktact.BaseMatchCase.__init__(self)
        self.num_tags = 0
        self.label = -1
        self.tc = 0
        self.label_int = -1
        self.tc_int = 0
        self.label_match = ofp.OFPML_NONE
        self.tc_match = 0

    def runTest(self):
        mpls_pop_act_tests(self)

class MplsActOneTagPop(MplsActNonTagPop):
    """
    MPLS action test with tagged pkts
    Excercise various test_conditions with pop action
    Test on one pair of ports
    """
    def __init__(self):
        MplsActNonTagPop.__init__(self)
        self.num_tags = 1
        self.label = random.randint(16, 1048575)
        self.tc = random.randint(0,7)
        self.label_match = self.label
        self.tc_match = self.tc

    def runTest(self):
        mpls_pop_act_tests(self)

class MplsActTwoTagPop(MplsActNonTagPop):
    """
    MPLS action test with two-tagged pkts
    Excercise various test_conditions with pop action
    Test on one pair of ports
    """
    def __init__(self):
        MplsActNonTagPop.__init__(self)
        self.num_tags = 2
        self.label = random.randint(16, 1048573)
        self.tc = random.randint(0,5)
        self.label_int = self.label + 1
        self.tc_int = self.tc + 1
        self.label_match = self.label
        self.tc_match = self.tc

    def runTest(self):
        mpls_pop_act_tests(self)


def mpls_action_support_check(parent):

    sup_acts = pktact.supported_actions_get(parent)
    sup_mpls_act = {}

    if (sup_acts & 1<<ofp.OFPAT_COPY_TTL_IN):
        sup_mpls_act['sup_copy_ttl_in'] = True
    if (sup_acts & 1<<ofp.OFPAT_COPY_TTL_OUT):
        sup_mpls_act['sup_copy_ttl_out'] = True
    if (sup_acts & 1<<ofp.OFPAT_SET_MPLS_LABEL):
        sup_mpls_act['sup_set_mpls_label'] = True
    if (sup_acts & 1<<ofp.OFPAT_SET_MPLS_TC):
        sup_mpls_act['sup_set_mpls_tc'] = True
    if (sup_acts & 1<<ofp.OFPAT_SET_MPLS_TTL):
        sup_mpls_act['sup_set_mpls_ttl'] = True
    if (sup_acts & 1<<ofp.OFPAT_DEC_MPLS_TTL):
        sup_mpls_act['sup_dec_mpls_ttl'] = True
    if (sup_acts & 1<<ofp.OFPAT_PUSH_MPLS):
        sup_mpls_act['sup_push_mpls'] = True
    if (sup_acts & 1<<ofp.OFPAT_POP_MPLS):
        sup_mpls_act['sup_pop_mpls'] = True

    return sup_mpls_act

def mpls_pop_act_tests(parent):
    """
    Test vlan pop action for the packets with/without tags

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param num_tags number of Vlan tags
    """
    parent.assertTrue(((parent.num_tags>=0) and (parent.num_tags<=2)),
        "Parameter num_tags not within an acceptable range")

    sup_mpls_act = mpls_action_support_check(parent)

    if sup_mpls_act.has_key('sup_pop_mpls') == False:
        skip_message_emit(parent, "MPLS pop action test. POP not supported")
        return

    act = action.action_pop_mpls()

    if parent.num_tags == 0:
        match_exp = False
        exp_msg = ofp.OFPT_ERROR
        exp_msg_type = ofp.OFPET_BAD_ACTION
        exp_msg_code = ofp.OFPBAC_MATCH_INCONSISTENT

    elif parent.num_tags == 1:
        match_exp = True
        exp_msg = ofp.OFPT_FLOW_REMOVED
        exp_msg_type = 0 #NOT_EXPECTED
        exp_msg_code = 0 #NOT_EXPECTED

    else:
        match_exp = True
        exp_msg = ofp.OFPT_FLOW_REMOVED
        exp_msg_type = 0 #NOT_EXPECTED
        exp_msg_code = 0 #NOT_EXPECTED

    exp_label = -1 #NOT EXPECTED/OUTER LABEL NOT EXPECTED
    exp_tc = 0
    exp_ttl = 0

    action_list=[act]

    flow_match_test_mpls(parent, pa_port_map,
                    wildcards=0,
                    mpls_label=parent.label,
                    mpls_tc=parent.tc,
                    mpls_label_int=parent.label_int,
                    mpls_tc_int=parent.tc_int,
                    label_match=parent.label_match,
                    tc_match=parent.tc_match,
                    exp_mpls_label=exp_label,
                    exp_mpls_tc=exp_tc,
                    match_exp=match_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    action_list=action_list,
                    max_test=1)

if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test-spec=mplsact"
