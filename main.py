#!/usr/bin/python

import sys
from simulation import *
from math import *

USAGE = "main.py <simulation type> <params>"

# The timing used today
basic_timing = [
    (30, [EW, WE]),
    (30, [NS, SN]),
    (15, [ES, WN]),
    (15, [SW, NE]),
]

# Timing that gives more
basic_timing2 = [
    (31, [EW, WE]),
    (30, [NS, SN]),
    (16, [ES, WN]),
    (15, [SW, NE]),
]

double_timing = [
    (60, [EW, WE]),
    (60, [NS, SN]),
    (30, [ES, WN]),
    (30, [SW, NE]),
]

def periodic(name):
    return lambda x: PeriodicController(globals()[name], x)

def cyclic_cleaning():
    return lambda x: CyclicCleaningController(x, [[EW, WE], [NS, SN], [ES, WN], [SW, NE]])

def acyclic_cleaning():
    return lambda x: AcyclicCleaningController(x, [[EW, WE], [NS, SN], [ES, WN], [SW, NE]])

types = {
    'periodic' : periodic,
    'cyclic_cleaning' : cyclic_cleaning,
    'acyclic_cleaning' : acyclic_cleaning
}    

def main(argv):
    flags = [x for x in argv if x.startswith("-")]
    argv = [x for x in argv if not x.startswith("-")]
    if len(argv) < 2:
        print USAGE
        return 1
    time_arg = [x for x in argv if x.startswith("time=")]
    time = 3600
    if len(time_arg) > 0:
        time_arg = time_arg[0]
        argv.remove(time_arg)
        time = 60 * float(time_arg[5:])
    controller = types[argv[1]](*argv[2:])
    if "--test" not in flags:
	simulate_many(controller, time, 300, 1, False)
    else:
        test_simulation(controller, time, 300, 1)   
    return 0

def simulate(controller, time):
    x = Intersection(LANES, INITIAL_CARS)
    c = controller(x)
    for i in xrange(int(time)):
        c.step()
    stats_by_dir = {dr : reduce(operator.add, [FloatStat(w) for w in x.waiting_times[dr]]) if x.waiting_times[dr] else FloatStat(0) for dr in DIRS}
    return DirectionsDict(stats_by_dir)
    #return { d: len(x.cars[d]) for d in DIRS }

def simulate_many(controller, time, N, num_simulations, verbose = False):
    for j in xrange(num_simulations):
        s = simulate(controller, time)
        if verbose:
            print "current:", s	
        for i in xrange(N):
	    res = simulate(controller, time)
	    if verbose:
                print "current:", res
	    s += res
        print FloatStatTotal(s.dct.values()), s 

	
def test_simulation(controller, time, N, num_simulations):
    for k in xrange(num_simulations):
        d = {dr : [] for dr in DIRS}
        tot = []
        for j in xrange(N):	
	    x = Intersection(LANES, INITIAL_CARS)
            c = controller(x)
            for i in xrange(int(time)):
                c.step()
    	    for dr in DIRS: 
	        d[dr] += x.waiting_times[dr]
                tot += x.waiting_times[dr]
        print "%.2f(%.2f) ;" % (numpy.mean(tot), numpy.std(tot))
        for dr in DIRS:
	    print "%.2f(%.2f)" % (numpy.mean(d[dr]), numpy.std(d[dr])), numpy.random.choice(d[dr], 20).tolist()

class FloatStat(object):
    def __init__(self, f = 0, f2 = None, n = 1):
        self.n = n
        self.f = f
        self.f2 = f2 if f2 is not None else f ** 2
    def __add__(self, other):
        return FloatStat(self.f + other.f, self.f2 + other.f2, self.n + other.n)
    def __radd__(self, other):
        if not other:
            return self
        else:
            return self+other
    def __repr__(self):
        avg = self.f / float(self.n)
        return "%.2f(%.2f)" % (avg, sqrt(self.f2 / float(self.n) - avg ** 2))

class DirectionsDict(object):
    def __init__(self, dct):
        self.dct = dct
    def __iadd__(self, other):
        for key, val in other.dct.iteritems():
            self.dct[key] = self.dct.get(key, 0) + val
        return self
    def __add__(self, other):
        res = DirectionsDict(self.dct.copy())
        res += other
        return res
    def __div__(self, a):
        return DirectionsDict({x:y/a for x,y in self.dct.iteritems()})
    def __repr__(self):
        return "[" + \
            ", ".join([repr(self.dct[x]) for x in DIRS]) + "]"

class StatTuple(object):
    def __init__(self, *tup):
        self.tup =  tup
    def __repr__(self): return repr(self.tup)
    def __add__(self, other):
        return StatTuple(*[x+y for x,y in zip(self.tup, other.tup)])
    def __div__(self, a):
        return StatTuple(*[x/a for x in self.tup])

class FloatStatTotal(object):
    def __init__(self, float_stats):
        self.mean = 0
        self.std = 0
        self.n = 0
        for fs in float_stats:
            self += fs

    def __iadd__(self, other):
        if isinstance(other, FloatStat):
            self.mean = (self.mean * self.n + other.f) / float(self.n + other.n)
            self.std = (self.std * self.n + sqrt(other.f2 / other.n - other.f**2 / other.n**2) * other.n) / float(self.n + other.n)
            self.n = self.n + other.n
            return self
        elif isinstance(other, FloatStatTotal):
            self.mean = (self.mean * self.n + other.mean * other.n) / (self.n + other.n)
            self.std = (self.std * self.n + other.std * other.n) / (self.n + other.n)
            self.n = self.n + other.n
            return self
        else:
            raise TypeError

    def __add__(self, other):
        res = FloatStatTotal([])
        res += self
        res += other
        return res

    def __repr__(self):
        return "%.2f(%.2f)" % (self.mean, self.std)

         
if __name__ == '__main__':
    sys.exit(main(sys.argv))
