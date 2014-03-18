

#!/usr/bin/python
# @author Jonathan Stout
from jinja2 import Environment, PackageLoader
from src.suite import Testsuite
from src.group import Testgroup
from src.management import Management
from src.util import *


if __name__ == '__main__':
    metadata = get_json(METADATA_LOC)
    reportdata = get_json(LOG_LOC)
    reportdata1 = get_json(LOG_LOC)
    specdata = get_json(SPEC_LOC)
    create_testreport_dir()
    env = Environment(loader=PackageLoader('ofreport', 'views'))

    management_template = env.get_template('management.html')
    management = Management(metadata, reportdata, specdata, management_template)
    management.save()


    # Generate PDF suite results
    testsuite_template = env.get_template('suite.html')
    reportdata['for_web'] = False
    reportdata['for_suite'] = True
    testsuite_pdf = Testsuite(metadata, reportdata, testsuite_template)
    testsuite_pdf.save()

    testgroup_template = env.get_template('group.html')
    # Create censored PDF
    for k, v in reportdata['groups']:
        v['profile'] = reportdata['profile']
        v['spec'] = specdata
        # Renders links and confidential content.
        v['for_web'] = False
        v['for_suite'] = False
        testgroup = Testgroup(k, metadata, v, testgroup_template)
        testgroup.savepdf()

    create_pdf()

    # Create HTML suite results
    reportdata1['for_web'] = True
    v['for_suite'] = True
    testsuite = Testsuite(metadata, reportdata1, testsuite_template)
    testsuite.save()

    # Create uncensored HTML report
    for k, v in reportdata1['groups']:
        v['profile'] = reportdata1['profile']
        v['spec'] = specdata
        # Renders links and confidential content.
        v['for_web'] = True
        v['for_suite'] = False
        testgroup = Testgroup(k, metadata, v, testgroup_template)
        testgroup.save()

try:
    import excel
except:
    print "Could not find excel.py"
