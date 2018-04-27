#!/usr/bin/env python3

"""A recursive DNS server

This module provides a recursive DNS server. You will have to implement this
server using the algorithm described in section 4.3.2 of RFC 1034.
"""


from threading import Thread
import socket
from dns.zone import *
from dns.message import *
from dns.cache import RecordCache
from dns.resolver import Resolver
from dns.socketWrapper import SocketWrapper
from dns.resource import ResourceRecord
from dns.cache import RecordCache


class RequestHandler(Thread):
    """A handler for requests to the DNS server"""

    def __init__(self, data, addr, catalog, sock, caching, cache, ttl=0):
        """Initialize the handler thread"""
        super().__init__()
        self.daemon = True
        self.data = data
        self.addr = addr
        self.catalog = catalog
        self.cache = cache
        self.resolver = Resolver(5, caching, ttl, sock, self.cache)
        self.sock = sock

    def run(self):
        """ Run the handler thread"""
        mess = self.data
        rd = mess.header.rd
        questions = mess.questions
        

        for q in questions:
            name = q.qname
            class_ = q.qclass
            type_ = q.qtype

            zone_resolution = self.resolveZone(str(name), type_, class_)
            if zone_resolution:
                mess.additionals += zone_resolution["additionals"]
                mess.authorities += zone_resolution["authorities"]
                mess.answers += zone_resolution["answers"]

                if type_ != Type.CNAME:
                    cnames = [ rr for rr in zone_resolution["answers"] if rr.type_ == Type.CNAME ]
                    for cn in cnames:
                        questions.append(Question( cn.rdata.cname , Type.A, cn.class_))

                mess.header.aa = 1
                continue

            cached_rrs = self.cache.lookup(str(name), type_, class_)
            cached_cname = self.cache.lookup(str(name), Type.CNAME, class_)
            if cached_rrs:
                mess.answers += cached_rrs
                continue
            elif cached_cname and type_ != Type.CNAME:
                for rr in cached_cname:
                    mess.answer.append(rr)
                    questions.append(Question( rr.rdata.cname , type_, class_))
                continue
            elif not rd:
                matched = self.cache.matchByLabel(str(name), Type.NS, class_)
                mess.authorities += matched
                for m in matched:
                    glue = self.cache.lookup(str(m.rdata.nsdname), Type.A, class_)
                    mess.additionals += glue
                continue

            if rd:
                hostname, aliaslist, ipaddrlist = self.resolver.gethostbyname(str(name))
                mess.answers += aliaslist
                mess.answers += ipaddrlist
                mess.header.ra = 1            
                continue

        
        # adjust header
        mess.header.qr = 1
        mess.header.qd_count = len(mess.questions)
        mess.header.an_count = len(mess.answers)
        mess.header.ns_count = len(mess.authorities)
        mess.header.ar_count = len(mess.additionals)

        # send message   
        #self.sock.sendto(mess.to_bytes(), self.addr)
        msg = (mess, self.addr[0], self.addr[1])
        self.sock.send(msg)

        #if zone.records[name]: # TODO: check for .
        #    mess.answers += 

    def resolveZone(self, name, type_, class_):
        name = Name(name)
        root_domain = name.labels[-2:]
        root_domain = root_domain[0] + "." + root_domain[1]

        if root_domain not in self.catalog.zones:
            return {}

        zone = self.catalog.zones[root_domain]

        current_domain = name

        if str(current_domain) in zone.records:
            records = zone.records[str(current_domain)]
            rrs_a = [rr for rr in records if (rr.type_ == Type.A or rr.type_ == Type.CNAME) and rr.class_ == Class.IN]
            if rrs_a:
                return {"answers" : rrs_a, "additionals" : [], "authorities" : []}

        while True:
            if str(current_domain) in zone.records:           
                records = zone.records[str(current_domain)]

                rrs_ns = [rr for rr in records if rr.type_ == Type.NS and rr.class_ == Class.IN]
                if rrs_ns:
                    ret = {"answers" : [], "authorities" : rrs_ns, "additionals" : []}

                    for rr_ns in rrs_ns:
                        ns_name = str(rr_ns.rdata.nsdname)
                        if ns_name in zone.records:
                            ns_records = zone.records[ns_name]
                            glue = [rr for rr in ns_records if rr.type_ == Type.A and rr.class_ == Class.IN]
                            ret["additionals"] += glue

                    return ret


            current_domain.labels = current_domain.labels[1:]
            if not current_domain.labels:
                break
                

        return {}
            
    
            


class Server:
    """A recursive DNS server"""

    """
    FLAGS
    The DNS Name Server is aware of DNS flags, namely it should use its DNS Resolver only if recursion is
    enabled in the query. Moreover, if it is authoritative over the requested FQDN in the query, it should then
    send an authoritative response.
    """

    def __init__(self, port, caching, ttl):
        """Initialize the server

        Args:
            port (int): port that server is listening on
            caching (bool): server uses resolver with caching if true
            ttl (int): ttl for records (if > 0) of cache
        """
        self.caching = caching
        self.ttl = ttl
        self.port = port
        self.done = False
        self.catalog = Catalog()
        self.sock = SocketWrapper(self.port)
        self.sock.start()
        self.cache = RecordCache(self.ttl)

    def serve(self):
        """Start serving requests"""
        while not self.done:
            data = None
            while not data:
                msgs = self.sock.msgThere(-1)
                for m in msgs:
                    data,addr = m
                    re = RequestHandler(data, addr, self.catalog, self.sock, self.caching, self.cache,self.ttl)
                    re.start()


    def shutdown(self):
        """Shut the server down"""
        self.cache.write_cache_file()
        self.done = True
        self.sock.shutdown()
