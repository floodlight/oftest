import os
import subprocess

import Switches
import Platforms

class UnsupportedPlatform(Exception):
    def __init__ (self):
        self.name = os.name

class UnsupportedSwitch(Exception):
    def __init__ (self, name):
        self.name = name


class Platform(object):
    def __init__ (self, options):
        self.options = options
        try:
            klass = Platforms.MAP[os.name][os.uname()[0]]
        except KeyError:
            raise UnsupportedPlatform()

    def __enter__ (self):
        self.driver = Platforms.MAP[os.name][os.uname()[0]](self.options.port_count)
        self.driver.setup_interfaces()
        return self.driver

    def __exit__ (self, extype, value, tb):
        self.driver.teardown_interfaces()


class Switch(object):
    def __init__ (self, options, driver):
        self.options = options
        self.driver = driver

        try:
            klass = Switches.MAP[options.switch]
        except KeyError:
            raise UnsupportedSwitch(options.switch)

    def __enter__ (self):
        self.switch = Switches.MAP[self.options.switch](self.driver.get_interfaces(), self.options)
        return self.switch

    def __exit__ (self, extype, value, tb):
        self.switch.stop()

