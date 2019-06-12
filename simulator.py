#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, 'python-bloomfilter/')

import math
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



class PacketStruct(object):

	def __init(self):
		self.csv = False

	def process_loops(self, node, target, context):
		return False

	def pcsv(self, value):
		if not self.csv:
			return value
		return ""

	def csvrep(self):
		self.csv = True
		self.report(True)

	def report(self, oneline = False):
		nl = "," if oneline else "\n"

		sumt = 0
		mint = float("inf")
		maxt = 0

		sumb = 0
		minb = sys.maxint
		maxb = 0

		suml = 0
		minl = sys.maxint
		maxl = 0

		fpos = 0

		for record in self.log:
			B, L, hops = record
			X = B + L
			if L <= 0:
				fpos += 1
				continue

			time = float(hops) / X

			sumt += time
			mint = min(mint, time)
			maxt = max(maxt, time)

			sumb += B
			minb = min(minb, B)
			maxb = max(maxb, B)

			suml += L
			minl = min(minl, L)
			maxl = max(maxl, L)

		print self.pcsv("Num:"), len(self.log), nl,
		print self.pcsv("Fp%:"), float(fpos) / len(self.log) * 100, self.pcsv("({})".format(fpos)), nl,
		print self.pcsv("MinB:"), minb, self.pcsv("hops"), nl,
		print self.pcsv("MaxB:"), maxb, self.pcsv("hops"), nl,
		print self.pcsv("AvgB:"), float(sumb) / (len(self.log)-fpos) if len(self.log)-fpos != 0 else "--", self.pcsv("hops"), nl,
		print self.pcsv("MinL:"), minl, self.pcsv("hops"), nl,
		print self.pcsv("MaxL:"), maxl, self.pcsv("hops"), nl,
		print self.pcsv("AvgL:"), float(suml) / (len(self.log)-fpos) if len(self.log)-fpos != 0 else "--", self.pcsv("hops"), nl,
		print self.pcsv("MinTime:"), mint, self.pcsv("X"), nl,
		print self.pcsv("MaxTime:"), maxt, self.pcsv("X"), nl,
		print self.pcsv("AvgTime:"), float(sumt) / (len(self.log)-fpos) if len(self.log)-fpos != 0 else "--", self.pcsv("X"), nl,
		print


class PacketMinSketch(PacketStruct):

	def __init__(self, b = 4, c = 1, H = 1, size = 32, cceiling = False, seed = 65137):
		self.log = []
		self.hash = size < 32 or H > 1
		self.cceiling = cceiling
		self.b = b # reseting
		self.c = c # chunks

		prgn = random.Random(seed)
		self.seeds = [ prgn.getrandbits(32) for _ in range(H) ]
		self.size = size # z (in bits)
		self.H = H # number of hashes

	def hash_node(self, node, seed):
		if not self.hash: return node
		#return hash((node,seed)) & (2**self.size-1)
		prgn = random.Random(seed)
		mask = prgn.getrandbits(32)
		return (hash(node) ^ mask) & (2**self.size-1)

	def process_loops(self, node, target, context):
		if "path" not in context:
			context["path"] = []

		if "psize" not in context:
			context["psize"] = 1 # phase size
			context["csize"] = 1 # chunk size
			context["phop"] = 0  # phase hop

		if "minsketch" not in context:
			context["minsketch"] = [ None for _ in range(self.c) ]
			if self.H > 0:
				for j in range(self.c):
					context["minsketch"][j] = [ None for _ in range(self.H) ]

		if "loopstart" not in context:
			try:
				context["loopstart"] = context["path"].index(node)
				context["loopsize"] = len(context["path"]) - context["loopstart"];
			except ValueError:
				pass

		# Compute hashes
		hashes = [ self.hash_node(node, self.seeds[i]) for i in range(self.H) ]

		# Detect loops, compare node id/hashes
		loop = False
		for j in range(self.c):
			for i in range(self.H):
				if (hashes[i] == context["minsketch"][j][i]):
					loop = True
					break
			if loop: break

		# Loop detected, report it
		if loop:
			self.log.append([
				context["loopstart"] if "loopstart" in context else -1,	# B
				context["loopsize"] if "loopstart" in context else -1,	# L
				len(context["path"]),	# hops
			])

			return False

		# Add node into path
		context["path"].append(node)

		# Update sketch
		for j in range(self.c):
			lower = math.ceil(context["csize"] * j)
			upper = math.ceil(context["csize"] * (j+1))

			# Reseting id/hash
			if context["phop"] == lower:
				context["minsketch"][j] = hashes
			elif context["phop"] > lower and context["phop"] < upper:
				for i in range(self.H):
					context["minsketch"][j][i] = min(context["minsketch"][j][i], hashes[i])

		# Increment phase hop
		context["phop"]	+= 1

		# Entering new phase?
		if context["phop"] == context["psize"]:
			context["psize"] *= self.b
			context["phop"]	= 0
			if self.cceiling:
				context["csize"] = (context["psize"] + self.c - 1) // self.c
			else:
				context["csize"] = float(context["psize"]) / self.c

		return True

	def report(self, oneline = False):
		nl = "," if oneline else "\n"

		print self.__class__.__name__, nl,
		print self.pcsv("Size:"), self.size, nl,
		print self.pcsv("b:"), self.b, nl,
		print self.pcsv("c:"), self.c, nl,
		print self.pcsv("H:"), self.H, nl,
		print self.pcsv("Mem:"), self.size * self.c * self.H, self.pcsv("bits"), nl,
		super(self.__class__, self).report(oneline)


class PacketBloomFilter(PacketStruct):

	def __init__(self, capacity, error_rate):
		self.capacity = capacity
		self.error_rate = error_rate
		self.log = []

	def process_loops(self, node, target, context):
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

	def report(self, oneline = False):
		nl = "," if oneline else "\n"

		bf = pb.BloomFilter(self.capacity, self.error_rate)
		print self.__class__.__name__, nl,
		print self.pcsv("Cap:"), self.capacity, nl,
		print self.pcsv("Rate:"), self.error_rate, nl,
		print self.pcsv("Mem:"), bf.num_bits, self.pcsv("bits"), nl,
		print self.pcsv("Hashes:"), bf.num_slices, nl,
		super(self.__class__, self).report(oneline)



class Traffic:

	def __init__(self):
		self.length = 0
		__metaclass__ = TrafficLength

	def __iter__(self):
		self.n = 0
		return self

	def __next__(self):
		raise StopIteration

	def __len__(self):
		return self.length

class TrafficLength(type):

	def __len__(self):
		return self.length


class RandomTraffic(Traffic):

	def __init__(self, topo, packets = 1000, seed = 65137):
		self.prgn = random.Random(seed)
		self.edges = topo.edge_nodes()
		self.length = packets

	def next(self):
		if self.n < self.length:
			self.n += 1
			return (
				self.edges[self.prgn.randint(0, len(self.edges)-1)],
				self.edges[self.prgn.randint(0, len(self.edges)-1)],
			)
		else:
			raise StopIteration


class RandomGeneratedTraffic(Traffic):

	def __init__(self, topo, packets = 1000, seed = 65137):
		self.prgn = random.Random(seed)
		self.edges = topo.edge_nodes()
		self.length = packets
		self.packets = []

		for i in range(0, packets):
			self.packets.append((
				self.edges[self.prgn.randint(0, len(self.edges)-1)],
				self.edges[self.prgn.randint(0, len(self.edges)-1)],
			))

	def next(self):
		if self.n < len(self.packets):
			ret = self.packets[self.n]
			self.n += 1
			return ret
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

	def __init__(self, topox, create_hosts, seed = 65137):
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

		# Generate node IDs
		prng = random.Random(seed)
		ids = prng.sample(xrange(2**32), len(self.nodes))
		for i, n in enumerate(self.nodes()):
			self.nodes[n]['id'] = ids[i]


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
			#print [self.nodes[node]['label'] for node in stpaths[src_node][dst_node]]

			if debug:
				length = len(stpaths[src_node][dst_node])
				sump += length
				minp = min(minp, length)
				maxp = max(maxp, length)

			context = {}
			while True:
				ret = pstruct.process_loops(self.nodes[src_node]['id'], self.nodes[dst_node]['id'], context)
				if not ret:
					#print " ", "loop detected!"
					break

				if src_node == dst_node:
					#print " ", "packet delivered"
					break

				next_node = self.routing[src_node][dst_node]
				#print " ", src_node, "->", next_node, context
				#print " ", self.nodes[src_node]['label'], "->", self.nodes[next_node]['label'], context
				src_node = next_node

			#print

		if debug:
			print "MinPath:", minp, "hops"
			print "MaxPath:", maxp, "hops"
			print "AvgPath:", float(sump) / len(traffic) if len(traffic) != 0 else "--", "hops"
			print


	@staticmethod
	def simulate_loops(pstruct, loopstart, looplen, loopnum = 100, seed = 65137):
		prng = random.Random(seed)
		pathlen = loopstart + looplen
		for i in xrange(loopnum):
			path = prng.sample(xrange(2**32), pathlen)
			context = {}
			ret = True

			for src_node in path[:loopstart]:
				ret = pstruct.process_loops(src_node, path[-1], context)
				if not ret: break

			offset = 0
			while ret and looplen > 0:
				src_node = path[loopstart + offset % looplen]
				ret = pstruct.process_loops(src_node, path[-1], context)
				offset += 1


	@staticmethod
	def simulate_paths(pstruct, pathlen, pathnum = 100, seed = 65137):
		Topology.simulate_loops(pstruct, pathlen, 0, pathnum, seed)


if __name__ == "__main__":

	#port_file = "stanford-backbone/port_map.txt"
	#topo_file = "stanford-backbone/backbone_topology.tf"
	#topo = Topology.load_stanford(port_file, topo_file)

	#gml_file = 'topology-zoo/archive/Cesnet201006.gml'
	#gml_file = 'topology-zoo/eu_nren_graphs/graphs/interconnect.gml'
	#gml_file = 'topology-zoo/eu_nren_graphs/graphs/condensed.gml'
	#gml_file = 'topology-zoo/eu_nren_graphs/graphs/condensed_west_europe.gml'
	#topo = Topology.load_zoo(gml_file)

	#nodes_count = len(topo.nodes())
	#nodes_log2 = nodes_count.bit_length()

	#print "nodes = {} ({} bits)".format(nodes_count, nodes_log2)
	#print

	#loopnum = 30
	#looplen = range(3, 20) # 10
	#topo.inject_loops(loopnum, looplen)

	#for i in range(37, 38):
	#	print i,
	#	topo.inject_loops(100, i, True)

	#sys.exit(1)

	#packets = 10000
	#traffic = RandomGeneratedTraffic(topo, packets)

	#traffic = RandomMappedTraffic(topo, [
	#    [ip2int('192.168.1.1'), ip2int('10.1.0.1')],
	#    [ip2int('192.168.1.1'), ip2int('10.1.0.2')],
	#])

	#packets = 10000

	# Brange = [5] # [0, 2, 3, 5, 7, 10]
	# Lrange = [20] # xrange(23, 32)
	# bf_capacity = 32 # nodes_count
	# bf_error_rates = [0.01, 0.001, 0.0001, 0.00001]

	# for bf_error_rate in bf_error_rates:
	#  	for B in Brange:
	#  		for l in Lrange:
	#  			pstruct = PacketBloomFilter(bf_capacity, bf_error_rate)
	#  			Topology.simulate_loops(pstruct, B, l, packets / 2)
	#  			Topology.simulate_paths(pstruct, l, packets / 2)
	#  			pstruct.csvrep()
	#  		print

	# sys.exit(1)

	# topo.process_loops(pstruct, traffic)
	# pstruct.report(oneline)
	# print

	packets = 5000

	brange = [4] # xrange(2, 5)
	Brange = [5] # [0, 2, 3, 5, 7, 10]
	#cHrange = [(1,1)]
	cHrange = itertools.product(range(1, 24), [2]) # [(1,1),(2,1),(2,2),(4,4),(8,4),(8,8)] # [(1, 4), (4, 1), (2, 2), (4, 2), (2, 4), (4, 4)] #  [(1,1)]
	#cHrange = itertools.product([1], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20])
	Lrange = [20] #xrange(3, 32)
	zrange = [20] #[32] #xrange(15,32+1)

	for b in brange:
		for c, H in cHrange:
			for B in Brange:
				for L in Lrange:
					for z in zrange:
						pstruct = PacketMinSketch(b = b, c = c, H = H, size = z)
						Topology.simulate_loops(pstruct, B, L, packets)
						Topology.simulate_paths(pstruct, L, packets)
						pstruct.csvrep()

	# sys.exit(1)

	# ms_size = nodes_log2
	# ms_counts = range(1, 13+1)
	# for ms_count in ms_counts:
	# 	pstruct = PacketMinSketch(size=nodes_log2, count=ms_count)
	# 	topo.process_loops(pstruct, traffic)
	# 	pstruct.report(oneline)
	# print
