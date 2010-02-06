"""This module exports OpenFlow protocol to Python.

(C) Copyright Stanford University
Date October 2009
Created by ykk
"""
import c2py
import cheader
import os
import socket
import select
import struct
import time

class messages(cheader.cheaderfile,c2py.cstruct2py,c2py.structpacker):
    """Class to handle OpenFlow messages

    (C) Copyright Stanford University
    Date October 2009
    Created by ykk
    """
    def __init__(self, openflow_headerfile=None):
        """Initialize with OpenFlow header file

        If filename is not provided, check the environment
        variable PYLIB_OPENFLOW_HEADER and search for openflow.h
        """
        if (openflow_headerfile != None):
            cheader.cheaderfile.__init__(self, openflow_headerfile)
        else:
            #Check environment variable
            path = os.getenv("PYLIB_OPENFLOW_HEADER")
            if not path:
                print "PYLIB_OPENFLOW_HEADER is not set in environment"
                sys.exit(2)
            cheader.cheaderfile.__init__(self, path+"/openflow.h")
        #Initialize cstruct2py
        c2py.cstruct2py.__init__(self)
        #Initalize packet
        c2py.structpacker.__init__(self, "!")
        ##Cached patterns
        self.patterns={}
        for (cstructname, cstruct) in self.structs.items():
            self.patterns[cstructname] = self.get_pattern(cstruct)

    def get_size(self, ctype):
        """Get size for ctype or name of type.
        Return None if ctype is not expanded or
        type with name is not found.
        """
        pattern = self.get_pattern(ctype)
        if (pattern != None):
            return c2py.cstruct2py.get_size(self,pattern)
    
    def get_pattern(self,ctype):
        """Get pattern string for ctype or name of type.
        Return None if ctype is not expanded or
        type with name is not found.
        """
        if (isinstance(ctype, str)):
            #Is name
            return self.patterns[ctype]
        else:
            return c2py.cstruct2py.get_pattern(self, ctype)
        
    def pack(self, ctype, *arg):
        """Pack packet accordingly ctype or name of type provided.
        Return struct packed.
        """
        if (isinstance(ctype, str)):
            return struct.pack(self.prefix+self.patterns[ctype], *arg)
        else:
            return c2py.structpacker.pack(self, ctype, *arg)

    def peek_from_front(self, ctype, binaryString, returnDictionary=True):
        """Unpack packet using front of the packet,
        accordingly ctype or name of ctype provided.

        Return dictionary of values indexed by arg name, 
        if ctype is known struct/type and returnDictionary is True,
        else return array of data unpacked.
        """
        if (isinstance(ctype,str)):
            data = c2py.structpacker.peek_from_front(self,
                                                     self.patterns[ctype],
                                                     binaryString,
                                                     returnDictionary)
            return self.data2dic(self.structs[ctype], data)
        else:
            return c2py.structpacker.peek_from_front(self,
                                                     ctype,
                                                     binaryString,
                                                     returnDictionary)
        
    def unpack_from_front(self, ctype, binaryString, returnDictionary=True):
        """Unpack packet using front of packet,
        accordingly ctype or name of ctype provided.

        Return (dictionary of values indexed by arg name, 
        remaining binary string) if ctype is known struct/type
        and returnDictionary is True,
        else return (array of data unpacked, remaining binary string).
        """
        if (isinstance(ctype,str)):
            (data, remaining) = c2py.structpacker.unpack_from_front(self,
                                                                    self.patterns[ctype],
                                                                    binaryString,
                                                                    returnDictionary)
            return (self.data2dic(self.structs[ctype], data), remaining)
        else:
            return c2py.structpacker.unpack_from_front(self,
                                                       ctype,
                                                       binaryString,
                                                       returnDictionary)

class connection:
    """Class to hold a connection.

    (C) Copyright Stanford University
    Date October 2009
    Created by ykk
    """
    def __init__(self, messages, sock=None):
        """Initialize
        """
        ##Reference to socket
        self.sock = sock
        ##Internal reference to OpenFlow messages
        self._messages = messages
        ##Buffer
        self.buffer = ""
        ##Header length for OpenFlow
        self.__header_length = self._messages.get_size("ofp_header")

    def send(self, msg):
        """Send bare message (given as binary string)
        """
        raise NotImplementedError()

    def structsend(self, ctype, *arg):
        """Build and send message.
        """
        self.send(self._messages.pack(ctype, *arg))

    def receive(self, maxlength=1024):
       """Receive raw in non-blocking way.

       Return buffer
       """
       if (select.select([self.sock],[],[],0)[0]):
           self.buffer += self.sock.recv(maxlength)
       return self.buffer

    def buffer_has_msg(self):
        """Check if buffer has a complete message
        """
        #Check at least ofp_header is received
        if (len(self.buffer) < self.__header_length):
            return False
        values = self._messages.peek_from_front("ofp_header", self.buffer)
        return (len(self.buffer) >= values["length"][0])

    def get_msg(self):
        """Get message from current buffer
        """
        if (self.buffer_has_msg()):
            values = self._messages.peek_from_front("ofp_header", self.buffer)
            msg = self.buffer[:values["length"][0]]
            self.buffer = self.buffer[values["length"][0]:]
            return msg
        else:
            return None

    def msgreceive(self, blocking=False, pollInterval=0.001):
        """Receive OpenFlow message.

        If non-blocking, can return None.
        """
        self.receive()
        if (self.buffer_has_msg()):
            return self.get_msg()
        if (blocking):
            while (not self.buffer_has_msg()):
                time.sleep(pollInterval)
                self.receive()
        return self.get_msg()

class safeconnection(connection):
    """OpenFlow connection with safety checks
    
    (C) Copyright Stanford University
    Date October 2009
    Created by ykk
    """
    def __init__(self, messages, sock=None, version=None,
                 xidstart = 0, autoxid=True):
        """Initialize with OpenFlow version.
        """
        connection.__init__(self, messages, sock)
        ##OpenFlow version
        if (version != None):
            self.version = version
        else:
            self.version = messages.get_value("OFP_VERSION")
        ##xid Counter
        self.nextxid = xidstart
        ##Automatic xid
        self.autoxid = autoxid
        ##Miss auto xid
        self.skipautoxid = 0

    def skip_auto_xid(self, n):
        """Miss automatic xid for the next n packets
        """
        self.skipautoxid = n

    def structsend_xid(self, ctype, *arg):
        """Build and send message, populating header automatically.
        Type and xid of message is not populated.
        """
        self.skipautoxid+=1
        self.structsend(ctype, *arg)

    def structsend(self, ctype, *arg):
        """Build and send message, populating header automatically.
        Type of message is not populated
        """
        msg = self._messages.pack(ctype, *arg)
        self.structsend_raw(msg)
        
    def structsend_raw(self, msg):
        """Check ofp_header and ensure correctness before sending.
        """
        (dic, remaining) = self._messages.unpack_from_front("ofp_header", msg)
        #Amend header
        if (self.version != None):
            dic["version"][0] = self.version
        if (self.autoxid and (self.skipautoxid == 0)):
            dic["xid"][0] = self.nextxid
            self.nextxid+=1
        if (self.skipautoxid != 0):
            self.skipautoxid-=1
        dic["length"][0] = len(remaining)+8
        #Send message
        self.send(self._messages.pack("ofp_header",
                                      dic["version"][0],
                                      dic["type"][0],
                                      dic["length"][0],
                                      dic["xid"][0])+\
                  remaining)

class tcpsocket(safeconnection):
    """Class to hold connection

    (C) Copyright Stanford University
    Date October 2009
    Created by ykk
    """
    def __init__(self, messages, host, port):
        """Initialize TCP socket to host and port
        """
        safeconnection.__init__(self, messages)
        ##Reference to socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.sock.setblocking(False)
        self.sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 0)

    def __del__(self):
        """Terminate connection
        """
        self.sock.shutdown(1)
        self.sock.close()

    def send(self, msg):
        """Send raw message (binary string)
        """
        self.sock.sendall(msg)

class connections:
    """Class to hold multiple connections
    
    (C) Copyright Stanford University
    Date November 2009
    Created by ykk
    """
    def __init__(self):
        """Initialize
        """
        ##List of sockets
        self.__sockets = []
        ##Dicionary of sockets to connection
        self.__connections = {}
        
    def add_connection(self, reference, connect):
        """Add connection with opaque reference object
        """
        if (not isinstance(connect,connection)): 
            raise RuntimeError("Connection must be openflow.connection!")
        self.__sockets.append(connect.sock)
        self.__connections[connect.sock] = (reference, connect)

    def receive(self, maxlength=1024):
        """Receive raw in non-blocking way
        """
        read_ready = select.select(self.__sockets,[],[],0)[0]
        for sock in read_ready:
            self.__connections[sock][1].receive(maxlength)
        
    def has_msg(self):
        """Check if any of the connections has a message

        Return (reference,connection) with message
        """
        for sock, refconnect in self.__connections.items():
            if (refconnect[1].buffer_has_msg()):
                return refconnect
        return None

    def msgreceive(self, blocking=False, pollInterval=0.001):
        """Receive OpenFlow message.

        If non-blocking, can return None.
        """
        self.receive()
        c = self.has_msg()
        if (c != None):
            return (c[0],c[1].get_msg())
        if (blocking):
            while (c == None):
                time.sleep(pollInterval)
                self.receive()
                c = self.has_msg()
        else:
            return (None, None)
        return (c[0],c[1].get_msg())
