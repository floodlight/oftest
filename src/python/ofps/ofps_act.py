"""
Functions to carry out actions on a packet
"""

def do_action_set_output_port(packet, action, groups, ctrl_if, output_now):
    """
    Carry out the set_output_port action
    @param packet The packet to be modified, forwarded, etc
    @param action The set_output_port action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    packet.set_output_port(action.port)

def do_action_set_vlan_vid(packet, action, groups, dataplane, ctrl_if, 
                           output_now):
    """
    Carry out the set_vlan_vid action
    @param packet The packet to be modified, forwarded, etc
    @param action The set_vlan_vid action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    packet.set_vlan_vid(packet, action.vlan_vid);

def do_action_set_vlan_pcp(packet, action, groups, dataplane, ctrl_if, 
                           output_now):
    """
    Carry out the set_vlan_pcp action
    @param packet The packet to be modified, forwarded, etc
    @param action The set_vlan_pcp action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    packet.set_vlan_pcp(packet, action.vlan_pcp);

def do_action_set_dl_src(packet, action, groups, dataplane, ctrl_if, 
                         output_now):
    """
    Carry out the set_dl_src action
    @param packet The packet to be modified, forwarded, etc
    @param action The set_dl_src action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    packet.set_dl_src(action.dl_addr)

def do_action_set_dl_dst(packet, action, groups, dataplane, ctrl_if, 
                         output_now):
    """
    Carry out the set_dl_dst action
    @param packet The packet to be modified, forwarded, etc
    @param action The set_dl_dst action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    packet.set_dl_dst(action.dl_addr)

def do_action_set_nw_src(packet, action, groups, dataplane, ctrl_if, 
                         output_now):
    """
    Carry out the set_nw_src action
    @param packet The packet to be modified, forwarded, etc
    @param action The set_nw_src action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    packet.set_nw_src(action.nw_addr)

def do_action_set_nw_dst(packet, action, groups, dataplane, ctrl_if, 
                         output_now):
    """
    Carry out the set_nw_dst action
    @param packet The packet to be modified, forwarded, etc
    @param action The set_nw_dst action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    packet.set_nw_dst(action.nw_addr)

def do_action_set_nw_tos(packet, action, groups, dataplane, ctrl_if, 
                         output_now):
    """
    Carry out the set_nw_tos action
    @param packet The packet to be modified, forwarded, etc
    @param action The set_nw_tos action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    pass

def do_action_set_nw_ecn(packet, action, groups, dataplane, ctrl_if, 
                         output_now):
    """
    Carry out the set_nw_ecn action
    @param packet The packet to be modified, forwarded, etc
    @param action The set_nw_ecn action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    pass

def do_action_set_tp_src(packet, action, groups, dataplane, ctrl_if, 
                         output_now):
    """
    Carry out the set_tp_src action
    @param packet The packet to be modified, forwarded, etc
    @param action The set_tp_src action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    pass

def do_action_set_tp_dst(packet, action, groups, dataplane, ctrl_if, 
                         output_now):
    """
    Carry out the set_tp_dst action
    @param packet The packet to be modified, forwarded, etc
    @param action The set_tp_dst action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    pass

def do_action_copy_ttl_out(packet, action, groups, dataplane, ctrl_if, 
                           output_now):
    """
    Carry out the copy_ttl_out action
    @param packet The packet to be modified, forwarded, etc
    @param action The copy_ttl_out action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    pass

def do_action_copy_ttl_in(packet, action, groups, dataplane, ctrl_if, 
                          output_now):
    """
    Carry out the copy_ttl_in action
    @param packet The packet to be modified, forwarded, etc
    @param action The copy_ttl_in action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    pass

def do_action_set_mpls_label(packet, action, groups, dataplane, ctrl_if, 
                             output_now):
    """
    Carry out the set_mpls_label action
    @param packet The packet to be modified, forwarded, etc
    @param action The set_mpls_label action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    pass

def do_action_set_mpls_tc(packet, action, groups, dataplane, ctrl_if, 
                          output_now):
    """
    Carry out the set_mpls_tc action
    @param packet The packet to be modified, forwarded, etc
    @param action The set_mpls_tc action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    pass

def do_action_set_mpls_ttl(packet, action, groups, dataplane, ctrl_if, 
                           output_now):
    """
    Carry out the set_mpls_ttl action
    @param packet The packet to be modified, forwarded, etc
    @param action The set_mpls_ttl action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    pass

def do_action_dec_mpls_ttl(packet, action, groups, dataplane, ctrl_if, 
                           output_now):
    """
    Carry out the dec_mpls_ttl action
    @param packet The packet to be modified, forwarded, etc
    @param action The dec_mpls_ttl action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    pass

def do_action_push_vlan(packet, action, groups, dataplane, ctrl_if, 
                        output_now):
    """
    Carry out the push_vlan action
    @param packet The packet to be modified, forwarded, etc
    @param action The push_vlan action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    pass

def do_action_pop_vlan(packet, action, groups, dataplane, ctrl_if, 
                       output_now):
    """
    Carry out the pop_vlan action
    @param packet The packet to be modified, forwarded, etc
    @param action The pop_vlan action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    pass

def do_action_push_mpls(packet, action, groups, dataplane, ctrl_if, 
                        output_now):
    """
    Carry out the push_mpls action
    @param packet The packet to be modified, forwarded, etc
    @param action The push_mpls action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    pass

def do_action_pop_mpls(packet, action, groups, dataplane, ctrl_if, 
                       output_now):
    """
    Carry out the pop_mpls action
    @param packet The packet to be modified, forwarded, etc
    @param action The pop_mpls action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    pass

def do_action_set_queue(packet, action, groups, dataplane, ctrl_if, 
                        output_now):
    """
    Carry out the set_queue action
    @param packet The packet to be modified, forwarded, etc
    @param action The set_queue action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    pass

def do_action_group(packet, action, groups, dataplane, ctrl_if, 
                    output_now):
    """
    Carry out the group action
    @param packet The packet to be modified, forwarded, etc
    @param action The group action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    pass

def do_action_set_nw_ttl(packet, action, groups, dataplane, ctrl_if, 
                         output_now):
    """
    Carry out the set_nw_ttl action
    @param packet The packet to be modified, forwarded, etc
    @param action The set_nw_ttl action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    pass

def do_action_dec_nw_ttl(packet, action, groups, dataplane, ctrl_if, 
                         output_now):
    """
    Carry out the dec_nw_ttl action
    @param packet The packet to be modified, forwarded, etc
    @param action The dec_nw_ttl action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    pass

def do_action_experimenter(packet, action, groups, dataplane, ctrl_if, 
                           output_now):
    """
    Carry out the experimenter action
    @param packet The packet to be modified, forwarded, etc
    @param action The experimenter action obj for parameters
    @param groups Pointer to the group table for group actions
    @param dataplane Pointer to the dataplane obj for fowarding
    @param ctrl_if Controller interface if needed
    """
    pass

