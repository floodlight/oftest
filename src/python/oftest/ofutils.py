
"""
Utilities for the OpenFlow test framework
"""

import random
import time

def gen_xid():
    return random.randrange(1,0xffffffff)

"""
Wait on a condition variable until the given function returns non-None or a timeout expires.
The condition variable must already be acquired.
There is deliberately no support for an infinite timeout.
TODO: get the default timeout from configuration
"""
def timed_wait(cv, fn, timeout=10):
    end_time = time.time() + timeout
    while True:
        if time.time() > end_time:
            return None

        val = fn()
        if val != None:
            return val

        remaining_time = end_time - time.time()
        cv.wait(remaining_time)
