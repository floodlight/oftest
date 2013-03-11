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
import struct
import select
import logging
from threading import Thread
from threading import Lock
from threading import Condition
import ofp
import ofutils


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
    @var switch If not None, do an active connection to the switch
    @var host The host to use for connect
    @var port The port to connect on 
    @var packets_total Total number of packets received
    @var packets_expired Number of packets popped from queue as queue full
    @var packets_handled Number of packets handled by something
    @var dbg_state Debug indication of state
    """

    def __init__(self, switch=None, host='127.0.0.1', port=6633, max_pkts=1024):
        Thread.__init__(self)
        # Socket related
        self.rcv_size = RCV_SIZE_DEFAULT
        self.listen_socket = None
        self.switch_socket = None
        self.switch_addr = None
        self.connect_cv = Condition()
        self.message_cv = Condition()

        # Used to wake up the event loop from another thread
        self.waker = ofutils.EventDescriptor()

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
        self.switch = switch
        self.passive = not self.switch
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

        # Create listen socket
        if self.passive:
            self.logger.info("Create/listen at " + self.host + ":" +
                             str(self.port))
            self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listen_socket.setsockopt(socket.SOL_SOCKET,
                                          socket.SO_REUSEADDR, 1)
            self.listen_socket.bind((self.host, self.port))
            self.listen_socket.listen(LISTEN_QUEUE_SIZE)

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
            hdr = ofp.parse.of_header_parse(pkt[offset:])
            if not hdr or hdr.length == 0:
                self.logger.error("Could not parse header")
                self.logger.error("pkt len %d." % len(pkt))
                if hdr:
                    self.logger.error("hdr len %d." % hdr.length)
                self.logger.error("%s" % hex_dump_buffer(pkt[:200]))
                self.shutdown()
                return

            # Extract the raw message bytes
            if (offset + hdr.length) > len(pkt):
                break
            rawmsg = pkt[offset : offset + hdr.length]
            offset += hdr.length

            if self.filter_packet(rawmsg, hdr):
                continue

            self.logger.debug("Msg in: buf len %d. hdr.type %s. hdr.len %d hdr.version %d hdr.xid %d" %
                              (len(pkt), ofp.ofp_type_map[hdr.type], hdr.length, hdr.version, hdr.xid))
            if hdr.version < ofp.OFP_VERSION:
                self.logger.error("Switch only supports up to OpenFlow version %d (OFTest version is %d)",
                                  hdr.version, ofp.OFP_VERSION)
                print "Switch only supports up to OpenFlow version %d (OFTest version is %d)" % \
                    (hdr.version, ofp.OFP_VERSION)
                self.disconnect()
                return

            msg = ofp.parse.of_message_parse(rawmsg)
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
                    if hdr.type == ofp.OFPT_ECHO_REQUEST:
                        self.logger.debug("Responding to echo request")
                        rep = ofp.message.echo_reply()
                        rep.xid = hdr.xid
                        # Ignoring additional data
                        self.message_send(rep.pack())
                        continue

                # Log error messages
                if hdr.type == ofp.OFPT_ERROR:
                    if msg.err_type in ofp.ofp_error_type_map:
                        type_str = ofp.ofp_error_type_map[msg.err_type]
                        if msg.err_type == ofp.OFPET_HELLO_FAILED:
                            code_map = ofp.ofp_hello_failed_code_map
                        elif msg.err_type == ofp.OFPET_BAD_REQUEST:
                            code_map = ofp.ofp_bad_request_code_map
                        elif msg.err_type == ofp.OFPET_BAD_ACTION:
                            code_map = ofp.ofp_bad_action_code_map
                        elif msg.err_type == ofp.OFPET_FLOW_MOD_FAILED:
                            code_map = ofp.ofp_flow_mod_failed_code_map
                        elif msg.err_type == ofp.OFPET_PORT_MOD_FAILED:
                            code_map = ofp.ofp_port_mod_failed_code_map
                        elif msg.err_type == ofp.OFPET_QUEUE_OP_FAILED:
                            code_map = ofp.ofp_queue_op_failed_code_map
                        else:
                            code_map = None

                        if code_map and msg.code in code_map:
                            code_str = code_map[msg.code]
                        else:
                            code_str = "unknown"
                    else:
                        type_str = "unknown"
                    self.logger.warn("Received error message: xid=%d type=%s (%d) code=%s (%d)",
                                     hdr.xid, type_str, msg.err_type, code_str, msg.code)

                # Now check for message handlers; preference is given to
                # handlers for a specific packet
                handled = False
                if hdr.type in self.handlers.keys():
                    handled = self.handlers[hdr.type](self, msg, rawmsg)
                if not handled and ("all" in self.handlers.keys()):
                    handled = self.handlers["all"](self, msg, rawmsg)

                if not handled: # Not handled, enqueue
                    self.logger.debug("Enqueuing pkt type " + ofp.ofp_type_map[hdr.type])
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

        if self.passive and s and s == self.listen_socket:
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
            self.logger.info(self.host+":"+str(self.port)+": Incoming connection from "+str(addr))

            with self.connect_cv:
                (self.switch_socket, self.switch_addr) = (sock, addr)
                self.switch_socket.setsockopt(socket.IPPROTO_TCP,
                                              socket.TCP_NODELAY, True)
                if self.initial_hello:
                    self.message_send(ofp.message.hello())
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
        elif s and s == self.waker:
            self.waker.wait()
        else:
            self.logger.error("Unknown socket ready: " + str(s))
            return -1

        return 0

    def active_connect(self):
        """
        Actively connect to a switch IP addr
        """
        try:
            self.logger.info("Trying active connection to %s" % self.switch)
            soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            soc.connect((self.switch, self.port))
            self.logger.info("Connected to " + self.switch + " on " +
                         str(self.port))
            soc.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
            self.switch_addr = (self.switch, self.port)
            return soc
        except (StandardError, socket.error), e:
            self.logger.error("Could not connect to %s at %d:: %s" % 
                              (self.switch, self.port, str(e)))
        return None

    def wakeup(self):
        """
        Wake up the event loop, presumably from another thread.
        """
        self.waker.notify()

    def sockets(self):
        """
        Return list of sockets to select on.
        """
        socs = [self.listen_socket, self.switch_socket, self.waker]
        return [x for x in socs if x]

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

        self.dbg_state = "running"

        while self.active:
            try:
                sel_in, sel_out, sel_err = \
                    select.select(self.sockets(), [], self.sockets(), 1)
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

        if not self.passive:  # Do active connection now
            self.logger.info("Attempting to connect to %s on port %s" %
                             (self.switch, str(self.port)))
            soc = self.active_connect()
            if soc:
                self.logger.info("Connected to %s", self.switch)
                self.dbg_state = "running"
                self.switch_socket = soc
                self.wakeup()
                with self.connect_cv:
                    if self.initial_hello:
                        self.message_send(hello())
                    self.connect_cv.notify() # Notify anyone waiting
            else:
                self.logger.error("Could not actively connect to switch %s",
                                  self.switch)
                self.active = False
        else:
            with self.connect_cv:
                ofutils.timed_wait(self.connect_cv, lambda: self.switch_socket,
                                   timeout=timeout)

        return self.switch_socket is not None
        
    def disconnect(self, timeout=-1):
        """
        If connected to a switch, disconnect.
        """
        if self.switch_socket:
            self.switch_socket.close()
            self.switch_socket = None
            self.switch_addr = None
            with self.packets_cv:
                self.packets = []
            with self.connect_cv:
                self.connect_cv.notifyAll()

    def wait_disconnected(self, timeout=-1):
        """
        @param timeout Block for up to timeout seconds. Pass -1 for the default.
        @return Boolean, True if disconnected
        """

        with self.connect_cv:
            ofutils.timed_wait(self.connect_cv, 
                               lambda: True if not self.switch_socket else None, 
                               timeout=timeout)
        return self.switch_socket is None
        
    def kill(self):
        """
        Force the controller thread to quit
        """
        self.active = False
        self.wakeup()
        self.join()

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

        self.wakeup()
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

    def poll(self, exp_msg=None, timeout=-1):
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

        if exp_msg is not None:
            self.logger.debug("Poll for %s" % ofp.ofp_type_map[exp_msg])
        else:
            self.logger.debug("Poll for any OF message")

        # Take the packet from the queue
        def grab():
            if len(self.packets) > 0:
                if exp_msg is None:
                    self.logger.debug("Looking for any packet")
                    (msg, pkt) = self.packets.pop(0)
                    return (msg, pkt)
                else:
                    self.logger.debug("Looking for %s" % ofp.ofp_type_map[exp_msg])
                    for i in range(len(self.packets)):
                        msg = self.packets[i][0]
                        self.logger.debug("Checking packets[%d] (%s)" % (i, ofp.ofp_type_map[msg.type]))
                        if msg.type == exp_msg:
                            (msg, pkt) = self.packets.pop(i)
                            return (msg, pkt)
            # Not found
            self.logger.debug("Packet not in queue")
            return None

        with self.packets_cv:
            ret = ofutils.timed_wait(self.packets_cv, grab, timeout=timeout)

        if ret != None:
            (msg, pkt) = ret
            self.logger.debug("Got message %s" % str(msg))
            return (msg, pkt)
        else:
            return (None, None)

    def transact(self, msg, timeout=-1):
        """
        Run a message transaction with the switch

        Send the message in msg and wait for a reply with a matching
        transaction id.  Transactions have the highest priority in
        received message handling.

        @param msg The message object to send; must not be a string
        @param timeout The timeout in seconds; if -1 use default.
        """

        if msg.xid == None:
            msg.xid = ofutils.gen_xid()

        self.logger.debug("Running transaction %d" % msg.xid)

        with self.xid_cv:
            if self.xid:
                self.logger.error("Can only run one transaction at a time")
                return (None, None)

            self.xid = msg.xid
            self.xid_response = None
            self.message_send(msg.pack())

            self.logger.debug("Waiting for transaction %d" % msg.xid)
            ofutils.timed_wait(self.xid_cv, lambda: self.xid_response, timeout=timeout)

            if self.xid_response:
                (resp, pkt) = self.xid_response
                self.xid_response = None
            else:
                (resp, pkt) = (None, None)

        if resp is None:
            self.logger.warning("No response for xid " + str(self.xid))
        return (resp, pkt)

    def message_send(self, msg):
        """
        Send the message to the switch

        @param msg A string or OpenFlow message object to be forwarded to
        the switch.
        """

        if not self.switch_socket:
            # Sending a string indicates the message is ready to go
            raise Exception("no socket")
        #@todo If not string, try to pack
        if type(msg) != type(""):
            if msg.xid == None:
                msg.xid = ofutils.gen_xid()
            outpkt = msg.pack()
        else:
            outpkt = msg

        msg_version, msg_type, msg_len, msg_xid = struct.unpack_from("!BBHL", outpkt)
        self.logger.debug("Msg out: buf len %d. hdr.type %s. hdr.len %d hdr.version %d hdr.xid %d",
                          len(outpkt),
                          ofp.ofp_type_map.get(msg_type, "unknown (%d)" % msg_type),
                          msg_len,
                          msg_version,
                          msg_xid)
        if self.switch_socket.sendall(outpkt) is not None:
            raise AssertionError("failed to send message to switch")

        return 0 # for backwards compatibility

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
        string += "  target switch   " + str(self.switch) + "\n"
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
