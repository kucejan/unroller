
# Unroller

**Detecting Routing Loops in the Data Plane**: _Jan Kučera (CESNET); Ran Ben Basat (Harvard University); Mário Kuka (CESNET); Gianni Antichi (Queen Mary University of London); Minlan Yu and Michael Mitzenmacher (Harvard University)._<br/>
**CoNEXT '20: Proceedings of the 16th International Conference on emerging Networking EXperiments and Technologies.**

* Paper: https://dl.acm.org/doi/pdf/10.1145/3386367.3431303
* Slides: https://drive.google.com/file/d/1wbyt6jkqUYKoe9sPMg1GQjySGVYwqJbe/view?usp=sharing


## P4 implementation

Follow the instructions on https://github.com/p4lang/p4app to install `p4app` tool. Run Unroller P4 application using:

```bash
p4app run unroller.p4app
```

It runs an Unroller detection of the loop shown in Figure 1 of the original paper, i.e., a generated packet visits a single switch before the loop (B = 1) and then enters the loop compound of four switches (L = 4). The switches have IDs 1, 6, 3, 2 and 7. The P4 code implements the Unroller algorithm using b = 4 and using a single switch ID stored inside the packet header (c = H = 1). The P4 application simulation outputs Unroller packet header after each of the hop on its path in the loop, for example:

```
###[ Unroller ]###
     etherType = 0x0
     hopid     = 5
     thcnt     = 0
     swids     = 1
     listids   = [3206565426]
```

In the Unroller header, we can see the number of currently visited hops (hopid), the current value of the threshold counter (thcnt), the number of stored switch IDs (swids) and a list of stored switch hashes (listids). For this specific example of the loop, after 11 hops, at switch with ID = 3, the loop is detected. The switch generates a digest message for the controller. The P4 app environment simulates the controller, outputs the digest and also prints a message, that the packet has been dropped by that switch.

```
LOOP DETECTED: digest received, see details:
switch_id: 0, cxt_id: 0, list_id: 1, buffer_id: 0, num_samples: 1
	timestamp: 3584898, swid: 0x00000003, hopid: 11

Received 0 packets, got 0 answers, remaining 1 packets
TIMEOUT: Receiving the response timeouted! The packet dropped by the switch.
```

In the report, we can see current time of the loop detection (timestamp), ID of the switch where the loop has been detected (swid) and the number of hops it takes to detect the loop (hopid).

The environment also enables to set the loop or algorithm parameters, e.g., B hops before entering the loop, L hops of the loop, IDs of involved switches or the detection threshold (Th). Go to `unroller.p4app/` to see further details.

## Python routing loops simulator

### Required packages

Install all required packages using the following commands:

```bash
sudo apt install build-essential python2 python2-dev
curl https://bootstrap.pypa.io/get-pip.py --output get-pip.py
sudo python2 get-pip.py
sudo pip2 install -r requirements.txt
```

### Real-life topologies

Go to `topologies/topology-zoo` or `topologies/rocketfuel` to see instructions to download some real-life topologies.

### Topology Evaluator tool

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

### Loops Simulator tool

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

#### Loading the configuration from a file

You can also save your configuration from the beginning of `loops-simulator.py` into a separate .py file and run the simulator loading the configuration, e.g., using:

```bash
./loops-simulator.py paper/table4-bloomfilter-stanford.py
```

The evaluation of the default number of runs (3M) for all the example configurations we used in the paper can be very time consuming. To override the number of runs of the configuration you can specify `-r RUNS` parameter, e.g., using:

```bash
./loops-simulator.py -r 10000 paper/table4-bloomfilter-stanford.py
```

## How to reproduce paper results?

To reproduce the results presented in the paper we prepared a set of commands which enables to rerun our loop simulator with the same configuration we used.

#### Table 4: Comparing Unroller to state-of-the-art solutions

To get the basic information about the topologies, e.g., number of nodes or diameter run:

```shell
./topology-evaluator.py -p stanford topologies/stanford-backbone/port_map.txt topologies/stanford-backbone/backbone_topology.tf
./topology-evaluator.py -p zoo topologies/topology-zoo/Bellsouth.gml
./topology-evaluator.py -p zoo topologies/topology-zoo/Geant2012.gml
./topology-evaluator.py -p zoo topologies/topology-zoo/AttMpls.gml
./topology-evaluator.py -p zoo topologies/topology-zoo/UsCarrier.gml
./topology-evaluator.py -p fattree 4
```

To get the expected memory consumption (number of bits needed) for detection of loops using Bloom filter or Unroller on the specific topology run:

```shell
./loops-simulator.py paper/table4-bloomfilter-bits-[topology].py
./loops-simulator.py paper/table4-unroller-bits-[topology].py
```

For example, to simulate Unroller on Stanford topology run:

```
./loops-simulator.py paper/table4-unroller-bits-stanford.py
```

Each line of the output for every topology represents 3M runs of the simulator (generated paths/loops) for the specified number of bits in the column *Mem*. To find the minimum memory overhead you need to find the line where *FP%* (false positive rate) is zero and *Mem* column is minimal.

To get the average detection time in case of using Unroller also run:

```shell
./loops-simulator.py paper/table4-unroller-time-[topology].py
```

For example, to simulate Unroller on Stanford topology run:

```
./loops-simulator.py paper/table4-unroller-time-stanford.py
```

You can then find the average detection time for Unroller as *AvgTime* column.

#### Figures 2-7: Sensitivity analysis

To get the data to plot any of the figures, run:

```
./loops-simulator.py paper/figureX.py
```

For example to run simulator to generate data for figure 6a data, run:

```
./loops-simulator.py paper/figure6a.py
```
