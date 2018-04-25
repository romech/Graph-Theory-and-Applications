# from concurrent.futures import ProcessPoolExecutor as proc_pool
from itertools import islice, product, repeat
from operator import itemgetter
import sys

from output_mgr import build_map, make_style, color, write_paths_csv, write_report
import pathfinding_algorithms
from pathfinding_algorithms import astar, dijkstra, levit, astar_euc, astar_cheb, astar_manh
from shortest_path import (
    mgr, nodes, node_ids, bounds,
    find_nearest_way_connections, expand_path, calculate_dists, random_points, linspaced_points
)

ALL_ALGORITHMS = (astar_manh, astar_euc, astar_cheb, dijkstra, levit)
# OK, now moving on to usage
def demonstrate(func, gr, start, ends, task_id='', write_res=True, draw_map=False):
    if write_res:
        label = str(task_id or start[0]) + ' - ' + func.__name__ 
        print('spawned', label)
    nodes[start[0]] = start[1]

    # path finding
    if func is dijkstra or func is levit:
        cost_paths = islice(func(gr, start[0], ends).values(), 10)
    else:
        pathfinding_algorithms.set_context(nodes)
        cost_paths = islice(filter(itemgetter(1), map(func, repeat(gr), repeat(start[0]), ends)), 10)
        
    try:
        costs, paths = zip(*cost_paths)
    except ValueError:
        print('Could not find any path from', start)
        return
    if not (write_res or draw_map): return

    summary = [(i+1, spot['original'].tags['name'], costs[i], round(costs[i]/40*60)) \
                for i, spot in enumerate(map(mgr.spots.get, (path[-1] for path in paths)))]


    if write_res:
        print('done with {} in {:.2f}s'.format(label, func.last_run()))
        write_paths_csv(paths, label, ('"{:.1f} km, ~{} min"'.format(length, time) for _,_,length,time in summary))
        
    
    if draw_map:
        comments = ('{}. {} ({:.1f} km, ~{} mins)'.format(*row) for row in summary)
        build_map(nodes, mgr.ways, filename=label+'.pdf', full=False,
                  highlight_ways=expand_path(paths), highlight_nodes=[make_style(color.gray(1)), start[0]],
                  comments=comments)
        print('map built', label)
    # return func.last_run()


def run_algorithms(starts, algorithms=ALL_ALGORITHMS, write_res=True, draw_map=False):
    global nodes
    nodes.update(starts)
    
    find_nearest_way_connections({**mgr.spots, **starts})
    dists = calculate_dists()
    print('Initialized weights in {:.2f} sec.'.format(calculate_dists.last_run()))

    dests = sorted(mgr.spots.keys(), key=lambda nd_id: nodes[nd_id]['x'])

    kw = [(f, dists, s[1], dests, s[0], write_res, draw_map) \
        for f,s in product(algorithms, enumerate(starts.items()))]

    list(map(demonstrate, *zip(*kw)))

    for fn in algorithms:
        print(fn.stats())

    

def demo_ui(start=None):
    run_algorithms(start or random_points(1), algorithms=(dijkstra,), write_res=True, draw_map=True)

def demo_linspace():
    run_algorithms(starts=linspaced_points(10, 10), write_res=False, draw_map=False)
    write_report('benchmark.txt', [fn.stats() for fn in ALL_ALGORITHMS])


def demo_astar():
    astars = (astar_manh, astar_cheb, astar_euc)
    run_algorithms(starts=random_points(5), algorithms=astars)
    write_report('astar heuristics.txt', [fn.stats() for fn in astars])
    

ARGV_OPTIONS = '''
* `benchmark` to compare performance of the algorithms
* `astar` to compare heuristics for A*
* ID to find and see the shortest paths from a node chosen by id
* LAT LON coordinates to do the same by coordinate
'''

if __name__ == '__main__':
    argv = sys.argv
    print(argv)
    if len(argv) == 1:
        try:
            print('Choose your option:', ARGV_OPTIONS)
            argv = input('Action:').split()
        except:
            write_report('README.txt', ['Run the program with some arguments:'+ARGV_OPTIONS])
            argv = []

    if not argv:
        print('No arguments provided, so I will just find the shortests paths from a random point.')
        demo_ui()
        sys.exit(0)

    if len(argv) == 2 and all(map(str.isnumeric, argv)):
        import math, utm
        lat, lon = map(float, argv)
        x, y, _, _ = utm.from_latlon(lat, lon)
        demo_ui({1:{'x':x, 'y':y, 'lat': math.radians(lat), 'lon':math.radians(lon)}})
        sys.exit(0)

    for arg in argv:
        if arg == 'benchmark':
            demo_linspace()
        elif arg == 'astar':
            demo_astar()
        elif arg.isdecimal():
            maybe_nodeid = int(arg)
            node = nodes.get(maybe_nodeid)
            if node:
                demo_ui({maybe_nodeid:node})
            else:
                print('Undefined argument (not a node of any road):', argv)
        
