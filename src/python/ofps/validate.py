'''
Created on Jan 24, 2011

@author: capveg
'''
import logging

from oftest import cstruct as ofp, packet
from oftest import ofutils


def validate_flow_mod(switch, flow_mod):
    """ Sanity check the flow_mods match and actions
    
    Make sure that all of the actions are valid and make
    sense given this match.
    
    @note:  this function is intentionally somewhat naive.  It does
    not consider the current state of the flow_tables or switch config
    before deciding a flow_mod is valid.  This behavior is conformant to
    the spec, per 5.5 in the spec 
    
    @return:  None if no error; else an ofp_error instance to send back to the
      controller 
    """
    logger = logging.getLogger("validate")

    err = None
    for instruction in flow_mod.instructions:
        t = instruction.__class__.__name__
        cmd = "err = _validate_" + \
                "%s(instruction, switch, flow_mod, logger)" % t
        try:
            exec cmd
            if err:
                return err
        except Exception, e:
            logger.error(
                "No validation test for instruction %s:: failed cmd '%s'::%s"  %
                (t, cmd, str(e)))
    return None
            
##### instructions 

def _validate_instruction_apply_actions(instruction, switch, flow_mod, logger):
    """ Sanity check apply actions
    """
    err = None
    for action in instruction.actions: 
        t = action.__class__.__name__
        cmd = "err = _validate_" + \
                "%s(action, switch, flow_mod, logger)" % t
        try:
            exec cmd
            if err:
                return err
        except:
            logger.error(
                "No validation test for action %s:: failed cmd '%s'"  %
                (t, cmd), exc_info=True)       
    return None

def _validate_instruction_goto_table(instruction, switch, flow_mod, logger):
    table_id = instruction.table_id
    if table_id >= 0 and table_id < switch.pipeline.n_tables :
        return None
    else:
        return ofutils.of_error_msg_make(ofp.OFPET_BAD_ACTION,
                                         ofp.OFPBAC_BAD_ARGUMENT, 
                                         flow_mod)

def _validate_instruction_write_actions(instruction, switch, flow_mod, logger):
    pass
def _validate_instruction_write_metadata(instruction, switch, flow_mod, logger):
    pass
def _validate_instruction_experimenter(instruction, switch, flow_mod, logger):
    pass
def _validate_instruction_clear_actions(instruction, switch, flow_mod, logger):
    pass



##### Actions

def _validate_action_output(action, switch, flow_mod, logger):

    if action.port >= ofp.OFPP_MAX or action.port in switch.ports:
        return None         # port is valid
    else:
        logger.error("invalid port %d (0x%x) in action_output" % 
                     (action.port, action.port))
        return ofutils.of_error_msg_make(ofp.OFPET_BAD_ACTION, 
                                     ofp.OFPBAC_BAD_OUT_PORT, 
                                     flow_mod)

def _validate_action_push_vlan(action, switch, flow_mod, logger):
    if (action.ethertype == packet.ETHERTYPE_VLAN or
            action.ethertype == packet.ETHERTYPE_VLAN_QinQ):
        return None
    else: 
        logger.error("invalid ethertype 0x%x in action_push_vlan" 
                            % action.ethertype )
        return ofutils.of_error_msg_make(ofp.OFPET_BAD_ACTION, 
                                     ofp.OFPBAC_BAD_ARGUMENT, 
                                     flow_mod) 
        
        
def _validate_action_pop_vlan(action, switch, flow_mod, logger):
    pass
def _validate_action_set_dl_dst(action, switch, flow_mod, logger):
    pass
def _validate_action_set_dl_src(action, switch, flow_mod, logger):
    pass
def _validate_action_set_nw_dst(action, switch, flow_mod, logger):
    pass
def _validate_action_set_nw_src(action, switch, flow_mod, logger):
    pass
def _validate_action_set_nw_tos(action, switch, flow_mod, logger):
    pass
def _validate_action_set_tp_dst(action, switch, flow_mod, logger):
    pass
def _validate_action_set_tp_src(action, switch, flow_mod, logger):
    pass
def _validate_action_set_vlan_vid(action, switch, flow_mod, logger):
    pass
# mpls
def _validate_action_set_mpls_label(action, switch, flow_mod, logger):
    if (action.mpls_label < 1048576 and action.mpls_label >=0 ):
        return None
    else:
        return ofutils.of_error_msg_make(ofp.OFPET_BAD_ACTION, 
                                         ofp.OFPBAC_BAD_ARGUMENT, 
                                         flow_mod) 
def _validate_action_push_mpls(action, switch, flow_mod, logger):
    if (action.ethertype == packet.ETHERTYPE_MPLS or
            action.ethertype == packet.ETHERTYPE_MPLS_MCAST):
        return None
    else:
        return ofutils.of_error_msg_make(ofp.OFPET_BAD_ACTION, 
                                         ofp.OFPBAC_BAD_ARGUMENT, 
                                         flow_mod)
         
def _validate_action_copy_ttl_out(action, switch, flow_mod, logger):
    pass
def _validate_action_copy_ttl_in(action, switch, flow_mod, logger):
    pass
def _validate_action_set_mpls_ttl(action, switch, flow_mod, logger):
    # noop; 8 bit in openflow, 8 bit in mpls
    pass
def _validate_action_dec_mpls_ttl(action, switch, flow_mod, logger):
    # noop; always works
    pass
def _validate_action_set_mpls_tc(action, switch, flow_mod, logger):
    if (action.mpls_tc < 8 and action.mpls_tc >=0 ):
        return None
    else:
        return ofutils.of_error_msg_make(ofp.OFPET_BAD_ACTION, 
                                         ofp.OFPBAC_BAD_ARGUMENT, 
                                         flow_mod)
        
