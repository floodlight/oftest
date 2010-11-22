#!/usr/bin/python


import os
import signal
import subprocess
import unittest

class OFPSTest(unittest.TestCase):
    
    Tests = ['Echo', 'EchoWithData', 'PacketIn', 'PacketOut', 'FeaturesRequest']
    TestDir='.'

    def setUp(self):
        log = open('ofps_regression.log','w+')
        self.switch = subprocess.Popen(OFPSTest.TestDir + "/run_switch.py",stdout=log, stderr=log)
        print "Started ofps via run_switch.py on pid: %d -- logging to ofps_regression.log" % (self.switch.pid)
    
    def runTest(self):
        print "Running oft with known list of working tests"
        working = ','.join(OFPSTest.Tests)
        subprocess.call([OFPSTest.TestDir + "/oft",'--verbose','--test-spec=%s' % (working)])
    
    def tearDown(self):
        if self.switch :
            print "Killing switch on pid: %d" % (self.switch.pid)
            os.kill(self.switch.pid,signal.SIGINT)




if __name__ == '__main__':
    unittest.main()
