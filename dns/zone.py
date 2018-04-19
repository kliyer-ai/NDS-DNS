#!/usr/bin/env python3

"""Zones of domain name space

See section 6.1.2 of RFC 1035 and section 4.2 of RFC 1034.
Instead of tree structures we simply use dictionaries from domain names to
zones or record sets.

These classes are merely a suggestion, feel free to use something else.
"""

import re
from dns.resource import ResourceRecord, RecordData, Type

class Catalog:
    """A catalog of zones"""

    def __init__(self):
        """Initialize the catalog"""
        self.zones = {"ourdomain.com" : Zone().read_master_file("master.zone")}

    def add_zone(self, name, zone):
        """Add a new zone to the catalog

        Args:
            name (str): root domain name
            zone (Zone): zone
        """
        self.zones[name] = zone


class Zone:
    """A zone in the domain name space"""

    def __init__(self):
        """Initialize the Zone """
        self.records = {}

    def add_node(self, name, record_set):
        """Add a record set to the zone

        Args:
            name (str): domain name
            record_set ([ResourceRecord]): resource records
        """
        self.records[name] = record_set

    def read_master_file(self, filename):
        """Read the zone from a master file

        See section 5 of RFC 1035.

        Args:
            filename (str): the filename of the master file
        """
        try:
            with open(filename, "r") as file_:
                for l in file_:
                    rr = l.split(";")[0]
                    if not rr:
                        continue
                    entries = re.split("[\ +]*[\\t+]*",rr)
                    name = entries[0]
                    ttl = entries[1]
                    class_ = entries[2]
                    type_ = entries[3]
                    address = entries[4]
                    rr = {"type":type_, "name":name, "class":class_, "ttl":ttl, "rdata":{"address":address}}
                    if name not in self.records:
                        self.records[name] = [ResourceRecord.from_dict(rr)]
                    else:
                        self.records[name].append(ResourceRecord.from_dict(rr))
                    print(self.records[name])
        except:
            print("could not read zone file")
        return self
