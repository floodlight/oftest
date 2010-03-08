
import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action
import logging

def delete_all_flows(controller, logger):
    logger.info("Deleting all flows")
    msg = message.flow_mod()
    msg.match.wildcards = ofp.OFPFW_ALL
    msg.command = ofp.OFPFC_DELETE
    msg.buffer_id = 0xffffffff
    return controller.message_send(msg)
    
