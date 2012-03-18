"""This module simulates the network.

Copyright(C) 2009, Stanford University
Date November 2009
Created by ykk
"""
import openflow
import output
import of.msg
import of.network

class network(of.network.network):
    """Class to simulate OpenFlow network

    Copyright(C) 2009, Stanford University
    Date November 2009
    Created by ykk
    """
    def __init__(self):
        """Initialize network
        """
        of.network.network.__init__(self)
        ##Name of use for output
        self.name = self.__class__.__name__+str(id(self))

class link(of.network.link):
    """Class to simulate link

    Copyright(C) 2009, Stanford University
    Date November 2009
    Created by ykk
    """
    def __init__(self, switch1, switch2, isUp=True):
        """Initialize link
        """
        of.network.link.__init__(self, switch1, switch2)
        ##Name of use for output
        self.name = self.__class__.__name__+str(id(self))
        ##Indicate if link is up
        self.isUp = isUp

class switch(of.network.switch):
    """Class to simulate OpenFlow switch

    Copyright(C) 2009, Stanford University
    Date November 2009
    Created by ykk
    """
    def __init__(self,  messages, controller, port, miss_send_len=128,
                 dpid=None, n_buffers=100, n_tables=1,
                 capability=None, parser=None, connection=None):
        """Initialize switch
        """
        of.network.switch.__init__(self,  miss_send_len,
                                   None, dpid, n_buffers, n_tables,
                                   capability)
        ##Name of use for output
        self.name = self.__class__.__name__+str(id(self))
        ##Reference to OpenFlow messages
        self.__messages = messages
        ##Reference to connection
        self.connection = openflow.tcpsocket(messages, controller, port)
        self.sock = self.connection.sock
        ##Reference to Parser
        self.parser = None
        if (parser == None):
            self.parser = of.msg.parser(messages)
        else:
            self.parser = parser

    def receive_openflow(self, packet):
        """Switch receive OpenFlow packet, and respond accordingly
        """
        dic = self.__messages.peek_from_front("ofp_header", packet)
        if (dic["type"][0] == self.__messages.get_value("OFPT_HELLO")):
            output.dbg("Receive hello", self.name)
        elif (dic["type"][0] == self.__messages.get_value("OFPT_ECHO_REQUEST")):
            self.reply_echo(dic["xid"][0])
        elif (dic["type"][0] == self.__messages.get_value("OFPT_FEATURES_REQUEST")):
            self.reply_features(dic["xid"][0])
        elif (dic["type"][0] == self.__messages.get_value("OFPT_FLOW_MOD")):
            self.handle_flow_mod(packet)
        else:
            output.dbg("Unprocessed message "+self.parser.header_describe(dic),
                       self.name)

    def send_hello(self):
        """Send hello
        """
        self.connection.structsend("ofp_hello",
                                   0, self.__messages.get_value("OFPT_HELLO"),
                                   0, 0)
        output.dbg("Send hello",self.name)

    def send_packet(self, inport, bufferid=None, packet="", xid=0, reason=None):
        """Send packet in
        Assume no match as reason, bufferid = 0xFFFFFFFF,
        and empty packet by default
        """
        if (reason == None):
            reason = self.__messages.get_value("OFPR_NO_MATCH")
        if (bufferid == None):
            bufferid = int("0xFFFFFFFF",16)
        pktin = self.__messages.pack("ofp_packet_in",
                                     0, self.__messages.get_value("OFPT_PACKET_IN"),
                                     0, xid, #header
                                     bufferid, len(packet),
                                     inport, reason, 0)
        self.connection.structsend_raw(pktin+packet)
        output.dbg("Send packet ",self.name)

    def send_echo(self, xid=0):
        """Send echo
        """
        self.connection.structsend_xid("ofp_header",
                                       0, self.__messages.get_value("OFPT_ECHO_REQUEST"),
                                       0, xid)
        output.dbg("Send echo", self.name)

    def reply_echo(self, xid):
        """Reply to echo request
        """
        self.connection.structsend_xid("ofp_header",
                                       0, self.__messages.get_value("OFPT_ECHO_REPLY"),
                                       0, xid)                                 
        output.dbg("Reply echo of xid:"+str(xid),self.name)

    def reply_features(self, xid):
        """Reply to feature request
        """
        self.connection.structsend_xid("ofp_switch_features",
                                       0, self.__messages.get_value("OFPT_FEATURES_REPLY"),
                                       0, xid,
                                       self.datapath_id, self.n_buffers,
                                       self.n_tables,0,0,0,
                                       self.capability.get_capability(self.__messages),
                                       self.capability.get_actions(self.__messages))
        output.dbg("Replied features request of xid "+str(xid), self.name)
        
    def handle_flow_mod(self, packet):
        """Handle flow mod: just print it here
        """
        output.dbg(self.parser.flow_mod_describe(packet), self.name)
        
