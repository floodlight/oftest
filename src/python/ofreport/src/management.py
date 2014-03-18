from copy import deepcopy
from util import *

class Management(object):
    def __init__(self, metadata, report_data, spec_data, template):
        """
        # Data to pass to template
        {
        "spec" : {"Grp40No120" : {}, ...},
        "40" : {"mandatory": {}, "optional": {}},
        "60" : {"mandatory": {}, "optional": {}},
        "total" : {"mandatory": {}, "optional": {}},
        "groups" : [ ("40", ["Grp40No120", {"test_no", "profile", "name", "desc", "result"}]), ... ]
        }
        """
        self.report_data = deepcopy(report_data)
        self.report_data['spec'] = spec_data
        self.report_data['meta'] = metadata
        self.template = template
        for k in self.report_data["groups"]:
            self.report_data["groups"][k]["tests"] = sorted(self.report_data["groups"][k]["tests"].iteritems())
        self.report_data["groups"] = sorted(self.report_data["groups"].iteritems())

    def save(self):
        html = self.template.render(self.report_data)
        f = open('{0}management.html'.format(PUBLISH_DIR), 'w')
        f.write(html.encode('utf-8'))
        f.close()
