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
import ofp
import oftest.dataplane as dataplane

from oftest.testutils import *

@disabled
class BaseHandshake(unittest.TestCase):
    """
    Base handshake case to set up controller, but do not send hello.
    """

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

        self.controllers = []
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
        self.controllers[0].message_send(ofp.message.hello())

        logging.info("Features request not sent, waiting for timeout")

        # wait for controller to die
        self.assertTrue(self.controllers[0].wait_disconnected(timeout=10),
                        "Not notified of controller disconnect")

@disabled
class CompleteHandshake(BaseHandshake):
    """
    Set up multiple controllers and complete handshake, but otherwise do nothing.
    """

    def buildControllerList(self):                                             
        # controller_list is a list of IP:port tuples
        con_list = test_param_get('controller_list')
        if con_list is not None:
            self.controller_list = []
            for controller in con_list:
                ip,portstr = controller.split(':')
                try:
                    port = int(portstr)
                except:
                    self.assertTrue(0, "failure converting port " +
                                    portstr + " to integer")
                self.controller_list.append( (ip, int(port)) )
        else:
            self.controller_list = [(config["controller_host"],
                                     config["controller_port"])]

    def __init__(self, keep_alive=True, cxn_cycles=5,
                 controller_timeout=-1, hello_timeout=5, 
                 features_req_timeout=5, disconnected_timeout=3):
        BaseHandshake.__init__(self)
        self.buildControllerList()
        self.keep_alive = keep_alive
        self.cxn_cycles = test_param_get('cxn_cycles') \
            or cxn_cycles
        self.controller_timeout = test_param_get('controller_timeout') \
            or controller_timeout
        self.hello_timeout = test_param_get('hello_timeout') \
            or hello_timeout
        self.features_req_timeout = test_param_get('features_req_timeout') \
            or features_req_timeout
        self.disconnected_timeout = test_param_get('disconnected_timeout') \
            or disconnected_timeout

    def runTest(self):
        for conspec in self.controller_list:
            self.controllerSetup(conspec[0], conspec[1])
        for i in range(len(self.controller_list)):
            self.controllers[i].cstate = 0
            self.controllers[i].keep_alive = self.keep_alive
            self.controllers[i].saved_switch_addr = None
        tick = 0.1  # time period in seconds at which controllers are handled

        disconnected_count = 0
        cycle = 0
        while True:
            states = []
            for con in self.controllers:
                condesc = con.host + ":" + str(con.port) + ": "
                logging.debug("Checking " + condesc)

                if con.switch_socket:
                    if con.switch_addr != con.saved_switch_addr:
                        con.saved_switch_addr = con.switch_addr
                        con.cstate = 0

                    if con.cstate == 0:
                        logging.info(condesc + "Sending hello to " +
                                     str(con.switch_addr))
                        con.message_send(ofp.message.hello())
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
                        con.message_send(ofp.message.features_request())
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
                            cycle = cycle + 1
                            logging.info("Cycle " + str(cycle))
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
            
                states.append(con.cstate)

            logging.debug("Cycle " + str(cycle) +
                          ", states " + str(states) +
                          ", disconnected_count " + str(disconnected_count))
            if 4 in states:
                disconnected_count = 0
            else:
                disconnected_count = disconnected_count + 1
            if cycle != 0:
                self.assertTrue(disconnected_count < self.disconnected_timeout/tick,
                                "Timeout expired connecting to controller")
            else:
               # on first cycle, allow more time for initial connect
               self.assertTrue(disconnected_count < 2*self.disconnected_timeout/tick,
                               "Timeout expired connecting to controller on init")

            if cycle > self.cxn_cycles:
               break
            time.sleep(tick)

@disabled
class HandshakeAndKeepalive(CompleteHandshake):
    """
    Complete handshake and respond to echo request, but otherwise do nothing.
    Good for manual testing.
    """

    def __init__(self):
       CompleteHandshake.__init__(self, keep_alive=True)

@disabled
class HandshakeNoEcho(CompleteHandshake):
    """
    Complete handshake, but otherwise do nothing, and do not respond to echo.
    """

    def __init__(self):
       CompleteHandshake.__init__(self, keep_alive=False)

@disabled
class HandshakeAndDrop(CompleteHandshake):
    """
    Complete handshake, but otherwise do nothing, and drop connection after a while.
    """

    def __init__(self):
       CompleteHandshake.__init__(self, keep_alive=True, controller_timeout=10)

