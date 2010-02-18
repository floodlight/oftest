"""This module generate Python code for OpenFlow structs.

(C) Copyright Stanford University
Date December 2009
Created by ykk
"""
import cpythonize
from config import *

class rules(cpythonize.rules):
    """Class that specify rules for pythonization of OpenFlow messages

    (C) Copyright Stanford University
    Date December 2009
    Created by ykk
    """
    def __init__(self, ofmsg):
        """Initialize rules
        """
        cpythonize.rules.__init__(self)
        ##Reference to ofmsg
        self.__ofmsg = ofmsg
        ##Default values for members
        self.default_values[('ofp_header','version')] = self.__ofmsg.get_value('OFP_VERSION')
        self.default_values[('ofp_switch_config',\
                             'miss_send_len')] = self.__ofmsg.get_value('OFP_DEFAULT_MISS_SEND_LEN')
        for x in ['ofp_flow_mod','ofp_flow_expired','ofp_flow_stats']:
            self.default_values[(x,'priority')] = self.__ofmsg.get_value('OFP_DEFAULT_PRIORITY')
        #Default values for struct
        self.default_values[('ofp_packet_out','buffer_id')] = 0xffffffff
        self.struct_default[('ofp_flow_mod',
                             'header')] = ".type = OFPT_FLOW_MOD"
#                             'header')] = ".type = "+str(self.__ofmsg.get_value('OFPT_FLOW_MOD'))
        ##Macros to exclude
        self.excluded_macros = ['OFP_ASSERT(EXPR)','OFP_ASSERT(_EXPR)','OFP_ASSERT',
                                'icmp_type','icmp_code','OFP_PACKED',
                                'OPENFLOW_OPENFLOW_H']
        ##Enforce mapping
        if GEN_ENUM_VALUES_LIST:
            self.enforced_maps['ofp_header'] = [ ('type','ofp_type_values') ]
        elif GEN_ENUM_DICTIONARY:
            self.enforced_maps['ofp_header'] = \
                [ ('type','ofp_type_map.keys()') ]
        
class pythonizer(cpythonize.pythonizer):
    """Class that pythonize C structures of OpenFlow messages

    (C) Copyright Stanford University
    Date December 2009
    Created by ykk
    """
    def __init__(self, ofmsg):
        """Initialize
        """
        ofrules =  rules(ofmsg)
        cpythonize.pythonizer.__init__(self, ofmsg, ofrules)
        ##Reference to OpenFlow message class
        self.__ofmsg = ofmsg
