import pickle
from collections import Counter, defaultdict
from math import radians
from sys import argv

import osmread as osm
from utm import from_latlon

from miscellaneous import pairwise
from output_mgr import build_map, write_adj_list, write_adj_matrix

DEBUG = __name__ == "__main__"
GUI = DEBUG
DEFAULT_FILENAME = 'Cheboksary.osm'
FILENAME = None
VERSION = 0.12

try:    # TODO: make a separate function
    with open(DEFAULT_FILENAME + 'dump', 'rb') as f:
        dump = pickle.load(f)
        print('Found dump, opening backup')
        if dump['dump_ver'] < VERSION:
            print('Dump is built by older version')
            first_read = True
        else:
            for k, v in dump.items():
                vars()[k] = v
            first_read = False
except:
    first_read = True


if GUI:
    import dialog as dd
    if first_read:
    # Attempting to get filename from 1 - ARGV, 2 - GUI, 3 - STDIN
        FILENAME = next((arg for arg in argv[1:] if arg.endswith('.osm')), None)
        if not FILENAME:
            try:                
                FILENAME = dd.reqestFile()
                if not FILENAME: # ↓ also critical
                    FILENAME = input('Absolute path to the file or just name: ')
            except:
                print('GUI loading failed. Looking for ".osm" file.')

# Attempting to get 1- PICKLE dump, 2 - original .OSM file
if first_read:
    if not FILENAME:
        FILENAME = DEFAULT_FILENAME

    ways, nodes, spots = [], {}, []
    is_spot = lambda node: ent.tags.get('amenity', None) == 'hospital' and 'name' in ent.tags
    # is_spot = lambda node: ent.tags.get('amenity', None) in ['hospital', 'clinic']
    # is_spot = lambda node: ent.tags.get('shop', None) in ['electronics', 'computer']

    try:
        for ent in osm.parse_file(FILENAME):
            if isinstance(ent, osm.Way) and 'highway' in ent.tags:
                ways.append(ent)
            elif isinstance(ent, osm.Node):
                if is_spot(ent):
                    spots.append(ent)
                nodes[ent.id] = ent

        if DEBUG:
            print('Done with reading. Total ways in file: {}. Total nodes: {}'.format(len(ways), len(nodes)))
    except FileNotFoundError:
        from sys import exit
        exit('This program just need the file :(')

def dictWithXY(node, ways=None, add_original=False):
    x,y,_,_ = from_latlon(node.lat, node.lon)
    return {'ways':ways, 'x':x, 'y':y, 'lat':radians(node.lat), 'lon':radians(node.lon),
            'original':node if add_original else None}

if first_read:
    spots = {nd.id:dictWithXY(nd, add_original=True) for nd in spots}
    
    for ww in ways:
        for nd_id in ww.nodes:
            nd = nodes[nd_id]
            # If node found -> making a dict of data
            if isinstance(nd, osm.Node):
                nodes[nd_id] = dictWithXY(nd, ways=[ww])
            else:
                nd['ways'].append(ww)

    # Removing redundant nodes
    nodes = {nd_id:nd for nd_id, nd in nodes.items() if isinstance(nd, dict)}
    nodes.update(spots)

if DEBUG:        
    print('Nodes associated with roads:', len(nodes))
    
    print('Kinds of road in the file:')
    types_rank = Counter(ww.tags['highway'] for ww in ways)
    for kind, count in types_rank.most_common(15):
        print('{:5} {}'.format(count, kind))


is_useful = lambda node_id, node: node.get('ways') and ((len(node['ways']) > 1) or \
    (node_id == node['ways'][0].nodes[0]) or (node_id == node['ways'][0].nodes[-1]))

useful_nodes = {nd_tuple[0] for nd_tuple in nodes.items() if is_useful(*nd_tuple)}
if DEBUG:
    print('Important nodes number is {} out of {}'.format(len(useful_nodes), len(nodes)))

if first_read:
    DIR_COUNT = {'no':2, 'yes':1, '-1':-1}
    adj_list = defaultdict(set)

    for ww in ways:
        way_dirs = DIR_COUNT[ww.tags.get('oneway', 'no')]    
        for nd1, nd2 in pairwise(filter(lambda nd: nd in useful_nodes, ww.nodes[::1 if way_dirs > 0 else -1])):
            adj_list[nd1].add(nd2)
            if way_dirs == 2:
                adj_list[nd2].add(nd1)


    dump = {'adj_list':adj_list, 'nodes': nodes, 'spots':spots, 'ways': ways, 'dump_ver':VERSION}
    with open(FILENAME+'dump', 'wb') as f:
        pickle.dump(dump, file=f)

if DEBUG:
    options = ['light-map', 'full-map', 'adj-list']
    if GUI:
        chosen = options # options TODO: make this selectable
    else:
        ans_list = input('Create output files? (all / {})'.format(' / '.split(options))).split()
        if 'all' in ans_list:
            chosen = options

    if 'adj-list' in chosen:
        print('Creating an adjancety list...')
        write_adj_list(adj_list, 'adj_list.txt')
    if 'light-map' in chosen:    
        print('Creating a light version of the map...')
        build_map(nodes, ways, 'light_map.pdf', full=False)
    if 'full-map' in chosen:
        print('Creating a full map...')
        build_map(nodes, ways, 'full_map.pdf')
