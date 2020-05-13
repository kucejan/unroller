
import random
import networkx as nx

from packetstructs import *


class Topology(nx.Graph):

	def __init__(self, topox, create_hosts = False, seed = 65137):
		super(self.__class__, self).__init__(topox)

		# Mark all nodes as internal/edge and label them
		for n in self.nodes():
			self.node[n]['edge'] = not create_hosts

		# Add and wire up hosts
		if create_hosts:
			offset = len(self.node)
			for i in range(1, len(self.node) + 1):
				self.add_node(offset + i, edge = True, label = self.node[i]['label'] + '-' + 'host')
				self.add_edge(offset + i, i)

		# Generate node IDs
		prng = random.Random(seed)
		ids = prng.sample(xrange(2**32), len(self.node))
		for i, n in enumerate(self.nodes()):
			self.node[n]['id'] = ids[i]

	@staticmethod
	def load_zoo(gml_file, create_hosts = True, seed = 65137):

		# Load topology from file
		topox = nx.read_gml(gml_file, label = 'id')

		# Convert to unidirected
		topox = nx.Graph(topox.to_undirected())

		# Use only the largest connected component
		topox = topox.subgraph(max(nx.connected_components(topox), key = len)).copy()

		# Relabel nodes to integeres, names available as 'name' attribute
		topox = nx.relabel.convert_node_labels_to_integers(topox, first_label = 1)

		return Topology(topox, create_hosts, seed)

	@staticmethod
	def load_stanford(port_file, topo_file, create_hosts = True, seed = 65137):

		PORT_TYPE_MULTIPLIER = 10000
		SWITCH_ID_MULTIPLIER = 100000

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

		return Topology(topox, create_hosts, seed)

	def get_stpaths(self):
		shortest_paths = {}
		edge_nodes = [n for n in self.nodes() if self.node[n]["edge"]]
		for u in edge_nodes:
			shortest_paths[u] = {}
			paths = nx.single_source_shortest_path(self, u)
			for v in edge_nodes:
				shortest_paths[u][v] = paths[v]
				# print u, v, paths[v]
		return shortest_paths

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

	def get_random_cycle(self):
		cycle = []

		return cycle

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