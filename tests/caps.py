"""
Basic capabilities and capacities tests

"""

import logging
import time
import unittest

from oftest import config
import oftest.controller as controller
import ofp
import oftest.dataplane as dataplane
import oftest.parse as parse
import oftest.base_tests as base_tests

from oftest.testutils import *

def flow_caps_common(obj, is_exact=True):
    """
    The common function for 

    @param obj The calling object
    @param is_exact If True, checking exact match; else wildcard
    """

    of_ports = config["port_map"].keys()
    of_ports.sort()

    delete_all_flows(obj.controller)

    pkt = simple_tcp_packet()
    match = packet_to_flow_match(obj, pkt)
    obj.assertTrue(match is not None, "Could not generate flow match from pkt")
    for port in of_ports:
        break;
    match.in_port = port
    match.nw_src = 1
    request = ofp.message.flow_mod()
    count_check = 101  # fixme:  better way to determine this.
    if is_exact:
        match.wildcards = 0
    else:
        match.wildcards |= ofp.OFPFW_DL_SRC

    request.match = match
    request.buffer_id = 0xffffffff      # set to NONE
    logging.info(request.show())

    tstats = ofp.message.table_stats_request()
    try:  # Determine the table index to check (or "all")
        table_idx = config["caps_table_idx"]
    except:
        table_idx = -1  # Accumulate all table counts

    # Make sure we can install at least one flow
    logging.info("Inserting initial flow")
    obj.controller.message_send(request)
    do_barrier(obj.controller, timeout=10)
    flow_count = 1

    logging.info("Table idx: " + str(table_idx))
    logging.info("Check every " + str(count_check) + " inserts")

    while True:
        request.match.nw_src += 1
        obj.controller.message_send(request)
        flow_count += 1
        if flow_count % count_check == 0:
            do_barrier(obj.controller, timeout=10)
            response, pkt = obj.controller.transact(tstats)
            obj.assertTrue(response is not None, "Get tab stats failed")
            logging.info(response.show())
            if table_idx == -1:  # Accumulate for all tables
                active_flows = 0
                for stats in response.stats:
                    active_flows += stats.active_count
            else: # Table index to use specified in config
                active_flows = response.stats[table_idx].active_count
            if active_flows != flow_count:
                break

    logging.error("RESULT: " + str(flow_count) + " flows inserted")
    logging.error("RESULT: " + str(active_flows) + " flows reported")

    # clean up and wait a bit in case the table is really big
    delete_all_flows(obj.controller)
    time.sleep(flow_count / 100)


@disabled
class FillTableExact(base_tests.SimpleProtocol):
    """
    Fill the flow table with exact matches; can take a while

    Fill table until no more flows can be added.  Report result.
    Increment the source IP address.  Assume the flow table will
    fill in less than 4 billion inserts

    To check the number of flows in the tables is expensive, so
    it's only done periodically.  This is controlled by the
    count_check variable.

    A switch may have multiple tables.  The default behaviour
    is to count all the flows in all the tables.  By setting 
    the parameter "caps_table_idx" in the configuration array,
    you can control which table to check.
    """

    def runTest(self):
        logging.info("Running " + str(self))
        flow_caps_common(self)

@disabled
class FillTableWC(base_tests.SimpleProtocol):
    """
    Fill the flow table with wildcard matches

    Fill table using wildcard entries until no more flows can be
    added.  Report result.
    Increment the source IP address.  Assume the flow table will
    fill in less than 4 billion inserts

    To check the number of flows in the tables is expensive, so
    it's only done periodically.  This is controlled by the
    count_check variable.

    A switch may have multiple tables.  The default behaviour
    is to count all the flows in all the tables.  By setting 
    the parameter "caps_table_idx" in the configuration array,
    you can control which table to check.

    """

    def runTest(self):
        logging.info("Running " + str(self))
        flow_caps_common(self, is_exact=False)
