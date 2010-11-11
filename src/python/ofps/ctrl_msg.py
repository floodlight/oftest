"""
Functions to handle specific controller messages

The function name must match ctrl_msg_<message_name> where
message_name is from the oftest message list.  For example, 
ctrl_msg_features_request.

@todo Implement these functions
"""

def ctrl_msg_aggregate_stats_reply(switch, msg, rawmsg):
    """
    Process an aggregate_stats_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type aggregate_stats_reply
    @param rawmsg The actual packet received as a string
    """
    print "Received aggregate_stats_reply from controller"

def ctrl_msg_aggregate_stats_request(switch, msg, rawmsg):
    """
    Process an aggregate_stats_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type aggregate_stats_request
    @param rawmsg The actual packet received as a string
    """
    print "Received aggregate_stats_request from controller"

def ctrl_msg_bad_action_error_msg(switch, msg, rawmsg):
    """
    Process a bad_action_error_msg message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type bad_action_error_msg
    @param rawmsg The actual packet received as a string
    """
    print "Received bad_action_error_msg from controller"

def ctrl_msg_bad_request_error_msg(switch, msg, rawmsg):
    """
    Process a bad_request_error_msg message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type bad_request_error_msg
    @param rawmsg The actual packet received as a string
    """
    print "Received bad_request_error_msg from controller"

def ctrl_msg_barrier_reply(switch, msg, rawmsg):
    """
    Process a barrier_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type barrier_reply
    @param rawmsg The actual packet received as a string
    """
    print "Received barrier_reply from controller"

def ctrl_msg_barrier_request(switch, msg, rawmsg):
    """
    Process a barrier_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type barrier_request
    @param rawmsg The actual packet received as a string
    """
    print "Received barrier_request from controller"

def ctrl_msg_desc_stats_reply(switch, msg, rawmsg):
    """
    Process a desc_stats_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type desc_stats_reply
    @param rawmsg The actual packet received as a string
    """
    print "Received desc_stats_reply from controller"

def ctrl_msg_desc_stats_request(switch, msg, rawmsg):
    """
    Process a desc_stats_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type desc_stats_request
    @param rawmsg The actual packet received as a string
    """
    print "Received desc_stats_request from controller"

def ctrl_msg_echo_reply(switch, msg, rawmsg):
    """
    Process an echo_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type echo_reply
    @param rawmsg The actual packet received as a string
    """
    print "Received echo_reply from controller"

def ctrl_msg_echo_request(switch, msg, rawmsg):
    """
    Process an echo_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type echo_request
    @param rawmsg The actual packet received as a string
    """
    print "Received echo_request from controller"

def ctrl_msg_error(switch, msg, rawmsg):
    """
    Process an error message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type error
    @param rawmsg The actual packet received as a string
    """
    print "Received error from controller"

def ctrl_msg_experimenter(switch, msg, rawmsg):
    """
    Process an experimenter message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type experimenter
    @param rawmsg The actual packet received as a string
    """
    print "Received experimenter from controller"

def ctrl_msg_features_reply(switch, msg, rawmsg):
    """
    Process a features_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type features_reply
    @param rawmsg The actual packet received as a string
    """
    print "Received features_reply from controller"

def ctrl_msg_features_request(switch, msg, rawmsg):
    """
    Process a features_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type features_request
    @param rawmsg The actual packet received as a string
    """
    print "Received features_request from controller"

def ctrl_msg_flow_mod(switch, msg, rawmsg):
    """
    Process a flow_mod message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type flow_mod
    @param rawmsg The actual packet received as a string
    """
    
    print "Received flow_mod from controller"

def ctrl_msg_flow_mod_failed_error_msg(switch, msg, rawmsg):
    """
    Process a flow_mod_failed_error_msg message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type flow_mod_failed_error_msg
    @param rawmsg The actual packet received as a string
    """
    print "Received flow_mod_failed_error_msg from controller"

def ctrl_msg_flow_removed(switch, msg, rawmsg):
    """
    Process a flow_removed message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type flow_removed
    @param rawmsg The actual packet received as a string
    """
    print "Received flow_removed from controller"

def ctrl_msg_flow_stats_reply(switch, msg, rawmsg):
    """
    Process a flow_stats_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type flow_stats_reply
    @param rawmsg The actual packet received as a string
    """
    print "Received flow_stats_reply from controller"

def ctrl_msg_flow_stats_request(switch, msg, rawmsg):
    """
    Process a flow_stats_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type flow_stats_request
    @param rawmsg The actual packet received as a string
    """
    print "Received flow_stats_request from controller"

def ctrl_msg_get_config_reply(switch, msg, rawmsg):
    """
    Process a get_config_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type get_config_reply
    @param rawmsg The actual packet received as a string
    """
    print "Received get_config_reply from controller"

def ctrl_msg_get_config_request(switch, msg, rawmsg):
    """
    Process a get_config_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type get_config_request
    @param rawmsg The actual packet received as a string
    """
    print "Received get_config_request from controller"

def ctrl_msg_group_desc_stats_request(switch, msg, rawmsg):
    """
    Process a group_desc_stats_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type group_desc_stats_request
    @param rawmsg The actual packet received as a string
    """
    print "Received group_desc_stats_request from controller"

def ctrl_msg_group_desc_stats_reply(switch, msg, rawmsg):
    """
    Process a group_desc_stats_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type group_desc_stats_reply
    @param rawmsg The actual packet received as a string
    """
    print "Received group_desc_stats_reply from controller"

def ctrl_msg_group_stats_request(switch, msg, rawmsg):
    """
    Process a group_stats_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type group_stats_request
    @param rawmsg The actual packet received as a string
    """
    print "Received group_stats_request from controller"

def ctrl_msg_group_stats_reply(switch, msg, rawmsg):
    """
    Process a group_stats_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type group_stats_reply
    @param rawmsg The actual packet received as a string
    """
    print "Received group_stats_reply from controller"

def ctrl_msg_group_mod(switch, msg, rawmsg):
    """
    Process a group_mod message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type group_mod
    @param rawmsg The actual packet received as a string
    """
    print "Received group_mod from controller"

def ctrl_msg_group_mod_failed_error_msg(switch, msg, rawmsg):
    """
    Process a group_mod_failed_error_msg message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type group_mod_failed_error_msg
    @param rawmsg The actual packet received as a string
    """
    print "Received group_mod_failed_error_msg from controller"

def ctrl_msg_hello(switch, msg, rawmsg):
    """
    Process a hello message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type hello
    @param rawmsg The actual packet received as a string
    """
    print "Received hello from controller"

def ctrl_msg_hello_failed_error_msg(switch, msg, rawmsg):
    """
    Process a hello_failed_error_msg message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type hello_failed_error_msg
    @param rawmsg The actual packet received as a string
    """
    print "Received hello_failed_error_msg from controller"

def ctrl_msg_packet_in(switch, msg, rawmsg):
    """
    Process a packet_in message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type packet_in
    @param rawmsg The actual packet received as a string
    """
    print "Received packet_in from controller"

def ctrl_msg_packet_out(switch, msg, rawmsg):
    """
    Process a packet_out message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type packet_out
    @param rawmsg The actual packet received as a string
    """
    print "Received packet_out from controller"

def ctrl_msg_port_mod(switch, msg, rawmsg):
    """
    Process a port_mod message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type port_mod
    @param rawmsg The actual packet received as a string
    """
    print "Received port_mod from controller"

def ctrl_msg_port_mod_failed_error_msg(switch, msg, rawmsg):
    """
    Process a port_mod_failed_error_msg message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type port_mod_failed_error_msg
    @param rawmsg The actual packet received as a string
    """
    print "Received port_mod_failed_error_msg from controller"

def ctrl_msg_port_stats_reply(switch, msg, rawmsg):
    """
    Process a port_stats_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type port_stats_reply
    @param rawmsg The actual packet received as a string
    """
    print "Received port_stats_reply from controller"

def ctrl_msg_port_stats_request(switch, msg, rawmsg):
    """
    Process a port_stats_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type port_stats_request
    @param rawmsg The actual packet received as a string
    """
    print "Received port_stats_request from controller"

def ctrl_msg_port_status(switch, msg, rawmsg):
    """
    Process a port_status message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type port_status
    @param rawmsg The actual packet received as a string
    """
    print "Received port_status from controller"

def ctrl_msg_queue_get_config_reply(switch, msg, rawmsg):
    """
    Process a queue_get_config_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type queue_get_config_reply
    @param rawmsg The actual packet received as a string
    """
    print "Received queue_get_config_reply from controller"

def ctrl_msg_queue_get_config_request(switch, msg, rawmsg):
    """
    Process a queue_get_config_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type queue_get_config_request
    @param rawmsg The actual packet received as a string
    """
    print "Received queue_get_config_request from controller"

def ctrl_msg_queue_op_failed_error_msg(switch, msg, rawmsg):
    """
    Process a queue_op_failed_error_msg message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type queue_op_failed_error_msg
    @param rawmsg The actual packet received as a string
    """
    print "Received queue_op_failed_error_msg from controller"

def ctrl_msg_queue_stats_reply(switch, msg, rawmsg):
    """
    Process a queue_stats_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type queue_stats_reply
    @param rawmsg The actual packet received as a string
    """
    print "Received queue_stats_reply from controller"

def ctrl_msg_queue_stats_request(switch, msg, rawmsg):
    """
    Process a queue_stats_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type queue_stats_request
    @param rawmsg The actual packet received as a string
    """
    print "Received queue_stats_request from controller"

def ctrl_msg_set_config(switch, msg, rawmsg):
    """
    Process a set_config message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type set_config
    @param rawmsg The actual packet received as a string
    """
    print "Received set_config from controller"

def ctrl_msg_switch_config_failed_error_msg(switch, msg, rawmsg):
    """
    Process a switch_config_failed_error_msg message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type switch_config_failed_error_msg
    @param rawmsg The actual packet received as a string
    """
    print "Received switch_config_failed_error_msg from controller"

def ctrl_msg_table_mod(switch, msg, rawmsg):
    """
    Process a table_mod message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type table_mod
    @param rawmsg The actual packet received as a string
    """
    print "Received table_mod from controller"

def ctrl_msg_table_mod_failed_error_msg(switch, msg, rawmsg):
    """
    Process a table_mod_failed_error_msg message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type table_mod_failed_error_msg
    @param rawmsg The actual packet received as a string
    """
    print "Received table_mod_failed_error_msg from controller"

def ctrl_msg_table_stats_reply(switch, msg, rawmsg):
    """
    Process a table_stats_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type table_stats_reply
    @param rawmsg The actual packet received as a string
    """
    print "Received table_stats_reply from controller"

def ctrl_msg_table_stats_request(switch, msg, rawmsg):
    """
    Process a table_stats_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type table_stats_request
    @param rawmsg The actual packet received as a string
    """
    print "Received table_stats_request from controller"
