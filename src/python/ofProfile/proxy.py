import aspects
import os
import profile

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
    
 
class simple_tcp_packet_decorator:
    def __init__(self,arg_profile=None,arg_test_runner_proxy=None):
        if arg_profile is None:
            self.profile = profile.profile()
        else:
            self.profile = arg_profile
            
        if arg_test_runner_proxy is None:
            self.test_runner_proxy = test_runner_decorator(self.profile)
        else:
            self.test_runner_proxy = arg_test_runner_proxy
            
    def create_decorator(self, arg_simple_tcp_packet):
        def around():
            # TODO : add code to use profile data 
            
            test = self.test_runner_proxy.get_current_test()
            #profile_match =  self.profile.get_profile_match(test)
            
        return around() 

