#!/usr/bin/python

import sys
import string
import threading
from scapy.all import *

iface = 'h1-eth0'
dst_mac = 'aa:bb:cc:dd:ee:ff'
src_mac = get_if_hwaddr(iface)
pcapfile = 'packet.pcap'
timeout = 1

c = 1
H = 1
swids = c * H


class Unroller(Packet):
    name = "Unroller"
    fields_desc = [
        XShortField("etherType", 0),
        ShortField("hopid", 0),
        ByteField("thcnt", 0),
        FieldLenField("swids", 1, fmt='B', count_of="listids"),
        FieldListField("listids", [0], IntField("", 0), count_from = lambda pkt: pkt.swids),
    ]

bind_layers(Ether, Unroller, type=0x1111)

try:
    packet = rdpcap(pcapfile, count=1)[0]
except:
    packet = Ether()/Unroller(swids=swids, listids=swids*[0])

packet[Ether].src = src_mac
packet[Ether].dst = dst_mac
#packet.show()

answer = srp1(packet, iface=iface, timeout=timeout)
if answer is not None:
    answer.show()
    wrpcap(pcapfile, answer)
else:
    print "TIMEOUT: Receiving the response timeouted! The packet probably dropped by the switch."
    sys.exit(1)

sys.exit(0)