
"""
Utilities for the OpenFlow test framework
"""

import random
import time

default_timeout = None # set by oft

def gen_xid():
    return random.randrange(1,0xffffffff)

"""
Wait on a condition variable until the given function returns non-None or a timeout expires.
The condition variable must already be acquired.
The timeout value -1 means use the default timeout.
There is deliberately no support for an infinite timeout.
TODO: get the default timeout from configuration
"""
def timed_wait(cv, fn, timeout=-1):
    if timeout == -1:
        # TODO make this configurable
        timeout = default_timeout

    end_time = time.time() + timeout
    while True:
        val = fn()
        if val != None:
            return val

        remaining_time = end_time - time.time()
        cv.wait(remaining_time)

        if time.time() > end_time:
            return None
