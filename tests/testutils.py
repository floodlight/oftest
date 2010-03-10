
import sys

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
                      ip_src='192.168.0.1',
                      ip_dst='192.168.0.2',
                      tcp_sport=1234,
                      tcp_dport=80
                      ):
    """
    Return a simple dataplane TCP packet

    Supports a few parameters:
    @param len Length of packet in bytes w/o CRC
    @param dl_dst Destinatino MAC
    @param dl_src Source MAC
    @param ip_src IP source
    @param ip_dst IP destination
    @param tcp_dport TCP destination port
    @param ip_sport TCP source port

    Generates a simple TCP request.  Users
    shouldn't assume anything about this packet other than that
    it is a valid ethernet/IP/TCP frame.
    """
    pkt = scapy.Ether(dst=dl_dst, src=dl_src)/ \
        scapy.IP(src=ip_src, dst=ip_dst)/ \
        scapy.TCP(sport=tcp_sport, dport=tcp_dport)
    pkt = pkt/("D" * (pktlen - len(pkt)))

    return pkt

def do_barrier(ctrl):
    b = message.barrier_request()
    ctrl.transact(b)
