# @author Jonathan Stout
from util import *

class Testgroup(object):
    def __init__(self, group_no, metadata, report_data, template):
        """
        report_data: All recorded data included in the test group.
        {
        'analysis': "", # testgroup
        'overview': "", # testgroup
        }
        """
        # Save Testgroup Fields
        report_data['meta'] = metadata
        report_data['group'] = group_no

        sorted_tests = []
        for k, v in report_data['tests'].iteritems():
            test_no = str(k.split("No")[1])
            if not str.isdigit(test_no[-1]):
                test_no = test_no[:-1]
            sorted_tests.append( (int(test_no), k, v) )

        report_data['tests'] = sorted(sorted_tests, key=lambda t: t[0])
        #print report_data['tests']

        for k, test, val in report_data['tests']:
            overview = get_html('{0}.html'.format(OVERVIEW_DIR + test))
            val['overview'] = overview
            analysis = get_html('{0}.html'.format(ANALYSIS_DIR + test))
            val['analysis'] = analysis
            logs = get_html('{0}.log'.format(LOG_DIR + test + '/testcase'))
            val['logs'] = logs
            caplinks = get_caplinks(LOG_DIR + test + '/',test)
            val['caplinks'] = caplinks
        self.group_no = group_no
        self.report_data = report_data
        self.template = template
        

    def savepdf(self):
        html = self.template.render(self.report_data)
        f = open('{0}Grp{1}.html'.format(PUBLISH_PDFGROUP_DIR, self.group_no), 'w')
        f.write(html.encode('utf-8'))
        f.close()


    def save(self):
        html = self.template.render(self.report_data)
        f = open('{0}Grp{1}.html'.format(PUBLISH_GROUP_DIR, self.group_no), 'w')
        f.write(html.encode('utf-8'))
        f.close()
   
