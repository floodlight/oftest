"""
Base classes for test cases

Tests will usually inherit from one of these classes to have the controller
and/or dataplane automatically set up.
"""

import logging
import unittest

from oftest import config
import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action

from oftest.testutils import *

class SimpleProtocol(unittest.TestCase):
    """
    Root class for setting up the controller
    """

    def setUp(self):
        logging.info("** START TEST CASE " + str(self))
        self.controller = controller.Controller(
            host=config["controller_host"],
            port=config["controller_port"])
        # clean_shutdown should be set to False to force quit app
        self.clean_shutdown = True
        self.controller.start()
        #@todo Add an option to wait for a pkt transaction to ensure version
        # compatibilty?
        self.controller.connect(timeout=20)

        # By default, respond to echo requests
        self.controller.keep_alive = True
        
        if not self.controller.active:
            raise Exception("Controller startup failed")
        if self.controller.switch_addr is None: 
            raise Exception("Controller startup failed (no switch addr)")
        logging.info("Connected " + str(self.controller.switch_addr))
        request = message.features_request()
        reply, pkt = self.controller.transact(request)
        self.assertTrue(reply is not None,
                        "Did not complete features_request for handshake")
        self.supported_actions = reply.actions
        logging.info("Supported actions: " + hex(self.supported_actions))

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
        logging.info("** Setup " + str(self) + " inheriting from "
                          + str(parent))
        self.controller = parent.controller
        self.supported_actions = parent.supported_actions
        
    def tearDown(self):
        logging.info("** END TEST CASE " + str(self))
        self.controller.shutdown()
        #@todo Review if join should be done on clean_shutdown
        if self.clean_shutdown:
            self.controller.join()

    def runTest(self):
        # Just a simple sanity check as illustration
        logging.info("Running simple proto test")
        self.assertTrue(self.controller.switch_socket is not None,
                        str(self) + 'No connection to switch')

    def assertTrue(self, cond, msg):
        if not cond:
            logging.error("** FAILED ASSERTION: " + msg)
        unittest.TestCase.assertTrue(self, cond, msg)

class SimpleDataPlane(SimpleProtocol):
    """
    Root class that sets up the controller and dataplane
    """
    def setUp(self):
        SimpleProtocol.setUp(self)
        self.dataplane = dataplane.DataPlane(config)
        for of_port, ifname in config["port_map"].items():
            self.dataplane.port_add(ifname, of_port)

    def inheritSetup(self, parent):
        """
        Inherit the setup of a parent

        See SimpleProtocol.inheritSetup
        """
        SimpleProtocol.inheritSetup(self, parent)
        self.dataplane = parent.dataplane

    def tearDown(self):
        logging.info("Teardown for simple dataplane test")
        SimpleProtocol.tearDown(self)
        if hasattr(self, 'dataplane'):
            self.dataplane.kill(join_threads=self.clean_shutdown)
        logging.info("Teardown done")

    def runTest(self):
        self.assertTrue(self.controller.switch_socket is not None,
                        str(self) + 'No connection to switch')
        # self.dataplane.show()
        # Would like an assert that checks the data plane

class DataPlaneOnly(unittest.TestCase):
    """
    Root class that sets up only the dataplane
    """

    def setUp(self):
        self.clean_shutdown = True
        logging.info("** START DataPlaneOnly CASE " + str(self))
        self.dataplane = dataplane.DataPlane(config)
        for of_port, ifname in config["port_map"].items():
            self.dataplane.port_add(ifname, of_port)

    def tearDown(self):
        logging.info("Teardown for simple dataplane test")
        self.dataplane.kill(join_threads=self.clean_shutdown)
        logging.info("Teardown done")

    def runTest(self):
        logging.info("DataPlaneOnly")
        # self.dataplane.show()
        # Would like an assert that checks the data plane
