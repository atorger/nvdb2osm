# TwoDimSearch
#
# Search data structure with range functions for two-dimensional points (x,y). Should ideally
# be implemented with 2dtree (or kdtree), but this is acceptable fast, often faster than
# non-native kdtrees it seems

import math
from sortedcontainers import SortedDict
from geometry_basics import Point

class TwoDimSearch:
    def __init__(self):
        self.xmap = SortedDict({})
        self._len = 0
        self._xit = None
        self._yit = None
        self._ymap = None

    @staticmethod
    def _calc_dist_sq(p, x, y):
        dx = p.x - x
        dy = p.y - y
        return dx * dx + dy * dy

    def __len__(self):
        return self._len

    def __iter__(self):
        self._xit = iter(self.xmap)
        return self

    def __next__(self):
        if self._yit is None:
            x = next(self._xit)
            self._ymap = self.xmap[x]
            self._yit = iter(self._ymap)
        try:
            y = next(self._yit)
            return self._ymap[y]
        except StopIteration:
            self._yit = None
            return self.__next__()

    def insert(self, point, ref):
        point_x = point[0]
        point_y = point[1]
        if point_x in self.xmap:
            ymap = self.xmap[point_x]
            if point_y in ymap:
                ymap[point_y].add(ref)
            else:
                ymap.update([(point_y, set([ref]))])
                self._len += 1
        else:
            self.xmap.update([(point_x, SortedDict({ point_y: set([ref]) }))])
            self._len += 1

    def remove(self, point, ref):
        point_x = point[0]
        point_y = point[1]
        if point_x in self.xmap:
            ymap = self.xmap[point_x]
            if point_y in ymap:
                refs = ymap[point_y]
                try:
                    refs.remove(ref)
                    if len(refs) == 0:
                        del ymap[point_y]
                        self._len -= 1
                except KeyError as e:
                    raise IndexError('ref does not exist for point') from e
                return
        raise IndexError('point does not exist')

    # removes the point and all references associated to it
    def remove_set(self, point):
        point_x = point[0]
        point_y = point[1]
        if point_x in self.xmap:
            ymap = self.xmap[point_x]
            if point_y in ymap:
                del ymap[point_y]
                self._len -= 1
                return
        raise IndexError('point does not exist')

    # traverses all points/sets and removes all occurances of ref. Warning: slow
    def remove_ref(self, ref):
        for ymap in self.xmap.values():
            del_refs = []
            for point_y, refs in ymap.items():
                try:
                    refs.remove(ref)
                    if len(refs) == 0:
                        del_refs.append(point_y)
                except KeyError:
                    pass
            for point_y in del_refs:
                del ymap[point_y]
                self._len -= 1

    def find_nearest_within(self, point, distance, exclude_self = False):
        if len(self.xmap) == 0:
            return distance + 1, None, None
        point_x = point[0]
        point_y = point[1]
        xit = self.xmap.irange(point_x - distance, point_x + distance)
        distance_sq = distance * distance
        min_dist = distance_sq + 1
        min_x = None # init for dumb pylint
        min_y = None # init for dumb pylint
        min_ymap = None # init for dumb pylint
        for x in xit:
            ymap = self.xmap[x]
            yit = ymap.irange(point_y - distance, point_y + distance)
            for y in yit:
                if exclude_self and point_x == x and point_y == y:
                    continue
                dist = self._calc_dist_sq(point, x, y)
                if  dist < min_dist:
                    min_dist = dist
                    min_ymap = ymap
                    min_x = x
                    min_y = y
        if min_dist > distance_sq:
            return distance + 1, None, None
        return math.sqrt(min_dist), Point(min_x, min_y), min_ymap[min_y]

    def __contains__(self, point):
        if not point[0] in self.xmap:
            return False
        ymap = self.xmap[point[0]]
        return point[1] in ymap

    def __getitem__(self, point):
        if point[0] in self.xmap:
            ymap = self.xmap[point[0]]
            if point[1] in ymap:
                return ymap[point[1]]
        raise IndexError('point does not exist')

    def find_all_within(self, point, distance):
        if len(self.xmap) == 0:
            return set()
        point_x = point[0]
        point_y = point[1]
        xit = self.xmap.irange(point_x - distance, point_x + distance)
        refs = set()
        for x in xit:
            ymap = self.xmap[x]
            yit = ymap.irange(point_y - distance, point_y + distance)
            for y in yit:
                for ref in ymap[y]:
                    refs.add(ref)
        return refs

    def find_all_within_list(self, point, distance):
        if len(self.xmap) == 0:
            return []
        point_x = point[0]
        point_y = point[1]
        xit = self.xmap.irange(point_x - distance, point_x + distance)
        point_list = []
        for x in xit:
            ymap = self.xmap[x]
            yit = ymap.irange(point_y - distance, point_y + distance)
            for y in yit:
                refs = ymap[y]
                point_list.append((Point(x, y), refs))
        return point_list
