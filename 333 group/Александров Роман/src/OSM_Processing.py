from collections import Counter
from itertools import tee
import osmread as osm
from pyx.canvas import canvas, clip
from pyx import path, unit, style, color
from sys import argv
from utm import from_latlon

if __name__ == "__main__":
    FILENAME = next((arg for arg in argv[1:] if arg.endswith('.osm')), None)
    if not FILENAME:
        try:
            import dialog as dd
            FILENAME = dd.reqestFile()
            if not FILENAME: # ↓ also critical
                FILENAME = input('Absolute path to the file or just name: ')
        except:
            print('GUI loading failed. Looking for ".osm" file.')
        finally:
            if not FILENAME:
                FILENAME = 'dump.osm'

ways, nodes = [], dict()
print('Beginning to read file', FILENAME)
try:
    for ent in osm.parse_file(FILENAME):
        if isinstance(ent, osm.Way) and 'highway' in ent.tags:
            ways.append(ent)
        elif isinstance(ent, osm.Node):
            nodes[ent.id] = ent
except FileNotFoundError:
    from sys import exit
    exit('This program just need the file :(')

print('Done with reading. Total ways in file: {}. Total nodes: {}'.format(len(ways), len(nodes)))
is_cheboksary = len(nodes) == 293616

for ww in ways:
    for nd_id in ww.nodes:
        nd = nodes[nd_id]
        # If node found -> making a dict of data
        if isinstance(nd, osm.Node):
            x,y,_,_ = from_latlon(nd.lat, nd.lon)
            nodes[nd_id] = {'ways':[ww], 'x':x, 'y':y}
        else:
            nd['ways'].append(ww)

nodes = {nd_id:nd for nd_id, nd in nodes.items() if isinstance(nd, dict)}   
print('Nodes associated with roads:', len(nodes))

print('Kinds of road in the file:')
types_rank = Counter(ww.tags['highway'] for ww in ways)
for kind, count in types_rank.most_common(15):
    print('{:5} {}'.format(count, kind))

def _pairwise(iterable):
    'Helper-function. Fancy iterator: s -> (s0,s1), (s1,s2), (s2, s3), ...'
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

is_useful = lambda node_id, node: node_id == len(node['ways']) > 1 or \
    node_id == node['ways'][0].nodes[0] or node_id == node['ways'][0].nodes[-1]

useful_nodes = {nd_tuple[0] for nd_tuple in nodes.items() if is_useful(*nd_tuple)}
print('Important nodes number is {} out of {}'.format(len(useful_nodes), len(nodes)))

DIR_COUNT = {'no':2, 'yes':1, '-1':-1}

adj_list = {nd_id: set() for nd_id in useful_nodes}
for ww in ways:
    way_dirs = DIR_COUNT[ww.tags.get('oneway', 'no')]    
    for nd_pair in _pairwise(filter(lambda nd: nd in useful_nodes, ww.nodes[::1 if way_dirs > 0 else -1])):
        adj_list[nd_pair[0]].add(nd_pair[1])
        if way_dirs == 2:
            adj_list[nd_pair[1]].add(nd_pair[0])


def write_adj_list(filename='adj_list.txt'):
    with open(filename, 'w') as f:
        for nd_id, adj_nodes in adj_list.items():
            f.write('{}:{}\n'.format(nd_id, ','.join(str(nd_adj) for nd_adj in adj_nodes)))


def write_adj_matrix(filename='adj_matrix.csv'):
    with open(filename, 'w') as f:
        f.write(','+','.join(map(str, adj_list)))
        for nd, adj in adj_list.items():
            f.write(str(nd)+''.join(',1' if adj_nd in adj else ',0' for adj_nd in adj_list)+'\n')

# Ok, crop nicely if it's Cheboksary, else let it slide
if is_cheboksary:
    BOUNDS = {'b':56.0061, 'l':46.9347, 'r':47.6023, 't':56.1966}
    b_left, b_bottom, _, _ = from_latlon(BOUNDS['b'], BOUNDS['l'])
    b_right, b_top,   _, _ = from_latlon(BOUNDS['t'], BOUNDS['r'])
    unit.set(uscale=0.001)

hw_omit = {'service', 'footway', 'track', 'path', 'steps', 'pedestrian', 'construction', 'proposed', 'bus_stop', 'cycleway'}
hw_important = {'trunk', 'primary', 'secondary', 'tertiary', 'primary_link'}
clr_important = color.rgbfromhexstring('#6b0000')

def build_map(filename='map.pdf', full=True):
    canv = canvas([clip(path.rect(b_left, b_bottom, b_right - b_left, b_top - b_bottom))]) if is_cheboksary else canvas()
    
    for ww in ways if full else filter(lambda ww: ww.tags['highway'] not in hw_omit, ways):
        if ww.tags['highway'] in hw_important:
            ww_style = [style.linewidth(10+int(ww.tags.get('lanes', 1))*10), clr_important]
        else:
            ww_style = [style.linewidth(5+int(ww.tags.get('lanes', 1))*5)]
            
        for segm in _pairwise((nodes[n_id]['x'], nodes[n_id]['y']) for n_id in ww.nodes):
            canv.stroke(path.line(*segm[0], *segm[1]), ww_style)
    
    (canv.writePDFfile, canv.writeSVGfile)[int(filename.endswith('.svg'))](filename)

print('Creating an adjancety list...')
write_adj_list('adj_list.txt')
print('Creating a light version of the map...')
build_map('light_map.svg', full=False)
print('Creating a full map...')
build_map('full_map.pdf')
