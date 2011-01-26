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

import logging

import random
import oftest.cstruct as ofp
import oftest.message as message
import oftest.action as action
import oftest.parse as parse
import basic
import pktact

import testutils

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

    pa_logger = logging.getLogger("mpls_act")
    pa_logger.info("Initializing test set")
    pa_port_map = config["port_map"]
    pa_config = config

################################################################

class MplsActNonTagPush(pktact.BaseMatchCase):
    """
    MPLS push action (0x8847) test with untagged pkt
    Expectation: Pkt with MPLS (LABEL=0 TC=0 TTL=same as in IP)
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
        mpls_push_act_tests(self)

class MplsActNonTagPushTtlIn(MplsActNonTagPush):
    """
    MPLS push and TTL-in action test with untagged pkts
    Expectation: Pkt with MPLS (LABEL=0 TC=0 TTL=same as in IP)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush1_act_tests(self, test_condition=0)

class MplsActNonTagPushTtlOut(MplsActNonTagPush):
    """
    MPLS push and TTL-out action test with untagged pkts
    Expectation: Pkt with MPLS (LABEL=0 TC=0 TTL=same as in IP)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush1_act_tests(self, test_condition=1)

class MplsActNonTagPushSetLabel(MplsActNonTagPush):
    """
    MPLS Push and Set LABEL action test with untagged pkt
    Expectation: Pkt with MPLS (LABEL=Set value TC=0)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush2_act_tests(self, test_condition=0)

class MplsActNonTagPushSetTc(MplsActNonTagPush):
    """
    MPLS Push and Set TC action test with untagged pkt
    Expectation: Pkt with MPLS (LABEL=0 TC=Set value)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush2_act_tests(self, test_condition=1)

class MplsActNonTagPushSetTtl(MplsActNonTagPush):
    """
    MPLS Push and Set TTL action test with untagged pkt
    Expectation: Pkt with MPLS (LABEL=0 TC=0 TTL=Set value)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush2_act_tests(self, test_condition=2)

class MplsActNonTagPushDecTtl(MplsActNonTagPush):
    """
    MPLS Push and TTL decrement action test with untagged pkt
    Expectation: Pkt with MPLS (LABEL=0 TC=0 TTL=IP's value-1)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush2_act_tests(self, test_condition=3)

class MplsActNonTagPushSetOutrange0(MplsActNonTagPush):
    """
    MPLS set LABEL action (outrange value) test with untagged pkt
    Expectation: OFPET_BAD_ACTION (BAD ARG) error
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush3_act_tests(self, test_condition=0)

class MplsActNonTagPushSetOutrange1(MplsActNonTagPush):
    """
    MPLS set TC action test with untagged pkt
    Expectation: OFPET_BAD_ACTION (INCONSISTENT) error
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush3_act_tests(self, test_condition=1)

class MplsActOneTagPop(MplsActNonTagPush):
    """
    MPLS pop action test with tagged pkt
    Expectation: Pkt w/o MPLS
    Test on one pair of ports
    """
    def __init__(self):
        MplsActNonTagPush.__init__(self)
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
    MPLS Copy TTL inward with tagged pkt
    Expectation: Pkt with MPLS (MPLS TTL=same as in IP)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_ttl_in_act_tests(self)

class MplsActOneTagTtlOut(MplsActOneTagPop):
    """
    MPLS Copy TTL outward with tagged pkt
    Expectation: Pkt with MPLS (IP TTL=same as in MPLS)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_ttl_out_act_tests(self)

class MplsActOneTagSetLabel0(MplsActOneTagPop):
    """
    MPLS set LABEL action test with tagged pkt
    Expectation: LABEL=Set value
    Test on one pair of ports
    """
    def runTest(self):
        mpls_set_label_act_tests(self, test_condition=0)

class MplsActOneTagSetLabel1(MplsActOneTagPop):
    """
    MPLS set LABEL action (outrange value) test with tagged pkt
    Expectation: OFPET_BAD_ACTION (BAD ARG) error
    Test on one pair of ports
    """
    def runTest(self):
        mpls_set_label_act_tests(self, test_condition=1)

class MplsActOneTagSetTc0(MplsActOneTagPop):
    """
    MPLS set action test with tagged pkt
    Expectation: TC=Set value
    Test on one pair of ports
    """
    def runTest(self):
        mpls_set_tc_act_tests(self, test_condition=0)

class MplsActOneTagSetTc1(MplsActOneTagPop):
    """
    MPLS set action test with tagged pkt
    Expectation: OFPET_BAD_ACTION (BAD ARG) error
    Test on one pair of ports
    """
    def runTest(self):
        mpls_set_tc_act_tests(self, test_condition=1)

class MplsActOneTagSetTtl(MplsActOneTagPop):
    """
    MPLS Set TTL action test with tagged pkt
    Expectation: Pkt with MPLS (TTL=set value)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_set_ttl_act_tests(self)

class MplsActOneTagDecTtl(MplsActOneTagPop):
    """
    MPLS TTL decrement action test with tagged pkt
    Expectation: Pkt with MPLS (TTL=Current-1)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_dec_ttl_act_tests(self)

class MplsActOneTagPush(MplsActOneTagPop):
    """
    MPLS push action (0x8847) test with tagged pkt
    Expectation: Pkt with two MPLSs
     - Outer MPLS LABEL=Set value
     - Outer and Inner MPLS should have the same values
    Test on one pair of ports
    """
    def runTest(self):
        mpls_push_act_tests(self)

class MplsActOneTagPushTtlIn(MplsActOneTagPop):
    """
    MPLS push and TTL-in action test with tagged pkt
    Expectation: Pkt with two MPLS tags
    (LABEL, TC, TTL=same as in current tag)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush1_act_tests(self, test_condition=0)

class MplsActOneTagPushTtlOut(MplsActOneTagPop):
    """
    MPLS push and TTL-out action test with tagged pkt
    Expectation: Pkt with two MPLS tags
    (LABEL, TC, TTL=same as in current tag)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush1_act_tests(self, test_condition=1)

class MplsActOneTagPushSetLabel(MplsActOneTagPop):
    """
    MPLS Push and Set LABEL action test with tagged pkt
    Expectation: Pkt with two MPLS tags
     - Outer MPLS LABEL=Set value
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush2_act_tests(self, test_condition=0)

class MplsActOneTagPushSetTc(MplsActOneTagPop):
    """
    MPLS Push and Set TC action test with tagged pkt
    Expectation: Pkt with two MPLS tags
     - Outer MPLS TC=Set value
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush2_act_tests(self, test_condition=1)

class MplsActOneTagPushSetTtl(MplsActOneTagPop):
    """
    MPLS Push and Set TTL action test with tagged pkt
    Expectation: Pkt with two MPLS tags
     - Outer MPLS TTL=Set value
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush2_act_tests(self, test_condition=2)

class MplsActOneTagPushDecTtl(MplsActOneTagPop):
    """
    MPLS Push and TTL decrement action test with tagged pkt
    Expectation: Pkt with two MPLS tags
     - Outer MPLS TTL= Inner tag's value-1
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush2_act_tests(self, test_condition=3)

class MplsActOneTagPushSetOutrange0(MplsActOneTagPop):
    """
    MPLS push and set LABEL action (outrange value) test with tagged pkt
    Expectation: OFPET_BAD_ACTION (BAD ARG) error
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush3_act_tests(self, test_condition=0)

class MplsActOneTagPushSetOutrange1(MplsActOneTagPop):
    """
    MPLS push and set TC action (outrange value) test with tagged pkt
    Expectation: OFPET_BAD_ACTION (BAD ARG) error
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush3_act_tests(self, test_condition=1)

class MplsActTwoTagPop(MplsActNonTagPush):
    """
    MPLS pop action test with two-tagged pkt
    Expectation: Outer MPLS tag to be removed
    Test on one pair of ports
    """
    def __init__(self):
        MplsActNonTagPush.__init__(self)
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
    MPLS Copy TTL inward with two-tagged pkt
    Expectation: Pkt with MPLS (Outer MPLS TTL=same as in Inner MPLS)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_ttl_in_act_tests(self)

class MplsActTwoTagTtlOut(MplsActTwoTagPop):
    """
    MPLS Copy TTL outward with two-tagged pkt
    Expectation: Pkt with MPLS (Inner MPLS TTL=same as in Outer MPLS)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_ttl_out_act_tests(self)

class MplsActTwoTagSetLabel0(MplsActTwoTagPop):
    """
    MPLS set LABEL action test with two-tagged pkt
    Expectation: LABEL=Set value
    Test on one pair of ports
    """
    def runTest(self):
        mpls_set_label_act_tests(self, test_condition=0)

class MplsActTwoTagSetLabel1(MplsActTwoTagPop):
    """
    MPLS set LABEL action (outrange value) test with two-tagged pkt
    Expectation: OFPET_BAD_ACTION (BAD ARG) error
    Test on one pair of ports
    """
    def runTest(self):
        mpls_set_label_act_tests(self, test_condition=1)

class MplsActTwoTagSetTc0(MplsActTwoTagPop):
    """
    MPLS set TC action test with two-tagged pkt
    Expectation: TC=Set value
    Test on one pair of ports
    """
    def runTest(self):
        mpls_set_tc_act_tests(self, test_condition=0)

class MplsActTwoTagSetTc1(MplsActTwoTagPop):
    """
    MPLS set TC action (outrange value) test with two-tagged pkt
    Expectation: OFPET_BAD_ACTION (BAD ARG) error
    Test on one pair of ports
    """
    def runTest(self):
        mpls_set_tc_act_tests(self, test_condition=1)

class MplsActTwoTagSetTtl(MplsActTwoTagPop):
    """
    MPLS set TTL action test with two-tagged pkt
    Expectation: TTL=Set value
    Test on one pair of ports
    """
    def runTest(self):
        mpls_set_ttl_act_tests(self)

class MplsActTwoTagDecTtl(MplsActTwoTagPop):
    """
    MPLS TTL decrement action test with two-tagged pkt
    Expectation: TTL=Inner tag's value-1
    Test on one pair of ports
    """
    def runTest(self):
        mpls_dec_ttl_act_tests(self)

class MplsActTwoTagPush(MplsActTwoTagPop):
    """
    MPLS push action (0x8847) test with two-tagged pkt
    Expectation: Pkt with three MPLS tags
     - Outer most and second MPLS should have the same values
    Test on one pair of ports
    """
    def runTest(self):
        mpls_push_act_tests(self)

class MplsActTwoTagPushTtlIn(MplsActTwoTagPop):
    """
    MPLS push and TTL-in action test with two-tagged pkts
    Expectation: Pkt with three MPLS (LABEL=0 TC=0 TTL=same as in Inner)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush1_act_tests(self,test_condition=0)

class MplsActTwoTagPushTtlOut(MplsActTwoTagPop):
    """
    MPLS push and TTL-out action test with two-tagged pkts
    Expectation: Pkt with three MPLS tags
    (Outer LABEL=0 Outer TC=0 Inner TTL=same as outer)
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush1_act_tests(self,test_condition=1)

class MplsActTwoTagPushSetLabel(MplsActTwoTagPop):
    """
    MPLS Push and Set LABEL action test with two-tagged pkt
    Expectation: Pkt with three MPLS tags
     - Outer most MPLS LABEL=Set Value
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush2_act_tests(self, test_condition=0)

class MplsActTwoTagPushSetTc(MplsActTwoTagPop):
    """
    MPLS Push and Set TC action test with two-tagged pkt
    Expectation: Pkt with three MPLS tags
     - Outer most MPLS TC=Set Value
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush2_act_tests(self, test_condition=1)

class MplsActTwoTagPushSetTtl(MplsActTwoTagPop):
    """
    MPLS Push and Set TTL action test with two-tagged pkt
    Expectation: Pkt with three MPLS tags
     - Outer most MPLS TTL=Set Value
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush2_act_tests(self, test_condition=2)

class MplsActTwoTagPushDecTtl(MplsActTwoTagPop):
    """
    MPLS Push and Set TTL action test with two-tagged pkt
    Expectation: Pkt with three MPLS tags
     - Outer most MPLS TTL=Inner-1
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush2_act_tests(self, test_condition=3)

class MplsActTwoTagPushSetOutrange0(MplsActTwoTagPop):
    """
    MPLS push and set LABEL action (outrange value) test with two-tagged pkt
    Expectation: OFPET_BAD_ACTION (BAD ARG) error
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush3_act_tests(self, test_condition=0)

class MplsActTwoTagPushSetOutrange1(MplsActTwoTagPop):
    """
    MPLS push and set TC action (outrange value) test with two-tagged pkt
    Expectation: OFPET_BAD_ACTION (BAD ARG) error
    Test on one pair of ports
    """
    def runTest(self):
        mpls_multipush3_act_tests(self, test_condition=1)


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
        testutils.skip_message_emit(parent, "MPLS pop action test. POP not supported")
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

    testutils.flow_match_test_mpls(parent, pa_port_map,
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
        testutils.skip_message_emit(parent,
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
        
    elif parent.num_tags == 1:
        match_exp = True
        exp_msg = ofp.OFPT_FLOW_REMOVED
        exp_msg_type = 0 #NOT_EXPECTED
        exp_msg_code = 0 #NOT_EXPECTED
        exp_ip_ttl = parent.ttl

    else:
        match_exp = True
        exp_msg = ofp.OFPT_FLOW_REMOVED
        exp_msg_type = 0 #NOT_EXPECTED
        exp_msg_code = 0 #NOT_EXPECTED
        exp_ttl_int = parent.ttl

    action_list=[act]

    testutils.flow_match_test_mpls(parent, pa_port_map,
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
        testutils.skip_message_emit(parent,
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

    testutils.flow_match_test_mpls(parent, pa_port_map,
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

def mpls_set_label_act_tests(parent, test_condition=0):
    """
    Test mpls set_label action for the packets with/without tags

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    parent.assertTrue(((parent.num_tags>=0) and (parent.num_tags<=2)),
        "Parameter num_tags not within an acceptable range")

    sup_mpls_act = mpls_action_support_check(parent)

    if sup_mpls_act.has_key('sup_set_mpls_label') == False:
        testutils.skip_message_emit(parent,
            "MPLS set_label action test. SET_LABEL not supported")
        return

    act = action.action_set_mpls_label()

    exp_tc = parent.tc
    exp_ttl = parent.ttl

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
        act.mpls_label = 1048576
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

    else:
        return

    testutils.flow_match_test_mpls(parent, pa_port_map,
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

def mpls_set_tc_act_tests(parent, test_condition=0):
    """
    Test mpls set_tc action for the packets with/without tags

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    parent.assertTrue(((parent.num_tags>=0) and (parent.num_tags<=2)),
        "Parameter num_tags not within an acceptable range")

    sup_mpls_act = mpls_action_support_check(parent)

    if sup_mpls_act.has_key('sup_set_mpls_tc') == False:
        testutils.skip_message_emit(parent,
            "MPLS set_tc action test. SET_TC not supported")
        return

    act = action.action_set_mpls_tc()

    exp_label = parent.label
    exp_ttl = parent.ttl

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
        act.mpls_tc = 8
        if parent.num_tags == 0:
            match_exp = False
            exp_msg = ofp.OFPT_ERROR
            exp_msg_type = ofp.OFPET_BAD_ACTION
            exp_msg_code = ofp.OFPBAC_MATCH_INCONSISTENT
            exp_tc = parent.tc

        else:
            match_exp = True
            exp_msg = ofp.OFPT_ERROR
            exp_msg_type = ofp.OFPET_BAD_ACTION
            exp_msg_code = ofp.OFPBAC_BAD_ARGUMENT
            exp_tc = act.mpls_tc

        action_list=[act]

    else:
        return

    testutils.flow_match_test_mpls(parent, pa_port_map,
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
        testutils.skip_message_emit(parent,
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

    testutils.flow_match_test_mpls(parent, pa_port_map,
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
        testutils.skip_message_emit(parent,
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

    testutils.flow_match_test_mpls(parent, pa_port_map,
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
        testutils.skip_message_emit(parent, "MPLS push action test. PUSH not supported")
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

    testutils.flow_match_test_mpls(parent, pa_port_map,
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

def mpls_multipush1_act_tests(parent, test_condition=0):
    """
    Test mpls push and copy actions for the packets with/without tags

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    parent.assertTrue(((parent.num_tags>=0) and (parent.num_tags<=2)),
        "Parameter num_tags not within an acceptable range")

    sup_mpls_act = mpls_action_support_check(parent)

    if sup_mpls_act.has_key('sup_push_mpls') == False:
        testutils.skip_message_emit(parent,
            "MPLS multipush action test. PUSH not supported")
        return
    if sup_mpls_act.has_key('sup_copy_ttl_in') == False:
        testutils.skip_message_emit(parent,
            "MPLS multipush action test. TTL_IN not supported")
        return
    if sup_mpls_act.has_key('sup_copy_ttl_out') == False:
        testutils.skip_message_emit(parent,
            "MPLS multipush action test. TTL_OUT not supported")
        return

    act = action.action_push_mpls()
    act.ethertype = 0x8847

    if test_condition == 0:
        act2 = action.action_copy_ttl_in()

    elif test_condition == 1:
        act2 = action.action_copy_ttl_out()

    else:
        return

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

    action_list=[act, act2]

    testutils.flow_match_test_mpls(parent, pa_port_map,
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

def mpls_multipush2_act_tests(parent, test_condition=0):
    """
    Test mpls push and set actions for the packets with/without tags

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    parent.assertTrue(((parent.num_tags>=0) and (parent.num_tags<=2)),
        "Parameter num_tags not within an acceptable range")

    sup_mpls_act = mpls_action_support_check(parent)

    if sup_mpls_act.has_key('sup_push_mpls') == False:
        testutils.skip_message_emit(parent,
            "MPLS multipush action test. PUSH not supported")
        return
    if sup_mpls_act.has_key('sup_set_mpls_label') == False:
        testutils.skip_message_emit(parent,
            "MPLS multipush action test. SET_LABEL not supported")
        return
    if sup_mpls_act.has_key('sup_set_mpls_tc') == False:
        testutils.skip_message_emit(parent,
            "MPLS multipush action test. SET_TC not supported")
        return
    if sup_mpls_act.has_key('sup_set_mpls_ttl') == False:
        testutils.skip_message_emit(parent,
            "MPLS multipush action test. SET_TTL not supported")
        return
    if sup_mpls_act.has_key('sup_dec_mpls_ttl') == False:
        testutils.skip_message_emit(parent,
            "MPLS multipush action test. DEC_TTL not supported")
        return

    act = action.action_push_mpls()
    act.ethertype = 0x8847

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

    else:
        return

    match_exp = True
    add_tag_exp = parent.num_tags > 0
    exp_msg = ofp.OFPT_FLOW_REMOVED
    exp_msg_type = 0 #NOT_EXPECTED
    exp_msg_code = 0 #NOT_EXPECTED

    action_list=[act, act2]

    testutils.flow_match_test_mpls(parent, pa_port_map,
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

def mpls_multipush3_act_tests(parent, test_condition=0):
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
        testutils.skip_message_emit(parent,
            "MPLS multipush action test. PUSH not supported")
        return
    if sup_mpls_act.has_key('sup_set_mpls_label') == False:
        testutils.skip_message_emit(parent,
            "MPLS multipush action test. SET_LABEL not supported")
        return
    if sup_mpls_act.has_key('sup_set_mpls_tc') == False:
        testutils.skip_message_emit(parent,
            "MPLS multipush action test. SET_TC not supported")
        return

    act = action.action_push_mpls()
    act.ethertype = 0x8847

    if test_condition == 0:
        act2 = action.action_set_mpls_label()
        act2.mpls_label = 1048576
        exp_label = act2.mpls_label
        exp_tc = 0
        exp_ttl = 0 # Not expected

    elif test_condition == 1:
        act2 = action.action_set_mpls_tc()
        act2.mpls_tc = 8
        exp_tc = act2.mpls_tc
        exp_label = 0
        exp_ttl = 0 # Not expected

    else:
        return

    match_exp = False
    exp_msg = ofp.OFPT_ERROR
    exp_msg_type = ofp.OFPET_BAD_ACTION
    exp_msg_code = ofp.OFPBAC_BAD_ARGUMENT

    action_list=[act, act2]

    testutils.flow_match_test_mpls(parent, pa_port_map,
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
