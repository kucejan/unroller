
import sys
import random
import progressbar
import networkx as nx

from packetstructs import *


class Topology(nx.Graph):

	def __init__(self, topox, create_hosts = False, seed = None, verbose = False, allcycles = False, directed = False):
		super(self.__class__, self).__init__(topox)

		# Check if the graph is fully connected
		if not nx.is_connected(self):
			raise nx.exception.NetworkXError("Graph is not fully connected!")

		# Mark all nodes as internal/edge and label them if note labeled
		for n in self.nodes():
			if 'edge' not in self.node[n]:
				self.node[n]['edge'] = not create_hosts

		# Add and wire up hosts
		if create_hosts:
			offset = len(self.node)
			for i in range(1, len(self.node) + 1):
				self.add_node(offset + i, edge = True, label = self.node[i]['label'] + '-' + 'host')
				self.add_edge(offset + i, i)

		# Generate node IDs
		self.prng = random.Random(seed)
		ids = self.prng.sample(xrange(2**32), len(self.node))
		for i, n in enumerate(self.nodes()):
			self.node[n]['id'] = ids[i]

		# Enable/disable verbose mode
		self.verbose = verbose

		# Enable/disable all cycles generator
		self.allcycles = allcycles

		# Enable/disable directed based cycles
		self.directed = directed

		nodes_count = len(self.nodes())
		nodes_log2 = nodes_count.bit_length()
		if self.verbose:
			print " -> nodes = {} ({} bits)".format(nodes_count, nodes_log2)

		# Get diameter
		if self.verbose:
			diameter = nx.diameter(self)
			print " -> diameter = {} hops".format(diameter)

		# Get number of cycles (too hard to find all cycles)
		if self.verbose:
			basissets = self.get_basissets()
			print " -> cycle basis = {}".format(len(basissets))
			if self.allcycles:

				def average(lst):
					suma = 0
					for item in lst:
						suma += len(item)
					return float(suma) / len(lst)

				cyclesets = self.get_cyclesets()
				print " -> cycles = {} (~ {} hops)".format(len(cyclesets), average(cyclesets))

	@staticmethod
	def load(topo_file, parser = 'zoo', create_hosts = False, seed = None, verbose = False, allcycles = False, directed = False):
		if parser == 'stanford':
			func = Topology.load_stanford
		elif parser == 'zoo':
			func = Topology.load_zoo
		elif parser == 'rocket':
			func = Topology.load_rocket
		elif parser == 'fattree':
			func = Topology.load_fattree
		else:
			return None

		return func(topo_file, create_hosts, seed, verbose, allcycles, directed)

	@staticmethod
	def load_fattree(topo_file, create_hosts = False, seed = None, verbose = False, allcycles = False, directed = False):

		K = int(topo_file)

		if verbose:
			print "Creating FatTree, K = {}".format(K)

		nodeid = 0
		topox = nx.Graph()

		# credits:
		# https://github.com/howar31/MiniNet/blob/master/topo-fat-tree.py

		# topology settings
		podNum = K                      # pods in FatTree
		coreSwitchNum = pow((K/2),2)    # core switches
		aggrSwitchNum = ((K/2)*K)       # aggregation switches
		edgeSwitchNum = ((K/2)*K)       # edge switches
		hostNum = (K*pow((K/2),2))      # hosts in K-ary FatTree

		coreSwitches = []
		aggrSwitches = []
		edgeSwitches = []

		# Core
		for core in range(0, coreSwitchNum):
			nodeid = nodeid+1
			topox.add_node(nodeid, label = "cs_"+str(core), edge = False)
			coreSwitches.append(nodeid)

		# Pod
		for pod in range(0, podNum):

			# Aggregate
			for aggr in range(0, aggrSwitchNum/podNum):
				nodeid = nodeid+1
				topox.add_node(nodeid, label = "as_"+str(pod)+"_"+str(aggr), edge = False)
				aggrSwitches.append(nodeid)
				for x in range((K/2)*aggr, (K/2)*(aggr+1)):
					topox.add_edge(nodeid, coreSwitches[x])

			# Edge
			for edge in range(0, edgeSwitchNum/podNum):
				nodeid = nodeid+1
				edgeid = nodeid
				topox.add_node(edgeid, label = "es_"+str(pod)+"_"+str(edge), edge = not create_hosts)
				edgeSwitches.append(edgeid)
				for x in range((edgeSwitchNum/podNum)*pod, ((edgeSwitchNum/podNum)*(pod+1))):
					topox.add_edge(edgeid, aggrSwitches[x])

				# Host
				if create_hosts:

					# One host per edge
					nodeid = nodeid+1
					topox.add_node(nodeid, label = "es_"+str(pod)+"_"+str(edge)+"-host", edge = True)
					topox.add_edge(nodeid, edgeid)

					# More hosts per edge
					# for x in range(0, (hostNum/podNum/(edgeSwitchNum/podNum))):
					# 	topox.add_node(nodeid, label = "es_"+str(pod)+"_"+str(edge)+"-host_"+str(x), edge = True)
					# 	topox.add_edge(nodeid, edgeSwitches[edge])

		return Topology(topox, False, seed, verbose, allcycles, directed)

	@staticmethod
	def load_rocket(topo_file, create_hosts = False, seed = None, verbose = False, allcycles = False, directed = False):

		if verbose:
			print "Loading {}".format(topo_file)

		nodes = {}
		topox = nx.Graph()

		f = open(topo_file, 'r')
		for line in f:
			tokens = line.strip().rsplit(' ', 1)
			tokens = tokens[0].split(' -> ')
			for i in [0, 1]:
				node = tokens[i]
				if node not in nodes:
					nodeid = len(nodes)+1
					nodes[node] = nodeid
					topox.add_node(nodeid, label = node)
			topox.add_edge(nodes[tokens[0]], nodes[tokens[1]])

		return Topology(topox, create_hosts, seed, verbose, allcycles, directed)

	@staticmethod
	def load_zoo(gml_file, create_hosts = False, seed = None, verbose = False, allcycles = False, directed = False):

		if verbose:
			print "Loading {}".format(gml_file)

		# Load topology from file
		topox = nx.read_gml(gml_file, label = 'id')

		# Convert to unidirected
		topox = nx.Graph(topox.to_undirected())

		# Use only the largest connected component
		topox = topox.subgraph(max(nx.connected_components(topox), key = len)).copy()

		# Relabel nodes to integeres, names available as 'name' attribute
		topox = nx.relabel.convert_node_labels_to_integers(topox, first_label = 1)

		return Topology(topox, create_hosts, seed, verbose, allcycles, directed)

	@staticmethod
	def load_stanford(topo_file, create_hosts = False, seed = None, verbose = False, allcycles = False, directed = False):

		PORT_TYPE_MULTIPLIER = 10000
		SWITCH_ID_MULTIPLIER = 100000

		port_file, topo_file = topo_file

		def load_ports(filename):
			ports = {}
			labels = {}
			f = open(filename, 'r')
			for line in f:
				if line.startswith("$"):
					tokens = line.strip().split("$")
					switch_name = tokens[1]

				if not line.startswith("$") and line != "":
					tokens = line.strip().split(":")
					port_flat = int(tokens[1])

					dpid = port_flat / SWITCH_ID_MULTIPLIER
					port = port_flat % PORT_TYPE_MULTIPLIER

					if dpid not in labels.keys():
						labels[dpid] = switch_name
					if dpid not in ports.keys():
						ports[dpid] = set()
					if port not in ports[dpid]:
						ports[dpid].add(port)
			f.close()
			return ports, labels

		def load_topology(filename):
			links = set()
			f = open(filename, 'r')
			for line in f:
				if line.startswith("link"):
					tokens = line.split('$')
					src_port_flat = int(tokens[1].strip('[]').split(', ')[0])
					dst_port_flat = int(tokens[7].strip('[]').split(', ')[0])
					links.add((src_port_flat, dst_port_flat))
			f.close()
			return links

		if verbose:
			print "Loading {}".format(port_file)
			print "Loading {}".format(topo_file)

		# Read Stanford topology files
		ports, labels = load_ports(port_file)
		links = load_topology(topo_file)

		topox = nx.Graph()

		# Create switch nodes
		for s in ports.keys():
			topox.add_node(s, label = labels[s])

		# Wire up switches
		for (src_port_flat, dst_port_flat) in links:
			src_dpid = src_port_flat / SWITCH_ID_MULTIPLIER
			dst_dpid = dst_port_flat / SWITCH_ID_MULTIPLIER
			topox.add_edge(src_dpid, dst_dpid)

		return Topology(topox, create_hosts, seed, verbose, allcycles, directed)

	def get_stpaths(self):
		if not hasattr(self, 'stpaths'):
			self.stpaths = {}
			edge_nodes = [n for n in self.nodes() if self.node[n]["edge"]]
			for u in edge_nodes:
				self.stpaths[u] = {}
				paths = nx.single_source_shortest_path(self, u)
				for v in edge_nodes:
					#if v not in paths: continue
					self.stpaths[u][v] = paths[v]
					# print u, v, paths[v]
		return self.stpaths

	def get_stpaths_routing(self):
		routing = {}
		nodes = self.nodes()
		for u in nodes:
			routing[u] = {}
			paths = nx.single_source_shortest_path(self, u)
			for v in nodes:
				if u != v:
					routing[u][v] = paths[v][1]
					# print u, v, paths[v]
		return routing

	def get_random_edge_path(self):
		edge_nodes = self.edge_nodes()
		src_node = edge_nodes[self.prng.randint(0, len(edge_nodes)-1)]
		dst_node = edge_nodes[self.prng.randint(0, len(edge_nodes)-1)]
		return self.get_stpaths()[src_node][dst_node]

	def get_basissets(self):
		if not hasattr(self, 'basissets'):

			def sortpairs(lst):
				i = iter(lst)
				first = prev = item = i.next()
				for item in i:
					if prev > item: yield item, prev
					else: yield prev, item
					prev = item
				if first > item: yield item, first
				else: yield first, item

			self.basissets = []
			for base in nx.cycle_basis(self):
				edgeset = set()

				pairs = sortpairs(base)
				for pair in pairs:
					edgeset.add(pair)

				self.basissets.append(edgeset)

		return self.basissets

	def get_cyclesets(self):
		if not hasattr(self, 'cyclesets'):
			self.cyclesets = list(set(self.find_all_cycles()))
		return self.cyclesets

	def get_random_cycleset(self):
		if self.allcycles:
			return self.get_cyclesets()[self.prng.randint(0, len(self.cyclesets)-1)]

		# credits:
		# https://stackoverflow.com/questions/12367801/finding-all-cycles-in-undirected-graphs/18388696#18388696

		basissets = self.get_basissets()
		basislen = len(basissets)

		while True:
			edgeset = set()

			basismask = random.getrandbits(basislen)
			if basismask == 0: continue
			for i, b in enumerate(bin(basismask)[:1:-1]):
				if b != '1': continue
				edgeset = edgeset ^ basissets[i]

			cycles = nx.Graph()
			cycles.add_edges_from(list(edgeset))

			comps = list(nx.connected_components(cycles))
			crand = random.randint(0, len(comps)-1)
			return comps[crand]

	def find_all_cycles(self):
		dg = self.to_directed()
		if self.directed:
			return [tuple(c) for c in nx.simple_cycles(dg)]
		return [frozenset(c) for c in nx.simple_cycles(dg)]

	def find_all_n_cycles(self, N):
		return [c for c in self.find_all_cycles() if len(c) == N]

	def edge_nodes(self):
		return [n for n in self.nodes() if self.node[n]["edge"]]

	def generate_paths(self, paths):
		Xs = []

		while len(Xs) < paths:
			path = self.get_random_edge_path()
			Xs.append(len(path))

		return Xs

	def generate_loops(self, loops, pathbased = False, B = 0):
		BL = []

		if (self.verbose):
			bar = progressbar.ProgressBar(maxval = loops,
				widgets = [progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
			print
			bar.start()

		while len(BL) < loops:
			cycle = self.get_random_cycleset()

			if pathbased:
				path = self.get_random_edge_path()

				intersect = set(path) & set(cycle)
				if len(intersect) == 0:
					continue

				for B, node in enumerate(path):
					if node in intersect:
						break

			BL.append((B, len(cycle)))
			if self.verbose:
				bar.update(len(BL))

		if self.verbose:
			bar.finish()
			print

		return BL

	def analyze_loops(self, loops, prefix = '', csv = False, pathbased = False):
		BL = self.generate_loops(loops, pathbased)

		if csv:
			for (B, L) in BL:
				print '#', B, L

		def average(lst, indexlst):
			suma = 0
			for item in lst:
				for index in indexlst:
					suma += item[index]
			return float(suma) / len(lst)

		def minimum(lst, indexlst):
			mina = sys.maxint
			for item in lst:
				newm = 0
				for index in indexlst:
					newm += item[index]
				mina = min(mina, newm)
			return mina

		def maximum(lst, indexlst):
			maxa = 0
			for item in lst:
				newm = 0
				for index in indexlst:
					newm += item[index]
				maxa = max(maxa, newm)
			return maxa

		if len(prefix):
			if isinstance(prefix, list):
				for item in prefix:
					print item,
			else:
				print prefix,

		# "File", "AVG-B", "AVG-L", "AVG-X", "MIN-B", "MIN-L", "MIN-X", "MAX-B", "MAX-L", "MAX-X", "Nodes", "Diameter", "Basis"
		print average(BL, [0]), average(BL, [1]), average(BL, [0,1]),
		print minimum(BL, [0]), minimum(BL, [1]), minimum(BL, [0,1]),
		print maximum(BL, [0]), maximum(BL, [1]), maximum(BL, [0,1]),
		print len(self.nodes()),
		print nx.diameter(self),
		print len(self.get_basissets()),
		print

	def inject_loops(self, loopnum = 0, looplen = 0, debug = False):
		if not hasattr(self, 'routing'):
			self.routing = self.get_stpaths_routing()

		# inject 1 loops
		if looplen == 1:
			if loopnum != 0:
				loops = random.sample(self.nodes(), loopnum)
			else:
				loops = self.nodes()

			for i, src in enumerate(loops, 1):
				if debug: print i, [src]
				for dst in self.nodes():
					self.routing[src][dst] = src
				#print src, src
			if debug: print

		# inject 2+ loops
		elif type(looplen) == list or looplen > 1:
			cycles = self.find_all_cycles()
			iteri = 0
			for cycle in cycles:
				if type(looplen) == list:
					if len(cycle) not in looplen: continue
				else:
					if len(cycle) != looplen: continue
				if debug: print iteri+1, cycle
				for src, new in zip(cycle, cycle[1:] + cycle[:1]):
					for dst in self.nodes():
						self.routing[src][dst] = new
					#print src, new
				iteri = iteri + 1
				if iteri == loopnum: break
			if iteri != loopnum:
				raise Exception('Specfied number (loopnum={}) of length-defined loops (looplen={}) not found!'.format(loopnum, looplen))
			if debug: print

	def process_loops(self, pstruct, traffic, debug = False):
		stpaths = self.get_stpaths()

		if not hasattr(self, 'routing'):
			self.routing = self.get_stpaths_routing()

		sump = 0
		minp = sys.maxint
		maxp = 0

		# iterate traffic
		for i, (src_node, dst_node) in enumerate(traffic):
			#print stpaths[src_node][dst_node]
			#print [self.node[node]['label'] for node in stpaths[src_node][dst_node]]

			if debug:
				length = len(stpaths[src_node][dst_node])
				sump += length
				minp = min(minp, length)
				maxp = max(maxp, length)

			context = {}
			while True:
				ret = pstruct.process_loops(self.node[src_node]['id'], context)
				if not ret:
					#print " ", "loop detected!"
					break

				if src_node == dst_node:
					#print " ", "packet delivered"
					break

				next_node = self.routing[src_node][dst_node]
				#print " ", src_node, "->", next_node, context
				#print " ", self.node[src_node]['label'], "->", self.node[next_node]['label'], context
				src_node = next_node

			pstruct.finalize(context)
			#print

		if debug:
			print "MinPath:", minp, "hops"
			print "MaxPath:", maxp, "hops"
			print "AvgPath:", float(sump) / len(traffic) if len(traffic) != 0 else "--", "hops"
			print