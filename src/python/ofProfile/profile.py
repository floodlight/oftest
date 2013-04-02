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
import generated.test_profiles as test_profiles

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
test_profiles    : ofp match field data for the test.

** profile_match is used distinguish from ofp_match.
"""

PROFILE_XSD_XML_CONFIG = {
    'match_field_test':  'match_field_test.xml',                 
    'switch_profile' : 'switch_profile.xml',            
    'test_profiles' :'test_profiles.xml' ,                 
}


"""
profile_match stores the OF match data from profile file.

The XML files are parsed and match data from profile file
is stored in 'match_data_map' of profile_match.

"""
class profile_match:
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
    
    def get_profile_match(self):
        return self.match_data_map
    
    
class profile:
    def __init__(self,profile_file=None):
        self.profile_disabled_match_fields = []
        self.profile_match_field_test_map = {}
        self.profile_test_match_map = {}        

    def parse(self):
        # reads the xml files.
        
        try:
            if PROFILE_XSD_XML_CONFIG.has_key('match_field_test'):
                self.match_field_test = match_field_test.CreateFromDocument(file(os.path.join(xml_dir,PROFILE_XSD_XML_CONFIG['match_field_test'])).read()) 
            
            if PROFILE_XSD_XML_CONFIG.has_key('switch_profile'):
                self.switch_profile = switch_profile.CreateFromDocument(file(os.path.join(xml_dir,PROFILE_XSD_XML_CONFIG['switch_profile'])).read())
            
            if PROFILE_XSD_XML_CONFIG.has_key('test_profiles'):
                self.test_profiles = test_profiles.CreateFromDocument(file(os.path.join(xml_dir,PROFILE_XSD_XML_CONFIG['test_profiles'])).read())
        except:
                traceback.print_exc()
                
        self.process_match_field_test()
        self.process_switch_profile()
        self.process_test_profiles()
       

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
                self.profile_disabled_match_fields.append(match_field.property_name)
    
    def process_test_profiles(self):
        
        #parsing the test_profiles.xml file storing in profile_test_match_map.
        for test_idx in range(len(self.test_profiles.test_profile[0].test)):
            test = self.test_profiles.test_profile[0].test[test_idx]
            
            for match_fields_idx in range(len(self.test_profiles.test_profile[0].test[test_idx].match_fields)):
                for match_field_idx in range(len(self.test_profiles.test_profile[0].test[test_idx].match_fields[match_fields_idx].match_field)):
                    
                    
                    # handle OFP 1.0
                    if OFP_VERSION  == 1.0:
                        match_field_key = self.test_profiles.test_profile[0].test[test_idx].match_fields[match_fields_idx].match_field[match_field_idx].property_name
                        match_field_val = self.test_profiles.test_profile[0].test[test_idx].match_fields[match_fields_idx].match_field[match_field_idx].property_value
                       
                        if profile_match_ofp10.match_data_map.has_key(match_field_key):
                            profile_match_ofp10.match_data_map[match_field_key] = match_field_val
                            profile_match = profile_match_ofp10.get_match(test)
                            
                            if self.profile_test_match_map.contains(test):
                                profile_matches = self.profile_test_match_map.get(test)
                                profile_matches.append(profile_match)
                                self.profile_test_match_map[test] = profile_matches
                            else:
                                profile_matches = []
                                profile_matches.append(profile_match)
                                
                                self.profile_test_match_map[test] = profile_matches 
                    else:
                        pass

    
    def get_match_field(self,arg_test):
        ret_val = None
        
        for match_field in self.profile_match_field_test_map.keys():
            for test in self.profile_match_field_test_map.get(match_field):
                if arg_test == test:
                    ret_val = match_field
                    break
        return ret_val
            
    def is_profile_match_field_enabled(self,arg_match_field):
        ret_val = True
        
        for disabled_match_field in self.profile_disabled_match_fields:
            if arg_match_field == disabled_match_field:
                ret_val = False
                break
            
        return ret_val
    
    def get_profile_match(self,test):
        ret_val = None
        
        if self.profile.profile_test_match_map.has_key(test):
            ret_val = self.profile.profile_test_match_map.get(test)
        
        return ret_val
    
    def is_profile_match_defined(self,test):
        ret_val = False
        
        if self.profile.profile_test_match_map.has_key(test):
            ret_val = True
            
        return ret_val
    
    def is_test_enabled(self,test):
        ret_val = False
        
        match_field = self.get_match_field(test)
        
        if match_field is not None:
            if self.profile.is_profile_match_defined(match_field):
                ret_val = True
            
        return ret_val


    