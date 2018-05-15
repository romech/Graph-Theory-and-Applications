from collections import defaultdict
from itertools import chain, product
from math import atan2, cos, inf, radians, sin, sqrt
from operator import attrgetter, itemgetter
from random import choice, randrange

import utm

import OSM_Processing as mgr
from output_mgr import bounds
from miscellaneous import pairwise, timed

adj_list, nodes = defaultdict(set), mgr.nodes
adj_list.update(mgr.adj_list)
ways = {way.id:way for way in mgr.ways}
node_ids = list(mgr.nodes.keys())


def dist_km(nd1, nd2):
    "Haversine distance"
    lat1, lon1 = nd1['lat'], nd1['lon']
    lat2, lon2 = nd2['lat'], nd2['lon']
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    # R = 6364 # approx. at Cheboksary
    return 6364 * 2 * atan2(sqrt(a), sqrt(1 - a))

dist_km_ids = lambda id1, id2: dist_km(nodes[id1], nodes[id2])
# dist_euc = lambda nd1, nd2: sqrt((nd1['x']-nd2['x'])**2 + (nd1['y']-nd2['y'])**2)
# _compose = lambda f, g: lambda *a, **kw: f(g(*a, **kw))

# dist_manh = lambda nd1, nd2: abs(nodes[nd1]['lat']-nodes[nd2]['lat']) + abs(nodes[nd1]['lon']-nodes[nd2]['lon'])


def get_info(nd_id):
    try:
        return dict(id=nd_id, **nodes[nd_id])
    except KeyError:
        return {id:nd_id}


# get_info = lambda nd_id: dict(id=nd_id, **nodes[nd_id])
def random_nodeid():
    return choice(node_ids)

def random_node():
    return nodes[random_nodeid()]

def make_point_at(x_rel, y_rel):
    x, y = bounds.left * (1 - x_rel) + bounds.right * x_rel, bounds.bottom * (1 - y_rel) + bounds.top * y_rel
    lat, lon = utm.to_latlon(x, y, 38, 'V')
    return {'x':x, 'y':y, 'lat':radians(lat), 'lon':radians(lon)}

def random_point():
    x, y = randrange(int(bounds.left), int(bounds.right)), randrange(int(bounds.bottom), int(bounds.top))
    lat, lon = utm.to_latlon(x, y, 38, 'V')
    return {'x':x, 'y':y, 'lat':radians(lat), 'lon':radians(lon)}

def random_points(count):
    return {i:random_point() for i in range(count)}

def linspaced_points(x_count, y_count):
    return {x*x_count+y:make_point_at(x/(x_count-1), y/(y_count-1)) \
            for x in range(x_count) for y in range(y_count)}

# Calculating weights of edges
@timed
def calculate_dists():
    dists = {}
    for nd_id, adj in adj_list.items():
        node1 = get_info(nd_id)
        dists[nd_id] = [(nd2, dist_km(node1, get_info(nd2))) for nd2 in adj]
    return dists

# The 2 awkward functions below connect spots with the road system
def find_nearest_way_connections(destinations):
    "Finds connection with a road, refines adj. list, returns a dict of tuples dest_id:waynode_id"
    dest_neighbors = { spot:(None, inf) for spot in destinations }
    for nd_id, nd in nodes.items():
        for dest_id, dest in destinations.items():
            if dist_km(nd, dest) < dest_neighbors[dest_id][1] and nd_id not in destinations:
                dest_neighbors[dest_id] = (nd_id, dist_km(nd, dest))
    
    for spot, neighbor in dest_neighbors.items():
        refine_adj_list(neighbor[0])
        adj_list[spot].add(neighbor[0])
        adj_list[neighbor[0]].add(spot)
    
    return {spot:neighbor[0] for spot, neighbor in dest_neighbors.items()}

def refine_adj_list(node):
    "Adds up to 2 edges to adj. list to make node connected"
    if node in adj_list:
        return
    way = nodes[node]['ways'][0].nodes
    self_index = way.index(node)
    before = next(nd for nd in way[self_index::-1] if nd in adj_list)
    after = next(nd for nd in way[self_index:] if nd in adj_list)
    if not after or not before:
        print('hmmmmm, something is wrong in `refine_adj_list`')
    else:
        adj_list[node].update((before, after))
        adj_list[before].add(node)
        adj_list[after].add(node)

# The next few functions are used to enhance paths for the full map
def get_len_of_segment(way, begin, end):
    "Returns length and segment that is part of the `way` from `begin` to `end`"
    ind1, ind2 = way.nodes.index(begin), way.nodes.index(end)
    if sum(1 for occ in way.nodes if occ == begin or occ == end)!=2:
        pass # whoops
    segm = way.nodes[min(ind1, ind2):max(ind1, ind2)+1]
    return sum(dist_km(nd1, nd2) for nd1, nd2 in pairwise(map(get_info, segm))), segm

def get_way_ids(nd_id):
    "Returns a set with the ways that cross `nd_id`"
    return set(way.id for way in get_info(nd_id).get('ways',[]))

def add_intermediate(n1, n2):
    "Returns shortest path across 1 way from n1 (incl.) to n2 (not incl.)"
    if mgr.spots.get(n1) or mgr.spots.get(n2): return [n1]
    common_ways = list(get_way_ids(n1) & get_way_ids(n2))
    connections = list(get_len_of_segment(ways[way_id], n1, n2) for way_id in common_ways)
    if connections:
        _, path = min(connections)
        return (path if path[0] == n1 else list(reversed(path)))[:-1]
    else:
        return [n1]

def expand_path(path):
    "Takes a path without intermediate nodes and returns an enhanced path as a list"
    # if len(path) == 2 and isinstance(path[1], tuple):
    #     path = restore_path(path)
    #     print('i fall in an obsolete IF @ shortest_path:118')
    return list(chain.from_iterable(add_intermediate(n1, n2) for n1, n2 in pairwise(path)))+[path[-1]]
