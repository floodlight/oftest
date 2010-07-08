
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

def simple_tcp_packet(pktlen=100, 
                      dl_dst='00:01:02:03:04:05',
                      dl_src='00:06:07:08:09:0a',
                      dl_vlan_enable=False,
                      dl_vlan=0,
                      dl_vlan_pcp=0,
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
    if (dl_vlan_enable):
        pkt = scapy.Ether(dst=dl_dst, src=dl_src)/ \
            scapy.Dot1Q(prio=dl_vlan_pcp, id=0, vlan=dl_vlan)/ \
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
