"""
Local platform

This platform uses veth pairs to send packets to and from a userspace
switch. The switch should be connected to veth0, veth2, veth4, and veth6.
"""

def platform_config_update(config):
    """
    Update configuration for the local platform

    @param config The configuration dictionary to use/update
    """
    base_of_port = 1
    base_if_index = 1
    port_count = 4

    port_map = {}
    # Use every other veth interface (veth1, veth3, ...)
    for idx in range(port_count):
        port_map[base_of_port + idx] = "veth%d" % (base_if_index + 2 * idx)
    config['port_map'] = port_map
