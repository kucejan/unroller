
import sys
import math
import random

sys.path.insert(0, 'python-bloomfilter/')
import pybloom as pb


class PacketStruct(object):

	def __init__(self):
		self.csv = False
		self.detections = 1
		self.log = []

	def process_loops(self, node, context):
		return False

	def finalize(self, context):
		self.log.append([
			"loopstart" in context,	# is the path a loop?
			context["loop?"],		# detection result
			context["loopstart"] if "loopstart" in context else -1,	# B
			context["loopsize"] if "loopstart" in context else -1,	# L
			len(context["path"]),	# hops
		])

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

		sumh = 0
		minh = sys.maxint
		maxh = 0

		sumb = 0
		minb = sys.maxint
		maxb = 0

		suml = 0
		minl = sys.maxint
		maxl = 0

		loops = 0
		paths = 0

		fpos = 0

		for record in self.log:
			loop, result, B, L, hops = record
			if not loop:
				paths += 1
				if result:
					fpos += 1
				continue

			loops += 1
			time = float(hops) / (B + L)

			sumt += time
			mint = min(mint, time)
			maxt = max(maxt, time)

			sumh += hops
			minh = min(minh, hops)
			maxh = max(maxh, hops)

			sumb += B
			minb = min(minb, B)
			maxb = max(maxb, B)

			suml += L
			minl = min(minl, L)
			maxl = max(maxl, L)

		print self.pcsv("Num:"), len(self.log), nl,
		print self.pcsv("Dets:"), self.detections, nl,
		print self.pcsv("Fp%:"), float(fpos) / paths * 100 if paths != 0 else 0.0, self.pcsv("({})".format(fpos)), nl,
		print self.pcsv("MinB:"), minb if loops != 0 else "--", self.pcsv("hops"), nl,
		print self.pcsv("MaxB:"), maxb if loops != 0 else "--", self.pcsv("hops"), nl,
		print self.pcsv("AvgB:"), float(sumb) / loops if loops != 0 else "--", self.pcsv("hops"), nl,
		print self.pcsv("MinL:"), minl if loops != 0 else "--", self.pcsv("hops"), nl,
		print self.pcsv("MaxL:"), maxl if loops != 0 else "--", self.pcsv("hops"), nl,
		print self.pcsv("AvgL:"), float(suml) / loops if loops != 0 else "--", self.pcsv("hops"), nl,
		print self.pcsv("MinTime:"), mint if loops != 0 else "--", self.pcsv("X"), nl,
		print self.pcsv("MaxTime:"), maxt if loops != 0 else "--", self.pcsv("X"), nl,
		print self.pcsv("AvgTime:"), float(sumt) / loops if loops != 0 else "--", self.pcsv("X"), nl,
		print self.pcsv("MinHops:"), minh if loops != 0 else "--", self.pcsv("X"), nl,
		print self.pcsv("MaxHops:"), maxh if loops != 0 else "--", self.pcsv("X"), nl,
		print self.pcsv("AvgHops:"), float(sumh) / loops if loops != 0 else "--", self.pcsv("X"), nl,
		print


class PacketMinSketch(PacketStruct):

	def __init__(self, b = 4, c = 1, H = 1, size = 32, detections = 1, cceiling = False, seed = 65137):
		super(PacketMinSketch, self).__init__()

		self.hash = size < 32 or H > 1
		self.cceiling = cceiling
		self.detections = detections
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

	def process_loops(self, node, context):
		if "path" not in context:
			context["path"] = []

		if "loop?" not in context:
			context["loop?"] = False

		if "detection" not in context:
			context["detection"] = 0

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
			context["detection"] += 1
			if context["detection"] >= self.detections:
				context["loop?"] = True
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
		print self.pcsv("Mem:"), self.size * self.c * self.H + math.log(self.detections, 2), self.pcsv("bits"), nl,
		super(self.__class__, self).report(oneline)


class PacketBloomFilter(PacketStruct):

	def __init__(self, capacity, error_rate, detections = 1):
		super(PacketBloomFilter, self).__init__()

		self.detections = detections
		self.capacity = capacity
		self.error_rate = error_rate

	def process_loops(self, node, context):
		if "path" not in context:
			context["path"] = []

		if "loop?" not in context:
			context["loop?"] = False

		if "detection" not in context:
			context["detection"] = 0

		if "bf" not in context:
			context["bf"] = pb.BloomFilter(self.capacity, self.error_rate)

		if "loopstart" not in context:
			try:
				context["loopstart"] = context["path"].index(node)
				context["loopsize"] = len(context["path"]) - context["loopstart"]
			except ValueError:
				pass

		if (node in context["bf"]):
			context["detection"] += 1
			if context["detection"] >= self.detections:
				context["loop?"] = True
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
		print self.pcsv("Mem:"), bf.num_bits + math.log(self.detections, 2), self.pcsv("bits"), nl,
		print self.pcsv("Hashes:"), bf.num_slices, nl,
		super(self.__class__, self).report(oneline)


def simulate_loops(pstruct, loopstart, looplen, loopnum = 100, seed = 65137):
	prng = random.Random(seed)
	pathlen = loopstart + looplen
	for i in xrange(loopnum):
		path = prng.sample(xrange(2**32), pathlen)
		context = {}
		ret = True

		for src_node in path[:loopstart]:
			ret = pstruct.process_loops(src_node, context)
			if not ret: break

		offset = 0
		while ret and looplen > 0:
			src_node = path[loopstart + offset % looplen]
			ret = pstruct.process_loops(src_node, context)
			offset += 1

		pstruct.finalize(context)


def simulate_paths(pstruct, pathlen, pathnum = 100, seed = 65137):
	Topology.simulate_loops(pstruct, pathlen, 0, pathnum, seed)
