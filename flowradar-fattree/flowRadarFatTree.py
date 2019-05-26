#!/usr/bin/python
from collections import Counter
import random
import math
import sys
import socket
import struct
import copy
import os

from HyperLogLog import HyperLogLogSketch
from flowRadar import FlowRadar
from flowRadar import flowType

def ip2int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]


def int2ip(addr):
    return socket.inet_ntoa(struct.pack("!I", addr))

def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z

class FRFatTree():
	def __init__(self, CSize, seed4mask = 65137, kc = 3, k=8):
		self.seed = seed4mask
		self.k = k
		self.kc = kc
		self.CSize = CSize
	def process(self, data):
		FatTreeK = self.k
		print 'FatTreeK = ', FatTreeK
		nrCoreSwitches = FatTreeK
		nrPods = FatTreeK
		nrAggrSwitchesPerPod = FatTreeK/2
		nrAggrSwitches = nrPods*nrAggrSwitchesPerPod
		nrEdgeSwitchesPerPod = FatTreeK/2
		nrEdgeSwitches = nrPods*nrEdgeSwitchesPerPod

		nrOverallSwitches = nrCoreSwitches + nrAggrSwitches + nrEdgeSwitches
		#switches i*nrEdgeSwitchesPerPod+(0,...,nrEdgeSwitchesPerPod-1) are in pod i
		#switches i*nrAggrSwitchesPerPod+(0,...,nrAggrSwitchesPerPod-1) + nrEdgeSwitches are in pod i
		#switches (0,...,nrCoreSwitches-1) + nrEdgeSwitches + nrAggrSwitches are the core switches
		routing = dict()
		routingPRNG = random.Random(self.seed)

		counts = dict(Counter(data))
		for ip in counts:
			srcEdgeSwitch = routingPRNG.randint(0,nrEdgeSwitches - 1)
			dstEdgeSwitch = routingPRNG.randint(0,nrEdgeSwitches - 1)
			if srcEdgeSwitch == dstEdgeSwitch: #resolved in edge switch
				routing[ip] = frozenset([srcEdgeSwitch])
			else:
				srcPod = srcEdgeSwitch / nrEdgeSwitchesPerPod
				dstPod = dstEdgeSwitch / nrEdgeSwitchesPerPod
				if srcPod == dstPod: #same pod
					aggSwitch = routingPRNG.randint(0,nrEdgeSwitchesPerPod - 1)
					aggSwitchNumber = srcPod*nrAggrSwitchesPerPod + nrEdgeSwitches + aggSwitch
					routing[ip] = frozenset([srcEdgeSwitch, aggSwitchNumber, dstEdgeSwitch])
					#routing[ip] = frozenset([srcEdgeSwitch, aggSwitchNumber])
				else:
					srcAggSwitch = routingPRNG.randint(0,nrEdgeSwitchesPerPod - 1)
					srcAggSwitchNumber = srcPod*nrAggrSwitchesPerPod + nrEdgeSwitches + srcAggSwitch
					dstAggSwitch = routingPRNG.randint(0,nrEdgeSwitchesPerPod - 1)
					dstAggSwitchNumber = dstPod*nrAggrSwitchesPerPod + nrEdgeSwitches + dstAggSwitch
					coreSwitch = routingPRNG.randint(0,nrCoreSwitches - 1) # PROC NE POLOVINA?
					coreSwitchNumber = coreSwitch + nrEdgeSwitches + nrAggrSwitches
					routing[ip] = frozenset([srcEdgeSwitch, srcAggSwitchNumber, coreSwitchNumber, dstAggSwitchNumber, dstEdgeSwitch])
					#routing[ip] = frozenset([srcEdgeSwitch, srcAggSwitchNumber, coreSwitchNumber, dstAggSwitchNumber])

		self.FR = FlowRadar(-1, self.kc, None, self.CSize,nrOverallSwitches,self.seed)
		#print len(set(data)), len(routing)
		for i,ip in enumerate(data):
			for n in routing[ip]:
				self.FR.add(ip,n)
			if (i % 10000) == 0:
				print i
	def netDecode(self):
		FRCopy = copy.deepcopy(self.FR)
		return FRCopy.NetDecode()

	def flowDecode(self):
		FRCopy = copy.deepcopy(self.FR)
		return FRCopy.FlowDecode()

class FREdgeOnly():
	def __init__(self, CSize, seed4mask = 65137, kc = 3, k=8):
		self.seed = seed4mask
		self.k = k
		self.kc = kc
		self.CSize = CSize
	def process(self, data):
		FatTreeK = self.k
		nrCoreSwitches = FatTreeK
		nrPods = FatTreeK
		nrAggrSwitchesPerPod = FatTreeK/2
		nrAggrSwitches = nrPods*nrAggrSwitchesPerPod
		nrEdgeSwitchesPerPod = FatTreeK/2
		nrEdgeSwitches = nrPods*nrEdgeSwitchesPerPod

		nrOverallSwitches = nrEdgeSwitches
		#switches i*nrEdgeSwitchesPerPod+(0,...,nrEdgeSwitchesPerPod-1) are in pod i
		#switches i*nrAggrSwitchesPerPod+(0,...,nrAggrSwitchesPerPod-1) + nrEdgeSwitches are in pod i
		#switches (0,...,nrCoreSwitches-1) + nrEdgeSwitches + nrAggrSwitches are the core switches
		routing = dict()
		routingPRNG = random.Random(self.seed)

		counts = dict(Counter(data))
		for ip in counts:
			srcEdgeSwitch = routingPRNG.randint(0,nrEdgeSwitches - 1)
			routing[ip] = frozenset([srcEdgeSwitch])

		self.FR = FlowRadar(-1, self.kc, None, self.CSize,nrOverallSwitches,self.seed)
		#print len(set(data)), len(routing)
		for i,ip in enumerate(data):
			for n in routing[ip]:
				self.FR.add(ip,n)
			if (i % 10000) == 0:
				print i
	def netDecode(self):
		FRCopy = copy.deepcopy(self.FR)
		return FRCopy.NetDecode()

	def flowDecode(self):
		FRCopy = copy.deepcopy(self.FR)
		return FRCopy.FlowDecode()

#NrPackets = 2**20
#kc = 3
#CSize = 20000
#FatTreeK = 8
#
#if (len(sys.argv) > 1):
#	NrPackets = 2**int(sys.argv[1])
#if (len(sys.argv) > 2):
#	kc = int(sys.argv[2])
#if (len(sys.argv) > 3):
#	CSize = int(sys.argv[3])
#outFile = None
#if (len(sys.argv) > 4):
#	if sys.argv[4] != '0':
#		outFile = sys.argv[4]
#
#seedVal = 156168
#if (len(sys.argv) > 5):
#	seedVal = int(sys.argv[5])
#
#if (len(sys.argv) > 6):
#	FatTreeK = int(sys.argv[6])
#
#
#FR = FlowRadar(-1, kc, None, CSize,1,seedVal)
#if False:
#	FR = ipRadar(-1, 3, None, 5,3,seedVal)
#	FR.add(7,0)
#	FR.add(7,1)
#	FR.add(7,0)
#	FR.add(7,1)
#	FR.add(8,0)
#	FR.add(6,0)
#	FR.add(6,2)
#	#FR.add(8,0)
#	#FR.add(9,0)
#	#FR.add(7,0)
#	#FR.add(0,0)
#	#print FR.CSs
#	#print FR.NetDecode()
#	totalDecode = dict()
#	for n in xrange(3):
#		totalDecode = merge_two_dicts(totalDecode, FR.singleDecode(n))
#	print totalDecode
#	exit()
##print FR.size(), FR.bfSize
##exit()
#dbg = False
#if dbg:
#	NrPackets = 100000
#
#
##flowType = 'srcips'
#
#if flowType == 'srcips':
#	if os.name == 'nt':
#		with open(r'C:\Users\sran\Dropbox\Sliding HHH\related papers\shared_vm\WindowHHHsrc\trace') as myfile:
#			head = [ip2int(next(myfile).split('\t')[0].replace(' ','.')) for x in xrange(NrPackets)]
#	else:
#		with open(r'/home/sran/tshark/NY2018/head.srcips') as myfile:
#			head = [ip2int(next(myfile).split('\t')[0].replace(' ','.')) for x in xrange(NrPackets)]
#elif flowType == '5-tuple':
#	if os.name == 'nt':
#		with open(r'C:\Users\sran\Dropbox\RoutingOblivious\head.5tuples.short') as myfile:
#			head = [hash(next(myfile)) for x in xrange(NrPackets)]
#	else:
#		with open(r'/home/sran/tshark/NY2018/head.5tuples') as myfile:
#			head = [hash(next(myfile)) for x in xrange(NrPackets)]
#
#data = head
#counts = dict(Counter(data))
#
#nrCoreSwitches = FatTreeK
#nrPods = FatTreeK
#nrAggrSwitchesPerPod = FatTreeK/2
#nrAggrSwitches = nrPods*nrAggrSwitchesPerPod
#nrEdgeSwitchesPerPod = FatTreeK/2
#nrEdgeSwitches = nrPods*nrEdgeSwitchesPerPod
#
#nrOverallSwitches = nrCoreSwitches + nrAggrSwitches + nrEdgeSwitches
##switches i*nrEdgeSwitchesPerPod+(0,...,nrEdgeSwitchesPerPod-1) are in pod i
##switches i*nrAggrSwitchesPerPod+(0,...,nrAggrSwitchesPerPod-1) + nrEdgeSwitches are in pod i
##switches (0,...,nrCoreSwitches-1) + nrEdgeSwitches + nrAggrSwitches are the core switches
#routing = dict()
#routingPRNG = random.Random(68513)
#for ip in counts:
#	srcEdgeSwitch = routingPRNG.randint(0,nrEdgeSwitches - 1)
#	dstEdgeSwitch = routingPRNG.randint(0,nrEdgeSwitches - 1)
#	if srcEdgeSwitch == dstEdgeSwitch: #resolved in edge switch
#		routing[ip] = frozenset([srcEdgeSwitch])
#	else:
#		srcPod = srcEdgeSwitch / nrEdgeSwitchesPerPod
#		dstPod = dstEdgeSwitch / nrEdgeSwitchesPerPod
#		if srcPod == dstPod: #same pod
#			aggSwitch = routingPRNG.randint(0,nrEdgeSwitchesPerPod - 1)
#			aggSwitchNumber = srcPod*nrAggrSwitchesPerPod + nrEdgeSwitches + aggSwitch
#			routing[ip] = frozenset([srcEdgeSwitch, aggSwitchNumber, dstEdgeSwitch])
#		else:
#			srcAggSwitch = routingPRNG.randint(0,nrEdgeSwitchesPerPod - 1)
#			srcAggSwitchNumber = srcPod*nrAggrSwitchesPerPod + nrEdgeSwitches + srcAggSwitch
#			dstAggSwitch = routingPRNG.randint(0,nrEdgeSwitchesPerPod - 1)
#			dstAggSwitchNumber = dstPod*nrAggrSwitchesPerPod + nrEdgeSwitches + dstAggSwitch
#			coreSwitch = routingPRNG.randint(0,nrCoreSwitches - 1)
#			coreSwitchNumber = coreSwitch + nrEdgeSwitches + nrAggrSwitches
#			routing[ip] = frozenset([srcEdgeSwitch, srcAggSwitchNumber, coreSwitchNumber, dstAggSwitchNumber, dstEdgeSwitch])
#
##print dict(Counter([len(x) for x in routing.values()]))
##exit()
#
#FR = FlowRadar(-1, kc, None, CSize,nrOverallSwitches,seedVal)
#for i,ip in enumerate(data):
#	for n in routing[ip]:
#		FR.add(ip,n)
#	if (i % 10000) == 0:
#		print i
#		sys.stdout.flush()
#	#if dbg:
#	#	print ip
#
#
#FRCopy = copy.deepcopy(FR)
#
#NETdecodedips = FR.NetDecode()
#if dbg:
#	print len(counts)#, counts
#	print len(NETdecodedips)#, decodedips
#
#NETSSE = 0
#for x in counts:
#	err = NETdecodedips.get(x,0) - counts[x]
#	NETSSE += err**2
#NETMSE = NETSSE / float(len(counts))
#NETRMSE = NETMSE ** 0.5
#
#SINGLEdecodedips = FRCopy.FlowDecode()
#if dbg:
#	print len(counts)#, counts
#	print len(SINGLEdecodedips)#, decodedips
#
#SINGLESSE = 0
#for x in counts:
#	err = SINGLEdecodedips.get(x,0) - counts[x]
#	SINGLESSE += err**2
#SINGLEMSE = SINGLESSE / float(len(counts))
#SINGLERMSE = SINGLEMSE ** 0.5
#
#if outFile is not None:
#	sys.stdout = open(outFile, "w+")
#print int(FR.size()), NETRMSE, SINGLERMSE
#sys.stdout.flush()
#