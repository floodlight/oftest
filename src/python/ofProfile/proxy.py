import aspects
import os
import profile

proxy_dir = os.path.dirname(os.path.realpath(__file__))

""" 
test_runner_proxy : proxy of unit unittest.TextTestRunner.run.
                    Saves the name of the test case being run.
"""
class test_runner_proxy:
    def __init__(self,arg_profile = None):
        if arg_profile is None:
            self.profile = profile.profile()
        else:
            self.profile = arg_profile
            
        self.test = None
    
    def test_runner_proxy(self,*a, **kw):
        self.current_test = a[1]._tests[0].id()
        self.current_test = self.current_test[:self.current_test.index('runTest')-1] 
        yield aspects.proceed(*a, **kw)
        
    def get_current_test(self):
        return self.test
    

