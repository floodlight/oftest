"""
Functions to carry out actions on a packet

Really these should be in the OFSwitch class, but separated here
for file modularity.
"""

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
    for action in actions:
        exec_str = "do_" + action.__name__ + \
            "(switch, packet, action, output_now)"
        try:
            exec(exec_str)
        except:  #@todo: Add constraint
            #@todo Define logging module
            print("Could not execute packet action" + str(action))

    # @todo This needs clarification.
    if packet.output_port is not None:
        dataplane.send(packet.output_port, packet.data)

def do_action_set_output_port(switch, packet, action, output_now):
    """
    Carry out the set_output_port action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_output_port action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    packet.set_output_port(action.port)

def do_action_set_vlan_vid(switch, packet, action, output_now):
    """
    Carry out the set_vlan_vid action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_vlan_vid action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    packet.set_vlan_vid(packet, action.vlan_vid);

def do_action_set_vlan_pcp(switch, packet, action, output_now):
    """
    Carry out the set_vlan_pcp action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_vlan_pcp action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    packet.set_vlan_pcp(packet, action.vlan_pcp);

def do_action_set_dl_src(switch, packet, action, output_now):
    """
    Carry out the set_dl_src action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_dl_src action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    packet.set_dl_src(action.dl_addr)

def do_action_set_dl_dst(switch, packet, action, output_now):
    """
    Carry out the set_dl_dst action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_dl_dst action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    packet.set_dl_dst(action.dl_addr)

def do_action_set_nw_src(switch, packet, action, output_now):
    """
    Carry out the set_nw_src action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_nw_src action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    packet.set_nw_src(action.nw_addr)

def do_action_set_nw_dst(switch, packet, action, output_now):
    """
    Carry out the set_nw_dst action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_nw_dst action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    packet.set_nw_dst(action.nw_addr)

def do_action_set_nw_tos(switch, packet, action, output_now):
    """
    Carry out the set_nw_tos action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_nw_tos action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    pass

def do_action_set_nw_ecn(switch, packet, action, output_now):
    """
    Carry out the set_nw_ecn action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_nw_ecn action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    pass

def do_action_set_tp_src(switch, packet, action, output_now):
    """
    Carry out the set_tp_src action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_tp_src action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    pass

def do_action_set_tp_dst(switch, packet, action, output_now):
    """
    Carry out the set_tp_dst action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_tp_dst action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    pass

def do_action_copy_ttl_out(switch, packet, action, output_now):
    """
    Carry out the copy_ttl_out action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The copy_ttl_out action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    pass

def do_action_copy_ttl_in(switch, packet, action, output_now):
    """
    Carry out the copy_ttl_in action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The copy_ttl_in action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    pass

def do_action_set_mpls_label(switch, packet, action, output_now):
    """
    Carry out the set_mpls_label action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_mpls_label action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    pass

def do_action_set_mpls_tc(switch, packet, action, output_now):
    """
    Carry out the set_mpls_tc action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_mpls_tc action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    pass

def do_action_set_mpls_ttl(switch, packet, action, output_now):
    """
    Carry out the set_mpls_ttl action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_mpls_ttl action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    pass

def do_action_dec_mpls_ttl(switch, packet, action, output_now):
    """
    Carry out the dec_mpls_ttl action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The dec_mpls_ttl action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    pass

def do_action_push_vlan(switch, packet, action, output_now):
    """
    Carry out the push_vlan action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The push_vlan action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    pass

def do_action_pop_vlan(switch, packet, action, output_now):
    """
    Carry out the pop_vlan action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The pop_vlan action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    pass

def do_action_push_mpls(switch, packet, action, output_now):
    """
    Carry out the push_mpls action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The push_mpls action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    pass

def do_action_pop_mpls(switch, packet, action, output_now):
    """
    Carry out the pop_mpls action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The pop_mpls action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    pass

def do_action_set_queue(switch, packet, action, output_now):
    """
    Carry out the set_queue action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_queue action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    pass

def do_action_group(switch, packet, action, output_now):
    """
    Carry out the group action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The group action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    pass

def do_action_set_nw_ttl(switch, packet, action, output_now):
    """
    Carry out the set_nw_ttl action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The set_nw_ttl action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    pass

def do_action_dec_nw_ttl(switch, packet, action, output_now):
    """
    Carry out the dec_nw_ttl action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The dec_nw_ttl action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    pass

def do_action_experimenter(switch, packet, action, output_now):
    """
    Carry out the experimenter action
    @param switch The parent switch object
    @param packet The packet to be modified, forwarded, etc
    @param action The experimenter action obj for parameters
    @param output_now For the set_output_port action, send packet immediately
    """
    pass

