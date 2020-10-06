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
	help='full CSV output', default=False)
parser.add_argument('-a', '--allcycles', action='store_true',
	help='use all cycles generator', default=False)
parser.add_argument('-H', '--hosts', action='store_true',
	help='create hosts in the topology', default=False)
parser.add_argument('-P', '--pathbased', action='store_true',
	help='use path-based loops', default=False)
parser.add_argument('-d', '--directed', action='store_true',
	help='use directed based cycles', default=False)
parser.add_argument('-v', '--verbose', action='store_true',
	help='verbose', default=False)
parser.add_argument('-s', '--seed', type=int, default=None,
	help='seed for PRNG to have consistend results')
parser.add_argument('-p', '--parser', type=str, default='zoo',
	choices=['zoo', 'rocket', 'stanford', 'fattree'],
	help='topology file / arguments parser')
parser.add_argument('-l', '--loops', type=int, default=1000,
	help='number of iterations')
parser.add_argument('-t', '--timeout', type=int, default=60,
	help='timeout in seconds for processing one file')
parser.add_argument('files', metavar='FILEorARG', type=str, nargs='+',
	help='topology file / argument')


args = parser.parse_args()

if len(args.files) == 0:
	parser.print_help()
	sys.exit(1)

print "File", "AVG-B", "AVG-L", "AVG-X", "MIN-B", "MIN-L", "MIN-X", "MAX-B", "MAX-L", "MAX-X", "Nodes", "Diameter", "Basis"
if args.verbose:
	print


while len(args.files) > 0:
	topo = None

	# Test if file exists, otherwise skip it
	topo_file = args.files.pop(0)
	if args.parser != 'fattree' and not os.path.exists(topo_file):
		print "No file", topo_file
		continue

	try:

		# Setup a timeout for the analysis operation
		with ic.timeout(args.timeout, exception=RuntimeError):

			if args.parser == 'stanford':
				topo_file = (topo_file, args.files.pop(0))

			# Load topology from file
			topo = Topology.load(topo_file, parser=args.parser, seed=args.seed, create_hosts=args.hosts,
				verbose=args.verbose, allcycles=args.allcycles, directed=args.directed)

			if args.parser == 'stanford':
				topo_file = topo_file[-1]

			# Analyze loops
			topo.analyze_loops(args.loops, prefix=topo_file, csv=args.csv, pathbased=args.pathbased)
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