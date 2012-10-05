"""
Connection test cases

"""

import time
import signal
import sys
import logging

import unittest
import random

import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action

from oftest.testutils import *

#@var cxn_port_map Local copy of the configuration map from OF port
# numbers to OS interfaces
cxn_port_map = None
#@var cxn_logger Local logger object
cxn_logger = None
#@var cxn_config Local copy of global configuration data
cxn_config = None

test_prio = {}

def test_set_init(config):
    """
    Set up function for connection test classes

    @param config The configuration dictionary; see oft
    """

    global cxn_port_map
    global cxn_logger
    global cxn_config

    cxn_logger = logging.getLogger("cxn")
    cxn_logger.info("Initializing test set")
    cxn_port_map = config["port_map"]
    cxn_config = config

class BaseHandshake(unittest.TestCase):
    """
    Base handshake case to set up controller, but do not send hello.
    """

    controllers = []
    default_timeout = 2

    def sig_handler(self, v1, v2):
        cxn_logger.critical("Received interrupt signal; exiting")
        print "Received interrupt signal; exiting"
        self.clean_shutdown = False
        self.tearDown()
        sys.exit(1)

    def controllerSetup(self, host, port):
        con = controller.Controller(host=host,port=port)

        # clean_shutdown should be set to False to force quit app
        self.clean_shutdown = True
        # disable initial hello so hello is under control of test
        con.initial_hello = False

        con.start()
        self.controllers.append(con)

    def setUp(self):
        self.logger = cxn_logger
        self.config = cxn_config
        #@todo Test cases shouldn't monkey with signals; move SIGINT handler
        # to top-level oft
        try:
           signal.signal(signal.SIGINT, self.sig_handler)
        except ValueError, e:
           cxn_logger.info("Could not set SIGINT handler: %s" % e)
        cxn_logger.info("** START TEST CASE " + str(self))

        self.default_timeout = test_param_get(cxn_config,
                                              'default_timeout') or 2

    def tearDown(self):
        cxn_logger.info("** END TEST CASE " + str(self))
        for con in self.controllers:
            con.shutdown()
            if self.clean_shutdown:
                con.join()

    def runTest(self):
        # do nothing in the base case
        pass

    def assertTrue(self, cond, msg):
        if not cond:
            cxn_logger.error("** FAILED ASSERTION: " + msg)
        unittest.TestCase.assertTrue(self, cond, msg)

test_prio["BaseHandshake"] = -1

class HandshakeNoHello(BaseHandshake):
    """
    TCP connect to switch, but do not sent hello,
    and wait for disconnect.
    """
    def runTest(self):
        self.controllerSetup(cxn_config["controller_host"],
                             cxn_config["controller_port"])
        self.controllers[0].connect(self.default_timeout)
        cxn_logger.info("TCP Connected " + 
                        str(self.controllers[0].switch_addr))
        cxn_logger.info("Hello not sent, waiting for timeout")

        # wait for controller to die
        count = 0
        self.assertTrue(self.controllers[0].wait_disconnected(timeout=10),
                        "Not notified of controller disconnect")

class HandshakeNoFeaturesRequest(BaseHandshake):
    """
    TCP connect to switch, send hello, but do not send features request,
    and wait for disconnect.
    """
    def runTest(self):
        self.controllerSetup(cxn_config["controller_host"],
                             cxn_config["controller_port"])
        self.controllers[0].connect(self.default_timeout)
        cxn_logger.info("TCP Connected " + 
                                    str(self.controllers[0].switch_addr))
        cxn_logger.info("Sending hello")
        self.controllers[0].message_send(message.hello())

        cxn_logger.info("Features request not sent, waiting for timeout")

        # wait for controller to die
        count = 0
        self.assertTrue(self.controllers[0].wait_disconnected(timeout=10),
                        "Not notified of controller disconnect")

class HandshakeAndKeepalive(BaseHandshake):
    """
    Complete handshake and respond to echo request, but otherwise do nothing.
    Good for manual testing.
    """
    def runTest(self):
        self.num_controllers = test_param_get(cxn_config, 
                                              'num_controllers') or 1

        for i in range(self.num_controllers):
            self.controllerSetup(cxn_config["controller_host"],
                                 cxn_config["controller_port"]+i)
        for i in range(self.num_controllers):
            self.controllers[i].handshake_done = False

        # try to maintain switch connections forever
        count = 0
        while True:
            for con in self.controllers:
                if con.switch_socket and con.handshake_done:
                    if count < 7:
                        cxn_logger.info(con.host + ":" + str(con.port) + 
                                        ": maintaining connection to " +
                                        str(con.switch_addr))
                        count = count + 1
                    else:
                        cxn_logger.info(con.host + ":" + str(con.port) + 
                                        ": disconnecting from " +
                                        str(con.switch_addr))
                        con.disconnect()
                        con.handshake_done = False
                        count = 0
                    time.sleep(1)
                else:
                    #@todo Add an option to wait for a pkt transaction to 
                    # ensure version compatibilty?
                    con.connect(self.default_timeout)
                    if not con.switch_socket:
                        cxn_logger.info("Did not connect to switch")
                        continue
                    cxn_logger.info("TCP Connected " + str(con.switch_addr))
                    cxn_logger.info("Sending hello")
                    con.message_send(message.hello())
                    request = message.features_request()
                    reply, pkt = con.transact(request, 
                                              timeout=self.default_timeout)
                    if reply:
                        cxn_logger.info("Handshake complete with " + 
                                        str(con.switch_addr))
                        con.handshake_done = True
                        con.keep_alive = True
                    else:
                        cxn_logger.info("Did not complete features_request for handshake")
                        con.disconnect()
                        con.handshake_done = False

test_prio["HandshakeAndKeepalive"] = -1

