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
@todo Set up reasonable logging facility
@todo Support select and listen on an administrative socket (or
use a timeout to support clean shutdown).

Currently only one connection is accepted during the life of
the controller.   There seems
to be no clean way to interrupt an accept call.  Using select that also listens
on an administrative socket and can shut down the socket might work.

"""

from oft_config import *
import os
import socket
import time
from threading import Thread
from threading import Lock
from threading import Condition
from message import *
from parse import *
from ofutils import *

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

    @todo Consider using SocketServer for listening socket
    @todo Test transaction code

    @var rcv_size The receive size to use for receive calls
    @var max_pkts The max size of the receive queue
    @var keep_alive If true, listen for echo requests and respond w/
    echo replies
    @var host The host to use for connect
    @var port The port to connect on 
    @var packets_total Total number of packets received
    @var packets_expired Number of packets popped from queue as queue full
    @var packets_handled Number of packets handled by something
    @var dbg_state Debug indication of state
    """

    def __init__(self, max_pkts=1024):
        Thread.__init__(self)
        # Socket related
        self.rcv_size = RCV_SIZE_DEFAULT
        self.listen_socket = None
        self.switch_socket = None
        self.switch_addr = None

        # Counters
        self.socket_errors = 0
        self.parse_errors = 0
        self.packets_total = 0
        self.packets_expired = 0
        self.packets_handled = 0

        # State
        self.connected = False
        self.packets = []
        self.sync = Lock()
        self.handlers = {}
        self.keep_alive = False

        # Settings
        self.max_pkts = max_pkts
        self.passive = True
        self.host = controller_host
        self.port = controller_port
        self.dbg_state = "init"
        # self.debug_level = DEBUG_VERBOSE
        self.debug_level = debug_level_default

        # Transaction variables 
        #   xid_cv: Condition variable (semaphore) for transaction
        #   xid: Transaction ID being waited on
        #   xid_response: Transaction response message
        self.xid_cv = Condition()
        self.xid = None
        self.xid_response = None

    def dbg(self, level, string):
        debug_log("CTRL", self.debug_level, level, string)

    def run(self):
        """
        Activity function for class

        Assumes connection to switch already exists.  Listens on
        switch_socket for messages until an error (or zero len pkt)
        occurs.

        When there is a message on the socket, check for handlers; queue the
        packet if no one handles the packet.

        See note for controller describing the limitation of a single
        connection for now.
        """

        if not self.switch_socket:
            self.dbg(DEBUG_ERROR, 
                     "Error in controller thread, no switch socket")
            self.shutdown()
            return

        # Read and process packets from socket connected to switch
        while 1:
            try:
                pkt = self.switch_socket.recv(self.rcv_size)
            except socket.error:
                self.dbg(DEBUG_ERROR, "Controller socket read error")
                self.socket_errors += 1
                break

            if len(pkt) == 0:
                # Considered an error; usually means switch has disconnected
                self.dbg(DEBUG_INFO, "length 0 pkt in")
                self.socket_errors += 1
                break

            if not self.connected:
                break
                
            (handled, msg) = self._pkt_handler_check(pkt)
            if handled:
                self.packets_handled += 1
                continue

            # Not handled, enqueue
            self.sync.acquire()
            if len(self.packets) >= self.max_pkts:
                self.packets.pop(0)
                self.packets_expired += 1
            self.packets.append((msg, pkt))
            self.packets_total += 1
            self.sync.release()

        self.shutdown()

    def connect(self, send_hello=True):
        """
        Connect to a switch and start this thread

        Create the listening socket, accept and block until a
        connection is made to the switch.  Then start the local
        thread and return.  Parameters to the call are take from
        member variables.

        @param send_hello If True, send the initial hello packet on connection
        @return Boolean where True indicates success 

        If already connected, returns True
        If the listen socket does not exist, will create it
        """

        self.dbg_state = "connecting"
        self.dbg(DEBUG_INFO, "open ctl host: >" + str(self.host) + "< port " +
            str(self.port))
        # Create the listening socket
        if not self.listen_socket:
            self.listen_socket = socket.socket(socket.AF_INET, 
                                               socket.SOCK_STREAM)
            self.listen_socket.setsockopt(socket.SOL_SOCKET, 
                                          socket.SO_REUSEADDR, 1)
            self.listen_socket.bind((self.host, self.port))
        self.dbg_state = "listening"
        self.listen_socket.listen(LISTEN_QUEUE_SIZE)
        self.dbg_state = "accepting"
        (self.switch_socket, self.switch_addr) = self.listen_socket.accept()
        if not self.switch_socket:
            self.socket_errors += 1
            self.dbg(DEBUG_WARN, "Failed on accept")
            self.dbg_state = "error"
            self.listen_socket.close()
            return False

        self.connected = True
        self.dbg_state = "connected"
        self.dbg(DEBUG_INFO, "Got connection to " + str(self.switch_addr))

        if send_hello:
            h = hello()
            self.message_send(h.pack())

        # Start the background thread
        self.start()

        return True

    def shutdown(self):
        """
        Shutdown the controller closing all sockets

        @todo Might want to synchronize shutdown with self.sync...
        """
        self.connected = False
        self.dbg_state = "closed"
        if self.switch_socket:
            try:
                self.switch_socket.shutdown(socket.SHUT_RDWR)
            except:
                self.dbg(DEBUG_INFO, "Ignoring switch soc shutdown error")
            self.switch_socket = None

        if self.listen_socket:
            try:
                self.listen_socket.shutdown(socket.SHUT_RDWR)
            except:
                self.dbg(DEBUG_INFO, "Ignoring listen soc shutdown error")
            self.listen_socket = None
        
    def _pkt_handler_check(self, pkt):
        """
        Check for packet handling before being enqueued

        This includes checking for an ongoing transaction (see transact())
        an echo request in case keep_alive is true, followed by
        registered message handlers.
        @param pkt The raw packet (string)
        @return (handled, msg) where handled is a boolean indicating
        the message was handled; msg if None is the parsed message
        """
        # Parse the header to get type
        hdr = of_header_parse(pkt)
        if not hdr:
            self.dbg(DEBUG_INFO, "Could not parse header, pkt len", len(pkt))
            self.parse_errors += 1
            return (True, None)
        # if self.debug_level <= DEBUG_VERBOSE:
        #     hdr.show()

        self.dbg(DEBUG_VERBOSE, "message: len %d. type %s. hdr.len %d" %
            (len(pkt), ofp_type_map[hdr.type], hdr.length))
        msg = of_message_parse(pkt)
        if not msg:
            self.parse_errors += 1
            self.dbg(DEBUG_WARN, "Could not parse message")
            return (True, None)

        # Check if transaction is waiting
        self.xid_cv.acquire()
        if self.xid:
            if hdr.xid == self.xid:
                self.xid_response = msg
                self.xid_cv.notify()
                self.xid_cv.release()
                return (True, None)
        self.xid_cv.release()

        # Check if keep alive is set; if so, respond to echo requests
        if self.keep_alive:
            if hdr.type == OFPT_ECHO_REQUEST:
                rep = echo_reply()
                rep.header.xid = hdr.xid
                # Ignoring additional data
                self.message_send(rep.pack())
                return (True, None)

        # Now check for message handlers; preference is given to
        # handlers for a specific packet
        handled = False
        if hdr.type in self.handlers.keys():
            handled = self.handlers[hdr.type](self, msg, pkt)
        if not handled and ("all" in self.handlers.keys()):
            handled = self.handlers["all"](self, msg, pkt)

        return (handled, msg)

    def register(self, msg_type, handler):
        """
        Register a callback to receive a specific message type.

        Only one handler may be registered for a given message type.
        @param msg_type The type of message to receive.  May be DEFAULT 
        for all non-handled packets.  The special type, the string "all"
        will send all packets to the handler.
        @param handler The function to call when a message of the given 
        type is received.
        """
        # Should check type is valid
        if not handler and msg_type in self.handlers.keys():
            del self.handlers[msg_type]
            return
        self.handlers[msg_type] = handler

    def poll(self, exp_msg=None, timeout=None):
        """
        Wait for the next OF message received from the switch.

        @param exp_msg If set, return only when this type of message 
        is received.
        @param timeout Not yet supported

        @retval A pair (msg, pkt) where msg is a message object and pkt
        the string representing the packet as received from the socket.
        This allows additional parsing by the receiver if necessary.

        The data members in the message are in host endian order.
        If an error occurs, None is returned
        """

        # For now do not support time out;
        if timeout:
            self.dbg(DEBUG_WARN, "Poll time out not supported")

        while len(self.packets) > 0:
            self.sync.acquire()
            (msg, pkt) = self.packets.pop(0)
            self.sync.release()
            if not exp_msg or (exp_msg and (msg.header.type == exp_msg)):
                return msg, pkt

        return None, None

    def transact(self, msg, timeout=None, zero_xid=False):
        """
        Run a message transaction with the switch

        Send the message in msg and wait for a reply with a matching
        transaction id.  Transactions have the highest priority in
        received message handling.

        @param msg The message object to send; must not be a string
        @param timeout The timeout in seconds (?)
        @param zero_xid Normally, if the XID is 0 an XID will be generated
        for the message.  Set xero_xid to override this behavior
        @return The matching message object or None if unsuccessful

        """

        if not zero_xid and msg.header.xid == 0:
            msg.header.xid = gen_xid()

        self.xid_cv.acquire()
        if self.xid:
            self.xid_cv.release()
            self.dbg(DEBUG_ERROR, 
                     "Can only run one transaction at a time")
            return None

        self.xid = msg.header.xid
        self.xid_response = None
        self.message_send(msg.pack())
        self.xid_cv.wait(timeout)
        msg = self.xid_response
        self.xid_response = None
        self.xid_cv.release()
        return msg

    def message_send(self, msg):
        """
        Send the message to the switch

        @param msg An OpenFlow message object to be forwarded to the switch.  

        @return None on success

        """

        if not self.switch_socket:
            # Sending a string indicates the message is ready to go
            self.dbg(DEBUG_INFO, "message_send: no socket")
            return -1

        if type(msg) != type(""):
            # Sending a string indicates the message is ready to go
            self.dbg(DEBUG_INFO, "message_send requires packet as string")
            return -1

        self.dbg(DEBUG_INFO, "Sending pkt of len " + str(len(msg)))
        return self.switch_socket.sendall(msg)

    def __str__(self):
        string = "Controller:\n"
        string += "  connected       " + str(self.connected) + "\n"
        string += "  state           " + self.dbg_state + "\n"
        string += "  switch_addr     " + str(self.switch_addr) + "\n"
        string += "  pending pkts    " + str(len(self.packets)) + "\n"
        string += "  total pkts      " + str(self.packets_total) + "\n"
        string += "  expired pkts    " + str(self.packets_expired) + "\n"
        string += "  handled pkts    " + str(self.packets_handled) + "\n"
        string += "  parse errors    " + str(self.parse_errors) + "\n"
        string += "  sock errrors    " + str(self.socket_errors) + "\n"
        string += "  max pkts        " + str(self.max_pkts) + "\n"
        string += "  host            " + str(self.host) + "\n"
        string += "  port            " + str(self.port) + "\n"
        string += "  keep_alive      " + str(self.keep_alive) + "\n"
        return string

    def show(self):
        print str(self)

def sample_handler(controller, msg, pkt):
    """
    Sample message handler

    This is the prototype for functions registered with the controller
    class for packet reception

    @param controller The controller calling the handler
    @param msg The parsed message object
    @param pkt The raw packet that was received on the socket.  This is
    in case the packet contains extra unparsed data.
    @returns Boolean value indicating if the packet was handled.  If
    not handled, the packet is placed in the queue for pollers to received
    """
    pass
