import aspects
import os
import profile
import parse

proxy_dir = os.path.dirname(os.path.realpath(__file__))

""" 
test_runner_decorator : decorator of unit unittest.TextTestRunner.run.
                    Saves the name of the test case being run.
"""
class test_runner_decorator:
    def __init__(self,arg_profile = None):
        if arg_profile is None:
            self.profile = profile.profile()
        else:
            self.profile = arg_profile
            
        self.test = None
    
    def test_runner_decorator(self,*a, **kw):
        self.current_test = a[1]._tests[0].id()
        self.current_test = self.current_test[:self.current_test.index('runTest')-1] 
        yield aspects.proceed(*a, **kw)
        
    def get_current_test(self):
        return self.test
    
""" 
packet_to_flow_match_decorator : decorator of parse.packet_to_flow_match.
                                Updates ofp_match based on entries from profile file.
"""
class packet_to_flow_match_decorator:
    def __init__(self,arg_profile=None,arg_test_runner_proxy=None):
        if arg_profile is None:
            self.profile = profile.profile()
        else:
            self.profile = arg_profile
            
        if arg_test_runner_proxy is None:
            self.test_runner_proxy = test_runner_decorator(self.profile)
        else:
            self.test_runner_proxy = arg_test_runner_proxy
            
    def create_decorator(self, arg_packet_to_flow_match):
        def around():
            # TODO : add code to use profile data 
            self.current_test = self.test_runner_proxy.get_current_test()
            match =  arg_packet_to_flow_match()
            
            updated_match = self.update_wildcards(match)
            updated_match = self.update_match_fields(updated_match)
            
            return updated_match    
        return around()
    
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
                match.wildcards &= OFPFW_NW_SRC
                
            if disabled_match_field == 'nw_dst':
                match.wildcards &= OFPFW_NW_DST 
        
        return match
        
    def update_match_fields(self,current_test,match):
        profile_match = self.profile.get_profile_match(self.current_test)
        
        if profile_match is not None:
            if profile_match.has_key('dl_src'):
                match.dl_src = parse_mac(profile_match.get('dl_src'))
            
            if profile_match.has_key('dl_dst'):
                match.dl_dst = parse_mac(profile_match.get('dl_dst'))
                    
            if profile_match.has_key('nw_src'):
                match.nw_src = parse_ip(profile_match.get('nw_src'))
            
            if profile_match.has_key('nw_dst'):
                match.nw_dst = parse_ip(profile_match.get('nw_dst'))
                    
            if profile_match.has_key('tp_src'):
                match.tp_src = profile_match.get('tp_src')
            
            if profile_match.has_key('tp_dst'):
                match.tp_dst = profile_match.get('tp_dst')
            
        return match