"""
Sample profile

A profile determines run specific behavior.  It is meant to capture
variations between different switch targets.

A profile defines two target specific variables.

1. A set of tests to skip

TO BE IMPLEMENTED:

2. A set of tests to run (overriding the default "skip" priority)
optionally specifying a test parameters specific to the test run

@todo Allow a test to be run multiple times with different params
"""

#@var skip_test_list The list of tests to skip for this run
skip_test_list = []

# A list of test cases
#@var run_test_list List of tests to run which would normally be skipped
run_test_list = []

#
# Ideally, we should allow parameters to be specified
#
# run_test_list = (
#     testcase = [dict(param1), dict(param2), ...],
# )
#
# for test_dict in profile.run_test_list:
#     for test_name, test_params in test_dict.items():
#          ...
