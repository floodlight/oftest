"""
veth8 platform

This platform uses 8 veth pairs. The switch should connect to veth0, veth2, ..., veth14.
"""

def platform_config_update(config):
    """
    Update configuration for the local platform

    @param config The configuration dictionary to use/update
    """

    config['port_map'] = {
        1: 'veth1',
        2: 'veth3',
        3: 'veth5',
        4: 'veth7',
        5: 'veth9',
        6: 'veth11',
        7: 'veth13',
        8: 'veth15',
    }
