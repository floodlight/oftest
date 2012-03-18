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
@todo Support select and listen on an administrative socket (or
use a timeout to support clean shutdown).

Currently only one connection is accepted during the life of
the controller.   There seems
to be no clean way to interrupt an accept call.  Using select that also listens
on an administrative socket and can shut down the socket might work.

"""

import os
import socket
import time
from threading import Thread
from threading import Lock
from threading import Condition
from message import *
from parse import *
from ofutils import *
# For some reason, it seems select to be last (or later).
# Otherwise get an attribute error when calling select.select
import select
import logging

##@todo Find a better home for these identifiers (controller)
RCV_SIZE_DEFAULT = 32768
LISTEN_QUEUE_SIZE = 1

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
    @var keep_alive If true, listen for echo requests and respond w/
    echo replies
    @var initial_hello If true, will send a hello message immediately
    upon connecting to the switch
    @var exit_on_reset If true, terminate controller on connection reset
    @var host The host to use for connect
    @var port The port to connect on 
    @var packets_total Total number of packets received
    @var packets_expired Number of packets popped from queue as queue full
    @var packets_handled Number of packets handled by something
    @var dbg_state Debug indication of state
    """

    def __init__(self, host='127.0.0.1', port=6633, max_pkts=1024):
        Thread.__init__(self)
        # Socket related
        self.rcv_size = RCV_SIZE_DEFAULT
        self.listen_socket = None
        self.switch_socket = None
        self.switch_addr = None
        self.socs = []
        self.connect_cv = Condition()
        self.message_cv = Condition()

        # Counters
        self.socket_errors = 0
        self.parse_errors = 0
        self.packets_total = 0
        self.packets_expired = 0
        self.packets_handled = 0
        self.poll_discards = 0

        # State
        self.packets = []
        self.sync = Lock()
        self.handlers = {}
        self.keep_alive = False
        self.active = True
        self.initial_hello = True
        self.exit_on_reset = True

        # Settings
        self.max_pkts = max_pkts
        self.passive = True
        self.host = host
        self.port = port
        self.dbg_state = "init"
        self.logger = logging.getLogger("controller")

        # Transaction and message type waiting variables 
        #   xid_cv: Condition variable (semaphore) for packet waiters
        #   xid: Transaction ID being waited on
        #   xid_response: Transaction response message
        #   expect_msg: Is a message being waited on 
        #   expect_msg_cv: Semaphore for waiters
        #   expect_msg_type: Type of message expected
        #   expect_msg_response: Result passed through here

        self.xid_cv = Condition()
        self.xid = None
        self.xid_response = None

        self.expect_msg = False
        self.expect_msg_cv = Condition()
        self.expect_msg_type = None
        self.expect_msg_response = None
        self.buffered_input = ""

    def _pkt_handle(self, pkt):
        """
        Check for all packet handling conditions

        Parse and verify message 
        Check if XID matches something waiting
        Check if message is being expected for a poll operation
        Check if keep alive is on and message is an echo request
        Check if any registered handler wants the packet
        Enqueue if none of those conditions is met

        an echo request in case keep_alive is true, followed by
        registered message handlers.
        @param pkt The raw packet (string) which may contain multiple OF msgs
        """

        # snag any left over data from last read()
        pkt = self.buffered_input + pkt
        self.buffered_input = ""

        # Process each of the OF msgs inside the pkt
        offset = 0
        while offset < len(pkt):
            # Parse the header to get type
            hdr = of_header_parse(pkt[offset:])
            if not hdr:
                self.logger.info("Could not parse header, pkt len", len(pkt))
                self.parse_errors += 1
                return
            if hdr.length == 0:
                self.logger.info("Header length is zero")
                self.parse_errors += 1
                return

            # Extract the raw message bytes
            if (offset + hdr.length) > len( pkt[offset:]):
                break
            rawmsg = pkt[offset : offset + hdr.length]

            self.logger.debug("Msg in: len %d. offset %d. type %s. hdr.len %d" %
                (len(pkt), offset, ofp_type_map[hdr.type], hdr.length))
            if hdr.version != OFP_VERSION:
                self.logger.error("Version %d does not match OFTest version %d"
                                  % (hdr.version, OFP_VERSION))
                print "Version %d does not match OFTest version %d" % \
                    (hdr.version, OFP_VERSION)
                self.active = False
                self.switch_socket = None
                self.kill()

            msg = of_message_parse(rawmsg)
            if not msg:
                self.parse_errors += 1
                self.logger.warn("Could not parse message")
                continue

            self.sync.acquire()

            # Check if transaction is waiting
            self.xid_cv.acquire()
            if self.xid:
                if hdr.xid == self.xid:
                    self.logger.debug("Matched expected XID " + str(hdr.xid))
                    self.xid_response = (msg, rawmsg)
                    self.xid = None
                    self.xid_cv.notify()
                    self.xid_cv.release()
                    self.sync.release()
                    continue
            self.xid_cv.release()

            # PREVENT QUEUE ACCESS AT THIS POINT?
            # Check if anyone waiting on this type of message
            self.expect_msg_cv.acquire()
            if self.expect_msg:
                if not self.expect_msg_type or (self.expect_msg_type == hdr.type):
                    self.logger.debug("Matched expected msg type "
                                       + ofp_type_map[hdr.type])
                    self.expect_msg_response = (msg, rawmsg)
                    self.expect_msg = False
                    self.expect_msg_cv.notify()
                    self.expect_msg_cv.release()
                    self.sync.release()
                    continue
            self.expect_msg_cv.release()

            # Check if keep alive is set; if so, respond to echo requests
            if self.keep_alive:
                if hdr.type == OFPT_ECHO_REQUEST:
                    self.sync.release()
                    self.logger.debug("Responding to echo request")
                    rep = echo_reply()
                    rep.header.xid = hdr.xid
                    # Ignoring additional data
                    self.message_send(rep.pack(), zero_xid=True)
                    offset += hdr.length
                    continue

            # Now check for message handlers; preference is given to
            # handlers for a specific packet
            handled = False
            if hdr.type in self.handlers.keys():
                handled = self.handlers[hdr.type](self, msg, rawmsg)
            if not handled and ("all" in self.handlers.keys()):
                handled = self.handlers["all"](self, msg, rawmsg)

            if not handled: # Not handled, enqueue
                self.logger.debug("Enqueuing pkt type " + ofp_type_map[hdr.type])
                if len(self.packets) >= self.max_pkts:
                    self.packets.pop(0)
                    self.packets_expired += 1
                self.packets.append((msg, rawmsg))
                self.packets_total += 1
            else:
                self.packets_handled += 1
                self.logger.debug("Message handled by callback")

            self.sync.release()
            offset += hdr.length
        # end of 'while offset < len(pkt)'
        #   note that if offset = len(pkt), this is
        #   appends a harmless empty string
        self.buffered_input += pkt[offset:]

    def _socket_ready_handle(self, s):
        """
        Handle an input-ready socket
        @param s The socket object that is ready
        @retval True, reset the switch connection
        """

        if s == self.listen_socket:
            if self.switch_socket:
                self.logger.error("Multiple switch cxns not supported")
                sys.exit(1)

            (self.switch_socket, self.switch_addr) = \
                self.listen_socket.accept()
            self.logger.info("Got cxn to " + str(self.switch_addr))
            # Notify anyone waiting
            self.connect_cv.acquire()
            self.connect_cv.notify()
            self.connect_cv.release()
            self.socs.append(self.switch_socket)
            if self.initial_hello:
                self.message_send(hello())
        elif s == self.switch_socket:
            try:
                pkt = self.switch_socket.recv(self.rcv_size)
            except:
                self.logger.warning("Error on switch read")
                return True

            if not self.active:
                return False

            if len(pkt) == 0:
                self.logger.info("zero-len pkt in")
                return True

            self._pkt_handle(pkt)
        else:
            self.logger.error("Unknown socket ready: " + str(s))
            return True

        return False

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

        self.dbg_state = "starting"

        # Create listen socket
        self.logger.info("Create/listen at " + self.host + ":" + 
                 str(self.port))
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, 
                                      socket.SO_REUSEADDR, 1)
        self.listen_socket.bind((self.host, self.port))
        self.dbg_state = "listening"
        self.listen_socket.listen(LISTEN_QUEUE_SIZE)

        self.logger.info("Waiting for switch connection")
        self.socs = [self.listen_socket]
        self.dbg_state = "running"
        while self.active:
            reset_switch_cxn = False
            try:
                sel_in, sel_out, sel_err = \
                    select.select(self.socs, [], self.socs, 1)
            except:
                print sys.exc_info()
                self.logger.error("Select error, exiting")
                sys.exit(1)

            if not self.active:
                break

            for s in sel_in:
                reset_switch_cxn = self._socket_ready_handle(s)

            for s in sel_err:
                self.logger.error("Got socket error on: " + str(s))
                if s == self.switch_socket:
                    reset_switch_cxn = True
                else:
                    self.logger.error("Socket error; exiting")
                    self.active = False
                    break

            if self.active and reset_switch_cxn:
                if self.exit_on_reset:
                    self.kill()
                else:
                    self.logger.warning("Closing switch cxn")
                    try:
                        self.switch_socket.close()
                    except:
                        pass
                    self.switch_socket = None
                    self.socs = self.socs[0:1]

        # End of main loop
        self.dbg_state = "closing"
        self.logger.info("Exiting controller thread")
        self.shutdown()

    def connect(self, timeout=None):
        """
        Connect to the switch

        @param timeout If None, block until connected.  If 0, return 
        immedidately.  Otherwise, block for up to timeout seconds
        @return Boolean, True if connected
        """

        if timeout == 0:
            return self.switch_socket is not None
        if self.switch_socket is not None:
            return True
        self.connect_cv.acquire()
        self.connect_cv.wait(timeout)
        self.connect_cv.release()

        return self.switch_socket is not None
        
    def kill(self):
        """
        Force the controller thread to quit

        Just sets the active state variable to false and expects
        the select timeout to kick in
        """
        self.active = False

    def shutdown(self):
        """
        Shutdown the controller closing all sockets

        @todo Might want to synchronize shutdown with self.sync...
        """
        self.active = False
        try:
            self.switch_socket.shutdown(socket.SHUT_RDWR)
        except:
            self.logger.info("Ignoring switch soc shutdown error")
        self.switch_socket = None

        try:
            self.listen_socket.shutdown(socket.SHUT_RDWR)
        except:
            self.logger.info("Ignoring listen soc shutdown error")
        self.listen_socket = None
        self.dbg_state = "down"

    def register(self, msg_type, handler):
        """
        Register a callback to receive a specific message type.

        Only one handler may be registered for a given message type.

        WARNING:  A lock is held during the handler call back, so 
        the handler should not make any blocking calls

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
        is received (unless timeout occurs).
        @param timeout If None, do not block.  Otherwise, sleep in
        intervals of 1 second until message is received.

        @retval A pair (msg, pkt) where msg is a message object and pkt
        the string representing the packet as received from the socket.
        This allows additional parsing by the receiver if necessary.

        The data members in the message are in host endian order.
        If an error occurs, (None, None) is returned

        The current queue is searched for a message of the desired type
        before sleeping on message in events.
        """

        msg = pkt = None

        self.logger.debug("Poll for " + ofp_type_map[exp_msg])
        # First check the current queue
        self.sync.acquire()
        if len(self.packets) > 0:
            if not exp_msg:
                (msg, pkt) = self.packets.pop(0)
                self.sync.release()
                return (msg, pkt)
            else:
                for i in range(len(self.packets)):
                    msg = self.packets[i][0]
                    if msg.header.type == exp_msg:
                        (msg, pkt) = self.packets.pop(i)
                        self.sync.release()
                        return (msg, pkt)

        # Okay, not currently in the queue
        if timeout is None or timeout <= 0:
            self.sync.release()
            return (None, None)

        msg = pkt = None
        self.logger.debug("Entering timeout")
        # Careful of race condition releasing sync before message cv
        # Also, this style is ripe for a lockup.
        self.expect_msg_cv.acquire()
        self.sync.release()
        self.expect_msg_response = None
        self.expect_msg = True
        self.expect_msg_type = exp_msg
        self.expect_msg_cv.wait(timeout)
        if self.expect_msg_response is not None:
            (msg, pkt) = self.expect_msg_response
        self.expect_msg_cv.release()

        if msg is None:
            self.logger.debug("Poll time out")
        else:
            self.logger.debug("Got msg " + str(msg))

        return (msg, pkt)

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
            self.logger.error("Can only run one transaction at a time")
            return None

        self.xid = msg.header.xid
        self.xid_response = None
        self.message_send(msg.pack())
        self.xid_cv.wait(timeout)
        if self.xid_response:
            (resp, pkt) = self.xid_response
            self.xid_response = None
        else:
            (resp, pkt) = (None, None)
        self.xid_cv.release()
        if resp is None:
            self.logger.warning("No response for xid " + str(self.xid))
        return (resp, pkt)

    def message_send(self, msg, zero_xid=False):
        """
        Send the message to the switch

        @param msg A string or OpenFlow message object to be forwarded to
        the switch.
        @param zero_xid If msg is an OpenFlow object (not a string) and if
        the XID in the header is 0, then an XID will be generated
        for the message.  Set xero_xid to override this behavior (and keep an
        existing 0 xid)

        @return -1 if error, 0 on success

        """

        if not self.switch_socket:
            # Sending a string indicates the message is ready to go
            self.logger.info("message_send: no socket")
            return -1
        #@todo If not string, try to pack
        if type(msg) != type(""):
            try:
                if msg.header.xid == 0 and not zero_xid:
                    msg.header.xid = gen_xid()
                outpkt = msg.pack()
            except:
                self.logger.error(
                         "message_send: not an OF message or string?")
                return -1
        else:
            outpkt = msg

        self.logger.debug("Sending pkt of len " + str(len(outpkt)))
        if self.switch_socket.sendall(outpkt) is None:
            return 0

        self.logger.error("Unknown error on sendall")
        return -1

    def __str__(self):
        string = "Controller:\n"
        string += "  state           " + self.dbg_state + "\n"
        string += "  switch_addr     " + str(self.switch_addr) + "\n"
        string += "  pending pkts    " + str(len(self.packets)) + "\n"
        string += "  total pkts      " + str(self.packets_total) + "\n"
        string += "  expired pkts    " + str(self.packets_expired) + "\n"
        string += "  handled pkts    " + str(self.packets_handled) + "\n"
        string += "  poll discards   " + str(self.poll_discards) + "\n"
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
