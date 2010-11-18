import subprocess

class PlatformDriver(object):
    def __init__ (self):
        pass

    def setup_interfaces (self):
        pass

    def teardown_interfaces (self):
        pass

    def get_interfaces (self):
        pass


class LinuxDriver(PlatformDriver):
    def __init__ (self, port_count):
        self.port_count = port_count
        self.veths = []

    def setup_interfaces (self):
        print "Setting up %d virtual ethernet pairs" % (self.port_count)
        subprocess.call(["/sbin/modprobe", "veth"])
        for idx in range(0, self.port_count):
            print "Creating veth pair " + str(idx)
            subprocess.call(["/sbin/ip", "link", "add", "type", "veth"])
        
        for idx in range(0, 2 * self.port_count):
            cmd = ["/sbin/ifconfig", 
                   "veth" + str(idx), 
                   "192.168.1" + str(idx) + ".1", 
                   "netmask", 
                   "255.255.255.0"]
            print "Cmd: " + str(cmd)
            subprocess.call(cmd)
        self.veths = [ "veth0"]
        for idx in range(1, self.port_count):
            self.veths.append("veth" + str(2 * idx))
        return self.veths
        
    def teardown_interfaces (self):
        print "Tearing down virtual ethernet pairs"
        subprocess.call(["/sbin/rmmod","veth"])

    def get_interfaces (self):
        return self.veths
    

MAP = {
    "posix" :   {
                "Linux" : LinuxDriver,
                }
    }

