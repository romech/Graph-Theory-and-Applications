# Based on https://ericphanson.com/posts/2016/the-traveling-salesman-and-10-lines-of-python/

import math
import random
from itertools import chain

# import matplotlib.pyplot as plt
# import numpy

from miscellaneous import pairwise, timed
from pathfinding_algorithms import Path

_history_eval, _history_taken = None, None

@timed
def simulated_annealing(start, dists, steps=1000):
    global _history_eval, _history_taken
    dist = lambda path: sum(dists[u][v] for u, v in pairwise(path))
    
    cities = list(filter(lambda c: c is not start, dists.keys()))
    random.shuffle(cities)
    tour = (start,) + tuple(cities) + (start,)
    tour_len = dist(tour)
    
    mutations, _history_eval, _history_taken = 0, [tour_len], [tour_len]

    for temperature in [steps**(-math.e)*(x**3) for x in range(steps, 0, -1)]:
    # for temperature in numpy.logspace(-3,1,num=steps)[::-1]:
        i, j = sorted(random.sample(range(1, len(tour)-1),2))
        tour_muted =  tour[:i] + tour[j:j+1] + tour[i+1:j] + tour[i:i+1] + tour[j+1:]
        muted_len = dist(tour_muted)
        _history_eval.append(muted_len)

        if muted_len < tour_len or math.exp((tour_len-muted_len)/temperature) > random.random():
            tour, tour_len = tour_muted, muted_len
            mutations += 1

        _history_taken.append(tour_len)

    print('Mutations:', mutations)
    return Path(cost=tour_len, path=tour)

# def plot_last():
#     plt.plot(range(len(_history_eval)), _history_eval, 'bo',
#              range(len(_history_taken)), _history_taken, 'k')
#     plt.show()


# nodes = ((1, 0), (2, 1000), (3, 4000))
# edges = {u:{v:abs(ux-vx) for v, vx in nodes if v!=u} for u, ux in nodes}

# 1 - - - - 2
# |         |
# |         |
# |         |
# 4 - - - - 3
if __name__ == '__main__':
    edges = {
        1:{1:0,2:4, 3:5, 4:3},
        2:{2:0,1:4, 3:3, 4:5},
        3:{3:0,1:5, 2:3, 4:4},
        4:{4:0,1:3, 2:5, 3:4}
    }
    start = 1
    cities = (2,3,4)

    print(simulated_annealing(start, edges, steps=50))
    plot_last()



# tour = list(cities)
# def dist(path):
#     return sum(edges[u][v] for u, v in pairwise(tour))

# for temperature in numpy.logspace(0,5,num=1000)[::-1]:
#     i, j = sorted(random.sample(range(len(cities)),2))
#     newTour =  tour[:i] + tour[j:j+1] + tour[i+1:j] + tour[i:i+1] + tour[j+1:]

#     if math.exp((dist(tour) - dist(newTour)) / temperature) > random.random():
#         tour = newTour

# print(tour)
