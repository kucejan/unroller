
# Unroller

*"Detecting Routing Loops in the Data Plane"*

## P4 implementation

Follow the instructions on https://github.com/p4lang/p4app to install `p4app` tool. Run Unroller P4 application using:

```
p4app run unroller.p4app
```

## Real-life topologies

Go to `topologies/topology-zoo` or `topologies/rocketfuel` to see instructions to download some real-life topologies.

## Topology Evaluator tool

Print help using:

```
./topology-evaluator.py --help
```

### Examples

```
./topology-evaluator.py -p zoo topologies/topology-zoo/archive/*.gml
./topology-evaluator.py -p stanford topologies/stanford-backbone/port_map.txt topologies/stanford-backbone/backbone_topology.tf
./topology-evaluator.py -p rocket $(find topologies/rocketfuel/maps-n-paths/ -type d | cut -d':' -f1 | sort -u | tail -n +2 | sed 's~\(.*\)/\([0-9]*\)~\1/\2:\2/edges~g' | xargs)
./topology-evaluator.py -p fattree 4
```

## Loops Simulator tool

TODO
