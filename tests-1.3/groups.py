# Distributed under the OpenFlow Software License (see LICENSE)
# Copyright (c) 2010 The Board of Trustees of The Leland Stanford Junior University
# Copyright (c) 2012, 2013 Big Switch Networks, Inc.
# Copyright (c) 2012, 2013 CPqD
# Copyright (c) 2012, 2013 Ericsson
"""
Group table test cases.
"""

import logging

from oftest import config
import oftest
import oftest.base_tests as base_tests
import ofp

from oftest.testutils import *

class GroupTest(base_tests.SimpleDataPlane):
    def setUp(self):
        base_tests.SimpleDataPlane.setUp(self)
        delete_all_flows(self.controller)
        delete_all_groups(self.controller)


class GroupAdd(GroupTest):
    """
    A regular group should be added successfully
    """

    def runTest(self):
        port1, = openflow_ports(1)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=0,
            buckets=[
                ofp.bucket(actions=[ofp.action.output(port1)])])

        self.controller.message_send(msg)
        do_barrier(self.controller)

        stats = get_stats(self, ofp.message.group_desc_stats_request())
        self.assertEquals(stats, [
            ofp.group_desc_stats_entry(
                type=msg.group_type,
                group_id=msg.group_id,
                buckets=msg.buckets)])


class GroupAddMaxID(GroupTest):
    """
    A group with ID OFPG_MAX should be added successfully
    """

    def runTest(self):
        port1, = openflow_ports(1)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=ofp.OFPG_MAX,
            buckets=[
                ofp.bucket(actions=[ofp.action.output(port1)])])

        self.controller.message_send(msg)
        do_barrier(self.controller)

        stats = get_stats(self, ofp.message.group_desc_stats_request())
        self.assertEquals(stats, [
            ofp.group_desc_stats_entry(
                type=msg.group_type,
                group_id=msg.group_id,
                buckets=msg.buckets)])


class GroupAddInvalidAction(GroupTest):
    """
    If any action in the buckets is invalid, OFPET_BAD_ACTION/<code> should be returned
    """

    def runTest(self):
        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=0,
            buckets=[
                ofp.bucket(actions=[ofp.action.output(ofp.OFPP_ANY)])])

        response, _ = self.controller.transact(msg)
        self.assertIsInstance(response, ofp.message.error_msg)
        self.assertEquals(response.err_type, ofp.OFPET_BAD_ACTION)
        self.assertEquals(response.code, ofp.OFPBAC_BAD_OUT_PORT)


class GroupAddExisting(GroupTest):
    """
    An addition with existing group id should result in OFPET_GROUP_MOD_FAILED/OFPGMFC_GROUP_EXISTS
    """

    def runTest(self):
        port1, port2, = openflow_ports(2)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=0,
            buckets=[
                ofp.bucket(actions=[ofp.action.output(port1)])])

        self.controller.message_send(msg)
        do_barrier(self.controller)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=0,
            buckets=[
                ofp.bucket(actions=[ofp.action.output(port2)])])

        response, _ = self.controller.transact(msg)
        self.assertIsInstance(response, ofp.message.error_msg)
        self.assertEquals(response.err_type, ofp.OFPET_GROUP_MOD_FAILED)
        self.assertEquals(response.code, ofp.OFPGMFC_GROUP_EXISTS)


class GroupAddInvalidID(GroupTest):
    """
    An addition with invalid group id (reserved) should result in OFPET_GROUP_MOD_FAILED/OFPGMFC_INVALID_GROUP
    """

    def runTest(self):
        port1, = openflow_ports(1)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=ofp.OFPG_ALL,
            buckets=[
                ofp.bucket(actions=[ofp.action.output(port1)])])

        response, _ = self.controller.transact(msg)
        self.assertIsInstance(response, ofp.message.error_msg)
        self.assertEquals(response.err_type, ofp.OFPET_GROUP_MOD_FAILED)
        self.assertEquals(response.code, ofp.OFPGMFC_INVALID_GROUP)


class GroupAddMinimumInvalidID(GroupTest):
    """
    An addition with invalid group id (reserved) should result in OFPET_GROUP_MOD_FAILED/OFPGMFC_INVALID_GROUP
    """

    def runTest(self):
        port1, = openflow_ports(1)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=ofp.OFPG_MAX+1,
            buckets=[
                ofp.bucket(actions=[ofp.action.output(port1)])])

        response, _ = self.controller.transact(msg)
        self.assertIsInstance(response, ofp.message.error_msg)
        self.assertEquals(response.err_type, ofp.OFPET_GROUP_MOD_FAILED)
        self.assertEquals(response.code, ofp.OFPGMFC_INVALID_GROUP)


class GroupModify(GroupTest):
    """
    A regular group modification should be successful
    """

    def runTest(self):
        port1, port2, = openflow_ports(2)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=0,
            buckets=[
                ofp.bucket(actions=[ofp.action.output(port1)])])

        self.controller.message_send(msg)
        do_barrier(self.controller)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_MODIFY,
            group_type=ofp.OFPGT_ALL,
            group_id=0,
            buckets=[
                ofp.bucket(actions=[ofp.action.output(port2)])])

        self.controller.message_send(msg)
        do_barrier(self.controller)

        stats = get_stats(self, ofp.message.group_desc_stats_request())
        self.assertEquals(stats, [
            ofp.group_desc_stats_entry(
                type=msg.group_type,
                group_id=msg.group_id,
                buckets=msg.buckets)])


class GroupModifyNonexisting(GroupTest):
    """
    A modification for a non-existing group should result in OFPET_GROUP_MOD_FAILED/OFPGMFC_UNKNOWN_GROUP
    """

    def runTest(self):
        port1, = openflow_ports(1)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_MODIFY,
            group_type=ofp.OFPGT_ALL,
            group_id=0,
            buckets=[
                ofp.bucket(actions=[ofp.action.output(port1)])])

        response, _ = self.controller.transact(msg)
        self.assertIsInstance(response, ofp.message.error_msg)
        self.assertEquals(response.err_type, ofp.OFPET_GROUP_MOD_FAILED)
        self.assertEquals(response.code, ofp.OFPGMFC_UNKNOWN_GROUP)


class GroupModifyLoop(GroupTest):
    """
    A modification causing loop should result in OFPET_GROUP_MOD_FAILED/OFPGMFC_LOOP
    """

    def runTest(self):
        port1, = openflow_ports(1)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=0,
            buckets=[
                ofp.bucket(actions=[ofp.action.output(port1)])])

        self.controller.message_send(msg)
        do_barrier(self.controller)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=1,
            buckets=[
                ofp.bucket(actions=[ofp.action.group(0)])])

        self.controller.message_send(msg)
        do_barrier(self.controller)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=2,
            buckets=[
                ofp.bucket(actions=[ofp.action.group(1)])])

        self.controller.message_send(msg)
        do_barrier(self.controller)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_MODIFY,
            group_type=ofp.OFPGT_ALL,
            group_id=0,
            buckets=[
                ofp.bucket(actions=[ofp.action.group(2)])])

        response, _ = self.controller.transact(msg)
        self.assertIsInstance(response, ofp.message.error_msg)
        self.assertEquals(response.err_type, ofp.OFPET_GROUP_MOD_FAILED)
        self.assertEquals(response.code, ofp.OFPGMFC_LOOP)


class GroupModifyInvalidID(GroupTest):
    """
    A modification for a reserved group should result in OFPET_GROUP_MOD_FAILED/OFPGMFC_INVALID_GROUP
    """

    def runTest(self):
        port1, = openflow_ports(1)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=ofp.OFPG_ALL,
            buckets=[
                ofp.bucket(actions=[ofp.action.output(port1)])])

        response, _ = self.controller.transact(msg)
        self.assertIsInstance(response, ofp.message.error_msg)
        self.assertEquals(response.err_type, ofp.OFPET_GROUP_MOD_FAILED)
        self.assertEquals(response.code, ofp.OFPGMFC_INVALID_GROUP)


class GroupModifyEmpty(GroupTest):
    """
    A modification for an existing group with no buckets should be accepted
    """

    def runTest(self):
        port1, = openflow_ports(1)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=0,
            buckets=[
                ofp.bucket(actions=[ofp.action.output(port1)])])

        self.controller.message_send(msg)
        do_barrier(self.controller)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_MODIFY,
            group_type=ofp.OFPGT_ALL,
            group_id=0,
            buckets=[])

        self.controller.message_send(msg)
        do_barrier(self.controller)

        stats = get_stats(self, ofp.message.group_desc_stats_request())
        self.assertEquals(stats, [
            ofp.group_desc_stats_entry(
                type=msg.group_type,
                group_id=msg.group_id,
                buckets=msg.buckets)])


class GroupDeleteExisting(GroupTest):
    """
    A deletion for an existing group should remove the group
    """

    def runTest(self):
        port1, = openflow_ports(1)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=0,
            buckets=[
                ofp.bucket(actions=[ofp.action.output(port1)])])

        self.controller.message_send(msg)
        do_barrier(self.controller)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_DELETE,
            group_id=0)

        self.controller.message_send(msg)
        do_barrier(self.controller)

        stats = get_stats(self, ofp.message.group_desc_stats_request())
        self.assertEquals(stats, [])


class GroupDeleteNonexisting(GroupTest):
    """
    A deletion for nonexisting group should result in no error
    """

    def runTest(self):
        msg = ofp.message.group_mod(
            command=ofp.OFPGC_DELETE,
            group_id=0)

        self.controller.message_send(msg)
        do_barrier(self.controller)
        verify_no_errors(self.controller)


class GroupDeleteAll(GroupTest):
    """
    A deletion for OFPG_ALL should remove all groups
    """

    def runTest(self):
        port1, = openflow_ports(1)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=0,
            buckets=[
                ofp.bucket(actions=[ofp.action.output(port1)])])

        self.controller.message_send(msg)
        do_barrier(self.controller)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=1,
            buckets=[
                ofp.bucket(actions=[ofp.action.output(port1)])])

        self.controller.message_send(msg)
        do_barrier(self.controller)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_DELETE,
            group_id=ofp.OFPG_ALL)

        self.controller.message_send(msg)
        do_barrier(self.controller)

        stats = get_stats(self, ofp.message.group_desc_stats_request())
        self.assertEquals(stats, [])


class GroupAddAllWeight(GroupTest):
    """
    An ALL group with weights for buckets should result in OFPET_GROUP_MOD_FAILED, OFPGMFC_INVALID_GROUP
    """

    def runTest(self):
        port1, port2, = openflow_ports(2)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=0,
            buckets=[
                ofp.bucket(weight=1, actions=[ofp.action.output(port1)]),
                ofp.bucket(weight=2, actions=[ofp.action.output(port2)])])

        response, _ = self.controller.transact(msg)
        self.assertIsInstance(response, ofp.message.error_msg)
        self.assertEquals(response.err_type, ofp.OFPET_GROUP_MOD_FAILED)
        self.assertEquals(response.code, ofp.OFPGMFC_INVALID_GROUP)


class GroupAddIndirectWeight(GroupTest):
    """
    An INDIRECT group with weights for buckets should result in OFPET_GROUP_MOD_FAILED, OFPGMFC_INVALID_GROUP
    """

    def runTest(self):
        port1, = openflow_ports(1)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_INDIRECT,
            group_id=0,
            buckets=[
                ofp.bucket(weight=1, actions=[ofp.action.output(port1)])])

        response, _ = self.controller.transact(msg)
        self.assertIsInstance(response, ofp.message.error_msg)
        self.assertEquals(response.err_type, ofp.OFPET_GROUP_MOD_FAILED)
        self.assertEquals(response.code, ofp.OFPGMFC_INVALID_GROUP)


class GroupAddIndirectBuckets(GroupTest):
    """
    An INDIRECT group with <>1 bucket should result in OFPET_GROUP_MOD_FAILED, OFPGMFC_INVALID_GROUP
    """

    def runTest(self):
        port1, port2, = openflow_ports(2)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_INDIRECT,
            group_id=0,
            buckets=[
                ofp.bucket(actions=[ofp.action.output(port1)]),
                ofp.bucket(actions=[ofp.action.output(port2)])])

        response, _ = self.controller.transact(msg)
        self.assertIsInstance(response, ofp.message.error_msg)
        self.assertEquals(response.err_type, ofp.OFPET_GROUP_MOD_FAILED)
        self.assertEquals(response.code, ofp.OFPGMFC_INVALID_GROUP)


class GroupAddSelectNoWeight(GroupTest):
    """
    A SELECT group with ==0 weights should result in OFPET_GROUP_MOD_FAILED, OFPGMFC_INVALID_GROUP
    """

    def runTest(self):
        port1, port2, = openflow_ports(2)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_SELECT,
            group_id=0,
            buckets=[
                ofp.bucket(actions=[ofp.action.output(port1)]),
                ofp.bucket(actions=[ofp.action.output(port2)])])

        response, _ = self.controller.transact(msg)
        self.assertIsInstance(response, ofp.message.error_msg)
        self.assertEquals(response.err_type, ofp.OFPET_GROUP_MOD_FAILED)
        self.assertEquals(response.code, ofp.OFPGMFC_INVALID_GROUP)


class GroupStats(GroupTest):
    """
    A group stats request should return an entry for the specified group
    """

    def runTest(self):
        port1, port2, = openflow_ports(2)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=10,
            buckets=[
                ofp.bucket(actions=[
                    ofp.action.set_field(ofp.oxm.tcp_src(2000)),
                    ofp.action.output(port1)]),
                ofp.bucket(actions=[
                    ofp.action.set_field(ofp.oxm.tcp_src(3000)),
                    ofp.action.output(port2)])])

        self.controller.message_send(msg)
        do_barrier(self.controller)

        request = ofp.message.group_stats_request(group_id=10)
        stats = get_stats(self, request)

        self.assertEquals(len(stats), 1)
        self.assertEquals(stats[0].group_id, 10)
        self.assertEquals(stats[0].ref_count, 0)
        self.assertEquals(stats[0].packet_count, 0)
        self.assertEquals(stats[0].byte_count, 0)
        self.assertEquals(len(stats[0].bucket_stats), 2)


class GroupStatsNonexistent(GroupTest):
    """
    A group stats request for a nonexistent group should return an empty list
    """

    def runTest(self):
        request = ofp.message.group_stats_request(group_id=10)
        stats = get_stats(self, request)
        self.assertEquals(len(stats), 0)


class GroupStatsAll(GroupTest):
    """
    A group stats request with OFPG_ALL should return an entry for each group
    """

    def runTest(self):
        port1, port2, = openflow_ports(2)

        msg0 = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=0,
            buckets=[
                ofp.bucket(actions=[
                    ofp.action.set_field(ofp.oxm.tcp_src(2000)),
                    ofp.action.output(port1)]),
                ofp.bucket(actions=[
                    ofp.action.set_field(ofp.oxm.tcp_src(3000)),
                    ofp.action.output(port2)])])

        self.controller.message_send(msg0)
        do_barrier(self.controller)

        msg1 = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=1,
            buckets=[
                ofp.bucket(actions=[
                    ofp.action.set_field(ofp.oxm.tcp_src(2001)),
                    ofp.action.output(port1)]),
                ofp.bucket(actions=[
                    ofp.action.set_field(ofp.oxm.tcp_src(3001)),
                    ofp.action.output(port2)])])

        self.controller.message_send(msg1)
        do_barrier(self.controller)

        request = ofp.message.group_stats_request(group_id=ofp.OFPG_ALL)
        stats = sorted(get_stats(self, request), key=lambda x: x.group_id)

        self.assertEquals(len(stats), 2)

        self.assertEquals(stats[0].group_id, 0)
        self.assertEquals(stats[0].ref_count, 0)
        self.assertEquals(stats[0].packet_count, 0)
        self.assertEquals(stats[0].byte_count, 0)
        self.assertEquals(len(stats[0].bucket_stats), 2)

        self.assertEquals(stats[1].group_id, 1)
        self.assertEquals(stats[1].ref_count, 0)
        self.assertEquals(stats[1].packet_count, 0)
        self.assertEquals(stats[1].byte_count, 0)
        self.assertEquals(len(stats[1].bucket_stats), 2)


class GroupDescStats(GroupTest):
    """
    A group desc stats request should return the type, id, and buckets for each group
    """

    def runTest(self):
        port1, port2, port3, = openflow_ports(3)

        msg0 = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=0,
            buckets=[
                ofp.bucket(actions=[
                    ofp.action.set_field(ofp.oxm.tcp_src(2000)),
                    ofp.action.output(port1)]),
                ofp.bucket(actions=[
                    ofp.action.set_field(ofp.oxm.tcp_src(3000)),
                    ofp.action.output(port2)]),
                ofp.bucket(actions=[
                    ofp.action.set_field(ofp.oxm.tcp_src(4000)),
                    ofp.action.output(port3)])])

        self.controller.message_send(msg0)
        do_barrier(self.controller)

        msg1 = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_SELECT,
            group_id=1,
            buckets=[
                ofp.bucket(
                    weight=1,
                    actions=[
                        ofp.action.set_field(ofp.oxm.tcp_src(2001)),
                        ofp.action.output(port1)]),
                ofp.bucket(
                    weight=2,
                    actions=[
                        ofp.action.set_field(ofp.oxm.tcp_src(3001)),
                        ofp.action.output(port2)]),
                ofp.bucket(
                    weight=3,
                    actions=[
                        ofp.action.set_field(ofp.oxm.tcp_src(4001)),
                        ofp.action.output(port3)])])

        self.controller.message_send(msg1)
        do_barrier(self.controller)

        msg2 = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_FF,
            group_id=2,
            buckets=[
                ofp.bucket(
                    watch_port=port1,
                    actions=[
                        ofp.action.set_field(ofp.oxm.tcp_src(2002)),
                        ofp.action.output(port1)]),
                ofp.bucket(
                    watch_port=port2,
                    actions=[
                        ofp.action.set_field(ofp.oxm.tcp_src(3002)),
                        ofp.action.output(port2,)]),
                ofp.bucket(
                    watch_port=port3,
                    actions=[
                        ofp.action.set_field(ofp.oxm.tcp_src(4002)),
                        ofp.action.output(port3,)])])

        self.controller.message_send(msg2)
        do_barrier(self.controller)

        request = ofp.message.group_desc_stats_request()
        stats = sorted(get_stats(self, request), key=lambda x: x.group_id)

        self.assertEquals(len(stats), 3)

        self.assertEquals(stats[0].group_id, msg0.group_id)
        self.assertEquals(stats[0].type, msg0.group_type)
        self.assertEquals(stats[0].buckets, msg0.buckets)

        self.assertEquals(stats[1].group_id, msg1.group_id)
        self.assertEquals(stats[1].type, msg1.group_type)
        self.assertEquals(stats[1].buckets, msg1.buckets)

        self.assertEquals(stats[2].group_id, msg2.group_id)
        self.assertEquals(stats[2].type, msg2.group_type)
        self.assertEquals(stats[2].buckets, msg2.buckets)


class GroupFlowSelect(GroupTest):
    """
    A flow stats request qualified on group id should select the correct flows
    """

    def runTest(self):
        port1, = openflow_ports(1)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=1,
            buckets=[])

        self.controller.message_send(msg)
        do_barrier(self.controller)

        msg = ofp.message.group_mod(
            command=ofp.OFPGC_ADD,
            group_type=ofp.OFPGT_ALL,
            group_id=2,
            buckets=[])

        self.controller.message_send(msg)
        do_barrier(self.controller)

        packet_in1 = simple_tcp_packet(tcp_sport=1000)

        flow_add_msg1 = flow_msg_create(
            self,
            packet_in1,
            ing_port=1,
            action_list=[
                ofp.action.group(1),
                ofp.action.output(port1)])

        self.controller.message_send(flow_add_msg1)
        do_barrier(self.controller)

        packet_in2 = simple_tcp_packet(tcp_sport=2000)

        flow_add_msg2 = flow_msg_create(
            self,
            packet_in2,
            ing_port=1,
            action_list=[
                ofp.action.group(2),
                ofp.action.output(port1)])

        self.controller.message_send(flow_add_msg2)
        do_barrier(self.controller)

        packet_in3 = simple_tcp_packet(tcp_sport=3000)

        flow_add_msg3 = flow_msg_create(
            self,
            packet_in3,
            ing_port=1,
            action_list=[
                ofp.action.group(2),
                ofp.action.output(port1)])

        self.controller.message_send(flow_add_msg3)
        do_barrier(self.controller)

        packet_in4 = simple_tcp_packet(tcp_sport=4000)

        flow_add_msg4 = flow_msg_create(
            self,
            packet_in4,
            ing_port=1,
            action_list=[
                ofp.action.output(port1)])

        self.controller.message_send(flow_add_msg4)
        do_barrier(self.controller)

        request = ofp.message.aggregate_stats_request(
            table_id=ofp.OFPTT_ALL,
            out_port=ofp.OFPP_ANY,
            out_group=2)

        response, _ = self.controller.transact(request)

        self.assertEqual(response.flow_count, 2,
                         'Did not match expected flow count')
