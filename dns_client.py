#!/usr/bin/env python3

""" Simple DNS client

A simple example of a client using the DNS resolver.
"""


from argparse import ArgumentParser

from dns.resolver import Resolver
from dns.cache import RecordCache
from dns.socketWrapper import SocketWrapper


def resolve():
    """Resolve a hostname using the resolver """
    parser = ArgumentParser(description="DNS Client")
    parser.add_argument("hostname", help="hostname to resolve")
    parser.add_argument("--timeout", metavar="time", type=int, default=5,
                        help="resolver timeout")
    parser.add_argument("-c", "--caching", action="store_true",
                        help="Enable caching")
    parser.add_argument("-t", "--ttl", metavar="time", type=int, default=0,
                        help="TTL value of cached entries (if > 0)")
    args = parser.parse_args()

    s = SocketWrapper(53)
    s.start()
    rc = RecordCache(3600)
    resolver = Resolver(args.timeout, args.caching, args.ttl, s, rc)
    hostname, aliaslist, ipaddrlist = resolver.gethostbyname(args.hostname)
    s.shutdown()
    rc.write_cache_file()

    print(hostname)
    print([rr.rdata.address for rr in aliaslist])
    print([rr.rdata.address for rr in ipaddrlist])



if __name__ == "__main__":
    resolve()
