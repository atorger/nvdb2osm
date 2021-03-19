import logging

from geometry_basics import *
from twodimsearch import TwoDimSearch

_log = logging.getLogger("geometry")


def snap_to_closest_way(ways, point):
    if len(ways) == 0:
        return None, None, None
    min_p = (None, None, None)
    for w in ways:
        for idx, p in enumerate(w.way):
            # to not miss snapping if there are sharp corners we need to check also the waypoints
            dist = dist2dsq(p, point)
            if min_p[0] is None or dist < min_p[0]:
                min_p = (dist, p, w)
            if idx > 0:
                lp = snap_to_line(point, w.way[idx-1], p)
                if lp is not None:
                    dist = dist2dsq(lp, point)
                    if min_p[0] is None or dist < min_p[0]:
                        min_p = (dist, lp, w)
    return math.sqrt(min_p[0]), min_p[1], min_p[2]

class GeometrySearch:

    def __init__(self, max_segment_length, use_dist=False, perform_self_testing=False):
        self._maxseglen = max_segment_length
        self._fillpoints = TwoDimSearch()
        self._realpoints = TwoDimSearch()
        self._self_cross_points = {}
        self._rlid2startdist = {}
        self._use_dist = use_dist
        self._perform_self_testing = perform_self_testing

    def insert(self, way):
        it = iter(way.way)
        first = next(it)
        prev = first
        if self._use_dist:
            self_points = {prev}
            prev.dist = self._rlid2startdist.get(way.rlid, 0)
        self._realpoints.insert(prev, way)
        for p in it:
            self._realpoints.insert(p, way)
            if self._use_dist:
                if p in self_points and (p != way.way[0] or way.way[-1] != way.way[0]): # exclude closed loop case
                    _log.info("Self-crossing point")
                    if p in self._self_cross_points:
                        self._self_cross_points[p].add(way)
                    else:
                        self._self_cross_points[p] = {way}
                if p.dist != -1:
                    _log.error(f"{way.way}")
                    _log.error(f"{way}")
                    raise RuntimeError("Expected way to not have set dist on points %s")
                self_points.add(p)
                p.dist = prev.dist + dist2d(prev, p)
            line_length = dist2d(prev, p)
            if line_length >= self._maxseglen:
                seg_count = math.ceil(line_length / self._maxseglen)
                x_delta = (p.x - prev.x) / float(seg_count)
                y_delta = (p.y - prev.y) / float(seg_count)
                for i in range(1, seg_count):
                    self._fillpoints.insert(Point(prev.x + i * x_delta, prev.y + i * y_delta), way)
            prev = p
        #print(len(self._realpoints), len(self._fillpoints))

        # rlid2startdist makes sure that if we have multiple segments per RLID the dist doesn't overlap
        if self._use_dist:
            self._rlid2startdist[way.rlid] = math.ceil(way.way[-1].dist) + 1

    def insert_waydb(self, way_db):
        for ways in way_db.values():
            for way in ways:
                self.insert(way)

    def _snap_point_to_line(self, point, rlid=None):
        ways = self._realpoints.find_all_within(point, self._maxseglen)
        if rlid is None:
            ways.update(self._fillpoints.find_all_within(point, self._maxseglen))
            return snap_to_closest_way(ways, point)

        # Only snap to specified RLID
        ref_ways = self._filter_reference_way(ways, rlid, allow_multiple_copies=True)
        if len(ref_ways) == 0:
            ways = self._fillpoints.find_all_within(point, self._maxseglen)
            ref_ways = self._filter_reference_way(ways, rlid, allow_multiple_copies=True)
        return snap_to_closest_way(ref_ways, point)

    def _insert_point_into_geometry(self, point, way, min_distance):
        if self._perform_self_testing:
            self._test_way_dist(way)
        for idx, p in enumerate(way.way):
            if idx == 0:
                continue
            prev = way.way[idx-1]
            is_between, _ = point_between_points(point, prev, p, 1e-5)
            if not is_between:
                continue
            dist1 = dist2d(prev, point)
            dist2 = dist2d(p, point)
            if dist1 >= min_distance and dist2 >= min_distance:
                point.dist = prev.dist + dist1
                way.way.insert(idx, point)
                if self._perform_self_testing:
                    self._test_way_dist(way)
                self._realpoints.insert(point, way)
                return point
            if dist1 < dist2:
                return prev
            return p

        raise RuntimeError(f"Insertion point not found for {way.rlid} {point}")

    def snap_point_into_geometry(self, point, realpoint_snap_distance, max_snap_distance):
        dist, p, _ = self._realpoints.find_nearest_within(point, realpoint_snap_distance)
        if p is not None:
            return dist, p, None
        dist, p, way = self._snap_point_to_line(point)
        if p is not None and dist < max_snap_distance:
            p = self._insert_point_into_geometry(p, way, realpoint_snap_distance)
            return dist, p, way
        return self._maxseglen + 1, None, None

    def _find_nearest_within_while_preferring_increased_length(self, way, way_idx, realpoint_snap_distance):

        # snap to closest point that doesn't shorten the segment length (if possible)

        point = way.way[way_idx]
        if 0 < way_idx < len(way.way) - 1:
            # not at and endpoint, we can make normal snapping
            dist, p, ways = self._realpoints.find_nearest_within(point, realpoint_snap_distance)
            ref_way = None
            if p is not None:
                ref_way = self._filter_reference_way(ways, way.rlid)
            return p, ref_way

        # we must check all points within range
        point_list = self._realpoints.find_all_within_list(point, realpoint_snap_distance)

        # filter out geometry with the matching rlid
        filtered_point_list = []
        for pp in point_list:
            ref_way = self._filter_reference_way(pp[1], way.rlid)
            if ref_way is not None:
                filtered_point_list.append(pp)
        point_list = filtered_point_list

        if way_idx == 0:
            neighbor_point = way.way[1]
        else:
            neighbor_point = way.way[way_idx-1]

        # we would prefer not to shorten orig_dist, if possible
        orig_dist = dist2dsq(point, neighbor_point)

        min_dev_dist = realpoint_snap_distance + 1
        min_dev_dist2 = realpoint_snap_distance + 1
        best_pp = None
        best_pp2 = None
        for pp in point_list:
            dist = dist2dsq(pp[0], neighbor_point)
            dev_dist = dist2dsq(pp[0], point)
            if dist >= orig_dist:
                if dev_dist < min_dev_dist:
                    min_dev_dist = dev_dist
                    best_pp = pp
            elif dev_dist < min_dev_dist2:
                min_dev_dist2 = dev_dist
                best_pp2 = pp
        if best_pp is None and best_pp2 is not None:
            #print("Had to select point that shortened way", point_list)
            best_pp = best_pp2
        elif best_pp is not None and min_dev_dist > min_dev_dist2:
            # FIXME this case seems to never happen, probably due to working with snapped geometry?
            pass

        if best_pp is not None:
            return best_pp[0], self._filter_reference_way(best_pp[1], way.rlid)

        return None, None

    def snap_waypoint_into_geometry(self, way, way_idx, realpoint_snap_distance, max_snap_distance, build_way=None):
        assert self._use_dist
        p, ref_way = self._find_nearest_within_while_preferring_increased_length(way, way_idx, realpoint_snap_distance)
        point = way.way[way_idx]
        if p is not None and ref_way is not None:
            for p1 in ref_way.way:
                if p1 == p:
                    p.dist = p1.dist
                    if build_way is not None and len(build_way) > 0 and p in self._self_cross_points:
                        bdist = build_way[-1].dist
                        if bdist > p1.dist:
                            p.dist = -1
                    if p.dist >= 0:
                        break
            assert (p.dist >= 0), "point not found in ref_way"
            return p, ref_way
        dist, p, ref_way = self._snap_point_to_line(point, way.rlid)
        if p is not None and dist < max_snap_distance:
            assert ref_way.rlid == way.rlid
            point = self._insert_point_into_geometry(p, ref_way, realpoint_snap_distance)
            return point, ref_way
        return None, None

    # this function is not efficient, but not meant to be used often
    def extend_geometry(self, ref_way, ext_way, update_dist_segs):
        _log.debug("Extend geometry")
        _log.debug(f"update_dist_segs: {update_dist_segs}")
        _log.debug(f"ref_way: {ref_way.way}")
        _log.debug(f"ext_way: {ext_way}")
        if ext_way[0] == ref_way.way[-1]:
            ref_way.way += ext_way[1:]
        elif ext_way[-1] == ref_way.way[0]:
            ref_way.way = ext_way[:-1] + ref_way.way
        elif snap_to_line(ref_way.way[-1], ext_way[0], ext_way[1]) is not None:
            ref_way.way += ext_way[1:]
        elif snap_to_line(ref_way.way[0], ext_way[-2], ext_way[-1]) is not None:
            ref_way.way = ext_way[:-1] + ref_way.way
        else:
            _log.debug("Extension does not connect to reference")
            return False

        update_set = set()
        for ref_set in self._realpoints:
            for w in ref_set:
                if w.rlid == ref_way.rlid:
                    update_set.add(w)
        _log.debug(f"Update set: {update_set}")
        update_map = {}
        if self._use_dist:
            del self._rlid2startdist[ref_way.rlid]
            for seg in update_dist_segs:
                for idx, p in enumerate(seg.way):
                    for w in update_set:
                        for p1 in w.way:
                            if p1 == p and p1.dist == p.dist:
                                update_map[(seg, idx)] = p1
        _log.debug(f"Update map: {update_map}")
        for w in update_set:
            for p in w.way:
                p.dist = -1
            self.insert(w)
        for k, p in update_map.items():
            seg = k[0]
            idx = k[1]
            assert p.dist != -1
            if seg.way[idx].dist != p.dist:
                _log.debug(f"dist {seg.way[idx].dist} => {p.dist}")
            else:
                _log.debug(f"no change in dist {p.dist}")
            seg.way[idx].dist = p.dist
        return True

    def _test_way_dist(self, way):
        assert self._use_dist
        it = iter(way.way)
        prev = next(it)
        ref_dist = way.way[0].dist
        assert ref_dist >= 0
        for p in it:
            if prev == p:
                _log.error(f"way.way: {way.way}")
                _log.error(f"way: {way}")
                raise RuntimeError("Duplicate point %s" % p)
            dist = dist2d(prev, p)
            if dist < 0.05:
                _log.error(f"way.way: {way.way}")
                _log.error(f"way: {way}")
                raise RuntimeError("Point closer placed than snap distance at %s in ref_way %s" % (p, dist))
            ref_dist += dist
            if abs(p.dist - ref_dist) > 1e-6:
                _log.error(f"way.way: {way.way}")
                _log.error(f"way: {way}")
                raise RuntimeError("Bad dist in ref_way %s (expected %s got %s)" % (p, ref_dist, p.dist))
            ref_dist = p.dist
            prev = p

    def find_all_nearby_ways(self, point_or_list_of_points):
        if isinstance(point_or_list_of_points, list):
            points = point_or_list_of_points
        else:
            points = [ point_or_list_of_points ]
        ways = set()
        for point in points:
            ways.update(self._realpoints.find_all_within(point, self._maxseglen))
            ways.update(self._fillpoints.find_all_within(point, self._maxseglen))
        return ways

    @staticmethod
    def _filter_reference_way(ref_set, rlid, allow_multiple_copies=False):
        if ref_set is None:
            raise RuntimeError("Empty reference set for RLID %s" % rlid)
        ref_ways = [w for w in ref_set if w.rlid == rlid]
        if allow_multiple_copies:
            return ref_ways
        if len(ref_ways) == 0:
            return None
        assert (len(ref_ways) == 1), "Multiple copies of RLID %s in reference geometry" % rlid
        return ref_ways[0]

    def find_reference_way(self, point, rlid):
        return self._filter_reference_way(self.find_all_connecting_ways(point), rlid)

    def find_all_connecting_ways(self, point_or_list_of_points):
        if isinstance(point_or_list_of_points, list):
            ways = set()
            for point in point_or_list_of_points:
                if point in self._realpoints:
                    ways.update(self._realpoints[point])
            return ways
        point = point_or_list_of_points
        if not point in self._realpoints:
            return set()
        return self._realpoints[point]

    def find_crossing_ways(self, way, abort_at_first=False):
        ways = set()
        for p in way.way:
            ways.update(self._realpoints.find_all_within(p, self._maxseglen))
            ways.update(self._fillpoints.find_all_within(p, self._maxseglen))
        crossing = []
        for w in ways:
            if w == way:
                continue
            it = iter(w.way)
            prev = next(it)
            for p in it:
                it1 = iter(way.way)
                prev1 = next(it1)
                match = False
                for p1 in it1:
                    cp = line_intersection(p1, prev1, p, prev)
                    if cp is not None:
                        match = True
                        crossing.append((w, cp))
                        if abort_at_first:
                            return crossing
                        break
                    prev1 = p1
                if match:
                    break
                prev = p
        return crossing

    @staticmethod
    def _endpoint_in_ways(point, ways):
        endpoint_count = 0
        for w in ways:
            if point in (w.way[0], w.way[-1]):
                endpoint_count += 1
        return endpoint_count

    def find_crossing_points_within(self, point, distance):
        points = self._realpoints.find_all_within_list(point, distance)
        rl = []
        for pl in points:
            if len(pl[1]) == 1:
                continue
            crossing_lines = len(pl[1])
            endpoint_count = self._endpoint_in_ways(pl[0], pl[1])
            if (endpoint_count % 2) != 0:
                endpoint_count -= 1 # T-crossing
            crossing_lines -= endpoint_count / 2
            if crossing_lines > 1:
                rl.append(pl)
        return rl
