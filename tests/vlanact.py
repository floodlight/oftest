"""
Test cases for vlan action features

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
                   ofp.OFPFW_NW_TOS]

MODIFY_ACTION_VALUES =  [ofp.OFPAT_SET_VLAN_VID,
                         ofp.OFPAT_SET_VLAN_PCP,
                         ofp.OFPAT_SET_DL_SRC,
                         ofp.OFPAT_SET_DL_DST,
                         ofp.OFPAT_SET_NW_SRC,
                         ofp.OFPAT_SET_NW_DST,
                         ofp.OFPAT_SET_NW_TOS,
                         ofp.OFPAT_SET_TP_SRC,
                         ofp.OFPAT_SET_TP_DST,
                         ofp.OFPAT_PUSH_VLAN,
                         ofp.OFPAT_POP_VLAN]

ETHERTYPE_VLAN = 0x8100
ETHERTYPE_VLAN_QinQ = 0x88a8

# Cache supported features to avoid transaction overhead
cached_supported_actions = None

TEST_VID_DEFAULT = 2

def test_set_init(config):
    """
    Set up function for packet action test classes

    @param config The configuration dictionary; see oft
    """

    global pa_port_map
    global pa_logger
    global pa_config

    pa_logger = logging.getLogger("vlan_act")
    pa_logger.info("Initializing test set")
    pa_port_map = config["port_map"]
    pa_config = config

###########################################################################

class VlanActNonTagPop(pktact.BaseMatchCase):
    """
    VLAN pop action test with untagged pkt
    Expectation: OFPET_BAD_ACTION (INCONSISTENT) error
    Test on one pair of ports
    """
    def __init__(self):
        pktact.BaseMatchCase.__init__(self)
        self.num_tags = 0
        self.vid = -1
        self.pcp = 0
        self.vlan_type = ETHERTYPE_VLAN
        self.vid_2nd = -1
        self.pcp_2nd = 0
        self.vid_match = ofp.OFPVID_NONE
        self.pcp_match = 0

    def runTest(self):
        vlan_pop_act_tests(self)

class VlanActNonTagPush0(VlanActNonTagPop):
    """
    VLAN push action (type VLAN) test with untagged pkt
    Expectation: Pkt with VLAN (VID=0 PCP=0)
    Test on one pair of ports
    """
    def runTest(self):
        vlan_singlepush_act_tests(self, test_condition=0)

class VlanActNonTagPush1(VlanActNonTagPop):
    """
    VLAN push action (type QinQ) test with untagged pkt
    Expectation: Pkt with VLAN (VID=0 PCP=0)
    Test on one pair of ports
    """
    def runTest(self):
        vlan_singlepush_act_tests(self, test_condition=1)

class VlanActNonTagPush2(VlanActNonTagPop):
    """
    VLAN push action (type other) test with untagged pkt
    Expectation: OFPET_BAD_ACTION (BAD ARG) error
    Test on one pair of ports
    """
    def runTest(self):
        vlan_singlepush_act_tests(self, test_condition=2)

class VlanActNonTagPushSetVid(VlanActNonTagPop):
    """
    VLAN Push and Set VID action test with untagged pkt
    Expectation: Pkt with VLAN (VID=Set value PCP=0)
    Test on one pair of ports
    """
    def runTest(self):
        vlan_multipush_act_tests(self, test_condition=0)

class VlanActNonTagPushSetPcp(VlanActNonTagPop):
    """
    VLAN Push and Set PCP action test with untagged pkt
    Expectation: Pkt with VLAN (VID=0 PCP=Set value)
    Test on one pair of ports
    """
    def runTest(self):
        vlan_multipush_act_tests(self, test_condition=1)

class VlanActNonTagPushSetVidPcp(VlanActNonTagPop):
    """
    VLAN Push, Set VID and Set PCP action test with untagged pkt
    Expectation: Pkt with VLAN (VID=Set value PCP=Set value)
    Test on one pair of ports
    """
    def runTest(self):
        vlan_multipush_act_tests(self, test_condition=2)

class VlanActNonTagPushPop(VlanActNonTagPop):
    """
    VLAN Push and Pop action test with untagged pkt
    Expectation: Same pkt
    Test on one pair of ports
    """
    def runTest(self):
        vlan_multipush_act_tests(self, test_condition=3)

class VlanActNonTagSetVid0(VlanActNonTagPop):
    """
    VLAN set VID action test with untagged pkt
    Expectation: OFPET_BAD_ACTION (INCONSISTENT) error
    Test on one pair of ports
    """
    def runTest(self):
        vlan_set_act_tests(self, test_condition=0)

class VlanActNonTagSetVid1(VlanActNonTagPop):
    """
    VLAN set VID action (outrange value) test with untagged pkt
    Expectation: OFPET_BAD_ACTION (BAD ARG) error
    Test on one pair of ports
    """
    def runTest(self):
        vlan_set_act_tests(self, test_condition=1)

class VlanActNonTagSetPcp0(VlanActNonTagPop):
    """
    VLAN set PCP action test with untagged pkt
    Expectation: OFPET_BAD_ACTION (INCONSISTENT) error
    Test on one pair of ports
    """
    def runTest(self):
        vlan_set_act_tests(self, test_condition=2)

class VlanActNonTagSetPcp1(VlanActNonTagPop):
    """
    VLAN set PCP action (outrane value) test with untagged pkt
    Expectation: OFPET_BAD_ACTION (BAD ARG) error
    Test on one pair of ports
    """
    def runTest(self):
        vlan_set_act_tests(self, test_condition=3)

class VlanActOneTagPop(VlanActNonTagPop):
    """
    VLAN pop action test with tagged pkt
    Expectation: Pkt w/o VLAN
    Test on one pair of ports
    """
    def __init__(self):
        VlanActNonTagPop.__init__(self)
        self.num_tags = 1
        self.vid = random.randint(0,4093)
        self.pcp = random.randint(0,5)
        self.vid_match = self.vid
        self.pcp_match = self.pcp

    def runTest(self):
        vlan_pop_act_tests(self)

class VlanActOneTagPush0(VlanActOneTagPop):
    """
    VLAN push action (type VLAN) test with tagged pkt
    Expectation: Pkt with two VLANs
     - Outer and Inner VLAN should have the same values
    Test on one pair of ports
    """
    def runTest(self):
        vlan_singlepush_act_tests(self, test_condition=0)

class VlanActOneTagPush1(VlanActOneTagPop):
    """
    VLAN push action (type QinQ) test with tagged pkt
    Expectation: Pkt with two VLANs
     - Outer and Inner VLAN should have the same values
    Test on one pair of ports
    """
    def runTest(self):
        vlan_singlepush_act_tests(self, test_condition=1)

class VlanActOneTagPush2(VlanActOneTagPop):
    """
    VLAN push action (type other) test with tagged pkt
    Expectation: OFPET_BAD_ACTION (BAD ARG) error
    Test on one pair of ports
    """
    def runTest(self):
        vlan_singlepush_act_tests(self, test_condition=2)

class VlanActOneTagPushSetVid(VlanActOneTagPop):
    """
    VLAN Push and Set VID action test with tagged pkt
    Expectation: Pkt with two VLANs
     - Outer VLAN VID=Set value
    Test on one pair of ports
    """
    def runTest(self):
        vlan_multipush_act_tests(self, test_condition=0)

class VlanActOneTagPushSetPcp(VlanActOneTagPop):
    """
    VLAN Push and Set PCP action test with tagged pkt
    Expectation: Pkt with two VLANs
     - Outer VLAN PCP=Set value
    Test on one pair of ports
    """
    def runTest(self):
        vlan_multipush_act_tests(self, test_condition=1)

class VlanActOneTagPushSetVidPcp(VlanActOneTagPop):
    """
    VLAN Push, Set VID and Set PCP action test with tagged pkt
    Expectation: Pkt with two VLANs
     - Outer VLAN VID=Set value PCP=Set value
    Test on one pair of ports
    """
    def runTest(self):
        vlan_multipush_act_tests(self, test_condition=2)

class VlanActOneTagPushSPop(VlanActOneTagPop):
    """
    VLAN multiple action test with tagged pkt
    Expectation: Same Pkt
    Test on one pair of ports
    """
    def runTest(self):
        vlan_multipush_act_tests(self, test_condition=3)

class VlanActOneTagSetVid0(VlanActOneTagPop):
    """
    VLAN set VID action test with tagged pkt
    Expectation: VID=Set value
    Test on one pair of ports
    """
    def runTest(self):
        vlan_set_act_tests(self, test_condition=0)

class VlanActOneTagSetVid1(VlanActOneTagPop):
    """
    VLAN set VID action (outrange value) test with tagged pkt
    Expectation: OFPET_BAD_ACTION (BAD ARG) error
    Test on one pair of ports
    """
    def runTest(self):
        vlan_set_act_tests(self, test_condition=1)

class VlanActOneTagSetPcp0(VlanActOneTagPop):
    """
    VLAN set action test with tagged pkt
    Expectation: PCP=Set value
    Test on one pair of ports
    """
    def runTest(self):
        vlan_set_act_tests(self, test_condition=2)

class VlanActOneTagSetPcp1(VlanActOneTagPop):
    """
    VLAN set action test with tagged pkt
    Expectation: OFPET_BAD_ACTION (BAD ARG) error
    Test on one pair of ports
    """
    def runTest(self):
        vlan_set_act_tests(self, test_condition=3)

class VlanActTwoTagPop(VlanActNonTagPop):
    """
    VLAN pop action test with two-tagged pkt
    Expectation: Outer VLAN tag to be removed
    Test on one pair of ports
    """
    def __init__(self):
        VlanActNonTagPop.__init__(self)
        self.num_tags = 2
        self.vid = random.randint(0,4093)
        self.pcp = random.randint(0,5)
        self.vlan_type = ETHERTYPE_VLAN_QinQ
        self.vid_2nd = self.vid + 1
        self.pcp_2nd = self.pcp + 1
        self.vid_match = self.vid
        self.pcp_match = self.pcp

    def runTest(self):
        vlan_pop_act_tests(self)

class VlanActTwoTagPush0(VlanActTwoTagPop):
    """
    VLAN push action (type VLAN) test with two-tagged pkt
    Expectation: Pkt with three VLANs
     - Outer most and second VLAN should have the same values
    Test on one pair of ports
    """
    def runTest(self):
        vlan_singlepush_act_tests(self, test_condition=0)

class VlanActTwoTagPush1(VlanActTwoTagPop):
    """
    VLAN push action (type QinQ) test with two-tagged pkt
    Expectation: Pkt with three VLANs
     - Outer most and second VLAN should have the same values
    Test on one pair of ports
    """
    def runTest(self):
        vlan_singlepush_act_tests(self, test_condition=1)

class VlanActTwoTagPush2(VlanActTwoTagPop):
    """
    VLAN push action (type other) test with two-tagged pkt
    Expectation: OFPET_BAD_ACTION (BAD ARG) error
    Test on one pair of ports
    """
    def runTest(self):
        vlan_singlepush_act_tests(self, test_condition=2)

class VlanActTwoTagPushSetVid(VlanActTwoTagPop):
    """
    VLAN Push and Set VID action test with two-tagged pkt
    Expectation: Pkt with three VLANs
     - Outer most VLAN VID=Set Value
    Test on one pair of ports
    """
    def runTest(self):
        vlan_multipush_act_tests(self, test_condition=0)

class VlanActTwoTagPushSetPcp(VlanActTwoTagPop):
    """
    VLAN Push and Set PCP action test with two-tagged pkt
    Expectation: Pkt with three VLANs
     - Outer most VLAN PCP=Set Value
    Test on one pair of ports
    """
    def runTest(self):
        vlan_multipush_act_tests(self, test_condition=1)

class VlanActTwoTagPushSetVidPcp(VlanActTwoTagPop):
    """
    VLAN Push, Set VID and Set PCP action test with two-tagged pkt
    Expectation: Pkt with three VLANs
     - Outer most VLAN VID=Set Value PCP=Set Value
    Test on one pair of ports
    """
    def runTest(self):
        vlan_multipush_act_tests(self, test_condition=2)

class VlanActTwoTagPushPop(VlanActTwoTagPop):
    """
    VLAN Push and Pop action test with two-tagged pkt
    Expectation: Same pkt
    Test on one pair of ports
    """
    def runTest(self):
        vlan_multipush_act_tests(self, test_condition=3)

class VlanActTwoTagSetVid0(VlanActTwoTagPop):
    """
    VLAN set VID action test with two-tagged pkt
    Expectation: VID=Set value
    Test on one pair of ports
    """
    def runTest(self):
        vlan_set_act_tests(self, test_condition=0)

class VlanActTwoTagSetVid1(VlanActTwoTagPop):
    """
    VLAN set VID action (outrange value) test with two-tagged pkt
    Expectation: OFPET_BAD_ACTION (BAD ARG) error
    Test on one pair of ports
    """
    def runTest(self):
        vlan_set_act_tests(self, test_condition=1)

class VlanActTwoTagSetPcp0(VlanActTwoTagPop):
    """
    VLAN set PCP action test with two-tagged pkt
    Expectation: PCP=Set value
    Test on one pair of ports
    """
    def runTest(self):
        vlan_set_act_tests(self, test_condition=2)

class VlanActTwoTagSetPcp1(VlanActTwoTagPop):
    """
    VLAN set PCP action (outrange value) test with two-tagged pkt
    Expectation: OFPET_BAD_ACTION (BAD ARG) error
    Test on one pair of ports
    """
    def runTest(self):
        vlan_set_act_tests(self, test_condition=3)


def vlan_action_support_check(parent):
    """
    Check if the target switch supports particular actions
    """

    sup_acts = pktact.supported_actions_get(parent)
    if not(sup_acts & 1<<ofp.OFPAT_POP_VLAN):
        sup_pop_vlan = False
    else:
        sup_pop_vlan = True
    if not(sup_acts & 1<<ofp.OFPAT_PUSH_VLAN):
        sup_push_vlan = False
    else:
        sup_push_vlan = True
    if not(sup_acts & 1<<ofp.OFPAT_SET_VLAN_VID):
        sup_set_vlan_vid = False
    else:
        sup_set_vlan_vid = True
    if not(sup_acts & 1<<ofp.OFPAT_SET_VLAN_PCP):
        sup_set_vlan_pcp = False
    else:
        sup_set_vlan_pcp = True

    return (sup_pop_vlan, sup_push_vlan, sup_set_vlan_vid, sup_set_vlan_pcp)

def vlan_pop_act_tests(parent):
    """
    Test vlan pop action for the packets with/without tags

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    parent.assertTrue(((parent.num_tags>=0) and (parent.num_tags<=2)),
        "Parameter num_tags not within an acceptable range")

    (sup_pop_vlan, sup_push_vlan, sup_set_vlan_vid, sup_set_vlan_pcp) = \
        vlan_action_support_check(parent)

    if sup_pop_vlan == False:
        testutils.skip_message_emit(parent, "Vlan pop action test. POP not supported")
        return

    act = action.action_pop_vlan()
    exp_vlan_type = ETHERTYPE_VLAN

    if parent.num_tags == 0:
        match_exp = False
        exp_vid = parent.vid
        exp_pcp = parent.pcp

        exp_msg = ofp.OFPT_ERROR
        exp_msg_type = ofp.OFPET_BAD_ACTION
        exp_msg_code = ofp.OFPBAC_MATCH_INCONSISTENT

    elif parent.num_tags == 1:
        match_exp = True
        exp_vid = -1
        exp_pcp = 0

        exp_msg = ofp.OFPT_FLOW_REMOVED
        exp_msg_type = 0 #NOT_EXPECTED
        exp_msg_code = 0 #NOT_EXPECTED

    else:
        match_exp = True
        exp_vid = -1
        exp_pcp = 0

        exp_msg = ofp.OFPT_FLOW_REMOVED
        exp_msg_type = 0 #NOT_EXPECTED
        exp_msg_code = 0 #NOT_EXPECTED

    action_list=[act]

    testutils.flow_match_test_vlan(parent, pa_port_map,
                    wildcards=0,
                    dl_vlan=parent.vid,
                    dl_vlan_pcp=parent.pcp,
                    dl_vlan_type=parent.vlan_type,
                    dl_vlan_int=parent.vid_2nd,
                    dl_vlan_pcp_int=parent.pcp_2nd,
                    vid_match=parent.vid_match,
                    pcp_match=parent.pcp_match,
                    exp_vid=exp_vid,
                    exp_pcp=exp_pcp,
                    exp_vlan_type=exp_vlan_type,
                    match_exp=match_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    action_list=action_list,
                    max_test=1)

def vlan_set_act_tests(parent, test_condition=0):
    """
    Test vlan set_vid and set_pcp action for the packets with/without tags

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param test_condition Value between 0 and 3
    """
    parent.assertTrue(((parent.num_tags>=0) and (parent.num_tags<=2)),
        "Parameter num_tags not within an acceptable range")

    (sup_pop_vlan, sup_push_vlan, sup_set_vlan_vid, sup_set_vlan_pcp) = \
        vlan_action_support_check(parent)

    new_vid = parent.vid + 2;
    new_pcp = parent.pcp + 2;

    if sup_set_vlan_vid == False:
        testutils.skip_message_emit(parent,
            "Vlan set action test. SET VLAN VID not supported")
        return
    if sup_set_vlan_pcp == False:
        testutils.skip_message_emit(parent,
            "Vlan set action test. SET VLAN PCP not supported")
        return

    exp_vlan_type = parent.vlan_type

    if test_condition == 0:
        act = action.action_set_vlan_vid()
        act.vlan_vid = new_vid
        if parent.num_tags == 0:
            match_exp = False
            exp_vid = -1
            exp_pcp = 0
            exp_msg = ofp.OFPT_ERROR
            exp_msg_type = ofp.OFPET_BAD_ACTION
            exp_msg_code = ofp.OFPBAC_MATCH_INCONSISTENT
        else:
            match_exp = True
            exp_vid = new_vid
            exp_pcp = parent.pcp
            exp_msg = ofp.OFPT_FLOW_REMOVED
            exp_msg_type = 0 #NOT_EXPECTED
            exp_msg_code = 0 #NOT_EXPECTED

    elif test_condition == 1:
        act = action.action_set_vlan_vid()
        act.vlan_vid = new_vid + 4096  #OUT OF RANGE
        match_exp = False
        exp_vid = -1
        exp_pcp = 0
        exp_msg = ofp.OFPT_ERROR
        exp_msg_type = ofp.OFPET_BAD_ACTION
        exp_msg_code = ofp.OFPBAC_BAD_ARGUMENT

    elif test_condition == 2:
        act = action.action_set_vlan_pcp()
        act.vlan_pcp = new_pcp
        if parent.num_tags == 0:
            match_exp = False
            exp_vid = -1
            exp_pcp = 0
            exp_msg = ofp.OFPT_ERROR
            exp_msg_type = ofp.OFPET_BAD_ACTION
            exp_msg_code = ofp.OFPBAC_MATCH_INCONSISTENT
        else:
            match_exp = True
            exp_vid = parent.vid
            exp_pcp = new_pcp
            exp_msg = ofp.OFPT_FLOW_REMOVED
            exp_msg_type = 0 #NOT_EXPECTED
            exp_msg_code = 0 #NOT_EXPECTED

    elif test_condition == 3:
        act = action.action_set_vlan_pcp()
        act.vlan_pcp = new_pcp + 8  #OUT OF RANGE
        match_exp = False
        exp_vid = -1
        exp_pcp = 0
        exp_msg = ofp.OFPT_ERROR
        exp_msg_type = ofp.OFPET_BAD_ACTION
        exp_msg_code = ofp.OFPBAC_BAD_ARGUMENT

    else:
        return

    action_list=[act]

    testutils.flow_match_test_vlan(parent, pa_port_map,
                    wildcards=0,
                    dl_vlan=parent.vid,
                    dl_vlan_pcp=parent.pcp,
                    dl_vlan_type=parent.vlan_type,
                    dl_vlan_int=parent.vid_2nd,
                    dl_vlan_pcp_int=parent.pcp_2nd,
                    vid_match=parent.vid_match,
                    pcp_match=parent.pcp_match,
                    exp_vid=exp_vid,
                    exp_pcp=exp_pcp,
                    exp_vlan_type=exp_vlan_type,
                    match_exp=match_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    action_list=action_list,
                    max_test=1)

def vlan_singlepush_act_tests(parent, test_condition=0):
    """
    Test vlan push action for the packets with/without tags

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param test_condition Value between 0 and 2
    """
    parent.assertTrue(((parent.num_tags>=0) and (parent.num_tags<=2)),
        "Parameter num_tags not within an acceptable range")

    (sup_pop_vlan, sup_push_vlan, sup_set_vlan_vid, sup_set_vlan_pcp) = \
        vlan_action_support_check(parent)

    if sup_push_vlan == False:
        testutils.skip_message_emit(parent,
            "Vlan single push action test. SET VLAN VID not supported")
        return

    if test_condition == 0:
        act = action.action_push_vlan()
        act.ethertype = ETHERTYPE_VLAN
        match_exp = True
        add_tag_exp = True
        if parent.num_tags == 0:
            exp_vid = 0
            exp_pcp = 0
        else:
            exp_vid = parent.vid
            exp_pcp = parent.pcp
        exp_msg = ofp.OFPT_FLOW_REMOVED
        exp_msg_type = 0 #NOT_EXPECTED
        exp_msg_code = 0 #NOT_EXPECTED

    elif test_condition == 1:
        act = action.action_push_vlan()
        act.ethertype = ETHERTYPE_VLAN_QinQ
        match_exp = True
        add_tag_exp = True
        if parent.num_tags == 0:
            exp_vid = 0
            exp_pcp = 0
        else:
            exp_vid = parent.vid
            exp_pcp = parent.pcp
        exp_msg = ofp.OFPT_FLOW_REMOVED
        exp_msg_type = 0 #NOT_EXPECTED
        exp_msg_code = 0 #NOT_EXPECTED

    elif test_condition == 2:
        act = action.action_push_vlan()
        act.ethertype = 0xaaa  #Other than 0x8100 and 0x88aa
        match_exp = False
        add_tag_exp = False
        exp_vid = 0
        exp_pcp = 0
        exp_msg = ofp.OFPT_ERROR
        exp_msg_type = ofp.OFPET_BAD_ACTION
        exp_msg_code = ofp.OFPBAC_BAD_ARGUMENT

    else:
        return

    action_list=[act]

    testutils.flow_match_test_vlan(parent, pa_port_map,
                    wildcards=0,
                    dl_vlan=parent.vid,
                    dl_vlan_pcp=parent.pcp,
                    dl_vlan_type=parent.vlan_type,
                    dl_vlan_int=parent.vid_2nd,
                    dl_vlan_pcp_int=parent.pcp_2nd,
                    vid_match=parent.vid_match,
                    pcp_match=parent.pcp_match,
                    exp_vid=exp_vid,
                    exp_pcp=exp_pcp,
                    exp_vlan_type=act.ethertype,
                    match_exp=match_exp,
                    add_tag_exp=add_tag_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    action_list=action_list,
                    max_test=1)

def vlan_multipush_act_tests(parent, test_condition=0):
    """
    Test vlan push action for the packets with/without tags

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param test_condition Value between 0 and 3
    """
    parent.assertTrue(((parent.num_tags>=0) and (parent.num_tags<=2)),
        "Parameter num_tags not within an acceptable range")

    (sup_pop_vlan, sup_push_vlan, sup_set_vlan_vid, sup_set_vlan_pcp) = \
        vlan_action_support_check(parent)

    if sup_push_vlan == False:
        testutils.skip_message_emit(parent,
            "Vlan multiple push action test. PUSH not supported")
        return
    if sup_pop_vlan == False:
        testutils.skip_message_emit(parent,
            "Vlan multiple push action test. POP not supported")
        return
    if sup_set_vlan_vid == False:
        testutils.skip_message_emit(parent,
            "Vlan multiple push action test. SET VLAN VID not supported")
        return
    if sup_set_vlan_pcp == False:
        testutils.skip_message_emit(parent,
            "Vlan multiple push action test. SET VLAN PCP not supported")
        return

    new_vid = parent.vid + 2;
    new_pcp = parent.pcp + 2;

    act = action.action_push_vlan()
    act.ethertype = ETHERTYPE_VLAN

    act3 = None
    if test_condition == 0:
        act2 = action.action_set_vlan_vid()
        act2.vlan_vid = new_vid
        add_tag_exp = True
        exp_vid = new_vid
        exp_vlan_type = act.ethertype
        if parent.num_tags == 0:
            exp_pcp = 0
        else:
            exp_pcp = parent.pcp

    elif test_condition == 1:
        act2 = action.action_set_vlan_pcp()
        act2.vlan_pcp = new_pcp
        add_tag_exp = True
        exp_pcp = new_pcp
        exp_vlan_type = act.ethertype
        if parent.num_tags == 0:
            exp_vid = 0
        else:
            exp_vid = parent.vid

    elif test_condition == 2:
        act2 = action.action_set_vlan_vid()
        act2.vlan_vid = new_vid
        act3 = action.action_set_vlan_pcp()
        act3.vlan_pcp = new_pcp
        add_tag_exp = True
        exp_vid = new_vid
        exp_pcp = new_pcp
        exp_vlan_type = act.ethertype

    elif test_condition == 3:
        act2 = action.action_pop_vlan()
        add_tag_exp = False
        exp_vid = parent.vid
        exp_pcp = parent.pcp
        exp_vlan_type = parent.vlan_type

    else:
        return

    match_exp = True
    exp_msg = ofp.OFPT_FLOW_REMOVED
    exp_msg_type = 0 #NOT_EXPECTED
    exp_msg_code = 0 #NOT_EXPECTED

    action_list=[act, act2]
    if act3 is not None:
        action_list.append(act3)

    testutils.flow_match_test_vlan(parent, pa_port_map,
                    wildcards=0,
                    dl_vlan=parent.vid,
                    dl_vlan_pcp=parent.pcp,
                    dl_vlan_type=parent.vlan_type,
                    dl_vlan_int=parent.vid_2nd,
                    dl_vlan_pcp_int=parent.pcp_2nd,
                    vid_match=parent.vid_match,
                    pcp_match=parent.pcp_match,
                    exp_vid=exp_vid,
                    exp_pcp=exp_pcp,
                    exp_vlan_type=exp_vlan_type,
                    match_exp=match_exp,
                    add_tag_exp=add_tag_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    action_list=action_list,
                    max_test=1)

if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test-spec=vlanact"
