"""
Connection test cases

"""

import time
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
#@var cxn_config Local copy of global configuration data
cxn_config = None

test_prio = {}

def test_set_init(config):
    """
    Set up function for connection test classes

    @param config The configuration dictionary; see oft
    """

    global cxn_port_map
    global cxn_config

    cxn_port_map = config["port_map"]
    cxn_config = config

class BaseHandshake(unittest.TestCase):
    """
    Base handshake case to set up controller, but do not send hello.
    """

    def controllerSetup(self, host, port):
        self.controller = controller.Controller(host=host,port=port)

        # clean_shutdown should be set to False to force quit app
        self.clean_shutdown = True
        # disable initial hello so hello is under control of test
        self.controller.initial_hello = False

        self.controller.start()
        #@todo Add an option to wait for a pkt transaction to ensure version
        # compatibilty?
        self.controller.connect(timeout=10)
        self.assertTrue(self.controller.active,
                        "Controller startup failed, not active")
        self.assertTrue(self.controller.switch_addr is not None,
                        "Controller startup failed, no switch addr")

    def setUp(self):
        self.config = cxn_config
        logging.info("** START TEST CASE " + str(self))

        self.test_timeout = test_param_get(cxn_config,
                                           'handshake_timeout') or 60

    def inheritSetup(self, parent):
        """
        Inherit the setup of a parent

        This allows running at test from within another test.  Do the
        following:

        sub_test = SomeTestClass()  # Create an instance of the test class
        sub_test.inheritSetup(self) # Inherit setup of parent
        sub_test.runTest()          # Run the test

        Normally, only the parent's setUp and tearDown are called and
        the state after the sub_test is run must be taken into account
        by subsequent operations.
        """
        self.config = parent.config
        logging.info("** Setup " + str(self) + 
                                    " inheriting from " + str(parent))
        self.controller = parent.controller
        
    def tearDown(self):
        logging.info("** END TEST CASE " + str(self))
        self.controller.shutdown()
        if self.clean_shutdown:
            self.controller.join()

    def runTest(self):
        # do nothing in the base case
        pass

    def assertTrue(self, cond, msg):
        if not cond:
            logging.error("** FAILED ASSERTION: " + msg)
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

        logging.info("TCP Connected " + 
                        str(self.controller.switch_addr))
        logging.info("Hello not sent, waiting for timeout")

        # wait for controller to die
        count = 0
        while self.controller.active and count < self.test_timeout:
            time.sleep(1)
            count = count + 1
        self.assertTrue(not self.controller.active, 
                        "Expected controller disconnect, but still active")

class HandshakeNoFeaturesRequest(BaseHandshake):
    """
    TCP connect to switch, send hello, but do not send features request,
    and wait for disconnect.
    """
    def runTest(self):
        self.controllerSetup(cxn_config["controller_host"],
                             cxn_config["controller_port"])

        logging.info("TCP Connected " + 
                                    str(self.controller.switch_addr))
        logging.info("Sending hello")
        self.controller.message_send(message.hello())

        logging.info("Features request not sent, waiting for timeout")

        # wait for controller to die
        count = 0
        while self.controller.active and count < self.test_timeout:
            time.sleep(1)
            count = count + 1
        self.assertTrue(not self.controller.active, 
                        "Expected controller disconnect, but still active")

class HandshakeAndKeepalive(BaseHandshake):
    """
    Complete handshake and respond to echo request, but otherwise do nothing.
    Good for manual testing.
    """
    def runTest(self):
        self.controllerSetup(cxn_config["controller_host"],
                             cxn_config["controller_port"])

        logging.info("TCP Connected " + 
                                    str(self.controller.switch_addr))
        logging.info("Sending hello")
        self.controller.message_send(message.hello())

        request = message.features_request()
        reply, pkt = self.controller.transact(request, timeout=20)
        self.assertTrue(reply is not None,
                        "Did not complete features_request for handshake")
        logging.info("Handshake complete with " + 
                        str(self.controller.switch_addr))

        self.controller.keep_alive = True

        # keep controller up forever
        while self.controller.active:
            time.sleep(1)

        self.assertTrue(not self.controller.active, 
                        "Expected controller disconnect, but still active")

test_prio["HandshakeAndKeepalive"] = -1

