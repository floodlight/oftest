"""
Serial failover test cases

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

#@var serial_failover_port_map Local copy of the configuration map from OF port
# numbers to OS interfaces
serial_failover_port_map = None
#@var serial_failover_config Local copy of global configuration data
serial_failover_config = None

test_prio = {}

def test_set_init(config):
    """
    Set up function for serial failover test classes

    @param config The configuration dictionary; see oft
    """

    global serial_failover_port_map
    global serial_failover_config

    serial_failover_port_map = config["port_map"]
    serial_failover_config = config

class SerialFailover(unittest.TestCase):
    """
    Opens a connection that the switch should use as its only controller,
    as specified by controller_host and controller_port.
    Then cause the connection to fail [fail method should be configurable].
    Ultimately, the switch should connect to the next controller port,
    as specified by 
    --test-params="controller_list=['ip2:port2','ip3:port3']".
    Multiple test params are specified by
    --test-params="param1=val1;param2=val2"
    """

    # populated by buildControllerList()
    controller_list = []
    controller_idx = 0
    # populated by setUp()
    test_timeout = 0
    test_iterations = 0

    def controllerSetup(self, host, port):
        self.controller = controller.Controller(host=host,port=port)

        # clean_shutdown should be set to False to force quit app
        self.clean_shutdown = True

        self.controller.start()
        #@todo Add an option to wait for a pkt transaction to ensure version
        # compatibilty?
        self.controller.connect(timeout=10)
        self.assertTrue(self.controller.active,
                        "Controller startup failed, not active")
        self.assertTrue(self.controller.switch_addr is not None,
                        "Controller startup failed, no switch addr")
        request = message.features_request()
        reply, pkt = self.controller.transact(request, timeout=20)
        self.assertTrue(reply is not None,
                        "Did not complete features_request for handshake")
        logging.info("Connected " + 
                                    str(self.controller.switch_addr))

        # send echo request and wait for reply
        request = message.echo_request()
        response, pkt = self.controller.transact(request)
        self.assertEqual(response.header.type, ofp.OFPT_ECHO_REPLY,
                         'response is not echo_reply')
        self.assertEqual(request.header.xid, response.header.xid,
                         'response xid != request xid')
        self.assertEqual(len(response.data), 0, 'response data non-empty')

    def connectionKill(self, kill_method):
        if kill_method == 'controller_shutdown':
            logging.info("Shutting down controller")
            self.controller.shutdown()
        elif kill_method == 'no_echo':
            logging.info("Disabling controller keep alive")
            self.controller.keep_alive = False

            # wait for controller to die
            count = 0
            while self.controller.active and count < self.test_timeout:
                time.sleep(1)
                count = count + 1
        else:
            self.assertTrue(false, "Unknown controller kill method")

    def buildControllerList(self):
        # controller_list is list of ip/port tuples
        partial_list = test_param_get(serial_failover_config,
                                      'controller_list')
        logging.debug("ctrl list: " + str(partial_list))
        self.controller_list = [(serial_failover_config["controller_host"],
                                 serial_failover_config["controller_port"])]
        if partial_list is not None:
            for controller in partial_list:
                ip,portstr = controller.split(':')
                try:
                    port = int(portstr)
                except:
                    self.assertTrue(0, "failure converting port " + 
                                    portstr + " to integer")
                self.controller_list.append( (ip, int(port)) )

    def getController(self):
        return self.controller_list[self.controller_idx]

    def getNextController(self):
        self.controller_idx = (self.controller_idx + 1) \
            % len(self.controller_list)
        return self.controller_list[self.controller_idx]

    def setUp(self):
        self.config = serial_failover_config
        logging.info("** START TEST CASE " + str(self))

        self.test_timeout = test_param_get(serial_failover_config,
                                           'failover_timeout') or 60
        self.test_iterations = test_param_get(serial_failover_config,
                                              'failover_iterations') or 4

        self.buildControllerList()
        self.controller_idx = 0
        controller = self.getController()
        self.controllerSetup(controller[0], controller[1])

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

    def doFailover(self, killmethod):
        logging.info("Starting serial failover test")
        self.assertTrue(self.controller.switch_socket is not None,
                        str(self) + 'No connection to switch')
        # kill controller connection
        self.connectionKill(killmethod)
        # establish new controller connection
        controller = self.getNextController()
        logging.debug("** Next controller (%u/%u)%s:%u" % 
                                     (self.controller_idx,
                                      len(self.controller_list),
                                      controller[0],
                                      controller[1]))
        self.controllerSetup(controller[0], controller[1])

    def runTest(self):
        for i in range(0,self.test_iterations):
            self.doFailover('controller_shutdown')

    def assertTrue(self, cond, msg):
        if not cond:
            logging.error("** FAILED ASSERTION: " + msg)
        unittest.TestCase.assertTrue(self, cond, msg)

test_prio["SerialFailover"] = -1


class SerialFailoverNoEcho(SerialFailover):

    def runTest(self):
        for i in range(0,self.test_iterations):
            self.doFailover('no_echo')

test_prio["SerialFailoverNoEcho"] = -1

