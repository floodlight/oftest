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
import logging

import oftest.cstruct as ofp
import oftest.message as message

"""
Action execution functions
"""

def execute_actions(switch, packet, actions):
    """
    Execute the list of actions on the packet
    @param switch The parent switch object
    @param packet The ingress packet on which to execute the actions
    @param actions The list of actions to be applied to the packet

    Actions are executed in whatever order they are passed without
    checking the integrity of this ordering.

    The handler function for an action must have the name
    do_action_<name>; for example do_action_set_dl_dst.
    """
    log = logging.getLogger('execute_actions')
    for action in actions.actions:
        try:
            callable = getattr(packet, action.__class__.__name__)
            packet.logger.debug("Exec action %s" % action.__class__.__name__)
            callable(action, switch)
        except (KeyError),e:
            log.logger.error("Could not execute packet action %s" %
                                str(e.__class__.__name__))


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
    msg.buffer_id = 0xffffffff
    msg.reason = reason
    msg.table_id = table_id
    switch.controller.message_send(msg)

