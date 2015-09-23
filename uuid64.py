"""

A 64-bit universally unique identifier.

time (0-47)
node (48-63)
"""

from datetime import datetime
import os
import struct
import socket
import time


EPOCH = datetime(2015, 8, 1)


def ip2int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]


def uuid64_fields(uuid64):
    """
    :type uuid64: int
    """
    return (uuid64 >> 48, uuid64 & 0xFFFF)


class UUID64(object):
    def __init__(self, node_id):
        self.node_id = node_id

    def issue(self, timestamp=None):
        """
        :param timestamp: UNIX timestamp (in seconds)
        :type timestamp: float
        """
        if timestamp:
            time_seq = int(timestamp * 1000)
        else:
            time_seq = int(time.time() * 1000)

        return int(time_seq << 16 | self.node_id)


def issue(timestamp=None):
    """
    :type timestamp: int
    """
    try:
        ipv4_addr = socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        ipv4_addr = '127.0.0.1'
    local_ip = os.environ.get('IPV4_ADDR', ipv4_addr)
    node_id = ip2int(local_ip) % (2 ** 16)
    uuid = UUID64(node_id)
    return uuid.issue(timestamp)
