
# Class to array member map
class_to_members_map = {
    'ofp_phy_port'                  : [
                                       'port_no',
                                       'hw_addr',
                                       'name',
                                       'config',
                                       'state',
                                       'curr',
                                       'advertised',
                                       'supported',
                                       'peer'
                                      ],
    'ofp_aggregate_stats_reply'     : [
                                       'packet_count',
                                       'byte_count',
                                       'flow_count'
                                      ],
    'ofp_table_stats'               : [
                                       'table_id',
                                       'name',
                                       'wildcards',
                                       'max_entries',
                                       'active_count',
                                       'lookup_count',
                                       'matched_count'
                                      ],
    'ofp_flow_removed'              : [
                                       'match',
                                       'cookie',
                                       'priority',
                                       'reason',
                                       'duration_sec',
                                       'duration_nsec',
                                       'idle_timeout',
                                       'packet_count',
                                       'byte_count'
                                      ],
    'ofp_port_stats'                : [
                                       'port_no',
                                       'rx_packets',
                                       'tx_packets',
                                       'rx_bytes',
                                       'tx_bytes',
                                       'rx_dropped',
                                       'tx_dropped',
                                       'rx_errors',
                                       'tx_errors',
                                       'rx_frame_err',
                                       'rx_over_err',
                                       'rx_crc_err',
                                       'collisions'
                                      ],
    'ofp_queue_stats'               : [
                                       'port_no',
                                       'queue_id',
                                       'tx_bytes',
                                       'tx_packets',
                                       'tx_errors'
                                      ],
    'ofp_action_tp_port'            : [
                                       'type',
                                       'len',
                                       'tp_port'
                                      ],
    'ofp_port_stats_request'        : [
                                       'port_no'
                                      ],
    'ofp_stats_request'             : [
                                       'type',
                                       'flags'
                                      ],
    'ofp_aggregate_stats_request'   : [
                                       'match',
                                       'table_id',
                                       'out_port'
                                      ],
    'ofp_port_status'               : [
                                       'reason',
                                       'desc'
                                      ],
    'ofp_action_header'             : [
                                       'type',
                                       'len'
                                      ],
    'ofp_port_mod'                  : [
                                       'port_no',
                                       'hw_addr',
                                       'config',
                                       'mask',
                                       'advertise'
                                      ],
    'ofp_action_vlan_vid'           : [
                                       'type',
                                       'len',
                                       'vlan_vid'
                                      ],
    'ofp_action_output'             : [
                                       'type',
                                       'len',
                                       'port',
                                       'max_len'
                                      ],
    'ofp_switch_config'             : [
                                       'flags',
                                       'miss_send_len'
                                      ],
    'ofp_action_nw_tos'             : [
                                       'type',
                                       'len',
                                       'nw_tos'
                                      ],
    'ofp_queue_get_config_reply'    : [
                                       'port'
                                      ],
    'ofp_packet_in'                 : [
                                       'buffer_id',
                                       'total_len',
                                       'in_port',
                                       'reason'
                                      ],
    'ofp_flow_stats'                : [
                                       'length',
                                       'table_id',
                                       'match',
                                       'duration_sec',
                                       'duration_nsec',
                                       'priority',
                                       'idle_timeout',
                                       'hard_timeout',
                                       'cookie',
                                       'packet_count',
                                       'byte_count'
                                      ],
    'ofp_flow_stats_request'        : [
                                       'match',
                                       'table_id',
                                       'out_port'
                                      ],
    'ofp_action_vendor_header'      : [
                                       'type',
                                       'len',
                                       'vendor'
                                      ],
    'ofp_stats_reply'               : [
                                       'type',
                                       'flags'
                                      ],
    'ofp_queue_stats_request'       : [
                                       'port_no',
                                       'queue_id'
                                      ],
    'ofp_desc_stats'                : [
                                       'mfr_desc',
                                       'hw_desc',
                                       'sw_desc',
                                       'serial_num',
                                       'dp_desc'
                                      ],
    'ofp_queue_get_config_request'  : [
                                       'port'
                                      ],
    'ofp_packet_queue'              : [
                                       'queue_id',
                                       'len'
                                      ],
    'ofp_action_dl_addr'            : [
                                       'type',
                                       'len',
                                       'dl_addr'
                                      ],
    'ofp_queue_prop_header'         : [
                                       'property',
                                       'len'
                                      ],
    'ofp_queue_prop_min_rate'       : [
                                       'prop_header',
                                       'rate'
                                      ],
    'ofp_action_enqueue'            : [
                                       'type',
                                       'len',
                                       'port',
                                       'queue_id'
                                      ],
    'ofp_switch_features'           : [
                                       'datapath_id',
                                       'n_buffers',
                                       'n_tables',
                                       'capabilities',
                                       'actions'
                                      ],
    'ofp_match'                     : [
                                       'wildcards',
                                       'in_port',
                                       'eth_src',
                                       'eth_dst',
                                       'vlan_vid',
                                       'vlan_pcp',
                                       'eth_type',
                                       'ip_dscp',
                                       'ip_proto',
                                       'ipv4_src',
                                       'ipv4_dst',
                                       'tcp_src',
                                       'tcp_dst'
                                      ],
    'ofp_header'                    : [
                                       'version',
                                       'type',
                                       'length',
                                       'xid'
                                      ],
    'ofp_vendor_header'             : [
                                       'vendor'
                                      ],
    'ofp_packet_out'                : [
                                       'buffer_id',
                                       'in_port',
                                       'actions_len'
                                      ],
    'ofp_action_nw_addr'            : [
                                       'type',
                                       'len',
                                       'nw_addr'
                                      ],
    'ofp_action_vlan_pcp'           : [
                                       'type',
                                       'len',
                                       'vlan_pcp'
                                      ],
    'ofp_flow_mod'                  : [
                                       'match',
                                       'cookie',
                                       'command',
                                       'idle_timeout',
                                       'hard_timeout',
                                       'priority',
                                       'buffer_id',
                                       'out_port',
                                       'flags'
                                      ],
    'ofp_error_msg'                 : [
                                       'type',
                                       'code'
                                      ],
    '_ignore' : []
}
