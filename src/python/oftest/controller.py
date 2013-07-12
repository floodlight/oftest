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


FILTER=''.join([(len(repr(chr(x)))==3) and chr(x) or '.' 
                for x in range(256)])

def hex_dump_buffer(src, length=16):
    """
    Convert src to a hex dump string and return the string
    @param src The source buffer
    @param length The number of bytes shown in each line
    @returns A string showing the hex dump
    """
    result = ["\n"]
    for i in xrange(0, len(src), length):
       chars = src[i:i+length]
       hex = ' '.join(["%02x" % ord(x) for x in chars])
       printable = ''.join(["%s" % ((ord(x) <= 127 and
                                     FILTER[ord(x)]) or '.') for x in chars])
       result.append("%04x  %-*s  %s\n" % (i, length*3, hex, printable))
    return ''.join(result)

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
    echo replies
    @var initial_hello If true, will send a hello message immediately
    upon connecting to the switch
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
        self.sync = Lock()
        self.handlers = {}
        self.keep_alive = False
        self.active = True
        self.initial_hello = True

        # OpenFlow message/packet queue
        # Protected by the packets_cv lock / condition variable
        self.packets = []
        self.packets_cv = Condition()

        # Settings
        self.max_pkts = max_pkts
        self.passive = True
        self.host = host
        self.port = port
        self.dbg_state = "init"
        self.logger = logging.getLogger("controller")
        self.filter_packet_in = False # Drop "excessive" packet ins
        self.pkt_in_run = 0 # Count on run of packet ins
        self.pkt_in_filter_limit = 50 # Count on run of packet ins
        self.pkt_in_dropped = 0 # Total dropped packet ins
        self.transact_to = 15 # Transact timeout default value; add to config

        # Transaction and message type waiting variables 
        #   xid_cv: Condition variable (semaphore) for packet waiters
        #   xid: Transaction ID being waited on
        #   xid_response: Transaction response message
        self.xid_cv = Condition()
        self.xid = None
        self.xid_response = None

        self.buffered_input = ""

    def filter_packet(self, rawmsg, hdr):
        """
        Check if packet should be filtered

        Currently filters packet in messages
        @return Boolean, True if packet should be dropped
        """
        # Add check for packet in and rate limit
        if self.filter_packet_in:
            # If we were dropping packets, report number dropped
            # TODO dont drop expected packet ins
            if self.pkt_in_run > self.pkt_in_filter_limit:
                self.logger.debug("Dropped %d packet ins (%d total)"
                            % ((self.pkt_in_run - 
                                self.pkt_in_filter_limit),
                                self.pkt_in_dropped))
            self.pkt_in_run = 0

        return False

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
            if not hdr or hdr.length == 0:
                self.logger.error("Could not parse header")
                self.logger.error("pkt len %d." % len(pkt))
                if hdr:
                    self.logger.error("hdr len %d." % hdr.length)
                self.logger.error("%s" % hex_dump_buffer(pkt[:200]))
                self.kill()
                return

            # Extract the raw message bytes
            if (offset + hdr.length) > len(pkt):
                break
            rawmsg = pkt[offset : offset + hdr.length]
            offset += hdr.length

            if self.filter_packet(rawmsg, hdr):
                continue

            self.logger.debug("Msg in: buf len %d. hdr.type %s. hdr.len %d" %
                              (len(pkt), ofp_type_map[hdr.type], hdr.length))
            if hdr.version != OFP_VERSION:
                self.logger.error("Version %d does not match OFTest version %d"
                                  % (hdr.version, OFP_VERSION))
                print "Version %d does not match OFTest version %d" % \
                    (hdr.version, OFP_VERSION)
                self.disconnect()
                return

            msg = of_message_parse(rawmsg)
            if not msg:
                self.parse_errors += 1
                self.logger.warn("Could not parse message")
                continue

            with self.sync:
                # Check if transaction is waiting
                with self.xid_cv:
                    if self.xid and hdr.xid == self.xid:
                        self.logger.debug("Matched expected XID " + str(hdr.xid))
                        self.xid_response = (msg, rawmsg)
                        self.xid = None
                        self.xid_cv.notify()
                        continue

                # Check if keep alive is set; if so, respond to echo requests
                if self.keep_alive:
                    if hdr.type == OFPT_ECHO_REQUEST:
                        self.logger.debug("Responding to echo request")
                        rep = echo_reply()
                        rep.header.xid = hdr.xid
                        # Ignoring additional data
                        if self.message_send(rep.pack(), zero_xid=True) < 0:
                            self.logger.error("Error sending echo reply")
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
                    with self.packets_cv:
                        if len(self.packets) >= self.max_pkts:
                            self.packets.pop(0)
                            self.packets_expired += 1
                        self.packets.append((msg, rawmsg))
                        self.packets_cv.notify_all()
                    self.packets_total += 1
                else:
                    self.packets_handled += 1
                    self.logger.debug("Message handled by callback")

        # end of 'while offset < len(pkt)'
        #   note that if offset = len(pkt), this is
        #   appends a harmless empty string
        self.buffered_input += pkt[offset:]

    def _socket_ready_handle(self, s):
        """
        Handle an input-ready socket

        @param s The socket object that is ready
        @returns 0 on success, -1 on error
        """

        if s and s == self.listen_socket:
            if self.switch_socket:
                self.logger.warning("Ignoring incoming connection; already connected to switch")
                (sock, addr) = self.listen_socket.accept()
                sock.close()
                return 0

            try:
                (sock, addr) = self.listen_socket.accept()
            except:
                self.logger.warning("Error on listen socket accept")
                return -1
            self.socs.append(sock)
            self.logger.info("Incoming connection from %s" % str(addr))

            with self.connect_cv:
                (self.switch_socket, self.switch_addr) = (sock, addr)
                if self.initial_hello:
                    self.message_send(hello())
                self.connect_cv.notify() # Notify anyone waiting
        elif s and s == self.switch_socket:
            for idx in range(3): # debug: try a couple of times
                try:
                    pkt = self.switch_socket.recv(self.rcv_size)
                except:
                    self.logger.warning("Error on switch read")
                    return -1
      
                if not self.active:
                    return 0
      
                if len(pkt) == 0:
                    self.logger.warning("Zero-length switch read, %d" % idx)
                else:
                    break

            if len(pkt) == 0: # Still no packet
                self.logger.warning("Zero-length switch read; closing cxn")
                self.logger.info(str(self))
                return -1

            self._pkt_handle(pkt)
        else:
            self.logger.error("Unknown socket ready: " + str(s))
            return -1

        return 0

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
            try:
                sel_in, sel_out, sel_err = \
                    select.select(self.socs, [], self.socs, 1)
            except:
                print sys.exc_info()
                self.logger.error("Select error, disconnecting")
                self.disconnect()

            for s in sel_err:
                self.logger.error("Got socket error on: " + str(s) + ", disconnecting")
                self.disconnect()

            for s in sel_in:
                if self._socket_ready_handle(s) == -1:
                    self.disconnect()

        # End of main loop
        self.dbg_state = "closing"
        self.logger.info("Exiting controller thread")
        self.shutdown()

    def connect(self, timeout=-1):
        """
        Connect to the switch

        @param timeout Block for up to timeout seconds. Pass -1 for the default.
        @return Boolean, True if connected
        """

        with self.connect_cv:
            timed_wait(self.connect_cv, lambda: self.switch_socket, timeout=timeout)
        return self.switch_socket is not None
        
    def disconnect(self, timeout=-1):
        """
        If connected to a switch, disconnect.
        """
        if self.switch_socket:
            self.socs.remove(self.switch_socket)
            self.switch_socket.close()
            self.switch_socket = None
            self.switch_addr = None
            with self.connect_cv:
                self.connect_cv.notifyAll()

    def wait_disconnected(self, timeout=-1):
        """
        @param timeout Block for up to timeout seconds. Pass -1 for the default.
        @return Boolean, True if disconnected
        """

        with self.connect_cv:
            timed_wait(self.connect_cv, 
                       lambda: True if not self.switch_socket else None, 
                       timeout=timeout)
        return self.switch_socket is None
        
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

        # Wakeup condition variables on which controller may be wait
        with self.xid_cv:
            self.xid_cv.notifyAll()

        with self.connect_cv:
            self.connect_cv.notifyAll()

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

    def poll(self, exp_msg=-1, timeout=-1):
        """
        Wait for the next OF message received from the switch.

        @param exp_msg If set, return only when this type of message 
        is received (unless timeout occurs).

        @param timeout Maximum number of seconds to wait for the message.
        Pass -1 for the default timeout.

        @retval A pair (msg, pkt) where msg is a message object and pkt
        the string representing the packet as received from the socket.
        This allows additional parsing by the receiver if necessary.

        The data members in the message are in host endian order.
        If an error occurs, (None, None) is returned
        """

        if exp_msg!=-1:
            self.logger.debug("Poll for %s" % ofp_type_map[exp_msg])
        else:
            self.logger.debug("Poll for any OF message")

        # Take the packet from the queue
        def grab():
            if len(self.packets) > 0:
                if exp_msg==-1:
                    self.logger.debug("Looking for any packet")
                    (msg, pkt) = self.packets.pop(0)
                    return (msg, pkt)
                else:
                    self.logger.debug("Looking for %s" % ofp_type_map[exp_msg])
                    for i in range(len(self.packets)):
                        msg = self.packets[i][0]
                        self.logger.debug("Checking packets[%d] (%s)" % (i, ofp_type_map[msg.header.type]))
                        if msg.header.type == exp_msg:
                            (msg, pkt) = self.packets.pop(i)
                            return (msg, pkt)
            # Not found
            self.logger.debug("Packet not in queue")
            return None

        with self.packets_cv:
            ret = timed_wait(self.packets_cv, grab, timeout=timeout)

        if ret != None:
            (msg, pkt) = ret
            self.logger.debug("Got message %s" % str(msg))
            return (msg, pkt)
        else:
            return (None, None)

    def transact(self, msg, timeout=-1, zero_xid=False):
        """
        Run a message transaction with the switch

        Send the message in msg and wait for a reply with a matching
        transaction id.  Transactions have the highest priority in
        received message handling.

        @param msg The message object to send; must not be a string
        @param timeout The timeout in seconds; if -1 use default.
        @param zero_xid Normally, if the XID is 0 an XID will be generated
        for the message.  Set zero_xid to override this behavior
        @return The matching message object or None if unsuccessful

        """

        if not zero_xid and msg.header.xid == 0:
            msg.header.xid = gen_xid()

        self.logger.debug("Running transaction %d" % msg.header.xid)

        with self.xid_cv:
            if self.xid:
                self.logger.error("Can only run one transaction at a time")
                return (None, None)

            self.xid = msg.header.xid
            self.xid_response = None
            if self.message_send(msg.pack()) < 0:
                self.logger.error("Error sending pkt for transaction %d" %
                                  msg.header.xid)
                return (None, None)

            self.logger.debug("Waiting for transaction %d" % msg.header.xid)
            timed_wait(self.xid_cv, lambda: self.xid_response, timeout=timeout)

            if self.xid_response:
                (resp, pkt) = self.xid_response
                self.xid_response = None
            else:
                (resp, pkt) = (None, None)

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
        for the message.  Set zero_xid to override this behavior (and keep an
        existing 0 xid)

        @return 0 on success

        """

        if not self.switch_socket:
            # Sending a string indicates the message is ready to go
            raise Exception("no socket")
        #@todo If not string, try to pack
        if type(msg) != type(""):
            if msg.header.xid == 0 and not zero_xid:
                msg.header.xid = gen_xid()
            outpkt = msg.pack()
        else:
            outpkt = msg

        self.logger.debug("Sending pkt of len " + str(len(outpkt)))
        if self.switch_socket.sendall(outpkt) is not None:
            raise Exception("unknown error on sendall")

        return 0

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
        string += "  pkt_in_run      " + str(self.pkt_in_run) + "\n"
        string += "  pkt_in_dropped  " + str(self.pkt_in_dropped) + "\n"
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
