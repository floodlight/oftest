import struct

# Structure definitions
class ofp_phy_port:
    """Automatically generated Python class for ofp_phy_port

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.port_no = 0
        self.hw_addr= [0,0,0,0,0,0]
        self.name= ""
        self.config = 0
        self.state = 0
        self.curr = 0
        self.advertised = 0
        self.supported = 0
        self.peer = 0

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.hw_addr, list)):
            return (False, "self.hw_addr is not list as expected.")
        if(len(self.hw_addr) != 6):
            return (False, "self.hw_addr is not of size 6 as expected.")
        if(not isinstance(self.name, str)):
            return (False, "self.name is not string as expected.")
        if(len(self.name) > 16):
            return (False, "self.name is not of size 16 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!H", self.port_no)
        packed += struct.pack("!BBBBBB", self.hw_addr[0], self.hw_addr[1], self.hw_addr[2], self.hw_addr[3], self.hw_addr[4], self.hw_addr[5])
        packed += self.name.ljust(16,'\0')
        packed += struct.pack("!LLLLLL", self.config, self.state, self.curr, self.advertised, self.supported, self.peer)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 48):
            return binaryString
        fmt = '!H'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.port_no,) = struct.unpack(fmt, binaryString[start:end])
        fmt = '!BBBBBB'
        start = 2
        end = start + struct.calcsize(fmt)
        (self.hw_addr[0], self.hw_addr[1], self.hw_addr[2], self.hw_addr[3], self.hw_addr[4], self.hw_addr[5]) = struct.unpack(fmt, binaryString[start:end])
        self.name = binaryString[8:24].replace("\0","")
        fmt = '!LLLLLL'
        start = 24
        end = start + struct.calcsize(fmt)
        (self.config, self.state, self.curr, self.advertised, self.supported, self.peer) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[48:]

    def __len__(self):
        """Return length of message
        """
        l = 48
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.port_no !=  other.port_no: return False
        if self.hw_addr !=  other.hw_addr: return False
        if self.name !=  other.name: return False
        if self.config !=  other.config: return False
        if self.state !=  other.state: return False
        if self.curr !=  other.curr: return False
        if self.advertised !=  other.advertised: return False
        if self.supported !=  other.supported: return False
        if self.peer !=  other.peer: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'port_no: ' + str(self.port_no) + '\n'
        outstr += prefix + 'hw_addr: ' + str(self.hw_addr) + '\n'
        outstr += prefix + 'name: ' + str(self.name) + '\n'
        outstr += prefix + 'config: ' + str(self.config) + '\n'
        outstr += prefix + 'state: ' + str(self.state) + '\n'
        outstr += prefix + 'curr: ' + str(self.curr) + '\n'
        outstr += prefix + 'advertised: ' + str(self.advertised) + '\n'
        outstr += prefix + 'supported: ' + str(self.supported) + '\n'
        outstr += prefix + 'peer: ' + str(self.peer) + '\n'
        return outstr


class ofp_aggregate_stats_reply:
    """Automatically generated Python class for ofp_aggregate_stats_reply

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.packet_count = 0
        self.byte_count = 0
        self.flow_count = 0
        self.pad= [0,0,0,0]

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.pad, list)):
            return (False, "self.pad is not list as expected.")
        if(len(self.pad) != 4):
            return (False, "self.pad is not of size 4 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!QQL", self.packet_count, self.byte_count, self.flow_count)
        packed += struct.pack("!BBBB", self.pad[0], self.pad[1], self.pad[2], self.pad[3])
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 24):
            return binaryString
        fmt = '!QQL'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.packet_count, self.byte_count, self.flow_count) = struct.unpack(fmt,  binaryString[start:end])
        fmt = '!BBBB'
        start = 20
        end = start + struct.calcsize(fmt)
        (self.pad[0], self.pad[1], self.pad[2], self.pad[3]) = struct.unpack(fmt, binaryString[start:end])
        return binaryString[24:]

    def __len__(self):
        """Return length of message
        """
        l = 24
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.packet_count !=  other.packet_count: return False
        if self.byte_count !=  other.byte_count: return False
        if self.flow_count !=  other.flow_count: return False
        if self.pad !=  other.pad: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'packet_count: ' + str(self.packet_count) + '\n'
        outstr += prefix + 'byte_count: ' + str(self.byte_count) + '\n'
        outstr += prefix + 'flow_count: ' + str(self.flow_count) + '\n'
        return outstr


class ofp_table_stats:
    """Automatically generated Python class for ofp_table_stats

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.table_id = 0
        self.pad= [0,0,0]
        self.name= ""
        self.wildcards = 0
        self.max_entries = 0
        self.active_count = 0
        self.lookup_count = 0
        self.matched_count = 0

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.pad, list)):
            return (False, "self.pad is not list as expected.")
        if(len(self.pad) != 3):
            return (False, "self.pad is not of size 3 as expected.")
        if(not isinstance(self.name, str)):
            return (False, "self.name is not string as expected.")
        if(len(self.name) > 32):
            return (False, "self.name is not of size 32 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!B", self.table_id)
        packed += struct.pack("!BBB", self.pad[0], self.pad[1], self.pad[2])
        packed += self.name.ljust(32,'\0')
        packed += struct.pack("!LLLQQ", self.wildcards, self.max_entries, self.active_count, self.lookup_count, self.matched_count)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 64):
            return binaryString
        fmt = '!B'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.table_id,) = struct.unpack(fmt, binaryString[start:end])
        fmt = '!BBB'
        start = 1
        end = start + struct.calcsize(fmt)
        (self.pad[0], self.pad[1], self.pad[2]) = struct.unpack(fmt, binaryString[start:end])
        self.name = binaryString[4:36].replace("\0","")
        fmt = '!LLLQQ'
        start = 36
        end = start + struct.calcsize(fmt)
        (self.wildcards, self.max_entries, self.active_count, self.lookup_count, self.matched_count) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[64:]

    def __len__(self):
        """Return length of message
        """
        l = 64
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.table_id !=  other.table_id: return False
        if self.pad !=  other.pad: return False
        if self.name !=  other.name: return False
        if self.wildcards !=  other.wildcards: return False
        if self.max_entries !=  other.max_entries: return False
        if self.active_count !=  other.active_count: return False
        if self.lookup_count !=  other.lookup_count: return False
        if self.matched_count !=  other.matched_count: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'table_id: ' + str(self.table_id) + '\n'
        outstr += prefix + 'name: ' + str(self.name) + '\n'
        outstr += prefix + 'wildcards: ' + str(self.wildcards) + '\n'
        outstr += prefix + 'max_entries: ' + str(self.max_entries) + '\n'
        outstr += prefix + 'active_count: ' + str(self.active_count) + '\n'
        outstr += prefix + 'lookup_count: ' + str(self.lookup_count) + '\n'
        outstr += prefix + 'matched_count: ' + str(self.matched_count) + '\n'
        return outstr


class ofp_flow_removed:
    """Automatically generated Python class for ofp_flow_removed

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.version = 0
        self.type = 0
        self.length = 0
        self.xid = 0
        self.match = ofp_match()
        self.cookie = 0
        self.priority = 0
        self.reason = 0
        self.pad = 0
        self.duration_sec = 0
        self.duration_nsec = 0
        self.idle_timeout = 0
        self.pad2= [0,0]
        self.packet_count = 0
        self.byte_count = 0

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.match, ofp_match)):
            return (False, "self.match is not class ofp_match as expected.")
        if(not isinstance(self.pad2, list)):
            return (False, "self.pad2 is not list as expected.")
        if(len(self.pad2) != 2):
            return (False, "self.pad2 is not of size 2 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!BBHL", self.version, self.type, self.length, self.xid)
        packed += self.match.pack()
        packed += struct.pack("!QHBBLLH", self.cookie, self.priority, self.reason, self.pad, self.duration_sec, self.duration_nsec, self.idle_timeout)
        packed += struct.pack("!BB", self.pad2[0], self.pad2[1])
        packed += struct.pack("!QQ", self.packet_count, self.byte_count)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 88):
            return binaryString
        fmt = '!BBHL'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.version, self.type, self.length, self.xid) = struct.unpack(fmt,  binaryString[start:end])
        self.match.unpack(binaryString[8:])
        fmt = '!QHBBLLH'
        start = 48
        end = start + struct.calcsize(fmt)
        (self.cookie, self.priority, self.reason, self.pad, self.duration_sec, self.duration_nsec, self.idle_timeout) = struct.unpack(fmt,  binaryString[start:end])
        fmt = '!BB'
        start = 70
        end = start + struct.calcsize(fmt)
        (self.pad2[0], self.pad2[1]) = struct.unpack(fmt, binaryString[start:end])
        fmt = '!QQ'
        start = 72
        end = start + struct.calcsize(fmt)
        (self.packet_count, self.byte_count) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[88:]

    def __len__(self):
        """Return length of message
        """
        l = 88
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.version !=  other.version: return False
        if self.type !=  other.type: return False
        if self.length !=  other.length: return False
        if self.xid !=  other.xid: return False
        if self.match !=  other.match: return False
        if self.cookie !=  other.cookie: return False
        if self.priority !=  other.priority: return False
        if self.reason !=  other.reason: return False
        if self.pad !=  other.pad: return False
        if self.duration_sec !=  other.duration_sec: return False
        if self.duration_nsec !=  other.duration_nsec: return False
        if self.idle_timeout !=  other.idle_timeout: return False
        if self.pad2 !=  other.pad2: return False
        if self.packet_count !=  other.packet_count: return False
        if self.byte_count !=  other.byte_count: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'version: ' + str(self.version) + '\n'
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'length: ' + str(self.length) + '\n'
        outstr += prefix + 'xid: ' + str(self.xid) + '\n'
        outstr += prefix + 'match: \n' 
        outstr += self.match.show(prefix + '  ')
        outstr += prefix + 'cookie: ' + str(self.cookie) + '\n'
        outstr += prefix + 'priority: ' + str(self.priority) + '\n'
        outstr += prefix + 'reason: ' + str(self.reason) + '\n'
        outstr += prefix + 'duration_sec: ' + str(self.duration_sec) + '\n'
        outstr += prefix + 'duration_nsec: ' + str(self.duration_nsec) + '\n'
        outstr += prefix + 'idle_timeout: ' + str(self.idle_timeout) + '\n'
        outstr += prefix + 'packet_count: ' + str(self.packet_count) + '\n'
        outstr += prefix + 'byte_count: ' + str(self.byte_count) + '\n'
        return outstr


class ofp_port_stats:
    """Automatically generated Python class for ofp_port_stats

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.port_no = 0
        self.pad= [0,0,0,0,0,0]
        self.rx_packets = 0
        self.tx_packets = 0
        self.rx_bytes = 0
        self.tx_bytes = 0
        self.rx_dropped = 0
        self.tx_dropped = 0
        self.rx_errors = 0
        self.tx_errors = 0
        self.rx_frame_err = 0
        self.rx_over_err = 0
        self.rx_crc_err = 0
        self.collisions = 0

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.pad, list)):
            return (False, "self.pad is not list as expected.")
        if(len(self.pad) != 6):
            return (False, "self.pad is not of size 6 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!H", self.port_no)
        packed += struct.pack("!BBBBBB", self.pad[0], self.pad[1], self.pad[2], self.pad[3], self.pad[4], self.pad[5])
        packed += struct.pack("!QQQQQQQQQQQQ", self.rx_packets, self.tx_packets, self.rx_bytes, self.tx_bytes, self.rx_dropped, self.tx_dropped, self.rx_errors, self.tx_errors, self.rx_frame_err, self.rx_over_err, self.rx_crc_err, self.collisions)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 104):
            return binaryString
        fmt = '!H'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.port_no,) = struct.unpack(fmt, binaryString[start:end])
        fmt = '!BBBBBB'
        start = 2
        end = start + struct.calcsize(fmt)
        (self.pad[0], self.pad[1], self.pad[2], self.pad[3], self.pad[4], self.pad[5]) = struct.unpack(fmt, binaryString[start:end])
        fmt = '!QQQQQQQQQQQQ'
        start = 8
        end = start + struct.calcsize(fmt)
        (self.rx_packets, self.tx_packets, self.rx_bytes, self.tx_bytes, self.rx_dropped, self.tx_dropped, self.rx_errors, self.tx_errors, self.rx_frame_err, self.rx_over_err, self.rx_crc_err, self.collisions) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[104:]

    def __len__(self):
        """Return length of message
        """
        l = 104
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.port_no !=  other.port_no: return False
        if self.pad !=  other.pad: return False
        if self.rx_packets !=  other.rx_packets: return False
        if self.tx_packets !=  other.tx_packets: return False
        if self.rx_bytes !=  other.rx_bytes: return False
        if self.tx_bytes !=  other.tx_bytes: return False
        if self.rx_dropped !=  other.rx_dropped: return False
        if self.tx_dropped !=  other.tx_dropped: return False
        if self.rx_errors !=  other.rx_errors: return False
        if self.tx_errors !=  other.tx_errors: return False
        if self.rx_frame_err !=  other.rx_frame_err: return False
        if self.rx_over_err !=  other.rx_over_err: return False
        if self.rx_crc_err !=  other.rx_crc_err: return False
        if self.collisions !=  other.collisions: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'port_no: ' + str(self.port_no) + '\n'
        outstr += prefix + 'rx_packets: ' + str(self.rx_packets) + '\n'
        outstr += prefix + 'tx_packets: ' + str(self.tx_packets) + '\n'
        outstr += prefix + 'rx_bytes: ' + str(self.rx_bytes) + '\n'
        outstr += prefix + 'tx_bytes: ' + str(self.tx_bytes) + '\n'
        outstr += prefix + 'rx_dropped: ' + str(self.rx_dropped) + '\n'
        outstr += prefix + 'tx_dropped: ' + str(self.tx_dropped) + '\n'
        outstr += prefix + 'rx_errors: ' + str(self.rx_errors) + '\n'
        outstr += prefix + 'tx_errors: ' + str(self.tx_errors) + '\n'
        outstr += prefix + 'rx_frame_err: ' + str(self.rx_frame_err) + '\n'
        outstr += prefix + 'rx_over_err: ' + str(self.rx_over_err) + '\n'
        outstr += prefix + 'rx_crc_err: ' + str(self.rx_crc_err) + '\n'
        outstr += prefix + 'collisions: ' + str(self.collisions) + '\n'
        return outstr


class ofp_queue_stats:
    """Automatically generated Python class for ofp_queue_stats

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.port_no = 0
        self.pad= [0,0]
        self.queue_id = 0
        self.tx_bytes = 0
        self.tx_packets = 0
        self.tx_errors = 0

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.pad, list)):
            return (False, "self.pad is not list as expected.")
        if(len(self.pad) != 2):
            return (False, "self.pad is not of size 2 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!H", self.port_no)
        packed += struct.pack("!BB", self.pad[0], self.pad[1])
        packed += struct.pack("!LQQQ", self.queue_id, self.tx_bytes, self.tx_packets, self.tx_errors)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 32):
            return binaryString
        fmt = '!H'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.port_no,) = struct.unpack(fmt, binaryString[start:end])
        fmt = '!BB'
        start = 2
        end = start + struct.calcsize(fmt)
        (self.pad[0], self.pad[1]) = struct.unpack(fmt, binaryString[start:end])
        fmt = '!LQQQ'
        start = 4
        end = start + struct.calcsize(fmt)
        (self.queue_id, self.tx_bytes, self.tx_packets, self.tx_errors) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[32:]

    def __len__(self):
        """Return length of message
        """
        l = 32
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.port_no !=  other.port_no: return False
        if self.pad !=  other.pad: return False
        if self.queue_id !=  other.queue_id: return False
        if self.tx_bytes !=  other.tx_bytes: return False
        if self.tx_packets !=  other.tx_packets: return False
        if self.tx_errors !=  other.tx_errors: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'port_no: ' + str(self.port_no) + '\n'
        outstr += prefix + 'queue_id: ' + str(self.queue_id) + '\n'
        outstr += prefix + 'tx_bytes: ' + str(self.tx_bytes) + '\n'
        outstr += prefix + 'tx_packets: ' + str(self.tx_packets) + '\n'
        outstr += prefix + 'tx_errors: ' + str(self.tx_errors) + '\n'
        return outstr


class ofp_action_tp_port:
    """Automatically generated Python class for ofp_action_tp_port

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.type = 0
        self.len = 0
        self.tp_port = 0
        self.pad= [0,0]

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.pad, list)):
            return (False, "self.pad is not list as expected.")
        if(len(self.pad) != 2):
            return (False, "self.pad is not of size 2 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!HHH", self.type, self.len, self.tp_port)
        packed += struct.pack("!BB", self.pad[0], self.pad[1])
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 8):
            return binaryString
        fmt = '!HHH'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.type, self.len, self.tp_port) = struct.unpack(fmt,  binaryString[start:end])
        fmt = '!BB'
        start = 6
        end = start + struct.calcsize(fmt)
        (self.pad[0], self.pad[1]) = struct.unpack(fmt, binaryString[start:end])
        return binaryString[8:]

    def __len__(self):
        """Return length of message
        """
        l = 8
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.type !=  other.type: return False
        if self.len !=  other.len: return False
        if self.tp_port !=  other.tp_port: return False
        if self.pad !=  other.pad: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'len: ' + str(self.len) + '\n'
        outstr += prefix + 'tp_port: ' + str(self.tp_port) + '\n'
        return outstr


class ofp_port_stats_request:
    """Automatically generated Python class for ofp_port_stats_request

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.port_no = 0
        self.pad= [0,0,0,0,0,0]

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.pad, list)):
            return (False, "self.pad is not list as expected.")
        if(len(self.pad) != 6):
            return (False, "self.pad is not of size 6 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!H", self.port_no)
        packed += struct.pack("!BBBBBB", self.pad[0], self.pad[1], self.pad[2], self.pad[3], self.pad[4], self.pad[5])
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 8):
            return binaryString
        fmt = '!H'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.port_no,) = struct.unpack(fmt, binaryString[start:end])
        fmt = '!BBBBBB'
        start = 2
        end = start + struct.calcsize(fmt)
        (self.pad[0], self.pad[1], self.pad[2], self.pad[3], self.pad[4], self.pad[5]) = struct.unpack(fmt, binaryString[start:end])
        return binaryString[8:]

    def __len__(self):
        """Return length of message
        """
        l = 8
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.port_no !=  other.port_no: return False
        if self.pad !=  other.pad: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'port_no: ' + str(self.port_no) + '\n'
        return outstr


class ofp_stats_request:
    """Automatically generated Python class for ofp_stats_request

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.version = 0
        self.type = 0
        self.length = 0
        self.xid = 0
        self.stats_type = 0
        self.flags = 0

    def __assert(self):
        """Sanity check
        """
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!BBHLHH", self.version, self.type, self.length, self.xid, self.stats_type, self.flags)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 12):
            return binaryString
        fmt = '!BBHLHH'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.version, self.type, self.length, self.xid, self.stats_type, self.flags) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[12:]

    def __len__(self):
        """Return length of message
        """
        l = 12
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.version !=  other.version: return False
        if self.type !=  other.type: return False
        if self.length !=  other.length: return False
        if self.xid !=  other.xid: return False
        if self.stats_type !=  other.stats_type: return False
        if self.flags !=  other.flags: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'version: ' + str(self.version) + '\n'
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'length: ' + str(self.length) + '\n'
        outstr += prefix + 'xid: ' + str(self.xid) + '\n'
        outstr += prefix + 'stats_type: ' + str(self.stats_type) + '\n'
        outstr += prefix + 'flags: ' + str(self.flags) + '\n'
        return outstr


class ofp_hello:
    """Automatically generated Python class for ofp_hello

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.version = 0
        self.type = 0
        self.length = 0
        self.xid = 0

    def __assert(self):
        """Sanity check
        """
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!BBHL", self.version, self.type, self.length, self.xid)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 8):
            return binaryString
        fmt = '!BBHL'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.version, self.type, self.length, self.xid) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[8:]

    def __len__(self):
        """Return length of message
        """
        l = 8
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.version !=  other.version: return False
        if self.type !=  other.type: return False
        if self.length !=  other.length: return False
        if self.xid !=  other.xid: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'version: ' + str(self.version) + '\n'
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'length: ' + str(self.length) + '\n'
        outstr += prefix + 'xid: ' + str(self.xid) + '\n'
        return outstr


class ofp_aggregate_stats_request:
    """Automatically generated Python class for ofp_aggregate_stats_request

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.match = ofp_match()
        self.table_id = 0
        self.pad = 0
        self.out_port = 0

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.match, ofp_match)):
            return (False, "self.match is not class ofp_match as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += self.match.pack()
        packed += struct.pack("!BBH", self.table_id, self.pad, self.out_port)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 44):
            return binaryString
        self.match.unpack(binaryString[0:])
        fmt = '!BBH'
        start = 40
        end = start + struct.calcsize(fmt)
        (self.table_id, self.pad, self.out_port) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[44:]

    def __len__(self):
        """Return length of message
        """
        l = 44
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.match !=  other.match: return False
        if self.table_id !=  other.table_id: return False
        if self.pad !=  other.pad: return False
        if self.out_port !=  other.out_port: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'match: \n' 
        outstr += self.match.show(prefix + '  ')
        outstr += prefix + 'table_id: ' + str(self.table_id) + '\n'
        outstr += prefix + 'out_port: ' + str(self.out_port) + '\n'
        return outstr


class ofp_port_status:
    """Automatically generated Python class for ofp_port_status

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.version = 0
        self.type = 0
        self.length = 0
        self.xid = 0
        self.reason = 0
        self.pad= [0,0,0,0,0,0,0]
        self.desc = ofp_phy_port()

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.pad, list)):
            return (False, "self.pad is not list as expected.")
        if(len(self.pad) != 7):
            return (False, "self.pad is not of size 7 as expected.")
        if(not isinstance(self.desc, ofp_phy_port)):
            return (False, "self.desc is not class ofp_phy_port as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!BBHLB", self.version, self.type, self.length, self.xid, self.reason)
        packed += struct.pack("!BBBBBBB", self.pad[0], self.pad[1], self.pad[2], self.pad[3], self.pad[4], self.pad[5], self.pad[6])
        packed += self.desc.pack()
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 64):
            return binaryString
        fmt = '!BBHLB'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.version, self.type, self.length, self.xid, self.reason) = struct.unpack(fmt,  binaryString[start:end])
        fmt = '!BBBBBBB'
        start = 9
        end = start + struct.calcsize(fmt)
        (self.pad[0], self.pad[1], self.pad[2], self.pad[3], self.pad[4], self.pad[5], self.pad[6]) = struct.unpack(fmt, binaryString[start:end])
        self.desc.unpack(binaryString[16:])
        return binaryString[64:]

    def __len__(self):
        """Return length of message
        """
        l = 64
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.version !=  other.version: return False
        if self.type !=  other.type: return False
        if self.length !=  other.length: return False
        if self.xid !=  other.xid: return False
        if self.reason !=  other.reason: return False
        if self.pad !=  other.pad: return False
        if self.desc !=  other.desc: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'version: ' + str(self.version) + '\n'
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'length: ' + str(self.length) + '\n'
        outstr += prefix + 'xid: ' + str(self.xid) + '\n'
        outstr += prefix + 'reason: ' + str(self.reason) + '\n'
        outstr += prefix + 'desc: \n' 
        outstr += self.desc.show(prefix + '  ')
        return outstr


class ofp_action_header:
    """Automatically generated Python class for ofp_action_header

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.type = 0
        self.len = 0
        self.pad= [0,0,0,0]

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.pad, list)):
            return (False, "self.pad is not list as expected.")
        if(len(self.pad) != 4):
            return (False, "self.pad is not of size 4 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!HH", self.type, self.len)
        packed += struct.pack("!BBBB", self.pad[0], self.pad[1], self.pad[2], self.pad[3])
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 8):
            return binaryString
        fmt = '!HH'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.type, self.len) = struct.unpack(fmt,  binaryString[start:end])
        fmt = '!BBBB'
        start = 4
        end = start + struct.calcsize(fmt)
        (self.pad[0], self.pad[1], self.pad[2], self.pad[3]) = struct.unpack(fmt, binaryString[start:end])
        return binaryString[8:]

    def __len__(self):
        """Return length of message
        """
        l = 8
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.type !=  other.type: return False
        if self.len !=  other.len: return False
        if self.pad !=  other.pad: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'len: ' + str(self.len) + '\n'
        return outstr


class ofp_port_mod:
    """Automatically generated Python class for ofp_port_mod

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.version = 0
        self.type = 0
        self.length = 0
        self.xid = 0
        self.port_no = 0
        self.hw_addr= [0,0,0,0,0,0]
        self.config = 0
        self.mask = 0
        self.advertise = 0
        self.pad= [0,0,0,0]

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.hw_addr, list)):
            return (False, "self.hw_addr is not list as expected.")
        if(len(self.hw_addr) != 6):
            return (False, "self.hw_addr is not of size 6 as expected.")
        if(not isinstance(self.pad, list)):
            return (False, "self.pad is not list as expected.")
        if(len(self.pad) != 4):
            return (False, "self.pad is not of size 4 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!BBHLH", self.version, self.type, self.length, self.xid, self.port_no)
        packed += struct.pack("!BBBBBB", self.hw_addr[0], self.hw_addr[1], self.hw_addr[2], self.hw_addr[3], self.hw_addr[4], self.hw_addr[5])
        packed += struct.pack("!LLL", self.config, self.mask, self.advertise)
        packed += struct.pack("!BBBB", self.pad[0], self.pad[1], self.pad[2], self.pad[3])
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 32):
            return binaryString
        fmt = '!BBHLH'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.version, self.type, self.length, self.xid, self.port_no) = struct.unpack(fmt,  binaryString[start:end])
        fmt = '!BBBBBB'
        start = 10
        end = start + struct.calcsize(fmt)
        (self.hw_addr[0], self.hw_addr[1], self.hw_addr[2], self.hw_addr[3], self.hw_addr[4], self.hw_addr[5]) = struct.unpack(fmt, binaryString[start:end])
        fmt = '!LLL'
        start = 16
        end = start + struct.calcsize(fmt)
        (self.config, self.mask, self.advertise) = struct.unpack(fmt,  binaryString[start:end])
        fmt = '!BBBB'
        start = 28
        end = start + struct.calcsize(fmt)
        (self.pad[0], self.pad[1], self.pad[2], self.pad[3]) = struct.unpack(fmt, binaryString[start:end])
        return binaryString[32:]

    def __len__(self):
        """Return length of message
        """
        l = 32
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.version !=  other.version: return False
        if self.type !=  other.type: return False
        if self.length !=  other.length: return False
        if self.xid !=  other.xid: return False
        if self.port_no !=  other.port_no: return False
        if self.hw_addr !=  other.hw_addr: return False
        if self.config !=  other.config: return False
        if self.mask !=  other.mask: return False
        if self.advertise !=  other.advertise: return False
        if self.pad !=  other.pad: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'version: ' + str(self.version) + '\n'
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'length: ' + str(self.length) + '\n'
        outstr += prefix + 'xid: ' + str(self.xid) + '\n'
        outstr += prefix + 'port_no: ' + str(self.port_no) + '\n'
        outstr += prefix + 'hw_addr: ' + str(self.hw_addr) + '\n'
        outstr += prefix + 'config: ' + str(self.config) + '\n'
        outstr += prefix + 'mask: ' + str(self.mask) + '\n'
        outstr += prefix + 'advertise: ' + str(self.advertise) + '\n'
        return outstr


class ofp_action_vlan_vid:
    """Automatically generated Python class for ofp_action_vlan_vid

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.type = 0
        self.len = 0
        self.vlan_vid = 0
        self.pad= [0,0]

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.pad, list)):
            return (False, "self.pad is not list as expected.")
        if(len(self.pad) != 2):
            return (False, "self.pad is not of size 2 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!HHH", self.type, self.len, self.vlan_vid)
        packed += struct.pack("!BB", self.pad[0], self.pad[1])
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 8):
            return binaryString
        fmt = '!HHH'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.type, self.len, self.vlan_vid) = struct.unpack(fmt,  binaryString[start:end])
        fmt = '!BB'
        start = 6
        end = start + struct.calcsize(fmt)
        (self.pad[0], self.pad[1]) = struct.unpack(fmt, binaryString[start:end])
        return binaryString[8:]

    def __len__(self):
        """Return length of message
        """
        l = 8
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.type !=  other.type: return False
        if self.len !=  other.len: return False
        if self.vlan_vid !=  other.vlan_vid: return False
        if self.pad !=  other.pad: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'len: ' + str(self.len) + '\n'
        outstr += prefix + 'vlan_vid: ' + str(self.vlan_vid) + '\n'
        return outstr


class ofp_action_output:
    """Automatically generated Python class for ofp_action_output

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.type = 0
        self.len = 0
        self.port = 0
        self.max_len = 0

    def __assert(self):
        """Sanity check
        """
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!HHHH", self.type, self.len, self.port, self.max_len)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 8):
            return binaryString
        fmt = '!HHHH'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.type, self.len, self.port, self.max_len) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[8:]

    def __len__(self):
        """Return length of message
        """
        l = 8
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.type !=  other.type: return False
        if self.len !=  other.len: return False
        if self.port !=  other.port: return False
        if self.max_len !=  other.max_len: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'len: ' + str(self.len) + '\n'
        outstr += prefix + 'port: ' + str(self.port) + '\n'
        outstr += prefix + 'max_len: ' + str(self.max_len) + '\n'
        return outstr


class ofp_switch_config:
    """Automatically generated Python class for ofp_switch_config

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.version = 0
        self.type = 0
        self.length = 0
        self.xid = 0
        self.flags = 0
        self.miss_send_len = 128

    def __assert(self):
        """Sanity check
        """
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!BBHLHH", self.version, self.type, self.length, self.xid, self.flags, self.miss_send_len)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 12):
            return binaryString
        fmt = '!BBHLHH'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.version, self.type, self.length, self.xid, self.flags, self.miss_send_len) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[12:]

    def __len__(self):
        """Return length of message
        """
        l = 12
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.version !=  other.version: return False
        if self.type !=  other.type: return False
        if self.length !=  other.length: return False
        if self.xid !=  other.xid: return False
        if self.flags !=  other.flags: return False
        if self.miss_send_len !=  other.miss_send_len: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'version: ' + str(self.version) + '\n'
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'length: ' + str(self.length) + '\n'
        outstr += prefix + 'xid: ' + str(self.xid) + '\n'
        outstr += prefix + 'flags: ' + str(self.flags) + '\n'
        outstr += prefix + 'miss_send_len: ' + str(self.miss_send_len) + '\n'
        return outstr


class ofp_action_nw_tos:
    """Automatically generated Python class for ofp_action_nw_tos

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.type = 0
        self.len = 0
        self.nw_tos = 0
        self.pad= [0,0,0]

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.pad, list)):
            return (False, "self.pad is not list as expected.")
        if(len(self.pad) != 3):
            return (False, "self.pad is not of size 3 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!HHB", self.type, self.len, self.nw_tos)
        packed += struct.pack("!BBB", self.pad[0], self.pad[1], self.pad[2])
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 8):
            return binaryString
        fmt = '!HHB'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.type, self.len, self.nw_tos) = struct.unpack(fmt,  binaryString[start:end])
        fmt = '!BBB'
        start = 5
        end = start + struct.calcsize(fmt)
        (self.pad[0], self.pad[1], self.pad[2]) = struct.unpack(fmt, binaryString[start:end])
        return binaryString[8:]

    def __len__(self):
        """Return length of message
        """
        l = 8
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.type !=  other.type: return False
        if self.len !=  other.len: return False
        if self.nw_tos !=  other.nw_tos: return False
        if self.pad !=  other.pad: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'len: ' + str(self.len) + '\n'
        outstr += prefix + 'nw_tos: ' + str(self.nw_tos) + '\n'
        return outstr


class ofp_queue_get_config_reply:
    """Automatically generated Python class for ofp_queue_get_config_reply

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.version = 0
        self.type = 0
        self.length = 0
        self.xid = 0
        self.port = 0
        self.pad= [0,0,0,0,0,0]

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.pad, list)):
            return (False, "self.pad is not list as expected.")
        if(len(self.pad) != 6):
            return (False, "self.pad is not of size 6 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!BBHLH", self.version, self.type, self.length, self.xid, self.port)
        packed += struct.pack("!BBBBBB", self.pad[0], self.pad[1], self.pad[2], self.pad[3], self.pad[4], self.pad[5])
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 16):
            return binaryString
        fmt = '!BBHLH'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.version, self.type, self.length, self.xid, self.port) = struct.unpack(fmt,  binaryString[start:end])
        fmt = '!BBBBBB'
        start = 10
        end = start + struct.calcsize(fmt)
        (self.pad[0], self.pad[1], self.pad[2], self.pad[3], self.pad[4], self.pad[5]) = struct.unpack(fmt, binaryString[start:end])
        return binaryString[16:]

    def __len__(self):
        """Return length of message
        """
        l = 16
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.version !=  other.version: return False
        if self.type !=  other.type: return False
        if self.length !=  other.length: return False
        if self.xid !=  other.xid: return False
        if self.port !=  other.port: return False
        if self.pad !=  other.pad: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'version: ' + str(self.version) + '\n'
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'length: ' + str(self.length) + '\n'
        outstr += prefix + 'xid: ' + str(self.xid) + '\n'
        outstr += prefix + 'port: ' + str(self.port) + '\n'
        return outstr


class ofp_packet_in:
    """Automatically generated Python class for ofp_packet_in

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.version = 0
        self.type = 0
        self.length = 0
        self.xid = 0
        self.buffer_id = 0
        self.total_len = 0
        self.in_port = 0
        self.reason = 0
        self.pad = 0

    def __assert(self):
        """Sanity check
        """
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!BBHLLHHBB", self.version, self.type, self.length, self.xid, self.buffer_id, self.total_len, self.in_port, self.reason, self.pad)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 18):
            return binaryString
        fmt = '!BBHLLHHBB'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.version, self.type, self.length, self.xid, self.buffer_id, self.total_len, self.in_port, self.reason, self.pad) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[18:]

    def __len__(self):
        """Return length of message
        """
        l = 18
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.version !=  other.version: return False
        if self.type !=  other.type: return False
        if self.length !=  other.length: return False
        if self.xid !=  other.xid: return False
        if self.buffer_id !=  other.buffer_id: return False
        if self.total_len !=  other.total_len: return False
        if self.in_port !=  other.in_port: return False
        if self.reason !=  other.reason: return False
        if self.pad !=  other.pad: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'version: ' + str(self.version) + '\n'
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'length: ' + str(self.length) + '\n'
        outstr += prefix + 'xid: ' + str(self.xid) + '\n'
        outstr += prefix + 'buffer_id: ' + str(self.buffer_id) + '\n'
        outstr += prefix + 'total_len: ' + str(self.total_len) + '\n'
        outstr += prefix + 'in_port: ' + str(self.in_port) + '\n'
        outstr += prefix + 'reason: ' + str(self.reason) + '\n'
        return outstr


class ofp_flow_stats:
    """Automatically generated Python class for ofp_flow_stats

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.length = 0
        self.table_id = 0
        self.pad = 0
        self.match = ofp_match()
        self.duration_sec = 0
        self.duration_nsec = 0
        self.priority = 0x8000
        self.idle_timeout = 0
        self.hard_timeout = 0
        self.pad2= [0,0,0,0,0,0]
        self.cookie = 0
        self.packet_count = 0
        self.byte_count = 0

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.match, ofp_match)):
            return (False, "self.match is not class ofp_match as expected.")
        if(not isinstance(self.pad2, list)):
            return (False, "self.pad2 is not list as expected.")
        if(len(self.pad2) != 6):
            return (False, "self.pad2 is not of size 6 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!HBB", self.length, self.table_id, self.pad)
        packed += self.match.pack()
        packed += struct.pack("!LLHHH", self.duration_sec, self.duration_nsec, self.priority, self.idle_timeout, self.hard_timeout)
        packed += struct.pack("!BBBBBB", self.pad2[0], self.pad2[1], self.pad2[2], self.pad2[3], self.pad2[4], self.pad2[5])
        packed += struct.pack("!QQQ", self.cookie, self.packet_count, self.byte_count)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 88):
            return binaryString
        fmt = '!HBB'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.length, self.table_id, self.pad) = struct.unpack(fmt,  binaryString[start:end])
        self.match.unpack(binaryString[4:])
        fmt = '!LLHHH'
        start = 44
        end = start + struct.calcsize(fmt)
        (self.duration_sec, self.duration_nsec, self.priority, self.idle_timeout, self.hard_timeout) = struct.unpack(fmt,  binaryString[start:end])
        fmt = '!BBBBBB'
        start = 58
        end = start + struct.calcsize(fmt)
        (self.pad2[0], self.pad2[1], self.pad2[2], self.pad2[3], self.pad2[4], self.pad2[5]) = struct.unpack(fmt, binaryString[start:end])
        fmt = '!QQQ'
        start = 64
        end = start + struct.calcsize(fmt)
        (self.cookie, self.packet_count, self.byte_count) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[88:]

    def __len__(self):
        """Return length of message
        """
        l = 88
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.length !=  other.length: return False
        if self.table_id !=  other.table_id: return False
        if self.pad !=  other.pad: return False
        if self.match !=  other.match: return False
        if self.duration_sec !=  other.duration_sec: return False
        if self.duration_nsec !=  other.duration_nsec: return False
        if self.priority !=  other.priority: return False
        if self.idle_timeout !=  other.idle_timeout: return False
        if self.hard_timeout !=  other.hard_timeout: return False
        if self.pad2 !=  other.pad2: return False
        if self.cookie !=  other.cookie: return False
        if self.packet_count !=  other.packet_count: return False
        if self.byte_count !=  other.byte_count: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'length: ' + str(self.length) + '\n'
        outstr += prefix + 'table_id: ' + str(self.table_id) + '\n'
        outstr += prefix + 'match: \n' 
        outstr += self.match.show(prefix + '  ')
        outstr += prefix + 'duration_sec: ' + str(self.duration_sec) + '\n'
        outstr += prefix + 'duration_nsec: ' + str(self.duration_nsec) + '\n'
        outstr += prefix + 'priority: ' + str(self.priority) + '\n'
        outstr += prefix + 'idle_timeout: ' + str(self.idle_timeout) + '\n'
        outstr += prefix + 'hard_timeout: ' + str(self.hard_timeout) + '\n'
        outstr += prefix + 'cookie: ' + str(self.cookie) + '\n'
        outstr += prefix + 'packet_count: ' + str(self.packet_count) + '\n'
        outstr += prefix + 'byte_count: ' + str(self.byte_count) + '\n'
        return outstr


class ofp_flow_stats_request:
    """Automatically generated Python class for ofp_flow_stats_request

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.match = ofp_match()
        self.table_id = 0
        self.pad = 0
        self.out_port = 0

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.match, ofp_match)):
            return (False, "self.match is not class ofp_match as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += self.match.pack()
        packed += struct.pack("!BBH", self.table_id, self.pad, self.out_port)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 44):
            return binaryString
        self.match.unpack(binaryString[0:])
        fmt = '!BBH'
        start = 40
        end = start + struct.calcsize(fmt)
        (self.table_id, self.pad, self.out_port) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[44:]

    def __len__(self):
        """Return length of message
        """
        l = 44
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.match !=  other.match: return False
        if self.table_id !=  other.table_id: return False
        if self.pad !=  other.pad: return False
        if self.out_port !=  other.out_port: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'match: \n' 
        outstr += self.match.show(prefix + '  ')
        outstr += prefix + 'table_id: ' + str(self.table_id) + '\n'
        outstr += prefix + 'out_port: ' + str(self.out_port) + '\n'
        return outstr


class ofp_action_vendor_header:
    """Automatically generated Python class for ofp_action_vendor_header

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.type = 0
        self.len = 0
        self.vendor = 0

    def __assert(self):
        """Sanity check
        """
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!HHL", self.type, self.len, self.vendor)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 8):
            return binaryString
        fmt = '!HHL'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.type, self.len, self.vendor) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[8:]

    def __len__(self):
        """Return length of message
        """
        l = 8
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.type !=  other.type: return False
        if self.len !=  other.len: return False
        if self.vendor !=  other.vendor: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'len: ' + str(self.len) + '\n'
        outstr += prefix + 'vendor: ' + str(self.vendor) + '\n'
        return outstr


class ofp_stats_reply:
    """Automatically generated Python class for ofp_stats_reply

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.version = 0
        self.type = 0
        self.length = 0
        self.xid = 0
        self.stats_type = 0
        self.flags = 0

    def __assert(self):
        """Sanity check
        """
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!BBHLHH", self.version, self.type, self.length, self.xid, self.stats_type, self.flags)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 12):
            return binaryString
        fmt = '!BBHLHH'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.version, self.type, self.length, self.xid, self.stats_type, self.flags) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[12:]

    def __len__(self):
        """Return length of message
        """
        l = 12
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.version !=  other.version: return False
        if self.type !=  other.type: return False
        if self.length !=  other.length: return False
        if self.xid !=  other.xid: return False
        if self.stats_type !=  other.stats_type: return False
        if self.flags !=  other.flags: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'version: ' + str(self.version) + '\n'
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'length: ' + str(self.length) + '\n'
        outstr += prefix + 'xid: ' + str(self.xid) + '\n'
        outstr += prefix + 'stats_type: ' + str(self.stats_type) + '\n'
        outstr += prefix + 'flags: ' + str(self.flags) + '\n'
        return outstr


class ofp_queue_stats_request:
    """Automatically generated Python class for ofp_queue_stats_request

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.port_no = 0
        self.pad= [0,0]
        self.queue_id = 0

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.pad, list)):
            return (False, "self.pad is not list as expected.")
        if(len(self.pad) != 2):
            return (False, "self.pad is not of size 2 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!H", self.port_no)
        packed += struct.pack("!BB", self.pad[0], self.pad[1])
        packed += struct.pack("!L", self.queue_id)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 8):
            return binaryString
        fmt = '!H'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.port_no,) = struct.unpack(fmt, binaryString[start:end])
        fmt = '!BB'
        start = 2
        end = start + struct.calcsize(fmt)
        (self.pad[0], self.pad[1]) = struct.unpack(fmt, binaryString[start:end])
        fmt = '!L'
        start = 4
        end = start + struct.calcsize(fmt)
        (self.queue_id,) = struct.unpack(fmt, binaryString[start:end])
        return binaryString[8:]

    def __len__(self):
        """Return length of message
        """
        l = 8
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.port_no !=  other.port_no: return False
        if self.pad !=  other.pad: return False
        if self.queue_id !=  other.queue_id: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'port_no: ' + str(self.port_no) + '\n'
        outstr += prefix + 'queue_id: ' + str(self.queue_id) + '\n'
        return outstr


class ofp_desc_stats:
    """Automatically generated Python class for ofp_desc_stats

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.mfr_desc= ""
        self.hw_desc= ""
        self.sw_desc= ""
        self.serial_num= ""
        self.dp_desc= ""

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.mfr_desc, str)):
            return (False, "self.mfr_desc is not string as expected.")
        if(len(self.mfr_desc) > 256):
            return (False, "self.mfr_desc is not of size 256 as expected.")
        if(not isinstance(self.hw_desc, str)):
            return (False, "self.hw_desc is not string as expected.")
        if(len(self.hw_desc) > 256):
            return (False, "self.hw_desc is not of size 256 as expected.")
        if(not isinstance(self.sw_desc, str)):
            return (False, "self.sw_desc is not string as expected.")
        if(len(self.sw_desc) > 256):
            return (False, "self.sw_desc is not of size 256 as expected.")
        if(not isinstance(self.serial_num, str)):
            return (False, "self.serial_num is not string as expected.")
        if(len(self.serial_num) > 32):
            return (False, "self.serial_num is not of size 32 as expected.")
        if(not isinstance(self.dp_desc, str)):
            return (False, "self.dp_desc is not string as expected.")
        if(len(self.dp_desc) > 256):
            return (False, "self.dp_desc is not of size 256 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += self.mfr_desc.ljust(256,'\0')
        packed += self.hw_desc.ljust(256,'\0')
        packed += self.sw_desc.ljust(256,'\0')
        packed += self.serial_num.ljust(32,'\0')
        packed += self.dp_desc.ljust(256,'\0')
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 1056):
            return binaryString
        self.mfr_desc = binaryString[0:256].replace("\0","")
        self.hw_desc = binaryString[256:512].replace("\0","")
        self.sw_desc = binaryString[512:768].replace("\0","")
        self.serial_num = binaryString[768:800].replace("\0","")
        self.dp_desc = binaryString[800:1056].replace("\0","")
        return binaryString[1056:]

    def __len__(self):
        """Return length of message
        """
        l = 1056
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.mfr_desc !=  other.mfr_desc: return False
        if self.hw_desc !=  other.hw_desc: return False
        if self.sw_desc !=  other.sw_desc: return False
        if self.serial_num !=  other.serial_num: return False
        if self.dp_desc !=  other.dp_desc: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'mfr_desc: ' + str(self.mfr_desc) + '\n'
        outstr += prefix + 'hw_desc: ' + str(self.hw_desc) + '\n'
        outstr += prefix + 'sw_desc: ' + str(self.sw_desc) + '\n'
        outstr += prefix + 'serial_num: ' + str(self.serial_num) + '\n'
        outstr += prefix + 'dp_desc: ' + str(self.dp_desc) + '\n'
        return outstr


class ofp_queue_get_config_request:
    """Automatically generated Python class for ofp_queue_get_config_request

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.version = 0
        self.type = 0
        self.length = 0
        self.xid = 0
        self.port = 0
        self.pad= [0,0]

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.pad, list)):
            return (False, "self.pad is not list as expected.")
        if(len(self.pad) != 2):
            return (False, "self.pad is not of size 2 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!BBHLH", self.version, self.type, self.length, self.xid, self.port)
        packed += struct.pack("!BB", self.pad[0], self.pad[1])
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 12):
            return binaryString
        fmt = '!BBHLH'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.version, self.type, self.length, self.xid, self.port) = struct.unpack(fmt,  binaryString[start:end])
        fmt = '!BB'
        start = 10
        end = start + struct.calcsize(fmt)
        (self.pad[0], self.pad[1]) = struct.unpack(fmt, binaryString[start:end])
        return binaryString[12:]

    def __len__(self):
        """Return length of message
        """
        l = 12
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.version !=  other.version: return False
        if self.type !=  other.type: return False
        if self.length !=  other.length: return False
        if self.xid !=  other.xid: return False
        if self.port !=  other.port: return False
        if self.pad !=  other.pad: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'version: ' + str(self.version) + '\n'
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'length: ' + str(self.length) + '\n'
        outstr += prefix + 'xid: ' + str(self.xid) + '\n'
        outstr += prefix + 'port: ' + str(self.port) + '\n'
        return outstr


class ofp_packet_queue:
    """Automatically generated Python class for ofp_packet_queue

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.queue_id = 0
        self.len = 0
        self.pad= [0,0]

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.pad, list)):
            return (False, "self.pad is not list as expected.")
        if(len(self.pad) != 2):
            return (False, "self.pad is not of size 2 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!LH", self.queue_id, self.len)
        packed += struct.pack("!BB", self.pad[0], self.pad[1])
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 8):
            return binaryString
        fmt = '!LH'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.queue_id, self.len) = struct.unpack(fmt,  binaryString[start:end])
        fmt = '!BB'
        start = 6
        end = start + struct.calcsize(fmt)
        (self.pad[0], self.pad[1]) = struct.unpack(fmt, binaryString[start:end])
        return binaryString[8:]

    def __len__(self):
        """Return length of message
        """
        l = 8
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.queue_id !=  other.queue_id: return False
        if self.len !=  other.len: return False
        if self.pad !=  other.pad: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'queue_id: ' + str(self.queue_id) + '\n'
        outstr += prefix + 'len: ' + str(self.len) + '\n'
        return outstr


class ofp_action_dl_addr:
    """Automatically generated Python class for ofp_action_dl_addr

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.type = 0
        self.len = 0
        self.dl_addr= [0,0,0,0,0,0]
        self.pad= [0,0,0,0,0,0]

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.dl_addr, list)):
            return (False, "self.dl_addr is not list as expected.")
        if(len(self.dl_addr) != 6):
            return (False, "self.dl_addr is not of size 6 as expected.")
        if(not isinstance(self.pad, list)):
            return (False, "self.pad is not list as expected.")
        if(len(self.pad) != 6):
            return (False, "self.pad is not of size 6 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!HH", self.type, self.len)
        packed += struct.pack("!BBBBBB", self.dl_addr[0], self.dl_addr[1], self.dl_addr[2], self.dl_addr[3], self.dl_addr[4], self.dl_addr[5])
        packed += struct.pack("!BBBBBB", self.pad[0], self.pad[1], self.pad[2], self.pad[3], self.pad[4], self.pad[5])
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 16):
            return binaryString
        fmt = '!HH'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.type, self.len) = struct.unpack(fmt,  binaryString[start:end])
        fmt = '!BBBBBB'
        start = 4
        end = start + struct.calcsize(fmt)
        (self.dl_addr[0], self.dl_addr[1], self.dl_addr[2], self.dl_addr[3], self.dl_addr[4], self.dl_addr[5]) = struct.unpack(fmt, binaryString[start:end])
        fmt = '!BBBBBB'
        start = 10
        end = start + struct.calcsize(fmt)
        (self.pad[0], self.pad[1], self.pad[2], self.pad[3], self.pad[4], self.pad[5]) = struct.unpack(fmt, binaryString[start:end])
        return binaryString[16:]

    def __len__(self):
        """Return length of message
        """
        l = 16
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.type !=  other.type: return False
        if self.len !=  other.len: return False
        if self.dl_addr !=  other.dl_addr: return False
        if self.pad !=  other.pad: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'len: ' + str(self.len) + '\n'
        outstr += prefix + 'dl_addr: ' + str(self.dl_addr) + '\n'
        return outstr


class ofp_queue_prop_header:
    """Automatically generated Python class for ofp_queue_prop_header

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.property = 0
        self.len = 0
        self.pad= [0,0,0,0]

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.pad, list)):
            return (False, "self.pad is not list as expected.")
        if(len(self.pad) != 4):
            return (False, "self.pad is not of size 4 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!HH", self.property, self.len)
        packed += struct.pack("!BBBB", self.pad[0], self.pad[1], self.pad[2], self.pad[3])
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 8):
            return binaryString
        fmt = '!HH'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.property, self.len) = struct.unpack(fmt,  binaryString[start:end])
        fmt = '!BBBB'
        start = 4
        end = start + struct.calcsize(fmt)
        (self.pad[0], self.pad[1], self.pad[2], self.pad[3]) = struct.unpack(fmt, binaryString[start:end])
        return binaryString[8:]

    def __len__(self):
        """Return length of message
        """
        l = 8
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.property !=  other.property: return False
        if self.len !=  other.len: return False
        if self.pad !=  other.pad: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'property: ' + str(self.property) + '\n'
        outstr += prefix + 'len: ' + str(self.len) + '\n'
        return outstr


class ofp_queue_prop_min_rate:
    """Automatically generated Python class for ofp_queue_prop_min_rate

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.prop_header = ofp_queue_prop_header()
        self.rate = 0
        self.pad= [0,0,0,0,0,0]

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.prop_header, ofp_queue_prop_header)):
            return (False, "self.prop_header is not class ofp_queue_prop_header as expected.")
        if(not isinstance(self.pad, list)):
            return (False, "self.pad is not list as expected.")
        if(len(self.pad) != 6):
            return (False, "self.pad is not of size 6 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += self.prop_header.pack()
        packed += struct.pack("!H", self.rate)
        packed += struct.pack("!BBBBBB", self.pad[0], self.pad[1], self.pad[2], self.pad[3], self.pad[4], self.pad[5])
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 16):
            return binaryString
        self.prop_header.unpack(binaryString[0:])
        fmt = '!H'
        start = 8
        end = start + struct.calcsize(fmt)
        (self.rate,) = struct.unpack(fmt, binaryString[start:end])
        fmt = '!BBBBBB'
        start = 10
        end = start + struct.calcsize(fmt)
        (self.pad[0], self.pad[1], self.pad[2], self.pad[3], self.pad[4], self.pad[5]) = struct.unpack(fmt, binaryString[start:end])
        return binaryString[16:]

    def __len__(self):
        """Return length of message
        """
        l = 16
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.prop_header !=  other.prop_header: return False
        if self.rate !=  other.rate: return False
        if self.pad !=  other.pad: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'prop_header: \n' 
        outstr += self.prop_header.show(prefix + '  ')
        outstr += prefix + 'rate: ' + str(self.rate) + '\n'
        return outstr


class ofp_action_enqueue:
    """Automatically generated Python class for ofp_action_enqueue

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.type = 0
        self.len = 0
        self.port = 0
        self.pad= [0,0,0,0,0,0]
        self.queue_id = 0

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.pad, list)):
            return (False, "self.pad is not list as expected.")
        if(len(self.pad) != 6):
            return (False, "self.pad is not of size 6 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!HHH", self.type, self.len, self.port)
        packed += struct.pack("!BBBBBB", self.pad[0], self.pad[1], self.pad[2], self.pad[3], self.pad[4], self.pad[5])
        packed += struct.pack("!L", self.queue_id)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 16):
            return binaryString
        fmt = '!HHH'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.type, self.len, self.port) = struct.unpack(fmt,  binaryString[start:end])
        fmt = '!BBBBBB'
        start = 6
        end = start + struct.calcsize(fmt)
        (self.pad[0], self.pad[1], self.pad[2], self.pad[3], self.pad[4], self.pad[5]) = struct.unpack(fmt, binaryString[start:end])
        fmt = '!L'
        start = 12
        end = start + struct.calcsize(fmt)
        (self.queue_id,) = struct.unpack(fmt, binaryString[start:end])
        return binaryString[16:]

    def __len__(self):
        """Return length of message
        """
        l = 16
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.type !=  other.type: return False
        if self.len !=  other.len: return False
        if self.port !=  other.port: return False
        if self.pad !=  other.pad: return False
        if self.queue_id !=  other.queue_id: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'len: ' + str(self.len) + '\n'
        outstr += prefix + 'port: ' + str(self.port) + '\n'
        outstr += prefix + 'queue_id: ' + str(self.queue_id) + '\n'
        return outstr


class ofp_switch_features:
    """Automatically generated Python class for ofp_switch_features

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.version = 0
        self.type = 0
        self.length = 0
        self.xid = 0
        self.datapath_id = 0
        self.n_buffers = 0
        self.n_tables = 0
        self.pad= [0,0,0]
        self.capabilities = 0
        self.actions = 0

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.pad, list)):
            return (False, "self.pad is not list as expected.")
        if(len(self.pad) != 3):
            return (False, "self.pad is not of size 3 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!BBHLQLB", self.version, self.type, self.length, self.xid, self.datapath_id, self.n_buffers, self.n_tables)
        packed += struct.pack("!BBB", self.pad[0], self.pad[1], self.pad[2])
        packed += struct.pack("!LL", self.capabilities, self.actions)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 32):
            return binaryString
        fmt = '!BBHLQLB'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.version, self.type, self.length, self.xid, self.datapath_id, self.n_buffers, self.n_tables) = struct.unpack(fmt,  binaryString[start:end])
        fmt = '!BBB'
        start = 21
        end = start + struct.calcsize(fmt)
        (self.pad[0], self.pad[1], self.pad[2]) = struct.unpack(fmt, binaryString[start:end])
        fmt = '!LL'
        start = 24
        end = start + struct.calcsize(fmt)
        (self.capabilities, self.actions) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[32:]

    def __len__(self):
        """Return length of message
        """
        l = 32
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.version !=  other.version: return False
        if self.type !=  other.type: return False
        if self.length !=  other.length: return False
        if self.xid !=  other.xid: return False
        if self.datapath_id !=  other.datapath_id: return False
        if self.n_buffers !=  other.n_buffers: return False
        if self.n_tables !=  other.n_tables: return False
        if self.pad !=  other.pad: return False
        if self.capabilities !=  other.capabilities: return False
        if self.actions !=  other.actions: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'version: ' + str(self.version) + '\n'
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'length: ' + str(self.length) + '\n'
        outstr += prefix + 'xid: ' + str(self.xid) + '\n'
        outstr += prefix + 'datapath_id: ' + str(self.datapath_id) + '\n'
        outstr += prefix + 'n_buffers: ' + str(self.n_buffers) + '\n'
        outstr += prefix + 'n_tables: ' + str(self.n_tables) + '\n'
        outstr += prefix + 'capabilities: ' + str(self.capabilities) + '\n'
        outstr += prefix + 'actions: ' + str(self.actions) + '\n'
        return outstr


class ofp_match:
    """Automatically generated Python class for ofp_match

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.wildcards = 0
        self.in_port = 0
        self.eth_src= [0,0,0,0,0,0]
        self.eth_dst= [0,0,0,0,0,0]
        self.vlan_vid = 0
        self.vlan_pcp = 0
        self.pad1 = 0
        self.eth_type = 0
        self.ip_dscp = 0
        self.ip_proto = 0
        self.pad2= [0,0]
        self.ipv4_src = 0
        self.ipv4_dst = 0
        self.tcp_src = 0
        self.tcp_dst = 0

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.eth_src, list)):
            return (False, "self.eth_src is not list as expected.")
        if(len(self.eth_src) != 6):
            return (False, "self.eth_src is not of size 6 as expected.")
        if(not isinstance(self.eth_dst, list)):
            return (False, "self.eth_dst is not list as expected.")
        if(len(self.eth_dst) != 6):
            return (False, "self.eth_dst is not of size 6 as expected.")
        if(not isinstance(self.pad2, list)):
            return (False, "self.pad2 is not list as expected.")
        if(len(self.pad2) != 2):
            return (False, "self.pad2 is not of size 2 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!LH", self.wildcards, self.in_port)
        packed += struct.pack("!BBBBBB", self.eth_src[0], self.eth_src[1], self.eth_src[2], self.eth_src[3], self.eth_src[4], self.eth_src[5])
        packed += struct.pack("!BBBBBB", self.eth_dst[0], self.eth_dst[1], self.eth_dst[2], self.eth_dst[3], self.eth_dst[4], self.eth_dst[5])
        packed += struct.pack("!HBBHBB", self.vlan_vid, self.vlan_pcp, self.pad1, self.eth_type, self.ip_dscp, self.ip_proto)
        packed += struct.pack("!BB", self.pad2[0], self.pad2[1])
        packed += struct.pack("!LLHH", self.ipv4_src, self.ipv4_dst, self.tcp_src, self.tcp_dst)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 40):
            return binaryString
        fmt = '!LH'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.wildcards, self.in_port) = struct.unpack(fmt,  binaryString[start:end])
        fmt = '!BBBBBB'
        start = 6
        end = start + struct.calcsize(fmt)
        (self.eth_src[0], self.eth_src[1], self.eth_src[2], self.eth_src[3], self.eth_src[4], self.eth_src[5]) = struct.unpack(fmt, binaryString[start:end])
        fmt = '!BBBBBB'
        start = 12
        end = start + struct.calcsize(fmt)
        (self.eth_dst[0], self.eth_dst[1], self.eth_dst[2], self.eth_dst[3], self.eth_dst[4], self.eth_dst[5]) = struct.unpack(fmt, binaryString[start:end])
        fmt = '!HBBHBB'
        start = 18
        end = start + struct.calcsize(fmt)
        (self.vlan_vid, self.vlan_pcp, self.pad1, self.eth_type, self.ip_dscp, self.ip_proto) = struct.unpack(fmt,  binaryString[start:end])
        fmt = '!BB'
        start = 26
        end = start + struct.calcsize(fmt)
        (self.pad2[0], self.pad2[1]) = struct.unpack(fmt, binaryString[start:end])
        fmt = '!LLHH'
        start = 28
        end = start + struct.calcsize(fmt)
        (self.ipv4_src, self.ipv4_dst, self.tcp_src, self.tcp_dst) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[40:]

    def __len__(self):
        """Return length of message
        """
        l = 40
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.wildcards !=  other.wildcards: return False
        if self.in_port !=  other.in_port: return False
        if self.eth_src !=  other.eth_src: return False
        if self.eth_dst !=  other.eth_dst: return False
        if self.vlan_vid !=  other.vlan_vid: return False
        if self.vlan_pcp !=  other.vlan_pcp: return False
        if self.pad1 !=  other.pad1: return False
        if self.eth_type !=  other.eth_type: return False
        if self.ip_dscp !=  other.ip_dscp: return False
        if self.ip_proto !=  other.ip_proto: return False
        if self.pad2 !=  other.pad2: return False
        if self.ipv4_src !=  other.ipv4_src: return False
        if self.ipv4_dst !=  other.ipv4_dst: return False
        if self.tcp_src !=  other.tcp_src: return False
        if self.tcp_dst !=  other.tcp_dst: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'wildcards: ' + str(self.wildcards) + '\n'
        outstr += prefix + 'in_port: ' + str(self.in_port) + '\n'
        outstr += prefix + 'eth_src: ' + str(self.eth_src) + '\n'
        outstr += prefix + 'eth_dst: ' + str(self.eth_dst) + '\n'
        outstr += prefix + 'vlan_vid: ' + str(self.vlan_vid) + '\n'
        outstr += prefix + 'vlan_pcp: ' + str(self.vlan_pcp) + '\n'
        outstr += prefix + 'eth_type: ' + str(self.eth_type) + '\n'
        outstr += prefix + 'ip_dscp: ' + str(self.ip_dscp) + '\n'
        outstr += prefix + 'ip_proto: ' + str(self.ip_proto) + '\n'
        outstr += prefix + 'ipv4_src: ' + str(self.ipv4_src) + '\n'
        outstr += prefix + 'ipv4_dst: ' + str(self.ipv4_dst) + '\n'
        outstr += prefix + 'tcp_src: ' + str(self.tcp_src) + '\n'
        outstr += prefix + 'tcp_dst: ' + str(self.tcp_dst) + '\n'
        return outstr


class ofp_header:
    """Automatically generated Python class for ofp_header

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.version = 0x01
        self.type = 0
        self.length = 0
        self.xid = 0

    def __assert(self):
        """Sanity check
        """
        if (not (self.type in ofp_type_map.keys())):
            return (False, "type must have values from ofp_type_map.keys()")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!BBHL", self.version, self.type, self.length, self.xid)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 8):
            return binaryString
        fmt = '!BBHL'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.version, self.type, self.length, self.xid) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[8:]

    def __len__(self):
        """Return length of message
        """
        l = 8
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.version !=  other.version: return False
        if self.type !=  other.type: return False
        if self.length !=  other.length: return False
        if self.xid !=  other.xid: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'version: ' + str(self.version) + '\n'
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'length: ' + str(self.length) + '\n'
        outstr += prefix + 'xid: ' + str(self.xid) + '\n'
        return outstr


class ofp_vendor_header:
    """Automatically generated Python class for ofp_vendor_header

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.version = 0
        self.type = 0
        self.length = 0
        self.xid = 0
        self.vendor = 0

    def __assert(self):
        """Sanity check
        """
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!BBHLL", self.version, self.type, self.length, self.xid, self.vendor)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 12):
            return binaryString
        fmt = '!BBHLL'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.version, self.type, self.length, self.xid, self.vendor) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[12:]

    def __len__(self):
        """Return length of message
        """
        l = 12
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.version !=  other.version: return False
        if self.type !=  other.type: return False
        if self.length !=  other.length: return False
        if self.xid !=  other.xid: return False
        if self.vendor !=  other.vendor: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'version: ' + str(self.version) + '\n'
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'length: ' + str(self.length) + '\n'
        outstr += prefix + 'xid: ' + str(self.xid) + '\n'
        outstr += prefix + 'vendor: ' + str(self.vendor) + '\n'
        return outstr


class ofp_packet_out:
    """Automatically generated Python class for ofp_packet_out

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.version = 0
        self.type = 0
        self.length = 0
        self.xid = 0
        self.buffer_id = 4294967295
        self.in_port = 0
        self.actions_len = 0

    def __assert(self):
        """Sanity check
        """
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!BBHLLHH", self.version, self.type, self.length, self.xid, self.buffer_id, self.in_port, self.actions_len)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 16):
            return binaryString
        fmt = '!BBHLLHH'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.version, self.type, self.length, self.xid, self.buffer_id, self.in_port, self.actions_len) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[16:]

    def __len__(self):
        """Return length of message
        """
        l = 16
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.version !=  other.version: return False
        if self.type !=  other.type: return False
        if self.length !=  other.length: return False
        if self.xid !=  other.xid: return False
        if self.buffer_id !=  other.buffer_id: return False
        if self.in_port !=  other.in_port: return False
        if self.actions_len !=  other.actions_len: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'version: ' + str(self.version) + '\n'
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'length: ' + str(self.length) + '\n'
        outstr += prefix + 'xid: ' + str(self.xid) + '\n'
        outstr += prefix + 'buffer_id: ' + str(self.buffer_id) + '\n'
        outstr += prefix + 'in_port: ' + str(self.in_port) + '\n'
        outstr += prefix + 'actions_len: ' + str(self.actions_len) + '\n'
        return outstr


class ofp_action_nw_addr:
    """Automatically generated Python class for ofp_action_nw_addr

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.type = 0
        self.len = 0
        self.nw_addr = 0

    def __assert(self):
        """Sanity check
        """
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!HHL", self.type, self.len, self.nw_addr)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 8):
            return binaryString
        fmt = '!HHL'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.type, self.len, self.nw_addr) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[8:]

    def __len__(self):
        """Return length of message
        """
        l = 8
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.type !=  other.type: return False
        if self.len !=  other.len: return False
        if self.nw_addr !=  other.nw_addr: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'len: ' + str(self.len) + '\n'
        outstr += prefix + 'nw_addr: ' + str(self.nw_addr) + '\n'
        return outstr


class ofp_action_vlan_pcp:
    """Automatically generated Python class for ofp_action_vlan_pcp

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.type = 0
        self.len = 0
        self.vlan_pcp = 0
        self.pad= [0,0,0]

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.pad, list)):
            return (False, "self.pad is not list as expected.")
        if(len(self.pad) != 3):
            return (False, "self.pad is not of size 3 as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!HHB", self.type, self.len, self.vlan_pcp)
        packed += struct.pack("!BBB", self.pad[0], self.pad[1], self.pad[2])
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 8):
            return binaryString
        fmt = '!HHB'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.type, self.len, self.vlan_pcp) = struct.unpack(fmt,  binaryString[start:end])
        fmt = '!BBB'
        start = 5
        end = start + struct.calcsize(fmt)
        (self.pad[0], self.pad[1], self.pad[2]) = struct.unpack(fmt, binaryString[start:end])
        return binaryString[8:]

    def __len__(self):
        """Return length of message
        """
        l = 8
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.type !=  other.type: return False
        if self.len !=  other.len: return False
        if self.vlan_pcp !=  other.vlan_pcp: return False
        if self.pad !=  other.pad: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'len: ' + str(self.len) + '\n'
        outstr += prefix + 'vlan_pcp: ' + str(self.vlan_pcp) + '\n'
        return outstr


class ofp_flow_mod:
    """Automatically generated Python class for ofp_flow_mod

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.version = 0
        self.type = 0
        self.length = 0
        self.xid = 0
        self.match = ofp_match()
        self.cookie = 0
        self.command = 0
        self.idle_timeout = 0
        self.hard_timeout = 0
        self.priority = 0x8000
        self.buffer_id = 0
        self.out_port = 0
        self.flags = 0

    def __assert(self):
        """Sanity check
        """
        if(not isinstance(self.match, ofp_match)):
            return (False, "self.match is not class ofp_match as expected.")
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!BBHL", self.version, self.type, self.length, self.xid)
        packed += self.match.pack()
        packed += struct.pack("!QHHHHLHH", self.cookie, self.command, self.idle_timeout, self.hard_timeout, self.priority, self.buffer_id, self.out_port, self.flags)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 72):
            return binaryString
        fmt = '!BBHL'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.version, self.type, self.length, self.xid) = struct.unpack(fmt,  binaryString[start:end])
        self.match.unpack(binaryString[8:])
        fmt = '!QHHHHLHH'
        start = 48
        end = start + struct.calcsize(fmt)
        (self.cookie, self.command, self.idle_timeout, self.hard_timeout, self.priority, self.buffer_id, self.out_port, self.flags) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[72:]

    def __len__(self):
        """Return length of message
        """
        l = 72
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.version !=  other.version: return False
        if self.type !=  other.type: return False
        if self.length !=  other.length: return False
        if self.xid !=  other.xid: return False
        if self.match !=  other.match: return False
        if self.cookie !=  other.cookie: return False
        if self.command !=  other.command: return False
        if self.idle_timeout !=  other.idle_timeout: return False
        if self.hard_timeout !=  other.hard_timeout: return False
        if self.priority !=  other.priority: return False
        if self.buffer_id !=  other.buffer_id: return False
        if self.out_port !=  other.out_port: return False
        if self.flags !=  other.flags: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'version: ' + str(self.version) + '\n'
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'length: ' + str(self.length) + '\n'
        outstr += prefix + 'xid: ' + str(self.xid) + '\n'
        outstr += prefix + 'match: \n' 
        outstr += self.match.show(prefix + '  ')
        outstr += prefix + 'cookie: ' + str(self.cookie) + '\n'
        outstr += prefix + 'command: ' + str(self.command) + '\n'
        outstr += prefix + 'idle_timeout: ' + str(self.idle_timeout) + '\n'
        outstr += prefix + 'hard_timeout: ' + str(self.hard_timeout) + '\n'
        outstr += prefix + 'priority: ' + str(self.priority) + '\n'
        outstr += prefix + 'buffer_id: ' + str(self.buffer_id) + '\n'
        outstr += prefix + 'out_port: ' + str(self.out_port) + '\n'
        outstr += prefix + 'flags: ' + str(self.flags) + '\n'
        return outstr


class ofp_error_msg:
    """Automatically generated Python class for ofp_error_msg

    Date 2013-03-11
    Created by of.pythonize.pythonizer
    Core structure: Messages do not include ofp_header
    Does not include var-length arrays
    """
    def __init__(self):
        """Initialize
        Declare members and default values
        """
        self.version = 0
        self.type = 0
        self.length = 0
        self.xid = 0
        self.err_type = 0
        self.code = 0

    def __assert(self):
        """Sanity check
        """
        return (True, None)

    def pack(self, assertstruct=True):
        """Pack message
        Packs empty array used as placeholder
        """
        if(assertstruct):
            if(not self.__assert()[0]):
                return None
        packed = ""
        packed += struct.pack("!BBHLHH", self.version, self.type, self.length, self.xid, self.err_type, self.code)
        return packed

    def unpack(self, binaryString):
        """Unpack message
        Do not unpack empty array used as placeholder
        since they can contain heterogeneous type
        """
        if (len(binaryString) < 12):
            return binaryString
        fmt = '!BBHLHH'
        start = 0
        end = start + struct.calcsize(fmt)
        (self.version, self.type, self.length, self.xid, self.err_type, self.code) = struct.unpack(fmt,  binaryString[start:end])
        return binaryString[12:]

    def __len__(self):
        """Return length of message
        """
        l = 12
        return l

    def __eq__(self, other):
        """Return True if self and other have same values
        """
        if type(self) != type(other): return False
        if self.version !=  other.version: return False
        if self.type !=  other.type: return False
        if self.length !=  other.length: return False
        if self.xid !=  other.xid: return False
        if self.err_type !=  other.err_type: return False
        if self.code !=  other.code: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    def show(self, prefix=''):
        """Generate string showing basic members of structure
        """
        outstr = ''
        outstr += prefix + 'version: ' + str(self.version) + '\n'
        outstr += prefix + 'type: ' + str(self.type) + '\n'
        outstr += prefix + 'length: ' + str(self.length) + '\n'
        outstr += prefix + 'xid: ' + str(self.xid) + '\n'
        outstr += prefix + 'err_type: ' + str(self.err_type) + '\n'
        outstr += prefix + 'code: ' + str(self.code) + '\n'
        return outstr


# Enumerated type definitions
ofp_error_type = ['OFPET_HELLO_FAILED', 'OFPET_BAD_REQUEST', 'OFPET_BAD_ACTION', 'OFPET_FLOW_MOD_FAILED', 'OFPET_PORT_MOD_FAILED', 'OFPET_QUEUE_OP_FAILED']
OFPET_HELLO_FAILED                  = 0
OFPET_BAD_REQUEST                   = 1
OFPET_BAD_ACTION                    = 2
OFPET_FLOW_MOD_FAILED               = 3
OFPET_PORT_MOD_FAILED               = 4
OFPET_QUEUE_OP_FAILED               = 5
ofp_error_type_map = {
    0                               : 'OFPET_HELLO_FAILED',
    1                               : 'OFPET_BAD_REQUEST',
    2                               : 'OFPET_BAD_ACTION',
    3                               : 'OFPET_FLOW_MOD_FAILED',
    4                               : 'OFPET_PORT_MOD_FAILED',
    5                               : 'OFPET_QUEUE_OP_FAILED'
}

ofp_flow_mod_flags = ['OFPFF_SEND_FLOW_REM', 'OFPFF_CHECK_OVERLAP', 'OFPFF_EMERG']
OFPFF_SEND_FLOW_REM                 = 1
OFPFF_CHECK_OVERLAP                 = 2
OFPFF_EMERG                         = 4
ofp_flow_mod_flags_map = {
    1                               : 'OFPFF_SEND_FLOW_REM',
    2                               : 'OFPFF_CHECK_OVERLAP',
    4                               : 'OFPFF_EMERG'
}

ofp_stats_reply_flags = ['OFPSF_REPLY_MORE']
OFPSF_REPLY_MORE                    = 1
ofp_stats_reply_flags_map = {
    1                               : 'OFPSF_REPLY_MORE'
}

ofp_flow_mod_failed_code = ['OFPFMFC_ALL_TABLES_FULL', 'OFPFMFC_OVERLAP', 'OFPFMFC_EPERM', 'OFPFMFC_BAD_EMERG_TIMEOUT', 'OFPFMFC_BAD_COMMAND', 'OFPFMFC_UNSUPPORTED']
OFPFMFC_ALL_TABLES_FULL             = 0
OFPFMFC_OVERLAP                     = 1
OFPFMFC_EPERM                       = 2
OFPFMFC_BAD_EMERG_TIMEOUT           = 3
OFPFMFC_BAD_COMMAND                 = 4
OFPFMFC_UNSUPPORTED                 = 5
ofp_flow_mod_failed_code_map = {
    0                               : 'OFPFMFC_ALL_TABLES_FULL',
    1                               : 'OFPFMFC_OVERLAP',
    2                               : 'OFPFMFC_EPERM',
    3                               : 'OFPFMFC_BAD_EMERG_TIMEOUT',
    4                               : 'OFPFMFC_BAD_COMMAND',
    5                               : 'OFPFMFC_UNSUPPORTED'
}

ofp_port_config = ['OFPPC_PORT_DOWN', 'OFPPC_NO_STP', 'OFPPC_NO_RECV', 'OFPPC_NO_RECV_STP', 'OFPPC_NO_FLOOD', 'OFPPC_NO_FWD', 'OFPPC_NO_PACKET_IN']
OFPPC_PORT_DOWN                     = 1
OFPPC_NO_STP                        = 2
OFPPC_NO_RECV                       = 4
OFPPC_NO_RECV_STP                   = 8
OFPPC_NO_FLOOD                      = 16
OFPPC_NO_FWD                        = 32
OFPPC_NO_PACKET_IN                  = 64
ofp_port_config_map = {
    1                               : 'OFPPC_PORT_DOWN',
    2                               : 'OFPPC_NO_STP',
    4                               : 'OFPPC_NO_RECV',
    8                               : 'OFPPC_NO_RECV_STP',
    16                              : 'OFPPC_NO_FLOOD',
    32                              : 'OFPPC_NO_FWD',
    64                              : 'OFPPC_NO_PACKET_IN'
}

ofp_port_state = ['OFPPS_LINK_DOWN', 'OFPPS_STP_LISTEN', 'OFPPS_STP_LEARN', 'OFPPS_STP_FORWARD', 'OFPPS_STP_BLOCK', 'OFPPS_STP_MASK']
OFPPS_LINK_DOWN                     = 1
OFPPS_STP_LISTEN                    = 0
OFPPS_STP_LEARN                     = 256
OFPPS_STP_FORWARD                   = 512
OFPPS_STP_BLOCK                     = 768
OFPPS_STP_MASK                      = 768
ofp_port_state_map = {
    1                               : 'OFPPS_LINK_DOWN',
    0                               : 'OFPPS_STP_LISTEN',
    256                             : 'OFPPS_STP_LEARN',
    512                             : 'OFPPS_STP_FORWARD',
    768                             : 'OFPPS_STP_BLOCK',
    768                             : 'OFPPS_STP_MASK'
}

ofp_config_flags = ['OFPC_FRAG_NORMAL', 'OFPC_FRAG_DROP', 'OFPC_FRAG_REASM', 'OFPC_FRAG_MASK']
OFPC_FRAG_NORMAL                    = 0
OFPC_FRAG_DROP                      = 1
OFPC_FRAG_REASM                     = 2
OFPC_FRAG_MASK                      = 3
ofp_config_flags_map = {
    0                               : 'OFPC_FRAG_NORMAL',
    1                               : 'OFPC_FRAG_DROP',
    2                               : 'OFPC_FRAG_REASM',
    3                               : 'OFPC_FRAG_MASK'
}

ofp_hello_failed_code = ['OFPHFC_INCOMPATIBLE', 'OFPHFC_EPERM']
OFPHFC_INCOMPATIBLE                 = 0
OFPHFC_EPERM                        = 1
ofp_hello_failed_code_map = {
    0                               : 'OFPHFC_INCOMPATIBLE',
    1                               : 'OFPHFC_EPERM'
}

ofp_capabilities = ['OFPC_FLOW_STATS', 'OFPC_TABLE_STATS', 'OFPC_PORT_STATS', 'OFPC_STP', 'OFPC_RESERVED', 'OFPC_IP_REASM', 'OFPC_QUEUE_STATS', 'OFPC_ARP_MATCH_IP']
OFPC_FLOW_STATS                     = 1
OFPC_TABLE_STATS                    = 2
OFPC_PORT_STATS                     = 4
OFPC_STP                            = 8
OFPC_RESERVED                       = 16
OFPC_IP_REASM                       = 32
OFPC_QUEUE_STATS                    = 64
OFPC_ARP_MATCH_IP                   = 128
ofp_capabilities_map = {
    1                               : 'OFPC_FLOW_STATS',
    2                               : 'OFPC_TABLE_STATS',
    4                               : 'OFPC_PORT_STATS',
    8                               : 'OFPC_STP',
    16                              : 'OFPC_RESERVED',
    32                              : 'OFPC_IP_REASM',
    64                              : 'OFPC_QUEUE_STATS',
    128                             : 'OFPC_ARP_MATCH_IP'
}

ofp_flow_removed_reason = ['OFPRR_IDLE_TIMEOUT', 'OFPRR_HARD_TIMEOUT', 'OFPRR_DELETE']
OFPRR_IDLE_TIMEOUT                  = 0
OFPRR_HARD_TIMEOUT                  = 1
OFPRR_DELETE                        = 2
ofp_flow_removed_reason_map = {
    0                               : 'OFPRR_IDLE_TIMEOUT',
    1                               : 'OFPRR_HARD_TIMEOUT',
    2                               : 'OFPRR_DELETE'
}

ofp_queue_properties = ['OFPQT_NONE', 'OFPQT_MIN_RATE']
OFPQT_NONE                          = 0
OFPQT_MIN_RATE                      = 0
ofp_queue_properties_map = {
    0                               : 'OFPQT_NONE',
    0                               : 'OFPQT_MIN_RATE'
}

ofp_flow_wildcards = ['OFPFW_IN_PORT', 'OFPFW_DL_VLAN', 'OFPFW_DL_SRC', 'OFPFW_DL_DST', 'OFPFW_DL_TYPE', 'OFPFW_NW_PROTO', 'OFPFW_TP_SRC', 'OFPFW_TP_DST', 'OFPFW_NW_SRC_SHIFT', 'OFPFW_NW_SRC_BITS', 'OFPFW_NW_SRC_MASK', 'OFPFW_NW_SRC_ALL', 'OFPFW_NW_DST_SHIFT', 'OFPFW_NW_DST_BITS', 'OFPFW_NW_DST_MASK', 'OFPFW_NW_DST_ALL', 'OFPFW_DL_VLAN_PCP', 'OFPFW_NW_TOS', 'OFPFW_ALL']
OFPFW_IN_PORT                       = 1
OFPFW_DL_VLAN                       = 2
OFPFW_DL_SRC                        = 4
OFPFW_DL_DST                        = 8
OFPFW_DL_TYPE                       = 16
OFPFW_NW_PROTO                      = 32
OFPFW_TP_SRC                        = 64
OFPFW_TP_DST                        = 128
OFPFW_NW_SRC_SHIFT                  = 8
OFPFW_NW_SRC_BITS                   = 6
OFPFW_NW_SRC_MASK                   = 16128
OFPFW_NW_SRC_ALL                    = 8192
OFPFW_NW_DST_SHIFT                  = 14
OFPFW_NW_DST_BITS                   = 6
OFPFW_NW_DST_MASK                   = 1032192
OFPFW_NW_DST_ALL                    = 524288
OFPFW_DL_VLAN_PCP                   = 1048576
OFPFW_NW_TOS                        = 2097152
OFPFW_ALL                           = 4194303
ofp_flow_wildcards_map = {
    1                               : 'OFPFW_IN_PORT',
    2                               : 'OFPFW_DL_VLAN',
    4                               : 'OFPFW_DL_SRC',
    8                               : 'OFPFW_DL_DST',
    16                              : 'OFPFW_DL_TYPE',
    32                              : 'OFPFW_NW_PROTO',
    64                              : 'OFPFW_TP_SRC',
    128                             : 'OFPFW_TP_DST',
    8                               : 'OFPFW_NW_SRC_SHIFT',
    6                               : 'OFPFW_NW_SRC_BITS',
    16128                           : 'OFPFW_NW_SRC_MASK',
    8192                            : 'OFPFW_NW_SRC_ALL',
    14                              : 'OFPFW_NW_DST_SHIFT',
    6                               : 'OFPFW_NW_DST_BITS',
    1032192                         : 'OFPFW_NW_DST_MASK',
    524288                          : 'OFPFW_NW_DST_ALL',
    1048576                         : 'OFPFW_DL_VLAN_PCP',
    2097152                         : 'OFPFW_NW_TOS',
    4194303                         : 'OFPFW_ALL'
}

ofp_port_reason = ['OFPPR_ADD', 'OFPPR_DELETE', 'OFPPR_MODIFY']
OFPPR_ADD                           = 0
OFPPR_DELETE                        = 1
OFPPR_MODIFY                        = 2
ofp_port_reason_map = {
    0                               : 'OFPPR_ADD',
    1                               : 'OFPPR_DELETE',
    2                               : 'OFPPR_MODIFY'
}

ofp_action_type = ['OFPAT_OUTPUT', 'OFPAT_SET_VLAN_VID', 'OFPAT_SET_VLAN_PCP', 'OFPAT_STRIP_VLAN', 'OFPAT_SET_DL_SRC', 'OFPAT_SET_DL_DST', 'OFPAT_SET_NW_SRC', 'OFPAT_SET_NW_DST', 'OFPAT_SET_NW_TOS', 'OFPAT_SET_TP_SRC', 'OFPAT_SET_TP_DST', 'OFPAT_ENQUEUE', 'OFPAT_VENDOR']
OFPAT_OUTPUT                        = 0
OFPAT_SET_VLAN_VID                  = 1
OFPAT_SET_VLAN_PCP                  = 2
OFPAT_STRIP_VLAN                    = 3
OFPAT_SET_DL_SRC                    = 4
OFPAT_SET_DL_DST                    = 5
OFPAT_SET_NW_SRC                    = 6
OFPAT_SET_NW_DST                    = 7
OFPAT_SET_NW_TOS                    = 8
OFPAT_SET_TP_SRC                    = 9
OFPAT_SET_TP_DST                    = 10
OFPAT_ENQUEUE                       = 11
OFPAT_VENDOR                        = 65535
ofp_action_type_map = {
    0                               : 'OFPAT_OUTPUT',
    1                               : 'OFPAT_SET_VLAN_VID',
    2                               : 'OFPAT_SET_VLAN_PCP',
    3                               : 'OFPAT_STRIP_VLAN',
    4                               : 'OFPAT_SET_DL_SRC',
    5                               : 'OFPAT_SET_DL_DST',
    6                               : 'OFPAT_SET_NW_SRC',
    7                               : 'OFPAT_SET_NW_DST',
    8                               : 'OFPAT_SET_NW_TOS',
    9                               : 'OFPAT_SET_TP_SRC',
    10                              : 'OFPAT_SET_TP_DST',
    11                              : 'OFPAT_ENQUEUE',
    65535                           : 'OFPAT_VENDOR'
}

ofp_flow_mod_command = ['OFPFC_ADD', 'OFPFC_MODIFY', 'OFPFC_MODIFY_STRICT', 'OFPFC_DELETE', 'OFPFC_DELETE_STRICT']
OFPFC_ADD                           = 0
OFPFC_MODIFY                        = 1
OFPFC_MODIFY_STRICT                 = 2
OFPFC_DELETE                        = 3
OFPFC_DELETE_STRICT                 = 4
ofp_flow_mod_command_map = {
    0                               : 'OFPFC_ADD',
    1                               : 'OFPFC_MODIFY',
    2                               : 'OFPFC_MODIFY_STRICT',
    3                               : 'OFPFC_DELETE',
    4                               : 'OFPFC_DELETE_STRICT'
}

ofp_queue_op_failed_code = ['OFPQOFC_BAD_PORT', 'OFPQOFC_BAD_QUEUE', 'OFPQOFC_EPERM']
OFPQOFC_BAD_PORT                    = 0
OFPQOFC_BAD_QUEUE                   = 1
OFPQOFC_EPERM                       = 2
ofp_queue_op_failed_code_map = {
    0                               : 'OFPQOFC_BAD_PORT',
    1                               : 'OFPQOFC_BAD_QUEUE',
    2                               : 'OFPQOFC_EPERM'
}

ofp_port = ['OFPP_MAX', 'OFPP_IN_PORT', 'OFPP_TABLE', 'OFPP_NORMAL', 'OFPP_FLOOD', 'OFPP_ALL', 'OFPP_CONTROLLER', 'OFPP_LOCAL', 'OFPP_NONE']
OFPP_MAX                            = 65280
OFPP_IN_PORT                        = 65528
OFPP_TABLE                          = 65529
OFPP_NORMAL                         = 65530
OFPP_FLOOD                          = 65531
OFPP_ALL                            = 65532
OFPP_CONTROLLER                     = 65533
OFPP_LOCAL                          = 65534
OFPP_NONE                           = 65535
ofp_port_map = {
    65280                           : 'OFPP_MAX',
    65528                           : 'OFPP_IN_PORT',
    65529                           : 'OFPP_TABLE',
    65530                           : 'OFPP_NORMAL',
    65531                           : 'OFPP_FLOOD',
    65532                           : 'OFPP_ALL',
    65533                           : 'OFPP_CONTROLLER',
    65534                           : 'OFPP_LOCAL',
    65535                           : 'OFPP_NONE'
}

ofp_bad_action_code = ['OFPBAC_BAD_TYPE', 'OFPBAC_BAD_LEN', 'OFPBAC_BAD_VENDOR', 'OFPBAC_BAD_VENDOR_TYPE', 'OFPBAC_BAD_OUT_PORT', 'OFPBAC_BAD_ARGUMENT', 'OFPBAC_EPERM', 'OFPBAC_TOO_MANY', 'OFPBAC_BAD_QUEUE']
OFPBAC_BAD_TYPE                     = 0
OFPBAC_BAD_LEN                      = 1
OFPBAC_BAD_VENDOR                   = 2
OFPBAC_BAD_VENDOR_TYPE              = 3
OFPBAC_BAD_OUT_PORT                 = 4
OFPBAC_BAD_ARGUMENT                 = 5
OFPBAC_EPERM                        = 6
OFPBAC_TOO_MANY                     = 7
OFPBAC_BAD_QUEUE                    = 8
ofp_bad_action_code_map = {
    0                               : 'OFPBAC_BAD_TYPE',
    1                               : 'OFPBAC_BAD_LEN',
    2                               : 'OFPBAC_BAD_VENDOR',
    3                               : 'OFPBAC_BAD_VENDOR_TYPE',
    4                               : 'OFPBAC_BAD_OUT_PORT',
    5                               : 'OFPBAC_BAD_ARGUMENT',
    6                               : 'OFPBAC_EPERM',
    7                               : 'OFPBAC_TOO_MANY',
    8                               : 'OFPBAC_BAD_QUEUE'
}

ofp_bad_request_code = ['OFPBRC_BAD_VERSION', 'OFPBRC_BAD_TYPE', 'OFPBRC_BAD_STAT', 'OFPBRC_BAD_VENDOR', 'OFPBRC_BAD_SUBTYPE', 'OFPBRC_EPERM', 'OFPBRC_BAD_LEN', 'OFPBRC_BUFFER_EMPTY', 'OFPBRC_BUFFER_UNKNOWN']
OFPBRC_BAD_VERSION                  = 0
OFPBRC_BAD_TYPE                     = 1
OFPBRC_BAD_STAT                     = 2
OFPBRC_BAD_VENDOR                   = 3
OFPBRC_BAD_SUBTYPE                  = 4
OFPBRC_EPERM                        = 5
OFPBRC_BAD_LEN                      = 6
OFPBRC_BUFFER_EMPTY                 = 7
OFPBRC_BUFFER_UNKNOWN               = 8
ofp_bad_request_code_map = {
    0                               : 'OFPBRC_BAD_VERSION',
    1                               : 'OFPBRC_BAD_TYPE',
    2                               : 'OFPBRC_BAD_STAT',
    3                               : 'OFPBRC_BAD_VENDOR',
    4                               : 'OFPBRC_BAD_SUBTYPE',
    5                               : 'OFPBRC_EPERM',
    6                               : 'OFPBRC_BAD_LEN',
    7                               : 'OFPBRC_BUFFER_EMPTY',
    8                               : 'OFPBRC_BUFFER_UNKNOWN'
}

ofp_port_features = ['OFPPF_10MB_HD', 'OFPPF_10MB_FD', 'OFPPF_100MB_HD', 'OFPPF_100MB_FD', 'OFPPF_1GB_HD', 'OFPPF_1GB_FD', 'OFPPF_10GB_FD', 'OFPPF_COPPER', 'OFPPF_FIBER', 'OFPPF_AUTONEG', 'OFPPF_PAUSE', 'OFPPF_PAUSE_ASYM']
OFPPF_10MB_HD                       = 1
OFPPF_10MB_FD                       = 2
OFPPF_100MB_HD                      = 4
OFPPF_100MB_FD                      = 8
OFPPF_1GB_HD                        = 16
OFPPF_1GB_FD                        = 32
OFPPF_10GB_FD                       = 64
OFPPF_COPPER                        = 128
OFPPF_FIBER                         = 256
OFPPF_AUTONEG                       = 512
OFPPF_PAUSE                         = 1024
OFPPF_PAUSE_ASYM                    = 2048
ofp_port_features_map = {
    1                               : 'OFPPF_10MB_HD',
    2                               : 'OFPPF_10MB_FD',
    4                               : 'OFPPF_100MB_HD',
    8                               : 'OFPPF_100MB_FD',
    16                              : 'OFPPF_1GB_HD',
    32                              : 'OFPPF_1GB_FD',
    64                              : 'OFPPF_10GB_FD',
    128                             : 'OFPPF_COPPER',
    256                             : 'OFPPF_FIBER',
    512                             : 'OFPPF_AUTONEG',
    1024                            : 'OFPPF_PAUSE',
    2048                            : 'OFPPF_PAUSE_ASYM'
}

ofp_type = ['OFPT_HELLO', 'OFPT_ERROR', 'OFPT_ECHO_REQUEST', 'OFPT_ECHO_REPLY', 'OFPT_VENDOR', 'OFPT_FEATURES_REQUEST', 'OFPT_FEATURES_REPLY', 'OFPT_GET_CONFIG_REQUEST', 'OFPT_GET_CONFIG_REPLY', 'OFPT_SET_CONFIG', 'OFPT_PACKET_IN', 'OFPT_FLOW_REMOVED', 'OFPT_PORT_STATUS', 'OFPT_PACKET_OUT', 'OFPT_FLOW_MOD', 'OFPT_PORT_MOD', 'OFPT_STATS_REQUEST', 'OFPT_STATS_REPLY', 'OFPT_BARRIER_REQUEST', 'OFPT_BARRIER_REPLY', 'OFPT_QUEUE_GET_CONFIG_REQUEST', 'OFPT_QUEUE_GET_CONFIG_REPLY']
OFPT_HELLO                          = 0
OFPT_ERROR                          = 1
OFPT_ECHO_REQUEST                   = 2
OFPT_ECHO_REPLY                     = 3
OFPT_VENDOR                         = 4
OFPT_FEATURES_REQUEST               = 5
OFPT_FEATURES_REPLY                 = 6
OFPT_GET_CONFIG_REQUEST             = 7
OFPT_GET_CONFIG_REPLY               = 8
OFPT_SET_CONFIG                     = 9
OFPT_PACKET_IN                      = 10
OFPT_FLOW_REMOVED                   = 11
OFPT_PORT_STATUS                    = 12
OFPT_PACKET_OUT                     = 13
OFPT_FLOW_MOD                       = 14
OFPT_PORT_MOD                       = 15
OFPT_STATS_REQUEST                  = 16
OFPT_STATS_REPLY                    = 17
OFPT_BARRIER_REQUEST                = 18
OFPT_BARRIER_REPLY                  = 19
OFPT_QUEUE_GET_CONFIG_REQUEST       = 20
OFPT_QUEUE_GET_CONFIG_REPLY         = 21
ofp_type_map = {
    0                               : 'OFPT_HELLO',
    1                               : 'OFPT_ERROR',
    2                               : 'OFPT_ECHO_REQUEST',
    3                               : 'OFPT_ECHO_REPLY',
    4                               : 'OFPT_VENDOR',
    5                               : 'OFPT_FEATURES_REQUEST',
    6                               : 'OFPT_FEATURES_REPLY',
    7                               : 'OFPT_GET_CONFIG_REQUEST',
    8                               : 'OFPT_GET_CONFIG_REPLY',
    9                               : 'OFPT_SET_CONFIG',
    10                              : 'OFPT_PACKET_IN',
    11                              : 'OFPT_FLOW_REMOVED',
    12                              : 'OFPT_PORT_STATUS',
    13                              : 'OFPT_PACKET_OUT',
    14                              : 'OFPT_FLOW_MOD',
    15                              : 'OFPT_PORT_MOD',
    16                              : 'OFPT_STATS_REQUEST',
    17                              : 'OFPT_STATS_REPLY',
    18                              : 'OFPT_BARRIER_REQUEST',
    19                              : 'OFPT_BARRIER_REPLY',
    20                              : 'OFPT_QUEUE_GET_CONFIG_REQUEST',
    21                              : 'OFPT_QUEUE_GET_CONFIG_REPLY'
}

ofp_packet_in_reason = ['OFPR_NO_MATCH', 'OFPR_ACTION']
OFPR_NO_MATCH                       = 0
OFPR_ACTION                         = 1
ofp_packet_in_reason_map = {
    0                               : 'OFPR_NO_MATCH',
    1                               : 'OFPR_ACTION'
}

ofp_stats_types = ['OFPST_DESC', 'OFPST_FLOW', 'OFPST_AGGREGATE', 'OFPST_TABLE', 'OFPST_PORT', 'OFPST_QUEUE', 'OFPST_VENDOR']
OFPST_DESC                          = 0
OFPST_FLOW                          = 1
OFPST_AGGREGATE                     = 2
OFPST_TABLE                         = 3
OFPST_PORT                          = 4
OFPST_QUEUE                         = 5
OFPST_VENDOR                        = 65535
ofp_stats_types_map = {
    0                               : 'OFPST_DESC',
    1                               : 'OFPST_FLOW',
    2                               : 'OFPST_AGGREGATE',
    3                               : 'OFPST_TABLE',
    4                               : 'OFPST_PORT',
    5                               : 'OFPST_QUEUE',
    65535                           : 'OFPST_VENDOR'
}

ofp_port_mod_failed_code = ['OFPPMFC_BAD_PORT', 'OFPPMFC_BAD_HW_ADDR']
OFPPMFC_BAD_PORT                    = 0
OFPPMFC_BAD_HW_ADDR                 = 1
ofp_port_mod_failed_code_map = {
    0                               : 'OFPPMFC_BAD_PORT',
    1                               : 'OFPPMFC_BAD_HW_ADDR'
}

# Values from macro definitions
OFP_FLOW_PERMANENT = 0
OFP_DL_TYPE_ETH2_CUTOFF = 0x0600
DESC_STR_LEN = 256
OFPFW_ICMP_CODE = OFPFW_TP_DST
OFPQ_MIN_RATE_UNCFG = 0xffff
OFP_VERSION = 0x01
OFP_MAX_TABLE_NAME_LEN = 32
OFP_DL_TYPE_NOT_ETH_TYPE = 0x05ff
OFP_DEFAULT_MISS_SEND_LEN = 128
OFP_MAX_PORT_NAME_LEN = 16
OFP_SSL_PORT = 6633
OFPFW_ICMP_TYPE = OFPFW_TP_SRC
OFP_TCP_PORT = 6633
SERIAL_NUM_LEN = 32
OFP_DEFAULT_PRIORITY = 0x8000
OFP_ETH_ALEN = 6
OFP_VLAN_NONE = 0xffff
OFPQ_ALL = 0xffffffff

# Basic structure size definitions.
# Does not include ofp_header members.
# Does not include variable length arrays.
OFP_ACTION_DL_ADDR_BYTES = 16
OFP_ACTION_ENQUEUE_BYTES = 16
OFP_ACTION_HEADER_BYTES = 8
OFP_ACTION_NW_ADDR_BYTES = 8
OFP_ACTION_NW_TOS_BYTES = 8
OFP_ACTION_OUTPUT_BYTES = 8
OFP_ACTION_TP_PORT_BYTES = 8
OFP_ACTION_VENDOR_HEADER_BYTES = 8
OFP_ACTION_VLAN_PCP_BYTES = 8
OFP_ACTION_VLAN_VID_BYTES = 8
OFP_AGGREGATE_STATS_REPLY_BYTES = 24
OFP_AGGREGATE_STATS_REQUEST_BYTES = 44
OFP_DESC_STATS_BYTES = 1056
OFP_ERROR_MSG_BYTES = 12
OFP_FLOW_MOD_BYTES = 72
OFP_FLOW_REMOVED_BYTES = 88
OFP_FLOW_STATS_BYTES = 88
OFP_FLOW_STATS_REQUEST_BYTES = 44
OFP_HEADER_BYTES = 8
OFP_HELLO_BYTES = 8
OFP_MATCH_BYTES = 40
OFP_PACKET_IN_BYTES = 18
OFP_PACKET_OUT_BYTES = 16
OFP_PACKET_QUEUE_BYTES = 8
OFP_PHY_PORT_BYTES = 48
OFP_PORT_MOD_BYTES = 32
OFP_PORT_STATS_BYTES = 104
OFP_PORT_STATS_REQUEST_BYTES = 8
OFP_PORT_STATUS_BYTES = 64
OFP_QUEUE_GET_CONFIG_REPLY_BYTES = 16
OFP_QUEUE_GET_CONFIG_REQUEST_BYTES = 12
OFP_QUEUE_PROP_HEADER_BYTES = 8
OFP_QUEUE_PROP_MIN_RATE_BYTES = 16
OFP_QUEUE_STATS_BYTES = 32
OFP_QUEUE_STATS_REQUEST_BYTES = 8
OFP_STATS_REPLY_BYTES = 12
OFP_STATS_REQUEST_BYTES = 12
OFP_SWITCH_CONFIG_BYTES = 12
OFP_SWITCH_FEATURES_BYTES = 32
OFP_TABLE_STATS_BYTES = 64
OFP_VENDOR_HEADER_BYTES = 12

