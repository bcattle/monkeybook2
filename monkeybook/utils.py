import datetime, itertools, cProfile

# Cool trick:   go through results in pstats interactive mode
#               python -m pstats run_yearbook-2013-03-25\ 12\:23\:19.851206.profile

def profileit(name):
    def inner(func):
        def wrapper(*args, **kwargs):
            prof = cProfile.Profile()
            retval = prof.runcall(func, *args, **kwargs)
            # Note use of name from outer scope
            prof.dump_stats('%s-%s.profile' % (name, datetime.datetime.now()))
            return retval
        return wrapper
    return inner


import time
from functools import wraps

def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwds):
        start = time.time()
        value = func(*args, **kwds)
        elapsed = time.time() - start
        print '%r ran in %2.2f sec' % (func.__name__, elapsed)
        return value
    return wrapper


def merge_spaces(s):
    """
    Combines consecutive spaces into one,
    useful for cleaning up multiline strings
    """
    return " ".join(s.split())

# http://stackoverflow.com/a/38990/1161906
def merge_dicts(*dicts):
    return dict(itertools.chain(*[d.iteritems() for d in dicts]))
