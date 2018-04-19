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


class RequestHandler(Thread):
    """A handler for requests to the DNS server"""

    def __init__(self, data, addr, catalog):
        """Initialize the handler thread"""
        super().__init__()
        self.daemon = True
        self.data = data
        self.addr = addr
        self.catalog = catalog
        self.cache = RecordCache(0)
        self.resolver = Resolver(1, True, 3600)
         # ONLY ONCE

    def run(self):
        """ Run the handler thread"""
        """(1) load the local zone file to memory, (2) listen to port 53 for
        incoming queries, (3) on receiving a query it should consult its zone, and try to answer from its zone (we
        will call this zone resolution) and cache. If recursion is disabled, it should send the zone resolution result
        (match/referral/name error) back to the originator of the query and stop. Otherwise, if recursion is enabled
        but the zone resolution result is a match, it should again respond and stop. If recursion is enabled and zone
        resolution result is not a match, only then (4) it should use the DNS Resolver to answer the query. Once
        resolution is done, it should (5) send the answer back to the originator of the query."""



        """
        1. Set or clear the value of recursion available in the response
            depending on whether the name server is willing to provide
            recursive service.  If recursive service is available and
            requested via the RD bit in the query, go to step 5,
            otherwise step 2.

        2. Search the available zones for the zone which is the nearest
            ancestor to QNAME.  If such a zone is found, go to step 3,
            otherwise step 4.

        3. Start matching down, label by label, in the zone.  The
            matching process can terminate several ways:  DO LAST!!!

                a. If the whole of QNAME is matched, we have found the
                    node.

                    If the data at the node is a CNAME, and QTYPE doesn't
                    match CNAME, copy the CNAME RR into the answer section
                    of the response, change QNAME to the canonical name in
                    the CNAME RR, and go back to step 1.

                    Otherwise, copy all RRs which match QTYPE into the
                    answer section and go to step 6.

                b. If a match would take us out of the authoritative data,
                    we have a referral.  This happens when we encounter a
                    node with NS RRs marking cuts along the bottom of a
                    zone.

                    Copy the NS RRs for the subzone into the authority
                    section of the reply.  Put whatever addresses are
                    available into the additional section, using glue RRs
                    if the addresses are not available from authoritative
                    data or the cache.  Go to step 4.

                c. If at some label, a match is impossible (i.e., the
                    corresponding label does not exist), look to see if a
                    the "*" label exists.

                    If the "*" label does not exist, check whether the name
                    we are looking for is the original QNAME in the query
                    or a name we have followed due to a CNAME.  If the name
                    is original, set an authoritative name error in the
                    response and exit.  Otherwise just exit.

                    If the "*" label does exist, match RRs at that node
                    against QTYPE.  If any match, copy them into the answer
                    section, but set the owner of the RR to be QNAME, and
                    not the node with the "*" label.  Go to step 6.

        4. Start matching down in the cache.  If QNAME is found in the
            cache, copy all RRs attached to it that match QTYPE into the
            answer section.  If there was no delegation from
            authoritative data, look for the best one from the cache, and
            put it in the authority section.  Go to step 6.

        5. Using the local resolver or a copy of its algorithm (see
            resolver section of this memo) to answer the query.  Store
            the results, including any intermediate CNAMEs, in the answer
            section of the response.

        6. Using local data only, attempt to add other RRs which may be
            useful to the additional section of the query.  Exit.
                """



        mess = Message.from_bytes(self.data)
        rd = mess.header.rd
        questions = mess.questions
        

        for q in questions:
            name = q.qname
            class_ = q.qclass
            type_ = q.qtype

            zone_resolution = self.resolveZone(name, type_, class_)
            if zone_resolution:
                mess.answers += zone_resolution
                continue

            cached_rr = self.cache.lookup(name, type_, class_)
            if cached_rr:
                mess.answers += cached_rr
                continue

            if rd:
                hostname, aliaslist, ipaddrlist = self.resolver.gethostbyname(name)
                ttl = 3600
                rrs_ip = [rr = {"type":Type.A, "name":hostname, "class":class_, "ttl":ttl, "rdata":{"address":ip}} for ip in ipaddrlist]
                rrs_cname = [rr = {"type":Type.CNAME, "name":hostname, "class":class_, "ttl":ttl, "rdata":{"cname":cname}} for cname in aliaslist]
                continue

            

        # send message   


            #if zone.records[name]: # TODO: check for .
            #    mess.answers += 
            """
            if type_ == Type.A:
                r = self.resolveZone(name, type_)
                if r:
                    mess.answers.append(r)
                    continue
            elif type_ == Type.NS:
                r = self.resolveZone(name, type_)
                if r:
                    mess.answers.append(r)
                    continue
            elif type_ == Type.CNAME:
                r = self.resolveZone(name, type_)
                if r:
                    mess.answers.append(r)
                    continue
            else:
                print("Question type not supported")
            """

    def resolveZone(self,name, type_, class_):
        zoneRecords = self.catalog.zones["ourdomain.com"].records
        matches = [rr for rr in zoneRecords if rr.name == name and rr.class_ == class_]
        if not matches:
            return None
        perfectmatch = [prr for prr in matches if prr.type_ == type_]
            
            


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

    def serve(self):
        """Start serving requests"""
        sock = socket.socket("AF_INET", "SOCK_DGRAM")
        sock.bind((socket.gethostbyname(socket.gethostname()),self.port))
        while not self.done:
            data, addr = sock.recvfrom(1024)
            re = RequestHandler(data, addr, self.catalog)
            re.start()


    def shutdown(self):
        """Shut the server down"""
        self.done = True
