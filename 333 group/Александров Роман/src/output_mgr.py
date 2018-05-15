from collections import namedtuple
from functools import lru_cache
from itertools import tee
import os.path

from pyx import color, path, style, text, unit
from pyx.canvas import canvas, clip
from transliterate import translit
from utm import from_latlon

from miscellaneous import pairwise

FOLDER_NAME = 'output'
_make_folder = True

def _open(filename, mode):
    global _make_folder
    if _make_folder:
        _make_folder = False
        try:
            os.mkdir(FOLDER_NAME)
        except FileExistsError:
            pass
    
    return open(os.path.join(FOLDER_NAME, filename), mode)

def write_adj_list(adj_list, filename='adj_list.txt'):
    '''
    Assuming `adj_list` is a dict of iterables, writes a file like:
    123:234,567
    345:123
    ...
    '''
    with _open(filename, 'w') as f:
        for nd_id, adj_nodes in adj_list.items():
            f.write('{}:{}\n'.format(nd_id, ','.join(str(nd_adj) for nd_adj in adj_nodes)))


def write_adj_matrix(adj_list, filename='adj_matrix.csv'):
    "Creates a file with an adjancety matrix. Really huge, thus not recommended to run."
    with _open(filename, 'w') as f:
        f.write(','+','.join(map(str, adj_list)))
        for nd, adj in adj_list.items():
            f.write(str(nd)+''.join(',1' if adj_nd in adj else ',0' for adj_nd in adj_list)+'\n')

unit.set(uscale=0.002)

_hw_omit = {'service', 'footway', 'track', 'path', 'steps', 'pedestrian', 'construction', 'proposed', 'bus_stop', 'cycleway'}
_hw_important = {'trunk', 'primary', 'secondary', 'tertiary', 'primary_link','highlight'}
_clr_important = color.rgbfromhexstring('#200000')

def _road_linestyle(kind, lanes):
    if kind in _hw_important:
        return [style.linewidth((int(lanes)+1)*8), _clr_important]
    else:
        return [style.linewidth((int(lanes)+1)*4)]

def linspace_colors(n):
    return [color.hsb(0.85*i/(n-1), 1, 0.85) for i in range(n)] if n > 1 else (color.hsb(0, 1, 0.85),)

def make_style(color=None, kind=None, lanes=None):
    '''
    Produces an object to be passed into `pyx.canvas.fill`
    `color` is probably required argument.
    `kind` or `lanes` number should be provided for roads.
    '''
    if kind:
        if kind in _hw_important:
            color = color or _clr_important
            lanes = lanes * 2 if lanes else 10
        lanes = style.linewidth((int(lanes)+1)*5)

    return list(filter(None,[color, lanes]))

Rect = namedtuple('Rect', ['right', 'top', 'left', 'bottom'])

if True: # marker for Cheboksary. TODO: make it another way
    bounds_ll = Rect(47.6023, 56.1966, 46.9347, 56.0061)
    bounds = Rect(*from_latlon(bounds_ll.top, bounds_ll.right)[:2],
                  *from_latlon(bounds_ll.bottom, bounds_ll.left)[:2])
    clip_box = path.rect(x=bounds.left, y=bounds.bottom,
                         width=bounds.right - bounds.left, height=bounds.top - bounds.bottom)

@lru_cache(maxsize=16, typed=True)
def _safer_text(txt):
    return translit(txt, 'ru', reversed=True).encode("ascii", errors="ignore").decode()


def build_map(nodes, ways, filename='map.pdf', full=True, highlight_ways=None, highlight_nodes=[], comments=None):
    '''
    Draws a map to a pdf/eps/svg file. Arguments:
    `nodes` - dict of dicts with `x` and `y` keys,
    `ways` - a list of `osm.Way` objects,
    `full` - helps to draw a light version of map without pedestrian paths,
    `highlight` - an iterable of node ids or lists of them to draw it highlighted
    '''
    # 1. Setting up a context
    _replace_with_xy = lambda n_id: (nodes[n_id]['x'], nodes[n_id]['y'])

    canv = canvas([clip(clip_box)]) if clip_box else canvas()
    
    # 2. Drawing roads
    for ww in ways if full else filter(lambda ww: ww.tags['highway'] not in _hw_omit, ways):
        ww_style = _road_linestyle(ww.tags['highway'], ww.tags.get('lanes', 1))
        
        for segm in pairwise(list(map(_replace_with_xy, ww.nodes))):
            canv.stroke(path.line(*segm[0], *segm[1]), ww_style)
 
    # 3. Drawing highlighted
    # ww_style = [style.linewidth(45), color.rgb(0, 0.5, 0)]
    if highlight_ways:
        styles = (make_style(clr, kind='highlight') for clr in linspace_colors(len(highlight_ways)))
        for way, _style in zip(highlight_ways, styles):
            for segm in pairwise(list(map(_replace_with_xy, way))):
                canv.stroke(path.line(*segm[0], *segm[1]), _style)
            canv.fill(path.circle(*_replace_with_xy(way[0]), 90), _style)    
            canv.fill(path.circle(*_replace_with_xy(way[-1]), 90), _style)
        for i, way in enumerate(highlight_ways, 1):
            x, y = _replace_with_xy(way[-1])
            canv.text(x - 60, y - 50, str(i))


    _style = [color.hsb(0.2, 1, 0.75)]
    for elem in highlight_nodes:
        if isinstance(elem, list):
            _style = elem
        else:
            canv.fill(path.circle(*_replace_with_xy(elem), 50), _style) #[color.rgb(0.5, 0, 0)]
    
    if comments:
        for i, line in enumerate(map(_safer_text, comments)):
            canv.text(bounds.left + 500, bounds.top - 800 - i * 500, line, [text.size.LARGE])
    canv.writePDFfile(_open(filename, 'wb'))
    # canv.writetofile(_open(filename, 'wb'))


from itertools import zip_longest
def write_paths_csv(paths, filename, summary=None):

    if not filename.endswith('.csv'):
        filename += '.csv'
    with _open(filename, 'w') as table:
        print_kw = {'sep':',,', 'file':table}
        
        # From ... to | ... ... ... | summary | blank line
        print('From,{},to:'.format(paths[0][0]), file=table)
        print(*(path[-1] for path in paths), **print_kw)
        if summary:
            print(**print_kw)        
            print(*summary, **print_kw)
        print(**print_kw)

        for nodes in zip_longest(*paths,fillvalue=''):
            print(*nodes, **print_kw)

def write_report(filename, contents):
    with _open(filename, 'w') as file:
        for line in contents:
            print(line, file=file)

if __name__ == '__main__':
    # write_paths_csv((1,2,3,4,5,6,7), 'demo.csv')

    write_paths_csv(((1,2,3),(1,10),(1,100,200,300)), 'demo')
