#!/usr/bin/env python2
# -*- coding: utf-8 -*-

packets = 3000000
Brange = [5]
Lrange = [20]
detections = [1]

genloops = False
genpaths = False
topoloops = False
topopaths = True
lbasedpaths = True

topoparser = 'stanford'
topofile = (
	"topologies/stanford-backbone/port_map.txt",
	"topologies/stanford-backbone/backbone_topology.tf")

enunroller = False
enbloomfilter = True

brange = [4]
cHrange = [(1,1)]
zrange = xrange(32,-1,-1)

bf_capacity = 14
bf_error_rates = []
