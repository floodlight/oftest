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
import oftest.cstruct as ofp
import oftest.message as message
import oftest.netutils as netutils

"""
Functions to handle specific controller messages

The function name must match <message_name> where
message_name is from the oftest message list.  For example, 
features_request.

@todo Implement these functions
"""

from exec_actions import execute_actions
from oftest.packet import Packet

def aggregate_stats_reply(switch, msg, rawmsg):
    """
    Process an aggregate_stats_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type aggregate_stats_reply
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received aggregate_stats_reply from controller")

def aggregate_stats_request(switch, msg, rawmsg):
    """
    Process an aggregate_stats_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type aggregate_stats_request
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received aggregate_stats_request from controller")

def bad_action_error_msg(switch, msg, rawmsg):
    """
    Process a bad_action_error_msg message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type bad_action_error_msg
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received bad_action_error_msg from controller")

def bad_request_error_msg(switch, msg, rawmsg):
    """
    Process a bad_request_error_msg message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type bad_request_error_msg
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received bad_request_error_msg from controller")

def barrier_reply(switch, msg, rawmsg):
    """
    Process a barrier_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type barrier_reply
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received barrier_reply from controller")

def barrier_request(switch, msg, rawmsg):
    """
    Process a barrier_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type barrier_request
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received barrier_request from controller")
    b = message.barrier_reply()
    b.header.xid = msg.header.xid
    switch.controller.message_send(b)

def desc_stats_reply(switch, msg, rawmsg):
    """
    Process a desc_stats_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type desc_stats_reply
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received desc_stats_reply from controller")

def desc_stats_request(switch, msg, rawmsg):
    """
    Process a desc_stats_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type desc_stats_request
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received desc_stats_request from controller")

def echo_reply(switch, msg, rawmsg):
    """
    Process an echo_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type echo_reply
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received echo_reply from controller")

def echo_request(switch, msg, rawmsg):
    """
    Process an echo_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type echo_request
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received echo_request from controller")
    msg.header.type = ofp.OFPT_ECHO_REPLY
    switch.controller.message_send(msg, zero_xid=True)

def error(switch, msg, rawmsg):
    """
    Process an error message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type error
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received error from controller")

def experimenter(switch, msg, rawmsg):
    """
    Process an experimenter message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type experimenter
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received experimenter from controller")

def features_reply(switch, msg, rawmsg):
    """
    Process a features_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type features_reply
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received features_reply from controller")

def features_request(switch, msg, rawmsg):
    """
    Process a features_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type features_request
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received features_request from controller")
    rep = message.features_reply()
    rep.header.xid = msg.header.xid
    rep.datapath_id = switch.config.getConfig('datapath_id')
    rep.n_buffers = 10000 #@todo figure out real number of buffers
    rep.n_tables = switch.config.n_tables
    # for now, list some simple things that we will likely (but don't yet) support
    rep.capabilities = ofp.OFPC_FLOW_STATS | ofp.OFPC_PORT_STATS | \
        ofp.OFPC_TABLE_STATS 
    ports = []
    for key, val in switch.config.port_map.iteritems():
        port = ofp.ofp_port()
        port.port_no = key
        port.name = val
        port.max_speed = 9999999
        port.curr_speed = 0
        mac = netutils.get_if_hwaddr(port.name)
        switch.logger.debug("Building features_reply: Found port %s (ind=%d) with mac %x:%x:%x:%x:%x:%x" % ((val, key) + mac))
        port.hw_addr = list(mac)    # stupid frickin' python; need to convert a tuple to a list
        #@todo fill in rest of port configs and stuff
        ports.append(port)
    rep.ports = ports
    switch.controller.message_send(rep)

def flow_mod(switch, msg, rawmsg):
    """
    Process a flow_mod message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type flow_mod
    @param rawmsg The actual packet received as a string
    """
    (rv, _) = switch.pipeline.flow_mod_process(msg, switch.groups)
    switch.logger.debug("Handled flow_mod, result: " + str(rv))
    if rv < 0:
        #@todo Send error message with error code
        pass

def flow_mod_failed_error_msg(switch, msg, rawmsg):
    """
    Process a flow_mod_failed_error_msg message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type flow_mod_failed_error_msg
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received flow_mod_failed_error_msg from controller")

def flow_removed(switch, msg, rawmsg):
    """
    Process a flow_removed message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type flow_removed
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received flow_removed from controller")

def flow_stats_reply(switch, msg, rawmsg):
    """
    Process a flow_stats_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type flow_stats_reply
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received flow_stats_reply from controller")

def flow_stats_request(switch, msg, rawmsg):
    """
    Process a flow_stats_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type flow_stats_request
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received flow_stats_request from controller")
    reply = switch.pipeline.flow_stats_get(msg,switch.groups)
    if not reply : 
        switch.logger.error("Got None reply from switch.pipeline.flow_stats_get(); dropping request")
    else:
        switch.logger.debug("Sending flow_stats_response to controller")
        switch.controller.message_send(reply)

def get_config_reply(switch, msg, rawmsg):
    """
    Process a get_config_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type get_config_reply
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received get_config_reply from controller")

def get_config_request(switch, msg, rawmsg):
    """
    Process a get_config_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type get_config_request
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received get_config_request from controller")

def group_desc_stats_request(switch, msg, rawmsg):
    """
    Process a group_desc_stats_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type group_desc_stats_request
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received group_desc_stats_request from controller")

def group_desc_stats_reply(switch, msg, rawmsg):
    """
    Process a group_desc_stats_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type group_desc_stats_reply
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received group_desc_stats_reply from controller")

def group_stats_request(switch, msg, rawmsg):
    """
    Process a group_stats_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type group_stats_request
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received group_stats_request from controller")

def group_stats_reply(switch, msg, rawmsg):
    """
    Process a group_stats_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type group_stats_reply
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received group_stats_reply from controller")

def group_mod(switch, msg, rawmsg):
    """
    Process a group_mod message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type group_mod
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received group_mod from controller")
    switch.groups.update(msg)

def group_mod_failed_error_msg(switch, msg, rawmsg):
    """
    Process a group_mod_failed_error_msg message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type group_mod_failed_error_msg
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received group_mod_failed_error_msg from controller")

def hello(switch, msg, rawmsg):
    """
    Process a hello message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type hello
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received hello from controller")

def hello_failed_error_msg(switch, msg, rawmsg):
    """
    Process a hello_failed_error_msg message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type hello_failed_error_msg
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received hello_failed_error_msg from controller")

def packet_in(switch, msg, rawmsg):
    """
    Process a packet_in message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type packet_in
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received packet_in from controller")

def packet_out(switch, msg, rawmsg):
    """
    Process a packet_out message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type packet_out
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received packet_out from controller")
    packet = Packet(in_port=msg.in_port, data=msg.data)
    switch.logger.debug("Executing action list")
    print msg.actions.show()
    execute_actions(switch, packet, msg.actions)

def port_mod(switch, msg, rawmsg):
    """
    Process a port_mod message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type port_mod
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received port_mod from controller")

def port_mod_failed_error_msg(switch, msg, rawmsg):
    """
    Process a port_mod_failed_error_msg message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type port_mod_failed_error_msg
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received port_mod_failed_error_msg from controller")

def port_stats_reply(switch, msg, rawmsg):
    """
    Process a port_stats_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type port_stats_reply
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received port_stats_reply from controller")

def port_stats_request(switch, msg, rawmsg):
    """
    Process a port_stats_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type port_stats_request
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received port_stats_request from controller")

def port_status(switch, msg, rawmsg):
    """
    Process a port_status message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type port_status
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received port_status from controller")

def queue_get_config_reply(switch, msg, rawmsg):
    """
    Process a queue_get_config_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type queue_get_config_reply
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received queue_get_config_reply from controller")

def queue_get_config_request(switch, msg, rawmsg):
    """
    Process a queue_get_config_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type queue_get_config_request
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received queue_get_config_request from controller")

def queue_op_failed_error_msg(switch, msg, rawmsg):
    """
    Process a queue_op_failed_error_msg message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type queue_op_failed_error_msg
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received queue_op_failed_error_msg from controller")

def queue_stats_reply(switch, msg, rawmsg):
    """
    Process a queue_stats_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type queue_stats_reply
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received queue_stats_reply from controller")

def queue_stats_request(switch, msg, rawmsg):
    """
    Process a queue_stats_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type queue_stats_request
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received queue_stats_request from controller")

def set_config(switch, msg, rawmsg):
    """
    Process a set_config message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type set_config
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received set_config from controller")

def switch_config_failed_error_msg(switch, msg, rawmsg):
    """
    Process a switch_config_failed_error_msg message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type switch_config_failed_error_msg
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received switch_config_failed_error_msg from controller")

def table_mod(switch, msg, rawmsg):
    """
    Process a table_mod message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type table_mod
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received table_mod from controller")

def table_mod_failed_error_msg(switch, msg, rawmsg):
    """
    Process a table_mod_failed_error_msg message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type table_mod_failed_error_msg
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received table_mod_failed_error_msg from controller")

def table_stats_reply(switch, msg, rawmsg):
    """
    Process a table_stats_reply message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type table_stats_reply
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received table_stats_reply from controller")

def table_stats_request(switch, msg, rawmsg):
    """
    Process a table_stats_request message from the controller
    @param switch The main switch object
    @param msg The parsed message object of type table_stats_request
    @param rawmsg The actual packet received as a string
    """
    switch.logger.debug("Received table_stats_request from controller")
    reply = switch.pipeline.table_stats_get(msg)
    if msg :
        switch.logger.debug("Sending table_stats_reply")
        switch.controller.message_send(reply)
    else:
        switch.logger.debug("Got NONE from pipeline.table_stats_get()!?")
