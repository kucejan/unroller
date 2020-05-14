#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import networkx as nx
import interruptingcow as ic

from topology import *
from traffic import *

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--csv', action='store_true',
	help='full CSV output')
parser.add_argument('-v', '--verbose', action='store_true',
	help='verbose', default=False)
parser.add_argument('-s', '--seed', type=int, default=None,
	help='seed for PRNG to have consistend results')
parser.add_argument('-p', '--parser', type=str, default='zoo',
	choices=['zoo', 'rocket', 'stanford'],
	help='topology file parser')
parser.add_argument('-l', '--loops', type=int, default=1000,
	help='number of iterations')
parser.add_argument('-t', '--timeout', type=int, default=60,
	help='timeout in seconds for processing one file')
parser.add_argument('files', metavar='FILE', type=str, nargs='+',
	help='topology file')


args = parser.parse_args()

print "File", "AVG-B", "AVG-L"
if args.verbose:
	print


while len(args.files) > 0:
	topo = None

	# Test if file exists, otherwise skip it
	if not os.path.exists(args.files[0]):
		args.files.pop(0)
		continue

	try:

		# Setup a timeout for the analysis operation
		with ic.timeout(args.timeout, exception=RuntimeError):

			if args.parser == 'stanford':
				topo_file = (args.files.pop(0), args.files.pop(0))
			else:
				topo_file = args.files.pop(0)

			# Load topology from file
			topo = Topology.load(topo_file, parser=args.parser,
				seed=args.seed, verbose=args.verbose)

			if args.parser == 'stanford':
				topo_file = topo_file[-1]

			# Analyze loops
			topo.analyze_loops(args.loops, prefix=topo_file, csv=args.csv)
			if args.verbose:
				print

	except nx.exception.NetworkXError as err:
		if args.verbose:
			print err
			print "Failed to load", topo_file
		continue

	except RuntimeError as err:
		if args.verbose:
			print err
    		print "Timeouted", topo_file
    	continue



# for cycle in cycles:
# 	print sorted(cycle)

# basis = nx.cycle_basis(topo)
# print basis
# print

# cycle_edges = set()
# while len(cycle_edges) == 0:
# 	basis_ids = []
# 	basis_mask = random.getrandbits(len(basis))
# 	for i, b in enumerate(bin(basis_mask)[:1:-1]):
# 	    if b == '1': basis_ids.append(i)
# 	print basis_ids
# 	# for basis_id in basis_ids:
# 	# 	basis_nodes = basis[basis_id]
# 	# 	print zip(basis_nodes, basis_nodes[1:]+basis_nodes[:1])
# 	for basis_id in basis_ids:
# 		basis_nodes = basis[basis_id]
# 		basis_edges = zip(basis_nodes, basis_nodes[1:]+basis_nodes[:1])
# 		basis_edges = set([frozenset(edge) for edge in basis_edges])
# 		print basis_edges
# 		print cycle_edges
# 		cycle_edges = basis_edges ^ cycle_edges
# 		print cycle_edges
# 		print


# 	cycle = nx.Graph()
# 	cycle.add_edges_from(cycle_edges)
# 	if len(list(nx.connected_components(cycle))) > 1:
# 		cycle_edges.clear()

# print cycle.nodes()

# cycle_set = set()
# for edge in cycle_edges:
# 	for node in edge:
# 		cycle_set.add(node)

# print cycle_set

# for cycle in cycles:
# 	if cycle == cycle_set:
# 		print "OK"
# 		break

# print "FAIL"
