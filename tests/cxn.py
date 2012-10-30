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
        self.controller_timeout = test_param_get('controller_timeout',
                                                 default=-1)
        self.hello_timeout = test_param_get('hello_timeout',
                                            default=5)
        self.features_req_timeout = test_param_get('features_req_timeout',
                                                   default=5)

        for i in range(self.num_controllers):
            self.controllerSetup(config["controller_host"],
                                 config["controller_port"]+i)
        for i in range(self.num_controllers):
            self.controllers[i].cstate = 0
            self.controllers[i].keep_alive = True
        tick = 0.1  # time period in seconds at which controllers are handled

        while True:
            for con in self.controllers:
                condesc = con.host + ":" + str(con.port) + ": "
                logging.debug("Checking " + condesc)

                if con.switch_socket: 
                    if con.cstate == 0:
                        logging.info(condesc + "Sending hello to " +
                                     str(con.switch_addr))
                        con.message_send(message.hello())
                        con.cstate = 1
                        con.count = 0
                    elif con.cstate == 1:
                        reply, pkt = con.poll(exp_msg=ofp.OFPT_HELLO,
                                              timeout=0)
                        if reply is not None:
                            logging.info(condesc + 
                                         "Hello received from " +
                                         str(con.switch_addr))
                            con.cstate = 2
                        else:
                            con.count = con.count + 1
                            # fall back to previous state on timeout
                            if con.count >= self.hello_timeout/tick:
                                logging.info(condesc + 
                                             "Timeout hello from " +
                                             str(con.switch_addr))
                                con.cstate = 0
                    elif con.cstate == 2:
                        logging.info(condesc + "Sending features request to " +
                                     str(con.switch_addr))
                        con.message_send(message.features_request())
                        con.cstate = 3
                        con.count = 0
                    elif con.cstate == 3:
                        reply, pkt = con.poll(exp_msg=ofp.OFPT_FEATURES_REPLY,
                                              timeout=0)
                        if reply is not None:
                            logging.info(condesc + 
                                         "Features request received from " +
                                         str(con.switch_addr))
                            con.cstate = 4
                            con.count = 0
                        else:
                            con.count = con.count + 1
                            # fall back to previous state on timeout
                            if con.count >= self.features_req_timeout/tick:
                                logging.info(condesc +
                                             "Timeout features request from " +
                                             str(con.switch_addr))
                                con.cstate = 2
                    elif con.cstate == 4:
                        if (self.controller_timeout < 0 or
                            con.count < self.controller_timeout/tick):
                            logging.debug(condesc +
                                          "Maintaining connection to " +
                                          str(con.switch_addr))
                            con.count = con.count + 1
                        else:
                            logging.info(condesc + 
                                         "Disconnecting from " +
                                         str(con.switch_addr))
                            con.disconnect()
                            con.cstate = 0
                else:
                    con.cstate = 0

            time.sleep(tick)
