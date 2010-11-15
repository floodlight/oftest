######################################################################
#
# All files associated with the OpenFlow Python Switch (ofps) are
# made available for public use and benefit with the expectation
# that others will use, modify and enhance the Software and contribute
# those enhancements back to the community. However, since we would
# like to make the Software available for broadest use, with as few
# restrictions as possible permission is hereby granted, free of
# charge, to any person obtaining a copy of this Software to deal in
# the Software under the copyrights without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject
# to the following conditions:
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# 
######################################################################

"""
Functions to carry out actions on a packet

Really these should be in the OFSwitch class, but they are put here
for file modularity.
"""

import oftest.message as message
import oftest.cstruct as ofp

def execute_actions(switch, packet, actions, output_now=False):
    """
    Execute the list of actions on the packet
    @param switch The parent switch object
    @param packet The ingress packet on which to execute the actions
    @param actions The list of actions to be applied to the packet
    @param output_now For the set_output_port action, send packet immediately

    Actions are executed in whatever order they are passed without
    checking the integrity of this ordering.

    The handler function for an action must have the name
    do_action_<name>; for example do_action_set_dl_dst.
    """
    for action in actions.actions:
        exec_str = "do_" + action.__class__.__name__ + \
            "(switch, packet, action, output_now)"
        try:
            switch.logger.debug("Executing do_" + action.__class__.__name__)
            exec(exec_str)
        except StandardError:
            #@todo Define logging module
            switch.logger.error("Could not execute packet action" + str(action))

    # @todo This needs clarification.
    if packet.output_port is not None:
        dataplane.send(packet.output_port, packet.data)

def packet_in_to_controller(switch, packet, reason=ofp.OFPR_NO_MATCH,
                            table_id=0):
    """
    Special action funtion to send a packet to the controller as packet_in

    @param switch The parent switch object
    @param packet The OFPS packet object to forward
    """
    #@todo For now, always forward entire packet, no buffering
    msg = message.packet_in()
    msg.data = packet.data
    msg.in_port = packet.in_port
    msg.in_phy_port = packet.in_port #@todo Check this
    msg.total_len = packet.bytes
    msg.buffer_id = -1
    msg.reason = reason
    msg.table_id = table_id
    switch.controller.message_send(msg)

def do_action_set_output_port(switch, packet, action, output_now):
    """
    Carry out the set_output_port action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_output_port action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_set_output_port: now " + str(output_now))
    if output_now:
        switch.dataplane.send(action.port, packet.data)        
    else:
        packet.set_output_port(action.port)

def do_action_set_vlan_vid(switch, packet, action, output_now):
    """
    Carry out the set_vlan_vid action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_vlan_vid action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_set_vlan_vid")
    packet.set_vlan_vid(packet, action.vlan_vid);

def do_action_set_vlan_pcp(switch, packet, action, output_now):
    """
    Carry out the set_vlan_pcp action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_vlan_pcp action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_set_vlan_pcp")
    packet.set_vlan_pcp(packet, action.vlan_pcp);

def do_action_set_dl_src(switch, packet, action, output_now):
    """
    Carry out the set_dl_src action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_dl_src action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_set_dl_src")
    packet.set_dl_src(action.dl_addr)

def do_action_set_dl_dst(switch, packet, action, output_now):
    """
    Carry out the set_dl_dst action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_dl_dst action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_set_dl_dst")
    packet.set_dl_dst(action.dl_addr)

def do_action_set_nw_src(switch, packet, action, output_now):
    """
    Carry out the set_nw_src action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_nw_src action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_set_nw_src")
    packet.set_nw_src(action.nw_addr)

def do_action_set_nw_dst(switch, packet, action, output_now):
    """
    Carry out the set_nw_dst action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_nw_dst action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_set_nw_dst")
    packet.set_nw_dst(action.nw_addr)

def do_action_set_nw_tos(switch, packet, action, output_now):
    """
    Carry out the set_nw_tos action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_nw_tos action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_set_nw_tos")

def do_action_set_nw_ecn(switch, packet, action, output_now):
    """
    Carry out the set_nw_ecn action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_nw_ecn action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_set_nw_ecn")

def do_action_set_tp_src(switch, packet, action, output_now):
    """
    Carry out the set_tp_src action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_tp_src action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_set_tp_src")

def do_action_set_tp_dst(switch, packet, action, output_now):
    """
    Carry out the set_tp_dst action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_tp_dst action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_set_tp_dst")

def do_action_copy_ttl_out(switch, packet, action, output_now):
    """
    Carry out the copy_ttl_out action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The copy_ttl_out action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_copy_ttl_out")

def do_action_copy_ttl_in(switch, packet, action, output_now):
    """
    Carry out the copy_ttl_in action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The copy_ttl_in action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_copy_ttl_in")

def do_action_set_mpls_label(switch, packet, action, output_now):
    """
    Carry out the set_mpls_label action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_mpls_label action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_set_mpls_label")

def do_action_set_mpls_tc(switch, packet, action, output_now):
    """
    Carry out the set_mpls_tc action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_mpls_tc action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_set_mpls_tc")

def do_action_set_mpls_ttl(switch, packet, action, output_now):
    """
    Carry out the set_mpls_ttl action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_mpls_ttl action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_set_mpls_ttl")

def do_action_dec_mpls_ttl(switch, packet, action, output_now):
    """
    Carry out the dec_mpls_ttl action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The dec_mpls_ttl action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_dec_mpls_ttl")

def do_action_push_vlan(switch, packet, action, output_now):
    """
    Carry out the push_vlan action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The push_vlan action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_push_vlan")

def do_action_pop_vlan(switch, packet, action, output_now):
    """
    Carry out the pop_vlan action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The pop_vlan action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_pop_vlan")

def do_action_push_mpls(switch, packet, action, output_now):
    """
    Carry out the push_mpls action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The push_mpls action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_push_mpls")

def do_action_pop_mpls(switch, packet, action, output_now):
    """
    Carry out the pop_mpls action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The pop_mpls action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_pop_mpls")

def do_action_set_queue(switch, packet, action, output_now):
    """
    Carry out the set_queue action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_queue action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_set_queue")

def do_action_group(switch, packet, action, output_now):
    """
    Carry out the group action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The group action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_group")

def do_action_set_nw_ttl(switch, packet, action, output_now):
    """
    Carry out the set_nw_ttl action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_nw_ttl action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_set_nw_ttl")

def do_action_dec_nw_ttl(switch, packet, action, output_now):
    """
    Carry out the dec_nw_ttl action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The dec_nw_ttl action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_dec_nw_ttl")

def do_action_experimenter(switch, packet, action, output_now):
    """
    Carry out the experimenter action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The experimenter action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    switch.logger.debug("do_action_experimenter")

