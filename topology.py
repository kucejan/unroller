
import random
import progressbar
import networkx as nx

from packetstructs import *


class Topology(nx.Graph):

	def __init__(self, topox, create_hosts = False, seed = None, verbose = False):
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

		nodes_count = len(self.nodes())
		nodes_log2 = nodes_count.bit_length()
		if self.verbose:
			print " -> nodes = {} ({} bits)".format(nodes_count, nodes_log2)

		self.cyclesets = [set(c) for c in self.find_all_cycles()]
		if self.verbose:
			print " -> cycles = {}".format(len(self.cyclesets))

	@staticmethod
	def load(topo_file, parser = 'zoo', create_hosts = True, seed = None, verbose = False):
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

		return func(topo_file, create_hosts, seed, verbose)

	@staticmethod
	def load_fattree(topo_file, create_hosts = True, seed = None, verbose = False):

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

		return Topology(topox, False, seed, verbose)

	@staticmethod
	def load_rocket(topo_file, create_hosts = True, seed = None, verbose = False):

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

		return Topology(topox, create_hosts, seed, verbose)

	@staticmethod
	def load_zoo(gml_file, create_hosts = True, seed = None, verbose = False):

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

		return Topology(topox, create_hosts, seed, verbose)

	@staticmethod
	def load_stanford(topo_file, create_hosts = True, seed = None, verbose = False):

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

		return Topology(topox, create_hosts, seed, verbose)

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

	def get_random_cycleset(self):
		return self.cyclesets[self.prng.randint(0, len(self.cyclesets)-1)]

	def find_all_cycles_old(self, source = None):
		"""forked from networkx dfs_edges function. Assumes nodes are integers, or at least
		types which work with min() and > ."""

		if source is None:
			# produce edges for all components
			nodes = self.nodes()
		else:
			# produce edges for components with source
			nodes = [source]

		# extra variables for cycle detection:
		cycle_stack = []
		output_cycles = set()

		def get_hashable_cycle(cycle):
			"""cycle as a tuple in a deterministic order."""
			m = min(cycle)
			mi = cycle.index(m)
			mi_plus_1 = mi + 1 if mi < len(cycle) - 1 else 0
			if cycle[mi-1] > cycle[mi_plus_1]:
				result = cycle[mi:] + cycle[:mi]
			else:
				result = list(reversed(cycle[:mi_plus_1])) + list(reversed(cycle[mi_plus_1:]))
			return tuple(result)

		for start in nodes:
			if start in cycle_stack:
				continue
			cycle_stack.append(start)

			stack = [(start, iter(self[start]))]
			while stack:
				parent,children = stack[-1]
				try:
					child = next(children)

					if child not in cycle_stack:
						cycle_stack.append(child)
						stack.append((child, iter(self[child])))
					else:
						i = cycle_stack.index(child)
						if i < len(cycle_stack) - 2:
						  output_cycles.add(get_hashable_cycle(cycle_stack[i:]))

				except StopIteration:
					stack.pop()
					cycle_stack.pop()

		return [list(i) for i in output_cycles]

	def find_all_n_cycles_old(self, N, source = None):
		return [c for c in self.find_all_cycles_old(source) if len(c) == N]

	def find_all_cycles(self):
		dg = self.to_directed()
		return nx.simple_cycles(dg)

	def find_all_n_cycles(self, N):
		return [c for c in self.find_all_cycles() if len(c) == N]

	def edge_nodes(self):
		return [n for n in self.nodes() if self.node[n]["edge"]]

	def generate_loops(self, loops):
		BL = []

		if (self.verbose):
			bar = progressbar.ProgressBar(maxval = loops,
				widgets = [progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
			print
			bar.start()

		while len(BL) < loops:
			cycle = self.get_random_cycleset()
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

	def analyze_loops(self, loops, prefix = '', csv = False):
		BL = self.generate_loops(loops)
		if csv:
			for (B, L) in BL:
				print '#', B, L

		def average(lst, index):
			suma = 0
			for item in lst:
				suma += item[index]
			return float(suma) / len(lst)

		if len(prefix):
			if isinstance(prefix, list):
				for item in prefix:
					print item,
			else:
				print prefix,
		print average(BL, 0), average(BL, 1)


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