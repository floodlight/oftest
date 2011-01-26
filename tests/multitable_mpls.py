"""
Test cases for mpls match with using multiple tables

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
import mplsact

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

ETHERTYPE_MPLS = 0x8847
ETYERTYPE_MPLS_MC = 0x8848
ETHERTYPE_IP = 0x0800

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

    pa_logger = logging.getLogger("multitable_mpls")
    pa_logger.info("Initializing test set")
    pa_port_map = config["port_map"]
    pa_config = config

###########################################################################

class TwoTableMplsSetMatch(pktact.BaseMatchCase):
    """
    Multitable test: Set LABEL+TC, apply it and expect it on outport
    Test Conditions:
     -Table0:
       Match: MPLS match, Actions: Set LABEL, Set TC
     -Table1:
       Match: Modified MPLS, Action: outport
     -Expectation:
       Modified pkt to be received
    """
    def runTest(self):
        mpls_set_two_tables_tests(self, match_exp=True)

class TwoTableMplsSetUnmatch(pktact.BaseMatchCase):
    """
    Multitable test: Set LABEL+TC, apply it but not expect it on outport
    Test Conditions:
     -Table0:
       Match: MPLS match, Actions: Set LABEL, Set TC
     -Table1:
       Match: Same as in Table0, Action: output
     -Expectation:
       Pkt NOT to be received
    """
    def runTest(self):
        mpls_set_two_tables_tests(self, match_exp=False)

class TwoTableMplsTtlInMatch(pktact.BaseMatchCase):
    """
    Multitable test: Copy TTL inwards, apply it and expect it on outport
    Test Conditions:
     -Table0:
       Match: MPLS match, Actions: Cp TTL-in
     -Table1:
       Match: Same MPLS, Action: outport
     -Expectation:
       Modified pkt to be received
    """
    def runTest(self):
        mpls_ttl_inout_two_tables_tests(self, test_inwards=True)

class TwoTableMplsTtlOutMatch(pktact.BaseMatchCase):
    """
    Multitable test: Copy TTL outwards, apply it and expect it on outport
    Test Conditions:
     -Table0:
       Match: MPLS match, Actions: Cp TTL-out
     -Table1:
       Match: Same MPLS, Action: output
     -Expectation:
       Modified pkt to be received
    """
    def runTest(self):
        mpls_ttl_inout_two_tables_tests(self, test_inwards=False)

class TwoTable0MplsPushSetLabelTcMatch(pktact.BaseMatchCase):
    """
    Multitable test: Push, Set LABEL, TC and apply it and expect it on outport
    Test Conditions:
     -Table0:
       Match: NO MPLS, Actions: Push, Set LABEL, TC
     -Table1:
       Match: MPLS, Action: output
     -Expectation:
       Modified pkt to be received (TTL to be copied)
    """
    def runTest(self):
        nompls_push_set_two_tables_tests(self)

class TwoTableMplsPushMatch(pktact.BaseMatchCase):
    """
    Multitable test: Push and apply it and expect it on outport
    Test Conditions:
     -Table0:
       Match: MPLS match, Actions: Push
     -Table1:
       Match: Same as in Table0, Action: output
     -Expectation:
       Pkt to be received
    """
    def runTest(self):
        mpls_push_two_tables_tests(self, match_exp=True)

class TwoTableMplsPushUnmatch(pktact.BaseMatchCase):
    """
    Multitable test: Push, Set LABEL, apply it but not expect it on outport
    Test Conditions:
     -Table0:
       Match: MPLS match, Actions: Push, Set LABEL
     -Table1:
       Match: Same as in Table0, Action: output
     -Expectation:
       Pkt NOT to be received
    """
    def runTest(self):
        mpls_push_two_tables_tests(self, match_exp=False)

class TwoTableMplsPushSetLabelMatch(pktact.BaseMatchCase):
    """
    Multitable test: Push, Set LABEL, apply it and expect it on outport
    Test Conditions:
     -Table0:
       Match: MPLS match, Actions: Push, Set LABEL
     -Table1:
       Match: Modified MPLS(LABEL), Action: output
     -Expectation:
       Pkt to be received
    """
    def runTest(self):
        mpls_push_set_two_tables_tests(self, test_condition=0, match_exp=True)

class TwoTableMplsPushSetLabelUnmatch(pktact.BaseMatchCase):
    """
    Multitable test: Push, Set LABEL, apply it but not expect it on outport
    Test Conditions:
     -Table0:
       Match: MPLS match, Actions: Push only
     -Table1:
       Match: Modified MPLS(LABEL), Action: output
     -Expectation:
       Pkt NOT to be received
    """
    def runTest(self):
        mpls_push_set_two_tables_tests(self, test_condition=0, match_exp=False)

class TwoTableMplsPushSetTcMatch(pktact.BaseMatchCase):
    """
    Multitable test: Push, Set TC, apply it and expect it on outport
    Test Conditions:
     -Table0:
       Match: MPLS match, Actions: Push, Set TC
     -Table1:
       Match: Modified MPLS(TC), Action: output
     -Expectation:
       Pkt to be received
    """
    def runTest(self):
        mpls_push_set_two_tables_tests(self, test_condition=1, match_exp=True)

class TwoTableMplsPushSetTcUnmatch(pktact.BaseMatchCase):
    """
    Multitable test: Push, Set TC, apply it but not expect it on outport
    Test Conditions:
     -Table0:
       Match: MPLS match, Actions: Push only
     -Table1:
       Match: Modified MPLS(TC), Action: output
     -Expectation:
       Pkt NOT to be received
    """
    def runTest(self):
        mpls_push_set_two_tables_tests(self, test_condition=1, match_exp=False)

class TwoTableMplsPushSetTtlMatch(pktact.BaseMatchCase):
    """
    Multitable test: Push, Set TTL, apply it and expect it on outport
    Test Conditions:
     -Table0:
       Match: MPLS match, Actions: Push, Set TTL
     -Table1:
       Match: Modified MPLS(TTL), Action: output
     -Expectation:
       Pkt to be received
    """
    def runTest(self):
        mpls_push_set_two_tables_tests(self, test_condition=2, match_exp=True)

class TwoTable1MplsPopMatch(pktact.BaseMatchCase):
    """
    Multitable test: Pop, apply it and expect it on outport
    Test Conditions:
     -Table0:
       Match: MPLS match, Actions: Pop
     -Table1:
       Match: NO_MPLS, Action: output
     -Expectation:
       Pkt to be received
    """
    def runTest(self):
        mpls_pop_two_tables_tests(self, test_condition=0, match_exp=True)

class TwoTable1MplsPopUnmatch(pktact.BaseMatchCase):
    """
    Multitable test: Pop, apply it but not expect it on outport
    Test Conditions:
     -Table0:
       Match: MPLS match, Actions: Pop
     -Table1:
       Match: Same MPLS, Action: output
     -Expectation:
       Pkt NOT to be received
    """
    def runTest(self):
        mpls_pop_two_tables_tests(self, test_condition=0, match_exp=False)

class TwoTable2MplsPopMatch(pktact.BaseMatchCase):
    """
    Multitable test: Pop, apply it and expect it on outport
    Test Conditions:
     -Table0:
       Match: Outer MPLS, Actions: Pop
     -Table1:
       Match: Inner MPLS, Action: output
     -Expectation:
       Pkt to be received
    """
    def runTest(self):
        mpls_pop_two_tables_tests(self, test_condition=1, match_exp=True)

class TwoTable2MplsPopUnmatch(pktact.BaseMatchCase):
    """
    Multitable test: Pop, apply it but not expect it on outport
    Test Conditions:
     -Table0:
       Match: Outer MPLS, Actions: Pop
     -Table1:
       Match: Same MPLS, Action: output
     -Expectation:
       Pkt NOT to be received
    """
    def runTest(self):
        mpls_pop_two_tables_tests(self, test_condition=1, match_exp=False)

###########################################################################

def mpls_set_two_tables_tests(parent, match_exp=True):
    """
    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    wildcards = 0
    label = random.randint(16, 1048574)
    tc = random.randint(0, 6)
    ttl = 64
    ip_ttl = 192

    # Match condition on TBL0 (match)
    label_match_tbl0 = label
    tc_match_tbl0 = tc
    dl_type_match_tbl0 = ETHERTYPE_MPLS

    # Set LABEL TC TTL
    exp_label = label + 1
    exp_tc = tc + 1
    exp_ttl = ttl + 2
    exp_ip_ttl = ip_ttl
    # Create action_list for TBL0
    act = action.action_set_mpls_label()
    act.mpls_label = exp_label
    act2 = action.action_set_mpls_tc()
    act2.mpls_tc = exp_tc
    act3 = action.action_set_mpls_ttl()
    act3.mpls_ttl = exp_ttl
    action_list_tbl0 = [act, act2, act3]

    # Expect modified pkt on TBL1 (match)
    if (match_exp) :
        label_match_tbl1 = exp_label
        tc_match_tbl1 = exp_tc
    # Expect the same pkt on TBL1 (Unmatch)
    else:
        label_match_tbl1 = label
        tc_match_tbl1 = tc
    dl_type_match_tbl1 = ETHERTYPE_MPLS

    # Output action for table1 will be set in the framework
    action_list_tbl1 = None

    flow_match_test_mpls_two_tables(parent, pa_port_map,
                    wildcards=wildcards,
                    mpls_label=label,
                    mpls_tc=tc,
                    mpls_ttl=ttl,
                    ip_ttl=ip_ttl,
                    label_match_tbl0=label_match_tbl0,
                    tc_match_tbl0=tc_match_tbl0,
                    dl_type_match_tbl0=dl_type_match_tbl0,
                    action_list_tbl0 = action_list_tbl0,
                    match_exp_tbl0=True,
                    label_match_tbl1=label_match_tbl1,
                    tc_match_tbl1=tc_match_tbl1,
                    dl_type_match_tbl1=dl_type_match_tbl1,
                    action_list_tbl1 = action_list_tbl1,
                    match_exp_tbl1=match_exp,
                    exp_mpls_label=exp_label,
                    exp_mpls_tc=exp_tc,
                    exp_mpls_ttl=exp_ttl,
                    exp_ip_ttl=exp_ip_ttl,
                    max_test=1)

def mpls_ttl_inout_two_tables_tests(parent, test_inwards=True):
    """
    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    wildcards = 0
    label = random.randint(16, 1048574)
    tc = random.randint(0, 6)
    ttl = 64
    ip_ttl = 192

    # Match condition on TBL0 (match)
    label_match_tbl0 = label
    tc_match_tbl0 = tc
    dl_type_match_tbl0 = ETHERTYPE_MPLS

    exp_label = label
    exp_tc = tc
    # Copy TTL inwards
    if (test_inwards):
        exp_ttl= ttl
        exp_ip_ttl=ttl
        # Create action_list for TBL0
        act = action.action_copy_ttl_in()
    # Copy TTL outwards
    else:
        exp_ttl= ip_ttl
        exp_ip_ttl=ip_ttl
        # Create action_list for TBL0
        act = action.action_copy_ttl_out()
    action_list_tbl0 = [act]

    # Expect modified pkt on TBL1 (match)
    label_match_tbl1 = exp_label
    tc_match_tbl1 = exp_tc
    dl_type_match_tbl1 = ETHERTYPE_MPLS

    # Output action for table1 will be set in the framework
    action_list_tbl1 = None

    flow_match_test_mpls_two_tables(parent, pa_port_map,
                    wildcards=wildcards,
                    mpls_label=label,
                    mpls_tc=tc,
                    mpls_ttl=ttl,
                    ip_ttl=ip_ttl,
                    label_match_tbl0=label_match_tbl0,
                    tc_match_tbl0=tc_match_tbl0,
                    dl_type_match_tbl0=dl_type_match_tbl0,
                    action_list_tbl0 = action_list_tbl0,
                    match_exp_tbl0=True,
                    label_match_tbl1=label_match_tbl1,
                    tc_match_tbl1=tc_match_tbl1,
                    dl_type_match_tbl1=dl_type_match_tbl1,
                    action_list_tbl1 = action_list_tbl1,
                    match_exp_tbl1=True,
                    exp_mpls_label=exp_label,
                    exp_mpls_tc=exp_tc,
                    exp_mpls_ttl=exp_ttl,
                    exp_ip_ttl=exp_ip_ttl,
                    max_test=1)

def nompls_push_set_two_tables_tests(parent):
    """
    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    wildcards = 0
    label = -1
    tc = 0
    ttl = 0
    ip_ttl = 192

    exp_label = random.randint(16, 1048574)
    exp_tc = random.randint(0, 6)
    exp_ttl = ip_ttl
    exp_ip_ttl = ip_ttl

    # Match condition on TBL0 (match)
    label_match_tbl0 = 0
    tc_match_tbl0 = 0
    dl_type_match_tbl0 = ETHERTYPE_IP

    # Create action_list for TBL0
    action_list_tbl0 = []
    act = action.action_push_mpls()
    act.ethertype = ETHERTYPE_MPLS
    action_list_tbl0.append(act)

    act = action.action_set_mpls_label()
    act.mpls_label = exp_label
    action_list_tbl0.append(act)
    act = action.action_set_mpls_tc()
    act.mpls_tc = exp_tc
    action_list_tbl0.append(act)

    # Match condition on TBL1 (match)
    label_match_tbl1 = exp_label
    tc_match_tbl1 = exp_tc
    dl_type_match_tbl1 = ETHERTYPE_MPLS

    # Output action for table1 will be set in the framework
    action_list_tbl1 = None

    flow_match_test_mpls_two_tables(parent, pa_port_map,
                    wildcards=wildcards,
                    mpls_label=label,
                    mpls_tc=tc,
                    mpls_ttl=ttl,
                    ip_ttl=ip_ttl,
                    label_match_tbl0=label_match_tbl0,
                    tc_match_tbl0=tc_match_tbl0,
                    dl_type_match_tbl0=dl_type_match_tbl0,
                    action_list_tbl0 = action_list_tbl0,
                    match_exp_tbl0 = True,
                    label_match_tbl1=label_match_tbl1,
                    tc_match_tbl1=tc_match_tbl1,
                    dl_type_match_tbl1=dl_type_match_tbl1,
                    action_list_tbl1 = action_list_tbl1,
                    match_exp_tbl1 = True,
                    exp_mpls_label=exp_label,
                    exp_mpls_tc=exp_tc,
                    exp_mpls_ttl=exp_ttl,
                    exp_ip_ttl=exp_ip_ttl,
                    add_tag_exp=False,
                    max_test=1)

def mpls_push_two_tables_tests(parent, match_exp = True):
    """
    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    wildcards = 0
    label = random.randint(16, 1048574)
    tc = random.randint(0, 6)
    ttl = 64

    # Match condition on TBL0 (match)
    label_match_tbl0 = label
    tc_match_tbl0 = tc
    dl_type_match_tbl0 = ETHERTYPE_MPLS

    # Match or Unmatch depends on match_exp parameter
    # Expect same tag
    exp_label = label
    exp_tc = tc
    exp_ttl = ttl

    # Create action_list for TBL0
    action_list_tbl0 = []
    act = action.action_push_mpls()
    act.ethertype = ETHERTYPE_MPLS
    action_list_tbl0.append(act)
    if (match_exp):
        pass
    else:
        act = action.action_set_mpls_label()
        act.mpls_label = label + 1
        action_list_tbl0.append(act)

    # Match condition on TBL1
    label_match_tbl1 = exp_label
    tc_match_tbl1 = exp_tc
    dl_type_match_tbl1 = ETHERTYPE_MPLS

    # Output action for table1 will be set in the framework
    action_list_tbl1 = None

    flow_match_test_mpls_two_tables(parent, pa_port_map,
                    wildcards=wildcards,
                    mpls_label=label,
                    mpls_tc=tc,
                    mpls_ttl=ttl,
                    label_match_tbl0=label_match_tbl0,
                    tc_match_tbl0=tc_match_tbl0,
                    dl_type_match_tbl0=dl_type_match_tbl0,
                    action_list_tbl0 = action_list_tbl0,
                    match_exp_tbl0 = True,
                    label_match_tbl1=label_match_tbl1,
                    tc_match_tbl1=tc_match_tbl1,
                    dl_type_match_tbl1=dl_type_match_tbl1,
                    action_list_tbl1 = action_list_tbl1,
                    match_exp_tbl1 = match_exp,
                    exp_mpls_label=exp_label,
                    exp_mpls_tc=exp_tc,
                    exp_mpls_ttl=exp_ttl,
                    add_tag_exp=True,
                    max_test=1)

def mpls_push_set_two_tables_tests(parent, test_condition=0, match_exp = True):
    """
    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    wildcards = 0
    label = random.randint(16, 1048574)
    tc = random.randint(0, 6)
    ttl = 64

    # Match condition on TBL0 (match)
    label_match_tbl0 = label
    tc_match_tbl0 = tc
    dl_type_match_tbl0 = ETHERTYPE_MPLS

    # Match or Unmatch depends on match_exp parameter
    # Expect different label
    if (test_condition == 0):
        exp_label = label + 1
        exp_tc = tc
        exp_ttl = ttl
    # Expect different TC
    elif (test_condition == 1):
        exp_label = label
        exp_tc = tc + 1
        exp_ttl = ttl
    # Expect different TTL
    else: # test_condition == 2
        exp_label = label
        exp_tc = tc
        exp_ttl = ttl + 2

    # Create action_list for TBL0
    action_list_tbl0 = []
    act = action.action_push_mpls()
    act.ethertype = ETHERTYPE_MPLS
    action_list_tbl0.append(act)
    if (match_exp):
        if (test_condition == 0):
            act = action.action_set_mpls_label()
            act.mpls_label = exp_label
            action_list_tbl0.append(act)
        elif (test_condition == 1):
            act = action.action_set_mpls_tc()
            act.mpls_tc = exp_tc
            action_list_tbl0.append(act)
        else: #test_condition == 2
            act = action.action_set_mpls_ttl()
            act.mpls_ttl = exp_ttl
            action_list_tbl0.append(act)

    # Match condition on TBL1
    label_match_tbl1 = exp_label
    tc_match_tbl1 = exp_tc
    dl_type_match_tbl1 = ETHERTYPE_MPLS

    # Output action for table1 will be set in the framework
    action_list_tbl1 = None

    flow_match_test_mpls_two_tables(parent, pa_port_map,
                    wildcards=wildcards,
                    mpls_label=label,
                    mpls_tc=tc,
                    mpls_ttl=ttl,
                    label_match_tbl0=label_match_tbl0,
                    tc_match_tbl0=tc_match_tbl0,
                    dl_type_match_tbl0=dl_type_match_tbl0,
                    action_list_tbl0 = action_list_tbl0,
                    match_exp_tbl0 = True,
                    label_match_tbl1=label_match_tbl1,
                    tc_match_tbl1=tc_match_tbl1,
                    dl_type_match_tbl1=dl_type_match_tbl1,
                    action_list_tbl1 = action_list_tbl1,
                    match_exp_tbl1 = match_exp,
                    exp_mpls_label=exp_label,
                    exp_mpls_tc=exp_tc,
                    exp_mpls_ttl=exp_ttl,
                    add_tag_exp=True,
                    max_test=1)

def mpls_pop_two_tables_tests(parent, test_condition=0, match_exp=True):
    """
    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    """
    wildcards = 0
    label = random.randint(16, 1048574)
    tc = random.randint(0, 6)
    ttl = 64
    ip_ttl = 192

    if (test_condition == 0):
        label_int = -1
        tc_int = 0
        ttl_int = 0
    else: #test_condition == 1
        label_int = label + 1
        tc_int = tc + 1
        ttl_int = ttl + 2

    # Match condition on TBL0
    label_match_tbl0 = label
    tc_match_tbl0 = tc
    dl_type_match_tbl0 = ETHERTYPE_MPLS

    # Create action_list for TBL0
    act = action.action_pop_mpls()
    if test_condition == 0:
        act.ethertype = ETHERTYPE_IP
    action_list_tbl0 = [act]

    # Create matching value for TBL1
    if (match_exp):
        if (test_condition == 0):
            label_match_tbl1 = 0
            tc_match_tbl1 = 0
            dl_type_match_tbl1 = ETHERTYPE_IP
        else: #test_condition == 1
            label_match_tbl1 = label_int
            tc_match_tbl1 = tc_int
            dl_type_match_tbl1 = ETHERTYPE_MPLS
    else:
        label_match_tbl1 = label
        tc_match_tbl1 = tc
        dl_type_match_tbl1 = ETHERTYPE_MPLS

    # Output action for table1 will be set in the framework
    action_list_tbl1 = None

    # One-tag-removed packet expected
    exp_label = -1
    exp_tc = 0
    exp_ttl = 0
    exp_ttl_int = ttl_int
    exp_ip_ttl = ip_ttl

    flow_match_test_mpls_two_tables(parent, pa_port_map,
                    wildcards=wildcards,
                    mpls_label=label,
                    mpls_tc=tc,
                    mpls_ttl=ttl,
                    ip_ttl=ip_ttl,
                    mpls_label_int=label_int,
                    mpls_tc_int=tc_int,
                    mpls_ttl_int=ttl_int,
                    label_match_tbl0=label_match_tbl0,
                    tc_match_tbl0=tc_match_tbl0,
                    dl_type_match_tbl0=dl_type_match_tbl0,
                    action_list_tbl0 = action_list_tbl0,
                    match_exp_tbl0=True,
                    label_match_tbl1=label_match_tbl1,
                    tc_match_tbl1=tc_match_tbl1,
                    dl_type_match_tbl1=dl_type_match_tbl1,
                    action_list_tbl1 = action_list_tbl1,
                    match_exp_tbl1=match_exp,
                    exp_mpls_label=exp_label,
                    exp_mpls_tc=exp_tc,
                    exp_mpls_ttl_int = exp_ttl_int,
                    exp_ip_ttl=exp_ip_ttl,
                    max_test=1)

###########################################################################

def flow_match_test_port_pair_mpls_two_tables(parent, ing_port, egr_port,
                                   wildcards=0,
                                   mpls_type=ETHERTYPE_MPLS,
                                   mpls_label=-1,
                                   mpls_tc=0,
                                   mpls_ttl=64,
                                   mpls_label_int=-1,
                                   mpls_tc_int=0,
                                   mpls_ttl_int=32,
                                   ip_ttl=192,
                                   label_match_tbl0=0,
                                   tc_match_tbl0=0,
                                   dl_type_match_tbl0=ETHERTYPE_MPLS,
                                   action_list_tbl0=None,
                                   check_expire_tbl0=False,
                                   match_exp_tbl0=True,
                                   exp_msg_tbl0=ofp.OFPT_FLOW_REMOVED,
                                   exp_msg_type_tbl0=0,
                                   exp_msg_code_tbl0=0,
                                   label_match_tbl1=0,
                                   tc_match_tbl1=0,
                                   dl_type_match_tbl1=ETHERTYPE_MPLS,
                                   action_list_tbl1=None,
                                   check_expire_tbl1=False,
                                   match_exp_tbl1=True,
                                   exp_msg_tbl1=ofp.OFPT_FLOW_REMOVED,
                                   exp_msg_type_tbl1=0,
                                   exp_msg_code_tbl1=0,
                                   add_tag_exp=False,
                                   exp_mpls_type=ETHERTYPE_MPLS,
                                   exp_mpls_label=-1,
                                   exp_mpls_tc=0,
                                   exp_mpls_ttl=64,
                                   exp_mpls_ttl_int=32,
                                   exp_ip_ttl=192,
                                   pkt=None, exp_pkt=None):
    """
    Flow match test for various mpls matching patterns on single TCP packet

    Run test with packet through switch from ing_port to egr_port
    See flow_match_test for parameter descriptions
    """
    parent.logger.info("Pkt match test: " + str(ing_port) + " to "
                       + str(egr_port))
    parent.logger.debug("  WC: " + hex(wildcards) + " mpls label: " +
                    str(mpls_label) +
                    " mpls tc: " + str(mpls_tc) +
                    " expire_table0: " + str(check_expire_tbl0) +
                    " expire_table1: " + str(check_expire_tbl1))

    # Check if the switch supports all the MPLS actions
    sup_act_dic = mplsact.mpls_action_support_check(parent)
    sup_act_elm = sup_act_dic.keys()
    for i in sup_act_elm:
        if sup_act_dic[i] == False:
            testutils.skip_message_emit(parent, "Switch doesn't support " +
                "one or more of MPLS actions : " + i)
            return

    len = 100
    len_w_shim = len + 4
    len_w_2shim = len_w_shim + 4
    len_w_3shim = len_w_2shim + 4
    if pkt is None:
        if mpls_label >= 0:
            if mpls_label_int >= 0:
                pktlen=len_w_2shim
            else:
                pktlen=len_w_shim
        else:
            pktlen=len
        pkt = testutils.simple_tcp_packet_w_mpls(pktlen=pktlen,
                                       mpls_type=mpls_type,
                                       mpls_label=mpls_label,
                                       mpls_tc=mpls_tc,
                                       mpls_ttl=mpls_ttl,
                                       mpls_label_int=mpls_label_int,
                                       mpls_tc_int=mpls_tc_int,
                                       mpls_ttl_int=mpls_ttl_int,
                                       ip_ttl=ip_ttl)

    if exp_pkt is None:
        if exp_mpls_label >= 0:
            if add_tag_exp:
                if mpls_label_int >= 0:
                    exp_pktlen=len_w_3shim
                else:
                    exp_pktlen=len_w_2shim
            else:
                if mpls_label_int >= 0:
                    exp_pktlen=len_w_2shim
                else:
                    exp_pktlen=len_w_shim
        else:
            #subtract action
            if mpls_label_int >= 0:
                exp_pktlen=len_w_shim
            else:
                exp_pktlen=len

        if add_tag_exp:
            exp_pkt = testutils.simple_tcp_packet_w_mpls(pktlen=exp_pktlen,
                                           mpls_type=exp_mpls_type,
                                           mpls_label_ext=exp_mpls_label,
                                           mpls_tc_ext=exp_mpls_tc,
                                           mpls_ttl_ext=exp_mpls_ttl,
                                           mpls_label=mpls_label,
                                           mpls_tc=mpls_tc,
                                           mpls_ttl=mpls_ttl,
                                           mpls_label_int=mpls_label_int,
                                           mpls_tc_int=mpls_tc_int,
                                           mpls_ttl_int=exp_mpls_ttl_int,
                                           ip_ttl=exp_ip_ttl)
        else:
            if (exp_mpls_label < 0) and (mpls_label_int >= 0):
                exp_pkt = testutils.simple_tcp_packet_w_mpls(pktlen=exp_pktlen,
                                           mpls_type=mpls_type,
                                           mpls_label=mpls_label_int,
                                           mpls_tc=mpls_tc_int,
                                           mpls_ttl=exp_mpls_ttl_int,
                                           ip_ttl=exp_ip_ttl)
            else:
                exp_pkt = testutils.simple_tcp_packet_w_mpls(pktlen=exp_pktlen,
                                           mpls_type=exp_mpls_type,
                                           mpls_label=exp_mpls_label,
                                           mpls_tc=exp_mpls_tc,
                                           mpls_ttl=exp_mpls_ttl,
                                           mpls_label_int=mpls_label_int,
                                           mpls_tc_int=mpls_tc_int,
                                           mpls_ttl_int=exp_mpls_ttl_int,
                                           ip_ttl=exp_ip_ttl)

    match = parse.packet_to_flow_match(pkt)
    parent.assertTrue(match is not None, "Flow match from pkt failed")

    # Flow Mod for Table0
    match.mpls_label = label_match_tbl0
    match.mpls_tc = tc_match_tbl0
    match.dl_type = dl_type_match_tbl0
    match.nw_tos = 0
    match.nw_proto = 0
    match.nw_src = 0
    match.nw_src_mask = 0
    match.nw_dst = 0
    match.nw_dst_mask = 0
    match.tp_src = 0
    match.tp_dst = 0

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
    # Other match parameters are the same
    match.mpls_label = label_match_tbl1
    match.mpls_tc = tc_match_tbl1
    match.dl_type = dl_type_match_tbl1

    request1 = testutils.flow_msg_create(parent, pkt, ing_port=ing_port,
                              action_list=action_list_tbl1,
                              wildcards=wildcards,
                              match=match,
                              check_expire=check_expire_tbl1,
                              table_id=1,
                              egr_port=egr_port)
    testutils.flow_msg_install(parent, request1)

    parent.logger.debug("Send packet: " + str(ing_port)
        + " to " + str(egr_port))
    parent.dataplane.send(ing_port, str(pkt))

    # Check response from switch
    #@todo Not all HW supports both pkt and byte counters
    #@todo We shouldn't expect the order of coming response..
    if match_exp_tbl0:
        if check_expire_tbl0:
            flow_removed_verify(parent, request0, pkt_count=1,
                                byte_count=pktlen)
    else:
        if exp_msg_tbl0 is ofp.OFPT_FLOW_REMOVED:
            if check_expire_tbl0:
                flow_removed_verify(parent, request0, pkt_count=0,
                                    byte_count=0)
        elif exp_msg_tbl0 is ofp.OFPT_ERROR:
            error_verify(parent, exp_msg_type_tbl0, exp_msg_code_tbl0)
        else:
            parent.assertTrue(0, "Rcv: Unexpected Message: " +
                              str(exp_msg_tbl0))

    if match_exp_tbl1:
        if check_expire_tbl1:
            flow_removed_verify(parent, request1, pkt_count=1,
                                byte_count=exp_pktlen)
    else:
        if exp_msg_tbl1 is ofp.OFPT_FLOW_REMOVED:
            if check_expire_tbl1:
                flow_removed_verify(parent, request1, pkt_count=0,
                                    byte_count=0)
        elif exp_msg_tbl1 is ofp.OFPT_ERROR:
            error_verify(parent, exp_msg_type_tbl1, exp_msg_code_tbl1)
        else:
            parent.assertTrue(0, "Rcv: Unexpected Message: " +
                              str(exp_msg_tbl1))

    # Check pkt
    if match_exp_tbl0 and match_exp_tbl1:
        testutils.receive_pkt_verify(parent, egr_port, exp_pkt)
    else:
        (_, rcv_pkt, _) = parent.dataplane.poll(timeout=1)
        parent.assertFalse(rcv_pkt is not None, "Packet on dataplane")

def flow_match_test_mpls_two_tables(parent, port_map, wildcards=0,
                         mpls_type=ETHERTYPE_MPLS,
                         mpls_label=-1, mpls_tc=0, mpls_ttl=64,
                         mpls_label_int=-1, mpls_tc_int=0, mpls_ttl_int=32,
                         ip_ttl=192,
                         label_match_tbl0=0,
                         tc_match_tbl0=0,
                         dl_type_match_tbl0=ETHERTYPE_MPLS,
                         action_list_tbl0=None,
                         check_expire_tbl0=False,
                         match_exp_tbl0=True,
                         exp_msg_tbl0=ofp.OFPT_FLOW_REMOVED,
                         exp_msg_type_tbl0=0, exp_msg_code_tbl0=0,
                         label_match_tbl1=0,
                         tc_match_tbl1=0,
                         dl_type_match_tbl1=ETHERTYPE_MPLS,
                         action_list_tbl1=None,
                         check_expire_tbl1=False,
                         match_exp_tbl1=True,
                         exp_msg_tbl1=ofp.OFPT_FLOW_REMOVED,
                         exp_msg_type_tbl1=0, exp_msg_code_tbl1=0,
                         add_tag_exp=False,
                         exp_mpls_type=ETHERTYPE_MPLS,
                         exp_mpls_label=-1, exp_mpls_tc=0, exp_mpls_ttl=64,
                         exp_mpls_ttl_int=32,
                         exp_ip_ttl=192,
                         pkt=None, exp_pkt=None,
                         max_test=0):
    """
    Run flow_match_test_port_pair on all port pairs
    @param max_test If > 0 no more than this number of tests are executed.
    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param wildcards For flow match entry
    @param mpls_type MPLS type
    @param mpls_label If not -1 create a pkt w/ MPLS tag
    @param mpls_tc MPLS TC associated with MPLS label
    @param mpls_ttl MPLS TTL associated with MPLS label
    @param mpls_label_int If not -1 create a pkt w/ Inner MPLS tag
    @param mpls_tc_int MPLS TC associated with Inner MPLS label
    @param mpls_ttl_int MPLS TTL associated with Inner MPLS label
    @param ip_ttl IP TTL
    @param label_match_tbl0 Matching value for MPLS LABEL field
    @param tc_match_tbl0 Matching value for MPLS TC field
    @param dl_type_match_tbl0 Matching value for DL_TYPE field
    @param action_list_tbl0 Additional actions to add to flow mod
    @param check_expire_tbl0 Check for flow expiration message
    @param match_exp_tbl0 Set whether packet is expected to receive
    @param exp_msg_tbl0 Expected message
    @param exp_msg_type_tbl0 Expected message type associated with the message
    @param exp_msg_code_tbl0 Expected message code associated with the msg_type
    @param label_match_tbl1 Matching value for MPLS LABEL field
    @param tc_match_tbl1 Matching value for MPLS TC field
    @param dl_type_match_tbl1 Matching value for DL_TYPE field
    @param action_list_tbl1 Additional actions to add to flow mod
    @param check_expire_tbl1 Check for flow expiration message
    @param match_exp_tbl0 Set whether packet is expected to receive
    @param exp_msg_tbl1 Expected message
    @param exp_msg_type_tbl1 Expected message type associated with the message
    @param exp_msg_code_tbl1 Expected message code associated with the msg_type
    @param add_tag_exp If True, expected_packet has an additional MPLS shim,
    If not expected_packet's MPLS shim is replaced as specified
    @param exp_mpls_type Expected MPLS ethertype
    @param exp_mpls_label Expected MPLS LABEL value. If -1, no MPLS expected
    @param exp_mpls_tc Expected MPLS TC value
    @param exp_mpls_ttl Expected MPLS TTL value
    @param exp_mpls_ttl_int Expected Inner MPLS TTL value
    @param exp_ip_ttl Expected IP TTL
    @param pkt If not None, use this packet for ingress
    @param exp_pkt If not None, use this as the expected output pkt
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
            flow_match_test_port_pair_mpls_two_tables(parent,
                                   ingress_port, egress_port,
                                   wildcards=wildcards,
                                   mpls_type=ETHERTYPE_MPLS,
                                   mpls_label=mpls_label,
                                   mpls_tc=mpls_tc,
                                   mpls_ttl=mpls_ttl,
                                   mpls_label_int=mpls_label_int,
                                   mpls_tc_int=mpls_tc_int,
                                   mpls_ttl_int=mpls_ttl_int,
                                   ip_ttl=ip_ttl,
                                   label_match_tbl0=label_match_tbl0,
                                   tc_match_tbl0=tc_match_tbl0,
                                   dl_type_match_tbl0=dl_type_match_tbl0,
                                   action_list_tbl0=action_list_tbl0,
                                   check_expire_tbl0=check_expire_tbl0,
                                   match_exp_tbl0=match_exp_tbl0,
                                   exp_msg_tbl0=exp_msg_tbl0,
                                   exp_msg_type_tbl0=exp_msg_type_tbl0,
                                   exp_msg_code_tbl0=exp_msg_code_tbl0,
                                   label_match_tbl1=label_match_tbl1,
                                   tc_match_tbl1=tc_match_tbl1,
                                   dl_type_match_tbl1=dl_type_match_tbl1,
                                   action_list_tbl1=action_list_tbl1,
                                   check_expire_tbl1=check_expire_tbl1,
                                   match_exp_tbl1=match_exp_tbl1,
                                   exp_msg_tbl1=exp_msg_tbl1,
                                   exp_msg_type_tbl1=exp_msg_type_tbl1,
                                   exp_msg_code_tbl1=exp_msg_code_tbl1,
                                   add_tag_exp=add_tag_exp,
                                   exp_mpls_type=exp_mpls_type,
                                   exp_mpls_label=exp_mpls_label,
                                   exp_mpls_tc=exp_mpls_tc,
                                   exp_mpls_ttl=exp_mpls_ttl,
                                   exp_mpls_ttl_int=exp_mpls_ttl_int,
                                   exp_ip_ttl=exp_ip_ttl,
                                   pkt=pkt, exp_pkt=exp_pkt)
            test_count += 1
            if (max_test > 0) and (test_count >= max_test):
                parent.logger.info("Ran " + str(test_count) + " tests; exiting")
                return

if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test-spec=multitable_mpls"
