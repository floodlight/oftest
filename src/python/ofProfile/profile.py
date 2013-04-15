import sys,traceback
import os

profile_dir = os.path.dirname(os.path.realpath(__file__))

of10_dir = os.path.join(profile_dir, '..','of10')
xsd_dir = os.path.join(profile_dir,'xsd')
xml_dir = os.path.join(profile_dir,'xml')
generated_dir = os.path.join(profile_dir,'generated')

sys.path.append(of10_dir)
sys.path.append(xsd_dir)
sys.path.append(xml_dir)
sys.path.append(generated_dir)

import generated.match_field_test as match_field_test
import generated.switch_profile as switch_profile
import generated.test_profile as test_profile

#from cstruct import ofp_match as cstruct_ofp_match

""" defines version used """
OFP_VERSION=1.0

"""
PROFILE_XSD_XML_CONFIG maps keys to xml file.

keys are used as id for python obj generated from XSD.
values are name of xml files to be used with corresponding XSD.

Keys :
match_field_test : ofp match field to set of associated tests..
switch_profile   : ofp match fields that are inactive for switch .
test_profile    : ofp match field data for the test.

** profile_match is used distinguish from ofp_match.
"""

PROFILE_XSD_XML_CONFIG = {
    'match_field_test':  'match_field_test.xml',                 
    'switch_profile' : 'switch_profile.xml',            
    'test_profile' :'test_profile.xml' ,                 
}


"""
profile_match stores the OF match data from profile file.

The XML files are parsed and match data from profile file
is stored in 'match_data_map' of profile_match.

"""
class profile_match:
    def __init__(self):
        self.profile_match_data = {}
    
    def get_profile_match(self):
        pass
        

# OF 1.0   
class profile_match_ofp10(profile_match):
    match_data_map = {
        'in_port' :0,
        'dl_src' :None,
        'dl_dst' :None,
        'dl_vlan' :None,
        'dl_vlan_pcp' :None,
        'nw_tos' :0,
        'nw_proto' :None,
        'nw_src' :None,
        'nw_dst' :None,
        'tp_src' :0,
        'tp_dst' :0,  
    }
    
    def get_map(self):
        return self.profile_match_data
    
class profile:
    _profile = None
    
    def __init__(self):
        self.profile_match_fields_disabled = []
        self.profile_match_fields_enabled = []
        self.profile_match_field_test_map = {}
        self.profile_test_match_map = {}
        self.match_field_test = None
        self.test_profile = None
        self.switch_profile =  None
        
        
    @classmethod  
    def get_instance(self):
        if profile._profile is None:
            profile._profile = profile()
            profile._profile.parse()
        return profile._profile
    
    def parse(self):
        # reads the xml files.
        
        try:
            if PROFILE_XSD_XML_CONFIG.has_key('match_field_test'):
                self.match_field_test = match_field_test.CreateFromDocument(file(os.path.join(xml_dir,PROFILE_XSD_XML_CONFIG['match_field_test'])).read()) 
            
            if PROFILE_XSD_XML_CONFIG.has_key('switch_profile'):
                self.switch_profile = switch_profile.CreateFromDocument(file(os.path.join(xml_dir,PROFILE_XSD_XML_CONFIG['switch_profile'])).read())
            
            if PROFILE_XSD_XML_CONFIG.has_key('test_profile'):
                self.test_profile = test_profile.CreateFromDocument(file(os.path.join(xml_dir,PROFILE_XSD_XML_CONFIG['test_profile'])).read())
        except:
                traceback.print_exc()
                
        self.process_match_field_test()
        self.process_switch_profile()
        self.process_test_profile()
       

    def process_match_field_test(self):
        #parses the match_field_test.xml file storing in 'profile_test_match_map'.
        for match_field_idx in range(len(self.match_field_test.match_field)):
            match_field =  self.match_field_test.match_field[match_field_idx].name
            
            for test_idx in range(len(self.match_field_test.match_field[match_field_idx].test)):
                if self.profile_match_field_test_map.has_key(match_field):
                    tests =  self.profile_match_field_test_map.get(match_field)
                    tests.append(self.match_field_test.match_field[match_field_idx].test[test_idx])
                    self.profile_match_field_test_map[match_field] = tests
                else:
                    tests = []
                    tests.append(self.match_field_test.match_field[match_field_idx].test[test_idx])
                    self.profile_match_field_test_map[match_field] = tests
        
        
    def process_switch_profile(self):
        #parses the switch_profile.xml file storing in profile_disabled_match_fields.
        for match_field in self.switch_profile.match_fields[0].match_field:
            if match_field.property_value  == 'Disable':
                self.profile_match_fields_disabled.append(match_field.property_name)
            else:
                self.profile_match_fields_enabled.append(match_field.property_name)
                
                
    def process_test_profile(self):
        #parsing the test_profiles.xml file storing in profile_test_match_map.
        for test_idx in range(len(self.test_profile.test)):
            test = self.test_profile.test[test_idx].name
            
            for match_fields_idx in range(len(self.test_profile.test[test_idx].match_fields)):
                for match_field_idx in range(len(self.test_profile.test[test_idx].match_fields[match_fields_idx].match_field)):
                    
                    # handle OFP 1.0
                    if OFP_VERSION  == 1.0:
                        match_field_key = self.test_profile.test[test_idx].match_fields[match_fields_idx].match_field[match_field_idx].property_name
                        match_field_val = self.test_profile.test[test_idx].match_fields[match_fields_idx].match_field[match_field_idx].property_value
                       
                        if profile_match_ofp10.match_data_map.has_key(match_field_key):
                            if self.profile_test_match_map.has_key(test):
                                profile_match = self.profile_test_match_map.get(test)
                                profile_match.get_map()[match_field_key] = match_field_val
                                self.profile_test_match_map[test] = profile_match
                            else:
                                profile_match = profile_match_ofp10()
                                profile_match.get_map()[match_field_key] =  match_field_val   
                                self.profile_test_match_map[test] = profile_match
                    else:
                        pass


    
    def get_tests_for_match_field(self,arg_match_field):
        ret_tests = []
        
        if self.profile_match_field_test_map.has_key(arg_match_field):
            ret_tests = self.profile_match_field_test_map.get(arg_match_field)
            
        return ret_tests
        
        
    def get_profile_enabled_match_fields(self):
        return set(self.profile_match_fields_enabled)
    
    def get_profile_disabled_match_fields(self):
        return set(self.profile_match_fields_disabled)
    
    def get_profile_match(self,test):
        ret_val = None
        
        if self.profile_test_match_map.has_key(test):
            ret_val = self.profile_test_match_map.get(test)
        
        return ret_val
            
    def is_profile_match_field_enabled(self,arg_match_field):
        ret_val = True
        
        for disabled_match_field in self.profile_match_fields_disabled:
            if arg_match_field == disabled_match_field:
                ret_val = False
                break
            
        return ret_val
    
    
    def is_profile_match_defined(self,test):
        ret_val = False
        
        if self.profile.profile_test_match_map.has_key(test):
            ret_val = True
            
        return ret_val
    
    def get_disabled_tests(self):
        ret_val = []
    
        for disabled_match_field in self.get_profile_disabled_match_fields():
            tests_for_match_field = self.get_tests_for_match_field(disabled_match_field)
            
            if len(tests_for_match_field) >0:
                ret_val +=tests_for_match_field
                
        return ret_val