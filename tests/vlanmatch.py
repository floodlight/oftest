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

    pa_logger = logging.getLogger("vlan_match")
    pa_logger.info("Initializing test set")
    pa_port_map = config["port_map"]
    pa_config = config

###########################################################################

class VlanExactNone0(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID, PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_NONE  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - VID: N/A  PCP: N/A
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_none_tests(self, vlan_id_mask = False, vlan_pcp_mask=False,
                        test_condition=0)

class VlanExactNone1(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID, PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_NONE  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: unmatch value  PCP: unmatch value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_none_tests(self, vlan_id_mask = False, vlan_pcp_mask=False,
                        test_condition=1)

class VlanExactNone2(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID, PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_NONE  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: unmatch value  PCP: match value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_none_tests(self, vlan_id_mask = False, vlan_pcp_mask=False,
                        test_condition=2)

class VlanExactAny0(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID, PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_ANY  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - VID: N/A  PCP: N/A
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_any_tests(self, vlan_id_mask = False, vlan_pcp_mask=False,
                       test_condition=0)

class VlanExactAny1(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID, PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_ANY  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: unmatch value  PCP: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_any_tests(self, vlan_id_mask = False, vlan_pcp_mask=False,
                       test_condition=1)

class VlanExactSpecific0(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID, PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - VID: N/A  PCP: N/A
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = False, vlan_pcp_mask=False,
                            test_condition=0)

class VlanExactSpecific1(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID, PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: match value  PCP: match value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = False, vlan_pcp_mask=False,
                            test_condition=1)

class VlanExactSpecific2(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID, PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: match value  PCP: unmatch value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = False, vlan_pcp_mask=False,
                            test_condition=2)

class VlanExactSpecific3(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID, PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: unmatch value  PCP: match value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = False, vlan_pcp_mask=False,
                            test_condition=3)

class VlanExactSpecific4(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID, PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 2
     - VID: match value  PCP: match value
     - Inner VID: unmatch value  PCP: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = False, vlan_pcp_mask=False,
                            test_condition=4)

class VlanExactSpecific5(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID, PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 2
     - VID: unmatch value  PCP: ummatch value
     - Inner VID: match value  PCP: match value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = False, vlan_pcp_mask=False,
                            test_condition=5)

class VlanExactOutrange0(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID, PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_NONE  PCP: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_outrange_tests(self, vlan_id_mask = False, vlan_pcp_mask=False,
                            test_condition=0)

class VlanExactOutrange1(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID, PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_ANY  PCP: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_outrange_tests(self, vlan_id_mask = False, vlan_pcp_mask=False,
                            test_condition=1)

class VlanExactOutrange2(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID, PCP
    Test conditions:
    - MATCH
     - VID: outrange value  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - FLOW_MOD_FAILED error
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_outrange_tests(self, vlan_id_mask = False, vlan_pcp_mask=False,
                            test_condition=2)

class VlanExactOutrange3(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID, PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - FLOW_MOD_FAILED error
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_outrange_tests(self, vlan_id_mask = False, vlan_pcp_mask=False,
                            test_condition=3)

class VlanExactOutrange4(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID, PCP
    Test conditions:
    - MATCH
     - VID: outrange value  PCP: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - FLOW_MOD_FAILED error
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_outrange_tests(self, vlan_id_mask = False, vlan_pcp_mask=False,
                            test_condition=4)

class VlanWildIdExactPcpNone0(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID and Exact PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_NONE  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - VID: N/A  PCP: N/A
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_none_tests(self, vlan_id_mask = True, vlan_pcp_mask=False,
                        test_condition=0)

class VlanWildIdExactPcpNone1(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID and Exact PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_NONE  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: unmatch value  PCP: unmatch value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_none_tests(self, vlan_id_mask = True, vlan_pcp_mask=False,
                        test_condition=1)

class VlanWildIdExactPcpNone2(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID and Exact PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_NONE  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: unmatch value  PCP: match value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_none_tests(self, vlan_id_mask = True, vlan_pcp_mask=False,
                        test_condition=2)

class VlanWildIdExactPcpAny0(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID and Exact PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_ANY  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - VID: N/A  PCP: N/A
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_any_tests(self, vlan_id_mask = True, vlan_pcp_mask=False,
                       test_condition=0)

class VlanWildIdExactPcpAny1(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID and Exact PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_ANY  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: unmatch value  PCP: unmatch value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_any_tests(self, vlan_id_mask = True, vlan_pcp_mask=False,
                       test_condition=1)

class VlanWildIdExactPcpSpecific0(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID and Exact PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - VID: N/A  PCP: N/A
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = True, vlan_pcp_mask=False,
                            test_condition=0)

class VlanWildIdExactPcpSpecific1(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID and Exact PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: match value  PCP: match value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = True, vlan_pcp_mask=False,
                            test_condition=1)

class VlanWildIdExactPcpSpecific2(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID and Exact PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: match value  PCP: unmatch value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = True, vlan_pcp_mask=False,
                            test_condition=2)

class VlanWildIdExactPcpSpecific3(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID and Exact PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: unmatch value  PCP: match value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = True, vlan_pcp_mask=False,
                            test_condition=3)

class VlanWildIdExactPcpSpecific4(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID and Exact PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 2
     - VID: match value  PCP: match value
     - Inner VID: unmatch value  PCP: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = True, vlan_pcp_mask=False,
                            test_condition=4)

class VlanWildIdExactPcpSpecific5(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID and Exact PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 2
     - VID: unmatch value  PCP: ummatch value
     - Inner VID: match value  PCP: match value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = True, vlan_pcp_mask=False,
                            test_condition=5)

class VlanWildIdExactPcpOutrange0(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID and Exact PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_NONE  PCP: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    Test on one pair of ports
    - EXPECTATIONS
     - FLOW_MOD_FAILED error
     - Pkt NOT to be forwarded
    """
    def runTest(self):
        vlan_outrange_tests(self, vlan_id_mask = True, vlan_pcp_mask=False,
                            test_condition=0)

class VlanWildIdExactPcpOutrange1(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID and Exact PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_ANY  PCP: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - FLOW_MOD_FAILED error
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_outrange_tests(self, vlan_id_mask = True, vlan_pcp_mask=False,
                            test_condition=1)

class VlanWildIdExactPcpOutrange2(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID and Exact PCP
    Test conditions:
    - MATCH
     - VID: outrange value  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_outrange_tests(self, vlan_id_mask = True, vlan_pcp_mask=False,
                            test_condition=2)

class VlanWildIdExactPcpOutrange3(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID and Exact PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - FLOW_MOD_FAILED error
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_outrange_tests(self, vlan_id_mask = True, vlan_pcp_mask=False,
                            test_condition=3)

class VlanWildIdExactPcpOutrange4(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID and Exact PCP
    Test conditions:
    - MATCH
     - VID: outrange value  PCP: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - FLOW_MOD_FAILED error
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_outrange_tests(self, vlan_id_mask = True, vlan_pcp_mask=False,
                            test_condition=4)

class VlanExactIdWildPcpNone0(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID and Wildcard PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_NONE  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - VID: N/A  PCP: N/A
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_none_tests(self, vlan_id_mask = False, vlan_pcp_mask=True,
                        test_condition=0)

class VlanExactIdWildPcpNone1(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID and Wildcard PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_NONE  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: unmatch value  PCP: unmatch value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_none_tests(self, vlan_id_mask = False, vlan_pcp_mask=True,
                        test_condition=1)

class VlanExactIdWildPcpNone2(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID and Wildcard PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_NONE  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: unmatch value  PCP: match value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_none_tests(self, vlan_id_mask = False, vlan_pcp_mask=True,
                        test_condition=2)

class VlanExactIdWildPcpAny0(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID and Wildcard PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_ANY  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - VID: N/A  PCP: N/A
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_any_tests(self, vlan_id_mask = False, vlan_pcp_mask=True,
                       test_condition=0)

class VlanExactIdWildPcpAny1(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID and Wildcard PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_ANY  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: unmatch value  PCP: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_any_tests(self, vlan_id_mask = False, vlan_pcp_mask=True,
                       test_condition=1)

class VlanExactIdWildPcpSpecific0(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID and Wildcard PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - VID: N/A  PCP: N/A
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = False, vlan_pcp_mask=True,
                            test_condition=0)

class VlanExactIdWildPcpSpecific1(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID and Wildcard PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: match value  PCP: match value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = False, vlan_pcp_mask=True,
                            test_condition=1)

class VlanExactIdWildPcpSpecific2(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID and Wildcard PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: match value  PCP: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = False, vlan_pcp_mask=True,
                            test_condition=2)

class VlanExactIdWildPcpSpecific3(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID and Wildcard PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: unmatch value  PCP: match value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = False, vlan_pcp_mask=True,
                            test_condition=3)

class VlanExactIdWildPcpSpecific4(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID and Wildcard PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 2
     - VID: match value  PCP: match value
     - Inner VID: unmatch value  PCP: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = False, vlan_pcp_mask=True,
                            test_condition=4)

class VlanExactIdWildPcpSpecific5(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID and Wildcard PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 2
     - VID: unmatch value  PCP: ummatch value
     - Inner VID: match value  PCP: match value
    - EXPECTATIONS
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = False, vlan_pcp_mask=True,
                            test_condition=5)

class VlanExactIdWildPcpOutrange0(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID and Wildcard PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_NONE  PCP: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_outrange_tests(self, vlan_id_mask = False, vlan_pcp_mask=True,
                            test_condition=0)

class VlanExactIdWildPcpOutrange1(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID and Wildcard PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_ANY  PCP: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_outrange_tests(self, vlan_id_mask = False, vlan_pcp_mask=True,
                            test_condition=1)

class VlanExactIdWildPcpOutrange2(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID and Wildcard PCP
    Test conditions:
    - MATCH
     - VID: outrange value  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - FLOW_MOD_FAILED error
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_outrange_tests(self, vlan_id_mask = False, vlan_pcp_mask=True,
                            test_condition=2)

class VlanExactIdWildPcpOutrange3(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID and Wildcard PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_outrange_tests(self, vlan_id_mask = False, vlan_pcp_mask=True,
                            test_condition=3)

class VlanExactIdWildPcpOutrange4(pktact.BaseMatchCase):
    """
    VLAN match test with Exact VID and Wildcard PCP
    Test conditions:
    - MATCH
     - VID: outrange value  PCP: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - FLOW_MOD_FAILED error
     - Pkt NOT to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_outrange_tests(self, vlan_id_mask = False, vlan_pcp_mask=True,
                            test_condition=4)

class VlanWildNone0(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID, PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_NONE  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - VID: N/A  PCP: N/A
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_none_tests(self, vlan_id_mask = True, vlan_pcp_mask=True,
                        test_condition=0)

class VlanWildNone1(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID, PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_NONE  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: unmatch value  PCP: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_none_tests(self, vlan_id_mask = True, vlan_pcp_mask=True,
                        test_condition=1)

class VlanWildNone2(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID, PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_NONE  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: unmatch value  PCP: match value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_none_tests(self, vlan_id_mask = True, vlan_pcp_mask=True,
                        test_condition=2)

class VlanWildAny0(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID, PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_ANY  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - VID: N/A  PCP: N/A
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_any_tests(self, vlan_id_mask = True, vlan_pcp_mask=True,
                       test_condition=0)

class VlanWildAny1(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID, PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_ANY  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: unmatch value  PCP: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_any_tests(self, vlan_id_mask = True, vlan_pcp_mask=True,
                       test_condition=1)

class VlanWildSpecific0(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID, PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 0
     - VID: N/A  PCP: N/A
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = True, vlan_pcp_mask=True,
                            test_condition=0)

class VlanWildSpecific1(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID, PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: match value  PCP: match value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = True, vlan_pcp_mask=True,
                            test_condition=1)

class VlanWildSpecific2(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID, PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: match value  PCP: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = True, vlan_pcp_mask=True,
                            test_condition=2)

class VlanWildSpecific3(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID, PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
     - VID: unmatch value  PCP: match value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = True, vlan_pcp_mask=True,
                            test_condition=3)

class VlanWildSpecific4(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID, PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 2
     - VID: match value  PCP: match value
     - Inner VID: unmatch value  PCP: unmatch value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = True, vlan_pcp_mask=True,
                            test_condition=4)

class VlanWildSpecific5(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID, PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 2
     - VID: unmatch value  PCP: ummatch value
     - Inner VID: match value  PCP: match value
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_specific_tests(self, vlan_id_mask = True, vlan_pcp_mask=True,
                            test_condition=5)

class VlanWildOutrange0(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID, PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_NONE  PCP: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_outrange_tests(self, vlan_id_mask = True, vlan_pcp_mask=True,
                            test_condition=0)

class VlanWildOutrange1(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID, PCP
    Test conditions:
    - MATCH
     - VID: OFPVID_ANY  PCP: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_outrange_tests(self, vlan_id_mask = True, vlan_pcp_mask=True,
                            test_condition=1)

class VlanWildOutrange2(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID, PCP
    Test conditions:
    - MATCH
     - VID: outrange value  PCP: SPECIFIC
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_outrange_tests(self, vlan_id_mask = True, vlan_pcp_mask=True,
                            test_condition=2)

class VlanWildOutrange3(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID, PCP
    Test conditions:
    - MATCH
     - VID: SPECIFIC  PCP: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_outrange_tests(self, vlan_id_mask = True, vlan_pcp_mask=True,
                            test_condition=3)

class VlanWildOutrange4(pktact.BaseMatchCase):
    """
    VLAN match test with Wildcard VID, PCP
    Test conditions:
    - MATCH
     - VID: outrange value  PCP: outrange value
    - SENDING PKT
     - NUM OF TAGS: 1
    - EXPECTATIONS
     - Pkt to be forwarded
    Test on one pair of ports
    """
    def runTest(self):
        vlan_outrange_tests(self, vlan_id_mask = True, vlan_pcp_mask=True,
                            test_condition=4)


def vlan_none_tests(parent, vlan_id_mask=False, vlan_pcp_mask=False,
                    test_condition=0):
    """
    Vlan match test with OFPVID_NONE

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param vlan_id_mask If True, VLAN ID is wildcarded
    @param vlan_pcp_mask If True, VLAN PCP is wildcarded
    @param test_condition The value between 0 and 2
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

    if test_condition == 0:
        vid = -1
        pcp_match = pcp
        match_exp = True

    elif test_condition == 1:
        vid = random.randint(0, 4095)
        pcp_match = 7 - pcp # unmatching value
        if (vlan_id_mask == True) and (vlan_pcp_mask == True):
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

    else:
        return

    if match_exp == True:
        exp_vid = vid
        exp_pcp = pcp
    else:
        exp_vid = 0 #NOT_EXPECTED
        exp_pcp = 0 #NOT_EXPECTED

    testutils.flow_match_test_vlan(parent, pa_port_map,
                dl_vlan=vid,
                dl_vlan_pcp=pcp,
                dl_vlan_int=-1,
                dl_vlan_pcp_int=0,
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

def vlan_any_tests(parent, vlan_id_mask=False, vlan_pcp_mask=False,
                   test_condition=0):
    """
    Vlan match test with OFPVID_ANY

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param vlan_id_mask If True, VLAN ID is wildcarded
    @param vlan_pcp_mask If True, VLAN PCP is wildcarded
    @param test_condition The value between 0 and 1
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
        if (vlan_id_mask == True) and (vlan_pcp_mask == False):
            match_exp = False
        else:
            match_exp = True
        match_exp = True

    else:
        return

    if match_exp == True:
        exp_vid = vid
        exp_pcp = pcp
    else:
        exp_vid = 0 #NOT_EXPECTED
        exp_pcp = 0 #NOT_EXPECTED

    testutils.flow_match_test_vlan(parent, pa_port_map,
                dl_vlan=vid,
                dl_vlan_pcp=pcp,
                dl_vlan_int=-1,
                dl_vlan_pcp_int=0,
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

def vlan_specific_tests(parent, vlan_id_mask=False, vlan_pcp_mask=False,
                        test_condition=0):
    """
    Vlan match test with specific matching value

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param vlan_id_mask If True, VLAN ID is wildcarded
    @param vlan_pcp_mask If True, VLAN PCP is wildcarded
    @param test_condition The value between 0 and 5
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

    vid_int = -1
    pcp_int = 0

    if test_condition == 0:
        vid = -1
        pcp = 0
        if vlan_id_mask == True:
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
        vid_int = vid_match + 1
        pcp_int = pcp_match + 1
        match_exp = True

    elif test_condition == 5:
        vid = vid_match + 1
        pcp = pcp_match + 1
        vid_int = vid_match
        pcp_int = pcp_match
        if vlan_id_mask == True:
            match_exp = True
        else:
            match_exp = False

    else:
        return

    if match_exp == True:
        exp_vid = vid
        exp_pcp = pcp
    else:
        exp_vid = 0 #NOT_EXPECTED
        exp_pcp = 0 #NOT_EXPECTED

    testutils.flow_match_test_vlan(parent, pa_port_map,
                dl_vlan=vid,
                dl_vlan_pcp=pcp,
                dl_vlan_int=vid_int,
                dl_vlan_pcp_int=pcp_int,
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

def vlan_outrange_tests(parent, vlan_id_mask=False, vlan_pcp_mask=False,
                        test_condition=0):
    """
    Vlan match test with out-of-range matching value, expecting an error

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param vlan_id_mask If True, VLAN ID is wildcarded
    @param vlan_pcp_mask If True, VLAN PCP is wildcarded
    @param test_condition The value between 0 and 4
    """
    wildcards = 0
    if vlan_id_mask == True:
        wildcards = ofp.OFPFW_DL_VLAN
    if vlan_pcp_mask == True:
        wildcards = wildcards + ofp.OFPFW_DL_VLAN_PCP

    vid = random.randint(0, 4095)
    pcp = random.randint(0, 7)
    exp_vid = vid
    exp_pcp = vid

    if test_condition == 0:
        vid_match = ofp.OFPVID_NONE
        pcp_match = pcp + 8  #out of range
        if vlan_pcp_mask == True:
            match_exp = True
            exp_msg = ofp.OFPT_FLOW_REMOVED
            exp_msg_type = 0 #NOT EXPECTED
            exp_msg_code = 0 #NOT EXPECTED
        else:
            match_exp = False
            if vlan_id_mask == True:
                exp_msg = ofp.OFPT_ERROR
                exp_msg_type = ofp.OFPET_FLOW_MOD_FAILED
                exp_msg_code = ofp.OFPFMFC_BAD_MATCH
            else:
                exp_msg = ofp.OFPT_FLOW_REMOVED
                exp_msg_type = 0 #NOT EXPECTED
                exp_msg_code = 0 #NOT EXPECTED

    elif test_condition == 1:
        vid_match = ofp.OFPVID_ANY
        pcp_match = pcp + 8  #out of range
        if (vlan_id_mask == True) and (vlan_pcp_mask == False):
            match_exp = False
            exp_msg = ofp.OFPT_ERROR
            exp_msg_type = ofp.OFPET_FLOW_MOD_FAILED
            exp_msg_code = ofp.OFPFMFC_BAD_MATCH
        else:
            match_exp = True
            exp_msg = ofp.OFPT_FLOW_REMOVED
            exp_msg_type = 0 #NOT EXPECTED
            exp_msg_code = 0 #NOT EXPECTED

    elif test_condition == 2:
        vid_match = vid + 4096  #out of range
        pcp_match = pcp
        if vlan_id_mask == True:
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
        vid_match = vid
        pcp_match = pcp + 8  #out of range
        if vlan_pcp_mask == True:
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
        vid_match = vid + 4096  #out of range
        pcp_match = pcp + 8  #out of range
        if (vlan_id_mask == True) and (vlan_pcp_mask == True):
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
        exp_vid = vid
        exp_pcp = pcp
    else:
        exp_vid = 0 #NOT EXPECTED
        exp_pcp = 0 #NOT EXPECTED

    testutils.flow_match_test_vlan(parent, pa_port_map,
                dl_vlan=vid,
                dl_vlan_pcp=pcp,
                dl_vlan_int=-1,
                dl_vlan_pcp_int=0,
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
    print "Please run through oft script:  ./oft --test-spec=vlanmatch"
