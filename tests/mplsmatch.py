"""
Test cases for mpls match features

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

MODIFY_ACTION_VALUES =  [ofp.OFPAT_SET_VLAN_VID,
                         ofp.OFPAT_SET_VLAN_PCP,
                         ofp.OFPAT_SET_DL_SRC,
                         ofp.OFPAT_SET_DL_DST,
                         ofp.OFPAT_SET_NW_SRC,
                         ofp.OFPAT_SET_NW_DST,
                         ofp.OFPAT_SET_NW_TOS,
                         ofp.OFPAT_SET_TP_SRC,
                         ofp.OFPAT_SET_TP_DST]

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

class MplsExact(pktact.BaseMatchCase):
    """
    Exact match with MPLS tagged/untagged pkts
    Excercise various test_conditions
    Test on one pair of ports
    """
    def runTest(self):
        mpls_none_tests(self, mpls_label_mask = False, mpls_tc_mask=False)
        mpls_any_tests(self, mpls_label_mask = False, mpls_tc_mask=False)
        mpls_specific_tests(self, mpls_label_mask = False, mpls_tc_mask=False)
        mpls_outrange_tests(self, mpls_label_mask = False, mpls_tc_mask=False)

class MplsWildLabelExactTc(pktact.BaseMatchCase):
    """
    Wildcard LABEL and Exact TCP match with MPLS tagged/untagged pkts
    Excercise various test_conditions
    Test on one pair of ports
    """
    def runTest(self):
        mpls_none_tests(self, mpls_label_mask = True, mpls_tc_mask=False)
        mpls_any_tests(self, mpls_label_mask = True, mpls_tc_mask=False)
        mpls_specific_tests(self, mpls_label_mask = True, mpls_tc_mask=False)
        mpls_outrange_tests(self, mpls_label_mask = True, mpls_tc_mask=False)

class MplsExactLabelWildTc(pktact.BaseMatchCase):
    """
    Exact LABEL and Wildcard TC match with MPLS tagged/untagged pkts
    Excercise various test_conditions
    Test on one pair of ports
    """
    def runTest(self):
        mpls_none_tests(self, mpls_label_mask = False, mpls_tc_mask=True)
        mpls_any_tests(self, mpls_label_mask = False, mpls_tc_mask=True)
        mpls_specific_tests(self, mpls_label_mask = False, mpls_tc_mask=True)
        mpls_outrange_tests(self, mpls_label_mask = False, mpls_tc_mask=True)

class MplsWildAll(pktact.BaseMatchCase):
    """
    Wildcard LABEL and Exact TC match with MPLS tagged/untagged pkts
    Excercise various test_conditions
    Test on one pair of ports
    """
    def runTest(self):
        mpls_none_tests(self, mpls_label_mask = True, mpls_tc_mask=True)
        mpls_any_tests(self, mpls_label_mask = True, mpls_tc_mask=True)
        mpls_specific_tests(self, mpls_label_mask = True, mpls_tc_mask=True)
        mpls_outrange_tests(self, mpls_label_mask = True, mpls_tc_mask=True)


def mpls_none_tests(parent, mpls_label_mask=False, mpls_tc_mask=False):
    """
    MPLS match test with OFPML_NONE

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param mpls_label_mask If True, MPLS LABEL is wildcarded
    @param mpls_tc_mask If True, MPLS TC is wildcarded
    """
    wildcards = 0
    if mpls_label_mask == True:
        wildcards = ofp.OFPFW_MPLS_LABEL
    if mpls_tc_mask == True:
        wildcards = wildcards + ofp.OFPFW_MPLS_TC

    label_match = ofp.OFPML_NONE
    tc = random.randint(0, 7)
    ttl = 128

    exp_msg = ofp.OFPT_FLOW_REMOVED
    exp_msg_type = 0 #NOT_EXPECTED
    exp_msg_code = 0 #NOT_EXPECTED

    for test_condition in range(3):
        if test_condition == 0:
            label = -1
            tc_match = tc
            match_exp = True

        elif test_condition == 1:
            label = random.randint(16, 1048575)
            tc_match = 7 - tc # unmatching value
            if mpls_label_mask == True:
                match_exp = True
            else:
                match_exp = False

        elif test_condition == 2:
            label = random.randint(16, 1048575)
            tc_match = tc
            if mpls_label_mask == True:
                match_exp = True
            else:
                match_exp = False

        if match_exp == True:
            exp_label = label
            exp_tc = tc
        else:
            exp_label = 0 #NOT_EXPECTED
            exp_tc = 0 #NOT_EXPECTED

        flow_match_test_mpls(parent, pa_port_map,
                    mpls_label_btm=label,
                    mpls_tc_btm=tc,
                    mpls_ttl_btm=ttl,
                    mpls_label_ext=-1,
                    mpls_tc_ext=0,
                    label_match=label_match,
                    tc_match=tc_match,
                    wildcards=wildcards,
                    exp_mpls_label=exp_label,
                    exp_mpls_tc=exp_tc,
                    exp_mpls_ttl=ttl,
                    match_exp=match_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    max_test=1)

def mpls_any_tests(parent, mpls_label_mask=False, mpls_tc_mask=False):
    """
    MPLS match test with OFPML_ANY

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param mpls_label_mask If True, MPLS LABEL is wildcarded
    @param mpls_tc_mask If True, MPLS TC is wildcarded
    """
    wildcards = 0
    if mpls_label_mask == True:
        wildcards = ofp.OFPFW_MPLS_LABEL
    if mpls_tc_mask == True:
        wildcards = wildcards + ofp.OFPFW_MPLS_TC

    tc = random.randint(0, 7)
    ttl = 128
    label_match = ofp.OFPML_ANY

    exp_msg = ofp.OFPT_FLOW_REMOVED
    exp_msg_type = 0 #NOT_EXPECTED
    exp_msg_code = 0 #NOT_EXPECTED

    for test_condition in range(2):
        if test_condition == 0:
            label = -1
            tc_match = 7 - tc # unmatching value
            if mpls_label_mask == True:
                match_exp = True
            else:
                match_exp = False

        elif test_condition == 1:
            label = random.randint(16, 1048575)
            tc_match = 7 - tc # unmatching value
            if mpls_label_mask == True:
                match_exp = True
            else:
                match_exp = False

        if match_exp == True:
            exp_label = label
            exp_tc = tc
        else:
            exp_label = 0 #NOT_EXPECTED
            exp_tc = 0 #NOT_EXPECTED

        flow_match_test_mpls(parent, pa_port_map,
                    mpls_label_btm=label,
                    mpls_tc_btm=tc,
                    mpls_ttl_btm=ttl,
                    mpls_label_ext=-1,
                    mpls_tc_ext=0,
                    label_match=label_match,
                    tc_match=tc_match,
                    wildcards=wildcards,
                    exp_mpls_label=exp_label,
                    exp_mpls_tc=exp_tc,
                    exp_mpls_ttl=ttl,
                    match_exp=match_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    max_test=1)

def mpls_specific_tests(parent, mpls_label_mask=False, mpls_tc_mask=False):
    """
    MPLS match test with specific matching value

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param mpls_label_mask If True, MPLS LABEL is wildcarded
    @param mpls_tc_mask If True, MPLS TC is wildcarded
    """
    wildcards = 0
    if mpls_label_mask == True:
        wildcards = ofp.OFPFW_MPLS_LABEL
    if mpls_tc_mask == True:
        wildcards = wildcards + ofp.OFPFW_MPLS_TC

    ttl = 128
    label_match = random.randint(16, 1048575)
    tc_match = random.randint(0, 6)

    exp_msg = ofp.OFPT_FLOW_REMOVED
    exp_msg_type = 0 #NOT_EXPECTED
    exp_msg_code = 0 #NOT_EXPECTED

    for test_condition in range(6):
        label_2nd = -1
        tc_2nd = 0
        if test_condition == 0:
            label = -1
            tc = 0
            if mpls_label_mask == True:
                match_exp = True
            else:
                match_exp = False

        elif test_condition == 1:
            label = label_match
            tc = tc_match
            match_exp = True

        elif test_condition == 2:
            label = label_match
            tc = tc_match + 1
            if (mpls_label_mask == True) or (mpls_tc_mask == True):
                match_exp = True
            else:
                match_exp = False

        elif test_condition == 3:
            label = label_match + 1
            tc = tc_match
            if mpls_label_mask == True:
                match_exp = True
            else:
                match_exp = False

        elif test_condition == 4:
            label = label_match
            tc = tc_match
            label_2nd = label_match + 1
            tc_2nd = tc_match + 1
            match_exp = True

        elif test_condition == 5:
            label = label_match + 1
            tc = tc_match + 1
            if mpls_label_mask == True:
                match_exp = True
            else:
                match_exp = False

        if match_exp == True:
            exp_label = label
            exp_tc = tc
        else:
            exp_label = 0 #NOT_EXPECTED
            exp_tc = 0 #NOT_EXPECTED

        flow_match_test_mpls(parent, pa_port_map,
                    mpls_label_btm=label,
                    mpls_tc_btm=tc,
                    mpls_ttl_btm=ttl,
                    mpls_label_ext=label_2nd,
                    mpls_tc_ext=tc_2nd,
                    label_match=label_match,
                    tc_match=tc_match,
                    wildcards=wildcards,
                    exp_mpls_label=exp_label,
                    exp_mpls_tc=exp_tc,
                    exp_mpls_ttl=ttl,
                    match_exp=match_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    max_test=1)

def mpls_outrange_tests(parent, mpls_label_mask=False, mpls_tc_mask=False):
    """
    MPLS match test with out-of-range matching value, expecting an error

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param mpls_label_mask If True, MPLS LABEL is wildcarded
    @param mpls_tc_mask If True, MPLS TC is wildcarded
    """
    wildcards = 0
    if mpls_label_mask == True:
        wildcards = ofp.OFPFW_MPLS_LABEL
    if mpls_tc_mask == True:
        wildcards = wildcards + ofp.OFPFW_MPLS_TC

    label = random.randint(16, 1048575)
    tc = random.randint(0, 7)
    ttl = 128
    exp_label = 0 #NOT_EXPECTED
    exp_tc = 0 #NOT_EXPECTED
    match_exp = False
    exp_msg = ofp.OFPT_ERROR
    exp_msg_type = ofp.OFPET_FLOW_MOD_FAILED
    exp_msg_code = ofp.OFPFMFC_BAD_MATCH

    for test_condition in range(5):
        if test_condition == 0:
            label_match = ofp.OFPML_NONE
            tc_match = tc + 8  #out of range

        elif test_condition == 1:
            label_match = ofp.OFPML_ANY
            tc_match = tc + 8  #out of range

        elif test_condition == 2:
            label_match = label + 1048576  #out of range
            tc_match = tc

        elif test_condition == 3:
            label_match = label
            tc_match = tc + 8  #out of range

        elif test_condition == 4:
            label_match = label + 1048576  #out of range
            tc_match = tc + 8  #out of range

        flow_match_test_mpls(parent, pa_port_map,
                    mpls_label_btm=label,
                    mpls_tc_btm=tc,
                    mpls_ttl_btm=ttl,
                    mpls_label_ext=-1,
                    mpls_tc_ext=0,
                    label_match=label_match,
                    tc_match=tc_match,
                    wildcards=wildcards,
                    exp_mpls_label=exp_label,
                    exp_mpls_tc=exp_tc,
                    exp_mpls_ttl=ttl,
                    match_exp=match_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    max_test=1)

if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test-spec=mplsmatch"
