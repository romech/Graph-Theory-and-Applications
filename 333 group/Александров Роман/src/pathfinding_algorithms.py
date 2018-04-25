from collections import OrderedDict, defaultdict, namedtuple
from functools import lru_cache
from heapq import heappop, heappush
from itertools import chain
from math import inf, sqrt
from operator import itemgetter

from sortedcontainers import SortedSet as btree_pqueue

from miscellaneous import timed

restore_path = lambda tup: (*restore_path(tup[1]),tup[0]) if tup else ()
Path = namedtuple('Path', ['cost', 'path'])

@timed
def dijkstra(gr, start, ends):
    '''
    `gr` is a `dict` { u:(v, cost) | (u,v) ∈ E }
    `f` is first vertex
    `t` is terminal
    returns: cost, path
    '''
    q, seen = [(0,start,())], set()
    ans = OrderedDict.fromkeys(ends)

    while q:
        cost, v1, path = heappop(q)
        if v1 not in seen:
            seen.add(v1)
            path = (v1, path)

            if v1 in ans and not ans[v1]:
                ans[v1] = Path(cost=cost, path=restore_path(path))

            for v2, c in gr.get(v1, ()):
                if v2 not in seen:
                    heappush(q, (cost+c, v2, path))

    return OrderedDict(filter(itemgetter(1), ans.items()))


class IndexedQueue(OrderedDict):
    "Queue with search ~ O(Log)"
    def push(self, item):
        self[item] = None

    def pop(self):
        return OrderedDict.popitem(self, last=False)[0]

# Same as `lambda: math.inf`, but doesn't break pickling for multiprocessing
def infinity(): return inf

@timed
def levit(gr, start, ends):
    '''
    An algorithm for finding the shortest path from one `start` node to all another.
    `gr` is an adjancety list { u:[(v, cost), ...] | (u,v) ∈ E },
    `ends` are the desired target nodes, though all graph is processed anyway.
    Returns a dict like { node: Path(cost, path) }
    '''
    dist = defaultdict(infinity)
    dist[start] = 0
    path = {start:(start,())}
    m0 = set()
    m1, m1_urg = IndexedQueue.fromkeys([start]), IndexedQueue()
    m2 = set(chain.from_iterable((v for v, _ in from_u) for from_u in gr.values())) - {start}
    
    def relax(u, v, w):
        if (dist[v] > dist[u] + w):
            dist[v] = dist[u] + w
            path[v] = (v, path[u])
            return True
        return False

    while m1 or m1_urg:
        u = m1_urg.pop() if m1_urg else m1.pop()
        for v, c in gr.get(u, ()):
            if v in m2:
                m1.push(v)
                m2.discard(v)
                relax(u, v, c)
            elif v in m1:
                relax(u, v, c)
            elif v in m0 and relax(u, v, c):
                m1_urg.push(v)
                m0.discard(v)
        m0.add(u)

    return OrderedDict((v, Path(cost=dist[v], path=restore_path(path[v]))) for v in ends if v in path)                


estim = namedtuple('estim', ['heur', 'dist', 'prev'])

def astar(gr, start, end, heur):
    c = {start: estim(heur=heur(start, end), dist=0, prev=None)}
    q = btree_pqueue([(c[start].heur, start)])

    while q:
        _, u = q.pop(0)
        if u == end:
            path = [u]
            while path[-1] is not start:
                path.append(c[path[-1]].prev)

            return Path(c[u].dist, tuple(reversed(path)))
        
        for v, w in gr.get(u, ()):
            tent = c[u].dist + w
            if v not in c or tent < c[v].dist:
                if v in c:
                    q.discard((c[v].heur, v))
                v_heur = tent+heur(v, end)
                c[v] = estim(heur=v_heur, dist=tent, prev=u)
                q.add((v_heur, v))
    
    return Path(inf, None)

def set_context(node_coords):
    global nodes
    nodes = node_coords

@lru_cache(maxsize=None, typed=True)
def dist_manh(id1, id2):
    return 0.55 * (abs(nodes[id1]['lat'] - nodes[id2]['lat']) * 3540 +
                  abs(nodes[id1]['lon'] - nodes[id2]['lon']) * 6364)

@lru_cache(maxsize=None, typed=True)
def dist_euc(id1, id2):
    return 0.55 * sqrt(((nodes[id1]['lat'] - nodes[id2]['lat']) * 3540) ** 2 +
                       ((nodes[id1]['lon'] - nodes[id2]['lon']) * 6364) ** 2)

@lru_cache(maxsize=None, typed=True)
def dist_cheb(id1, id2):
    return 0.55 * max(abs(nodes[id1]['lat'] - nodes[id2]['lat']) * 3540,
               abs(nodes[id1]['lon'] - nodes[id2]['lon']) * 6364)


@timed
def astar_manh(*args, **kwargs):
    return astar(*args, heur=dist_manh, **kwargs)

@timed
def astar_euc(*args, **kwargs):
    return astar(*args, heur=dist_euc, **kwargs)

@timed
def astar_cheb(*args, **kwargs):
    return astar(*args, heur=dist_cheb, **kwargs)


