#!/usr/bin/env python3

"""A cache for resource records

This module contains a class which implements a cache for DNS resource records,
you still have to do most of the implementation. The module also provides a
class and a function for converting ResourceRecords from and to JSON strings.
It is highly recommended to use these.
"""


import json
import time
from dns.name import Name
import threading

from dns.resource import ResourceRecord


class RecordCache:
    """Cache for ResourceRecords"""
    addLock = threading.Lock()
    writeLock = threading.Lock()
    def __init__(self, ttl):
        """Initialize the RecordCache

        Args:
            ttl (int): TTL of cached entries (if > 0)
        """
        self.records = []
        self.ttl = ttl
        self.read_cache_file()

    def lookup(self, dname, type_, class_):
        print("using caching")
        """Lookup resource records in cache

        Lookup for the resource records for a domain name with a specific type
        and class.

        Args:
            dname (str): domain name
            type_ (Type): type
            class_ (Class): class
        """
        dname = Name(dname)
        rrs = [ResourceRecord.from_dict(r) for r in self.records if (time.time() - r["timestamp"]) <r["ttl"]]
        rs = [r for r in rrs if r.name == dname and r.class_ == class_ and r.type_ == type_]
        return rs

    def matchByLabel(self, dname, type_, class_):
        """
        Args:
            dname (Name): domain name
            type_ (Type): type
            class_ (Class): class
        """
        dname = Name(dname)
        while dname.labels:
            rrs = self.lookup(str(dname), type_, class_)
            if rrs:
                return rrs
            dname.labels = dname.labels[1:]
        return []


    def add_record(self, record):
        """Add a new Record to the cache

        Args:
            record (ResourceRecord): the record added to the cache
        """
        dic = record.to_dict()
        with self.addLock:
            if dic not in self.records:
                if self.ttl > 0:
                    dic["ttl"] = self.ttl
                dic["timestamp"] = time.time()
                self.records.append(dic)
        

    def read_cache_file(self):
        """Read the cache file from disk"""
        dcts = []
        try:
            with open("cache", "r") as file_:
                dcts = json.load(file_)
        except:
            print("could not read cache")
        self.records = [dct for dct in dcts if (time.time() - dct["timestamp"]) < dct["ttl"]]

    def write_cache_file(self):
        """Write the cache file to disk"""
        try:
            with self.writeLock:
                with open("cache", "w") as file_:
                    #print("file")
                    json.dump(self.records, file_, indent=2)
        except:
            print("could not write cache")
