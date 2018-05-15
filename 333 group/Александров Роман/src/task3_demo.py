from collections import OrderedDict
from functools import reduce
from sys import argv

from toolz import itertoolz as itz, functoolz as ftz

from output_mgr import build_map, write_paths_csv
from shortest_path import (
    mgr, adj_list, nodes, find_nearest_way_connections,
    random_nodeid, calculate_dists, expand_path)
from pathfinding_algorithms import dijkstra, IndexedQueue, Path
from tsp_nn import nearest_neighbor
from tsp_sim_annealing import simulated_annealing#, plot_last as sim_ann_plot
from miscellaneous import pairwise, timed

def init_spots(additional={}):
    "`Spots` and sth. else may be disconnected from roads."
    global spots, all_dists
    spots = dict(itz.take(10, sorted(mgr.spots.items(), key=lambda id_nd: id_nd[1]['x'])))
    nodes.update(spots)
    nodes.update(additional)
    find_nearest_way_connections({**spots, **additional})
    all_dists = calculate_dists()


def run_algorithm(func, start, paths, draw_map=False, label=None):
    "Runs TSP on a simplified graph. Outputs CSV and map with the full graph."
    try:
        ans = func(start, {u:{v:w.cost \
                for v, w in vw.items()} \
                for u, vw in paths.items()})
    except ValueError as exc:
        print('Some failure. Nodes are poorly connected ({})'.format(exc))
        return None
    
    print(ans)
    label = 'tsp ({})'.format(func.__name__.replace('_', ' ').title())
    pairs = [paths[u][v].path for u,v in pairwise(ans.path)]
    summary = ( ('Length:','{:.1f} km'.format(ans.cost)),
                ('Completed in:','{:.4f} sec.'.format(func.last_run())) )
    write_paths_csv(pairs, label, map(','.join, summary))
    if draw_map:
        build_map(  mgr.nodes, mgr.ways, label+'.pdf', full=False, highlight_ways=pairs,
                    comments=map(' '.join, summary))
    return ans


def demo_city(start=None):
    draw_map = True
    randomly = start is None

    while True:
        if randomly:
            start = random_nodeid() 
        if dijkstra(all_dists, start, spots.keys()):
            dests = (start,)+tuple(spots.keys())
            paths = {begin:dijkstra(all_dists, begin, dests) for begin in dests}
            break
        elif not randomly:
            raise Exception('Unreachable start node')

    run_algorithm(nearest_neighbor, start, paths, draw_map=draw_map)
    run_algorithm(simulated_annealing, start, paths, draw_map=draw_map)

    print(nearest_neighbor.stats())
    print(simulated_annealing.stats())
    # sim_ann_plot()


if __name__ == '__main__':
    if len(argv) >= 1 and argv[-1].isdecimal() and int(argv[-1]) in nodes:
        init_spots()
        demo_city(int(argv[-1]))

    elif len(argv) >= 2 and all(map(str.isnumeric, argv[-2:])):
        import math, utm
        lat, lon = map(float, argv[-2:])
        x, y, _, _ = utm.from_latlon(lat, lon)
        init_spots({1:{'x':x, 'y':y, 'lat': math.radians(lat), 'lon':math.radians(lon)}})
        demo_city(1)

    else:
        print('No valid arguments provided, so warehouse is just a random point.')
        init_spots()
        demo_city()
        
    