"""
Fragment common to generating instructions and actions
"""

import re
from class_maps import class_to_members_map


template_no_list = """
class --OBJ_TYPE--_--TYPE--(--PARENT_TYPE--):
    \"""
    Wrapper class for --TYPE-- --OBJ_TYPE-- object

    --DOC_INFO--
    \"""
    def __init__(self):
        --PARENT_TYPE--.__init__(self)
        self.type = --ACT_INST_NAME--
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "--OBJ_TYPE--_--TYPE--\\n"
        outstr += --PARENT_TYPE--.show(self, prefix)
        return outstr
"""

def gen_class(t, parent, obj_type, template=None):
    if not parent in class_to_members_map.keys():
        doc_info = "Unknown parent action/instruction class: " + parent
    else:
        doc_info = "Data members inherited from " + parent + ":\n"
    for var in class_to_members_map[parent]:
        doc_info += "    @arg " + var + "\n"
    if obj_type == "action":
        name = "OFPAT_" + t.upper()
    else:
        name = "OFPIT_" + t.upper()
    if template is None:
        template = template_no_list
    to_print = re.sub('--TYPE--', t, template)
    to_print = re.sub('--OBJ_TYPE--', obj_type, to_print)
    to_print = re.sub('--PARENT_TYPE--', parent, to_print)
    to_print = re.sub('--ACT_INST_NAME--', name, to_print)
    to_print = re.sub('--DOC_INFO--', doc_info, to_print)
    print to_print
