#!/usr/bin/python

import unittest
import logging

from message_unittests import *
from instruction import *
from instruction_list import *
from packet import *

if __name__ == '__main__':
    logging.basicConfig(filename="", level=logging.DEBUG)
    unittest.main()
