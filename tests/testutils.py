
import sys
import copy

try:
    import scapy.all as scapy
except:
    try:
        import scapy as scapy
    except:
        sys.exit("Need to install scapy for packet parsing")

import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action
import oftest.parse as parse
import logging
import types

global skipped_test_count
skipped_test_count = 0

# Some useful defines
IP_ETHERTYPE = 0x800
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

def delete_all_flows(ctrl, logger):
    """
    Delete all flows on the switch
    @param ctrl The controller object for the test
    @param logger Logging object
    """

    logger.info("Deleting all flows")
    msg = message.flow_mod()
    msg.match.wildcards = ofp.OFPFW_ALL
    msg.out_port = ofp.OFPP_NONE
    msg.command = ofp.OFPFC_DELETE
    msg.buffer_id = 0xffffffff
    return ctrl.message_send(msg)

def clear_port_config(parent, port, logger):
    """
    Clear the port configuration (currently only no flood setting)

    @param parent Object implementing controller and assert equal
    @param logger Logging object
    """
    rv = port_config_set(parent.controller, port,
                         0, ofp.OFPPC_NO_FLOOD, logger)
    self.assertEqual(rv, 0, "Failed to reset port config")

def simple_tcp_packet(pktlen=100, 
                      dl_dst='00:01:02:03:04:05',
                      dl_src='00:06:07:08:09:0a',
                      dl_vlan_enable=False,
                      dl_vlan=0,
                      dl_vlan_pcp=0,
                      dl_vlan_cfi=0,
                      ip_src='192.168.0.1',
                      ip_dst='192.168.0.2',
                      ip_tos=0,
                      tcp_sport=1234,
                      tcp_dport=80
                      ):
    """
    Return a simple dataplane TCP packet

    Supports a few parameters:
    @param len Length of packet in bytes w/o CRC
    @param dl_dst Destinatino MAC
    @param dl_src Source MAC
    @param dl_vlan_enable True if the packet is with vlan, False otherwise
    @param dl_vlan VLAN ID
    @param dl_vlan_pcp VLAN priority
    @param ip_src IP source
    @param ip_dst IP destination
    @param ip_tos IP ToS
    @param tcp_dport TCP destination port
    @param ip_sport TCP source port

    Generates a simple TCP request.  Users
    shouldn't assume anything about this packet other than that
    it is a valid ethernet/IP/TCP frame.
    """
    # Note Dot1Q.id is really CFI
    if (dl_vlan_enable):
        pkt = scapy.Ether(dst=dl_dst, src=dl_src)/ \
            scapy.Dot1Q(prio=dl_vlan_pcp, id=dl_vlan_cfi, vlan=dl_vlan)/ \
            scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos)/ \
            scapy.TCP(sport=tcp_sport, dport=tcp_dport)
    else:
        pkt = scapy.Ether(dst=dl_dst, src=dl_src)/ \
            scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos)/ \
            scapy.TCP(sport=tcp_sport, dport=tcp_dport)

    pkt = pkt/("D" * (pktlen - len(pkt)))

    return pkt

def simple_icmp_packet(pktlen=60, 
                      dl_dst='00:01:02:03:04:05',
                      dl_src='00:06:07:08:09:0a',
                      dl_vlan_enable=False,
                      dl_vlan=0,
                      dl_vlan_pcp=0,
                      ip_src='192.168.0.1',
                      ip_dst='192.168.0.2',
                      ip_tos=0,
                      icmp_type=8,
                      icmp_code=0
                      ):
    """
    Return a simple ICMP packet

    Supports a few parameters:
    @param len Length of packet in bytes w/o CRC
    @param dl_dst Destinatino MAC
    @param dl_src Source MAC
    @param dl_vlan_enable True if the packet is with vlan, False otherwise
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
    if (dl_vlan_enable):
        pkt = scapy.Ether(dst=dl_dst, src=dl_src)/ \
            scapy.Dot1Q(prio=dl_vlan_pcp, id=0, vlan=dl_vlan)/ \
            scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos)/ \
            scapy.ICMP(type=icmp_type, code=icmp_code)
    else:
        pkt = scapy.Ether(dst=dl_dst, src=dl_src)/ \
            scapy.IP(src=ip_src, dst=ip_dst, tos=ip_tos)/ \
            scapy.ICMP(type=icmp_type, code=icmp_code)

    pkt = pkt/("0" * (pktlen - len(pkt)))

    return pkt

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
    reply, pkt = controller.transact(request, timeout=2)
    logger.debug(reply.show())
    if reply is None:
        logger.warn("Get feature request failed")
        return None, None, None
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
    reply, pkt = controller.transact(request, timeout=2)
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
        (rcv_port, rcv_pkt, pkt_time) = dataplane.poll(
            port_number=ofport, timeout=1)
        assert_if.assertTrue(rcv_pkt is not None, 
                             "Did not receive pkt on " + str(ofport))
        assert_if.assertEqual(str(pkt), str(rcv_pkt),
                              "Response packet does not match send packet " +
                              "on port " + str(ofport))

    for ofport in no_ports:
        logger.debug("Negative check for pkt on port " + str(ofport))
        (rcv_port, rcv_pkt, pkt_time) = dataplane.poll(
            port_number=ofport, timeout=1)
        assert_if.assertTrue(rcv_pkt is None, 
                             "Unexpected pkt on port " + str(ofport))


def receive_pkt_verify(parent, egr_port, exp_pkt):
    """
    Receive a packet and verify it matches an expected value

    parent must implement dataplane, assertTrue and assertEqual
    """
    (rcv_port, rcv_pkt, pkt_time) = parent.dataplane.poll(port_number=egr_port,
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
    (response, raw) = parent.controller.poll(ofp.OFPT_FLOW_REMOVED, 2)
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
                           str(request,priority) + " != " + 
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

def flow_msg_create(parent, pkt, ing_port=None, action_list=None, wildcards=0,
               egr_port=None, egr_queue=None, check_expire=False):
    """
    Create a flow message

    Match on packet with given wildcards.  
    See flow_match_test for other parameter descriptoins
    @param egr_queue if not None, make the output an enqueue action
    """
    match = parse.packet_to_flow_match(pkt)
    parent.assertTrue(match is not None, "Flow match from pkt failed")
    match.wildcards = wildcards
    match.in_port = ing_port

    request = message.flow_mod()
    request.match = match
    request.buffer_id = 0xffffffff
    if check_expire:
        request.flags |= ofp.OFPFF_SEND_FLOW_REM
        request.hard_timeout = 1

    if action_list is not None:
        for act in action_list:
            parent.logger.debug("Adding action " + act.show())
            rv = request.actions.add(act)
            parent.assertTrue(rv, "Could not add action" + act.show())

    # Set up output/enqueue action if directed
    if egr_queue is not None:
        parent.assertTrue(egr_port is not None, "Egress port not set")
        act = action.action_enqueue()
        act.port = egr_port
        act.queue_id = egr_queue
        rv = request.actions.add(act)
        parent.assertTrue(rv, "Could not add enqueue action " + 
                          str(egr_port) + " Q: " + str(egr_queue))
    elif egr_port is not None:
        act = action.action_output()
        act.port = egr_port
        rv = request.actions.add(act)
        parent.assertTrue(rv, "Could not add output action " + str(egr_port))

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
        rc = delete_all_flows(parent.controller, parent.logger)
        parent.assertEqual(rc, 0, "Failed to delete all flows")
        do_barrier(parent.controller)

    parent.logger.debug("Insert flow")
    rv = parent.controller.message_send(request)
    parent.assertTrue(rv != -1, "Error installing flow mod")
    do_barrier(parent.controller)

def flow_match_test_port_pair(parent, ing_port, egr_port, wildcards=0, 
                              dl_vlan=-1, pkt=None, exp_pkt=None,
                              action_list=None, check_expire=False):
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

    request = flow_msg_create(parent, pkt, ing_port=ing_port, 
                              wildcards=wildcards, egr_port=egr_port,
                              action_list=action_list)

    flow_msg_install(parent, request)

    parent.logger.debug("Send packet: " + str(ing_port) + " to " + str(egr_port))
    parent.dataplane.send(ing_port, str(pkt))

    if exp_pkt is None:
        exp_pkt = pkt
    receive_pkt_verify(parent, egr_port, exp_pkt)

    if check_expire:
        #@todo Not all HW supports both pkt and byte counters
        flow_removed_verify(parent, request, pkt_count=1, byte_count=len(pkt))

def flow_match_test(parent, port_map, wildcards=0, dl_vlan=-1, pkt=None, 
                    exp_pkt=None, action_list=None, check_expire=False, 
                    max_test=0):
    """
    Run flow_match_test_port_pair on all port pairs

    @param max_test If > 0 no more than this number of tests are executed.
    @param parent Must implement controller, dataplane, assertTrue, assertEqual
    and logger
    @param pkt If not None, use this packet for ingress
    @param wildcards For flow match entry
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
                                      wildcards=wildcards, dl_vlan=dl_vlan, 
                                      pkt=pkt, exp_pkt=exp_pkt,
                                      action_list=action_list,
                                      check_expire=check_expire)
            test_count += 1
            if (max_test > 0) and (test_count > max_test):
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
            act = action.action_strip_vlan()
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
