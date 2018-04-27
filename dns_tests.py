#!/usr/bin/env python3

"""Tests for your DNS resolver and server"""


import sys
import unittest
from unittest import TestCase
import unittest
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
from dns.cache import RecordCache
from dns.resource import *
import time


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
    def setUp(self):
        file = "testCache"
        with open(file, "w") as file_:
            file_.write("")
        RC = RecordCache(2, file)
        self.RC = RC
        self.r1= ResourceRecord.from_dict(
            {"type": "A", "name": "dnsIsAwesome.com", "class": "IN", "ttl": 2, "rdata": {"address": "192.123.12.23"}})
        RC.add_record(self.r1)
        RC.write_cache_file()

    def test_files(self):
        RC = self.RC
        RC.read_cache_file()
        r = RC.lookup("dnsIsAwesome.com",Type.A, Class.IN)
        r_in = False
        for i in r:
            if(i.to_dict() == self.r1.to_dict()):
                r_in = True
        self.assertEqual(True, r_in)

    def test_type_security(self):
        RC = self.RC
        RC.read_cache_file()
        r = RC.lookup("dnsIsAwesome.com", Type.CNAME, Class.IN)
        r_in = False
        for i in r:
            if (i.to_dict() == self.r1.to_dict()):
                r_in = True
        self.assertEqual(False, r_in)

    def test_TTL(self):
        r2 = ResourceRecord.from_dict({"type": "A", "name": "ttlMayBe.com", "class": "IN", "ttl": 2, "rdata": {"address": "192.123.12.23"}})
        self.RC.add_record(r2)
        rs = self.RC.lookup("ttlMayBe.com",Type.A, Class.IN)
        r2d = r2.to_dict()
        r2d.pop("ttl", None)
        ls = [j.to_dict() for j in rs]
        for l in ls:
            l.pop("ttl", None)
        self.assertIn(r2d,ls)
        time.sleep(3)
        rs = self.RC.lookup("ttlMayBe.com",Type.A, Class.IN)
        ls = [j.to_dict() for j in rs]
        for l in ls:
            l.pop("ttl", None)
        self.assertNotIn(r2d,ls)



class TestResolverCache(TestCase):
    """Resolver tests with cache enabled"""
    def setUp(self):
        self.RC = RecordCache(100,"ResolverTestCache.cache")
        self.res = Resolver(5,True,-1)

    def test_resolver_caching(self):
        hostname = "google.com"
        t = time.time()
        self.res.gethostbyname(hostname)
        d1 = time.time()-t
        t = time.time()
        self.res.gethostbyname(hostname)
        d2 = time.time()-t
        self.assertTrue(d2<d1)

    def tearDown(self):
        self.res.shutdown()



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
