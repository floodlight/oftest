
# Class to array member map
class_to_members_map = {
    'ofp_action_mpls_tc'            : [
                                       'type',
                                       'len',
                                       'mpls_tc'
                                      ],
    'ofp_aggregate_stats_reply'     : [
                                       'packet_count',
                                       'byte_count',
                                       'flow_count'
                                      ],
    'ofp_action_set_queue'          : [
                                       'type',
                                       'len',
                                       'queue_id'
                                      ],
    'ofp_table_stats'               : [
                                       'table_id',
                                       'name',
                                       'wildcards',
                                       'match',
                                       'instructions',
                                       'write_actions',
                                       'apply_actions',
                                       'config',
                                       'max_entries',
                                       'active_count',
                                       'lookup_count',
                                       'matched_count'
                                      ],
    'ofp_table_mod'                 : [
                                       'table_id',
                                       'config'
                                      ],
    'ofp_flow_removed'              : [
                                       'cookie',
                                       'priority',
                                       'reason',
                                       'table_id',
                                       'duration_sec',
                                       'duration_nsec',
                                       'idle_timeout',
                                       'packet_count',
                                       'byte_count',
                                       'match'
                                      ],
    'ofp_instruction_actions'       : [
                                       'type',
                                       'len'
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
    'ofp_action_nw_ecn'             : [
                                       'type',
                                       'len',
                                       'nw_ecn'
                                      ],
    'ofp_group_mod'                 : [
                                       'command',
                                       'type',
                                       'group_id'
                                      ],
    'ofp_port_stats_request'        : [
                                       'port_no'
                                      ],
    'ofp_stats_request'             : [
                                       'type',
                                       'flags'
                                      ],
    'ofp_instruction'               : [
                                       'type',
                                       'len'
                                      ],
    'ofp_group_stats_request'       : [
                                       'group_id'
                                      ],
    'ofp_experimenter_header'       : [
                                       'experimenter'
                                      ],
    'ofp_aggregate_stats_request'   : [
                                       'table_id',
                                       'out_port',
                                       'out_group',
                                       'cookie',
                                       'cookie_mask',
                                       'match'
                                      ],
    'ofp_queue_get_config_request'  : [
                                       'port'
                                      ],
    'ofp_instruction_experimenter'  : [
                                       'type',
                                       'len',
                                       'experimenter'
                                      ],
    'ofp_action_nw_ttl'             : [
                                       'type',
                                       'len',
                                       'nw_ttl'
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
    'ofp_action_experimenter_header' : [
                                       'type',
                                       'len',
                                       'experimenter'
                                      ],
    'ofp_queue_get_config_reply'    : [
                                       'port'
                                      ],
    'ofp_queue_prop_header'         : [
                                       'property',
                                       'len'
                                      ],
    'ofp_packet_in'                 : [
                                       'buffer_id',
                                       'in_port',
                                       'in_phy_port',
                                       'total_len',
                                       'reason',
                                       'table_id'
                                      ],
    'ofp_instruction_write_metadata' : [
                                       'type',
                                       'len',
                                       'metadata',
                                       'metadata_mask'
                                      ],
    'ofp_flow_stats'                : [
                                       'length',
                                       'table_id',
                                       'duration_sec',
                                       'duration_nsec',
                                       'priority',
                                       'idle_timeout',
                                       'hard_timeout',
                                       'cookie',
                                       'packet_count',
                                       'byte_count',
                                       'match'
                                      ],
    'ofp_action_mpls_label'         : [
                                       'type',
                                       'len',
                                       'mpls_label'
                                      ],
    'ofp_flow_stats_request'        : [
                                       'table_id',
                                       'out_port',
                                       'out_group',
                                       'cookie',
                                       'cookie_mask',
                                       'match'
                                      ],
    'ofp_header'                    : [
                                       'version',
                                       'type',
                                       'length',
                                       'xid'
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
    'ofp_match'                     : [
                                       'type',
                                       'length',
                                       'in_port',
                                       'wildcards',
                                       'dl_src',
                                       'dl_src_mask',
                                       'dl_dst',
                                       'dl_dst_mask',
                                       'dl_vlan',
                                       'dl_vlan_pcp',
                                       'dl_type',
                                       'nw_tos',
                                       'nw_proto',
                                       'nw_src',
                                       'nw_src_mask',
                                       'nw_dst',
                                       'nw_dst_mask',
                                       'tp_src',
                                       'tp_dst',
                                       'mpls_label',
                                       'mpls_tc',
                                       'metadata',
                                       'metadata_mask'
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
    'ofp_packet_queue'              : [
                                       'queue_id',
                                       'len'
                                      ],
    'ofp_port'                      : [
                                       'port_no',
                                       'hw_addr',
                                       'name',
                                       'config',
                                       'state',
                                       'curr',
                                       'advertised',
                                       'supported',
                                       'peer',
                                       'curr_speed',
                                       'max_speed'
                                      ],
    'ofp_action_dl_addr'            : [
                                       'type',
                                       'len',
                                       'dl_addr'
                                      ],
    'ofp_bucket_counter'            : [
                                       'packet_count',
                                       'byte_count'
                                      ],
    'ofp_queue_prop_min_rate'       : [
                                       'prop_header',
                                       'rate'
                                      ],
    'ofp_bucket'                    : [
                                       'len',
                                       'weight',
                                       'watch_port',
                                       'watch_group'
                                      ],
    'ofp_switch_features'           : [
                                       'datapath_id',
                                       'n_buffers',
                                       'n_tables',
                                       'capabilities',
                                       'reserved'
                                      ],
    'ofp_action_pop_mpls'           : [
                                       'type',
                                       'len',
                                       'ethertype'
                                      ],
    'ofp_flow_mod'                  : [
                                       'cookie',
                                       'cookie_mask',
                                       'table_id',
                                       'command',
                                       'idle_timeout',
                                       'hard_timeout',
                                       'priority',
                                       'buffer_id',
                                       'out_port',
                                       'out_group',
                                       'flags',
                                       'match'
                                      ],
    'ofp_packet_out'                : [
                                       'buffer_id',
                                       'in_port',
                                       'actions_len'
                                      ],
    'ofp_instruction_goto_table'    : [
                                       'type',
                                       'len',
                                       'table_id'
                                      ],
    'ofp_action_nw_addr'            : [
                                       'type',
                                       'len',
                                       'nw_addr'
                                      ],
    'ofp_action_group'              : [
                                       'type',
                                       'len',
                                       'group_id'
                                      ],
    'ofp_group_stats'               : [
                                       'length',
                                       'group_id',
                                       'ref_count',
                                       'packet_count',
                                       'byte_count'
                                      ],
    'ofp_action_vlan_pcp'           : [
                                       'type',
                                       'len',
                                       'vlan_pcp'
                                      ],
    'ofp_action_push'               : [
                                       'type',
                                       'len',
                                       'ethertype'
                                      ],
    'ofp_group_desc_stats'          : [
                                       'length',
                                       'type',
                                       'group_id'
                                      ],
    'ofp_error_msg'                 : [
                                       'type',
                                       'code'
                                      ],
    'ofp_action_mpls_ttl'           : [
                                       'type',
                                       'len',
                                       'mpls_ttl'
                                      ],
    '_ignore' : []
}
