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

from oftest.oflog import *
from oftest.testutils import *
from time import sleep
from FuncUtils import*


def port_queues_get(self, queue_stats, port_num):
            result = []
            for qs in queue_stats.stats:
                if qs.port_no != port_num:
                    continue
                result.append(qs.queue_id)
            return result


class Grp60No10(base_tests.SimpleDataPlane):

    """Verify Packet counters per flow are
    incremented by no. of packets received for that flow"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp60No10 PktPerFlow test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state      
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

       
        #Create a Match on Ingress flow
        logging.info("Installing a flow entry")
        (pkt,match) = wildcard_all_except_ingress(self,of_ports)
       
        #Send Packets matching the flow 
        logging.info("Sending 5 packets matching the flow entry")
        num_pkts = 5 
        for pkt_cnt in range(num_pkts):
            self.dataplane.send(of_ports[0],str(pkt))
         
        #Verify Recieved Packets/Bytes Per Flow  
        logging.info("Expected packet count :" +str(num_pkts))
        verify_flowstats(self,match,packet_count=num_pkts)
        logging.info("Packet counter incremented correctly")

class Grp60No20(base_tests.SimpleDataPlane):

    """Verify Byte counters per flow are
    incremented by no. of  bytes received for that flow"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp60No20 BytPerFlow test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state      
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Installing a flow entry")
           

        sleep(2)
        
        #Create a Match on Ingress flow
        #(pkt,match) = wildcard_all_except_ingress(self,of_ports)
        (pkt,match) = exact_match(self,of_ports)

        #Send Packets matching the flow 
        logging.info("Sending 5 packets matching the flow entry")
        num_pkts = 5
        # +4 bytes include ethernet frame crc. Not all devices count the
        # crc, so expected byte count may also be
        # byte_count - (num_packets * 4).
        byte_count = num_pkts*(len(str(pkt))+4)
        for pkt_cnt in range(num_pkts):
            self.dataplane.send(of_ports[0],str(pkt))

        logging.info("expected byte count:"+str(byte_count))
        #Verify Recieved Packets/Bytes Per Flow  
        verify_flowstats(self,match,byte_count=byte_count)
        logging.info("Byte counter incremented correctly")

class Grp60No30(base_tests.SimpleDataPlane):
    
    """Verify Duration_sec and Duration_nsec counters per flow varies in accordance with the amount of 
    time the flow was alive"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp60No30 DurationPerFlow test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Installing a flow entry")
        #Create a flow with match on ingress_port
        (pkt,match) = wildcard_all_except_ingress(self,of_ports)
    
        #Create flow_stats request 
        test_timeout = 30
        stat_req = message.flow_stats_request()
        stat_req.match= match
        stat_req.table_id = 0xff
        stat_req.out_port = ofp.OFPP_NONE
        
        flow_stats_gen_ts =  range (10,test_timeout,10)
        
        for ts in range(0,test_timeout):
            if ts in flow_stats_gen_ts:
                logging.info("Sending a flow stats request")
                response, pkt = self.controller.transact(stat_req)
                
                self.assertTrue(response is not None,"No response to stats request")
                self.assertTrue(len(response.stats) == 1,"Did not receive flow stats reply")
                
                stat = response.stats[0]
                self.assertTrue(stat.duration_sec == ts,"Flow stats reply incorrect")
                logging.info("Duration of flow is " + str(stat.duration_sec) + str(stat.duration_nsec)) 
            
            sleep(1)


class Grp60No40(base_tests.SimpleDataPlane):    
    '''
    Verify Duration_nsec counters per flow varies in accordance with
    the amount of time the flow was alive.
    '''

    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp60No40 Duration (nsecs).")
        dataplane_ports = config["port_map"].keys()
        dataplane_ports.sort()
        self.assertTrue(len(dataplane_ports) > 1, "Not enough ports for test.")
        
        logging.info("Clearing switch state...")
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows.")

        logging.info("Installing flow entry that matches on in_port.")
        (pkt,match) = wildcard_all_except_ingress(self, dataplane_ports)

        req = message.flow_stats_request()
        req.match= match
        req.table_id = 0xff
        req.out_port = ofp.OFPP_NONE

        duration_verifications = 5
        previous_duration = (-1, -1)
        for v in range(0, duration_verifications):
            logging.info("Sending ofp_stats_request of type ofp.OFPST_FLOW")
            res, pkt = self.controller.transact(req)
            self.assertTrue(res is not None, "No ofp_stats_reply message received in response to ofp_stats_request.")
            self.assertTrue(res.type == ofp.OFPST_FLOW, "Expected ofp_stats_reply of type ofp.OFPST_FLOW, got {0}".format(res.type))
            self.assertTrue(len(res.stats) == 1, "Received {0} ofp_flow_stats in the ofp_stats_reply message, but expected exactly 1".format(len(res.stats)))

            logging.info("Comparing duration in nsecs from ofp_flow_stats to previous duration in nsecs.")
            duration = (res.stats[0].duration_sec, res.stats[0].duration_nsec)
            if duration[1] < previous_duration[1]:
                self.assertGreater(duration[0], previous_duration[0], "Duration in nsecs was less than previous duration in nsecs, but the duration in secs was not greater than the previous duration in secs.")
            else:
                # In the case that a switch can't report in
                # millisecond granularity, we expect
                # duration_nsec to be reported as 0xffffffff.
                if duration[1] == previous_duration[1] and duration[1] == 4294967295:
                    logging.info("Duration in nsec is not supported. Reported as -1 or 0xffffffff")
                    return
                self.assertNotEqual(duration[1], previous_duration[1], "ofp_flow_stats.duration_nsec {0} was the same as the previous duration_nsec {1}.".format(duration, previous_duration))
            previous_duration = duration
            time.sleep(1.5)


class Grp60No50(base_tests.SimpleDataPlane):

    """Verify that rx_packets counter in the Port_Stats reply
        increments when packets are received on a port"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp60No50 RxPktPerPort test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        # Clear Switch State
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        sleep(2)
        
        #Insert a flow with match on all ingress port
        logging.info("Insert a flow with match on ingress_port")
        (pkt, match ) = wildcard_all_except_ingress(self,of_ports)

        # Send Port_Stats request for the ingress port (retrieve old counter state)
        logging.info("Sending a port stats request to retrieve initial counter values")
        (counter) = get_portstats(self,of_ports[0])

        # Send packets matching the flow
        logging.info("Sending 5 packets matching the flow entry")
        num_pkts = 5 
        for pkt_cnt in range(num_pkts):
            self.dataplane.send(of_ports[0],str(pkt))

        pkts = num_pkts+counter[0]
        #Verify recieved packet counters 
        logging.info("Verifying whether the rx_packet counter has been incremented correctly")
        verify_portstats(self,of_ports[0],rx_packets=pkts)

class Grp60No60(base_tests.SimpleDataPlane):

    """Verify that tx_packets counter in the Port_Stats reply , increments when packets are transmitted by a port"""
    @wireshark_capture  
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp60No60 TxPktPerPort test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Insert any flow matching on in_port=ingress_port, action output to egress_port T ")
        #Insert a flow with match on all ingress port
        (pkt,match) = wildcard_all_except_ingress(self,of_ports)
        
        # Send Port_Stats request for the ingress port (retrieve old counter state)
        logging.info("Sending Port stats request to retreive initial counter values")
        (counter) = get_portstats(self,of_ports[1])
        
        #Send packets matching the flow
        logging.info("Sending 5 packets matching the flow entry")
        num_pkts = 5
        for pkt_cnt in range(num_pkts):
            self.dataplane.send(of_ports[0],str(pkt))

        pkts = num_pkts+counter[1]
        
        #Verify transmitted_packet counters 
        logging.info("Verifying whether the tx_packet counter has been incremented correctly")
        verify_portstats(self,of_ports[1],tx_packets=pkts)



class Grp60No70(base_tests.SimpleDataPlane):

    """Verify that recieved bytes counter in the Port_Stats reply , increments in accordance with the bytes recieved on a port"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp60No70 RxBytPerPort test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        sleep(2)

        logging.info("Insert any flow matching on in_port=ingress_port")
        #Insert a flow with match on all ingress port
        (pkt, match ) = wildcard_all_except_ingress(self,of_ports)

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        logging.info("Sending port stats request to  retreive initial counter values")
        (counter) = get_portstats(self,of_ports[0])
           
        #Send packets matching the flow.
        logging.info("Sending 5 packets matching the flow entry")
        num_pkts = 5
        byte_count = num_pkts*(len(str(pkt))+4)
        for pkt_cnt in range(num_pkts):
            self.dataplane.send(of_ports[0],str(pkt))

        byt_count = byte_count+counter[2]
        

        #Verify recieved_bytes counters 
        logging.info("Verifying whether the rx_bytes counter has been incremented correctly")
        verify_portstats(self,of_ports[0],rx_byte=byt_count)


class Grp60No80(base_tests.SimpleDataPlane):

    """Verify that trasnsmitted bytes counter in the Port_Stats reply , increments in accordance with the bytes trasmitted by a port"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp60No80 TxBytPerPort test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        sleep(2)

        logging.info("Insert any flow matching on in_port=ingress_port,action = output to egress_port T")
        #Insert a flow with match on all ingress port
        (pkt, match ) = wildcard_all_except_ingress(self,of_ports)

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        logging.info("Sending a port stats request to retreive initial counter values")
        (counter) = get_portstats(self,of_ports[1])
        
        #Send packets matching the flow.
        logging.info("Sending 5 packets matching the flow entry")
        num_pkts = 5
        byte_count = num_pkts*(len(str(pkt))+4)
        for pkt_cnt in range(num_pkts):
            self.dataplane.send(of_ports[0],str(pkt))

        byt_count = byte_count+counter[3]
        
        #Verify trasmitted_bytes counters 
        logging.info("Verifying whether the tx_bytes counter has been incremented correctly")
        verify_portstats(self,of_ports[1],tx_byte=byt_count)


class Grp60No90(base_tests.SimpleDataPlane):

    """Verify that rx_dropped counters in the Port_Stats reply increments in accordance with the packets dropped by RX"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp60No90 Rx_Drops test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has rx_dropped count")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        (counter) = get_portstats(self,of_ports[0])

        rx_drp = counter[4]
        logging.info("recieved dropped count is :" + str(rx_drp))


class Grp60No100(base_tests.SimpleDataPlane):

    """Verify that tx_dropped counters in the Port_Stats reply increments in accordance with the packets dropped by TX"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp60No100 Tx_Drops test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has tx_dropped count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        (counter) = get_portstats(self,of_ports[1])
        
        tx_drp = counter[5]
        logging.info("Transmitted dropped count is :" + str(tx_drp))


class Grp60No110(base_tests.SimpleDataPlane):

    """Verify that rx_errors counters in the Port_Stats reply increments in accordance with number of recieved error  
          This is a super-set of more specific receive errors and should be greater than or equal to the sum of all
                  rx_*_err values"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp60No110 Rx_Errors test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has rx_errors count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        (counter) = get_portstats(self,of_ports[0])

        rx_err = counter[6]    
        logging.info("Recieve Errors count is :" + str(rx_err))


class Grp60No120(base_tests.SimpleDataPlane):

    """Verify that Tx_errors counters in the Port_Stats reply increments in accordance with number of trasmit error"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp60No120 Tx_Errors test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has Tx_errors count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        (counter) = get_portstats(self,of_ports[0])
        
        tx_err = counter[7]
        logging.info("Trasmit Error count is :" + str(tx_err))


class Grp60No130(base_tests.SimpleDataPlane):

    """Verify that rx_frm_err counters in the Port_Stats reply increments in accordance with the number of frame alignment errors"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp60No130 Rx_Frame_Err test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has rx_frame_err count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        (counter) = get_portstats(self,of_ports[0])
        
        rx_fr_err = counter[8]
        logging.info("Recieve Frame Errors count is :" + str(rx_fr_err))



class Grp60No140(base_tests.SimpleDataPlane):

    """Verify that rx_over_err counters in the Port_Stats reply increments in accordance with the number of with RX overrun"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp60No140 Rx_O_Err test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has rx_over_err count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        (counter) = get_portstats(self,of_ports[0])
        
        rx_over_err = counter[9]
        logging.info("Recieve Overrun Errors  count is :" + str(rx_over_err))


class Grp60No150(base_tests.SimpleDataPlane):

    """Verify that rx_crc_err counters in the Port_Stats reply increments in accordance with the number of crc errors"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp60No150 crc_error test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has rx_crc_err count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        (counter) = get_portstats(self,of_ports[0])

        rx_crc_err = counter[10]   
        logging.info("Recieve CRC Errors  count is :" + str(rx_crc_err))


class Grp60No160(base_tests.SimpleDataPlane):

    """Verify that collisons counters in the Port_Stats reply increments in accordance with the collisions encountered by the switch """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp60No160 Collisions test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has Collisions count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        (counter) = get_portstats(self,of_ports[0])

        collisions = counter[11]
        logging.info("collisions count is :" + str(collisions))


class Grp60No170(base_tests.SimpleDataPlane):

    """Verify that tx_packets in the queue_stats reply increments in accordance with the number of transmitted packets"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp60No170 TxPktPerQueue test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        # Get queue stats from switch (retrieve current state)
        (queue_stats,p) = get_queuestats(self,ofp.OFPP_ALL,ofp.OFPQ_ALL)
  
        for idx in range(len(of_ports)):
            ingress_port = of_ports[idx]
            egress_port = of_ports[(idx + 1) % len(of_ports)]

            queue_id = port_queues_get(self,queue_stats,egress_port)

            for egress_queue_id in queue_id:

                #Clear switch state
                rv = delete_all_flows(self.controller)
                self.assertEqual(rv, 0, "Failed to delete all flows")

                # Get Queue stats for selected egress queue only
                logging.info("Retreiving queue stats for selected egress queue only")
                (qs_before,p) = get_queuestats(self,egress_port,egress_queue_id)

                #Insert a flow with enqueue action to queues configured on egress_port
                logging.info("Installing a flow entry with enqueue action configured on egress port")
                (pkt,match) = enqueue(self,ingress_port,egress_port,egress_queue_id)
              
                #Send packet on the ingress_port and verify its received on egress_port
                logging.info("Sending a packet on the ingress port and verifying the packet is received on the egress port")
                send_packet(self,pkt,ingress_port,egress_port)
                
                expected_packets = qs_before.stats[0].tx_packets+1
                logging.info("Verifying whether the tx packets in queue stats has been incremented correctly")
                verify_queuestats(self,egress_port,egress_queue_id,expect_packet=expected_packets)
       

class Grp60No180(base_tests.SimpleDataPlane):

    """Verify that tx_bytes in the queue_stats reply increments in accordance with the number of transmitted bytes"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp60No180 TxBytPerQueue test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        # Get queue stats from switch (retrieve current state)
        (queue_stats,p) = get_queuestats(self,ofp.OFPP_ALL,ofp.OFPQ_ALL)
  
        for idx in range(len(of_ports)):
            ingress_port = of_ports[idx]
            egress_port = of_ports[(idx + 1) % len(of_ports)]

            queue_id = port_queues_get(self,queue_stats,egress_port)

            for egress_queue_id in queue_id:

                #Clear switch state
                rv = delete_all_flows(self.controller)
                self.assertEqual(rv, 0, "Failed to delete all flows")

                # Get Queue stats for selected egress queue only
                logging.info("Retreiving the queue stats for selected egress queue")
                (qs_before,p) = get_queuestats(self,egress_port,egress_queue_id)

                #Insert a flow with enqueue action to queues configured on egress_port
                logging.info("Installing a flow entry with the enqueue action configured on the egress port")
                (pkt,match) = enqueue(self,ingress_port,egress_port,egress_queue_id)

                #Send packet on the ingress_port and verify its received on egress_port
                logging.info("Sending packet on ingress port and verifying its received on the egress port")
                send_packet(self,pkt,ingress_port,egress_port)
                
                expected_bytes = qs_before.stats[0].tx_bytes+len(str(pkt))

                logging.info("Verifying whether the tx bytes counter in the queue stats has been incremented correctly")
                verify_queuestats(self,egress_port,egress_queue_id,expect_byte=expected_bytes)
       
       

class Grp60No190(base_tests.SimpleDataPlane):

    """Verify that tx_errors in the queue_stats reply increments in accordance with the number of packets dropped due to overrun """
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp60No190 TxErrorPerQueue test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Queue_Stats Request")
        logging.info("Verify reply has Tramitted Overrun errors count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        (counter) = get_portstats(self,of_ports[0])

        tx_err = counter[12]
        logging.info("Transmit Overrun Error count is :" + str(tx_err))




class Grp60No200(base_tests.SimpleDataPlane):

    """Verify that active_count counter in the Table_Stats reply , increments in accordance with the flows inserted in a table"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp60No200 Active Counter test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear Switch state
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Installing a flow entry matching on in_port=ingress_port,action = output to egress_port T ")
       

        #Insert a flow with match on all ingress port
        (pkt, match ) = wildcard_all_except_ingress(self,of_ports)

        #Generate  Table_Stats
        logging.info("Verifying whether the active_counter in table stats has been incremented correctly") 
        verify_tablestats(self,expect_active=1)


class Grp60No210(base_tests.SimpleDataPlane):
    
    """Verify that lookup_count and matched_count counter in the Table_Stats reply 
        increments in accordance with the packets looked up and matched with the flows in the table"""
    @wireshark_capture
    def runTest(self):
        logging = get_logger()
        logging.info("Running Grp60No210 LookupMatchedCount test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear Switch state
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")


        #Get Current Table Stats
        logging.info("Retreiving initial table stats")
        (current_lookedup,current_matched,current_active) = get_tablestats(self)

        print current_lookedup, current_matched
        sleep(2)

        #Insert a flow with match on all ingress port
        logging.info("Installing a flow entry matching on in_port=ingress_port,action = output to egress_port")
        (pkt, match ) = wildcard_all_except_ingress(self,of_ports)

        #send packet pkt N times (pkt matches the flow)
        logging.info("Sending 5 packets matching the flow entry")
        num_sends = 5
        for pkt_cnt in range(num_sends):
            self.dataplane.send(of_ports[0],str(pkt))

        #send packet pkt N' (pkt does not match the flow)
        logging.info("Sending 5 non matching packets")
        num_sends2 = 5
        for pkt_cnt in range(num_sends):
            self.dataplane.send(of_ports[1],str(pkt))

        new_lookup = num_sends+num_sends2+current_lookedup
        logging.info("expected_lookup:"+str(new_lookup))
        new_matched = num_sends2 + current_matched
        logging.info("expected_matched:"+str(new_matched))
        print new_lookup, new_matched
        #Verify lookup_count and matched_count counters.
        logging.info("Verifying whether the lookup_counter and matched_counter have been incremented correctly")
        verify_tablestats(self,expect_lookup=new_lookup,expect_match=new_matched)
        


