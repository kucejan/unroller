
# Unroller

*"Detecting Routing Loops in the Data Plane"*

## P4 implementation

Follow the instructions on https://github.com/p4lang/p4app to install `p4app` tool. Run Unroller P4 application using:

```bash
p4app run unroller.p4app
```

## Real-life topologies

Go to `topologies/topology-zoo` or `topologies/rocketfuel` to see instructions to download some real-life topologies.

## Topology Evaluator tool

Print help using:

```bash
./topology-evaluator.py --help
```

#### Examples

```bash
./topology-evaluator.py -p zoo topologies/topology-zoo/archive/*.gml
./topology-evaluator.py -p stanford topologies/stanford-backbone/port_map.txt topologies/stanford-backbone/backbone_topology.tf
./topology-evaluator.py -p rocket $(find topologies/rocketfuel/maps-n-paths/ -type d | cut -d':' -f1 | sort -u | tail -n +2 | sed 's~\(.*\)/\([0-9]*\)~\1/\2:\2/edges~g' | xargs)
./topology-evaluator.py -p fattree 4
```

## Loops Simulator tool

Edit the configuration at the beginning of `loops-simulator.py` file using your favourite text editor, e.g. `vim`.

Run the simulator using:

```bash
./loops-simulator.py
```

#### Common settings

```python

# Number of generated packets (iterations)
packets = 3000000

# Number of hops before entering the loop (list)
Brange = [5] # [0, 2, 3, 5, 7, 10]

# The length of the loop
Lrange = [20] # xrange(15, 25)

# Number of success loop detection before
# reporting it (called Th in the paper)
detections = [1] # [1, 2, 4]

# Generate loops and/or loop-free paths
#   When generating loop-free paths, the paths
#   has the length of X = B + X
genloops = False
genpaths = False

# Generate loops using a topology
topoloops = False

# Generate paths using a topology
topopaths = True

# Generate paths based on the loops length
lbasedpaths = True

# Topology parser and source file (stanford)
topoparser = 'stanford'
topofile = (
	"topologies/stanford-backbone/port_map.txt",
	"topologies/stanford-backbone/backbone_topology.tf")

# Topology parser and source file (zoo)
topoparser = 'zoo'
topofile = 'topologies/topology-zoo/UsCarrier.gml'
# topofile = 'topologies/topology-zoo/archive/Geant2012.gml'
# topofile = 'topologies/topology-zoo/archive/Bellsouth.gml'
# topofile = 'topologies/topology-zoo/AttMpls.gml'
# topofile = 'topologies/topology-zoo/archive/Cesnet201006.gml'
# topofile = 'topologies/topology-zoo/eu_nren_graphs/graphs/interconnect.gml'
# topofile = 'topologies/topology-zoo/eu_nren_graphs/graphs/condensed.gml'
# topofile = 'topologies/topology-zoo/eu_nren_graphs/graphs/condensed_west_europe.gml'

# Topology parser and source file (rocket)
topoparser = 'rocket'
topofile = 'topologies/rocketfuel/maps-n-paths/101\:101/edges'

# Topology parser and source file (fattree)
topoparser = 'fattree'
topofile = '2'
# topofile = '4'

# Enable Unroller and/or BF simulator
enunroller = False
enbloomfilter = True

```

#### Unroller specific simulator settings

```python

# b: how aggressively the resetting intervals are increased
brange = [4] # xrange(2, 5)

# (c, H) pairs, where
# c: number of chunks the phase is partitioned to
# H: number of hash functions
cHrange = [(1,1)] # [(1,1), (2,2), (4,4), (8,4), (8,8), (1,4), (4,1), (4,2), (2,4)]
# cHrange = itertools.product([1], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20])

# z: stored number of bits of the switch identifier
zrange = xrange(17, 32+1) # xrange(2, 32+1)
```

#### Bloom-filter specific simulator settings

```python

# Expected capacity of the BF (# of hops)
bf_capacity = 20

# Expected error rates of the BF (affects number of hash functions)
bf_error_rates = [0.01, 0.001, 0.0001, 0.00001]

```