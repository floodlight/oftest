from copy import deepcopy
from oftest import config
from unittest import TextTestRunner
from unittest import _TextTestResult

import sys

class ConformanceTextTestRunner(TextTestRunner):
    """
    Extended version of TextTestRunner to provide a modified
    ConformanceTextTestResult class. Modified result class adds
    support for manditory and optional testcases.
    """
    def __init__(self, stream=sys.stderr, descriptions=True, verbosity=1):
        TextTestRunner.__init__(self, stream, descriptions, verbosity)

    def _makeResult(self):
        """
        Returns a custom TestResult class meant to record
        optional and manditory test case results.
        """
        return ConformanceTextTestResult(self.stream, self.descriptions, self.verbosity)


class ConformanceTextTestResult(_TextTestResult):
    """
    An extention of TestResult to consider mandatory and optional
    testcases. Also included is the skipped attribute, which is
    not included in python 2.6.
    """
    def __init__(self, stream, descriptions, verbosity):
        _TextTestResult.__init__(self, stream, descriptions, verbosity)
        self.result = {}
        self.mandatory_successes = []
        self.mandatory_failures = []
        self.optional_successes = []
        self.optional_failures = []

    def addFailure(self, test, err):
        """
        Adds the pair (test, err) to either mandatory_successes
        or mandatory_failures depending on requirement specified.
        """
        _TextTestResult.addFailure(self, test, err)
        try:
            if test.mandatory:
                self.mandatory_failures.append( (test, err) )
                return
        except AttributeError:
            pass
        self.optional_failures.append( (test, err) )

    def addSuccess(self, test):
        """
        Adds the pair (test, err) to either optional_successes
        or optional_failures depending on requirement specified.
        """
        _TextTestResult.addSuccess(self, test)
        testname = test.__class__.__name__
        group_no = testname[3:].split("No")[0]
        self.saveResult(testname, group_no, "passed")

    def saveResult(self, testname, group_no, testcase_result, testcase_trace=""):
        """
        Saves the results of the test in json form. These results
        can then be used to generate a generic report. Results
        are only published if command line option --publish is
        specified.
        """
        profile = ""
        tmp_result = {"result": testcase_result "traceback": testcase_trace}
        profile_total = {"total": 0, "passed": 0, "failed": 0, "error": 0}
        total = {"mandatory": deepcopy(profile_total), "optional": deepcopy(profile_total)}

        # Initialize group data structure if doesn't exist
        if not group_no in self.result["groups"]:
            self.result["groups"][group_no] = {"total": deepcopy(total), "tests": {}}
        # If test already exists rollback counters
        if testname in self.result["groups"][group_no]["tests"]:
            old_testcase = self.result["groups"][group_no]["tests"][testname]
            old_profile = "mandatory" if old_testcase["mandatory"] else "optional"
            old_result = old_testcase["result"]
            self.result["total"][old_profile]["total"] -= 1
            self.result["total"][old_profile][old_result] -= 1
            self.result["groups"][group_no]["total"][old_profile]["total"] -= 1
            self.result["groups"][group_no]["total"][old_profile][old_result] -= 1
        # Update counters and save asserstions
        try:
            if test.mandatory:
                profile = "mandatory"
                tmp_result["mandatory"] = True
        except AttributeError:
            profile = "optional"
            tmp_result["mandatory"] = False
        self.result["total"][profile]["total"] += 1
        self.result["total"][profile][testcase_result] += 1
        self.result["groups"][group_no]["total"][profile]["total"] += 1
        self.result["groups"][group_no]["total"][profile][testcase_result] += 1
        # TODO::Save to file
