"""
OpenFlow Test Framework

Framework assert definition
"""

import sys
import logging

def oft_assert(condition, string):
    """
    Test framework assertion check

    @param condition The boolean condition to check
    @param string String to print if error

    If condition is not true, it is considered a test framework
    failure and exit is called.

    This assert is meant to represent a violation in the 
    assumptions of how the test framework is supposed to work
    (for example, an inconsistent packet queue state) rather than
    a test failure.
    """
    if not condition:
        logging.critical("Internal error: " + string)
        sys.exit(1)

