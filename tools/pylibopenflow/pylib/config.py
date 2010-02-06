
# of_message specific controls

# Do not include any arrays marked [0]
IGNORE_ZERO_ARRAYS = 1

# Do not include the ofp_header as a member in any structure
# This allows messages to be consistently generated as:
#   explicit header declaration
#   core member declaration
#   variable length data
IGNORE_OFP_HEADER = 1

# Generate object equality functions
GEN_OBJ_EQUALITY = 1

# Generate object show functions
GEN_OBJ_SHOW = 1

# Generate lists of enum values
GEN_ENUM_VALUES_LIST = 0

# Generate dictionary of enum strings to values
GEN_ENUM_DICTIONARY = 1
