#!/usr/bin/env python3

"""DNS Resolver

This module contains a class for resolving hostnames. You will have to implement
things in this module. This resolver will be both used by the DNS client and the
DNS server, but with a different list of servers.
"""


import socket

from dns.classes import Class
from dns.message import Message, Question, Header
from dns.name import Name
from dns.rtypes import Type


class Resolver:
    """DNS resolver"""

    def __init__(self, timeout, caching, ttl):
        """Initialize the resolver

        Args:
            caching (bool): caching is enabled if True
            ttl (int): ttl of cache entries (if > 0)
        """
        self.timeout = timeout
        self.caching = caching
        self.ttl = ttl

    def gethostbyname(self, hostname):
        """Translate a host name to IPv4 address.

        Currently this method contains an example. You will have to replace
        this example with the algorithm described in section 5.3.3 in RFC 1034.

        Args:
            hostname (str): the hostname to resolve

        Returns:
            (str, [str], [str]): (hostname, aliaslist, ipaddrlist)
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self.timeout)

        """
        .                        3600000      NS    A.ROOT-SERVERS.NET.
        A.ROOT-SERVERS.NET.      3600000      A     198.41.0.4
        A.ROOT-SERVERS.NET.      3600000      AAAA  2001:503:ba3e::2:30
        """

        # Create and send query
        question = Question(Name(hostname), Type.A, Class.IN)
        header = Header(9001, 0, 1, 0, 0, 0)
        header.qr = 0  # 0 for query
        header.opcode = 0 # standad query
        header.rd = 0 # not recursive
        query = Message(header, [question])

        aliaslist = []
        ipaddrlist = []

        stackIP = []
        stackIP.append('198.41.0.4')

        stackName = []

        found = False

        while not found:
            if stackIP:
                address = stackIP.pop()
                sock.sendto(query.to_bytes(), (address, 53))
            elif stackName:
                _, _, ips = self.gethostbyname(stackName.pop())
                stackIP += ips
                continue
            else:
                break

            # Receive response
            data = sock.recv(512)
            response = Message.from_bytes(data)
            print("New Loop")
            print(stackIP)
            print(stackName)

            for a in response.additionals:
                if a.type_ == Type.A:
                    stackIP.append(a.rdata.address)
                    print('Found A')
                if a.type_ == Type.AAAA:
                    print("Found AAAA")
            
            for a in response.authorities:
                print(type(a))
                if a.type_ == Type.NS:
                    nsdname = str(a.rdata.nsdname)
                    if nsdname not in stackName:
                        stackName.append(nsdname)
                elif a.type_ == Type.SOA:
                    print("SOA:", a.rdata[0].to_dict()) # is tuple, watch out

            # Get data

            for answer in response.answers:                
                if answer.type_ == Type.A:
                    ipaddrlist.append(answer.rdata.address)
                    found = True
                if answer.type_ == Type.CNAME:
                    aliaslist.append(hostname)
                    hostname = str(answer.rdata.cname)
                    found = True


        return hostname, aliaslist, ipaddrlist
