#!/usr/bin/env python3

""" DNS server

This script contains the code for starting a DNS server.

project by
    Nick Stracke s4771192
    Johannes-Lucas Loewe s1013635

Note: our zone file is not called zone but ourdomain.zone to keep up with specifications!
"""


from argparse import ArgumentParser

from dns.server import Server


def run_server():
    parser = ArgumentParser(description="DNS Server")
    parser.add_argument("-c", "--caching", action="store_true",
            help="Enable caching")
    parser.add_argument("-t", "--ttl", metavar="time", type=int, default=0, 
            help="TTL value of cached entries (if > 0)")
    parser.add_argument("-p", "--port", type=int, default=5353,
            help="Port which server listens on")
    args = parser.parse_args()

    server = Server(args.port, args.caching, args.ttl)
    try:
        server.serve()
    except KeyboardInterrupt:
        server.shutdown()
        print("shutting down...")


if __name__ == "__main__":
    run_server()
