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
from dns import cache
from dns.zone import Zone

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
        self.rc = cache.RecordCache(ttl)
        self.ttl = ttl
        self.zone = Zone()

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



        """
        The top level algorithm has four steps:

        1. See if the answer is in local information, and if so return
            it to the client.

        2. Find the best servers to ask. FIRST FROM LIST

        3. Send them queries until one returns a response.

        4. Analyze the response, either:

                a. if the response answers the question or contains a name
                    error, cache the data as well as returning it back to
                    the client.

                b. if the response contains a better delegation to other
                    servers, cache the delegation information, and go to
                    step 2.

                c. if the response shows a CNAME and that is not the
                    answer itself, cache the CNAME, change the SNAME to the
                    canonical name in the CNAME RR and go to step 1.

                d. if the response shows a servers failure or other
                    bizarre contents, delete the server from the SLIST and
                    go back to step 3.
        """

        alias_list = []
        a_list = []
        found = False

        acs = self.getRecordsFromCache(hostname,Type.A, Class.IN) 
        if acs:
            a_list += acs
            return hostname, alias_list, a_list
            


        # Create and send query
        question = Question(Name(hostname), Type.A, Class.IN)
        header = Header(9001, 0, 1, 0, 0, 0)
        header.qr = 0  # 0 for query
        header.opcode = 0 # standad query
        header.rd = 0 # not recursive
        query = Message(header, [question])


        slist = []
        self.zone.read_master_file('dns/root.zone')

        sbelt = []
        for root in list(self.zone.records.values()):
            sbelt += [r for r in root if r.type_ == Type.A]



        while not found:
            if slist:
                rr = slist.pop()
                print(rr.to_dict())

                if rr.type_ == Type.A:
                    addr = rr.rdata.address
                    sock.sendto(query.to_bytes(), (addr, 53))
                elif rr.type_ == Type.NS:
                    fqdn = str(rr.rdata.nsdname)
                    _, _, a_rrs = self.gethostbyname(fqdn)
                    slist += a_rrs 
                    continue
                elif rr.type_ == Type.CNAME:
                    fqdn = str(rr.rdata.cname)
                    _, cname_rrs, a_rrs = self.gethostbyname(fqdn)
                    a_list += a_rrs
                    alias_list += cname_rrs
                    break

            elif sbelt:
                rr = sbelt.pop()
                print(rr.to_dict())
                addr = rr.rdata.address
                sock.sendto(query.to_bytes(), (addr, 53))
            else:
                break

            # Receive response
            data = sock.recv(512)
            response = Message.from_bytes(data)

            for answer in response.answers:                
                if answer.type_ == Type.A:
                    self.addRecordToCache(answer)
                    a_list.append(answer)
                    found = True
                if answer.type_ == Type.CNAME:
                    self.addRecordToCache(answer)
                    alias_list.append(answer)
                    slist += [answer] 
                    continue

            nss = []
            for auth in response.authorities:
                if auth.type_ == Type.NS:
                    nss.append(auth)
                    self.addRecordToCache(auth)

            a_add = {}
            for add in response.additionals:
                if add.type_ == Type.A:
                    name = str(add.name)
                    a_add[name] = add
                    self.addRecordToCache(add)

            for ns in nss:
                name = str(ns.rdata.nsdname)
                if name in a_add:
                    slist += [a_add[name]]
                else:
                    slist += [ns] 


        return hostname, alias_list, a_list

    def addRecordToCache(self, record):
        if self.caching:
            self.rc.add_record(record)

    def getRecordsFromCache(self, dname, t=Type.A, c=Class.IN):
        if self.caching:
            return self.rc.lookup(Name(dname),t,c)
        else:
            return []