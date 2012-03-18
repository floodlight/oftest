
"""
Utilities for the OpenFlow test framework
"""

import random

def gen_xid():
    return random.randrange(1,0xffffffff)
