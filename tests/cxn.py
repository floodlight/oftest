"""
Connection test cases

"""

import time
import sys
import logging

import unittest
import random

from oftest import config
import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action

from oftest.testutils import *

class BaseHandshake(unittest.TestCase):
    """
    Base handshake case to set up controller, but do not send hello.
    """

    priority = -1
    controllers = []
    default_timeout = 2

    def controllerSetup(self, host, port):
        con = controller.Controller(host=host,port=port)

        # clean_shutdown should be set to False to force quit app
        self.clean_shutdown = True
        # disable initial hello so hello is under control of test
        con.initial_hello = False

        con.start()
        self.controllers.append(con)

    def setUp(self):
        logging.info("** START TEST CASE " + str(self))

        self.default_timeout = test_param_get('default_timeout',
                                              default=2)

    def tearDown(self):
        logging.info("** END TEST CASE " + str(self))
        for con in self.controllers:
            con.shutdown()
            if self.clean_shutdown:
                con.join()

    def runTest(self):
        # do nothing in the base case
        pass

    def assertTrue(self, cond, msg):
        if not cond:
            logging.error("** FAILED ASSERTION: " + msg)
        unittest.TestCase.assertTrue(self, cond, msg)

class HandshakeNoHello(BaseHandshake):
    """
    TCP connect to switch, but do not sent hello,
    and wait for disconnect.
    """
    def runTest(self):
        self.controllerSetup(config["controller_host"],
                             config["controller_port"])
        self.controllers[0].connect(self.default_timeout)

        logging.info("TCP Connected " + 
                     str(self.controllers[0].switch_addr))
        logging.info("Hello not sent, waiting for timeout")

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
        self.controllerSetup(config["controller_host"],
                             config["controller_port"])
        self.controllers[0].connect(self.default_timeout)

        logging.info("TCP Connected " + 
                     str(self.controllers[0].switch_addr))
        logging.info("Sending hello")
        self.controllers[0].message_send(message.hello())

        logging.info("Features request not sent, waiting for timeout")

        # wait for controller to die
        count = 0
        self.assertTrue(self.controllers[0].wait_disconnected(timeout=10),
                        "Not notified of controller disconnect")

class HandshakeAndKeepalive(BaseHandshake):
    """
    Complete handshake and respond to echo request, but otherwise do nothing.
    Good for manual testing.
    """

    priority = -1

    def runTest(self):
        self.num_controllers = test_param_get('num_controllers', default=1)

        for i in range(self.num_controllers):
            self.controllerSetup(config["controller_host"],
                                 config["controller_port"]+i)
        for i in range(self.num_controllers):
            self.controllers[i].handshake_done = False

        # try to maintain switch connections forever
        count = 0
        while True:
            for con in self.controllers:
                if con.switch_socket and con.handshake_done:
                    if count < 7:
                        logging.info(con.host + ":" + str(con.port) + 
                                     ": maintaining connection to " +
                                     str(con.switch_addr))
                        count = count + 1
                    else:
                        logging.info(con.host + ":" + str(con.port) + 
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
                        logging.info("Did not connect to switch")
                        continue
                    logging.info("TCP Connected " + str(con.switch_addr))
                    logging.info("Sending hello")
                    con.message_send(message.hello())
                    request = message.features_request()
                    reply, pkt = con.transact(request, 
                                              timeout=self.default_timeout)
                    if reply:
                        logging.info("Handshake complete with " + 
                                    str(con.switch_addr))
                        con.handshake_done = True
                        con.keep_alive = True
                    else:
                        logging.info("Did not complete features_request " +
                                     "for handshake")
                        con.disconnect()
                        con.handshake_done = False

