#!/usr/bin/python2.7

import numpy, operator

DIRS = EW, ES, SN, SW, WE, WN, NS, NE = range(8)

LANES = {EW: 2, ES: 2, SN: 2, SW: 2, WE: 2, WN: 1, NS: 2, NE: 1}

INITIAL_CARS = { EW: 133, ES: 67, SN: 10, SW: 5, WE: 16, WN: 4, NS: 20, NE: 5  }

AVERAGES = { EW: 56.85 / 90.,   ES: 26.4 / 90.,
             SN: 48.17 / 90., SW: 25 / 90.,
             WE: 40.2 / 90., WN: 12.05 / 90.,
             NS: 54.8/ 90., NE: 12.42 / 90., }


class Intersection(object):
    def __init__(self, lanes, cars):
        self.lanes = lanes.copy()
        self.cars = {dr : [None] * cars[dr] for dr in DIRS}
        self.active_dirs = None
        self.average = AVERAGES
        self.delay = 2
        self.time = 0
        self.waiting_times = { d: [] for d in DIRS }

    def insert_new_cars(self):
        for dr in DIRS:
            for i in xrange(numpy.random.poisson(self.average[dr])):
                self.cars[dr].append(self.time)
         
    def step_second(self):
        self.insert_new_cars()
        if self.delay > 0:
            self.delay -= 1
        else:
            for dr in self.active_dirs:
                for i in xrange(min(self.lanes[dr], len(self.cars[dr]))):
                    enter_time = self.cars[dr][0]
                    if enter_time is not None:
                        self.waiting_times[dr].append(self.time - enter_time)
                    del self.cars[dr][0]
        self.time += 1

    def change_dirs(self, dirs):
        self.active_dirs = dirs
        self.delay = 2

class TrafficController(object):
    def __init__(self, intersection):
        self.intersection = intersection

class PeriodicController(TrafficController):
    def __init__(self, timing, intersection):
        super(PeriodicController, self).__init__(intersection)
        self.timing = timing   
        self.time = 0
        self.phase = 0
        self.intersection.change_dirs(self.timing[self.phase][1])

    def step(self):
        self.intersection.step_second()
        self.time += 1
        if self.time >= self.timing[self.phase][0]:
            self.phase = (self.phase + 1) % len(self.timing)
            self.time = 0
            self.intersection.change_dirs(self.timing[self.phase][1])

class CleaningController(TrafficController):
    def __init__(self, intersection, dirs_list):
        super(CleaningController, self).__init__(intersection)
        self.dirs_list = dirs_list
        self.phase = 0
        self.intersection.change_dirs(self.dirs_list[0])
        
    def step(self):
        raise NotImplementedError()

class CyclicCleaningController(CleaningController):
    def step(self):
        if all([self.intersection.cars[dr] == [] for dr in self.dirs_list[self.phase]]):
            self.phase = (self.phase + 1) % len(self.dirs_list)
            self.intersection.change_dirs(self.dirs_list[self.phase])
        self.intersection.step_second()
        
class AcyclicCleaningController(CleaningController):
    def step(self):
        if all([self.intersection.cars[dr] ==  [] for dr in self.dirs_list[self.phase]]):
            max_size = -1             
            for new_phase in range(4):
                size = sum([len(self.intersection.cars[d]) for d in self.dirs_list[new_phase]])
                if size > max_size:
                    self.phase = new_phase
                    max_size = size
            self.intersection.change_dirs(self.dirs_list[self.phase])
        self.intersection.step_second()

