"""
Test cases for testing DL/NW bit mask features

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

BYTE_LEN = 8
NW_ALEN = 32

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


class ExactDlSrcMask(pktact.BaseMatchCase):
    """
    Execute exact match test with DL source address bitmask
    for one port pair

    Generate a packet
    Generate and install a matching flow without wildcard mask,
    but with DL source address bitmask
    (Shift the masking position bit by bit)
    Add an action to forward to a port
    Send the packet to the port
    Verify the packet is received at the other port
    """
    def __init__(self):
        pktact.BaseMatchCase.__init__(self)
        self.dl_nw_mask = {
            "dl_src" : [0, 0, 0, 0, 0, 0],
            "dl_dst" : [0, 0, 0, 0, 0, 0],
            "nw_src" : 0,
            "nw_dst" : 0
            }

    def runTest(self):
        #@todo More test methods should be added
        for idx in range(ofp.OFP_ETH_ALEN):
            dl_mask=[0, 0, 0, 0, 0, 0]
            for bit_pos in range(BYTE_LEN):
                dl_mask[idx] = 1 << bit_pos
                self.dl_nw_mask['dl_src'] = dl_mask
                bitmask_test(self, pa_port_map,
                             mask=self.dl_nw_mask, max_test=1)
                self.dl_nw_mask['dl_src'] = [0, 0, 0, 0, 0, 0]

class ExactDlDstMask(ExactDlSrcMask):
    """
    Execute exact match test with DL destination address bitmask
    for one port pair

    Generate a packet
    Generate and install a matching flow without wildcard mask,
    but with DL destination address bitmask
    (Shift the masking position bit by bit)
    Add an action to forward to a port
    Send the packet to the port
    Verify the packet is received at the other port
    """
    def runTest(self):
        #@todo More test methods should be added
        for idx in range(ofp.OFP_ETH_ALEN):
            dl_mask=[0, 0, 0, 0, 0, 0]
            for bit_pos in range(BYTE_LEN):
                dl_mask[idx] = 1 << bit_pos
                self.dl_nw_mask['dl_dst'] = dl_mask
                bitmask_test(self, pa_port_map,
                             mask=self.dl_nw_mask, max_test=1)
                self.dl_nw_mask['dl_dst'] = [0, 0, 0, 0, 0, 0]

class ExactNwSrcSftMask(ExactDlSrcMask):
    """
    Execute exact match test with NW source address bitmask
    for one port pair

    Generate a packet
    Generate and install a matching flow without wildcard mask,
    but with NW source address bitmask
    (Shift the masking position bit by bit)
    Add an action to forward to a port
    Send the packet to the port
    Verify the packet is received at the other port
    """
    def runTest(self):
        #@todo More test methods should be added
        for bit_pos in range(NW_ALEN):
            self.dl_nw_mask['nw_src'] = 1 << bit_pos
            bitmask_test(self, pa_port_map,
                         mask=self.dl_nw_mask, max_test=1)
            self.dl_nw_mask['nw_src'] = 0

class ExactNwSrcNetMask(ExactDlSrcMask):
    """
    Execute exact match test with NW source address bitmask
    for one port pair

    Generate a packet
    Generate and install a matching flow without wildcard mask,
    but with NW source address bitmask
    (Increase the masking positions as a netmask)
    Add an action to forward to a port
    Send the packet to the port
    Verify the packet is received at the other port
    """
    def runTest(self):
        #@todo More test methods should be added
        for bit_pos in range(NW_ALEN):
            self.dl_nw_mask['nw_src'] = (self.dl_nw_mask['nw_src']
                                         + (1 << bit_pos))
            bitmask_test(self, pa_port_map,
                         mask=self.dl_nw_mask, max_test=1)
        self.dl_nw_mask['nw_src'] = 0

class ExactNwDstSftMask(ExactDlSrcMask):
    """
    Execute exact match test with NW destination address bitmask
    for one port pair

    Generate a packet
    Generate and install a matching flow without wildcard mask,
    but with NW destination address bitmask
    (Shift the masking position bit by bit)
    Add an action to forward to a port
    Send the packet to the port
    Verify the packet is received at the other port
    """
    def runTest(self):
        #@todo More test methods should be added
        for bit_pos in range(NW_ALEN):
            self.dl_nw_mask['nw_dst'] = 1 << bit_pos
            bitmask_test(self, pa_port_map,
                         mask=self.dl_nw_mask, max_test=1)
            self.dl_nw_mask['nw_dst'] = 0

class ExactNwDstNetMask(ExactDlSrcMask):
    """
    Execute exact match test with NW destination address bitmask
    for one port pair

    Generate a packet
    Generate and install a matching flow without wildcard mask,
    but with NW destination address bitmask
    (Increase the masking positions as a netmask)
    Add an action to forward to a port
    Send the packet to the port
    Verify the packet is received at the other port
    """
    def runTest(self):
        #@todo More test methods should be added
        for bit_pos in range(NW_ALEN):
            self.dl_nw_mask['nw_dst'] = (self.dl_nw_mask['nw_dst']
                                         + (1 << bit_pos))
            bitmask_test(self, pa_port_map,
                         mask=self.dl_nw_mask, max_test=1)
        self.dl_nw_mask['nw_dst'] = 0

class WildcardDlSrcMask(ExactDlSrcMask):
    """
    Execute wildcard match test with DL source address bitmask
    for one port pair

    Generate a packet
    Generate and install a matching flow with wildcard mask
    and with DL source address bitmask
    (Shift the masking position bit by bit)
    Add an action to forward to a port
    Send the packet to the port
    Verify the packet is received at the other port
    """
    def runTest(self):
        #@todo More test methods should be added
        for wc in WILDCARD_VALUES:
            for idx in range(ofp.OFP_ETH_ALEN):
                dl_mask=[0, 0, 0, 0, 0, 0]
                for bit_pos in range(BYTE_LEN):
                    dl_mask[idx] = 1 << bit_pos
                    self.dl_nw_mask['dl_src'] = dl_mask
                    bitmask_test(self, pa_port_map,
                                 mask=self.dl_nw_mask,
                                 wildcards=wc, max_test=1)
                    self.dl_nw_mask['dl_src'] = [0, 0, 0, 0, 0, 0]

class WildcardDlDstMask(ExactDlSrcMask):
    """
    Execute wildcard matching with DL destination address bitmask
    for one port pair

    Generate a packet
    Generate and install a matching flow with wildcard mask,
    and with DL destination address bitmask
    (Shift the masking position bit by bit)
    Add an action to forward to a port
    Send the packet to the port
    Verify the packet is received at the other port
    """
    def runTest(self):
        #@todo More test methods should be added
        for wc in WILDCARD_VALUES:
            for idx in range(ofp.OFP_ETH_ALEN):
                dl_mask=[0, 0, 0, 0, 0, 0]
                for bit_pos in range(BYTE_LEN):
                    dl_mask[idx] = 1 << bit_pos
                    self.dl_nw_mask['dl_dst'] = dl_mask
                    bitmask_test(self, pa_port_map,
                                 mask=self.dl_nw_mask,
                                 wildcards=wc, max_test=1)
                    self.dl_nw_mask['dl_dst'] = [0, 0, 0, 0, 0, 0]

class WildcardNwSrcSftMask(ExactDlSrcMask):
    """
    Execute wildcard matching with NW source address bitmask
    for one port pair

    Generate a packet
    Generate and install a matching flow with wildcard mask,
    and with NW source address bitmask
    (Shift the masking position bit by bit)
    Add an action to forward to a port
    Send the packet to the port
    Verify the packet is received at the other port
    """
    def runTest(self):
        #@todo More test methods should be added
        for wc in WILDCARD_VALUES:
            for bit_pos in range(NW_ALEN):
                self.dl_nw_mask['nw_src'] = 1 << bit_pos
                bitmask_test(self, pa_port_map,
                             mask=self.dl_nw_mask,
                             wildcards=wc, max_test=1)
                self.dl_nw_mask['nw_src'] = 0

class WildcardNwSrcNetMask(ExactDlSrcMask):
    """
    Execute wildcard matching with NW source address bitmask
    for one port pair

    Generate a packet
    Generate and install a matching flow with wildcard mask,
    and with NW source address bitmask
    (Increase the masking positions as a netmask)
    Add an action to forward to a port
    Send the packet to the port
    Verify the packet is received at the other port
    """
    def runTest(self):
        #@todo More test methods should be added
        for wc in WILDCARD_VALUES:
            for bit_pos in range(NW_ALEN):
                self.dl_nw_mask['nw_src'] = (self.dl_nw_mask['nw_src']
                                             + (1 << bit_pos))
                bitmask_test(self, pa_port_map,
                             mask=self.dl_nw_mask,
                             wildcards=wc, max_test=1)
            self.dl_nw_mask['nw_src'] = 0

class WildcardNwDstSftMask(ExactDlSrcMask):
    """
    Execute wildcard match test with NW destination address bitmask
    for one port pair

    Generate a packet
    Generate and install a matching flow with wildcard mask,
    and with NW destination address bitmask
    (Shift the masking position bit by bit)
    Add an action to forward to a port
    Send the packet to the port
    Verify the packet is received at the other port
    """
    def runTest(self):
        #@todo More test methods should be added
        for wc in WILDCARD_VALUES:
            for bit_pos in range(NW_ALEN):
                self.dl_nw_mask['nw_dst'] = 1 << bit_pos
                bitmask_test(self, pa_port_map,
                             mask=self.dl_nw_mask,
                             wildcards=wc, max_test=1)
                self.dl_nw_mask['nw_dst'] = 0

class WildcardNwDstNetMask(ExactDlSrcMask):
    """
    Execute wildcard match test with NW destination address bitmask
    for one port pair

    Generate a packet
    Generate and install a matching flow with wildcard mask,
    and with NW destination address bitmask
    (Increase the masking positions as a netmask)
    Add an action to forward to a port
    Send the packet to the port
    Verify the packet is received at the other port
    """
    def runTest(self):
        #@todo More test methods should be added
        for wc in WILDCARD_VALUES:
            for bit_pos in range(NW_ALEN):
                self.dl_nw_mask['nw_dst'] = (self.dl_nw_mask['nw_dst']
                                             + (1 << bit_pos))
                bitmask_test(self, pa_port_map,
                             mask=self.dl_nw_mask,
                             wildcards=wc, max_test=1)
            self.dl_nw_mask['nw_dst'] = 0


def bitmask_test(parent, port_map, wildcards=0,
                 mask=None, dl_vlan=-1, pkt=None,
                 exp_pkt=None, action_list=None, check_expire=False,
                 max_test=0):
    """
    Run flow_match_test with DL/NW bitmasks

    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param pkt If not None, use this packet for ingress
    @param wildcards For flow match entry
    @param mask DL/NW address bit masks as a dictionary. If set, it is tested
    against the corresponding match fields with the opposite values
    @param dl_vlan If not -1, and pkt is None, create a pkt w/ VLAN tag
    @param exp_pkt If not None, use this as the expected output pkt; els use pkt
    @param action_list Additional actions to add to flow mod
    @param check_expire Check for flow expiration message
    @param max_test If > 0 no more than this number of tests are executed.
    """
    pkt = testutils.simple_tcp_packet(dl_vlan_enable=(dl_vlan >= 0),
                                      dl_vlan=dl_vlan)
    match = parse.packet_to_flow_match(pkt)
    parent.assertTrue(match is not None, "Flow match from pkt failed")
    if mask is not None:
        match.dl_src_mask = mask['dl_src']
        match.dl_dst_mask = mask['dl_dst']
        match.nw_src_mask = mask['nw_src']
        match.nw_dst_mask = mask['nw_dst']
        #Set unmatching values on corresponding match fields
        for i in range(ofp.OFP_ETH_ALEN):
            match.dl_src[i] = match.dl_src[i] ^ match.dl_src_mask[i]
            match.dl_dst[i] = match.dl_dst[i] ^ match.dl_dst_mask[i]
        match.nw_src = match.nw_src ^ match.nw_src_mask
        match.nw_dst = match.nw_dst ^ match.nw_dst_mask

    testutils.flow_match_test(parent, pa_port_map,
                              pkt=pkt, match=match,
                              wildcards=wildcards, max_test=1)

if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test-spec=dlnw_mask"
