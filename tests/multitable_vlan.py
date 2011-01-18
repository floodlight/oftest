"""
Test cases for vlan match with using multiple tables

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
import oftest.instruction as instruction
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
                         ofp.OFPAT_SET_TP_DST]

ETHERTYPE_VLAN = 0x8100

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

###########################################################################

class TwoTableVlanSetMatch(pktact.BaseMatchCase):
    """
    Multitable test: Set VID+PCP, apply it and expect it on outport
    Test Conditions:
     -Table0:
       Match: VLAN match, Actions: Set VID, Set PCP
     -Table1:
       Match: Modified VLAN, Action: outport
     -Expectation:
       Modified pkt to be received
    """
    def runTest(self):
        vlan_set_two_tables_tests(self, test_condition=0)

class TwoTableVlanSetUnmatch(pktact.BaseMatchCase):
    """
    Multitable test: Set VID+PCP, apply it but not expect it on outport
    Test Conditions:
     -Table0:
       Match: VLAN match, Actions: Set VID, Set PCP
     -Table1:
       Match: Same as in Table0, Action: output
     -Expectation:
       Pkt NOT to be received
    """
    def runTest(self):
        vlan_set_two_tables_tests(self, test_condition=1)

class TwoTable0VlanPushSetVidPcpMatch(pktact.BaseMatchCase):
    """
    Multitable test: Push, Set VID, PCP and apply it and expect it on outport
    Test Conditions:
     -Table0:
       Match: NO VLAN, Actions: Push, set VID, set PCP
     -Table1:
       Match: VLAN, Action: output
     -Expectation:
       Pkt to be received
    """
    def runTest(self):
        novlan_push_two_tables_tests(self)

class TwoTableVlanPushSetVidMatch0(pktact.BaseMatchCase):
    """
    Multitable test: Push, Set VID, apply it and expect it on outport
    Test Conditions:
     -Table0:
       Match: VLAN match, Actions: Push (Must be the same tag value)
     -Table1:
       Match: Same as in Table0, Action: output
     -Expectation:
       Pkt to be received
    """
    def runTest(self):
        vlan_push_two_tables_tests(self, test_condition=0, match_exp=True)

class TwoTableVlanPushSetVidUnmatch0(pktact.BaseMatchCase):
    """
    Multitable test: Push, Set VID, apply it but not expect it on outport
    Test Conditions:
     -Table0:
       Match: VLAN match, Actions: Push, Set VID
     -Table1:
       Match: Same as in Table0, Action: output
     -Expectation:
       Pkt NOT to be received
    """
    def runTest(self):
        vlan_push_two_tables_tests(self, test_condition=0, match_exp=False)

class TwoTableVlanPushSetVidMatch1(pktact.BaseMatchCase):
    """
    Multitable test: Push, Set VID, apply it and expect it on outport
    Test Conditions:
     -Table0:
       Match: VLAN match, Actions: Push, Set VID
     -Table1:
       Match: Modified VLAN (VID), Action: output
     -Expectation:
       Pkt to be received
    """
    def runTest(self):
        vlan_push_two_tables_tests(self, test_condition=1, match_exp=True)

class TwoTableVlanPushSetVidUnmatch1(pktact.BaseMatchCase):
    """
    Multitable test: Push, Set VID, apply it but not expect it on outport
    Test Conditions:
     -Table0:
       Match: VLAN match, Actions: Push
     -Table1:
       Match: Modified VLAN (VID), Action: output
     -Expectation:
       Pkt NOT to be received
    """
    def runTest(self):
        vlan_push_two_tables_tests(self, test_condition=1, match_exp=False)

class TwoTableVlanPushSetPcpMatch(pktact.BaseMatchCase):
    """
    Multitable test: Push, Set PCP, apply it and expect it on outport
    Test Conditions:
     -Table0:
       Match: VLAN match, Actions: Push, Set PCP
     -Table1:
       Match: Modified VLAN (PCP), Action: output
     -Expectation:
       Pkt to be received
    """
    def runTest(self):
        vlan_push_two_tables_tests(self, test_condition=2, match_exp=True)

class TwoTableVlanPushSetPcpUnmatch(pktact.BaseMatchCase):
    """
    Multitable test: Push, Set PCP, apply it but not expect it on outport
    Test Conditions:
     -Table0:
       Match: VLAN match, Actions: Push
     -Table1:
       Match: Modified VLAN (PCP), Action: output
     -Expectation:
       Pkt NOT to be received
    """
    def runTest(self):
        vlan_push_two_tables_tests(self, test_condition=2, match_exp=False)

class TwoTableVlanPushSetVidPcpMatch(pktact.BaseMatchCase):
    """
    Multitable test: Push, Set VID+PCP, apply it and expect it on outport
    Test Conditions:
     -Table0:
       Match: VLAN match, Actions: Push, Set VID, Set PCP
     -Table1:
       Match: Modified VLAN (VID, PCP), Action: output
     -Expectation:
       Pkt to be received
    """
    def runTest(self):
        vlan_push_two_tables_tests(self, test_condition=3, match_exp=True)

class TwoTableVlanPushSetVidPcpUnmatch(pktact.BaseMatchCase):
    """
    Multitable test: Push, Set VID+PCP, apply it but not expect it on outport
    Test Conditions:
     -Table0:
       Match: VLAN match, Actions: Push
     -Table1:
       Match: Modified VLAN (VID, PCP), Action: output
     -Expectation:
       Pkt NOT to be received
    """
    def runTest(self):
        vlan_push_two_tables_tests(self, test_condition=3, match_exp=False)

class TwoTable1VlanPopMatch(pktact.BaseMatchCase):
    """
    Multitable test: Pop, apply it and expect it on outport
    Test Conditions:
     -Table0:
       Match: VLAN match, Actions: Pop
     -Table1:
       Match: NO_VLAN, Action: output
     -Expectation:
       Pkt to be received
    """
    def runTest(self):
        vlan_pop_two_tables_tests(self, test_condition=0, match_exp=True)

class TwoTable1VlanPopUnmatch(pktact.BaseMatchCase):
    """
    Multitable test: Pop, apply it but not expect it on outport
    Test Conditions:
     -Table0:
       Match: VLAN match, Actions: Pop
     -Table1:
       Match: Same VLAN match, Action: output
     -Expectation:
       Pkt NOT to be received
    """
    def runTest(self):
        vlan_pop_two_tables_tests(self, test_condition=0, match_exp=False)

class TwoTable2VlanPopMatch(pktact.BaseMatchCase):
    """
    Multitable test: Pop, apply it and expect it on outport
    Test Conditions:
     -Table0:
       Match: Outer VLAN match, Actions: Pop
     -Table1:
       Match: Inner VLAN match, Action: output
     -Expectation:
       Pkt to be received
    """
    def runTest(self):
        vlan_pop_two_tables_tests(self, test_condition=1, match_exp=True)

class TwoTable2VlanPopUnmatch(pktact.BaseMatchCase):
    """
    Multitable test: Pop, apply it but not expect it on outport
    Test Conditions:
     -Table0:
       Match: Outer VLAN match, Actions: Pop
     -Table1:
       Match: Same VLAN match, Action: output
     -Expectation:
       Pkt NOT to be received
    """
    def runTest(self):
        vlan_pop_two_tables_tests(self, test_condition=1, match_exp=False)

###########################################################################

def vlan_set_two_tables_tests(parent, test_condition=0):
    """
    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    wildcards = 0
    vid = random.randint(0, 4094)
    pcp = random.randint(0, 6)
    vid_int = -1
    pcp_int = 0

    exp_vid = vid + 1
    exp_pcp = pcp + 1

    # Match condition on TBL0 (match)
    vid_match_tbl0 = vid
    pcp_match_tbl0 = pcp

    # Expect modified pkt on TBL1 (match)
    if (test_condition == 0):
        vid_match_tbl1 = exp_vid
        pcp_match_tbl1 = exp_pcp
        match_exp_tbl1 = True
    # Expect the same pkt on TBL1 (Unmatch)
    else: #test_condition == 1
        vid_match_tbl1 = vid
        pcp_match_tbl1 = pcp
        match_exp_tbl1 = False

    # Create action_list for TBL0
    act = action.action_set_vlan_vid()
    act.vlan_vid = exp_vid
    act2 = action.action_set_vlan_pcp()
    act2.vlan_pcp = exp_pcp
    action_list_tbl0 = [act, act2]

    # Create action_list for TBL1
    act = action.action_set_output()
    action_list_tbl1 = [act]

    flow_match_test_vlan_two_tables(parent, pa_port_map,
                    wildcards=wildcards,
                    dl_vlan=vid,
                    dl_vlan_pcp=pcp,
                    dl_vlan_int=vid_int,
                    dl_vlan_pcp_int=pcp_int,
                    vid_match_tbl0=vid_match_tbl0,
                    pcp_match_tbl0=pcp_match_tbl0,
                    action_list_tbl0 = action_list_tbl0,
                    match_exp_tbl0=True,
                    vid_match_tbl1=vid_match_tbl1,
                    pcp_match_tbl1=pcp_match_tbl1,
                    action_list_tbl1 = action_list_tbl1,
                    match_exp_tbl1=match_exp_tbl1,
                    exp_vid=exp_vid,
                    exp_pcp=exp_pcp,
                    max_test=1)

def novlan_push_two_tables_tests(parent):
    """
    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    wildcards = 0
    vid = -1
    pcp = 0
    vid_int = -1
    pcp_int = 0

    exp_vid = random.randint(0, 4094)
    exp_pcp = random.randint(0, 6)

    # Match condition on TBL0 (match)
    vid_match_tbl0 = ofp.OFPVID_NONE
    pcp_match_tbl0 = 0

    # Create action_list for TBL0
    action_list_tbl0 = []
    act = action.action_push_vlan()
    act.ethertype = ETHERTYPE_VLAN
    action_list_tbl0.append(act)

    act = action.action_set_vlan_vid()
    act.vlan_vid = exp_vid
    action_list_tbl0.append(act)
    act = action.action_set_vlan_pcp()
    act.vlan_pcp = exp_pcp
    action_list_tbl0.append(act)

    # Create action_list for TBL1
    vid_match_tbl1 = exp_vid
    pcp_match_tbl1 = exp_pcp

    act = action.action_set_output()
    action_list_tbl1 = [act]

    flow_match_test_vlan_two_tables(parent, pa_port_map,
                    dl_vlan=vid,
                    dl_vlan_pcp=pcp,
                    dl_vlan_int=vid_int,
                    dl_vlan_pcp_int=pcp_int,
                    vid_match_tbl0=vid_match_tbl0,
                    pcp_match_tbl0=pcp_match_tbl0,
                    action_list_tbl0 = action_list_tbl0,
                    match_exp_tbl0 = True,
                    vid_match_tbl1=vid_match_tbl1,
                    pcp_match_tbl1=pcp_match_tbl1,
                    action_list_tbl1 = action_list_tbl1,
                    match_exp_tbl1 = True,
                    exp_vid=exp_vid,
                    exp_pcp=exp_pcp,
                    add_tag_exp=True,
                    wildcards=wildcards,
                    max_test=1)

def vlan_push_two_tables_tests(parent, test_condition=0, match_exp = True):
    """
    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    wildcards = 0
    vid = random.randint(0, 4094)
    pcp = random.randint(0, 6)
    vid_int = -1
    pcp_int = 0

    if (test_condition == 0):
        exp_vid = vid
        exp_pcp = pcp
    elif (test_condition == 1):
        exp_vid = vid + 1
        exp_pcp = pcp
    elif (test_condition == 2):
        exp_vid = vid
        exp_pcp = pcp + 1
    else: # test_condition == 3
        exp_vid = vid + 1
        exp_pcp = pcp + 1

    # Match condition on TBL0 (match)
    vid_match_tbl0 = vid
    pcp_match_tbl0 = pcp

    # Create action_list for TBL0
    action_list_tbl0 = []
    act = action.action_push_vlan()
    act.ethertype = ETHERTYPE_VLAN
    action_list_tbl0.append(act)
    if (match_exp):
        # PUSH-only for test0
        if (test_condition == 1):
            act = action.action_set_vlan_vid()
            act.vlan_vid = exp_vid
            action_list_tbl0.append(act)
        elif (test_condition == 2):
            act = action.action_set_vlan_pcp()
            act.vlan_pcp = exp_pcp
            action_list_tbl0.append(act)
        elif (test_condition == 3):
            act = action.action_set_vlan_vid()
            act.vlan_vid = exp_vid
            action_list_tbl0.append(act)
            act = action.action_set_vlan_pcp()
            act.vlan_pcp = exp_pcp
            action_list_tbl0.append(act)
    else:
        if (test_condition == 0):
            act = action.action_set_vlan_vid()
            act.vlan_vid = vid + 1
            action_list_tbl0.append(act)

    # Create action_list for TBL1
    vid_match_tbl1 = exp_vid
    pcp_match_tbl1 = exp_pcp

    act = action.action_set_output()
    action_list_tbl1 = [act]

    flow_match_test_vlan_two_tables(parent, pa_port_map,
                    dl_vlan=vid,
                    dl_vlan_pcp=pcp,
                    dl_vlan_int=vid_int,
                    dl_vlan_pcp_int=pcp_int,
                    vid_match_tbl0=vid_match_tbl0,
                    pcp_match_tbl0=pcp_match_tbl0,
                    action_list_tbl0 = action_list_tbl0,
                    match_exp_tbl0 = True,
                    vid_match_tbl1=vid_match_tbl1,
                    pcp_match_tbl1=pcp_match_tbl1,
                    action_list_tbl1 = action_list_tbl1,
                    match_exp_tbl1 = match_exp,
                    exp_vid=exp_vid,
                    exp_pcp=exp_pcp,
                    add_tag_exp=True,
                    wildcards=wildcards,
                    max_test=1)

def vlan_pop_two_tables_tests(parent, test_condition=0, match_exp=True):
    """
    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    wildcards = 0
    vid = random.randint(0, 4094)
    pcp = random.randint(0, 6)

    if (test_condition == 0):
        vid_int = -1
        pcp_int = 0
    else: #test_condition == 1
        vid_int = vid + 1
        pcp_int = pcp + 1

    vid_match_tbl0 = vid
    pcp_match_tbl0 = pcp

    # Create matching value for TBL1
    if (match_exp):
        if (test_condition == 0):
            vid_match_tbl1 = ofp.OFPVID_NONE
            pcp_match_tbl1 = 0
        else: #test_condition == 1
            vid_match_tbl1 = vid_int
            pcp_match_tbl1 = pcp_int
    else:
        vid_match_tbl1 = vid
        pcp_match_tbl1 = pcp

    # Tag-removed packet expected
    exp_vid = -1
    exp_pcp = 0

    act = action.action_pop_vlan()
    action_list_tbl0 = [act]

    act = action.action_set_output()
    action_list_tbl1 = [act]

    flow_match_test_vlan_two_tables(parent, pa_port_map,
                    dl_vlan=vid,
                    dl_vlan_pcp=pcp,
                    dl_vlan_int=vid_int,
                    dl_vlan_pcp_int=pcp_int,
                    vid_match_tbl0=vid_match_tbl0,
                    pcp_match_tbl0=pcp_match_tbl0,
                    action_list_tbl0 = action_list_tbl0,
                    match_exp_tbl0=True,
                    vid_match_tbl1=vid_match_tbl1,
                    pcp_match_tbl1=pcp_match_tbl1,
                    action_list_tbl1 = action_list_tbl1,
                    match_exp_tbl1=match_exp,
                    exp_vid=exp_vid,
                    exp_pcp=exp_pcp,
                    wildcards=wildcards,
                    max_test=1)

###########################################################################

def flow_match_test_port_pair_vlan_two_tables(parent, ing_port, egr_port,
                                   wildcards=0, dl_vlan=-1, dl_vlan_pcp=0,
                                   dl_vlan_type=ETHERTYPE_VLAN,
                                   dl_vlan_int=-1, dl_vlan_pcp_int=0,
                                   vid_match_tbl0=ofp.OFPVID_NONE,
                                   pcp_match_tbl0=0,
                                   action_list_tbl0=None,
                                   check_expire_tbl0=False,
                                   match_exp_tbl0=True,
                                   exp_msg_tbl0=ofp.OFPT_FLOW_REMOVED,
                                   exp_msg_type_tbl0=0,
                                   exp_msg_code_tbl0=0,
                                   vid_match_tbl1=ofp.OFPVID_NONE,
                                   pcp_match_tbl1=0,
                                   action_list_tbl1=None,
                                   check_expire_tbl1=False,
                                   match_exp_tbl1=True,
                                   exp_msg_tbl1=ofp.OFPT_FLOW_REMOVED,
                                   exp_msg_type_tbl1=0,
                                   exp_msg_code_tbl1=0,
                                   exp_vid=-1, exp_pcp=0,
                                   exp_vlan_type=ETHERTYPE_VLAN,
                                   add_tag_exp=False,
                                   pkt=None, exp_pkt=None):
    """
    Flow match test for various vlan matching patterns on single TCP packet

    Run test with packet through switch from ing_port to egr_port
    See flow_match_test for parameter descriptions
    """
    parent.logger.info("Pkt match test: " + str(ing_port) + " to "
                       + str(egr_port))
    parent.logger.debug("  WC: " + hex(wildcards) + " vlan: " + str(dl_vlan) +
                    " expire_table0: " + str(check_expire_tbl0) +
                    " expire_table1: " + str(check_expire_tbl1))
    len = 100
    len_w_vid = len + 4

    if pkt is None:
        if dl_vlan >= 0:
            if dl_vlan_int >= 0:
                pkt = testutils.simple_tcp_packet(pktlen=len_w_vid,
                        dl_vlan_enable=True,
                        dl_vlan=dl_vlan_int,
                        dl_vlan_pcp=dl_vlan_pcp_int)
                pkt.push_vlan(dl_vlan_type)
                pkt.set_vlan_vid(dl_vlan)
                pkt.set_vlan_pcp(dl_vlan_pcp)
            else:
                pkt = testutils.simple_tcp_packet(pktlen=len_w_vid,
                        dl_vlan_enable=True,
                        dl_vlan_type=dl_vlan_type,
                        dl_vlan=dl_vlan,
                        dl_vlan_pcp=dl_vlan_pcp)
        else:
            pkt = testutils.simple_tcp_packet(pktlen=len,
                                    dl_vlan_enable=False)

    if exp_pkt is None:
        if exp_vid >= 0:
            if add_tag_exp:
                if dl_vlan >= 0:
                    if dl_vlan_int >= 0:
                        exp_pkt = testutils.simple_tcp_packet(pktlen=len_w_vid,
                                    dl_vlan_enable=True,
                                    dl_vlan=dl_vlan_int,
                                    dl_vlan_pcp=dl_vlan_pcp_int)
                        exp_pkt.push_vlan(dl_vlan_type)
                        exp_pkt.set_vlan_vid(dl_vlan)
                        exp_pkt.set_vlan_pcp(dl_vlan_pcp)
                    else:
                        exp_pkt = testutils.simple_tcp_packet(pktlen=len_w_vid,
                                    dl_vlan_enable=True,
                                    dl_vlan_type=dl_vlan_type,
                                    dl_vlan=dl_vlan,
                                    dl_vlan_pcp=dl_vlan_pcp)
                    #Push one more tag in either case
                    exp_pkt.push_vlan(exp_vlan_type)
                    exp_pkt.set_vlan_vid(exp_vid)
                    exp_pkt.set_vlan_pcp(exp_pcp)
                else:
                    exp_pkt = testutils.simple_tcp_packet(pktlen=len_w_vid,
                                dl_vlan_enable=True,
                                dl_vlan_type=exp_vlan_type,
                                dl_vlan=exp_vid,
                                dl_vlan_pcp=exp_pcp)
            else:
                if dl_vlan_int >= 0:
                    exp_pkt = testutils.simple_tcp_packet(pktlen=len_w_vid,
                                dl_vlan_enable=True,
                                dl_vlan=dl_vlan_int,
                                dl_vlan_pcp=dl_vlan_pcp_int)
                    exp_pkt.push_vlan(exp_vlan_type)
                    exp_pkt.set_vlan_vid(exp_vid)
                    exp_pkt.set_vlan_pcp(exp_pcp)

                else:
                    exp_pkt = testutils.simple_tcp_packet(pktlen=len_w_vid,
                                dl_vlan_enable=True,
                                dl_vlan_type=exp_vlan_type,
                                dl_vlan=exp_vid,
                                dl_vlan_pcp=exp_pcp)
        else:
            #subtract action
            if dl_vlan_int >= 0:
                exp_pkt = testutils.simple_tcp_packet(pktlen=len_w_vid,
                            dl_vlan_enable=True,
                            dl_vlan=dl_vlan_int,
                            dl_vlan_pcp=dl_vlan_pcp_int)
            else:
                exp_pkt = testutils.simple_tcp_packet(pktlen=len,
                            dl_vlan_enable=False)

    match = parse.packet_to_flow_match(pkt)
    parent.assertTrue(match is not None, "Flow match from pkt failed")
    match.wildcards = wildcards

    # Flow Mod for Table0
    match.dl_vlan = vid_match_tbl0
    match.dl_vlan_pcp = pcp_match_tbl0

    inst_1 = instruction.instruction_apply_actions()
    inst_2 = instruction.instruction_goto_table()
    inst_2.table_id = 1
    inst_list = [inst_1, inst_2]
    request0 = testutils.flow_msg_create(parent, pkt, ing_port=ing_port,
                              instruction_list=inst_list,
                              action_list=action_list_tbl0,
                              wildcards=wildcards,
                              match=match,
                              check_expire=check_expire_tbl0,
                              table_id=0)

    testutils.flow_msg_install(parent, request0)

    # Flow Mod for Table1
    match.dl_vlan = vid_match_tbl1
    match.dl_vlan_pcp = pcp_match_tbl1

    request1 = testutils.flow_msg_create(parent, pkt, ing_port=ing_port,
                              action_list=action_list_tbl1,
                              wildcards=wildcards,
                              match=match,
                              check_expire=check_expire_tbl1,
                              table_id=1,
                              egr_port=egr_port)

    testutils.flow_msg_install(parent, request1)

    parent.logger.debug("Send packet: " + str(ing_port) + " to " + str(egr_port))
    parent.dataplane.send(ing_port, str(pkt))

    if match_exp_tbl0:
        if check_expire_tbl0:
            #@todo Not all HW supports both pkt and byte counters
            #@todo We shouldn't expect the order of coming response..
            flow_removed_verify(parent, request0, pkt_count=1, byte_count=pktlen)
    else:
        if exp_msg_tbl0 is ofp.OFPT_FLOW_REMOVED:
            if check_expire_tbl0:
                flow_removed_verify(parent, request0, pkt_count=0, byte_count=0)
        elif exp_msg_tbl0 is ofp.OFPT_ERROR:
            error_verify(parent, exp_msg_type_tbl0, exp_msg_code_tbl0)
        else:
            parent.assertTrue(0, "Rcv: Unexpected Message: " + str(exp_msg_tbl0))

    if match_exp_tbl1:
        if check_expire_tbl1:
            #@todo Not all HW supports both pkt and byte counters
            #@todo We shouldn't expect the order of coming response..
            flow_removed_verify(parent, request1, pkt_count=1, byte_count=exp_pktlen)
    else:
        if exp_msg_tbl1 is ofp.OFPT_FLOW_REMOVED:
            if check_expire_tbl1:
                flow_removed_verify(parent, request1, pkt_count=0, byte_count=0)
        elif exp_msg_tbl1 is ofp.OFPT_ERROR:
            error_verify(parent, exp_msg_type_tbl1, exp_msg_code_tbl1)
        else:
            parent.assertTrue(0, "Rcv: Unexpected Message: " + str(exp_msg_tbl1))

    if match_exp_tbl0 and match_exp_tbl1:
        testutils.receive_pkt_verify(parent, egr_port, exp_pkt)
    else:
        (_, rcv_pkt, _) = parent.dataplane.poll(timeout=1)
        parent.assertFalse(rcv_pkt is not None, "Packet on dataplane")

def flow_match_test_vlan_two_tables(parent, port_map, wildcards=0,
                         dl_vlan=-1, dl_vlan_pcp=0,
                         dl_vlan_type=ETHERTYPE_VLAN,
                         dl_vlan_int=-1, dl_vlan_pcp_int=0,
                         vid_match_tbl0=ofp.OFPVID_NONE,
                         pcp_match_tbl0=0,
                         action_list_tbl0=None,
                         check_expire_tbl0=False,
                         match_exp_tbl0=True,
                         exp_msg_tbl0=ofp.OFPT_FLOW_REMOVED,
                         exp_msg_type_tbl0=0, exp_msg_code_tbl0=0,
                         vid_match_tbl1=ofp.OFPVID_NONE,
                         pcp_match_tbl1=0,
                         action_list_tbl1=None,
                         check_expire_tbl1=False,
                         match_exp_tbl1=True,
                         exp_msg_tbl1=ofp.OFPT_FLOW_REMOVED,
                         exp_msg_type_tbl1=0, exp_msg_code_tbl1=0,
                         exp_vid=-1, exp_pcp=0,
                         exp_vlan_type=ETHERTYPE_VLAN,
                         add_tag_exp=False,
                         pkt=None, exp_pkt=None,
                         max_test=0):
    """
    Run flow_match_test_port_pair on all port pairs

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param wildcards For flow match entry
    @param dl_vlan If not -1, and pkt is not None, create a pkt w/ VLAN tag
    @param dl_vlan_pcp VLAN PCP associated with dl_vlan
    @param dl_vlan_type VLAN ether type associated with dl_vlan
    @param dl_vlan_int If not -1, create pkt w/ Inner Vlan tag
    @param dl_vlan_pcp_int VLAN PCP associated with dl_vlan_2nd
    @param vid_match_tbl0 Matching value for VLAN VID field of Table0
    @param pcp_match_tbl0 Matching value for VLAN PCP field of Table0
    @param action_list_tbl0 Additional actions to add to flow mod of Table0
    @param check_expire_tbl0 Check for flow expiration message
    @param match_exp_tbl0 Set whether packet is expected to receive
    @param exp_msg_tbl0 Expected message
    @param exp_msg_type_tbl0 Expected message type associated with the message
    @param exp_msg_code_tbl0 Expected message code associated with the msg_type
    @param vid_match_tbl1 Matching value for VLAN VID field of Table1
    @param pcp_match_tbl1 Matching value for VLAN PCP field of Table1
    @param action_list_tbl1 Additional actions to add to flow mod of Table1
    @param check_expire_tbl1 Check for flow expiration message
    @param match_exp_tbl1 Set whether packet is expected to receive
    @param exp_msg_tbl1 Expected message
    @param exp_msg_type_tbl1 Expected message type associated with the message
    @param exp_msg_code_tbl1 Expected message code associated with the msg_type
    @param exp_vid Expected VLAN VID value. If -1, no VLAN expected
    @param exp_pcp Expected VLAN PCP value
    @param exp_vlan_type Expected VLAN ether type
    @param add_tag_exp If True, expected_packet has an additional vlan tag,
    If not, expected_packet's vlan tag is replaced as specified
    @param pkt If not None, use this packet for ingress
    @param exp_pkt If not None, use this as the expected output pkt
    @param max_test If > 0 no more than this number of tests are executed.
    """
    of_ports = port_map.keys()
    of_ports.sort()
    parent.assertTrue(len(of_ports) > 1, "Not enough ports for test")
    test_count = 0

    for ing_idx in range(len(of_ports)):
        ingress_port = of_ports[ing_idx]
        for egr_idx in range(len(of_ports)):
            if egr_idx == ing_idx:
                continue
            egress_port = of_ports[egr_idx]
            flow_match_test_port_pair_vlan_two_tables(parent, ingress_port, egress_port,
                                           wildcards=wildcards,
                                           dl_vlan=dl_vlan,
                                           dl_vlan_pcp=dl_vlan_pcp,
                                           dl_vlan_type=dl_vlan_type,
                                           dl_vlan_int=dl_vlan_int,
                                           dl_vlan_pcp_int=dl_vlan_pcp_int,
                                           vid_match_tbl0=vid_match_tbl0,
                                           pcp_match_tbl0=pcp_match_tbl0,
                                           action_list_tbl0=action_list_tbl0,
                                           check_expire_tbl0=check_expire_tbl0,
                                           match_exp_tbl0=match_exp_tbl0,
                                           exp_msg_tbl0=exp_msg_tbl0,
                                           exp_msg_type_tbl0=exp_msg_type_tbl0,
                                           exp_msg_code_tbl0=exp_msg_code_tbl0,
                                           vid_match_tbl1=vid_match_tbl1,
                                           pcp_match_tbl1=pcp_match_tbl1,
                                           action_list_tbl1=action_list_tbl1,
                                           check_expire_tbl1=check_expire_tbl1,
                                           match_exp_tbl1=match_exp_tbl1,
                                           exp_msg_tbl1=exp_msg_tbl1,
                                           exp_msg_type_tbl1=exp_msg_type_tbl1,
                                           exp_msg_code_tbl1=exp_msg_code_tbl1,
                                           exp_vid=exp_vid,
                                           exp_pcp=exp_pcp,
                                           exp_vlan_type=exp_vlan_type,
                                           add_tag_exp=add_tag_exp,
                                           pkt=pkt, exp_pkt=exp_pkt)
            test_count += 1
            if (max_test > 0) and (test_count >= max_test):
                parent.logger.info("Ran " + str(test_count) + " tests; exiting")
                return

if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test-spec=multivlan"
