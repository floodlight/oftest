import aspects
import os
from oftest.cstruct import *
import ofProfile.profile
import oftest.testutils
from oftest.parse import *


proxy_dir = os.path.dirname(os.path.realpath(__file__))

"""         
test_runner_decorator : decorator of unit unittest.TextTestRunner.run.
                    Saves the name of the test case being run.
"""
class test_runner_decorator:
    _test_runner_decorator = None
    
    def __init__(self):
        self.profile = ofProfile.profile.profile.get_instance()
        self.test = None
    
    @classmethod    
    def get_instance(self):
        if test_runner_decorator._test_runner_decorator is None:
            test_runner_decorator._test_runner_decorator =  test_runner_decorator()
        return test_runner_decorator._test_runner_decorator
    
    def around_method(self,*a, **kw):
        self.current_test = a[1]._tests[0].id()
        self.current_test = self.current_test[:self.current_test.index('runTest')-1] 
        yield aspects.proceed(*a, **kw)
        
    def get_current_test(self):
        return self.current_test
    
""" 
packet_to_flow_match_decorator : decorator of parse.packet_to_flow_match.
                                Updates ofp_match based on entries from profile file.
"""
class packet_to_flow_match_decorator:
    def __init__(self):
        self.test_runner_decorator = test_runner_decorator.get_instance()
        self.profile = ofProfile.profile.profile.get_instance()
            
    def create_decorator(self, arg_packet_to_flow_match):
        def around(packet):
            self.current_test = self.test_runner_decorator.get_current_test()
            match =  arg_packet_to_flow_match(packet)
            
            updated_match = self.update_wildcards(match)
            updated_match = self.update_match_fields(self.current_test,updated_match)
            
            return updated_match    
        return around
    
    
    def update_wildcards(self,match):
        disabled_match_fields = self.profile.get_profile_disabled_match_fields()
        
        for disabled_match_field in disabled_match_fields:
            if disabled_match_field == 'tp_src':
                match.wildcards &= OFPFW_TP_SRC
                    
            if disabled_match_field == 'tp_dst':
                match.wildcards &= OFPFW_TP_DST
                
            if disabled_match_field == 'dl_src':
                match.wildcards &= OFPFW_DL_SRC
                
            if disabled_match_field == 'dl_dst':
                match.wildcards &= OFPFW_DL_DST
                    
            if disabled_match_field == 'nw_src':
                match.wildcards &= OFPFW_NW_SRC_MASK
                
            if disabled_match_field == 'nw_dst':
                match.wildcards &= OFPFW_NW_DST_MASK 
        
        return match
        
    def update_match_fields(self,current_test,match):
        profile_match = self.profile.get_profile_match(self.current_test)
        profile_match_map = profile_match.get_map()
        
        if profile_match_map is not None:
            if profile_match_map.has_key('dl_src'):
                match.dl_src = parse_mac(profile_match_map.get('dl_src'))
            
            if profile_match_map.has_key('dl_dst'):
                match.dl_dst = parse_mac(profile_match_map.get('dl_dst'))
                    
            if profile_match_map.has_key('nw_src'):
                match.nw_src = parse_ip(profile_match_map.get('nw_src'))
            
            if profile_match_map.has_key('nw_dst'):
                match.nw_dst = parse_ip(profile_match_map.get('nw_dst'))
                    
            if profile_match_map.has_key('tp_src'):
                match.tp_src = profile_match_map.get('tp_src')
            
            if profile_match_map.has_key('tp_dst'):
                match.tp_dst = profile_match_map.get('tp_dst')
        else:
            print 'profile match is None !!'
        
        return match