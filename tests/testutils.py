
import sys
import logging
#import types

#import oftest.controller as controller
from oftest import cstruct as ofp
import oftest.message as message
#import oftest.dataplane as dataplane
import oftest.action as action
import oftest.parse as parse
from oftest import instruction
from oftest.packet import Packet

global skipped_test_count
skipped_test_count = 0

# Some useful defines
IP_ETHERTYPE = 0x800
ETHERTYPE_VLAN = 0x8100
ETHERTYPE_MPLS = 0x8847
TCP_PROTOCOL = 0x6
UDP_PROTOCOL = 0x11

def clear_switch(parent, port_list, logger):
    """
    Clear the switch configuration

    @param parent Object implementing controller and assert equal
    @param logger Logging object
    """
    for port in port_list:
        clear_port_config(parent, port, logger)
    delete_all_flows(parent.controller, logger)

def initialize_table_config(ctrl, logger):
    """
    Initialize all table configs to default setting ("CONTROLLER")
    @param ctrl The controller object for the test
    """
    logger.info("Initializing all table configs")
    request = message.table_mod()  
    request.config = ofp.OFPTC_TABLE_MISS_CONTROLLER
    rv = 0
    for table_id in [0, 1, 2, 3, 4, 5, 6, 7]:
        request.table_id = table_id
        rv |= ctrl.message_send(request)
    return rv

def delete_all_flows(ctrl, logger):
    """
    Delete all flows on the switch
    @param ctrl The controller object for the test
    @param logger Logging object
    """

    logger.info("Deleting all flows")
    #DEFAULT_TABLE_COUNT = 4
    return delete_all_flows_one_table(ctrl, logger, table_id=0xff)

def delete_all_flows_one_table(ctrl, logger, table_id=0):
    """
    Delete all flows on a table
    @param ctrl The controller object for the test
    @param logger Logging object
    @param table_id Table ID
    """
    logger.info("Deleting all flows on table ID: " + str(table_id))
    msg = message.flow_mod()
    msg.match.wildcards = ofp.OFPFW_ALL
    msg.match.dl_src_mask= [255,255,255,255,255,255]
    msg.match.dl_dst_mask= [255,255,255,255,255,255]
    msg.match.nw_src_mask = 0xffffffff
    msg.match.nw_dst_mask = 0xffffffff
    msg.out_port = ofp.OFPP_ANY  # @todo CHECKME 
    msg.command = ofp.OFPFC_DELETE
    msg.buffer_id = 0xffffffff
    msg.table_id = table_id
    logger.debug(msg.show())

    return ctrl.message_send(msg)

def clear_port_config(parent, port, logger):
    """
    Clear the port configuration 

    @param parent Object implementing controller and assert equal
    @param logger Logging object
    """
    rv = port_config_set(parent.controller, port,
                         0, 0, logger)
    parent.assertEqual(rv, 0, "Failed to reset port config")

def simple_tcp_packet(**args):
    """
    Return a simple dataplane TCP packet

    Supports a few parameters:
    @param len Length of packet in bytes w/o CRC
    @param dl_dst Destinatino MAC
    @param dl_src Source MAC
    @param dl_vlan_enable True if the packet is with vlan, False otherwise
    @param dl_vlan_type Ether type for VLAN
    @param dl_vlan VLAN ID
    @param dl_vlan_pcp VLAN priority
    @param ip_src IP source
    @param ip_dst IP destination
    @param ip_tos IP ToS
    @param tcp_dport TCP destination port
    @param tcp_sport TCP source port

    Generates a simple TCP request.  Users
    shouldn't assume anything about this packet other than that
    it is a valid ethernet/IP/TCP frame.
    """
    # Note Dot1Q.id is really CFI

    return Packet().simple_tcp_packet(**args)

def simple_icmp_packet(*args):
    """
    Return a simple ICMP packet

    Supports a few parameters:
    @param len Length of packet in bytes w/o CRC
    @param dl_dst Destinatino MAC
    @param dl_src Source MAC
    @param dl_vlan_enable True if the packet is with vlan, False otherwise
    @param dl_vlan_type Ether type for VLAN
    @param dl_vlan VLAN ID
    @param dl_vlan_pcp VLAN priority
    @param ip_src IP source
    @param ip_dst IP destination
    @param ip_tos IP ToS
    @param icmp_type ICMP type
    @param icmp_code ICMP code

    Generates a simple ICMP ECHO REQUEST.  Users
    shouldn't assume anything about this packet other than that
    it is a valid ethernet/ICMP frame.
    """

    return Packet().simple_icmp_packet(*args)

def do_barrier(ctrl):
    b = message.barrier_request()
    ctrl.transact(b)


def port_config_get(controller, port_no, logger):
    """
    Get a port's configuration

    Gets the switch feature configuration and grabs one port's
    configuration

    @returns (hwaddr, config, advert) The hwaddress, configuration and
    advertised values
    """
    request = message.features_request()
    reply, _ = controller.transact(request, timeout=2)
    if reply is None:
        logger.warn("Get feature request failed")
        return None, None, None
    logger.debug(reply.show())
    for idx in range(len(reply.ports)):
        if reply.ports[idx].port_no == port_no:
            return (reply.ports[idx].hw_addr, reply.ports[idx].config,
                    reply.ports[idx].advertised)
    
    logger.warn("Did not find port number for port config")
    return None, None, None

def port_config_set(controller, port_no, config, mask, logger):
    """
    Set the port configuration according the given parameters

    Gets the switch feature configuration and updates one port's
    configuration value according to config and mask
    """
    logger.info("Setting port " + str(port_no) + " to config " + str(config))
    request = message.features_request()
    reply, _ = controller.transact(request, timeout=2)
    if reply is None:
        return -1
    logger.debug(reply.show())
    for idx in range(len(reply.ports)):
        if reply.ports[idx].port_no == port_no:
            break
    if idx >= len(reply.ports):
        return -1
    mod = message.port_mod()
    mod.port_no = port_no
    mod.hw_addr = reply.ports[idx].hw_addr
    mod.config = config
    mod.mask = mask
    mod.advertise = reply.ports[idx].advertised
    rv = controller.message_send(mod)
    return rv

def receive_pkt_check(dataplane, pkt, yes_ports, no_ports, assert_if, logger):
    """
    Check for proper receive packets across all ports
    @param dataplane The dataplane object
    @param pkt Expected packet; may be None if yes_ports is empty
    @param yes_ports Set or list of ports that should recieve packet
    @param no_ports Set or list of ports that should not receive packet
    @param assert_if Object that implements assertXXX
    """
    for ofport in yes_ports:
        logger.debug("Checking for pkt on port " + str(ofport))
        (_, rcv_pkt, _) = dataplane.poll(
            port_number=ofport, timeout=1)
        assert_if.assertTrue(rcv_pkt is not None, 
                             "Did not receive pkt on " + str(ofport))
        assert_if.assertEqual(str(pkt), str(rcv_pkt),
                              "Response packet does not match send packet " +
                              "on port " + str(ofport))

    for ofport in no_ports:
        logger.debug("Negative check for pkt on port " + str(ofport))
        (_, rcv_pkt, _) = dataplane.poll(
            port_number=ofport, timeout=1)
        assert_if.assertTrue(rcv_pkt is None, 
                             "Unexpected pkt on port " + str(ofport))


def receive_pkt_verify(parent, egr_port, exp_pkt):
    """
    Receive a packet and verify it matches an expected value

    parent must implement dataplane, assertTrue and assertEqual
    """
    (rcv_port, rcv_pkt, _) = parent.dataplane.poll(port_number=egr_port,
                                                          timeout=1)
    if rcv_pkt is None:
        parent.logger.error("ERROR: No packet received from " + str(egr_port))

    parent.assertTrue(rcv_pkt is not None,
                      "Did not receive packet port " + str(egr_port))
    parent.logger.debug("Packet len " + str(len(rcv_pkt)) + " in on " + 
                    str(rcv_port))

    if str(exp_pkt) != str(rcv_pkt):
        parent.logger.error("ERROR: Packet match failed.")
        parent.logger.debug("Expected len " + str(len(exp_pkt)) + ": "
                        + str(exp_pkt).encode('hex'))
        parent.logger.debug("Received len " + str(len(rcv_pkt)) + ": "
                        + str(rcv_pkt).encode('hex'))
    parent.assertEqual(str(exp_pkt), str(rcv_pkt),
                       "Packet match error on port " + str(egr_port))
    
def match_verify(parent, req_match, res_match):
    """
    Verify flow matches agree; if they disagree, report where

    parent must implement assertEqual
    Use str() to ensure content is compared and not pointers
    """

    parent.assertEqual(req_match.wildcards, res_match.wildcards,
                       'Match failed: wildcards: ' + hex(req_match.wildcards) +
                       " != " + hex(res_match.wildcards))
    parent.assertEqual(req_match.in_port, res_match.in_port,
                       'Match failed: in_port: ' + str(req_match.in_port) +
                       " != " + str(res_match.in_port))
    parent.assertEqual(str(req_match.dl_src), str(res_match.dl_src),
                       'Match failed: dl_src: ' + str(req_match.dl_src) +
                       " != " + str(res_match.dl_src))
    parent.assertEqual(str(req_match.dl_dst), str(res_match.dl_dst),
                       'Match failed: dl_dst: ' + str(req_match.dl_dst) +
                       " != " + str(res_match.dl_dst))
    parent.assertEqual(req_match.dl_vlan, res_match.dl_vlan,
                       'Match failed: dl_vlan: ' + str(req_match.dl_vlan) +
                       " != " + str(res_match.dl_vlan))
    parent.assertEqual(req_match.dl_vlan_pcp, res_match.dl_vlan_pcp,
                       'Match failed: dl_vlan_pcp: ' + 
                       str(req_match.dl_vlan_pcp) + " != " + 
                       str(res_match.dl_vlan_pcp))
    parent.assertEqual(req_match.dl_type, res_match.dl_type,
                       'Match failed: dl_type: ' + str(req_match.dl_type) +
                       " != " + str(res_match.dl_type))

    if (not(req_match.wildcards & ofp.OFPFW_DL_TYPE)
        and (req_match.dl_type == IP_ETHERTYPE)):
        parent.assertEqual(req_match.nw_tos, res_match.nw_tos,
                           'Match failed: nw_tos: ' + str(req_match.nw_tos) +
                           " != " + str(res_match.nw_tos))
        parent.assertEqual(req_match.nw_proto, res_match.nw_proto,
                           'Match failed: nw_proto: ' + str(req_match.nw_proto) +
                           " != " + str(res_match.nw_proto))
        parent.assertEqual(req_match.nw_src, res_match.nw_src,
                           'Match failed: nw_src: ' + str(req_match.nw_src) +
                           " != " + str(res_match.nw_src))
        parent.assertEqual(req_match.nw_dst, res_match.nw_dst,
                           'Match failed: nw_dst: ' + str(req_match.nw_dst) +
                           " != " + str(res_match.nw_dst))

        if (not(req_match.wildcards & ofp.OFPFW_NW_PROTO)
            and ((req_match.nw_proto == TCP_PROTOCOL)
                 or (req_match.nw_proto == UDP_PROTOCOL))):
            parent.assertEqual(req_match.tp_src, res_match.tp_src,
                               'Match failed: tp_src: ' + 
                               str(req_match.tp_src) +
                               " != " + str(res_match.tp_src))
            parent.assertEqual(req_match.tp_dst, res_match.tp_dst,
                               'Match failed: tp_dst: ' + 
                               str(req_match.tp_dst) +
                               " != " + str(res_match.tp_dst))

def flow_removed_verify(parent, request=None, pkt_count=-1, byte_count=-1):
    """
    Receive a flow removed msg and verify it matches expected

    @params parent Must implement controller, assertEqual
    @param pkt_count If >= 0, verify packet count
    @param byte_count If >= 0, verify byte count
    """
    (response, _) = parent.controller.poll(ofp.OFPT_FLOW_REMOVED, 2)
    parent.assertTrue(response is not None, 'No flow removed message received')

    if request is None:
        return

    parent.assertEqual(request.cookie, response.cookie,
                       "Flow removed cookie error: " +
                       hex(request.cookie) + " != " + hex(response.cookie))

    req_match = request.match
    res_match = response.match
    verifyMatchField(req_match, res_match)

    if (req_match.wildcards != 0):
        parent.assertEqual(request.priority, response.priority,
                           'Flow remove prio mismatch: ' + 
                           str(request.priority) + " != " + 
                           str(response.priority))
        parent.assertEqual(response.reason, ofp.OFPRR_HARD_TIMEOUT,
                           'Flow remove reason is not HARD TIMEOUT:' +
                           str(response.reason))
        if pkt_count >= 0:
            parent.assertEqual(response.packet_count, pkt_count,
                               'Flow removed failed, packet count: ' + 
                               str(response.packet_count) + " != " +
                               str(pkt_count))
        if byte_count >= 0:
            parent.assertEqual(response.byte_count, byte_count,
                               'Flow removed failed, byte count: ' + 
                               str(response.byte_count) + " != " + 
                               str(byte_count))
def flow_msg_create(parent, pkt, ing_port=0, instruction_list=None, 
                    action_list=None, match=None, wildcards=0, egr_port=None, 
                    egr_queue=None, table_id=0, check_expire=False):
    """
    Multi-purpose flow_mod creation utility

    Match on packet with given wildcards.  
    See flow_match_test for other parameter descriptoins
   
    if egr_queue is set
             append an out_queue action to egr_queue to the actions_list
    else if egr_port is set:  
             append an output action to egr_port to the actions_list
    if the instruction_list is empty, 
        append an APPLY instruction to it
    Add the action_list to the first write or apply instruction
    
    @param egr_queue if not None, make the output an enqueue action
    @param table_id Table ID for writing a flow_mod
    """

    if match is None:
        match = parse.packet_to_flow_match(pkt)
    parent.assertTrue(match is not None, "Flow match from pkt failed")
    match.wildcards = wildcards & 0xfffffffff # mask out anything out of range
    match.in_port = ing_port

    request = message.flow_mod()
    request.match = match
    request.buffer_id = 0xffffffff
    request.table_id = table_id
    if check_expire:
        request.flags |= ofp.OFPFF_SEND_FLOW_REM
        request.hard_timeout = 1    
    
    if action_list is None:
        action_list = []
    if instruction_list is None:
        instruction_list = []
    
    # Set up output/enqueue action if directed
    if egr_queue is not None:
        parent.assertTrue(egr_port is not None, "Egress port not set")
        act = action.action_set_queue()
        act.port = egr_port
        act.queue_id = egr_queue
        action_list.append(act)
    elif egr_port is not None:
        act = action.action_output()
        act.port = egr_port
        action_list.append(act)
        
    inst = None
    if len(instruction_list) == 0: 
        inst = instruction.instruction_apply_actions()
        instruction_list.append(inst)
    else:
        for inst in instruction_list:
            if (inst.type == ofp.OFPIT_WRITE_ACTIONS or
                inst.type == ofp.OFPIT_APPLY_ACTIONS):
                break

    # add all the actions to the last inst
    for act in action_list:
        parent.logger.debug("Adding action " + act.show())
        rv = inst.actions.add(act)
        parent.assertTrue(rv, "Could not add action" + act.show())
    # NOTE that the inst has already been added to the flow_mod

    # add all the instrutions to the flow_mod
    for i in instruction_list: 
        parent.logger.debug("Adding instruction " + inst.show())
        rv = request.instructions.add(i)
        parent.assertTrue(rv, "Could not add instruction " + i.show())

 
    parent.logger.debug(request.show())

    return request

def flow_msg_install(parent, request, clear_table=True):
    """
    Install a flow mod message in the switch

    @param parent Must implement controller, assertEqual, assertTrue
    @param request The request, all set to go
    @param clear_table If true, clear the flow table before installing
    """
    if clear_table:
        parent.logger.debug("Clear flow table")
        if request.table_id:
            table_id = request.table_id
        else:
            table_id = 0
        rc = delete_all_flows_one_table(parent.controller,
                                        parent.logger,
                                        table_id)
        parent.assertEqual(rc, 0, "Failed to delete all flows on table: "
                           + str(table_id))
        do_barrier(parent.controller)

    parent.logger.debug("Insert flow::\n%s" % request.show())
    rv = parent.controller.message_send(request)
    parent.assertTrue(rv != -1, "Error installing flow mod")
    do_barrier(parent.controller)

def error_verify(parent, exp_type, exp_code):
    """
    Receive an error msg and verify if it is as expected

    @param parent Must implement controller, assertEqual
    @param exp_type Expected error type
    @param exp_code Expected error code
    """
    (response, raw) = parent.controller.poll(ofp.OFPT_ERROR, 2)
    parent.assertTrue(response is not None, 'No error message received')

    if (exp_type is None) or (exp_code is None):
        parent.logger.debug("Parametrs are not sufficient")
        return

    parent.assertEqual(exp_type, response.type,
                       'Error message type mismatch: ' +
                       str(exp_type) + " != " +
                       str(response.type))
    parent.assertEqual(exp_code, response.code,
                       'Error message code mismatch: ' +
                       str(exp_code) + " != " +
                       str(response.code))

def flow_match_test_port_pair(parent, ing_port, egr_port, match=None, 
                              wildcards=0, mask=None,
                              dl_vlan=-1, pkt=None, exp_pkt=None,
                              apply_action_list=None, check_expire=False):
    """
    Flow match test on single TCP packet

    Run test with packet through switch from ing_port to egr_port
    See flow_match_test for parameter descriptions
    """

    parent.logger.info("Pkt match test: " + str(ing_port) + " to " + str(egr_port))
    parent.logger.debug("  WC: " + hex(wildcards) + " vlan: " + str(dl_vlan) +
                    " expire: " + str(check_expire))
    if pkt is None:
        pkt = simple_tcp_packet(dl_vlan_enable=(dl_vlan >= 0), dl_vlan=dl_vlan)

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

    request = flow_msg_create(parent, pkt, ing_port=ing_port, 
                              match=match,
                              wildcards=wildcards, egr_port=egr_port,
                              action_list=apply_action_list)

    flow_msg_install(parent, request)

    parent.logger.debug("Send packet: " + str(ing_port) + " to " + str(egr_port))
    parent.dataplane.send(ing_port, str(pkt))

    if exp_pkt is None:
        exp_pkt = pkt
    receive_pkt_verify(parent, egr_port, exp_pkt)

    if check_expire:
        #@todo Not all HW supports both pkt and byte counters
        flow_removed_verify(parent, request, pkt_count=1, byte_count=len(pkt))
def flow_match_test(parent, port_map, match=None, wildcards=0,
                    mask=None, dl_vlan=-1, pkt=None,
                    exp_pkt=None, apply_action_list=None,
                    check_expire=False,  max_test=0):
    """
    Run flow_match_test_port_pair on all port pairs

    @param max_test If > 0 no more than this number of tests are executed.
    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param pkt If not None, use this packet for ingress
    @param match If not None, use this value in flow_mod
    @param wildcards For flow match entry
    @param mask DL/NW address bit masks as a dictionary. If set, it is tested
    against the corresponding match fields with the opposite values
    @param dl_vlan If not -1, and pkt is None, create a pkt w/ VLAN tag
    @param exp_pkt If not None, use this as the expected output pkt; els use pkt
    @param action_list Additional actions to add to flow mod
    @param check_expire Check for flow expiration message
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
            flow_match_test_port_pair(parent, ingress_port, egress_port, 
                                      match=match, wildcards=wildcards,
                                      dl_vlan=dl_vlan, mask=mask,
                                      pkt=pkt, exp_pkt=exp_pkt,
                                      apply_action_list=apply_action_list,
                                      check_expire=check_expire)
            test_count += 1
            if (max_test > 0) and (test_count >= max_test):
                parent.logger.info("Ran " + str(test_count) + " tests; exiting")
                return

def flow_match_test_port_pair_vlan(parent, ing_port, egr_port, wildcards=0,
                                   dl_vlan=-1, dl_vlan_pcp=0,
                                   dl_vlan_type=ETHERTYPE_VLAN,
                                   dl_vlan_int=-1, dl_vlan_pcp_int=0,
                                   vid_match=ofp.OFPVID_NONE, pcp_match=0,
                                   exp_vid=-1, exp_pcp=0,
                                   exp_vlan_type=ETHERTYPE_VLAN,
                                   match_exp=True,
                                   add_tag_exp=False,
                                   exp_msg=ofp.OFPT_FLOW_REMOVED,
                                   exp_msg_type=0, exp_msg_code=0,
                                   pkt=None, exp_pkt=None,
                                   action_list=None, check_expire=False):
    """
    Flow match test for various vlan matching patterns on single TCP packet

    Run test with packet through switch from ing_port to egr_port
    See flow_match_test_vlan for parameter descriptions
    """
    parent.logger.info("Pkt match test: " + str(ing_port) + " to " + str(egr_port))
    parent.logger.debug("  WC: " + hex(wildcards) + " vlan: " + str(dl_vlan) +
                    " expire: " + str(check_expire))
    len = 100
    len_w_vid = len + 4

    if pkt is None:
        if dl_vlan >= 0:
            if dl_vlan_int >= 0:
                pkt = simple_tcp_packet(pktlen=len_w_vid,
                        dl_vlan_enable=True,
                        dl_vlan=dl_vlan_int,
                        dl_vlan_pcp=dl_vlan_pcp_int)
                pkt.push_vlan(dl_vlan_type)
                pkt.set_vlan_vid(dl_vlan)
                pkt.set_vlan_pcp(dl_vlan_pcp)
            else:
                pkt = simple_tcp_packet(pktlen=len_w_vid,
                        dl_vlan_enable=True,
                        dl_vlan_type=dl_vlan_type,
                        dl_vlan=dl_vlan,
                        dl_vlan_pcp=dl_vlan_pcp)
        else:
            pkt = simple_tcp_packet(pktlen=len,
                                    dl_vlan_enable=False)

    if exp_pkt is None:
        if exp_vid >= 0:
            if add_tag_exp:
                if dl_vlan >= 0:
                    if dl_vlan_int >= 0:
                        exp_pkt = simple_tcp_packet(pktlen=len_w_vid,
                                    dl_vlan_enable=True,
                                    dl_vlan=dl_vlan_int,
                                    dl_vlan_pcp=dl_vlan_pcp_int)
                        exp_pkt.push_vlan(dl_vlan_type)
                        exp_pkt.set_vlan_vid(dl_vlan)
                        exp_pkt.set_vlan_pcp(dl_vlan_pcp)
                    else:
                        exp_pkt = simple_tcp_packet(pktlen=len_w_vid,
                                    dl_vlan_enable=True,
                                    dl_vlan_type=dl_vlan_type,
                                    dl_vlan=dl_vlan,
                                    dl_vlan_pcp=dl_vlan_pcp)
                    #Push one more tag in either case
                    exp_pkt.push_vlan(exp_vlan_type)
                    exp_pkt.set_vlan_vid(exp_vid)
                    exp_pkt.set_vlan_pcp(exp_pcp)
                else:
                    exp_pkt = simple_tcp_packet(pktlen=len_w_vid,
                                dl_vlan_enable=True,
                                dl_vlan_type=exp_vlan_type,
                                dl_vlan=exp_vid,
                                dl_vlan_pcp=exp_pcp)
            else:
                if dl_vlan_int >= 0:
                    exp_pkt = simple_tcp_packet(pktlen=len_w_vid,
                                dl_vlan_enable=True,
                                dl_vlan=dl_vlan_int,
                                dl_vlan_pcp=dl_vlan_pcp_int)
                    exp_pkt.push_vlan(exp_vlan_type)
                    exp_pkt.set_vlan_vid(exp_vid)
                    exp_pkt.set_vlan_pcp(exp_pcp)

                else:
                    exp_pkt = simple_tcp_packet(pktlen=len_w_vid,
                                dl_vlan_enable=True,
                                dl_vlan_type=exp_vlan_type,
                                dl_vlan=exp_vid,
                                dl_vlan_pcp=exp_pcp)
        else:
            #subtract action
            if dl_vlan_int >= 0:
                exp_pkt = simple_tcp_packet(pktlen=len_w_vid,
                            dl_vlan_enable=True,
                            dl_vlan=dl_vlan_int,
                            dl_vlan_pcp=dl_vlan_pcp_int)
            else:
                exp_pkt = simple_tcp_packet(pktlen=len,
                            dl_vlan_enable=False)

    match = parse.packet_to_flow_match(pkt)
    parent.assertTrue(match is not None, "Flow match from pkt failed")

    match.dl_vlan = vid_match
    match.dl_vlan_pcp = pcp_match
    match.wildcards = wildcards

    request = flow_msg_create(parent, pkt, ing_port=ing_port,
                              wildcards=wildcards,
                              match=match,
                              egr_port=egr_port,
                              action_list=action_list)

    flow_msg_install(parent, request)

    parent.logger.debug("Send packet: " + str(ing_port) + " to " + str(egr_port))
    parent.logger.debug("Sent:" + str(pkt).encode('hex'))
    parent.dataplane.send(ing_port, str(pkt))

    if match_exp:
        receive_pkt_verify(parent, egr_port, exp_pkt)
        if check_expire:
            #@todo Not all HW supports both pkt and byte counters
            flow_removed_verify(parent, request, pkt_count=1, byte_count=len(pkt))
    else:
        if exp_msg is ofp.OFPT_FLOW_REMOVED:
            if check_expire:
                flow_removed_verify(parent, request, pkt_count=0, byte_count=0)
        elif exp_msg is ofp.OFPT_ERROR:
            error_verify(parent, exp_msg_type, exp_msg_code)
        else:
            parent.assertTrue(0, "Rcv: Unexpected Message: " + str(exp_msg))

        (_, rcv_pkt, _) = parent.dataplane.poll(timeout=1)
        parent.assertFalse(rcv_pkt is not None, "Packet on dataplane")

def flow_match_test_vlan(parent, port_map, wildcards=0,
                         dl_vlan=-1, dl_vlan_pcp=0, dl_vlan_type=ETHERTYPE_VLAN,
                         dl_vlan_int=-1, dl_vlan_pcp_int=0,
                         vid_match=ofp.OFPVID_NONE, pcp_match=0,
                         exp_vid=-1, exp_pcp=0,
                         exp_vlan_type=ETHERTYPE_VLAN,
                         match_exp=True,
                         add_tag_exp=False,
                         exp_msg=ofp.OFPT_FLOW_REMOVED,
                         exp_msg_type=0, exp_msg_code=0,
                         pkt=None, exp_pkt=None,
                         action_list=None,
                         check_expire=False,
                         max_test=0):
    """
    Run flow_match_test_port_pair on all port pairs

    @param max_test If > 0 no more than this number of tests are executed.
    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param wildcards For flow match entry
    @param dl_vlan If not -1, and pkt is not None, create a pkt w/ VLAN tag
    @param dl_vlan_pcp VLAN PCP associated with dl_vlan
    @param dl_vlan_type VLAN ether type associated with dl_vlan
    @param dl_vlan_int If not -1, create pkt w/ Inner Vlan tag
    @param dl_vlan_pcp_int VLAN PCP associated with dl_vlan_2nd
    @param vid_match Matching value for VLAN VID field
    @param pcp_match Matching value for VLAN PCP field
    @param exp_vid Expected VLAN VID value. If -1, no VLAN expected
    @param exp_vlan_type Expected VLAN ether type
    @param exp_pcp Expected VLAN PCP value
    @param match_exp Set whether packet is expected to receive
    @param add_tag_exp If True, expected_packet has an additional vlan tag,
    If not, expected_packet's vlan tag is replaced as specified
    @param exp_msg Expected message
    @param exp_msg_type Expected message type associated with the message
    @param exp_msg_code Expected message code associated with the msg_type
    @param pkt If not None, use this packet for ingress
    @param exp_pkt If not None, use this as the expected output pkt
    @param action_list Additional actions to add to flow mod
    @param check_expire Check for flow expiration message
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
            flow_match_test_port_pair_vlan(parent, ingress_port, egress_port,
                                           wildcards=wildcards,
                                           dl_vlan=dl_vlan,
                                           dl_vlan_pcp=dl_vlan_pcp,
                                           dl_vlan_type=dl_vlan_type,
                                           dl_vlan_int=dl_vlan_int,
                                           dl_vlan_pcp_int=dl_vlan_pcp_int,
                                           vid_match=vid_match,
                                           pcp_match=pcp_match,
                                           exp_vid=exp_vid,
                                           exp_pcp=exp_pcp,
                                           exp_vlan_type=exp_vlan_type,
                                           exp_msg=exp_msg,
                                           exp_msg_type=exp_msg_type,
                                           exp_msg_code=exp_msg_code,
                                           match_exp=match_exp,
                                           add_tag_exp=add_tag_exp,
                                           pkt=pkt, exp_pkt=exp_pkt,
                                           action_list=action_list,
                                           check_expire=check_expire)
            test_count += 1
            if (max_test > 0) and (test_count >= max_test):
                parent.logger.info("Ran " + str(test_count) + " tests; exiting")
                return

def test_param_get(config, key, default=None):
    """
    Return value passed via test-params if present

    @param config The configuration structure for OFTest
    @param key The lookup key
    @param default Default value to use if not found

    If the pair 'key=val' appeared in the string passed to --test-params
    on the command line, return val (as interpreted by exec).  Otherwise
    return default value.
    """
    try:
        exec config["test_params"]
    except:
        return default

    s = "val = " + str(key)
    try:
        val = None
        exec s
        return val
    except:
        return default

def action_generate(parent, field_to_mod, mod_field_vals):
    """
    Create an action to modify the field indicated in field_to_mod

    @param parent Must implement, assertTrue
    @param field_to_mod The field to modify as a string name
    @param mod_field_vals Hash of values to use for modified values
    """

    act = None

    if field_to_mod in ['pktlen']:
        return None

    if field_to_mod == 'dl_dst':
        act = action.action_set_dl_dst()
        act.dl_addr = parse.parse_mac(mod_field_vals['dl_dst'])
    elif field_to_mod == 'dl_src':
        act = action.action_set_dl_src()
        act.dl_addr = parse.parse_mac(mod_field_vals['dl_src'])
    elif field_to_mod == 'dl_vlan_enable':
        if not mod_field_vals['dl_vlan_enable']: # Strip VLAN tag
            act = action.action_pop_vlan()
        # Add VLAN tag is handled by dl_vlan field
        # Will return None in this case
    elif field_to_mod == 'dl_vlan':
        act = action.action_set_vlan_vid()
        act.vlan_vid = mod_field_vals['dl_vlan']
    elif field_to_mod == 'dl_vlan_pcp':
        act = action.action_set_vlan_pcp()
        act.vlan_pcp = mod_field_vals['dl_vlan_pcp']
    elif field_to_mod == 'ip_src':
        act = action.action_set_nw_src()
        act.nw_addr = parse.parse_ip(mod_field_vals['ip_src'])
    elif field_to_mod == 'ip_dst':
        act = action.action_set_nw_dst()
        act.nw_addr = parse.parse_ip(mod_field_vals['ip_dst'])
    elif field_to_mod == 'ip_tos':
        act = action.action_set_nw_tos()
        act.nw_tos = mod_field_vals['ip_tos']
    elif field_to_mod == 'tcp_sport':
        act = action.action_set_tp_src()
        act.tp_port = mod_field_vals['tcp_sport']
    elif field_to_mod == 'tcp_dport':
        act = action.action_set_tp_dst()
        act.tp_port = mod_field_vals['tcp_dport']
    else:
        parent.assertTrue(0, "Unknown field to modify: " + str(field_to_mod))

    return act

def pkt_action_setup(parent, start_field_vals={}, mod_field_vals={}, 
                     mod_fields={}, check_test_params=False):
    """
    Set up the ingress and expected packet and action list for a test

    @param parent Must implement, assertTrue, config hash and logger
    @param start_field_values Field values to use for ingress packet (optional)
    @param mod_field_values Field values to use for modified packet (optional)
    @param mod_fields The list of fields to be modified by the switch in the test.
    @params check_test_params If True, will check the parameters vid, add_vlan
    and strip_vlan from the command line.

    Returns a triple:  pkt-to-send, expected-pkt, action-list
    """

    new_actions = []


    base_pkt_params = {}
    base_pkt_params['pktlen'] = 100
    base_pkt_params['dl_dst'] = '00:DE:F0:12:34:56'
    base_pkt_params['dl_src'] = '00:23:45:67:89:AB'
    base_pkt_params['dl_vlan_enable'] = False
    base_pkt_params['dl_vlan'] = 2
    base_pkt_params['dl_vlan_pcp'] = 0
    base_pkt_params['ip_src'] = '192.168.0.1'
    base_pkt_params['ip_dst'] = '192.168.0.2'
    base_pkt_params['ip_tos'] = 0
    base_pkt_params['tcp_sport'] = 1234
    base_pkt_params['tcp_dport'] = 80
    for keyname in start_field_vals.keys():
        base_pkt_params[keyname] = start_field_vals[keyname]

    mod_pkt_params = {}
    mod_pkt_params['pktlen'] = 100
    mod_pkt_params['dl_dst'] = '00:21:0F:ED:CB:A9'
    mod_pkt_params['dl_src'] = '00:ED:CB:A9:87:65'
    mod_pkt_params['dl_vlan_enable'] = False
    mod_pkt_params['dl_vlan'] = 3
    mod_pkt_params['dl_vlan_pcp'] = 7
    mod_pkt_params['ip_src'] = '10.20.30.40'
    mod_pkt_params['ip_dst'] = '50.60.70.80'
    mod_pkt_params['ip_tos'] = 0xf0
    mod_pkt_params['tcp_sport'] = 4321
    mod_pkt_params['tcp_dport'] = 8765
    for keyname in mod_field_vals.keys():
        mod_pkt_params[keyname] = mod_field_vals[keyname]

    # Check for test param modifications
    strip = False
    if check_test_params:
        add_vlan = test_param_get(parent.config, 'add_vlan')
        strip_vlan = test_param_get(parent.config, 'strip_vlan')
        vid = test_param_get(parent.config, 'vid')

        if add_vlan and strip_vlan:
            parent.assertTrue(0, "Add and strip VLAN both specified")

        if vid:
            base_pkt_params['dl_vlan_enable'] = True
            base_pkt_params['dl_vlan'] = vid
            if 'dl_vlan' in mod_fields:
                mod_pkt_params['dl_vlan'] = vid + 1

        if add_vlan:
            base_pkt_params['dl_vlan_enable'] = False
            mod_pkt_params['dl_vlan_enable'] = True
            mod_pkt_params['pktlen'] = base_pkt_params['pktlen'] + 4
            mod_fields.append('pktlen')
            mod_fields.append('dl_vlan_enable')
            if 'dl_vlan' not in mod_fields:
                mod_fields.append('dl_vlan')
        elif strip_vlan:
            base_pkt_params['dl_vlan_enable'] = True
            mod_pkt_params['dl_vlan_enable'] = False
            mod_pkt_params['pktlen'] = base_pkt_params['pktlen'] - 4
            mod_fields.append('dl_vlan_enable')
            mod_fields.append('pktlen')

    # Build the ingress packet
    ingress_pkt = simple_tcp_packet(**base_pkt_params)

    # Build the expected packet, modifying the indicated fields
    for item in mod_fields:
        base_pkt_params[item] = mod_pkt_params[item]
        act = action_generate(parent, item, mod_pkt_params)
        if act:
            new_actions.append(act)

    expected_pkt = simple_tcp_packet(**base_pkt_params)

    return (ingress_pkt, expected_pkt, new_actions)
        
def wildcard_all_set(match):
    match.wildcards = ofp.OFPFW_ALL
    match.nw_dst_mask = 0xffffffff
    match.nw_src_mask = 0xffffffff
    match.dl_dst_mask = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
    match.dl_src_mask = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff]

def skip_message_emit(parent, s):
    """
    Print out a 'skipped' message to stderr

    @param s The string to print out to the log file
    @param parent Must implement config and logger objects
    """
    global skipped_test_count

    skipped_test_count += 1
    parent.logger.info("Skipping: " + s)
    if parent.config["dbg_level"] < logging.WARNING:
        sys.stderr.write("(skipped) ")
    else:
        sys.stderr.write("(S)")

def do_echo_request_reply_test(test,controller):
        request = message.echo_request()
        response, _ = controller.transact(request)
        test.assertEqual(response.header.type, ofp.OFPT_ECHO_REPLY,
                         'response is not echo_reply')
        test.assertEqual(request.header.xid, response.header.xid,
                         'response xid != request xid')
        test.assertEqual(len(response.data), 0, 'response data non-empty')

def match_all_generate():
    match = ofp.ofp_match()
    match.length = ofp.OFP_MATCH_BYTES
    match.wildcards = ofp.OFPFW_ALL
    match.dl_src_mask = [255,255,255,255,255,255]
    match.dl_dst_mask = [255,255,255,255,255,255]
    match.nw_src_mask = int(0xffffffff)
    match.nw_dst_mask = int(0xffffffff)
    return match

from oftest.packet import MplsTag
def simple_tcp_packet_w_mpls(pktlen=100,
                      dl_dst='00:01:02:03:04:05',
                      dl_src='00:06:07:08:09:0a',
                      mpls_type=0x8847,
                      mpls_label=-1,
                      mpls_tc=0,
                      mpls_ttl=64,
                      mpls_label_int=-1,
                      mpls_tc_int=0,
                      mpls_ttl_int=32,
                      mpls_label_ext=-1,
                      mpls_tc_ext=0,
                      mpls_ttl_ext=128,
                      ip_src='192.168.0.1',
                      ip_dst='192.168.0.2',
                      ip_tos=0,
                      ip_ttl=192,
                      tcp_sport=1234,
                      tcp_dport=80
                      ):
    """
    Return a simple dataplane TCP packet w/wo MPLS tags

    Supports a few parameters:
    @param len Length of packet in bytes w/o CRC
    @param dl_dst Destinatino MAC
    @param dl_src Source MAC
    @param mpls_type MPLS type as ether type
    @param mpls_label MPLS LABEL if not -1
    @param mpls_tc MPLS TC
    @param mpls_ttl MPLS TTL
    @param mpls_label_int Inner MPLS LABEL if not -1. The shim will be added
    inside of mpls_label shim.
    @param mpls_tc_int Inner MPLS TC
    @param mpls_ttl_int Inner MPLS TTL
    @param mpls_label_ext External MPLS LABEL if not -1. The shim will be
    added outside of mpls_label shim
    @param mpls_tc_ext External MPLS TC
    @param mpls_ttl_ext External MPLS TTL
    @param ip_src IP source
    @param ip_dst IP destination
    @param ip_tos IP ToS
    @param tcp_dport TCP destination port
    @param ip_sport TCP source port

    Generates a simple MPLS/IP/TCP request.  Users
    shouldn't assume anything about this packet other than that
    it is a valid ethernet/IP/TCP frame.
    """
    
    mpls_tags = ()
    
    if mpls_label_ext >= 0:
        tag = MplsTag(mpls_label_ext, mpls_tc_ext, mpls_ttl_ext)
        mpls_tags += (tag,)
        
    if mpls_label >= 0:
        tag = MplsTag(mpls_label, mpls_tc, mpls_ttl)
        mpls_tags += (tag,)
        
    if mpls_label_int >= 0:
        tag = MplsTag(mpls_label_int, mpls_tc_int, mpls_ttl_int)
        mpls_tags += (tag,)
    
    pkt = Packet().simple_tcp_packet(pktlen=pktlen,
                                     dl_dst=dl_dst,
                                     dl_src=dl_src,
                                     mpls_type=mpls_type,
                                     mpls_tags=mpls_tags,
                                     ip_src=ip_src,
                                     ip_dst=ip_dst,
                                     ip_tos=ip_tos,  
                                     ip_ttl=ip_ttl,
                                     tcp_sport=tcp_sport,
                                     tcp_dport=tcp_dport)
    return pkt
    
def flow_match_test_port_pair_mpls(parent, ing_port, egr_port, wildcards=0,
                                   mpls_type=0x8847,
                                   mpls_label=-1, mpls_tc=0,mpls_ttl=64,
                                   mpls_label_int=-1, mpls_tc_int=0,
                                   mpls_ttl_int=32,
                                   ip_ttl=192,
                                   exp_mpls_type=0x8847,
                                   exp_mpls_label=-1, exp_mpls_tc=0,
                                   exp_mpls_ttl=64,
                                   exp_mpls_ttl_int=32,
                                   exp_ip_ttl=192,
                                   label_match=0, tc_match=0,
                                   dl_type_match=ETHERTYPE_MPLS,
                                   match_exp=True,
                                   add_tag_exp=False,
                                   exp_msg=ofp.OFPT_FLOW_REMOVED,
                                   exp_msg_type=0, exp_msg_code=0,
                                   pkt=None,
                                   exp_pkt=None, action_list=None,
                                   check_expire=False):
    """
    Flow match test on single packet w/ MPLS tags

    Run test with packet through switch from ing_port to egr_port
    See flow_match_test for parameter descriptions
    """
    parent.logger.info("Pkt match test: " + str(ing_port) + " to " + str(egr_port))
    parent.logger.debug("  WC: " + hex(wildcards) + " MPLS: " +
                    str(mpls_label) + " expire: " + str(check_expire))
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
        pkt = simple_tcp_packet_w_mpls(pktlen=pktlen,
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
            exp_pkt = simple_tcp_packet_w_mpls(pktlen=exp_pktlen,
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
                exp_pkt = simple_tcp_packet_w_mpls(pktlen=exp_pktlen,
                                           mpls_type=mpls_type,
                                           mpls_label=mpls_label_int,
                                           mpls_tc=mpls_tc_int,
                                           mpls_ttl=exp_mpls_ttl_int,
                                           ip_ttl=exp_ip_ttl)
            else:
                exp_pkt = simple_tcp_packet_w_mpls(pktlen=exp_pktlen,
                                           mpls_type=exp_mpls_type,
                                           mpls_label=exp_mpls_label,
                                           mpls_tc=exp_mpls_tc,
                                           mpls_ttl=exp_mpls_ttl,
                                           mpls_label_int=mpls_label_int,
                                           mpls_tc_int=mpls_tc_int,
                                           mpls_ttl_int=exp_mpls_ttl_int,
                                           ip_ttl=exp_ip_ttl)
    wildcards = (ofp.OFPFW_ALL & ~(ofp.OFPFW_DL_TYPE | ofp.OFPFW_MPLS_LABEL | ofp.OFPFW_MPLS_TC)) | wildcards

    match = parse.packet_to_flow_match(pkt)
    parent.assertTrue(match is not None, "Flow match from pkt failed")

    match.mpls_label = label_match
    match.mpls_tc = tc_match
    match.wildcards = wildcards

    match.dl_type = dl_type_match
    match.nw_tos = 0
    match.nw_proto = 0
    match.nw_src = 0
    match.nw_src_mask = 0xFFFFFFFF
    match.nw_dst = 0
    match.nw_dst_mask = 0xFFFFFFFF
    match.tp_src = 0
    match.tp_dst = 0

    request = flow_msg_create(parent, pkt, ing_port=ing_port,
                              wildcards=wildcards,
                              match=match,
                              egr_port=egr_port,
                              action_list=action_list)

    flow_msg_install(parent, request)

    parent.logger.debug("Send packet: " + str(ing_port) + " to " + str(egr_port))
    #parent.logger.debug(str(pkt).encode("hex"))
    parent.dataplane.send(ing_port, str(pkt))

    if match_exp:
        receive_pkt_verify(parent, egr_port, exp_pkt)
        if check_expire:
            #@todo Not all HW supports both pkt and byte counters
            flow_removed_verify(parent, request, pkt_count=1, byte_count=len(pkt))
    else:
        if exp_msg == ofp.OFPT_FLOW_REMOVED:
            if check_expire:
                flow_removed_verify(parent, request, pkt_count=0, byte_count=0)
        elif exp_msg == ofp.OFPT_ERROR:
            error_verify(parent, exp_msg_type, exp_msg_code)
        else:
            parent.assertTrue(0, "Rcv: Unexpected Message: " + str(exp_msg))
        (_, rcv_pkt, _) = parent.dataplane.poll(timeout=1)
        parent.assertFalse(rcv_pkt is not None, "Packet on dataplane")

def flow_match_test_mpls(parent, port_map, wildcards=0,
                         mpls_type=0x8847,
                         mpls_label=-1, mpls_tc=0, mpls_ttl=64,
                         mpls_label_int=-1, mpls_tc_int=0, mpls_ttl_int=32,
                         ip_ttl = 192,
                         label_match=0, tc_match=0,
                         dl_type_match=ETHERTYPE_MPLS,
                         exp_mpls_type=0x8847,
                         exp_mpls_label=-1, exp_mpls_tc=0, exp_mpls_ttl=64,
                         exp_mpls_ttl_int=32,
                         exp_ip_ttl=192,
                         match_exp=True,
                         add_tag_exp=False,
                         exp_msg=ofp.OFPT_FLOW_REMOVED,
                         exp_msg_type=0, exp_msg_code=0,
                         pkt=None,
                         exp_pkt=None, action_list=None, check_expire=False,
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
    @param label_match Matching value for MPLS LABEL field
    @param tc_match Matching value for MPLS TC field
    @param exp_mpls_label Expected MPLS LABEL value. If -1, no MPLS expected
    @param exp_mpls_tc Expected MPLS TC value
    @param exp_mpls_ttl Expected MPLS TTL value
    @param exp_mpls_ttl_int Expected Inner MPLS TTL value
    @param ip_ttl Expected IP TTL
    @param match_exp Set whether packet is expected to receive
    @param add_tag_exp If True, expected_packet has an additional MPLS shim,
    If not expected_packet's MPLS shim is replaced as specified
    @param exp_msg Expected message
    @param exp_msg_type Expected message type associated with the message
    @param exp_msg_code Expected message code associated with the msg_type
    @param pkt If not None, use this packet for ingress
    @param exp_pkt If not None, use this as the expected output pkt; els use pkt
    @param action_list Additional actions to add to flow mod
    @param check_expire Check for flow expiration message
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
            flow_match_test_port_pair_mpls(parent, ingress_port, egress_port,
                                      wildcards=wildcards,
                                      mpls_type=mpls_type,
                                      mpls_label=mpls_label,
                                      mpls_tc=mpls_tc,
                                      mpls_ttl=mpls_ttl,
                                      mpls_label_int=mpls_label_int,
                                      mpls_tc_int=mpls_tc_int,
                                      mpls_ttl_int=mpls_ttl_int,
                                      ip_ttl=ip_ttl,
                                      label_match=label_match,
                                      tc_match=tc_match,
                                      dl_type_match=dl_type_match,
                                      exp_mpls_type=exp_mpls_type,
                                      exp_mpls_label=exp_mpls_label,
                                      exp_mpls_tc=exp_mpls_tc,
                                      exp_mpls_ttl=exp_mpls_ttl,
                                      exp_mpls_ttl_int=exp_mpls_ttl_int,
                                      exp_ip_ttl=exp_ip_ttl,
                                      match_exp=match_exp,
                                      exp_msg=exp_msg,
                                      exp_msg_type=exp_msg_type,
                                      exp_msg_code=exp_msg_code,
                                      add_tag_exp=add_tag_exp,
                                      pkt=pkt, exp_pkt=exp_pkt,
                                      action_list=action_list,
                                      check_expire=check_expire)
            test_count += 1
            if (max_test > 0) and (test_count >= max_test):
                parent.logger.info("Ran " + str(test_count) + " tests; exiting")
                return
