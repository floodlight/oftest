"""
Group table test cases.
"""
import logging

from oftest import config
import of12 as ofp
import oftest.oft12.testutils as testutils
import oftest.base_tests as base_tests

def create_group_desc_stats_req():
    # XXX Zoltan: hack, remove if message module is fixed
    m = ofp.message.group_desc_stats_request()

    return m



def create_group_stats_req(group_id = 0):
    m = ofp.message.group_stats_request()
    m.group_id = group_id

    return m



def create_group_mod_msg(command = ofp.OFPGC_ADD, type = ofp.OFPGT_ALL,
               group_id = 0, buckets = []):
    m = ofp.message.group_mod()
    m.command = command
    m.type = type
    m.group_id = group_id
    for b in buckets:
        m.buckets.add(b)

    return m



# XXX Zoltan: watch_port/_group off ?
def create_bucket(weight = 0, watch_port = 0, watch_group = 0, actions=[]):
    b = ofp.bucket.bucket()
    b.weight = weight
    b.watch_port = watch_port
    b.watch_group = watch_group
    for a in actions:
        b.actions.add(a)

    return b



def create_action(**kwargs):
    a = kwargs.get('action')
    if a == ofp.OFPAT_OUTPUT:
        act = ofp.action.action_output()
        act.port = kwargs.get('port', 1)
        return act
    if a == ofp.OFPAT_GROUP:
        act = ofp.action.action_group()
        act.group_id = kwargs.get('group_id', 0)
        return act
    if a == ofp.OFPAT_SET_FIELD:
        port = kwargs.get('tcp_sport', 0)
        field_2b_set = ofp.match.tcp_src(port)
        act = ofp.action.action_set_field()
        act.field = field_2b_set
        return act;



def create_flow_msg(packet = None, in_port = None, match = None, apply_action_list = []):

    apply_inst = ofp.instruction.instruction_apply_actions()

    if apply_action_list is not None:
        for act in apply_action_list:
            apply_inst.actions.add(act)

    request = ofp.message.flow_mod()
    request.match.type = ofp.OFPMT_OXM

    if match is None:
        match = ofp.parse.packet_to_flow_match(packet)
    
    request.match_fields = match
    
    if in_port != None:
        match_port = testutils.oxm_field.in_port(in_port)
        request.match_fields.tlvs.append(match_port)
    request.buffer_id = 0xffffffff
    request.priority = 1000
    
    request.instructions.add(apply_inst)

    return request



class GroupTest(base_tests.SimpleDataPlane):

    def clear_switch(self):
        testutils.delete_all_flows(self.controller, logging)
        testutils.delete_all_groups(self.controller, logging)

    def send_ctrl_exp_noerror(self, msg, log = ''):
        logging.info('Sending message ' + log)
#        logging.debug(msg.show())
        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, 'Error sending!')

        logging.info('Waiting for error messages...')
        (response, raw) = self.controller.poll(ofp.OFPT_ERROR, 1)

        self.assertTrue(response is None, 'Unexpected error message received')

        testutils.do_barrier(self.controller);



    def send_ctrl_exp_error(self, msg, log = '', type = 0, code = 0):
        logging.info('Sending message ' + log)
        logging.debug(msg.show())
        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, 'Error sending!')

        logging.info('Waiting for error messages...')
        (response, raw) = self.controller.poll(ofp.OFPT_ERROR, 1)

        self.assertTrue(response is not None, 
                        'Did not receive an error message')

        self.assertEqual(response.header.type, ofp.OFPT_ERROR,
                         'Did not receive an error message')

        if type != 0:
            self.assertEqual(response.type, type,
                             'Did not receive a ' + str(type) + ' type error message')

        if code != 0:
            self.assertEqual(response.code, code,
                             'Did not receive a ' + str(code) + ' code error message')
        
        testutils.do_barrier(self.controller);



    def send_ctrl_exp_reply(self, msg, resp_type = ofp.OFPT_ERROR, log = ''):
        logging.info('Sending message ' + log)
        logging.debug(msg.show())
        rv = self.controller.message_send(msg)
        self.assertTrue(rv != -1, 'Error sending!')

        logging.info('Waiting for error messages...')
        (response, raw) = self.controller.poll(resp_type, 1)

        self.assertTrue(response is not None, 'Did not receive expected message')

        return response



    def send_data(self, packet, in_port):
        self.logger.debug("Send packet on port " + str(in_port))
        self.dataplane.send(in_port, str(packet))


    def recv_data(self, port, expected = None):
        pkt = testutils.receive_pkt_verify(self, port, expected)
        return pkt

"""
Management
"""

class GroupAdd(GroupTest):
    """
    A regular group should be added successfully (without errors)
    """

    def runTest(self):
        self.clear_switch()

        group_add_msg = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 0, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 1)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg, 'group add')



class GroupAddInvalidAction(GroupTest):
    """
    If any action in the buckets is invalid, OFPET_BAD_ACTION/<code> should be returned
    """

    def runTest(self):
        self.clear_switch()

        group_add_msg = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 0, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= ofp.OFPP_ANY)
            ])
        ])

        self.send_ctrl_exp_error(group_add_msg, 'group add',
                                 ofp.OFPET_BAD_ACTION,
                                 ofp.OFPBAC_BAD_OUT_PORT)



class GroupAddExisting(GroupTest):
    """
    An addition with existing group id should result in OFPET_GROUP_MOD_FAILED/OFPGMFC_GROUP_EXISTS
    """

    def runTest(self):
        self.clear_switch()

        group_add_msg = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 0, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 1)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg, 'group add 1')

        group_mod_msg2 = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 0, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 1)
            ])
        ])

        self.send_ctrl_exp_error(group_add_msg, 'group add 2',
                                 ofp.OFPET_GROUP_MOD_FAILED,
                                 ofp.OFPGMFC_GROUP_EXISTS)



class GroupAddInvalidID(GroupTest):
    """
    An addition with invalid group id (reserved) should result in OFPET_GROUP_MOD_FAILED/OFPGMFC_INVALID_GROUP
    """

    def runTest(self):
        self.clear_switch()

        group_add_msg = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = ofp.OFPG_ALL, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 1)
            ])
        ])

        self.send_ctrl_exp_error(group_add_msg, 'group add',
                                 ofp.OFPET_GROUP_MOD_FAILED,
                                 ofp.OFPGMFC_INVALID_GROUP)



class GroupMod(GroupTest):
    """
    A regular group modification should be successful (no errors)
    """

    def runTest(self):
        self.clear_switch()

        group_add_msg = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 0, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 1)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg, 'group add')

        group_mod_msg = \
        create_group_mod_msg(ofp.OFPGC_MODIFY, ofp.OFPGT_ALL, group_id = 0, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 1)
            ])
        ])

        self.send_ctrl_exp_noerror(group_mod_msg, 'group mod')



class GroupModNonexisting(GroupTest):
    """
    A modification for non-existing group should result in OFPET_GROUP_MOD_FAILED/OFPGMFC_UNKNOWN_GROUP
    """

    def runTest(self):
        self.clear_switch()

        group_add_msg = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 0, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 1)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg, 'group add')

        group_mod_msg = \
        create_group_mod_msg(ofp.OFPGC_MODIFY, ofp.OFPGT_ALL, group_id = 1, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 1)
            ])
        ])

        self.send_ctrl_exp_error(group_mod_msg, 'group mod',
                                 ofp.OFPET_GROUP_MOD_FAILED,
                                 ofp.OFPGMFC_UNKNOWN_GROUP)



class GroupModLoop(GroupTest):
    """
    A modification causing loop should result in OFPET_GROUP_MOD_FAILED/OFPGMFC_LOOP
    """

    def runTest(self):
        self.clear_switch()

        group_add_msg1 = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 0, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 1)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg1, 'group add 1')

        group_add_msg2 = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 1, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_GROUP, group_id= 0)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg2, 'group add 2')

        group_add_msg3 = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 2, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_GROUP, group_id= 0)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg3, 'group add 3')


        group_mod_msg = \
        create_group_mod_msg(ofp.OFPGC_MODIFY, ofp.OFPGT_ALL, group_id = 0, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_GROUP, group_id= 2)
            ])
        ])

        self.send_ctrl_exp_error(group_mod_msg, 'group mod',
                                 ofp.OFPET_GROUP_MOD_FAILED,
                                 ofp.OFPGMFC_LOOP)



class GroupModInvalidID(GroupTest):
    """
    A modification for reserved group should result in OFPET_BAD_ACTION/OFPGMFC_INVALID_GROUP
    """

    def runTest(self):
        self.clear_switch()

        group_mod_msg = \
        create_group_mod_msg(ofp.OFPGC_MODIFY, ofp.OFPGT_ALL, group_id = ofp.OFPG_ALL, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 1)
            ])
        ])

        self.send_ctrl_exp_error(group_mod_msg, 'group mod',
                                 ofp.OFPET_GROUP_MOD_FAILED,
                                 ofp.OFPGMFC_INVALID_GROUP)



class GroupModEmpty(GroupTest):
    """
    A modification for existing group with no buckets should be accepted
    """

    def runTest(self):
        self.clear_switch()

        group_add_msg = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 0, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 1)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg, 'group add')

        group_mod_msg = \
        create_group_mod_msg(ofp.OFPGC_MODIFY, ofp.OFPGT_ALL, group_id = 0, buckets = [
        ])

        self.send_ctrl_exp_noerror(group_mod_msg, 'group mod')



class GroupDelExisting(GroupTest):
    """
    A deletion for existing group should remove the group
    """

    def runTest(self):
        #self.clear_switch()

        group_add_msg = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 10, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 1)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg, 'group add')

        group_del_msg = \
        create_group_mod_msg(ofp.OFPGC_DELETE, ofp.OFPGT_ALL, group_id = 10, buckets = [
        ])

        self.send_ctrl_exp_noerror(group_del_msg, 'group del')

#        self.send_ctrl_exp_noerror(group_add_msg, 'group add')




class GroupDelNonexisting(GroupTest):
    """
    A deletion for nonexisting group should result in no error
    """

    def runTest(self):
        #self.clear_switch()

        group_add_msg = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 0, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 1)
            ])
        ])

#        self.send_ctrl_exp_noerror(group_add_msg, 'group add')

        group_del_msg = \
        create_group_mod_msg(ofp.OFPGC_DELETE, ofp.OFPGT_ALL, group_id = 10, buckets = [
        ])

        self.send_ctrl_exp_noerror(group_del_msg, 'group del')



class GroupDelAll(GroupTest):
    """
    #@todo: A deletion for OFGP_ALL should remove all groups
    """

    def runTest(self):
        self.clear_switch()

        group_add_msg1 = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 1, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 1)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg1, 'group add 1')

        group_add_msg2 = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 2, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 1)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg2, 'group add 2')

        group_del_msg = \
        create_group_mod_msg(ofp.OFPGC_DELETE, group_id = ofp.OFPG_ALL)

        self.send_ctrl_exp_noerror(group_del_msg, 'group del')

#        self.send_ctrl_exp_noerror(group_add_msg1, 'group add 1')
#        self.send_ctrl_exp_noerror(group_add_msg2, 'group add 2')


"""
Management (specific)
"""

class GroupAddAllWeight(GroupTest):
    """
    An ALL group with weights for buckets should result in OFPET_GROUP_MOD_FAILED, OFPGMFC_INVALID_GROUP
    """

    def runTest(self):
        self.clear_switch()

        group_add_msg = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 0, buckets = [
            create_bucket(1, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 2)
            ]),
            create_bucket(2, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 2)
            ])
        ])

        self.send_ctrl_exp_error(group_add_msg, 'group add',
                                 ofp.OFPET_GROUP_MOD_FAILED,
                                 ofp.OFPGMFC_INVALID_GROUP)



class GroupAddIndirectWeight(GroupTest):
    """
    An INDIRECT group with weights for buckets should result in OFPET_GROUP_MOD_FAILED, OFPGMFC_INVALID_GROUP
    """

    def runTest(self):
        self.clear_switch()

        group_add_msg = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_INDIRECT, group_id = 0, buckets = [
            create_bucket(1, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 2)
            ])
        ])

        self.send_ctrl_exp_error(group_add_msg, 'group add',
                                 ofp.OFPET_GROUP_MOD_FAILED,
                                 ofp.OFPGMFC_INVALID_GROUP)



class GroupAddIndirectBuckets(GroupTest):
    """
    An INDIRECT group with <>1 bucket should result in OFPET_GROUP_MOD_FAILED, OFPGMFC_INVALID_GROUP
    """

    def runTest(self):
        self.clear_switch()

        group_add_msg = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_INDIRECT, group_id = 0, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 2)
            ]),
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 2)
            ])
        ])

        self.send_ctrl_exp_error(group_add_msg, 'group add',
                                 ofp.OFPET_GROUP_MOD_FAILED,
                                 ofp.OFPGMFC_INVALID_GROUP)



class GroupAddSelectNoWeight(GroupTest):
    """
    A SELECT group with ==0 weights should result in OFPET_GROUP_MOD_FAILED, OFPGMFC_INVALID_GROUP
    """

    def runTest(self):
        self.clear_switch()

        group_add_msg = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_SELECT, group_id = 0, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 2)
            ]),
            create_bucket(0, 0, 0, [
                create_action(action= ofp.OFPAT_OUTPUT, port= 2)
            ])
        ])

        self.send_ctrl_exp_error(group_add_msg, 'group add',
                                 ofp.OFPET_GROUP_MOD_FAILED,
                                 ofp.OFPGMFC_INVALID_GROUP)


"""
Action
"""

#@todo: A group action with invalid id should result in error
#@todo: A group action for nonexisting group should result in error


"""
Working
"""

class GroupProcEmpty(GroupTest):
    """
    A group with no buckets should not alter the action set of the packet
    """

    def runTest(self):
    
        self.clear_switch()

        group_add_msg = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 1, buckets = [
        ])

        self.send_ctrl_exp_noerror(group_add_msg, 'group add')

        packet_in  = testutils.simple_tcp_packet()
        
        flow_add_msg = \
        create_flow_msg(packet = packet_in, in_port = 1, apply_action_list = [
            create_action(action = ofp.OFPAT_GROUP, group_id = 1)
        ])

        self.send_ctrl_exp_noerror(flow_add_msg, 'flow add')

        self.send_data(packet_in, 1)
        
        self.recv_data(2, None)

class GroupProcSimple(GroupTest):
    """
    A group should apply its actions on packets
    """

    def runTest(self):
#        self.clear_switch()
        testutils.clear_switch(self,config["port_map"],logging)

        group_add_msg = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 1, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 2000),
                create_action(action = ofp.OFPAT_OUTPUT, port = 2)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg, 'group add')

        packet_in  = testutils.simple_tcp_packet(tcp_sport=1000)
        packet_out = testutils.simple_tcp_packet(tcp_sport=2000)
        
        flow_add_msg = \
        testutils.flow_msg_create(self,packet_in,ing_port = 1,action_list = [
            create_action(action = ofp.OFPAT_GROUP, group_id = 1)
        ])
        
        self.send_ctrl_exp_noerror(flow_add_msg, 'flow add')

        self.send_data(packet_in, 1)
        
        self.recv_data(2, packet_out)



class GroupProcMod(GroupTest):
    """
    A modification for existing group should modify the group
    """

    def runTest(self):
        testutils.clear_switch(self,config["port_map"],logging)
#        self.clear_switch()

        group_add_msg = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 1, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 2000),
                create_action(action = ofp.OFPAT_OUTPUT, port = 2)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg, 'group add')

        group_mod_msg = \
        create_group_mod_msg(ofp.OFPGC_MODIFY, ofp.OFPGT_ALL, group_id = 1, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 3000),
                create_action(action = ofp.OFPAT_OUTPUT, port = 2)
            ])
        ])

        self.send_ctrl_exp_noerror(group_mod_msg, 'group mod')


        packet_in  = testutils.simple_tcp_packet(tcp_sport=1000)
        packet_out = testutils.simple_tcp_packet(tcp_sport=3000)
        
        flow_add_msg = \
        testutils.flow_msg_create(self,packet_in,ing_port = 1,action_list = [
            create_action(action = ofp.OFPAT_GROUP, group_id = 1)
        ])
        
        self.send_ctrl_exp_noerror(flow_add_msg, 'flow add')

        self.send_data(packet_in, 1)
        
        self.recv_data(2, packet_out)



class GroupProcChain(GroupTest):
    """
    A group after a group should apply its actions on packets
    """

    def runTest(self):
        self.clear_switch()

        group_add_msg2 = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 2, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 2000),
                create_action(action = ofp.OFPAT_OUTPUT, port = 2)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg2, 'group add')

        group_add_msg1 = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 1, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action = ofp.OFPAT_GROUP, group_id = 2),
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg1, 'group add')

        packet_in  = testutils.simple_tcp_packet(tcp_sport=1000)
        packet_out = testutils.simple_tcp_packet(tcp_sport=2000)
        
        flow_add_msg = \
        testutils.flow_msg_create(self,packet_in,ing_port = 1,action_list = [
            create_action(action = ofp.OFPAT_GROUP, group_id = 1)
        ])
        
        self.send_ctrl_exp_noerror(flow_add_msg, 'flow add')

        self.send_data(packet_in, 1)
        
        self.recv_data(2, packet_out)



"""
Working (specific)
"""

class GroupProcAll(GroupTest):
    """
    An ALL group should use all of its buckets, modifying the resulting packet(s)
    """

    def runTest(self):
        self.clear_switch()

        group_add_msg = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 1, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 2000),
                create_action(action = ofp.OFPAT_OUTPUT, port = 2)
            ]),
            create_bucket(0, 0, 0, [
                create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 3000),
                create_action(action = ofp.OFPAT_OUTPUT, port = 3)
            ]),
            create_bucket(0, 0, 0, [
                create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 4000),
                create_action(action = ofp.OFPAT_OUTPUT, port = 4)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg, 'group add')

        packet_in  = testutils.simple_tcp_packet(tcp_sport=1000)
        packet_out1 = testutils.simple_tcp_packet(tcp_sport=2000)
        packet_out2 = testutils.simple_tcp_packet(tcp_sport=3000)
        packet_out3 = testutils.simple_tcp_packet(tcp_sport=4000)
        
        flow_add_msg = \
        testutils.flow_msg_create(self,packet_in,ing_port = 1,action_list = [
            create_action(action = ofp.OFPAT_GROUP, group_id = 1)
        ])

        self.send_ctrl_exp_noerror(flow_add_msg, 'flow add')

        self.send_data(packet_in, 1)
        
        self.recv_data(2, packet_out1)
        self.recv_data(3, packet_out2)
        self.recv_data(4, packet_out3)



class GroupProcAllChain(GroupTest):
    """
    An ALL group should use all of its buckets, modifying the resulting packet(s)
    """

    def runTest(self):
        self.clear_switch()

        group_add_msg2 = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 2, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 2000),
                create_action(action = ofp.OFPAT_OUTPUT, port = 2)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg2, 'group add 2')

        group_add_msg3 = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 3, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 3000),
                create_action(action = ofp.OFPAT_OUTPUT, port = 3)
            ]),
            create_bucket(0, 0, 0, [
                create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 4000),
                create_action(action = ofp.OFPAT_OUTPUT, port = 4)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg3, 'group add 3')

        group_add_msg1 = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 1, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action = ofp.OFPAT_GROUP, group_id = 2),
            ]),
            create_bucket(0, 0, 0, [
                create_action(action = ofp.OFPAT_GROUP, group_id = 3),
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg1, 'group add 1')

        packet_in  = testutils.simple_tcp_packet(tcp_sport=1000)
        packet_out1 = testutils.simple_tcp_packet(tcp_sport=2000)
        packet_out2 = testutils.simple_tcp_packet(tcp_sport=3000)
        packet_out3 = testutils.simple_tcp_packet(tcp_sport=4000)
        
        flow_add_msg = \
        testutils.flow_msg_create(self,packet_in,ing_port = 1,action_list = [
            create_action(action = ofp.OFPAT_GROUP, group_id = 1)
        ])

        self.send_ctrl_exp_noerror(flow_add_msg, 'flow add')

        self.send_data(packet_in, 1)
        
        self.recv_data(2, packet_out1)
        self.recv_data(3, packet_out2)
        self.recv_data(4, packet_out3)



class GroupProcIndirect(GroupTest):
    """
    An INDIRECT group should use its only bucket
    """

    def runTest(self):
        testutils.clear_switch(self,config["port_map"],logging)
#        self.clear_switch()

        group_add_msg = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_INDIRECT, group_id = 1, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 2000),
                create_action(action = ofp.OFPAT_OUTPUT, port = 2)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg, 'group add')

        packet_in  = testutils.simple_tcp_packet(tcp_sport=1000)
        packet_out = testutils.simple_tcp_packet(tcp_sport=2000)
        
        flow_add_msg = \
        testutils.flow_msg_create(self,packet_in,ing_port = 1,action_list = [
            create_action(action = ofp.OFPAT_GROUP, group_id = 1)
        ])

        self.send_ctrl_exp_noerror(flow_add_msg, 'flow add')

        self.send_data(packet_in, 1)
        
        self.recv_data(2, packet_out)



class GroupProcSelect(GroupTest):
    """
    An ALL group should use all of its buckets, modifying the resulting packet(s)
    """

    def runTest(self):
        testutils.clear_switch(self,config["port_map"],logging)
#        self.clear_switch()

        group_add_msg = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_SELECT, group_id = 1, buckets = [
            create_bucket(1, 0, 0, [
                create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 2000),
                create_action(action = ofp.OFPAT_OUTPUT, port = 2)
            ]),
            create_bucket(1, 0, 0, [
                create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 3000),
                create_action(action = ofp.OFPAT_OUTPUT, port = 3)
            ]),
            create_bucket(1, 0, 0, [
                create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 4000),
                create_action(action = ofp.OFPAT_OUTPUT, port = 4)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg, 'group add')

        packet_in  = testutils.simple_tcp_packet(tcp_sport=1000)
        packet_out1 = testutils.simple_tcp_packet(tcp_sport=2000)
        packet_out2 = testutils.simple_tcp_packet(tcp_sport=3000)
        packet_out3 = testutils.simple_tcp_packet(tcp_sport=4000)
        
        flow_add_msg = \
        testutils.flow_msg_create(self,packet_in,ing_port = 1,action_list = [
            create_action(action = ofp.OFPAT_GROUP, group_id = 1)
        ])

        self.send_ctrl_exp_noerror(flow_add_msg, 'flow add')

        self.send_data(packet_in, 1)
        
        recv1 = self.recv_data(2)
        recv2 = self.recv_data(3)
        recv3 = self.recv_data(4)

        self.assertTrue(((recv1 is not None) or (recv2 is not None) or (recv3 is not None)),
                        "Did not receive a packet")
        
        self.assertTrue(((recv1 is not None) and (recv2 is None) and (recv3 is None)) or \
                        ((recv1 is None) and (recv2 is not None) and (recv3 is None)) or \
                        ((recv1 is None) and (recv2 is None) and (recv3 is not None)),
                        "Received too many packets")

        self.assertTrue(((recv1 is not None) and testutils.pkt_verify(self, recv1, packet_out1)) or \
                        ((recv2 is not None) and testutils.pkt_verify(self, recv2, packet_out2)) or \
                        ((recv3 is not None) and testutils.pkt_verify(self, recv3, packet_out3)),
                        "Received unexpected packet")

#@todo: A FF group should always use its first alive bucket


"""
Statistics
"""

#@todo A regular group added should increase the number of groups and buckets

class GroupStats(GroupTest):
    """
    A packet sent to the group should increase byte/packet counters of group
    """

    def runTest(self):
#        self.clear_switch()
        testutils.clear_switch(self,config["port_map"],logging)
        
        group_add_msg = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 10, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 2000),
                create_action(action = ofp.OFPAT_OUTPUT, port = 2)
            ]),
            create_bucket(0, 0, 0, [
                create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 3000),
                create_action(action = ofp.OFPAT_OUTPUT, port = 3)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg, 'group add')

        packet_in  = testutils.simple_tcp_packet(tcp_sport=1000)
        
        flow_add_msg = \
        testutils.flow_msg_create(self,packet_in,ing_port = 1,action_list = [
            create_action(action = ofp.OFPAT_GROUP, group_id = 10)
        ])

        self.send_ctrl_exp_noerror(flow_add_msg, 'flow add')

        self.send_data(packet_in, 1)
        self.send_data(packet_in, 1)
        self.send_data(packet_in, 1)

        group_stats_req = \
        create_group_stats_req(10)

        response = \
        self.send_ctrl_exp_reply(group_stats_req,
                                 ofp.OFPT_STATS_REPLY, 'group stat')

        exp_len = ofp.OFP_HEADER_BYTES + \
                  ofp.OFP_STATS_REPLY_BYTES + \
                  ofp.OFP_GROUP_STATS_BYTES + \
                  ofp.OFP_BUCKET_COUNTER_BYTES * 2

        self.assertEqual(len(response), exp_len,
                         'Received packet length does not equal expected length')
        # XXX Zoltan: oftest group_stats_req handling needs to be fixed
        #             right now only the expected message length is checked
        #             responses should be checked in Wireshark



class GroupStatsAll(GroupTest):
    """
    A packet sent to the group should increase byte/packet counters of group
    """

    def runTest(self):
#        self.clear_switch()
        testutils.clear_switch(self,config["port_map"],logging)

        group_add_msg1 = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 10, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 2000),
                create_action(action = ofp.OFPAT_OUTPUT, port = 2)
            ]),
            create_bucket(0, 0, 0, [
                create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 3000),
                create_action(action = ofp.OFPAT_OUTPUT, port = 3)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg1, 'group add 1')

        group_add_msg2 = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 20, buckets = [
            create_bucket(0, 0, 0, [
                create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 2000),
                create_action(action = ofp.OFPAT_OUTPUT, port = 2)
            ]),
            create_bucket(0, 0, 0, [
                create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 3000),
                create_action(action = ofp.OFPAT_OUTPUT, port = 3)
            ])
        ])

        self.send_ctrl_exp_noerror(group_add_msg2, 'group add 2')

        packet_in  = testutils.simple_tcp_packet(tcp_sport=1000)
        
        flow_add_msg1 = \
        testutils.flow_msg_create(self,packet_in,ing_port = 1,action_list = [
            create_action(action = ofp.OFPAT_GROUP, group_id = 10)
        ])

        self.send_ctrl_exp_noerror(flow_add_msg1, 'flow add 1')

        flow_add_msg2 = \
        testutils.flow_msg_create(self,packet_in,ing_port = 2,action_list = [
            create_action(action = ofp.OFPAT_GROUP, group_id = 20)
        ])

        self.send_ctrl_exp_noerror(flow_add_msg2, 'flow add 2')

        self.send_data(packet_in, 1)
        self.send_data(packet_in, 1)
        self.send_data(packet_in, 2)
        self.send_data(packet_in, 2)
        self.send_data(packet_in, 2)

        group_stats_req = \
        create_group_stats_req(ofp.OFPG_ALL)

        response = \
        self.send_ctrl_exp_reply(group_stats_req,
                                 ofp.OFPT_STATS_REPLY, 'group stat')

        exp_len = ofp.OFP_HEADER_BYTES + \
                  ofp.OFP_STATS_REPLY_BYTES + \
                  ofp.OFP_GROUP_STATS_BYTES + \
                  ofp.OFP_BUCKET_COUNTER_BYTES * 2 + \
                  ofp.OFP_GROUP_STATS_BYTES + \
                  ofp.OFP_BUCKET_COUNTER_BYTES * 2

        self.assertEqual(len(response), exp_len,
                         'Received packet length does not equal expected length')
        # XXX Zoltan: oftest group_stats_req handling needs to be fixed
        #             right now only the expected message length is checked
        #             responses should be checked in Wireshark



class GroupDescStats(GroupTest):
    """
    Desc stats of a group should work
    """

    def runTest(self):
        self.clear_switch()

        b1 = create_bucket(0, 0, 0, [
                 create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 2000),
                 create_action(action = ofp.OFPAT_OUTPUT, port = 2)
            ])
        b2 =  create_bucket(0, 0, 0, [
                  create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 3000),
                  create_action(action = ofp.OFPAT_OUTPUT, port = 3)
            ])
        b3 = create_bucket(0, 0, 0, [
                 create_action(action = ofp.OFPAT_SET_FIELD, tcp_sport = 4000),
                 create_action(action = ofp.OFPAT_OUTPUT, port = 4)
            ])

        group_add_msg = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 10, buckets = [b1, b2, b3])

        self.send_ctrl_exp_noerror(group_add_msg, 'group add')

        group_desc_stats_req = \
        create_group_desc_stats_req()

        response = \
        self.send_ctrl_exp_reply(group_desc_stats_req,
                                 ofp.OFPT_STATS_REPLY, 'group desc stat')

        exp_len = ofp.OFP_HEADER_BYTES + \
                  ofp.OFP_STATS_REPLY_BYTES + \
                  ofp.OFP_GROUP_DESC_STATS_BYTES + \
                  len(b1) + len(b2) + len(b3)

        self.assertEqual(len(response), exp_len,
                         'Received packet length does not equal expected length')
        # XXX Zoltan: oftest group_stats_req handling needs to be fixed
        #             right now only the expected message length is checked
        #             responses should be checked in Wireshark


#@todo: A flow added with group action should increase the ref counter of the ref. group
#@todo: A flow removed with group action should decrease the ref counter of the ref. group
#@todo: A group added with group action should increase the ref counter of the ref. group
#@todo: A group removed with group action should decrease the ref counter of the ref. group


"""
Flows
"""

#@todo: A deletion for existing group should remove flows referring to that group
#@todo: A flow added referencing a nonexisting group should return an error

"""
Flow select
"""

class GroupFlowSelect(GroupTest):
    """
    A group action select with group id should select the correct flows only
    """

    def runTest(self):
        self.clear_switch()

        group_add_msg1 = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 1, buckets = [])

        self.send_ctrl_exp_noerror(group_add_msg1, 'group add 1')

        group_add_msg2 = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 2, buckets = [])

        self.send_ctrl_exp_noerror(group_add_msg2, 'group add 2')

        packet_in1 = testutils.simple_tcp_packet(tcp_sport=1000)
        
        flow_add_msg1 = \
        testutils.flow_msg_create(self,packet_in1,ing_port = 1,action_list = [
            create_action(action = ofp.OFPAT_GROUP, group_id = 1),
            create_action(action = ofp.OFPAT_OUTPUT, port = 2)
        ])

        self.send_ctrl_exp_noerror(flow_add_msg1, 'flow add 1')

        packet_in2 = testutils.simple_tcp_packet(tcp_sport=2000)

        flow_add_msg2 = \
        testutils.flow_msg_create(self,packet_in2,ing_port = 1,action_list = [
            create_action(action = ofp.OFPAT_GROUP, group_id = 2),
            create_action(action = ofp.OFPAT_OUTPUT, port = 2)
        ])

        self.send_ctrl_exp_noerror(flow_add_msg2, 'flow add 2')

        packet_in3 = testutils.simple_tcp_packet(tcp_sport=3000)

        flow_add_msg3 = \
        testutils.flow_msg_create(self,packet_in3,ing_port = 1,action_list = [
            create_action(action = ofp.OFPAT_GROUP, group_id = 2),
            create_action(action = ofp.OFPAT_OUTPUT, port = 2)
        ])

        self.send_ctrl_exp_noerror(flow_add_msg3, 'flow add 3')

        packet_in4 = testutils.simple_tcp_packet(tcp_sport=4000)

        flow_add_msg4 = \
        testutils.flow_msg_create(self,packet_in4,ing_port = 1,action_list = [
            create_action(action = ofp.OFPAT_OUTPUT, port = 2)
        ])

        self.send_ctrl_exp_noerror(flow_add_msg4, 'flow add 4')

        aggr_stat_req = ofp.message.aggregate_stats_request()
        aggr_stat_req.table_id = 0xff
        aggr_stat_req.out_port = ofp.OFPP_ANY
        aggr_stat_req.out_group = 2

        response = \
        self.send_ctrl_exp_reply(aggr_stat_req,
                                 ofp.OFPT_STATS_REPLY, 'aggr stat')

        self.assertEqual(response.stats[0].flow_count, 2,
                         'Did not match expected flow count')

class GroupFlowSelectAll(GroupTest):
    """
    A group action select with OFPG_ALL should ignore output group action
    """

    def runTest(self):
        self.clear_switch()

        group_add_msg1 = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 1, buckets = [])

        self.send_ctrl_exp_noerror(group_add_msg1, 'group add 1')

        group_add_msg2 = \
        create_group_mod_msg(ofp.OFPGC_ADD, ofp.OFPGT_ALL, group_id = 2, buckets = [])

        self.send_ctrl_exp_noerror(group_add_msg2, 'group add 2')

        packet_in1 = testutils.simple_tcp_packet(tcp_sport=1000)
        
        flow_add_msg1 = \
        testutils.flow_msg_create(self,packet_in1,ing_port = 1,action_list = [
            create_action(action = ofp.OFPAT_GROUP, group_id = 1),
            create_action(action = ofp.OFPAT_OUTPUT, port = 2)
        ])

        self.send_ctrl_exp_noerror(flow_add_msg1, 'flow add 1')

        packet_in2 = testutils.simple_tcp_packet(tcp_sport=2000)

        flow_add_msg2 = \
        testutils.flow_msg_create(self,packet_in2,ing_port = 1,action_list = [
            create_action(action = ofp.OFPAT_GROUP, group_id = 2),
            create_action(action = ofp.OFPAT_OUTPUT, port = 2)
        ])

        self.send_ctrl_exp_noerror(flow_add_msg2, 'flow add 2')

        packet_in3 = testutils.simple_tcp_packet(tcp_sport=3000)

        flow_add_msg3 = \
        testutils.flow_msg_create(self,packet_in3,ing_port = 1,action_list = [
            create_action(action = ofp.OFPAT_GROUP, group_id = 2),
            create_action(action = ofp.OFPAT_OUTPUT, port = 2)
        ])

        self.send_ctrl_exp_noerror(flow_add_msg3, 'flow add 3')

        packet_in4 = testutils.simple_tcp_packet(tcp_sport=4000)

        flow_add_msg4 = \
        testutils.flow_msg_create(self,packet_in4,ing_port = 1,action_list = [
            create_action(action = ofp.OFPAT_OUTPUT, port = 2)
        ])

        self.send_ctrl_exp_noerror(flow_add_msg4, 'flow add 4')

        aggr_stat_req = ofp.message.aggregate_stats_request()
        aggr_stat_req.table_id = 0xff
        aggr_stat_req.out_port = ofp.OFPP_ANY
        aggr_stat_req.out_group = ofp.OFPG_ANY

        response = \
        self.send_ctrl_exp_reply(aggr_stat_req,
                                 ofp.OFPT_STATS_REPLY, 'group desc stat')

        self.assertEqual(response.stats[0].flow_count, 4,
                         'Did not match expected flow count')




if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test_spec=basic"
