from itertools import tee
from functools import wraps
from statistics import mean, stdev
from timeit import default_timer


def pairwise(iterable):
    'Helper-function. Fancy iterator: s -> (s0,s1), (s1,s2), (s2, s3), ...'
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def _stats_string(data, label):
    if data:
        m = mean(data)
        return '{:.2f}+-{:.2f} sec for {}'.format(m, stdev(data, xbar=m) if len(data) > 1 else 0, label)

def timed(fn):
    "Decorator for function time measurement"
    fn.hist = []
    @wraps(fn)
    def decfn(*a, **kw):
        t0 = default_timer()
        res = fn(*a, **kw)
        fn.hist.append(default_timer() - t0)
        return res
    decfn.last_run = lambda: fn.hist[-1] if fn.hist else None
    decfn.avg = lambda: sum(fn.hist)/len(fn.hist) if fn.hist else None
    decfn.stats = lambda: _stats_string(fn.hist, fn.__name__)
    return decfn

if __name__ == '__main__':
    import time, random
    @timed
    def waiter():
        time.sleep(random.random())

    for _ in range(4):
        waiter()
    print(waiter.stats())

        