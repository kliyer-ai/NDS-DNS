#!/usr/bin/env python3

"""DNS Resolver

This module contains a class for resolving hostnames. You will have to implement
things in this module. This resolver will be both used by the DNS client and the
DNS server, but with a different list of servers.
"""


import socket
import time

from dns.classes import Class
from dns.message import Message, Question, Header
from dns.name import Name
from dns.rtypes import Type
from dns.cache import RecordCache
from dns.zone import Zone
from dns.socketWrapper import SocketWrapper
import time

class Resolver:
    """DNS resolver"""

    def __init__(self, timeout, caching, ttl, sock = None,cache = None):
        """Initialize the resolver

        Args:
            caching (bool): caching is enabled if True
            ttl (int): ttl of cache entries (if > 0)
        """
        self.timeout = timeout
        self.caching = caching
        self.rc = cache
        self.ttl = ttl
        if self.rc == None:
            self.rc = RecordCache(self.ttl)
        self.zone = Zone()
        self.sock = sock
        if self.sock is None:
            self.sock = SocketWrapper(53)
            self.sock.start()

    def _make_id(self):
        gm = time.gmtime()
        mss = str(time.time()).split(".")[1][0:3] 
        gms = str(gm.tm_sec)
        id = int(gms + mss)
        return id 

    def gethostbyname(self, hostname):
        """Translate a host name to IPv4 address.

        Currently this method contains an example. You will have to replace
        this example with the algorithm described in section 5.3.3 in RFC 1034.

        Args:
            hostname (str): the hostname to resolve

        Returns:
            (str, [str], [str]): (hostname, aliaslist, ipaddrlist)
        """
        alias_list = []
        a_list = []
        slist = []        
        found = False

        acs = self.getRecordsFromCache(hostname,Type.A, Class.IN) 
        if acs:
            a_list += acs
            return hostname, alias_list, a_list

        nscs = self.matchByLabel(hostname, Type.NS, Class.IN)
        for ns in nscs:
            glue = self.getRecordsFromCache(str(ns.rdata.nsdname))
            if glue:
                slist += glue
            else:
                slist += [ns]


        id = self._make_id()

        # Create and send query
        question = Question(Name(hostname), Type.A, Class.IN)
        header = Header(id, 0, 1, 0, 0, 0)
        header.qr = 0  # 0 for query
        header.opcode = 0 # standad query
        header.rd = 0 # not recursive
        query = Message(header, [question])

        self.zone.read_master_file('dns/root.zone')

        sbelt = []
        for root in list(self.zone.records.values()):
            sbelt += [r for r in root if r.type_ == Type.A]



        while not found:
            if slist:
                rr = slist.pop()
                if rr.type_ == Type.A:
                    addr = rr.rdata.address
                    self.sock.send((query,addr, 53))
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
                addr = rr.rdata.address
                self.sock.send((query,addr, 53))
            else:
                break

            # Receive response
            data = None
            while not data:
                data = self.sock.msgThere(id)
            response,_ = data[0]
            #response = Message.from_bytes(data)

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
            return self.rc.lookup(dname,t,c)
        else:
            return []

    def matchByLabel(self, dname, type_, class_):
        if self.caching:
            return self.rc.matchByLabel(dname, type_, class_)
        else:
            return []

    def shutdown(self):
        """
        to be used only when initialized for testing
        :return:
        """
        self.sock.shutdown()