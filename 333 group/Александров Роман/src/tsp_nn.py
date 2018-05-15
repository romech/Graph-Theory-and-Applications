from toolz import functoolz as fn
from toolz import itertoolz as itz

from miscellaneous import timed
from pathfinding_algorithms import Path


def _append_to_path(node_cost, path):
    return Path(cost=path.cost+node_cost[1], path=path.path+(node_cost[0],))


@timed
def nearest_neighbor(start, dists):
    left = set(dists.keys())
    path = fn.reduce(
        lambda p, _: fn.pipe(
                dists[p.path[-1]].items(),
                fn.partial(filter, lambda c: c[0] not in p.path),
                fn.partial(min, key=itz.second),
                fn.partial(_append_to_path, path=p)
            ),
        range(len(left)-1),
        Path(cost=0, path=(start,))
    )
    return _append_to_path((start, dists[path.path[-1]][start]), path)


if __name__ == '__main__':
    # TEST
    # 1-d fully connected points
    nodes = (('a', 0), ('b', 1), ('c', 4))
    edges = {u:{v:abs(ux-vx) for v, vx in nodes if v!=u} for u, ux in nodes}
    assert nearest_neighbor('b', edges) == Path(cost=8, path=('b', 'a', 'c', 'b'))
