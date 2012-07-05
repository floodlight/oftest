import os.path
import subprocess
import signal

class OFSwitch(object):
    """
    Base class for running OpenFlow switches
    Not sure if this is useful; putting it here preemptively
    """
    Name="none"

    def __init__(self,interfaces,config):
        self.interfaces = interfaces
        self.port = config.port

    def start(self):
        """ 
        Start up all the various parts of a switch:
            should block 
        """    
        pass

    def test(self):
        """ 
        Run a self test to make sure the switch is runnable
        """
        return True

    def stop(self):
        """
        Stop any parts of the switch that could be still running
        """
        pass
   
class OFReferenceSwitch(OFSwitch):
    """
    Start up an OpenFlow reference switch
    """

    Name="reference"

    def __init__(self,interfaces,config):
        super(OFReferenceSwitch, self).__init__(interfaces, config)
        if config.of_dir:
            self.of_dir = os.path.normpath(config.of_dir)
        else:
            self.of_dir = os.path.normpath("../../openflow")
        self.ofd = os.path.normpath(self.of_dir + "/udatapath/ofdatapath")
        self.ofp = os.path.normpath(self.of_dir + "/secchan/ofprotocol")
        self.ofd_op = None

    def test(self):
        if not OFSwitch.test(self):
            return False

        if not os.path.exists(self.ofd):
            print "Could not find datapath daemon: " + self.ofd
            return False

        if not os.path.exists(self.ofp):
            print "Could not find protocol daemon: " + self.ofp
            return False

        return True

    def start(self):
        ints = ','.join(self.interfaces)
        self.ofd_op = subprocess.Popen([self.ofd, "-i", ints, "punix:/tmp/ofd"])
        print "Started ofdatapath on IFs " + ints + \
                    " with pid " + str(self.ofd_op.pid)        
        subprocess.call([self.ofp, "unix:/tmp/ofd", 
                "tcp:%s:%d" % (self.config.controller_host, self.config.port),
                "--fail=closed", "--max-backoff=1"])

    def stop(self):
        if self.ofd_op:
            print "Killing ofdatapath on pid: %d" % (self.ofd_op.pid)
            os.kill(self.ofd_op.pid,signal.SIGTERM)
            #self.ofd_op.kill()   ### apparently Popen.kill() requires python 2.6

class OFPS(OFSwitch):
    """
    Start up an OpenFlow reference switch
    """

    Name="ofps"

    def __init__(self,interfaces,config):
        super(OFPS, self).__init__(interfaces, config)
        if config.of_dir:
            self.of_dir = os.path.normpath(config.of_dir)
        else:
            self.of_dir = os.path.normpath("../src/python/ofps")
        self.ofps = os.path.normpath(self.of_dir + "/ofps.py")
        self.config = config
        
    def test(self):
        if not OFSwitch.test(self):
            return False

        if not os.path.exists(self.ofps):
            print "Could not find datapath daemon: " + self.ofd
            return False

        return True

    def start(self):
        intfs = ','.join(self.interfaces)
        how = None
        if self.config.passive_connect:
            how = "-P"
        else:
            how = "-c %s" % self.config.controller_host
        cmd = "%s %s -i %s -p %d" % (self.ofps, 
                                        how, 
                                        intfs, 
                                        self.port)
        print "Running '%s'" % (cmd)
        subprocess.call(cmd, shell=True)
        
    def stop(self):
        pass

#ederlf: OF1.2 reference switch start 
class OFReferenceSwitch12(OFSwitch):
    """
    Start up Ericsson/OpenFlow/CPqD reference switch 12    
    """

    Name="reference12"

    def __init__(self,interfaces,config):
        super(OFReferenceSwitch12, self).__init__(interfaces, config)
        self.config = config
        if config.of_dir:
            self.of_dir = os.path.normpath(config.of_dir)
        else:
            self.of_dir = os.path.normpath("../../of12softswitch")
        self.ofd = os.path.normpath(self.of_dir + "/udatapath/ofdatapath")
        self.ofp = os.path.normpath(self.of_dir + "/secchan/ofprotocol")
        self.ofd_op = None


    def test(self):
        if not OFSwitch.test(self):
            return False

        if not os.path.exists(self.ofd):
            print "Could not find datapath daemon: " + self.ofd
            return False

        if not os.path.exists(self.ofp):
            print "Could not find protocol daemon: " + self.ofp
            return False

        return True

    def start(self):
        ints = ','.join(self.interfaces)
        self.ofd_op = subprocess.Popen([self.ofd, "-i", ints, "punix:/tmp/ofd", "-v", ">", "ref12.log"])
        print "Started ofdatapath on IFs " + ints + \
                    " with pid " + str(self.ofd_op.pid)        
        subprocess.call([self.ofp, "unix:/tmp/ofd", 
                "tcp:%s:%d" % (self.config.controller_host, self.config.port), "--max-backoff=1"])

    def stop(self):
        if self.ofd_op:
            print "Killing ofdatapath on pid: %d" % (self.ofd_op.pid)
            os.kill(self.ofd_op.pid,signal.SIGTERM)
            #self.ofd_op.kill()   ### apparently Popen.kill() requires python 2.6

MAP = {
    "ofps" : OFPS,
    "none" : OFSwitch,
    "reference" : OFReferenceSwitch,
    "reference12":OFReferenceSwitch12,  
    }
    
