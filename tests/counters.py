"""These tests fall under Conformance Test-Suite (OF-SWITCH-1.0.0 TestCases).
    Refer Documentation -- Detailed testing methodology 
    <Some of test-cases are directly taken from oftest> """

"Test Suite 5 --> Counters"

import logging

import unittest
import random

from oftest import config
import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action
import oftest.parse as parse
import oftest.base_tests as base_tests
import time

from oftest.testutils import *
from time import sleep
from FuncUtils import*


def portQueuesGet(self, queue_stats, port_num):
            result = []
            for qs in queue_stats.stats:
                if qs.port_no != port_num:
                    continue
                result.append(qs.queue_id)
            return result


class FlowCounter1(base_tests.SimpleDataPlane):

    """Verify Packet and Byte counters per flow are
    incremented by no. of packets/bytes received for that flow"""

    def runTest(self):

        logging.info("Running Flow_Counter_1 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state      
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Insert any flow")
        logging.info("Sending N Packets matching the flow")
        logging.info("Verify packet/byte counters increment in accordance")
        
        #Create a Match on Ingress flow
        (pkt,match) = Wildcard_All_Except_Ingress(self,of_ports)
       
        #Send Packets matching the flow 
        num_pkts = 5 
        byte_count = num_pkts*len(str(pkt))
        for pkt_cnt in range(num_pkts):
            self.dataplane.send(of_ports[0],str(pkt))
         
        #Verify Recieved Packets/Bytes Per Flow  
        Verify_FlowStats(self,match,byte_count=byte_count,packet_count=num_pkts)


class FlowCounter2(base_tests.SimpleDataPlane):
    
    """Verify Duration_sec and Duration_nsec counters per flow varies in accordance with the amount of 
    time the flow was alive"""

    def runTest(self):
        
        logging.info("Running Flow_Counter_2 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Insert any flow")
        logging.info("Send Flow_stats request after n sec intervals")
        logging.info("Verify duration_sec and nsec counters are incrementing in accordance with the life of flow")

        #Create a flow with match on ingress_port
        pkt = simple_tcp_packet()
        match = parse.packet_to_flow_match(pkt)
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        self.assertTrue(match is not None, 
                        "Could not generate flow match from pkt")
        match.in_port = of_ports[0]
        flow_mod_msg = message.flow_mod()
        flow_mod_msg.match = match
        flow_mod_msg.cookie = random.randint(0,9007199254740992)
        flow_mod_msg.buffer_id = 0xffffffff
        flow_mod_msg.idle_timeout = 0
        flow_mod_msg.hard_timeout = 0
        act = action.action_output()
        act.port = of_ports[1]
        self.assertTrue(flow_mod_msg.actions.add(act), "Could not add action")
        rv = self.controller.message_send(flow_mod_msg)
        self.assertTrue(rv != -1, "Error installing flow mod")
        self.assertEqual(do_barrier(self.controller), 0, "Barrier failed")
        
        #Create flow_stats request 
        test_timeout = 30
        stat_req = message.flow_stats_request()
        stat_req.match= match
        stat_req.out_port = of_ports[1]
        
        flow_stats_gen_ts =  range (10,test_timeout,10)
        
        for ts in range(0,test_timeout):
            if ts in flow_stats_gen_ts:
                response, pkt = self.controller.transact(stat_req)
                
                self.assertTrue(response is not None,"No response to stats request")
                self.assertTrue(len(response.stats) == 1,"Did not receive flow stats reply")
                
                stat = response.stats[0]
                self.assertTrue(stat.duration_sec == ts,"Flow stats reply incorrect")
                logging.info("Duration of flow is " + str(stat.duration_sec) + str(stat.duration_nsec)) 
            
            sleep(1)



class PortCounter1(base_tests.SimpleDataPlane):

    """Verify that rx_packets counter in the Port_Stats reply , increments when packets are received on a port"""
    
    def runTest(self):

        logging.info("Running Port_Counter_1 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        # Clear Switch State
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Insert a flow with match on ingress_port")
        logging.info("Send N Packets on an ingress_port P ")
        logging.info("Send Port_Stats Request for Port P , verify recieved packets counters are incrementing in accordance")
        
        #Insert a flow with match on all ingress port
        (pkt, match ) = Wildcard_All_Except_Ingress(self,of_ports)

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        port_stats_req = message.port_stats_request()
        port_stats_req.port_no = of_ports[0]   
        response,pkt = self.controller.transact(port_stats_req)
        self.assertTrue(response is not None,"No response received for port stats request") 
        current_counter=0

        for obj in response.stats:
            current_counter += obj.rx_packets
        
        #Send packets matching the flow
        num_pkts = 5
        for pkt_cnt in range(num_pkts):
            self.dataplane.send(of_ports[0],str(pkt))
        
        #Verify recieved packet counters 
        Verify_PortStats1(self,of_ports[0],current_counter,num_pkts)


class PortCounter2(base_tests.SimpleDataPlane):

    """Verify that tx_packets counter in the Port_Stats reply , increments when packets are transmitted by a port"""
      
    def runTest(self):

        logging.info("Running Port_Counter_2 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")


        logging.info("Insert any flow matching on in_port=ingress_port, action output to egress_port T ")
        logging.info("Send N Packets matching the flow on ingress_port P ")
        logging.info("Send Port_Stats Request for Port P , verify transmitted packets counters are incrementing in accordance")
        
        #Insert a flow with match on all ingress port
        (pkt, match ) = Wildcard_All_Except_Ingress(self,of_ports)
        
        # Send Port_Stats request for the ingress port (retrieve current counter state)
        port_stats_req = message.port_stats_request()
        port_stats_req.port_no = of_ports[1]   
        response,pkt = self.controller.transact(port_stats_req)
        self.assertTrue(response is not None,"No response received for port stats request") 
        current_counter=0

        for obj in response.stats:
            current_counter += obj.tx_packets
        
        #Send packets matching the flow
        num_pkts = 5
        for pkt_cnt in range(num_pkts):
            self.dataplane.send(of_ports[0],str(pkt))
        
        #Verify transmitted_packet counters 
        Verify_PortStats2(self,of_ports[1],current_counter,num_pkts)


class PortCounter3(base_tests.SimpleDataPlane):

    """Verify that recieved bytes counter in the Port_Stats reply , increments in accordance with the bytes recieved on a port"""

    def runTest(self):
        
        logging.info("Running Port_Counter_3 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Insert any flow matching on in_port=ingress_port")
        logging.info("Send N Packets matching the flow on ingress_port P ")
        logging.info("Send Port_Stats Request for Port P , verify recieved bytes counters are incrementing in accordance")
        
        #Insert a flow with match on all ingress port
        (pkt, match ) = Wildcard_All_Except_Ingress(self,of_ports)

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        port_stats_req = message.port_stats_request()
        port_stats_req.port_no = of_ports[0]   
        response,pkt = self.controller.transact(port_stats_req)
        self.assertTrue(response is not None,"No response received for port stats request") 
        current_counter=0

        for obj in response.stats:
            current_counter += obj.rx_bytes
         
        #Send packets matching the flow.
        num_pkts = 5
        byte_count = num_pkts*len(str(pkt))
        for pkt_cnt in range(num_pkts):
            self.dataplane.send(of_ports[0],str(pkt))

        
        #Verify recieved_bytes counters 
        Verify_PortStats3(self,of_ports[0],current_counter,byte_count)


class PortCounter4(base_tests.SimpleDataPlane):

    """Verify that trasnsmitted bytes counter in the Port_Stats reply , increments in accordance with the bytes trasmitted by a port"""

    def runTest(self):
        
        logging.info("Running Port_Counter_4 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Insert any flow matching on in_port=ingress_port,action = output to egress_port")
        logging.info("Send N Packets matching the flow on ingress_port P ")
        logging.info("Send Port_Stats Request for Port P , verify trasmitted bytes counters are incrementing in accordance")
        
        #Insert a flow with match on all ingress port
        (pkt, match ) = Wildcard_All_Except_Ingress(self,of_ports)

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        port_stats_req = message.port_stats_request()
        port_stats_req.port_no = of_ports[1]   
        response,pkt = self.controller.transact(port_stats_req)
        self.assertTrue(response is not None,"No response received for port stats request") 
        current_counter=0

        for obj in response.stats:
            current_counter += obj.tx_bytes
        
        #Send packets matching the flow.
        num_pkts = 5
        byte_count = num_pkts*len(str(pkt))
        for pkt_cnt in range(num_pkts):
            self.dataplane.send(of_ports[0],str(pkt))

        
        #Verify trasmitted_bytes counters 
        Verify_PortStats4(self,of_ports[1],current_counter,byte_count)


class TableCounter1(base_tests.SimpleDataPlane):

    """Verify that active_count counter in the Table_Stats reply , increments in accordance with the flows inserted in a table"""

    def runTest(self):

        logging.info("Running Table_Counter_1 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear Switch state
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Insert any flow matching on in_port=ingress_port,action = output to egress_port")
        logging.info("Send Table_Stats, verify active_count counter is incremented in accordance")

        #Insert a flow with match on all ingress port
        (pkt, match ) = Wildcard_All_Except_Ingress(self,of_ports)

        #Generate  Table_Stats
        Verify_TableStats(self,active_entries=1)


class TableCounter2(base_tests.SimpleDataPlane):
    
    """Verify that lookup_count and matched_count counter in the Table_Stats reply 
        increments in accordance with the packets looked up and matched with the flows in the table"""

    def runTest(self):

        logging.info("Running Table_Counter_1 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear Switch state
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Insert any flow matching on in_port=ingress_port,action = output to egress_port")
        logging.info("Send N packets matching the flow, N' packets not matching the flow")
        logging.info("Send Table_Stats, verify lookup_count = N+N' & matched_count=N ")

        # Send Table_Stats reuqest (retrieve current table counters )

        stat_req = message.table_stats_request()
        response, pkt = self.controller.transact(stat_req,
                                                     timeout=5)
        self.assertTrue(response is not None, 
                            "No response to stats request")
        current_lookedup = 0
        current_matched = 0
            
        for obj in response.stats:
            current_lookedup += obj.lookup_count
            current_matched  += obj.matched_count

        #Insert a flow with match on all ingress port
        (pkt, match ) = Wildcard_All_Except_Ingress(self,of_ports)

        #send packet pkt N times (pkt matches the flow)
        num_sends = 5
        for pkt_cnt in range(num_sends):
            self.dataplane.send(of_ports[0],str(pkt))

        #send packet pkt N' (pkt does not match the flow)
        num_sends2 = 5
        for pkt_cnt in range(num_sends):
            self.dataplane.send(of_ports[1],str(pkt))

        #Verify lookup_count and matched_count counters.
        Verify_TableStats1(self,current_lookedup,current_matched,num_sends+num_sends2,num_sends)



class QueueCounter1(base_tests.SimpleDataPlane):

    """Verify that tx_packets in the queue_stats reply increments in accordance with the number of transmitted packets"""
    
    def runTest(self):
        logging.info("Running Queue_Counter_1 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        # Get queue stats from switch (retrieve current state)
        (queue_stats,p) = Get_QueueStats(self,ofp.OFPP_ALL,ofp.OFPQ_ALL)
  
        for idx in range(len(of_ports)):
            ingress_port = of_ports[idx]
            egress_port = of_ports[(idx + 1) % len(of_ports)]

            queue_id = portQueuesGet(self,queue_stats,egress_port)

            for egress_queue_id in queue_id:

                #Clear switch state
                rv = delete_all_flows(self.controller)
                self.assertEqual(rv, 0, "Failed to delete all flows")

                # Get Queue stats for selected egress queue only
                (qs_before,p) = Get_QueueStats(self,egress_port,egress_queue_id)

                #Insert a flow with enqueue action to queues configured on egress_port
                (pkt,match) = Enqueue(self,ingress_port,egress_port,egress_queue_id)
              
                #Send packet on the ingress_port and verify its received on egress_port
                SendPacket(self,pkt,ingress_port,egress_port)
                
                # FIXME: instead of sleeping, keep requesting queue stats until
                # the expected queue counter increases or some large timeout is
                # reached
                time.sleep(2)

                # Get Queue Stats for selected egress queue after packets have been sent
                (qs_after,p) = Get_QueueStats(self,egress_port,egress_queue_id)

                #Verify transmitted packets counter is incremented in accordance
                self.assertEqual(qs_after.stats[0].tx_packets,qs_before.stats[0].tx_packets + 1,"tx_packet count incorrect")
       

class QueueCounter2(base_tests.SimpleDataPlane):

    """Verify that tx_bytes in the queue_stats reply increments in accordance with the number of transmitted bytes"""
    
    def runTest(self):
        logging.info("Running Queue_Counter_2 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        # Get queue stats from switch (retrieve current state)
        (queue_stats,p) = Get_QueueStats(self,ofp.OFPP_ALL,ofp.OFPQ_ALL)
  
        for idx in range(len(of_ports)):
            ingress_port = of_ports[idx]
            egress_port = of_ports[(idx + 1) % len(of_ports)]

            queue_id = portQueuesGet(self,queue_stats,egress_port)

            for egress_queue_id in queue_id:

                #Clear switch state
                rv = delete_all_flows(self.controller)
                self.assertEqual(rv, 0, "Failed to delete all flows")

                # Get Queue stats for selected egress queue only
                (qs_before,p) = Get_QueueStats(self,egress_port,egress_queue_id)

                #Insert a flow with enqueue action to queues configured on egress_port
                (pkt,match) = Enqueue(self,ingress_port,egress_port,egress_queue_id)
              
                #Send packet on the ingress_port and verify its received on egress_port
                SendPacket(self,pkt,ingress_port,egress_port)
                
                # FIXME: instead of sleeping, keep requesting queue stats until
                # the expected queue counter increases or some large timeout is
                # reached
                time.sleep(2)

                # Get Queue Stats for selected egress queue after packets have been sent
                (qs_after,p) = Get_QueueStats(self,egress_port,egress_queue_id)

                #Verify transmitted packets counter is incremented in accordance
                self.assertEqual(qs_after.stats[0].tx_bytes,qs_before.stats[0].tx_bytes + len(str(pkt)),"tx_bytes count incorrect")
       


class RxDrops(base_tests.SimpleDataPlane):

    """Verify that rx_dropped counters in the Port_Stats reply increments in accordance with the packets dropped by RX"""

    def runTest(self):
        
        logging.info("Running Rx_Drops test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has rx_dropped count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        port_stats_req = message.port_stats_request()
        port_stats_req.port_no = of_ports[0]   
        response,pkt = self.controller.transact(port_stats_req)
        self.assertTrue(response is not None,"No response received for port stats request") 
        current_counter=0

        for obj in response.stats:
            current_counter += obj.rx_dropped
        
        logging.info("recieved dropped count is :" + str(current_counter))



class TxDrops(base_tests.SimpleDataPlane):

    """Verify that tx_dropped counters in the Port_Stats reply increments in accordance with the packets dropped by TX"""

    def runTest(self):
        
        logging.info("Running Tx_Drops test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has tx_dropped count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        port_stats_req = message.port_stats_request()
        port_stats_req.port_no = of_ports[0]   
        response,pkt = self.controller.transact(port_stats_req)
        self.assertTrue(response is not None,"No response received for port stats request") 
        current_counter=0

        for obj in response.stats:
            current_counter += obj.tx_dropped
        
        logging.info("Transmitted dropped count is :" + str(current_counter))


class RxErrors(base_tests.SimpleDataPlane):

    """Verify that rx_errors counters in the Port_Stats reply increments in accordance with number of recieved error  
          This is a super-set of more specific receive errors and should be greater than or equal to the sum of all
                  rx_*_err values"""

    def runTest(self):
        
        logging.info("Running Rx_Errors test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has rx_errors count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        port_stats_req = message.port_stats_request()
        port_stats_req.port_no = of_ports[0]   
        response,pkt = self.controller.transact(port_stats_req)
        self.assertTrue(response is not None,"No response received for port stats request") 
        current_counter=0

        for obj in response.stats:
            current_counter += obj.rx_errors
        
        logging.info("Recieve Errors count is :" + str(current_counter))


class TxErrors(base_tests.SimpleDataPlane):

    """Verify that Tx_errors counters in the Port_Stats reply increments in accordance with number of trasmit error"""

    def runTest(self):
        
        logging.info("Running Tx_Errors test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has Tx_errors count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        port_stats_req = message.port_stats_request()
        port_stats_req.port_no = of_ports[0]   
        response,pkt = self.controller.transact(port_stats_req)
        self.assertTrue(response is not None,"No response received for port stats request") 
        current_counter=0

        for obj in response.stats:
            current_counter += obj.tx_errors
        
        logging.info("Trasmit Error count is :" + str(current_counter))


class RxFrameErr(base_tests.SimpleDataPlane):

    """Verify that rx_frm_err counters in the Port_Stats reply increments in accordance with the number of frame alignment errors"""

    def runTest(self):
        
        logging.info("Running Rx_Frame_Err test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has rx_frame_err count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        port_stats_req = message.port_stats_request()
        port_stats_req.port_no = of_ports[0]   
        response,pkt = self.controller.transact(port_stats_req)
        self.assertTrue(response is not None,"No response received for port stats request") 
        current_counter=0

        for obj in response.stats:
            current_counter += obj.rx_frame_err
        
        logging.info("Recieve Frame Errors count is :" + str(current_counter))





class RxOErr(base_tests.SimpleDataPlane):

    """Verify that rx_over_err counters in the Port_Stats reply increments in accordance with the number of with RX overrun"""

    def runTest(self):
        
        logging.info("Running Rx_O_Err test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has rx_over_err count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        port_stats_req = message.port_stats_request()
        port_stats_req.port_no = of_ports[0]   
        response,pkt = self.controller.transact(port_stats_req)
        self.assertTrue(response is not None,"No response received for port stats request") 
        current_counter=0

        for obj in response.stats:
            current_counter += obj.rx_over_err
        
        logging.info("Recieve Overrun Errors  count is :" + str(current_counter))




class RxCrcErr(base_tests.SimpleDataPlane):

    """Verify that rx_crc_err counters in the Port_Stats reply increments in accordance with the number of crc errors"""

    def runTest(self):
        
        logging.info("Running Port_Counter_9 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has rx_crc_err count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        port_stats_req = message.port_stats_request()
        port_stats_req.port_no = of_ports[0]   
        response,pkt = self.controller.transact(port_stats_req)
        self.assertTrue(response is not None,"No response received for port stats request") 
        current_counter=0

        for obj in response.stats:
            current_counter += obj.rx_crc_err
        
        logging.info("Recieve CRC Errors  count is :" + str(current_counter))



class Collisions(base_tests.SimpleDataPlane):

    """Verify that collisons counters in the Port_Stats reply increments in accordance with the collisions encountered by the switch """

    def runTest(self):
        
        logging.info("Running Collisions test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has Collisions count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        port_stats_req = message.port_stats_request()
        port_stats_req.port_no = of_ports[0]   
        response,pkt = self.controller.transact(port_stats_req)
        self.assertTrue(response is not None,"No response received for port stats request") 
        current_counter=0

        for obj in response.stats:
            current_counter += obj.collisions
        
        logging.info("collisions count is :" + str(current_counter))




class QueueCounter3(base_tests.SimpleDataPlane):

    """Verify that tx_errors in the queue_stats reply increments in accordance with the number of packets dropped due to overrun """

    def runTest(self):
        
        logging.info("Running Queue_Counter_3 test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Queue_Stats Request")
        logging.info("Verify reply has Tramitted Overrun errors count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        port_stats_req = message.port_stats_request()
        port_stats_req.port_no = of_ports[0]   
        response,pkt = self.controller.transact(port_stats_req)
        self.assertTrue(response is not None,"No response received for port stats request") 
        current_counter=0

        for obj in response.stats:
            current_counter += obj.tx_errors

        logging.info("Transmit Overrun Error count is :" + str(current_counter))


