#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, 'python-bloomfilter/')

import struct
import socket
import random
import itertools
import networkx as nx
import matplotlib.pyplot as plt
import pybloom as pb



def ip2int(addr):
	return struct.unpack("!I", socket.inet_aton(addr))[0]

def int2ip(addr):
	return socket.inet_ntoa(struct.pack("!I", addr))

def power2(num):
	return num != 0 and ((num & (num-1)) == 0)



class PacketStruct():

	def process_loops(self, node, context):
		return False

	def report(self):
		pass


class PacketMinSketch(PacketStruct):

	def __init__(self, size = 32, seed = 65137):
		self.size = size # in bits
		self.seed = seed
		self.log = []

	def hash_node(self, node, seed = None):
		if self.seed is not None:
			random.seed(self.seed)
		mask = random.getrandbits(32)
		return (hash(node) ^ mask) & (2**self.size-1)

	def process_loops(self, node, context):
		if "path" not in context:
			context["path"] = []

		if "minsketch" not in context:
			context["minsketch"] = None

		if "loopstart" not in context:
			try:
				context["loopstart"] = context["path"].index(node)
				context["loopsize"] = len(context["path"]) - context["loopstart"]
			except ValueError:
				pass

		node_hash = self.hash_node(node, self.seed)

		if (node_hash == context["minsketch"]):
			self.log.append([
				context["loopstart"],	# B
				context["loopsize"],	# L
				len(context["path"]),	# hops
			])

			return False

		context["path"].append(node)

		if power2(len(context["path"])) or "minsketch" not in context:
			context["minsketch"] = node_hash
		else:
			context["minsketch"] = min(node_hash, context["minsketch"])

		return True

	def report(self):
		suma = 0
		mina = float("inf")
		maxa = 0

		for record in self.log:
			B, L, hops = record
			X = B + L
			time = float(hops) / X
			mina = min(mina, time)
			maxa = max(maxa, time)
			suma += time

		print "Num:", len(self.log)
		print "Min:", mina, "X"
		print "Max:", maxa, "X"
		print "Avg:", suma / len(self.log), "X"
		print "Mem:", self.size, "bits"


class PacketBloomFilter(PacketStruct):

	def __init__(self, capacity, error_rate):
		self.capacity = capacity
		self.error_rate = error_rate
		self.log = []

	def process_loops(self, node, context):
		if "path" not in context:
			context["path"] = []

		if "bf" not in context:
			context["bf"] = pb.BloomFilter(self.capacity, self.error_rate)

		if "loopstart" not in context:
			try:
				context["loopstart"] = context["path"].index(node)
				context["loopsize"] = len(context["path"]) - context["loopstart"]
			except ValueError:
				pass

		if (node in context["bf"]):
			self.log.append([
				context["loopstart"] if "loopstart" in context else -1,	# B
				context["loopsize"] if "loopstart" in context else -1,	# L
				len(context["path"]),	# hops
			])

			return False

		context["path"].append(node)
		context["bf"].add(node)

		return True

	def report(self):
		suma = 0
		mina = float("inf")
		maxa = 0
		fpos = 0

		for record in self.log:
			B, L, hops = record
			X = B + L
			if L <= 0:
				fpos += 1
				continue
			time = float(hops) / X
			mina = min(mina, time)
			maxa = max(maxa, time)
			suma += time

		bf = pb.BloomFilter(self.capacity, self.error_rate)

		print "Num:", len(self.log)
		print "Fp%:", float(fpos) / len(self.log) * 100, "({})".format(fpos)
		print "Min:", mina, "X"
		print "Max:", maxa, "X"
		print "Avg:", suma / (len(self.log)-fpos) if len(self.log)-fpos != 0 else "--", "X"
		print "Mem:", bf.num_bits, "bits"


class Traffic:

	def __iter__(self):
		self.n = 0
		return self

	def __next__(self):
		raise StopIteration


class RandomTraffic(Traffic):

	def __init__(self, topo, packets = 1000, seed = 65137):
		self.prng = random.Random(seed)
		self.edges = topo.edge_nodes()
		self.packets = packets

	def next(self):
		if self.n < self.packets:
			self.n += 1
			return (
				self.edges[self.prng.randint(0, len(self.edges)-1)],
				self.edges[self.prng.randint(0, len(self.edges)-1)],
			)
		else:
			raise StopIteration


class RandomMappedTraffic(Traffic):

	def __init__(self, topo, data = [], seed = 65137):
		self.prng = random.Random(seed)
		self.edges = topo.edge_nodes()
		self.data = data

		self.item2node = {}
		for record in data:
			for item in record:
				if item not in self.item2node:
					self.item2node[item] = self.edges[self.prng.randint(0, len(self.edges)-1)]

	def next(self):
		if self.n < len(self.data):
			src_item, dst_item = self.data[self.n]
			self.n += 1
			return (
				self.item2node[src_item],
				self.item2node[dst_item],
			)
		else:
			raise StopIteration



class Topology(nx.Graph):

	def __init__(self, topox, create_hosts):
		super(self.__class__, self).__init__(topox)

		# Mark all nodes as internal/edge and label them
		for n in self.nodes():
			self.nodes[n]['edge'] = not create_hosts

		# Add and wire up hosts
		if create_hosts:
			offset = len(self.nodes)
			for i in range(1, len(self.nodes) + 1):
				self.add_node(offset + i, edge = True, label = self.nodes[i]['label'] + '-' + 'host')
				self.add_edge(offset + i, i)

	@staticmethod
	def load_zoo(gml_file, create_hosts = True):

		# Load topology from file
		topox = nx.read_gml(gml_file, label = 'id')

		# Convert to unidirected
		topox = nx.Graph(topox.to_undirected())

		# Use only the largest connected component
		topox = topox.subgraph(max(nx.connected_components(topox), key = len)).copy()

		# Relabel nodes to integeres, names available as 'name' attribute
		topox = nx.relabel.convert_node_labels_to_integers(topox, first_label = 1)

		return Topology(topox, create_hosts)

	@staticmethod
	def load_stanford(port_file, topo_file, create_hosts = True):

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

		return Topology(topox, create_hosts)


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

	def process_loops(self, pstruct, traffic, looplen = 0, loopnum = 0, seed = 65137):
		stpaths = self.get_stpaths()
		routing = self.get_stpaths_routing()

		# inject 1 loops
		if looplen == 1:
			if loopnum != 0:
				loops = random.sample(self.nodes(), loopnum)
			else:
				loops = self.nodes()

			for i, src in enumerate(loops, 1):
				#print i, [src]
				for dst in self.nodes():
					routing[src][dst] = src
				#print src, src
			#print

		# inject 2+ loops
		elif looplen > 1:
			cycles = self.find_all_cycles()
			iteri = 0
			for cycle in cycles:
				if len(cycle) != looplen: continue
				#print iteri+1, cycle
				for src, new in zip(cycle, cycle[1:] + cycle[:1]):
					for dst in self.nodes():
						routing[src][dst] = new
					#print src, new
				iteri = iteri + 1
				if iteri == loopnum: break
			if iteri != loopnum:
				raise Exception('Specfied number (loopnum={}) of length-defined loops (looplen={}) not found!'.format(loopnum, looplen))
			#print

		#sys.exit(1)

		# iterate traffic
		for i, (src_node, dst_node) in enumerate(traffic):
			#print stpaths[src_node][dst_node]
			#print [self.nodes[node]['label'] for node in stpaths[src_node][dst_node]]

			context = {}
			while (src_node != dst_node):
				ret = pstruct.process_loops(src_node, context)
				if not ret:
					#print " ", "loop detected!"
					break

				next_node = routing[src_node][dst_node]
				#print " ", src_node, "->", next_node, context
				#print " ", self.nodes[src_node]['label'], "->", self.nodes[next_node]['label'], context
				src_node = next_node

			#print



if __name__ == "__main__":

	#port_file = "stanford-backbone/port_map.txt"
	#topo_file = "stanford-backbone/backbone_topology.tf"
	#topo = Topology.load_stanford(port_file, topo_file)

	#gml_file = 'topology-zoo/archive/Cesnet201006.gml'
	#gml_file = 'topology-zoo/eu_nren_graphs/graphs/interconnect.gml'
	#gml_file = 'topology-zoo/eu_nren_graphs/graphs/condensed.gml'
	gml_file = 'topology-zoo/eu_nren_graphs/graphs/condensed_west_europe.gml'
	topo = Topology.load_zoo(gml_file)

	nodes_count = len(topo.nodes())
	nodes_log2 = nodes_count.bit_length()

	print "nodes = {} ({} bits)".format(nodes_count, nodes_log2)
	print

	packets = 10000
	traffic = RandomTraffic(topo, packets)

	#traffic = RandomMappedTraffic(topo, [
	#    [ip2int('192.168.1.1'), ip2int('10.1.0.1')],
	#    [ip2int('192.168.1.1'), ip2int('10.1.0.2')],
	#])

	#ms_size = nodes_log2
	#pstruct = PacketMinSketch(size=nodes_log2)

	bf_capacity = 20 # nodes_count
	bf_error_rate = 0.05
	pstruct = PacketBloomFilter(capacity=bf_capacity, error_rate=bf_error_rate)

	looplen = 10
	loopnum = 10
	topo.process_loops(pstruct, traffic, looplen=looplen, loopnum=loopnum)
	pstruct.report()
