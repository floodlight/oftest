"""
Platform configuration file
platform == remote
"""

remote_port_map = {
    23 : "eth2",
    24 : "eth3",
    25 : "eth4",
    26 : "eth5"
    }

def platform_config_update(config):
    """
    Update configuration for the remote platform

    @param config The configuration dictionary to use/update
    This routine defines the port map used for this configuration
    """

    global remote_port_map
    config["port_map"] = remote_port_map.copy()
    config["caps_table_idx"] = 0
