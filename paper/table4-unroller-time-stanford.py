#!/usr/bin/env python2
# -*- coding: utf-8 -*-

packets = 100000
Brange = [5]
Lrange = [20]
detections = [1]

genloops = False
genpaths = False
topoloops = True
topopaths = False
lbasedpaths = True

topoparser = 'stanford'
topofile = (
	"topologies/stanford-backbone/port_map.txt",
	"topologies/stanford-backbone/backbone_topology.tf")

enunroller = True
enbloomfilter = False

brange = [4]
cHrange = [(1,1)]
zrange = [32]
