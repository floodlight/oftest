"""
OpenFlow Test Framework

Controller class

Provide the interface to the control channel to the switch under test.  

Class inherits from thread so as to run in background allowing
asynchronous callbacks (if needed, not required).  Also supports
polling.

The controller thread maintains a queue.  Incoming messages that
are not handled by a callback function are placed in this queue for 
poll calls.  

Callbacks and polling support specifying the message type

@todo Support transaction semantics via xid
"""

import sys
sys.path.append("../protocol")
import os
import socket
import time
import promisc
from threading import Thread
from threading import Lock
from message import *
from parse import *
from netutils import *

class Controller(Thread):
    """
    Class abstracting the control interface to the switch.  

    For receiving messages, two mechanism will be implemented.  First,
    query the interface with poll.  Second, register to have a
    function called by message type.  The callback is passed the
    message type as well as the raw packet (or message object)

    One of the main purposes of this object is to translate between network 
    and host byte order.  'Above' this object, things should be in host
    byte order.
    """

    def __init__(host=HOST_DEFAULT, port=PORT_DEFAULT, passive=1):
        if (passive):
            # FIXME: add error handling
            self.sock = open_ctrlsocket(host, port)
            self.clientsock, self.clientaddr = self.sock.accept()
        else:
            print "Error in controller init: Active cxn not supported"

    def register(self, msg_type, handler):
        """
        Register a callback to receive a specific message type.

        Only one handler may be registered for a given message type.
        @param msg_type The type of message to receive.  May be DEFAULT 
        for all non-handled packets.  
        @param handler The function to call when a message of the given 
        type is received.
        """
        print "Controller message handler registration not supported"

    def poll(self, exp_msg=None, timeout=RCV_TIMEOUT_DEFAULT):
        """
        Wait for the next OF message received from the switch.

        @param exp_msg If set, return only when this type of message 
        is received.

        @param timeout If set, return E_TIMEOUT if mesage is not
        received in this time.  If set to 0, will not block.

        @retval A triple (msg_type, msg, data) where msg_type is the OpenFlow 
        message type value OFPT_xxx, msg is a message object (from a 
        SWIG generated class) appropriate to the message type and data is
        a string of any additional information following the 
        normal message.  Note that
        many messages do not have classes so ofp_hello is returned which 
        simply has the header.
        The data members in the message are in host endian order.
        If a timeout (or other error) occurs, None is returned
        """
        while 1:
            okay, pkt = rcv_data_from_socket(self.clientsoc, timeout)
            if not okay or not pkt:
                # FIXME: Check for error
                return None, None
            # Convert msg to the proper OpenFlow message object
            hdr = of_header_parse(pkt)
            print "DEBUG: msg in. pkt len %d. type %d. length %d" % \
                (len(pkt), hdr.type, hdr.length)

            if not exp_msg or (exp_msg and (hdr.type == exp_msg)):
                return msg_type, msg

    def transact(self, msg, xid=None):
        """
        Run a transaction

        Send the message in msg and wait for a reply with a matching
        transaction id.

        @param msg The message to send
        @param xid If non None, set the transaction ID of the message; 
        otherwise use the one already present in the message's header.

        """
        print "Controller transact not supported"

    def message_send(self, msg):
        """
        Send the message to the switch

        @param msg An OpenFlow message object to be forwarded to the switch.  

        """
        pass

    def kill(self):
        self.clientsock.close()
