"""
No-ingress action profile

Profile for switch that does not support the IN_PORT port
in the output action.

We also don't run the port config modify test for this profile.
"""

#@var skip_test_list The list of tests to skip for this run
skip_test_list = [
    "PortConfigMod",
    "FloodMinusPort",
    "ModifyL2DstIngressMC",
    "ModifyL2DstIngress",
    "DirectMC",
    "AllPlusIngress",
    "FloodPlusIngress"
]
