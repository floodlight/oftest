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

# @FIXME Move someplace else

def get_flow_count(obj, table_idx=-1):
    """
    Get the number of flows on the switch in the given table
    (or all if table_idx == -1).
    """
    tstats = ofp.message.table_stats_request()
    response, pkt = obj.controller.transact(tstats)
    obj.assertTrue(response is not None, "Get tab stats failed")
    logging.debug(response.show())

    if table_idx == -1:  # Accumulate for all tables
        active_flows = 0
        for stats in response.entries:
            active_flows += stats.active_count
    else: # Table index to use specified in config
        active_flows = response.entries[table_idx].active_count

    return active_flows


def add_some_flows(obj, count, match, mod_prio, mod_in_port, max_flows=0):
    """
    Add some flows to the switch and then do a barrier
    @param count Number of flows to add
    @param match The base match to use when adding
    @param mod_prio Modify the priority (over the range of 0-9)
    @param mod_in_port Modify the ingress port (between first and second ports)
    @param max_flows The max flows to allow in the table
    
    Returns a boolean indication of whether all flows got into the table
    """

    of_ports = config["port_map"].keys()
    of_ports.sort()

    # Get the current flow count in the switch
    orig_count = get_flow_count(obj)

    iter_count = count
    if (max_flows > 0) and (orig_count + count > max_flows):
        # Only add enough to reach max_flows
        iter_count = max_flows - orig_count

    request = ofp.message.flow_add()

    request.match = match
    request.buffer_id = 0xffffffff      # set to NONE

    port_idx = 0

    # Try to add 'count' flows
    for idx in range(0, iter_count):
        request.match.ipv4_src += 1
        if mod_in_port:
            request.match.in_port = of_ports[port_idx]
            port_idx = (port_idx + 1) % 2
        if mod_prio:
            request.priority = (request.priority + 1) % 10

        obj.controller.message_send(request)

    do_barrier(obj.controller, timeout=60)
    new_count = get_flow_count(obj)

    return (new_count == (orig_count + count))

def mod_flows(obj, match, out_port):
    """
    Modify flows based on match changing action to out_port
    """

    logging.info("Modifying with out_port " + str(out_port))
    request = ofp.message.flow_modify()

    request.match = match
    request.buffer_id = 0xffffffff      # set to NONE

    act = ofp.action.output()
    act.port = out_port
    request.actions.append(act)

    obj.controller.message_send(request)
    do_barrier(obj.controller, timeout=60)
    
    
def delete_some_flows(obj, in_port=-1):
    """
    Delete flows on the switch, possibly based on in_port
    @param in_port The port to delete if > 0
    """

    msg = ofp.message.flow_delete()
    if in_port > 0:
        logging.info("Deleting flows on port " + str(in_port))
        msg.match.wildcards = ofp.OFPFW_ALL - ofp.OFPFW_IN_PORT
        msg.match.in_port = in_port
    else:
        logging.info("Deleting all flows")
        msg.match.wildcards = ofp.OFPFW_ALL

    msg.out_port = ofp.OFPP_NONE
    msg.buffer_id = 0xffffffff
    obj.controller.message_send(msg)
    do_barrier(obj.controller, timeout=60)

    logging.info("After deleting some flows, %d flows in table" %
                 get_flow_count(obj))

def clear_and_fill_table(obj,
                         is_exact=True,
                         block_size=101,
                         mod_prio=False,
                         mod_in_port=False,
                         max_flows=0):

    """
    Fill the flow table (or install some number of flows) blocking every
    so often with a barrier.

    @param obj The calling object
    @param is_exact If True, checking exact match; else wildcard
    @param block_size Number of flows to add between blocks
    @param mod_prio If True, use varying priorities (0-9) on flows
    @param mod_in_port If True, modify in_port with flows (two ports)
    @param max_flows If > 0, do not install more than this many flows.
    """

    of_ports = config["port_map"].keys()
    of_ports.sort()

    delete_all_flows(obj.controller)
    do_barrier(obj.controller, timeout=60)

    pkt = simple_tcp_packet()
    match = packet_to_flow_match(obj, pkt)
    obj.assertTrue(match is not None, "Could not generate flow match from pkt")
    match.in_port = of_ports[0]
    match.ipv4_src = 1
    if is_exact:
        match.wildcards = 0
    else:
        match.wildcards |= ofp.OFPFW_DL_SRC

    logging.info("Adding flows with barrier every %d inserts.  (Max %d)" %
                 (block_size, max_flows))

    iters = 1
    while add_some_flows(obj, block_size, match, mod_prio, mod_in_port, max_flows):
        iters += 1

    logging.info("Tried to add %d blocks of %d flows" %
                 (iters, block_size))

def churn_flow_table(obj, add_iterations=5, modify_iterations=0, max_flows=0):

    """
    Fill table with exact matches; then churn the table with del + adds

    @param obj The calling object
    """

    of_ports = config["port_map"].keys()
    of_ports.sort()
    in_ports = [of_ports[0], of_ports[1]]
    out_ports = [of_ports[2], of_ports[3]]

    clear_and_fill_table(obj, mod_prio=True, mod_in_port=True, max_flows=max_flows)
    # Table contains max_flows entries split with half in_ports[0], half in_ports[1]

    pkt = simple_tcp_packet()
    match = packet_to_flow_match(obj, pkt)
    obj.assertTrue(match is not None, "Could not generate flow match from pkt")

    match.in_port = in_ports[0]
    match.wildcards = 0

    # Churn the table with adds/deletes
    for iter in range(0, add_iterations):
        start = time.time()
        logging.info("Add Iter %d. Currently %d flows.  Deleting flows on port %d"
                     % (iter, get_flow_count(obj), of_ports[0]))
        delete_some_flows(obj, in_port=in_ports[0])
        logging.info("Now %d flows" % get_flow_count(obj))

        logging.info("Adding flows on port %d" % of_ports[0])
        match.ipv4_src = 1000 * (iter + 1)
        if not add_some_flows(obj, 500, match, True, False):
            logging.info("Did not add all flows to table")
            # Should this be an assert?
        end = time.time()
        logging.info("Iteration %d took %d seconds" % (iter, end - start))

    # Do modifies on the table
    match.wildcards = ofp.OFPFW_ALL - ofp.OFPFW_IN_PORT
    out_idx = 0
    for iter in range(0, modify_iterations):
        start = time.time()
        out_port = out_ports[out_idx]
        out_idx = (out_idx + 1) % 2

        match.in_port = in_ports[0]
        logging.info("Modify Iter %d. current count %d. in port %d. output %d"
                     % (iter, get_flow_count(obj), match.in_port, out_port))
        mod_flows(obj, match, out_port)

        match.in_port = in_ports[1]
        logging.info("Now match in port %d" % match.in_port)
        mod_flows(obj, match, out_port)

        end = time.time()
        logging.info("After modify, %d flows" % get_flow_count(obj))
        logging.info("Iteration %d took %d seconds" % (iter, end - start))

@disabled
class FillTableExact(base_tests.SimpleProtocol):
    """
    Fill the flow table with exact matches; can take a while

    Fill table until no more flows can be added.  Report result.
    Increment the source IP address.  Assume the flow table will
    fill in less than 4 billion inserts

    A switch may have multiple tables.  The default behaviour
    is to count all the flows in all the tables.  By setting 
    the parameter "caps_table_idx" in the configuration array,
    you can control which table to check.
    """

    def runTest(self):
        logging.info("Running " + str(self))
        start = time.time()
        clear_and_fill_table(self)
        end = time.time()
        logging.info("Took %d seconds to fill table" % (end - start))
        logging.error("RESULT: %d flows reported" % get_flow_count(self))

@disabled
class FillTableWC(base_tests.SimpleProtocol):
    """
    Fill the flow table with wildcard matches

    Fill table using wildcard entries until no more flows can be
    added.  Report result.
    Increment the source IP address.  Assume the flow table will
    fill in less than 4 billion inserts

    A switch may have multiple tables.  The default behaviour
    is to count all the flows in all the tables.  By setting 
    the parameter "caps_table_idx" in the configuration array,
    you can control which table to check.

    """

    def runTest(self):
        logging.info("Running " + str(self))
        start = time.time()
        clear_and_fill_table(self, is_exact=False)
        end = time.time()
        logging.info("Took %d seconds to fill table" % (end - start))
        logging.error("RESULT: %d flows reported" % get_flow_count(self))


@disabled
class ReFillTableExact(base_tests.SimpleProtocol):
    """
    Fill the flow table with exact matches 5 times and track 
    the time
    """

    def runTest(self):
        logging.info("Running " + str(self))
        for idx in range(0, 5):
            start = time.time()
            clear_and_fill_table(self)
            end = time.time()
            logging.info("Table now has %d flows" % get_flow_count(self))
            logging.info("Run %d took %d seconds" % (idx, end - start))

@disabled
class ChurnTable(base_tests.SimpleProtocol):
    """
    Fill the flow table with exact matches; can take a while

    Then add and delete entries in blocks
    """

    def runTest(self):
        logging.info("Running " + str(self))
        churn_flow_table(self)

@disabled
class ChurnTableMod(base_tests.SimpleProtocol):
    """
    Add a bunch of flows and then modify them with flow_modify messages

    """
    # @FIXME allow max_flows to be a test parameter

    def runTest(self):
        logging.info("Running " + str(self))
        churn_flow_table(self, add_iterations=0, modify_iterations=5,
                         max_flows=test_param_get("max_flows", 1000))
