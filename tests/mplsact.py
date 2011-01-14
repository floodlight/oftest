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
    MPLS action test with untagged pkts (pop)
    Test on one pair of ports
    """
    def __init__(self):
        pktact.BaseMatchCase.__init__(self)
        self.num_tags = 0
        self.label = -1
        self.tc = 0
        self.ttl = 0
        self.label_int = -1
        self.tc_int = 0
        self.ttl_int = 0
        self.ip_ttl = 192
        self.label_match = ofp.OFPML_NONE
        self.tc_match = 0

    def runTest(self):
        mpls_pop_act_tests(self)

class MplsActNonTagTtlIn(MplsActNonTagPop):
    """
    MPLS action test with untagged pkts (Copy TTL in)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_ttl_in_act_tests(self)

class MplsActNonTagTtlOut(MplsActNonTagPop):
    """
    MPLS action test with untagged pkts (Copy TTL out)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_ttl_out_act_tests(self)

class MplsActNonTagSetLabel(MplsActNonTagPop):
    """
    MPLS action test with untagged pkts (Set label)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_set_label_act_tests(self)

class MplsActNonTagSetTc(MplsActNonTagPop):
    """
    MPLS action test with untagged pkts (Set TC)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_set_tc_act_tests(self)

class MplsActNonTagSetTtl(MplsActNonTagPop):
    """
    MPLS action test with untagged pkts (Set TTL)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_set_ttl_act_tests(self)

class MplsActNonTagDecTtl(MplsActNonTagPop):
    """
    MPLS action test with untagged pkts (Dec TTL)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_dec_ttl_act_tests(self)

class MplsActNonTagPush(MplsActNonTagPop):
    """
    MPLS action test with untagged pkts (Push)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_push_act_tests(self)

class MplsActNonTagPushAndTtlInOut(MplsActNonTagPop):
    """
    MPLS action test with untagged pkts
    Push+TTLin/out actions. The result should be the same as single Push act
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush1_act_tests(self)

class MplsActNonTagPushAndSet(MplsActNonTagPop):
    """
    MPLS action test with untagged pkts
    Push+set label/tc/ttl/dec_ttl actions
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush2_act_tests(self)

class MplsActNonTagPushAndSetOutrange(MplsActNonTagPop):
    """
    MPLS action test with untagged pkts
    Push+set label/tc with outrange values
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush3_act_tests(self)

class MplsActOneTagPop(MplsActNonTagPop):
    """
    MPLS action test with tagged pkts (Pop)
    Test on one pair of ports
    """
    def __init__(self):
        MplsActNonTagPop.__init__(self)
        self.num_tags = 1
        self.label = random.randint(16, 1048573)
        self.tc = random.randint(0,5)
        self.ttl = 64
        self.label_match = self.label
        self.tc_match = self.tc

    def runTest(self):
        mpls_pop_act_tests(self)

class MplsActOneTagTtlIn(MplsActOneTagPop):
    """
    MPLS action test with tagged pkts (Copy TTL in)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_ttl_in_act_tests(self)

class MplsActOneTagTtlOut(MplsActOneTagPop):
    """
    MPLS action test with tagged pkts (Copy TTL out)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_ttl_out_act_tests(self)

class MplsActOneTagSetLabel(MplsActOneTagPop):
    """
    MPLS action test with tagged pkts (Set label)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_set_label_act_tests(self)

class MplsActOneTagSetTc(MplsActOneTagPop):
    """
    MPLS action test with tagged pkts (Set TC)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_set_tc_act_tests(self)

class MplsActOneTagSetTtl(MplsActOneTagPop):
    """
    MPLS action test with tagged pkts (Set TTL)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_set_ttl_act_tests(self)

class MplsActOneTagDecTtl(MplsActOneTagPop):
    """
    MPLS action test with tagged pkts (Dec TTL)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_dec_ttl_act_tests(self)

class MplsActOneTagPush(MplsActOneTagPop):
    """
    MPLS action test with tagged pkts (Push)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_push_act_tests(self)

class MplsActOneTagPushAndTtlInOut(MplsActOneTagPop):
    """
    MPLS action test with tagged pkts
    Push+TTLin/out actions. The result should be the same as single Push act
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush1_act_tests(self)

class MplsActOneTagPushAndSet(MplsActOneTagPop):
    """
    MPLS action test with tagged pkts
    Push+set label/tc/ttl/dec_ttl actions
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush2_act_tests(self)

class MplsActOneTagPushAndSetOutrange(MplsActOneTagPop):
    """
    MPLS action test with tagged pkts
    Push+set label/tc with outrange values
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush3_act_tests(self)

class MplsActTwoTagPop(MplsActNonTagPop):
    """
    MPLS action test with two-tagged pkts (pop)
    Test on one pair of ports
    """
    def __init__(self):
        MplsActNonTagPop.__init__(self)
        self.num_tags = 2
        self.label = random.randint(16, 1048573)
        self.tc = random.randint(0,5)
        self.ttl = 64
        self.label_int = self.label + 1
        self.tc_int = self.tc + 1
        self.ttl_int = 32
        self.label_match = self.label
        self.tc_match = self.tc

    def runTest(self):
        mpls_pop_act_tests(self)

class MplsActTwoTagTtlIn(MplsActTwoTagPop):
    """
    MPLS action test with two-tagged pkts (Copy TTL in)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_ttl_in_act_tests(self)

class MplsActTwoTagTtlOut(MplsActTwoTagPop):
    """
    MPLS action test with two-tagged pkts (Copy TTL out)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_ttl_out_act_tests(self)

class MplsActTwoTagSetLabel(MplsActTwoTagPop):
    """
    MPLS action test with two-tagged pkts (Set label)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_set_label_act_tests(self)

class MplsActTwoTagSetTc(MplsActTwoTagPop):
    """
    MPLS action test with two-tagged pkts (Set TC)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_set_tc_act_tests(self)

class MplsActTwoTagSetTtl(MplsActTwoTagPop):
    """
    MPLS action test with two-tagged pkts (Set TTL)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_set_ttl_act_tests(self)

class MplsActTwoTagDecTtl(MplsActTwoTagPop):
    """
    MPLS action test with two-tagged pkts (Dec TTL)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_dec_ttl_act_tests(self)

class MplsActTwoTagPush(MplsActTwoTagPop):
    """
    MPLS action test with two-tagged pkts (Push)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_push_act_tests(self)

class MplsActTwoTagPushAndTtlInOut(MplsActTwoTagPop):
    """
    MPLS action test with two-tagged pkts
    Push+TTLin/out actions. The result should be the same as single Push act
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush1_act_tests(self)

class MplsActTwoTagPushAndSet(MplsActTwoTagPop):
    """
    MPLS action test with two-tagged pkts
    Push+set label/tc/ttl/dec_ttl actions
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush2_act_tests(self)

class MplsActTwoTagPushAndSetOutrange(MplsActTwoTagPop):
    """
    MPLS action test with two-tagged pkts
    Push+set label/tc with outrange values
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush3_act_tests(self)


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
    Test mpls pop action for the packets with/without tags

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    parent.assertTrue(((parent.num_tags>=0) and (parent.num_tags<=2)),
        "Parameter num_tags not within an acceptable range")

    sup_mpls_act = mpls_action_support_check(parent)

    if sup_mpls_act.has_key('sup_pop_mpls') == False:
        skip_message_emit(parent, "MPLS pop action test. POP not supported")
        return

    act = action.action_pop_mpls()
    act.ethertype = 0x8847 if parent.num_tags > 1 else 0x0800

    if parent.num_tags == 0:
        match_exp = False
        exp_msg = ofp.OFPT_ERROR
        exp_msg_type = ofp.OFPET_BAD_ACTION
        exp_msg_code = ofp.OFPBAC_MATCH_INCONSISTENT

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
                    exp_mpls_ttl=exp_ttl,
                    match_exp=match_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    action_list=action_list,
                    max_test=1)

def mpls_ttl_in_act_tests(parent):
    """
    Test mpls ttl_in action for the packets with/without tags
    It tests if outermost TTL value has been copied to the next outermost TTL

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    parent.assertTrue(((parent.num_tags>=0) and (parent.num_tags<=2)),
        "Parameter num_tags not within an acceptable range")

    sup_mpls_act = mpls_action_support_check(parent)

    if sup_mpls_act.has_key('sup_copy_ttl_in') == False:
        skip_message_emit(parent,
            "MPLS copy_ttl_in action test. TTL_IN not supported")
        return

    act = action.action_copy_ttl_in()

    exp_label = parent.label
    exp_tc = parent.tc
    exp_ttl = parent.ttl
    exp_ttl_int = parent.ttl_int
    exp_ip_ttl = parent.ip_ttl

    if parent.num_tags == 0:
        match_exp = False
        exp_msg = ofp.OFPT_ERROR
        exp_msg_type = ofp.OFPET_BAD_ACTION
        exp_msg_code = ofp.OFPBAC_MATCH_INCONSISTENT

    else:
        match_exp = True
        exp_msg = ofp.OFPT_FLOW_REMOVED
        exp_msg_type = 0 #NOT_EXPECTED
        exp_msg_code = 0 #NOT_EXPECTED
        exp_ttl_int = parent.ttl

    action_list=[act]

    flow_match_test_mpls(parent, pa_port_map,
                    wildcards=0,
                    mpls_label=parent.label,
                    mpls_tc=parent.tc,
                    mpls_ttl=parent.ttl,
                    mpls_label_int=parent.label_int,
                    mpls_tc_int=parent.tc_int,
                    mpls_ttl_int=parent.ttl_int,
                    ip_ttl=parent.ip_ttl,
                    label_match=parent.label_match,
                    tc_match=parent.tc_match,
                    exp_mpls_label=exp_label,
                    exp_mpls_tc=exp_tc,
                    exp_mpls_ttl=exp_ttl,
                    exp_mpls_ttl_int=exp_ttl_int,
                    exp_ip_ttl=exp_ip_ttl,
                    match_exp=match_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    action_list=action_list,
                    max_test=1)

def mpls_ttl_out_act_tests(parent):
    """
    Test mpls ttl_out action for the packets with/without tags
    It tests if the second-outermost TTL value has been copied to the
    outermost TTL

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    parent.assertTrue(((parent.num_tags>=0) and (parent.num_tags<=2)),
        "Parameter num_tags not within an acceptable range")

    sup_mpls_act = mpls_action_support_check(parent)

    if sup_mpls_act.has_key('sup_copy_ttl_out') == False:
        skip_message_emit(parent,
            "MPLS copy_ttl_out action test. TTL_OUT not supported")
        return

    act = action.action_copy_ttl_out()

    exp_label = parent.label
    exp_tc = parent.tc
    exp_ttl = parent.ttl

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
        exp_ttl = parent.ip_ttl

    else:
        match_exp = True
        exp_msg = ofp.OFPT_FLOW_REMOVED
        exp_msg_type = 0 #NOT_EXPECTED
        exp_msg_code = 0 #NOT_EXPECTED
        exp_ttl = parent.ttl_int

    action_list=[act]

    flow_match_test_mpls(parent, pa_port_map,
                    wildcards=0,
                    mpls_label=parent.label,
                    mpls_tc=parent.tc,
                    mpls_ttl=parent.ttl,
                    mpls_label_int=parent.label_int,
                    mpls_tc_int=parent.tc_int,
                    mpls_ttl_int=parent.ttl_int,
                    ip_ttl=parent.ip_ttl,
                    label_match=parent.label_match,
                    tc_match=parent.tc_match,
                    exp_mpls_label=exp_label,
                    exp_mpls_tc=exp_tc,
                    exp_mpls_ttl=exp_ttl,
                    match_exp=match_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    action_list=action_list,
                    max_test=1)

def mpls_set_label_act_tests(parent):
    """
    Test mpls set_label action for the packets with/without tags

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    parent.assertTrue(((parent.num_tags>=0) and (parent.num_tags<=2)),
        "Parameter num_tags not within an acceptable range")

    sup_mpls_act = mpls_action_support_check(parent)

    if sup_mpls_act.has_key('sup_set_mpls_label') == False:
        skip_message_emit(parent,
            "MPLS set_label action test. SET_LABEL not supported")
        return

    act = action.action_set_mpls_label()

    exp_tc = parent.tc
    exp_ttl = parent.ttl

    for test_condition in range(2):
        if test_condition == 0:
            act.mpls_label = parent.label + 2
            if parent.num_tags == 0:
                match_exp = False
                exp_msg = ofp.OFPT_ERROR
                exp_msg_type = ofp.OFPET_BAD_ACTION
                exp_msg_code = ofp.OFPBAC_MATCH_INCONSISTENT
                exp_label = parent.label

            else:
                match_exp = True
                exp_msg = ofp.OFPT_FLOW_REMOVED
                exp_msg_type = 0 #NOT_EXPECTED
                exp_msg_code = 0 #NOT_EXPECTED
                exp_label = act.mpls_label

            action_list=[act]

        elif test_condition == 1:
            act.mpls_label = parent.label + 1048576
            if parent.num_tags == 0:
                match_exp = False
                exp_msg = ofp.OFPT_ERROR
                exp_msg_type = ofp.OFPET_BAD_ACTION
                exp_msg_code = ofp.OFPBAC_MATCH_INCONSISTENT
                exp_label = parent.label

            else:
                match_exp = True
                exp_msg = ofp.OFPT_ERROR
                exp_msg_type = ofp.OFPET_BAD_ACTION
                exp_msg_code = ofp.OFPBAC_BAD_ARGUMENT
                exp_label = act.mpls_label

            action_list=[act]

            flow_match_test_mpls(parent, pa_port_map,
                    wildcards=0,
                    mpls_label=parent.label,
                    mpls_tc=parent.tc,
                    mpls_ttl=parent.ttl,
                    mpls_label_int=parent.label_int,
                    mpls_tc_int=parent.tc_int,
                    mpls_ttl_int=parent.ttl_int,
                    ip_ttl=parent.ip_ttl,
                    label_match=parent.label_match,
                    tc_match=parent.tc_match,
                    exp_mpls_label=exp_label,
                    exp_mpls_tc=exp_tc,
                    exp_mpls_ttl=exp_ttl,
                    match_exp=match_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    action_list=action_list,
                    max_test=1)

def mpls_set_tc_act_tests(parent):
    """
    Test mpls set_tc action for the packets with/without tags

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    parent.assertTrue(((parent.num_tags>=0) and (parent.num_tags<=2)),
        "Parameter num_tags not within an acceptable range")

    sup_mpls_act = mpls_action_support_check(parent)

    if sup_mpls_act.has_key('sup_set_mpls_tc') == False:
        skip_message_emit(parent,
            "MPLS set_tc action test. SET_TC not supported")
        return

    act = action.action_set_mpls_tc()

    exp_label = parent.label
    exp_ttl = parent.ttl

    for test_condition in range(2):
        if test_condition == 0:
            act.mpls_tc = parent.tc + 2
            if parent.num_tags == 0:
                match_exp = False
                exp_msg = ofp.OFPT_ERROR
                exp_msg_type = ofp.OFPET_BAD_ACTION
                exp_msg_code = ofp.OFPBAC_MATCH_INCONSISTENT
                exp_tc = parent.tc

            else:
                match_exp = True
                exp_msg = ofp.OFPT_FLOW_REMOVED
                exp_msg_type = 0 #NOT_EXPECTED
                exp_msg_code = 0 #NOT_EXPECTED
                exp_tc = act.mpls_tc

            action_list=[act]

        elif test_condition == 1:
            act.mpls_tc = parent.tc + 7
            if parent.num_tags == 0:
                match_exp = False
                exp_msg = ofp.OFPT_ERROR
                exp_msg_type = ofp.OFPET_BAD_ACTION
                exp_msg_code = ofp.OFPBAC_MATCH_INCONSISTENT
                exp_label = parent.label

            else:
                match_exp = True
                exp_msg = ofp.OFPT_ERROR
                exp_msg_type = ofp.OFPET_BAD_ACTION
                exp_msg_code = ofp.OFPBAC_BAD_ARGUMENT
                exp_label = act.mpls_tc

            action_list=[act]

            flow_match_test_mpls(parent, pa_port_map,
                    wildcards=0,
                    mpls_label=parent.label,
                    mpls_tc=parent.tc,
                    mpls_ttl=parent.ttl,
                    mpls_label_int=parent.label_int,
                    mpls_tc_int=parent.tc_int,
                    mpls_ttl_int=parent.ttl_int,
                    ip_ttl=parent.ip_ttl,
                    label_match=parent.label_match,
                    tc_match=parent.tc_match,
                    exp_mpls_label=exp_label,
                    exp_mpls_tc=exp_tc,
                    exp_mpls_ttl=exp_ttl,
                    match_exp=match_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    action_list=action_list,
                    max_test=1)

def mpls_set_ttl_act_tests(parent):
    """
    Test mpls set_ttl action for the packets with/without tags

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    parent.assertTrue(((parent.num_tags>=0) and (parent.num_tags<=2)),
        "Parameter num_tags not within an acceptable range")

    sup_mpls_act = mpls_action_support_check(parent)

    if sup_mpls_act.has_key('sup_set_mpls_ttl') == False:
        skip_message_emit(parent,
            "MPLS set_ttl action test. SET_TTL not supported")
        return

    act = action.action_set_mpls_ttl()

    exp_label = parent.label
    exp_tc = parent.tc

    act.mpls_ttl = parent.ttl + 2
    if parent.num_tags == 0:
        match_exp = False
        exp_msg = ofp.OFPT_ERROR
        exp_msg_type = ofp.OFPET_BAD_ACTION
        exp_msg_code = ofp.OFPBAC_MATCH_INCONSISTENT
        exp_ttl = parent.ttl

    else:
        match_exp = True
        exp_msg = ofp.OFPT_FLOW_REMOVED
        exp_msg_type = 0 #NOT_EXPECTED
        exp_msg_code = 0 #NOT_EXPECTED
        exp_ttl = act.mpls_ttl

    action_list=[act]

    flow_match_test_mpls(parent, pa_port_map,
                    wildcards=0,
                    mpls_label=parent.label,
                    mpls_tc=parent.tc,
                    mpls_ttl=parent.ttl,
                    mpls_label_int=parent.label_int,
                    mpls_tc_int=parent.tc_int,
                    mpls_ttl_int=parent.ttl_int,
                    ip_ttl=parent.ip_ttl,
                    label_match=parent.label_match,
                    tc_match=parent.tc_match,
                    exp_mpls_label=exp_label,
                    exp_mpls_tc=exp_tc,
                    exp_mpls_ttl=exp_ttl,
                    match_exp=match_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    action_list=action_list,
                    max_test=1)

def mpls_dec_ttl_act_tests(parent):
    """
    Test mpls dec_ttl action for the packets with/without tags

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    parent.assertTrue(((parent.num_tags>=0) and (parent.num_tags<=2)),
        "Parameter num_tags not within an acceptable range")

    sup_mpls_act = mpls_action_support_check(parent)

    if sup_mpls_act.has_key('sup_dec_mpls_ttl') == False:
        skip_message_emit(parent,
            "MPLS dec_ttl action test. DEC_TTL not supported")
        return

    act = action.action_dec_mpls_ttl()

    exp_label = parent.label
    exp_tc = parent.tc

    if parent.num_tags == 0:
        match_exp = False
        exp_msg = ofp.OFPT_ERROR
        exp_msg_type = ofp.OFPET_BAD_ACTION
        exp_msg_code = ofp.OFPBAC_MATCH_INCONSISTENT
        exp_ttl = parent.ttl

    else:
        match_exp = True
        exp_msg = ofp.OFPT_FLOW_REMOVED
        exp_msg_type = 0 #NOT_EXPECTED
        exp_msg_code = 0 #NOT_EXPECTED
        exp_ttl = parent.ttl - 1

    action_list=[act]

    flow_match_test_mpls(parent, pa_port_map,
                    wildcards=0,
                    mpls_label=parent.label,
                    mpls_tc=parent.tc,
                    mpls_ttl=parent.ttl,
                    mpls_label_int=parent.label_int,
                    mpls_tc_int=parent.tc_int,
                    mpls_ttl_int=parent.ttl_int,
                    ip_ttl=parent.ip_ttl,
                    label_match=parent.label_match,
                    tc_match=parent.tc_match,
                    exp_mpls_label=exp_label,
                    exp_mpls_tc=exp_tc,
                    exp_mpls_ttl=exp_ttl,
                    match_exp=match_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    action_list=action_list,
                    max_test=1)

def mpls_push_act_tests(parent):
    """
    Test mpls push action for the packets with/without tags

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    parent.assertTrue(((parent.num_tags>=0) and (parent.num_tags<=2)),
        "Parameter num_tags not within an acceptable range")

    sup_mpls_act = mpls_action_support_check(parent)

    if sup_mpls_act.has_key('sup_push_mpls') == False:
        skip_message_emit(parent, "MPLS push action test. PUSH not supported")
        return

    act = action.action_push_mpls()
    act.ethertype = 0x8847

    if parent.num_tags == 0:
        exp_label = 0
        exp_tc = 0
        exp_ttl = parent.ip_ttl

    else:
        exp_label = parent.label
        exp_tc = parent.tc
        exp_ttl = parent.ttl

    match_exp = True
    add_tag_exp = parent.num_tags > 0
    exp_msg = ofp.OFPT_FLOW_REMOVED
    exp_msg_type = 0 #NOT_EXPECTED
    exp_msg_code = 0 #NOT_EXPECTED

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
                    exp_mpls_ttl=exp_ttl,
                    match_exp=match_exp,
                    add_tag_exp=add_tag_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    action_list=action_list,
                    max_test=1)

def mpls_multipush1_act_tests(parent):
    """
    Test mpls push and copy actions for the packets with/without tags

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    parent.assertTrue(((parent.num_tags>=0) and (parent.num_tags<=2)),
        "Parameter num_tags not within an acceptable range")

    sup_mpls_act = mpls_action_support_check(parent)

    if sup_mpls_act.has_key('sup_push_mpls') == False:
        skip_message_emit(parent,
            "MPLS multipush action test. PUSH not supported")
        return
    if sup_mpls_act.has_key('sup_copy_ttl_in') == False:
        skip_message_emit(parent,
            "MPLS multipush action test. TTL_IN not supported")
        return
    if sup_mpls_act.has_key('sup_copy_ttl_out') == False:
        skip_message_emit(parent,
            "MPLS multipush action test. TTL_OUT not supported")
        return

    act = action.action_push_mpls()
    act.ethertype = 0x8847

    for test_condition in range(2):
        if test_condition == 0:
            act2 = action.action_copy_ttl_in()
        elif test_condition == 1:
            act2 = action.action_copy_ttl_out()

        if parent.num_tags == 0:
            exp_label = 0
            exp_tc = 0
            exp_ttl = parent.ip_ttl
        else:
            exp_label = parent.label
            exp_tc = parent.tc
            exp_ttl = parent.ttl

        match_exp = True
        add_tag_exp = True
        exp_msg = ofp.OFPT_FLOW_REMOVED
        exp_msg_type = 0 #NOT_EXPECTED
        exp_msg_code = 0 #NOT_EXPECTED

        action_list=[act, act2]

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
                    exp_mpls_ttl=exp_ttl,
                    match_exp=match_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    action_list=action_list,
                    max_test=1)

def mpls_multipush2_act_tests(parent):
    """
    Test mpls push and set actions for the packets with/without tags

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    parent.assertTrue(((parent.num_tags>=0) and (parent.num_tags<=2)),
        "Parameter num_tags not within an acceptable range")

    sup_mpls_act = mpls_action_support_check(parent)

    if sup_mpls_act.has_key('sup_push_mpls') == False:
        skip_message_emit(parent,
            "MPLS multipush action test. PUSH not supported")
        return
    if sup_mpls_act.has_key('sup_set_mpls_label') == False:
        skip_message_emit(parent,
            "MPLS multipush action test. SET_LABEL not supported")
        return
    if sup_mpls_act.has_key('sup_set_mpls_tc') == False:
        skip_message_emit(parent,
            "MPLS multipush action test. SET_TC not supported")
        return
    if sup_mpls_act.has_key('sup_set_mpls_ttl') == False:
        skip_message_emit(parent,
            "MPLS multipush action test. SET_TTL not supported")
        return
    if sup_mpls_act.has_key('sup_dec_mpls_ttl') == False:
        skip_message_emit(parent,
            "MPLS multipush action test. DEC_TTL not supported")
        return

    act = action.action_push_mpls()
    act.ethertype = 0x8847

    for test_condition in range(4):
        if test_condition == 0:
            act2 = action.action_set_mpls_label()
            act2.mpls_label = parent.label + 2
            exp_label = act2.mpls_label
            if parent.num_tags == 0:
                exp_tc = 0
                exp_ttl = parent.ip_ttl
            else:
                exp_tc = parent.tc
                exp_ttl = parent.ttl
        elif test_condition == 1:
            act2 = action.action_set_mpls_tc()
            act2.mpls_tc = parent.tc + 2
            exp_tc = act2.mpls_tc
            if parent.num_tags == 0:
                exp_label = 0
                exp_ttl = parent.ip_ttl
            else:
                exp_label = parent.label
                exp_ttl = parent.ttl
        elif test_condition == 2:
            act2 = action.action_set_mpls_ttl()
            act2.mpls_ttl = parent.ttl + 2
            exp_ttl = act2.mpls_ttl
            if parent.num_tags == 0:
                exp_label = 0
                exp_tc = 0
            else:
                exp_label = parent.label
                exp_tc = parent.tc
        elif test_condition == 3:
            act2 = action.action_dec_mpls_ttl()
            if parent.num_tags == 0:
                exp_ttl = parent.ip_ttl - 1
                exp_label = 0
                exp_tc = 0
            else:
                exp_ttl = parent.ttl - 1
                exp_label = parent.label
                exp_tc = parent.tc

        match_exp = True
        add_tag_exp = parent.num_tags > 0
        exp_msg = ofp.OFPT_FLOW_REMOVED
        exp_msg_type = 0 #NOT_EXPECTED
        exp_msg_code = 0 #NOT_EXPECTED

        action_list=[act, act2]

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
                    exp_mpls_ttl=exp_ttl,
                    match_exp=match_exp,
                    add_tag_exp=add_tag_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    action_list=action_list,
                    max_test=1)

def mpls_multipush3_act_tests(parent):
    """
    Test mpls push and set with out-of-range value actions for the packets
    with/without tags

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    parent.assertTrue(((parent.num_tags>=0) and (parent.num_tags<=2)),
        "Parameter num_tags not within an acceptable range")

    sup_mpls_act = mpls_action_support_check(parent)

    if sup_mpls_act.has_key('sup_push_mpls') == False:
        skip_message_emit(parent,
            "MPLS multipush action test. PUSH not supported")
        return
    if sup_mpls_act.has_key('sup_set_mpls_label') == False:
        skip_message_emit(parent,
            "MPLS multipush action test. SET_LABEL not supported")
        return
    if sup_mpls_act.has_key('sup_set_mpls_tc') == False:
        skip_message_emit(parent,
            "MPLS multipush action test. SET_TC not supported")
        return

    act = action.action_push_mpls()
    act.ethertype = 0x8847

    for test_condition in range(2):
        if test_condition == 0:
            act2 = action.action_set_mpls_label()
            act2.mpls_label = parent.label + 1048576
            exp_label = act2.mpls_label
            exp_tc = 0
            exp_ttl = 0 # Not expected
        elif test_condition == 1:
            act2 = action.action_set_mpls_tc()
            act2.mpls_tc = parent.tc + 8
            exp_tc = act2.mpls_tc
            exp_label = 0
            exp_ttl = 0 # Not expected

        match_exp = False
        exp_msg = ofp.OFPT_ERROR
        exp_msg_type = ofp.OFPET_BAD_ACTION
        exp_msg_code = ofp.OFPBAC_BAD_ARGUMENT

        action_list=[act, act2]

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
                    exp_mpls_ttl=exp_ttl,
                    match_exp=match_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    action_list=action_list,
                    max_test=1)

if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test-spec=mplsact"
