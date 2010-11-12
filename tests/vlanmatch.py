"""
Test cases for vlan match features

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

    pa_logger = logging.getLogger("pkt_act")
    pa_logger.info("Initializing test set")
    pa_port_map = config["port_map"]
    pa_config = config

###########################################################################

class VlanExact(pktact.BaseMatchCase):
    """
    Exact match with Vlan tagged/untagged pkts
    Excercise various test_conditions
    Test on one pair of ports
    """
    def runTest(self):
        vlan_none_tests(self, vlan_id_mask = False, vlan_pcp_mask=False)
        vlan_any_tests(self, vlan_id_mask = False, vlan_pcp_mask=False)
        vlan_specific_tests(self, vlan_id_mask = False, vlan_pcp_mask=False)
        vlan_outrange_tests(self, vlan_id_mask = False, vlan_pcp_mask=False)

class VlanWildIdExactPcp(pktact.BaseMatchCase):
    """
    Wildcard VID and Exact PCP match with Vlan tagged/untagged pkts
    Excercise various test_conditions
    Test on one pair of ports
    """
    def runTest(self):
        vlan_none_tests(self, vlan_id_mask = True, vlan_pcp_mask=False)
        vlan_any_tests(self, vlan_id_mask = True, vlan_pcp_mask=False)
        vlan_specific_tests(self, vlan_id_mask = True, vlan_pcp_mask=False)
        vlan_outrange_tests(self, vlan_id_mask = True, vlan_pcp_mask=False)

class VlanExactIdWildPcp(pktact.BaseMatchCase):
    """
    Exact VID and Wildcard PCP match with Vlan tagged/untagged pkts
    Excercise various test_conditions
    Test on one pair of ports
    """
    def runTest(self):
        vlan_none_tests(self, vlan_id_mask = False, vlan_pcp_mask=True)
        vlan_any_tests(self, vlan_id_mask = False, vlan_pcp_mask=True)
        vlan_specific_tests(self, vlan_id_mask = False, vlan_pcp_mask=True)
        vlan_outrange_tests(self, vlan_id_mask = False, vlan_pcp_mask=True)

class VlanWildAll(pktact.BaseMatchCase):
    """
    Wildcard VID and Exact PCP match with Vlan tagged/untagged pkts
    Excercise various test_conditions
    Test on one pair of ports
    """
    def runTest(self):
        vlan_none_tests(self, vlan_id_mask = True, vlan_pcp_mask=True)
        vlan_any_tests(self, vlan_id_mask = True, vlan_pcp_mask=True)
        vlan_specific_tests(self, vlan_id_mask = True, vlan_pcp_mask=True)
        vlan_outrange_tests(self, vlan_id_mask = True, vlan_pcp_mask=True)


def vlan_none_tests(parent, vlan_id_mask=False, vlan_pcp_mask=False):
    """
    Vlan match test with OFPVID_NONE

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param vlan_id_mask If True, VLAN ID is wildcarded
    @param vlan_pcp_mask If True, VLAN PCP is wildcarded
    """
    wildcards = 0
    if vlan_id_mask == True:
        wildcards = ofp.OFPFW_DL_VLAN
    if vlan_pcp_mask == True:
        wildcards = wildcards + ofp.OFPFW_DL_VLAN_PCP

    vid_match = ofp.OFPVID_NONE
    pcp = random.randint(0, 7)

    exp_msg = ofp.OFPT_FLOW_REMOVED
    exp_msg_type = 0 #NOT_EXPECTED
    exp_msg_code = 0 #NOT_EXPECTED

    for test_condition in range(3):
        if test_condition == 0:
            vid = -1
            pcp_match = pcp
            match_exp = True

        elif test_condition == 1:
            vid = random.randint(0, 4095)
            pcp_match = 7 - pcp # unmatching value
            if vlan_id_mask == True:
                match_exp = True
            else:
                match_exp = False

        elif test_condition == 2:
            vid = random.randint(0, 4095)
            pcp_match = pcp
            if vlan_id_mask == True:
                match_exp = True
            else:
                match_exp = False

        if match_exp == True:
            exp_vid = vid
            exp_pcp = pcp
        else:
            exp_vid = 0 #NOT_EXPECTED
            exp_pcp = 0 #NOT_EXPECTED

        flow_match_test_vlan(parent, pa_port_map,
                    dl_vlan=vid,
                    dl_vlan_pcp=pcp,
                    dl_vlan_2nd=-1,
                    dl_vlan_pcp_2nd=0,
                    vid_match=vid_match,
                    pcp_match=pcp_match,
                    exp_vid=exp_vid,
                    exp_pcp=exp_pcp,
                    wildcards=wildcards,
                    match_exp=match_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    max_test=1)

def vlan_any_tests(parent, vlan_id_mask=False, vlan_pcp_mask=False):
    """
    Vlan match test with OFPVID_ANY

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param vlan_id_mask If True, VLAN ID is wildcarded
    @param vlan_pcp_mask If True, VLAN PCP is wildcarded
    """
    wildcards = 0
    if vlan_id_mask == True:
        wildcards = ofp.OFPFW_DL_VLAN
    if vlan_pcp_mask == True:
        wildcards = wildcards + ofp.OFPFW_DL_VLAN_PCP

    pcp = random.randint(0, 7)
    vid_match = ofp.OFPVID_ANY

    exp_msg = ofp.OFPT_FLOW_REMOVED
    exp_msg_type = 0 #NOT_EXPECTED
    exp_msg_code = 0 #NOT_EXPECTED

    for test_condition in range(2):
        if test_condition == 0:
            vid = -1
            pcp_match = 7 - pcp # unmatching value
            if vlan_id_mask == True:
                match_exp = True
            else:
                match_exp = False

        elif test_condition == 1:
            vid = random.randint(0, 4095)
            pcp_match = 7 - pcp # unmatching value
            if vlan_id_mask == True:
                match_exp = False
            else:
                match_exp = True

        if match_exp == True:
            exp_vid = vid
            exp_pcp = pcp
        else:
            exp_vid = 0 #NOT_EXPECTED
            exp_pcp = 0 #NOT_EXPECTED

        flow_match_test_vlan(parent, pa_port_map,
                    dl_vlan=vid,
                    dl_vlan_pcp=pcp,
                    dl_vlan_2nd=-1,
                    dl_vlan_pcp_2nd=0,
                    vid_match=vid_match,
                    pcp_match=pcp_match,
                    exp_vid=exp_vid,
                    exp_pcp=exp_pcp,
                    wildcards=wildcards,
                    match_exp=match_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    max_test=1)

def vlan_specific_tests(parent, vlan_id_mask=False, vlan_pcp_mask=False):
    """
    Vlan match test with specific matching value

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param vlan_id_mask If True, VLAN ID is wildcarded
    @param vlan_pcp_mask If True, VLAN PCP is wildcarded
    """
    wildcards = 0
    if vlan_id_mask == True:
        wildcards = ofp.OFPFW_DL_VLAN
    if vlan_pcp_mask == True:
        wildcards = wildcards + ofp.OFPFW_DL_VLAN_PCP

    vid_match = random.randint(0, 4094)
    pcp_match = random.randint(0, 6)

    exp_msg = ofp.OFPT_FLOW_REMOVED
    exp_msg_type = 0 #NOT_EXPECTED
    exp_msg_code = 0 #NOT_EXPECTED

    for test_condition in range(6):
        if test_condition == 0:
            vid = -1
            pcp = 0
            if (vlan_id_mask == True) and (vlan_pcp_mask == True):
                match_exp = True
            else:
                match_exp = False

        elif test_condition == 1:
            vid = vid_match
            pcp = pcp_match
            match_exp = True

        elif test_condition == 2:
            vid = vid_match
            pcp = pcp_match + 1
            if vlan_pcp_mask == True:
                match_exp = True
            else:
                match_exp = False

        elif test_condition == 3:
            vid = vid_match + 1
            pcp = pcp_match
            if vlan_id_mask == True:
                match_exp = True
            else:
                match_exp = False

        elif test_condition == 4:
            vid = vid_match
            pcp = pcp_match
            vid_2nd = vid_match + 1
            pcp_2nd = pcp_match + 1
            match_exp = True

        elif test_condition == 5:
            vid = vid_match + 1
            pcp = pcp_match + 1
            if (vlan_id_mask == True) and (vlan_pcp_mask == True):
                match_exp = True
            else:
                match_exp = False

        if match_exp == True:
            exp_vid = vid
            exp_pcp = pcp
        else:
            exp_vid = 0 #NOT_EXPECTED
            exp_pcp = 0 #NOT_EXPECTED

        flow_match_test_vlan(parent, pa_port_map,
                    dl_vlan=vid,
                    dl_vlan_pcp=pcp,
                    dl_vlan_2nd=-1,
                    dl_vlan_pcp_2nd=0,
                    vid_match=vid_match,
                    pcp_match=pcp_match,
                    exp_vid=exp_vid,
                    exp_pcp=exp_pcp,
                    wildcards=wildcards,
                    match_exp=match_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    max_test=1)

def vlan_outrange_tests(parent, vlan_id_mask=False, vlan_pcp_mask=False):
    """
    Vlan match test with out-of-range matching value, expecting an error
    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param vlan_id_mask If True, VLAN ID is wildcarded
    @param vlan_pcp_mask If True, VLAN PCP is wildcarded
    """
    wildcards = 0
    if vlan_id_mask == True:
        wildcards = ofp.OFPFW_DL_VLAN
    if vlan_pcp_mask == True:
        wildcards = wildcards + ofp.OFPFW_DL_VLAN_PCP

    vid = random.randint(0, 4095)
    pcp = random.randint(0, 7)
    exp_vid = 0 #NOT_EXPECTED
    exp_pcp = 0 #NOT_EXPECTED
    match_exp = False
    exp_msg = ofp.OFPT_ERROR
    exp_msg_type = ofp.OFPET_FLOW_MOD_FAILED
    exp_msg_code = ofp.OFPFMFC_BAD_MATCH

    for test_condition in range(5):
        if test_condition == 0:
            vid_match = ofp.OFPVID_NONE
            pcp_match = pcp + 8  #out of range

        elif test_condition == 1:
            vid_match = ofp.OFPVID_ANY
            pcp_match = pcp + 8  #out of range

        elif test_condition == 2:
            vid_match = vid + 4096  #out of range
            pcp_match = pcp

        elif test_condition == 3:
            vid_match = vid
            pcp_match = pcp + 8  #out of range

        elif test_condition == 4:
            vid_match = vid + 4096  #out of range
            pcp_match = pcp + 8  #out of range

        flow_match_test_vlan(parent, pa_port_map,
                    dl_vlan=vid,
                    dl_vlan_pcp=pcp,
                    dl_vlan_2nd=-1,
                    dl_vlan_pcp_2nd=0,
                    vid_match=vid_match,
                    pcp_match=pcp_match,
                    exp_vid=exp_vid,
                    exp_pcp=exp_pcp,
                    wildcards=wildcards,
                    match_exp=match_exp,
                    exp_msg=exp_msg,
                    exp_msg_type=exp_msg_type,
                    exp_msg_code=exp_msg_code,
                    max_test=1)

if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test-spec=basic"
