#!/usr/bin/python
from collections import Counter
import random
import math
import sys
import socket
import struct

from config import flowType


def ip2int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]


def int2ip(addr):
    return socket.inet_ntoa(struct.pack("!I", addr))
	
def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z

class FlowRadar():
	def randomizedHash(self,rng,kc, seed4mask = None): 
		if seed4mask is not None:
			random.seed(seed4mask)
		mask = random.getrandbits(64)
		self.randomizedHashRND = random.Random()
		def hashIt(x): #returns the set of counters for flow x
			self.randomizedHashRND.seed(hash(x) ^ mask)
			return self.randomizedHashRND.sample(xrange(rng), kc)
		return hashIt 
	def __init__(self,kf, kc = 4, bfSize = None , CSize = 20000, N = 1, seed4mask = None):
	# kf -- the number of hash functions in the bloom filter
	# kc -- the number of hash functions in the counting table
	# bfSize -- size of the bloom filter
	# CSize -- size of the counting table
	# N -- number of switches
		self.bfs = [set() for _ in xrange(N)] #TODO: replace with actual bloom filters
		self.CSs = [[[0,0,0] for j in xrange(CSize)] for _ in xrange(N)]
		#self.Hcs = [[self.randomizedHash(CSize) for j in xrange(kc)] for _ in xrange(N)]
		self.Hcs = [self.randomizedHash(CSize, kc, seed4mask+_) for _ in xrange(N)]
		self.kc = kc
		self.N = N
		self.CSize = CSize
		if bfSize is None:
			bfSize = (CSize/1.24) * 4 #4 bytes per item to avoid false poitives altogether
		self.bfSize = bfSize
		
	def size(self): #memory consumption per switch in bytes
		if flowType == '5-tuple':
			flowSize = 13 #src+dst ip, ports, protocol
		else:
			flowSize = 4 #srcips
		counterSize = 4 #up to 2**32~4B packets
		flowCntSize = 1 #up to 256 collisions per entry
		entrySize = flowSize + counterSize + flowCntSize
		return entrySize * self.CSize + self.bfSize
		
	def add(self, x, n): #add a packet from x to switch #n
		if x not in self.bfs[n]:
			self.bfs[n].add(x)
			for l in self.Hcs[n](x):
				self.CSs[n][l][0] = self.CSs[n][l][0] ^ x
				self.CSs[n][l][1] += 1
		for l in self.Hcs[n](x):
			self.CSs[n][l][2] += 1
			
	def singleDecode(self,n):
		singleDecoded = True
		localDecodedFlows = dict()
		while singleDecoded == True:
			singleDecoded = False
			for l in xrange(self.CSize):
				if self.CSs[n][l][1] == 1:
					x = self.CSs[n][l][0]
					freq = self.CSs[n][l][2]
					localDecodedFlows[x] = freq
					singleDecoded = True
					self.decoded = True
					#self.bfs[n].remove(x)
					for l in self.Hcs[n](x):
						self.CSs[n][l][0] = self.CSs[n][l][0] ^ x
						self.CSs[n][l][1] -= 1
						self.CSs[n][l][2] -= freq
		return localDecodedFlows
					
	def FlowDecode(self):
		res = dict()
		for n in xrange(self.N):
			res = merge_two_dicts(res, self.singleDecode(n))
		return res
			
	def NetDecode(self):
		self.decoded = True
		self.decodedFlows = dict()
		while self.decoded == True:
			self.decoded = False
			for n in xrange(self.N):
				localDecodedFlows = self.singleDecode(n) #try decoding from switch #n
				self.decodedFlows = merge_two_dicts(self.decodedFlows, localDecodedFlows)
				for x in localDecodedFlows:
					for s in set(xrange(self.N)) - set([n]):
						if x in self.bfs[s]:
							for l in self.Hcs[s](x):
								self.CSs[s][l][0] = self.CSs[s][l][0] ^ x
								self.CSs[s][l][1] -= 1
								self.CSs[s][l][2] -= localDecodedFlows[x]
				
		return self.decodedFlows
