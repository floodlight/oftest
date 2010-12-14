'''
Created on Dec 7, 2010

@author: capveg
'''
import random

import basic
import oftest.message as message
import oftest.cstruct as ofp
import logging


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