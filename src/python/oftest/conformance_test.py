from unittest import TextTestRunner
from unittest import TextTestResult


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


class ConformanceTextTestResult(TextTestResult):
    """
    An extention of TestResult to consider mandatory and optional
    testcases. Also included is the skipped attribute, which is
    not included in python 2.6.
    """
    def __init__(self, stream, descriptions, verbosity):
        TextTestResult.__init__(self, stream, descriptions, verbosity)
        self.mandatory_successes = []
        self.mandatory_failures = []
        self.optional_successes = []
        self.optional_failures = []

    def addFailure(self, test, err):
        """
        Adds the pair (test, err) to either mandatory_successes
        or mandatory_failures depending on requirement specified.
        """
        TextTestResult.addFailure(self, test, err)
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
        TextTestResult.addSuccess(self, test)
        try:
            if test.mandatory:
                self.mandatory_successes.append(test)
                return
        except AttributeError:
            pass
        self.optional_successes.append(test)
