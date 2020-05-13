
import random


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