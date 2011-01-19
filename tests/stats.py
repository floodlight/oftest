'''
Created on Dec 7, 2010

@author: capveg
'''
import random
import logging

import basic
import oftest.message as message
import oftest.cstruct as ofp
import testutils

class DescStatsGet(basic.SimpleProtocol):
    """ Make sure we get a sane desc stats reply to our request"""
    def runTest(self):
        request = message.desc_stats_request()
        xid = int(random.random() * 1000)
        request.header.xid = xid
        response, _ = self.controller.transact(request)
        self.assertTrue(response, "Got no desc_stats reply!")
        self.assertEqual(response.header.type, ofp.OFPT_STATS_REPLY,
                         'response is not echo_reply')
        self.assertEqual(request.header.xid, response.header.xid,
                         'response xid != request xid')

class TableStats(basic.SimpleProtocol):
    """
     Fill up the flow table a bit and make sure
     that the table stats reply agrees with our reply

    """
    def get_first_table_active_entries(self, table_stats_reply):
        """ Return the number of entries in the first table
        
        verify the reply, verify that it has at least one stat entry
        and then return the active count
        """
        self.assertTrue(table_stats_reply is not None, "Did not get response")
        basic_logger.debug(table_stats_reply.show())
        stats = table_stats_reply.stats
        self.assertTrue(len(stats) >= 1, "Got empty reply")
        for stat in stats:
            if stat.table_id == 0:
                return stat.active_count
        self.assertTrue(None, "Failed to find table_id==0 in table_stats_reply")

    def runTest(self):
        basic_logger.info("Running TableStats")
        testutils.delete_all_flows(self.controller, self.logger)
        basic_logger.info("Sending table stats request")
        request = message.table_stats_request()
        response, _ = self.controller.transact(request, timeout=2)
    
        # delete everything, so there should be no entries
        self.assertEqual(self.get_first_table_active_entries(response), 0)
        # add two entries to first table
        m1 = testutils.match_all_generate()
        m1.dl_type = 0x800
        m1.wildcards ^= ofp.OFPFW_DL_TYPE
        fm1 = testutils.flow_msg_create(self, None, match=m1, egr_port=2)
        rv = self.controller.message_send(fm1)
        self.assertEqual(rv, 0)
        m2 = testutils.match_all_generate()
        m2.dl_type = 0x806
        m2.wildcards ^= ofp.OFPFW_DL_TYPE
        fm2 = testutils.flow_msg_create(self, None, match=m2, egr_port=2)
        rv = self.controller.message_send(fm2)
        self.assertEqual(rv, 0)
        testutils.do_barrier(self.controller)
        response, _ = self.controller.transact(request, timeout=2)
        self.assertEqual(self.get_first_table_active_entries(response), 2)

# magic needed for oftest to 'discover' this module
def test_set_init(config):
    """
    Set up function for basic test classes

    @param config The configuration dictionary; see oft
    """

    global basic_port_map
    global basic_logger
    global basic_config

    basic_logger = logging.getLogger("stats")
    basic_logger.info("Initializing test set")
    basic_port_map = config["port_map"]
    basic_config = config        
        
if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test_spec=stats" 