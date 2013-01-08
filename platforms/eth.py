"""
Eth platform

This platform uses the --interface command line option to choose the ethernet interfaces.
"""

def platform_config_update(config):
    """
    Update configuration for the local platform

    @param config The configuration dictionary to use/update
    """

    port_map = {}

    for (ofport, interface) in config["interfaces"]:
        port_map[ofport] = interface

    # Default to a veth configuration compatible with the reference switch
    if not port_map:
        port_map = {
            1: 'veth1',
            2: 'veth3',
            3: 'veth5',
            4: 'veth7',
        }

    config['port_map'] = port_map
