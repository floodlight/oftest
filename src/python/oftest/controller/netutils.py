#!/usr/bin/env python

"""
Network utilities for the OpenFlow controller
"""

import socket

RCV_TIMEOUT_DEFAULT = 10
HOST_DEFAULT = ''
PORT_DEFAULT = 6633
RCV_SIZE_DEFAULT = 4096

def rcv_data_from_socket(sock, timeout=RCV_TIMEOUT_DEFAULT):
    """ 
    Wait for data on a specified socket.

    Time out in (timeout)seconds.

    @param sock control socket
    @param timeout Timeout if data hasn't come in a specified seconds
    @return A pair (okay, msg) okay is boolean to indicate a packet was
    received.  msg is the message if okay is True

    """
    sock.settimeout(RCV_TIMEOUT)
    try:
        rcvmsg = sock.recv(RCV_SIZE)
        return (True, rcvmsg)
    except socket.timeout:
        return (False, None)

def open_ctrlsocket(host=HOST_DEFAULT, port=PORT_DEFAULT):
    """ Open a socket for a controller connection.

        @param host host IP address
        @param port transport port number for the test-controller
        @retval s socket
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(1)
    return s	
