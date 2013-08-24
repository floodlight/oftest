"""
Pcap file writer
"""

import struct

PcapHeader = struct.Struct("<LHHLLLL")
PcapPktHeader = struct.Struct("<LLLL")

class PcapWriter(object):
    def __init__(self, filename):
        """
        Open a pcap file
        """
        self.stream = file(filename, 'w')

        self.stream.write(PcapHeader.pack(
            0xa1b2c3d4, # magic
            2, # major
            4, # minor
            0, # timezone offset
            0, # timezone accuracy
            65535, # snapshot length
            1 # ethernet linktype
        ))

    def write(self, data, timestamp):
        """
        Write a packet to a pcap file

        'data' should be a string containing the packet data.
        'timestamp' should be a float.
        """
        self.stream.write(PcapPktHeader.pack(
            int(timestamp), # timestamp seconds
            int((timestamp - int(timestamp)) * 10**6), # timestamp microseconds
            len(data), # truncated length
            len(data) # un-truncated length
        ))
        self.stream.write(data)

    def close(self):
        self.stream.close()
