"""
Controller Interface Class

This class supports the interface to the controller.  It is 
roughly based on the controller object from OFTest.  It is 
threaded.
"""


import os
import socket
import time
from threading import Thread
from oftest.message import *
from oftest.parse import *
from oftest.ofutils import *
# For some reason, it seems select to be last (or later).
# Otherwise get an attribute error when calling select.select
import select
import logging

##@todo Find a better home for these identifiers (controller)
RCV_SIZE_DEFAULT = 32768


class ControllerInterface(Thread):
    """
    Class abstracting the interface to the controller.
    """

    def __init__(self, host='127.0.0.1', port=6633):
        Thread.__init__(self)

        self.ctrl_socket = None
        self.rcv_size = RCV_SIZE_DEFAULT
        self.socs = []

        # Counters
        self.parse_errors = 0
        self.packets_total = 0
        self.packets_handled = 0
        self.packets_discarded = 0

        # State
        self.handlers = {}
        self.keep_alive = False
        self.active = True
        self.initial_hello = True
        self.exit_on_reset = True

        # Settings
        self.host = host
        self.port = port
        self.dbg_state = "init"
        self.logger = logging.getLogger("controller")

    def _pkt_handle(self, pkt):
        """
        Check for all packet handling conditions

        Parse and verify message 
        Check if keep alive is on and message is an echo request
        Check if any registered handler wants the packet
        Discard if none of those conditions is met

        @param pkt The raw packet (string) which may contain multiple OF msgs
        """
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
            rawmsg = pkt[offset : offset + hdr.length]

            self.logger.debug("Msg in: len %d. offset %d. type %s. hdr.len %d" %
                (len(pkt), offset, ofp_type_map[hdr.type], hdr.length))
            if hdr.version != OFP_VERSION:
                self.logger.error("Version %d does not match my version %d"
                                  % (hdr.version, OFP_VERSION))
                print "Version %d does not match my version %d" % \
                    (hdr.version, OFP_VERSION)
                self.active = False
                self.switch_socket = None
                self.kill()

            msg = of_message_parse(rawmsg)
            if not msg:
                self.parse_errors += 1
                self.logger.warn("Could not parse message")
                continue

            # Check if keep alive is set; if so, respond to echo requests
            if self.keep_alive:
                if hdr.type == OFPT_ECHO_REQUEST:
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
                self.packets_discarded += 1
                self.logger.debug("Message discarded")
            else:
                self.packets_handled += 1
                self.logger.debug("Message handled by callback")

            offset += hdr.length

    def _socket_ready(self):
        try:
            pkt = self.ctrl_socket.recv(self.rcv_size)
        except:
            self.logger.warning("Error on switch read")
            return

        if len(pkt) == 0:
            self.logger.info("zero-len pkt in")
            return

        self._pkt_handle(pkt)

    def run(self):
        """
        Activity function for class

        Create connection to controller.
        Listens on socket for messages until an error (or zero len pkt)
        occurs.

        When there is a message on the socket, check for handlers; queue the
        packet if no one handles the packet.
        """

        self.dbg_state = "starting"

        # Create listen socket
        self.logger.info("Create at " + self.host + ":" + 
                 str(self.port))
        self.ctrl_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.logger.info("Connecting\n")
        self.dbg_state = "connecting"
        self.ctrl_socket.connect((self.host, self.port))
        self.dbg_state = "connected"
        self.socs = [self.ctrl_socket]
        while self.active:
            try:
                sel_in, sel_out, sel_err = \
                    select.select(self.socs, [], self.socs, 1)
            except:
                print sys.exc_info()
                self.logger.error("Select error, exiting")
                sys.exit(1)
            if s in sel_in:
                if _socket_ready():
                    self.logger.error("Error reading packet from controller")
                    self.active = False

    def message_send(self, msg):
        """
        Send the message to the switch

        @param msg A string or OpenFlow message object to be forwarded to
        the switch.

        @return -1 if error, 0 on success

        """

        if not self.switch_socket:
            # Sending a string indicates the message is ready to go
            self.logger.info("message_send: no socket")
            return -1
        #@todo If not string, try to pack
        if type(msg) != type(""):
            try:
                if msg.header.xid == 0:
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

    def __str__(self):
        string = "Controller Interface:\n"
        string += "  state           " + self.dbg_state + "\n"
        string += "  total pkts      " + str(self.packets_total) + "\n"
        string += "  handled pkts    " + str(self.packets_handled) + "\n"
        string += "  discarded pkts  " + str(self.packets_discarded) + "\n"
        string += "  parse errors    " + str(self.parse_errors) + "\n"
        string += "  host            " + str(self.host) + "\n"
        string += "  port            " + str(self.port) + "\n"
        string += "  keep_alive      " + str(self.keep_alive) + "\n"
        return string

    def show(self):
        print str(self)
