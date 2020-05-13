#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import math
import itertools

sys.path.insert(0, 'python-bloomfilter/')
import pybloom as pb

from packetstructs import *

#
## Common settings

# Number of generated packets (iterations)
packets = 100

# Number of hops before entering the loop (list)
Brange = [5] # [0, 2, 3, 5, 7, 10]

# The length of the loop
Lrange = [20] # xrange(15, 25)

# Number of success loop detection before
# reporting it (called Th in the paper)
detections = [1, 2, 4]

# Generate loops and/or loop-free paths
#   When generating loop-free paths, the paths
#   has the length of X = B + X
genloops = True
genpaths = False

# Enable Unroller and/or BF simulator
enunroller = True
enbloomfilter = True


#
## Unroller simulator settings

# b: how aggressively the resetting intervals are increased
brange = [4] # xrange(2, 5)

# (c, H) pairs, where
# c: number of chunks the phase is partitioned to
# H: number of hash functions
#
cHrange = [(1,1)] # [(1,1), (2,2), (4,4), (8,4), (8,8), (1,4), (4,1), (4,2), (2,4)]
# cHrange = itertools.product([1], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20])

zrange = [14] # xrange(2, 32+1)


#
## Bloomfilter simulator settings

# Expected capacity of the BF (# of hops)
bf_capacity = 20

# Expected error rates of the BF (affects number of hash functions)
bf_error_rates = [0.01] # [0.01, 0.001, 0.0001, 0.00001]
# bf_error_rates = [0.00153, 0.00194, 0.00235, 0.00292, 0.00362, 0.00391, 0.00461, 0.00558, 0.00677,
# 	0.00782, 0.00902, 0.01068, 0.01263, 0.01494, 0.01563, 0.01768, 0.02042, 0.02358, 0.02724, 0.03125,
# 	0.03463, 0.03905, 0.04403, 0.04965, 0.05599, 0.0625, 0.06785, 0.07469, 0.08223, 0.09052, 0.09965,
# 	0.1097, 0.12076, 0.125, 0.13294, 0.14287, 0.15355, 0.16502, 0.17735, 0.19061, 0.20485, 0.22016,
# 	0.23661, 0.25, 0.26047, 0.27329, 0.28675, 0.30086, 0.31567, 0.3312, 0.3475, 0.36461, 0.38255, 0.40138,
# 	0.42113, 0.44186, 0.46361, 0.48643, 0.5, 0.51037, 0.52278, 0.53549, 0.54851, 0.56184, 0.5755, 0.58949,
# 	0.60383, 0.61851, 0.63355, 0.64895, 0.66473, 0.68089, 0.69744, 0.7144, 0.73177, 0.74956, 0.76779,
# 	0.78645, 0.80558, 0.82516, 0.84522, 0.86578, 0.88682, 0.90839, 0.93047, 0.9531, 0.97627]
# bf_num_bits_pairs = [(pb.BloomFilter(bf_capacity, p).num_bits, p) for p in [(z+1)/1000000. for z in xrange(999999)]]
# bf_error_rates = [w for (i,(q,w)) in enumerate(bf_num_bits_pairs) if q < bf_num_bits_pairs[i-1][0]]


#
## Simulate Unroller structure

if enunroller:
	for dets in detections:
		for b in brange:
			for c, H in cHrange:
				for B in Brange:
					for L in Lrange:
						for z in zrange:
							pstruct = PacketMinSketch(b = b, c = c, H = H, size = z, detections = dets)
							if genloops: simulate_loops(pstruct, B, L, packets)
							if genpaths: simulate_paths(pstruct, L+B, packets)
							pstruct.csvrep()
						if len(zrange) > 1: print
					if len(Lrange) > 1: print
				if len(Brange) > 1: print
			if len(cHrange) > 1: print
		if len(brange) > 1: print
	if len(detections) > 1: print
	print


#
## Simulate BloomFilter structure

if enbloomfilter:
	for dets in detections:
		for bf_error_rate in bf_error_rates:
			for B in Brange:
				for L in Lrange:
					pstruct = PacketBloomFilter(bf_capacity, bf_error_rate, detections = dets)
					if genloops: simulate_loops(pstruct, B, L, packets)
					if genpaths: simulate_paths(pstruct, B+L, packets)
					pstruct.csvrep()
				if len(Lrange) > 1: print
			if len(Brange) > 1: print
		if len(bf_error_rates) > 1: print
	if len(detections) > 1: print
	print