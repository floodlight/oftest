# @author Jonathan Stout
from copy import deepcopy
from util import *

class Testsuite(object):
    def __init__(self, metadata, report_data, template):
        """
        Data to pass to template
        {
        "meta" : {"vendor" : "", ...},
        "analysis" : "",
        "overview" : "",
        "total" : {"mandatory": {}, "optional": {}},
        "groups": [ ("10", {"total": {}, "overview": "", "analysis": ""}), ... ]
        }
        """
        #report_data = deepcopy(report_data)
        report_data = report_data
        report_data['meta'] = metadata
        report_data['analysis'] = get_html('{0}.html'.format(ANALYSIS_DIR + '/suite'))
        report_data['overview'] = get_html('{0}.html'.format(OVERVIEW_DIR + '/suite'))
        '''for group in report_data['groups'].iterkeys():
            report_data['groups'][group]['analysis'] = get_html('{0}testgroup{1}.html'.format(ANALYSIS_DIR, group))
            report_data['groups'][group]['overview'] = get_html('{0}testgroup{1}.html'.format(OVERVIEW_DIR, group))'''
        groups = []
        
        for k, v in report_data['groups'].iteritems():
            report_data['groups'][k]['analysis'] = get_html('{0}testgroup{1}.html'.format(ANALYSIS_DIR, k))
            report_data['groups'][k]['overview'] = get_html('{0}testgroup{1}.html'.format(OVERVIEW_DIR, k))
            report_data['groups'][k]['group'] = k
            groups.append( (int(k), report_data['groups'][k]) )

        report_data['groups'] = sorted(groups, key=lambda g: g[0])
        self.report_data = report_data
        self.template = template

    def save(self):
        html = self.template.render(self.report_data)
        f = open('{0}index.html'.format(PUBLISH_DIR), 'w')
        f.write(html)
        f.close()


    def savepdf(self):
        html = self.template.render(self.report_data)
        f = open('{0}index.html'.format(PUBLISH_DIR), 'w')
        f.write(html)
        f.close()
