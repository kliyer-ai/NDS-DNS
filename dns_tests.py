#!/usr/bin/env python3

"""Tests for your DNS resolver and server"""


import sys
import unittest
from unittest import TestCase
from argparse import ArgumentParser
from dns.resolver import Resolver
from dns.socketWrapper import SocketWrapper
import socket
from dns.server import Server
import threading
from dns.classes import Class
from dns.message import Message, Question, Header
from dns.name import Name
from dns.rtypes import Type


PORT = 5001
SERVER = "localhost"


class TestResolver(TestCase):
    """Resolver tests"""

    def test_check_query(self):
        pass
        """
        s = SocketWrapper(1234)
        s.start()
        res = Resolver(5, False, 3600, s)
        hostname, alias, ips = res.gethostbyname("nickstracke.xyz")
        s.shutdown()
        ip1 = ips[0].rdata.address
        ip2= socket.gethostbyname("nickstracke.xyz")
        self.assertEqual(ip1, ip2)
        """
        

class TestCache(TestCase):
    """Cache tests"""


class TestResolverCache(TestCase):
    """Resolver tests with cache enabled"""


class TestServer(TestCase):
    """Server tests"""

    def setUp(self):
        self.server = Server(PORT, False, 3600)
        self.s1 = threading.Thread(target=self.server.serve)
        self.s1.daemon = True
        self.s1.start()

    def tearDown(self):
        self.server.shutdown()

    def test_server_no_caching(self):
        data = self.send_query("nickstracke.xyz", PORT+1)
        
        mess = Message.from_bytes(data)
        ip1 = mess.answers[0].rdata.address
        ip2= socket.gethostbyname("nickstracke.xyz")
        self.assertEqual(ip1, ip2)

    
    def test_concurrency(self):
        s2 = threading.Thread(target=self.send_query, args=("nickstracke.xyz", PORT+2))
        s2.daemon = True
        s2.start()
        data = self.send_query("nickstracke.xyz", PORT+3)

        mess = Message.from_bytes(data)
        ip1 = mess.answers[0].rdata.address
        ip2= socket.gethostbyname("nickstracke.xyz")
        self.assertEqual(ip1, ip2)

    def test_authority(self):
        data = self.send_query("ns1.ourdomain.com", PORT+4)
        mess = Message.from_bytes(data)
        ip1 = mess.answers[0].rdata.address
        print(ip1)
        self.assertEqual(ip1, "255.255.255.255")
    

    def send_query(self, hostname, port):
        question = Question(Name(hostname), Type.A, Class.IN)
        # use port as id
        header = Header(port, 0, 1, 0, 0, 0)
        header.qr = 0  # 0 for query
        header.opcode = 0 # standad query
        header.rd = 1 #  recursive
        query = Message(header, [question])
        ip = (([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")] or [[(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) + ["no IP found"])[0]

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((ip, port))
        
        sock.sendto(query.to_bytes(), (ip, PORT))
        data = sock.recv(1024)
        sock.close()

        return data


def run_tests():
    """Run the DNS resolver and server tests"""
    parser = ArgumentParser(description="DNS Tests")
    parser.add_argument("-s", "--server", type=str, default="localhost",
                        help="the address of the server")
    parser.add_argument("-p", "--port", type=int, default=5001,
                        help="the port of the server")
    args, extra = parser.parse_known_args()
    global PORT, SERVER
    PORT = args.port
    SERVER = args.server

    # Pass the extra arguments to unittest
    sys.argv[1:] = extra

    # Start test suite
    unittest.main()


if __name__ == "__main__":
    run_tests()
