
# of_message specific controls

# Do not include any arrays marked [0]
IGNORE_ZERO_ARRAYS = True

# Do not include the ofp_header as a member in any structure
# This allows messages to be consistently generated as:
#   explicit header declaration
#   core member declaration
#   variable length data
IGNORE_OFP_HEADER = True

# Generate object equality functions
GEN_OBJ_EQUALITY = True

# Generate object show functions
GEN_OBJ_SHOW = True

# Generate lists of enum values
GEN_ENUM_VALUES_LIST = False

# Generate dictionary of enum strings to values
GEN_ENUM_DICTIONARY = True

# Auxilary info:  Stuff written to stdout for additional processing
# Currently generates a (python) map from a class to a list of
# the data members; used for documentation
GEN_AUX_INFO = True
