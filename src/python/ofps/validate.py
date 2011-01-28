'''
Created on Jan 24, 2011

@author: capveg
'''
import logging

from oftest import cstruct as ofp, packet
from oftest import ofutils
from oftest.cstruct import OFPML_NONE


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

    err = _validate_match(switch, flow_mod, logger)
    if err:
        return err
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
    pass        # always passes

def _validate_action_set_dl_dst(action, switch, flow_mod, logger):
    pass

def _validate_action_set_dl_src(action, switch, flow_mod, logger):
    pass

def _validate_action_set_nw_dst(action, switch, flow_mod, logger):
    pass        # always passes

def _validate_action_set_nw_src(action, switch, flow_mod, logger):
    pass        # always passes

def _validate_action_set_nw_tos(action, switch, flow_mod, logger):
    if _test_nw_tos(action.nw_tos):
        return None
    else:
        return ofutils.of_error_msg_make(ofp.OFPET_BAD_ACTION, 
                                         ofp.OFPBAC_BAD_ARGUMENT, 
                                         flow_mod) 
        
def _validate_action_set_tp_dst(action, switch, flow_mod, logger):
    pass        # always passes

def _validate_action_set_tp_src(action, switch, flow_mod, logger):
    pass        # always passes

def _validate_action_set_vlan_vid(action, switch, flow_mod, logger):
    if _test_vlan_vid(action.vlan_vid):
        return None
    else:
        return ofutils.of_error_msg_make(ofp.OFPET_BAD_ACTION, 
                                         ofp.OFPBAC_BAD_ARGUMENT, 
                                         flow_mod) 
def _validate_action_set_vlan_pcp(action, switch, flow_mod, logger):
    if _test_vlan_pcp(action.vlan_pcp):
        return None
    else:
        return ofutils.of_error_msg_make(ofp.OFPET_BAD_ACTION, 
                                         ofp.OFPBAC_BAD_ARGUMENT, 
                                         flow_mod) 
# mpls
def _validate_action_set_mpls_label(action, switch, flow_mod, logger):
    if _test_mpls_label(action.mpls_label):
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
    if _test_mpls_tc(action.mpls_tc):
        return None
    else:
        return ofutils.of_error_msg_make(ofp.OFPET_BAD_ACTION, 
                                         ofp.OFPBAC_BAD_ARGUMENT, 
                                         flow_mod)
        
###### match
class MatchException(StandardError):
    def __init__(self,of_err):
        self.of_err = of_err
        
def _validate_match(switch, flow_mod, logger):
    match = flow_mod.match
    try:
        _validate_match_mpls(match, flow_mod, logger)
        _validate_match_vlan(match, flow_mod, logger)
    except MatchException, e:
        return e.of_err
    return None             # the success case

def _validate_match_mpls(match, flow_mod, logger):
    mpls_label_specified = (match.wildcards & ofp.OFPFMF_MPLS_LABEL) == 0
    if ( mpls_label_specified and
                not _test_mpls_label(match.mpls_label)):
        logger.error(
            "rejecting broken match: bad mpls label: %x %d" %
            (match.wildcards, match.mpls_label))
        raise MatchException(
                    ofutils.of_error_msg_make(
                            ofp.OFPET_FLOW_MOD_FAILED, 
                            ofp.OFPFMFC_BAD_MATCH, 
                            flow_mod))
    # We only care about the tc value:
    # IF it's not wildcarded and
    #  if mpls_label is wildcarded or not NONE
    #        because if there is no mpls_label, there is no tc
    tc_needs_test = (
            (match.wildcards & ofp.OFPFMF_MPLS_TC) == 0 and
            ( not mpls_label_specified or 
                    match.mpls_label != ofp.OFPML_NONE ))
    if ( tc_needs_test and not _test_mpls_tc(match.mpls_tc)):
        logger.error("rejecting broken match: bad mpls tc")
        raise MatchException(
                    ofutils.of_error_msg_make(
                            ofp.OFPET_FLOW_MOD_FAILED, 
                            ofp.OFPFMFC_BAD_MATCH, 
                            flow_mod))
    return None

def _validate_match_vlan(match, flow_mod, logger):
    vlan_specified = (match.wildcards & ofp.OFPFMF_DL_VLAN) == 0
    if ( vlan_specified and not _test_vlan_vid(match.dl_vlan)):
        logger.error("rejecting broken match: bad vlan: %d" %
                     match.dl_vlan)
        raise MatchException(
                    ofutils.of_error_msg_make(
                            ofp.OFPET_FLOW_MOD_FAILED, 
                            ofp.OFPFMFC_BAD_MATCH, 
                            flow_mod))
    pcp_needs_test = (
            (match.wildcards & ofp.OFPFMF_DL_VLAN_PCP) == 0 and
            (not vlan_specified or match.dl_vlan != ofp.OFPVID_NONE))
    if ( pcp_needs_test and not _test_vlan_pcp(match.dl_vlan_pcp)):
        logger.error("rejecting broken match: bad vlan_pcp")
        raise MatchException(
                    ofutils.of_error_msg_make(
                            ofp.OFPET_FLOW_MOD_FAILED, 
                            ofp.OFPFMFC_BAD_MATCH, 
                            flow_mod))
    return None
########### Actual tests
def _test_mpls_label(mpls_label):
    
    if mpls_label == ofp.OFPML_ANY or mpls_label == OFPML_NONE:
        return True
    if mpls_label < 0 or mpls_label > 0x0fffff:
        return False
    return True

def _test_mpls_tc(mpls_tc):
    if mpls_tc < 0 or mpls_tc >= 8:
        return False
    return True

def _test_vlan_vid(vlan_vid):
    if vlan_vid == ofp.OFPVID_NONE:
        return True
    if vlan_vid < 0 or vlan_vid >= 4096:
        return False
    return True

def _test_vlan_pcp(vlan_pcp):
    if vlan_pcp < 0 or vlan_pcp >= 8:
        return False
    return True

def _test_nw_tos(nw_tos):
    if nw_tos < 0 or nw_tos >= 8:
        return False
    return True
