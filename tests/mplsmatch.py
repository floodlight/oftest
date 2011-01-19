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

    pa_logger = logging.getLogger("mpls_match")
    pa_logger.info("Initializing test set")
    pa_port_map = config["port_map"]
    pa_config = config

###########################################################################

class MplsExactNone0(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_NONE  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - LABEL: N/A  TC: N/A
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_none_tests(self, mpls_label_mask = False, mpls_tc_mask=False,
                        test_condition=0)

class MplsExactNone1(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_NONE  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: unmatch value  TC: unmatch value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_none_tests(self, mpls_label_mask = False, mpls_tc_mask=False,
                        test_condition=1)

class MplsExactNone2(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_NONE  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: unmatch value  TC: match value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_none_tests(self, mpls_label_mask = False, mpls_tc_mask=False,
                        test_condition=2)

class MplsExactAny0(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_ANY  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - LABEL: N/A  TC: N/A
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_any_tests(self, mpls_label_mask = False, mpls_tc_mask=False,
                       test_condition=0)

class MplsExactAny1(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_ANY  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: unmatch value  TC: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_any_tests(self, mpls_label_mask = False, mpls_tc_mask=False,
                       test_condition=1)

class MplsExactSpecific0(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - LABEL: N/A  TC: N/A
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = False, mpls_tc_mask=False,
                            test_condition=0)

class MplsExactSpecific1(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: match value  TC: match value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = False, mpls_tc_mask=False,
                            test_condition=1)

class MplsExactSpecific2(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: match value  TC: unmatch value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = False, mpls_tc_mask=False,
                            test_condition=2)

class MplsExactSpecific3(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: unmatch value  TC: match value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = False, mpls_tc_mask=False,
                            test_condition=3)

class MplsExactSpecific4(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 2
     - LABEL: match value  TC: match value
     - Inner LABEL: unmatch value  TC: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = False, mpls_tc_mask=False,
                            test_condition=4)

class MplsExactSpecific5(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 2
     - LABEL: unmatch value  TC: ummatch value
     - Inner LABEL: match value  TC: match value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = False, mpls_tc_mask=False,
                            test_condition=5)

class MplsExactOutrange0(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_NONE  TC: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_outrange_tests(self, mpls_label_mask = False, mpls_tc_mask=False,
                            test_condition=0)

class MplsExactOutrange1(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_ANY  TC: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - FLOW_MOD_FAILED error
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_outrange_tests(self, mpls_label_mask = False, mpls_tc_mask=False,
                            test_condition=1)

class MplsExactOutrange2(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: outrange value  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - FLOW_MOD_FAILED error
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_outrange_tests(self, mpls_label_mask = False, mpls_tc_mask=False,
                            test_condition=2)

class MplsExactOutrange3(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - FLOW_MOD_FAILED error
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_outrange_tests(self, mpls_label_mask = False, mpls_tc_mask=False,
                            test_condition=3)

class MplsExactOutrange4(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: outrange value  TC: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - FLOW_MOD_FAILED error
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_outrange_tests(self, mpls_label_mask = False, mpls_tc_mask=False,
                            test_condition=4)

class MplsWildLabelExactTcNone0(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL and Exact TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_NONE  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - LABEL: N/A  TC: N/A
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_none_tests(self, mpls_label_mask = True, mpls_tc_mask=False,
                        test_condition=0)

class MplsWildLabelExactTcNone1(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL and Exact TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_NONE  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: unmatch value  TC: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_none_tests(self, mpls_label_mask = True, mpls_tc_mask=False,
                        test_condition=1)

class MplsWildLabelExactTcNone2(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL and Exact TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_NONE  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: unmatch value  TC: match value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_none_tests(self, mpls_label_mask = True, mpls_tc_mask=False,
                        test_condition=2)

class MplsWildLabelExactTcAny0(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL and Exact TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_ANY  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - LABEL: N/A  TC: N/A
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_any_tests(self, mpls_label_mask = True, mpls_tc_mask=False,
                       test_condition=0)

class MplsWildLabelExactTcAny1(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL and Exact TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_ANY  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: unmatch value  TC: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_any_tests(self, mpls_label_mask = True, mpls_tc_mask=False,
                       test_condition=1)

class MplsWildLabelExactTcSpecific0(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL and Exact TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - LABEL: N/A  TC: N/A
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = True, mpls_tc_mask=False,
                            test_condition=0)

class MplsWildLabelExactTcSpecific1(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL and Exact TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: match value  TC: match value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = True, mpls_tc_mask=False,
                            test_condition=1)

class MplsWildLabelExactTcSpecific2(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL and Exact TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: match value  TC: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = True, mpls_tc_mask=False,
                            test_condition=2)

class MplsWildLabelExactTcSpecific3(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL and Exact TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: unmatch value  TC: match value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = True, mpls_tc_mask=False,
                            test_condition=3)

class MplsWildLabelExactTcSpecific4(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL and Exact TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 2
     - LABEL: match value  TC: match value
     - Inner LABEL: unmatch value  TC: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = True, mpls_tc_mask=False,
                            test_condition=4)

class MplsWildLabelExactTcSpecific5(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL and Exact TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 2
     - LABEL: unmatch value  TC: ummatch value
     - Inner LABEL: match value  TC: match value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = True, mpls_tc_mask=False,
                            test_condition=5)

class MplsWildLabelExactTcOutrange0(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL and Exact TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_NONE  TC: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_outrange_tests(self, mpls_label_mask = True, mpls_tc_mask=False,
                            test_condition=0)

class MplsWildLabelExactTcOutrange1(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL and Exact TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_ANY  TC: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_outrange_tests(self, mpls_label_mask = True, mpls_tc_mask=False,
                            test_condition=1)

class MplsWildLabelExactTcOutrange2(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL and Exact TC
    Test conditions:
    - MATCH
     - LABEL: outrange value  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_outrange_tests(self, mpls_label_mask = True, mpls_tc_mask=False,
                            test_condition=2)

class MplsWildLabelExactTcOutrange3(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL and Exact TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_outrange_tests(self, mpls_label_mask = True, mpls_tc_mask=False,
                            test_condition=3)

class MplsWildLabelExactTcOutrange4(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL and Exact TC
    Test conditions:
    - MATCH
     - LABEL: outrange value  TC: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_outrange_tests(self, mpls_label_mask = True, mpls_tc_mask=False,
                            test_condition=4)

class MplsExactLabelWildTcNone0(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL and Wildcard TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_NONE  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - LABEL: N/A  TC: N/A
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_none_tests(self, mpls_label_mask = False, mpls_tc_mask=True,
                        test_condition=0)

class MplsExactLabelWildTcNone1(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL and Wildcard TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_NONE  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: unmatch value  TC: unmatch value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_none_tests(self, mpls_label_mask = False, mpls_tc_mask=True,
                        test_condition=1)

class MplsExactLabelWildTcNone2(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL and Wildcard TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_NONE  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: unmatch value  TC: match value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_none_tests(self, mpls_label_mask = False, mpls_tc_mask=True,
                        test_condition=2)

class MplsExactLabelWildTcAny0(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL and Wildcard TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_ANY  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - LABEL: N/A  TC: N/A
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_any_tests(self, mpls_label_mask = False, mpls_tc_mask=True,
                       test_condition=0)

class MplsExactLabelWildTcAny1(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL and Wildcard TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_ANY  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: unmatch value  TC: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_any_tests(self, mpls_label_mask = False, mpls_tc_mask=True,
                       test_condition=1)

class MplsExactLabelWildTcSpecific0(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL and Wildcard TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - LABEL: N/A  TC: N/A
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = False, mpls_tc_mask=True,
                            test_condition=0)

class MplsExactLabelWildTcSpecific1(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL and Wildcard TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: match value  TC: match value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = False, mpls_tc_mask=True,
                            test_condition=1)

class MplsExactLabelWildTcSpecific2(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL and Wildcard TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: match value  TC: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = False, mpls_tc_mask=True,
                            test_condition=2)

class MplsExactLabelWildTcSpecific3(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL and Wildcard TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: unmatch value  TC: match value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = False, mpls_tc_mask=True,
                            test_condition=3)

class MplsExactLabelWildTcSpecific4(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL and Wildcard TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 2
     - LABEL: match value  TC: match value
     - Inner LABEL: unmatch value  TC: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = False, mpls_tc_mask=True,
                            test_condition=4)

class MplsExactLabelWildTcSpecific5(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL and Wildcard TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 2
     - LABEL: unmatch value  TC: ummatch value
     - Inner LABEL: match value  TC: match value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = False, mpls_tc_mask=True,
                            test_condition=5)

class MplsExactLabelWildTcOutrange0(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL and Wildcard TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_NONE  TC: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_outrange_tests(self, mpls_label_mask = False, mpls_tc_mask=True,
                            test_condition=0)

class MplsExactLabelWildTcOutrange1(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL and Wildcard TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_ANY  TC: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_outrange_tests(self, mpls_label_mask = False, mpls_tc_mask=True,
                            test_condition=1)

class MplsExactLabelWildTcOutrange2(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL and Wildcard TC
    Test conditions:
    - MATCH
     - LABEL: outrange value  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - FLOW_MOD_FAILED error
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_outrange_tests(self, mpls_label_mask = False, mpls_tc_mask=True,
                            test_condition=2)

class MplsExactLabelWildTcOutrange3(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL and Wildcard TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_outrange_tests(self, mpls_label_mask = False, mpls_tc_mask=True,
                            test_condition=3)

class MplsExactLabelWildTcOutrange4(pktact.BaseMatchCase):
    """
    MPLS match test with Exact LABEL and Wildcard TC
    Test conditions:
    - MATCH
     - LABEL: outrange value  TC: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - FLOW_MOD_FAILED error
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_outrange_tests(self, mpls_label_mask = False, mpls_tc_mask=True,
                            test_condition=4)

class MplsWildNone0(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_NONE  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - LABEL: N/A  TC: N/A
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_none_tests(self, mpls_label_mask = True, mpls_tc_mask=True,
                        test_condition=0)

class MplsWildNone1(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_NONE  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: unmatch value  TC: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_none_tests(self, mpls_label_mask = True, mpls_tc_mask=True,
                        test_condition=1)

class MplsWildNone2(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_NONE  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: unmatch value  TC: match value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_none_tests(self, mpls_label_mask = True, mpls_tc_mask=True,
                        test_condition=2)

class MplsWildAny0(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_ANY  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - LABEL: N/A  TC: N/A
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_any_tests(self, mpls_label_mask = True, mpls_tc_mask=True,
                       test_condition=0)

class MplsWildAny1(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_ANY  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: unmatch value  TC: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_any_tests(self, mpls_label_mask = True, mpls_tc_mask=True,
                       test_condition=1)

class MplsWildSpecific0(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - LABEL: N/A  TC: N/A
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = True, mpls_tc_mask=True,
                            test_condition=0)

class MplsWildSpecific1(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: match value  TC: match value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = True, mpls_tc_mask=True,
                            test_condition=1)

class MplsWildSpecific2(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: match value  TC: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = True, mpls_tc_mask=True,
                            test_condition=2)

class MplsWildSpecific3(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - LABEL: unmatch value  TC: match value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = True, mpls_tc_mask=True,
                            test_condition=3)

class MplsWildSpecific4(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 2
     - LABEL: match value  TC: match value
     - Inner LABEL: unmatch value  TC: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = True, mpls_tc_mask=True,
                            test_condition=4)

class MplsWildSpecific5(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 2
     - LABEL: unmatch value  TC: ummatch value
     - Inner LABEL: match value  TC: match value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_specific_tests(self, mpls_label_mask = True, mpls_tc_mask=True,
                            test_condition=5)

class MplsWildOutrange0(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_NONE  TC: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_outrange_tests(self, mpls_label_mask = True, mpls_tc_mask=True,
                            test_condition=0)

class MplsWildOutrange1(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: OFPML_ANY  TC: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_outrange_tests(self, mpls_label_mask = True, mpls_tc_mask=True,
                            test_condition=1)

class MplsWildOutrange2(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: outrange value  TC: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_outrange_tests(self, mpls_label_mask = True, mpls_tc_mask=True,
                            test_condition=2)

class MplsWildOutrange3(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: SPECIFIC  TC: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_outrange_tests(self, mpls_label_mask = True, mpls_tc_mask=True,
                            test_condition=3)

class MplsWildOutrange4(pktact.BaseMatchCase):
    """
    MPLS match test with Wildcard LABEL, TC
    Test conditions:
    - MATCH
     - LABEL: outrange value  TC: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        mpls_outrange_tests(self, mpls_label_mask = True, mpls_tc_mask=True,
                            test_condition=4)


def mpls_none_tests(parent, mpls_label_mask=False, mpls_tc_mask=False,
                    test_condition=0):
    """
    MPLS match test with OFPML_NONE

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param mpls_label_mask If True, MPLS LABEL is wildcarded
    @param mpls_tc_mask If True, MPLS TC is wildcarded
    @param test_condition Value between 0 and 2
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

    else:
        return

    if match_exp == True:
        exp_label = label
        exp_tc = tc
        exp_ttl = ttl
    else:
        exp_label = 0 #NOT_EXPECTED
        exp_tc = 0 #NOT_EXPECTED
        exp_ttl = 0 #NOT_EXPECTED

    testutils.flow_match_test_mpls(parent, pa_port_map,
                wildcards=wildcards,
                mpls_label=label,
                mpls_tc=tc,
                mpls_ttl=ttl,
                mpls_label_int=-1,
                mpls_tc_int=0,
                label_match=label_match,
                tc_match=tc_match,
                exp_mpls_label=exp_label,
                exp_mpls_tc=exp_tc,
                exp_mpls_ttl=exp_ttl,
                match_exp=match_exp,
                exp_msg=exp_msg,
                exp_msg_type=exp_msg_type,
                exp_msg_code=exp_msg_code,
                max_test=1)

def mpls_any_tests(parent, mpls_label_mask=False, mpls_tc_mask=False,
                   test_condition=0):
    """
    MPLS match test with OFPML_ANY

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param mpls_label_mask If True, MPLS LABEL is wildcarded
    @param mpls_tc_mask If True, MPLS TC is wildcarded
    @param test_condition Value between 0 and 1
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
        match_exp = True

    else:
        return

    if match_exp == True:
        exp_label = label
        exp_tc = tc
        exp_ttl = ttl
    else:
        exp_label = 0 #NOT_EXPECTED
        exp_tc = 0 #NOT_EXPECTED
        exp_ttl = 0 #NOT_EXPECTED

    testutils.flow_match_test_mpls(parent, pa_port_map,
                wildcards=wildcards,
                mpls_label=label,
                mpls_tc=tc,
                mpls_ttl=ttl,
                mpls_label_int=-1,
                mpls_tc_int=0,
                label_match=label_match,
                tc_match=tc_match,
                exp_mpls_label=exp_label,
                exp_mpls_tc=exp_tc,
                exp_mpls_ttl=exp_ttl,
                match_exp=match_exp,
                exp_msg=exp_msg,
                exp_msg_type=exp_msg_type,
                exp_msg_code=exp_msg_code,
                max_test=1)

def mpls_specific_tests(parent, mpls_label_mask=False, mpls_tc_mask=False,
                        test_condition=0):
    """
    MPLS match test with specific matching value

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param mpls_label_mask If True, MPLS LABEL is wildcarded
    @param mpls_tc_mask If True, MPLS TC is wildcarded
    @param test_condition Value between 0 and 5
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

    label_int = -1
    tc_int = 0
    ttl_int = 0

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
        label_int = label_match + 1
        tc_int = tc_match + 1
        ttl_int = ttl + 1
        match_exp = True

    elif test_condition == 5:
        label = label_match + 1
        tc = tc_match + 1
        if mpls_label_mask == True:
            match_exp = True
        else:
            match_exp = False

    else:
        return

    if match_exp == True:
        exp_label = label
        exp_tc = tc
        exp_ttl = ttl
        exp_ttl_int = ttl_int
    else:
        exp_label = 0 #NOT_EXPECTED
        exp_tc = 0 #NOT_EXPECTED
        exp_ttl = 0 #NOT_EXPECTED
        exp_ttl_int = 0 #NOT_EXPECTED

    testutils.flow_match_test_mpls(parent, pa_port_map,
                wildcards=wildcards,
                mpls_label=label,
                mpls_tc=tc,
                mpls_ttl=ttl,
                mpls_label_int=label_int,
                mpls_tc_int=tc_int,
                mpls_ttl_int=ttl_int,
                label_match=label_match,
                tc_match=tc_match,
                exp_mpls_label=exp_label,
                exp_mpls_tc=exp_tc,
                exp_mpls_ttl=exp_ttl,
                exp_mpls_ttl_int=exp_ttl_int,
                match_exp=match_exp,
                exp_msg=exp_msg,
                exp_msg_type=exp_msg_type,
                exp_msg_code=exp_msg_code,
                max_test=1)

def mpls_outrange_tests(parent, mpls_label_mask=False, mpls_tc_mask=False,
                        test_condition=0):
    """
    MPLS match test with out-of-range matching value, expecting an error

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param mpls_label_mask If True, MPLS LABEL is wildcarded
    @param mpls_tc_mask If True, MPLS TC is wildcarded
    @param test_condition Value between 0 and 4
    """
    wildcards = 0
    if mpls_label_mask == True:
        wildcards = ofp.OFPFW_MPLS_LABEL
    if mpls_tc_mask == True:
        wildcards = wildcards + ofp.OFPFW_MPLS_TC

    label = random.randint(16, 1048575)
    tc = random.randint(0, 7)
    ttl = 128

    if test_condition == 0:
        label_match = ofp.OFPML_NONE
        tc_match = tc + 8  #out of range
        if mpls_label_mask == True:
            match_exp = True
        else:
            match_exp = False
        exp_msg = ofp.OFPT_FLOW_REMOVED
        exp_msg_type = 0 #NOT EXPECTED
        exp_msg_code = 0 #NOT EXPECTED

    elif test_condition == 1:
        label_match = ofp.OFPML_ANY
        tc_match = tc + 8  #out of range
        if (mpls_label_mask == True) or (mpls_tc_mask == True):
            match_exp = True
            exp_msg = ofp.OFPT_FLOW_REMOVED
            exp_msg_type = 0 #NOT EXPECTED
            exp_msg_code = 0 #NOT EXPECTED
        else:
            match_exp = False
            exp_msg = ofp.OFPT_ERROR
            exp_msg_type = ofp.OFPET_FLOW_MOD_FAILED
            exp_msg_code = ofp.OFPFMFC_BAD_MATCH

    elif test_condition == 2:
        label_match = label + 1048576  #out of range
        tc_match = tc
        if mpls_label_mask == True:
            match_exp = True
            exp_msg = ofp.OFPT_FLOW_REMOVED
            exp_msg_type = 0 #NOT EXPECTED
            exp_msg_code = 0 #NOT EXPECTED
        else:
            match_exp = False
            exp_msg = ofp.OFPT_ERROR
            exp_msg_type = ofp.OFPET_FLOW_MOD_FAILED
            exp_msg_code = ofp.OFPFMFC_BAD_MATCH

    elif test_condition == 3:
        label_match = label
        tc_match = tc + 8  #out of range
        if (mpls_label_mask == True) or (mpls_tc_mask == True):
            match_exp = True
            exp_msg = ofp.OFPT_FLOW_REMOVED
            exp_msg_type = 0 #NOT EXPECTED
            exp_msg_code = 0 #NOT EXPECTED
        else:
            match_exp = False
            exp_msg = ofp.OFPT_ERROR
            exp_msg_type = ofp.OFPET_FLOW_MOD_FAILED
            exp_msg_code = ofp.OFPFMFC_BAD_MATCH

    elif test_condition == 4:
        label_match = label + 1048576  #out of range
        tc_match = tc + 8  #out of range
        if mpls_label_mask == True:
            match_exp = True
            exp_msg = ofp.OFPT_FLOW_REMOVED
            exp_msg_type = 0 #NOT EXPECTED
            exp_msg_code = 0 #NOT EXPECTED
        else:
            match_exp = False
            exp_msg = ofp.OFPT_ERROR
            exp_msg_type = ofp.OFPET_FLOW_MOD_FAILED
            exp_msg_code = ofp.OFPFMFC_BAD_MATCH

    else:
        return

    if match_exp == True:
        exp_label = label
        exp_tc = tc
        exp_ttl = ttl
    else:
        exp_label = 0 #NOT EXPECTED
        exp_tc = 0 #NOT EXPECTED
        exp_ttl = 0 #NOT EXPECTED

    testutils.flow_match_test_mpls(parent, pa_port_map,
                wildcards=wildcards,
                mpls_label=label,
                mpls_tc=tc,
                mpls_ttl=ttl,
                mpls_label_int=-1,
                mpls_tc_int=0,
                label_match=label_match,
                tc_match=tc_match,
                exp_mpls_label=exp_label,
                exp_mpls_tc=exp_tc,
                exp_mpls_ttl=exp_ttl,
                match_exp=match_exp,
                exp_msg=exp_msg,
                exp_msg_type=exp_msg_type,
                exp_msg_code=exp_msg_code,
                max_test=1)

if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test-spec=mplsmatch"
