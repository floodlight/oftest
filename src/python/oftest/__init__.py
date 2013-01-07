'''Docstring to silence pylint; ignores --ignore option for __init__.py'''
import sys

# Global config dictionary
# Populated by oft.
config = {}

# Global DataPlane instance used by all tests.
# Populated by oft.
dataplane_instance = None

# Alias of10 modules into oftest namespace for backwards compatbility
import of10
from of10 import *
for modname in of10.__all__:
    sys.modules["oftest." + modname] = sys.modules["of10." + modname]
