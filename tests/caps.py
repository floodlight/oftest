"""
Basic capabilities and capacities tests

"""

import logging

import unittest

import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action
import oftest.parse as parse
import basic

from testutils import *

#@var caps_port_map Local copy of the configuration map from OF port
# numbers to OS interfaces
caps_port_map = None
#@var caps_logger Local logger object
caps_logger = None
#@var caps_config Local copy of global configuration data
caps_config = None

# For test priority
test_prio = {}

def test_set_init(config):
    """
    Set up function for caps test classes

    @param config The configuration dictionary; see oft
    """

    basic.test_set_init(config)

    global caps_port_map
    global caps_logger
    global caps_config

    caps_logger = logging.getLogger("caps")
    caps_logger.info("Initializing caps test set")
    caps_port_map = config["port_map"]
    caps_config = config


def flow_caps_common(obj, is_exact=True):
    """
    The common function for 

    @param obj The calling object
    @param is_exact If True, checking exact match; else wildcard
    """

    global caps_port_map
    of_ports = caps_port_map.keys()
    of_ports.sort()

    rv = delete_all_flows(obj.controller, caps_logger)
    obj.assertEqual(rv, 0, "Failed to delete all flows")

    pkt = simple_tcp_packet()
    match = parse.packet_to_flow_match(pkt)
    obj.assertTrue(match is not None, "Could not generate flow match from pkt")
    for port in of_ports:
        break;
    match.in_port = port
    match.nw_src = 1
    request = message.flow_mod()
    count_check = 101  # fixme:  better way to determine this.
    if is_exact:
        match.wildcards = 0
    else:
        match.wildcards |= ofp.OFPFW_DL_SRC

    request.match = match
    request.buffer_id = 0xffffffff      # set to NONE
    caps_logger.info(request.show())

    tstats = message.table_stats_request()
    try:  # Determine the table index to check (or "all")
        table_idx = caps_config["caps_table_idx"]
    except:
        table_idx = -1  # Accumulate all table counts

    # Make sure we can install at least one flow
    caps_logger.info("Inserting initial flow")
    rv = obj.controller.message_send(request)
    obj.assertTrue(rv != -1, "Error installing flow mod")
    do_barrier(obj.controller)
    flow_count = 1

    caps_logger.info("Table idx: " + str(table_idx))
    caps_logger.info("Check every " + str(count_check) + " inserts")

    while True:
        request.match.nw_src += 1
        rv = obj.controller.message_send(request)
#        do_barrier(obj.controller)
        flow_count += 1
        if flow_count % count_check == 0:
            response, pkt = obj.controller.transact(tstats, timeout=2)
            obj.assertTrue(response is not None, "Get tab stats failed")
            caps_logger.info(response.show())
            if table_idx == -1:  # Accumulate for all tables
                active_flows = 0
                for stats in response.stats:
                    active_flows += stats.active_count
            else: # Table index to use specified in config
                active_flows = response.stats[table_idx].active_count
            if active_flows != flow_count:
                break

    caps_logger.error("RESULT: " + str(flow_count) + " flows inserted")
    caps_logger.error("RESULT: " + str(active_flows) + " flows reported")


class FillTableExact(basic.SimpleProtocol):
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
        caps_logger.info("Running " + str(self))
        flow_caps_common(self)

test_prio["FillTableExact"] = -1

class FillTableWC(basic.SimpleProtocol):
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
        caps_logger.info("Running " + str(self))
        flow_caps_common(self, is_exact=False)

test_prio["FillTableWC"] = -1
