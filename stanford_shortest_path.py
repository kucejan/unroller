import networkx as nx
import matplotlib.pyplot as plt

PORT_TYPE_MULTIPLIER = 10000
SWITCH_ID_MULTIPLIER = 100000

def load_ports(filename):
    ports = {}
    names = {}
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

            if dpid not in names.keys():
                names[dpid] = switch_name
            if dpid not in ports.keys():
                ports[dpid] = set()
            if port not in ports[dpid]:
                ports[dpid].add(port)
    f.close()
    return ports, names

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

def get_topology(port_file, topo_file):

    topo = nx.Graph()
    link_port_map = {}

    # Read topology info
    ports, names = load_ports(port_file)
    links = load_topology(topo_file)
    switches = ports.keys()

    # print ports
    # print links
    # print switches
    # print names

    sw_port_max = {}

    # Create switch nodes
    for s in switches:
        topo.add_node(s, isHost = False, name = names[s])
        if not s in link_port_map:
            link_port_map[s] = {}
            sw_port_max[s] = 1

    # Wire up switches
    link_set = set()
    for (src_port_flat, dst_port_flat) in links:
        src_dpid = src_port_flat / SWITCH_ID_MULTIPLIER
        dst_dpid = dst_port_flat / SWITCH_ID_MULTIPLIER

        if not (src_dpid, dst_dpid) in link_set:
            port1 = sw_port_max[src_dpid]
            port2 = sw_port_max[dst_dpid]
            topo.add_edge(src_dpid, dst_dpid)
            link_port_map[src_dpid][dst_dpid] = port1
            link_port_map[dst_dpid][src_dpid] = port2
            sw_port_max[src_dpid] += 1
            sw_port_max[dst_dpid] += 1
            link_set.add((src_dpid, dst_dpid))
            link_set.add((dst_dpid, src_dpid))

    # Wire up hosts
    host_id = len(switches) + 1
    for s in switches:
        # Edge ports
        topo.add_node(host_id, isHost = True)
        topo.add_edge(host_id, s)
        link_port_map[s][host_id] = sw_port_max[s]
        sw_port_max[s] += 1
        host_id += 1

    return topo, link_port_map

def get_shortest_paths(topo):
    shortest_paths = {}
    edge_nodes = [n for n in topo.nodes() if topo.node[n]["isHost"]]
    for u in edge_nodes:
        shortest_paths[u] = {}
        paths = nx.single_source_shortest_path(topo, u)
        for v in edge_nodes:
            if u != v:
                shortest_paths[u][v] = paths[v]
                # print u, v, paths[v]
    return shortest_paths

def get_shortest_paths_routing(topo):
    routing = {}
    nodes = topo.nodes()
    for u in nodes:
        routing[u] = {}
        paths = nx.single_source_shortest_path(topo, u)
        for v in nodes:
            if u != v:
                routing[u][v] = paths[v][1]
                # print u, v, paths[v]
    return routing

def find_all_cycles(G, source=None):
    """forked from networkx dfs_edges function. Assumes nodes are integers, or at least
    types which work with min() and > ."""
    if source is None:
        # produce edges for all components
        nodes=G.nodes()
    else:
        # produce edges for components with source
        nodes=[source]
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

        stack = [(start,iter(G[start]))]
        while stack:
            parent,children = stack[-1]
            try:
                child = next(children)

                if child not in cycle_stack:
                    cycle_stack.append(child)
                    stack.append((child,iter(G[child])))
                else:
                    i = cycle_stack.index(child)
                    if i < len(cycle_stack) - 2:
                      output_cycles.add(get_hashable_cycle(cycle_stack[i:]))

            except StopIteration:
                stack.pop()
                cycle_stack.pop()

    return [list(i) for i in output_cycles]

def find_all_n_cycles(G, N, source=None):
    return [c for c in find_all_cycles(G, source) if len(c) == N]

if __name__ == "__main__":
    port_file = "stanford-backbone/port_map.txt"
    topo_file = "stanford-backbone/backbone_topology.tf"

    topo, _ = get_topology(port_file, topo_file)
    routing = get_shortest_paths_routing(topo)

    print routing
    print

    print find_all_n_cycles(topo, 7)