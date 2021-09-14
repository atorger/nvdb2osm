import logging
from functools import cmp_to_key

from twodimsearch import TwoDimSearch
from geometry_search import GeometrySearch
from geometry_basics import *
from merge_tags import merge_tags
from proj_xy import latlon_str
from shapely_utils import *
from nseg_tools import *
from osmxml import *

GEO_FILL_LENGTH = 50

_log = logging.getLogger("waydb")

# join_ways()
#
# Join ways that have matching endpoints. We also update the STARTAVST/SLUTAVST and
# NVDB tags for debugging and gap resolving purposes
#
def join_ways(ways):
    if len(ways) == 1:
        return ways

    # Due to snapping some very short segments can be zero length, sort to make sure
    # we go through in order, otherwise we can miss to include the zero length segments
    def startavst(w):
        return w.tags["STARTAVST"]
    ways.sort(key=startavst)

    w1 = ways.pop(0)
    ways_out = [ w1 ]
    if w1.way[0] == w1.way[-1]:
        # only okay if all are the same
        for p in w1.way[1:]:
            if p != w1.way[0]:
                _log.error(f"w1 {w1}")
                _log.error(f"w1.way {w1.way}")
                raise RuntimeError("Closed way not expected here")
    while len(ways) > 0:
        match = False
        for idx, w2 in enumerate(ways):
            if w1.way[-1] == w2.way[0]:
                w1.way += w2.way[1:]
                w1.tags["SLUTAVST"] = w2.tags["SLUTAVST"]
                match = True
                del ways[idx]
                break
            if w1.way[0] == w2.way[-1]:
                w1.way = w2.way[:-1] + w1.way
                w1.tags["STARTAVST"] = w2.tags["STARTAVST"]
                match = True
                del ways[idx]
                break
        if not match:
            # In some cases RLID is split in disconnected ways
            w1 = ways.pop(0)
            ways_out.append(w1)
    return ways_out

# remove_short_segments_and_redundant_points()
#
# Remove segments shorter than 'min_seg_len' unless the point is endpoint or in the
# 'point_keepers' set. If the whole way is shorter than minimum segment it's reduced
# to one point
#
def remove_short_segments_and_redundant_points(way1, min_seg_len, point_keepers=None):
    way = way1.way
    dsq = min_seg_len * min_seg_len
    new_way = []
    if point_keepers is None:
        point_keepers = set()
    for idx, p in enumerate(way):
        if idx == 0:
            new_way.append(p)
            may_remove = False
        elif p == new_way[-1]:
            pass # duplicate
        elif p in point_keepers or idx == len(way) - 1:
            if dist2dsq(new_way[-1], p) < dsq:
                if not may_remove:
                    if new_way[-1] == way[0] and p == way[-1]:
                        # special case with two closely spaced points
                        if not way[-1] in point_keepers:
                            return [ way[0] ]
                        if not way[0] in point_keepers:
                            return [ way[-1] ]
                    _log.error(f"RLID {way1.rlid} {way1.tags}")
                    _log.error(f"way {way}")
                    _log.error(f"new_way {new_way}")
                    raise RuntimeError("Keeper points closer than minimum segment length %s < %s" % (dist2d(new_way[-1], p), min_seg_len))
                del new_way[-1]
            new_way.append(p)
            may_remove = False
        elif dist2dsq(new_way[-1], p) >= dsq:
            new_way.append(p)
            may_remove = True
    if len(new_way) == len(way):
        return way
    return new_way

def copy_way(way):
    new_way = []
    for p in way:
        new_way.append(Point(p.x, p.y))
    return new_way

def join_ways_using_nvdb_tags(ways, snap_dist):
    if len(ways) == 1:
        return ways

    def compare_avst(w1, w2):
        res = w1.tags["STARTAVST"] - w2.tags["STARTAVST"]
        if res == 0:
            res = w1.tags["SLUTAVST"] - w2.tags["SLUTAVST"]
        if res < 0:
            return -1
        if res > 0:
            return 1
        return 0

    ways.sort(key=cmp_to_key(compare_avst))
    new_ways = []
    it = iter(ways)
    pw = next(it)
    for w in it:
        if pw.tags["SLUTAVST"] < w.tags["STARTAVST"]:
            # there's a gap between 'pw' and 'w', keep both
            new_ways.append(pw)
        elif pw.tags["SLUTAVST"] == w.tags["STARTAVST"]:
            # perfect join, extend 'pw' with 'w'
            w.tags["STARTAVST"] = pw.tags["STARTAVST"]
            w.way = pw.way + w.way # we probably add a double point here, removed elsewhere
        elif pw.tags["SLUTAVST"] >= w.tags["SLUTAVST"]:
            # 'pw' spans the whole of 'w', discard 'w'
            w = pw
        else:
            # partial overlap

            # figure out how much of 'pw' that is before 'w' starts, and store to 'nw'
            gs = GeometrySearch(10)
            gs.insert(w)
            nw = []
            for p in pw.way:
                _, p1, _ = gs.snap_point_into_geometry(p, snap_dist, snap_dist)
                if p1 is None:
                    nw.append(p)
                else:
                    break
            w.tags["STARTAVST"] = pw.tags["STARTAVST"]
            w.way = nw + w.way
        pw = w
    new_ways += [ pw ]
    return new_ways

# join_Reflinjetillkomst_gaps()
#
# With the data source NVDB-Reflinjetillkomst some gaps in RLID segment that should be a
# single segment has been observed (rare). This function tries to identify that and join the ways
# if needed.
#
# Note that even if segments are joined incorrectly, if the actual data layers doesn't contain any
# data in the joined segment it will not turn up in the map, so better join one too many than one
# too few.
#
def join_Reflinjetillkomst_gaps(ways):

    if len(ways) == 1:
        return ways

    def startavst(w):
        return w.tags["STARTAVST"]

    ways.sort(key=startavst)
    i = 0
    while i + 1 < len(ways):
        dist = dist2d(ways[i+0].way[-1], ways[i+1].way[0])
        # previous max gap was 1.0, but 2.4 meter gap was observed in Falun dataset,
        # and then 3.4 meters in Kil dataset, and 8.6 meters in Piteå.
        #
        # Any false joins are not too bad as it won't join the data layers on top.
        if dist < 10:
            avst_diff = ways[i+1].tags["STARTAVST"] - ways[i+0].tags["SLUTAVST"]
            _log.warning(f"a suspiciously small gap was found in RLID {ways[i].rlid} ({dist}m), segments where joined (AVST diff {avst_diff}m)")
            ways[i+1].way = ways[i].way + ways[i+1].way
            del ways[i]
        else:
            i += 1
    return ways

# remove_Reflinjetillkomst_overlaps
#
# In rare occassions overlaps have been observed in the NVDB ref layer. This function cleans it up.
#
def remove_Reflinjetillkomst_overlaps(ways, snap_dist):

    if len(ways) == 1:
        return ways

    # remove segments that have been snapped to zero length
    filtered_ways = []
    for w in ways:
        if w.way[0] != w.way[-1]:
            filtered_ways.append(w)
        else:
            all_same = True
            for p in w.way[1:]:
                if p != w.way[0]:
                    all_same = False
                    break
            if not all_same:
                filtered_ways.append(w)
    ways = filtered_ways

    if len(ways) == 1:
        return ways

    def startavst(w):
        return w.tags["STARTAVST"]

    ways.sort(key=startavst)

    has_overlap = False
    prev_way = ways[0]
    for way in ways[1:]:
        if prev_way.tags["SLUTAVST"] > way.tags["STARTAVST"]:
            _log.warning(f"overlapping segment for RLID {way.rlid} ({prev_way.tags['SLUTAVST']} > {way.tags['STARTAVST']}).")
            has_overlap = True
            break
        prev_way = way
    if has_overlap:
        return join_ways_using_nvdb_tags(ways, snap_dist)
    return ways


# print_progress()
#
# print progress 10%...20%... etc
#
def print_progress(last_print, idx, data_len, progress_text="work"):
    if data_len <= 1:
        return last_print
    progress = int(100 * idx / (data_len-1))
    if progress % 10 == 0 and progress != last_print:
        last_print = progress
        _log.info(f"{progress_text}: {progress}%")
    return last_print


def test_self_connections(way):
    # this will not trigger a warning for connected endpoints (closed loop), as that is normal
    points = set()
    for i, p in enumerate(way.way):
        if p in points and (i != len(way.way) - 1 or p != way.way[0]):
            _log.warning(f"RLID {way.rlid} connects to itself at {latlon_str(p)}")
        points.add(p)


def extend_and_snap(way, is_start, snappoints, snappoints_extra, snap_dist, ext_dist):
    # get last line segment bast->tip and ignore duplicated points
    base = None
    if is_start:
        tip = way[0]
        for p in way[1:]:
            if p != tip:
                base = p
                break
    else:
        tip = way[-1]
        for p in reversed(way[:-1]):
            if p != tip:
                base = p
                break
    if base is None:
        return None, None, None

    # get list of all possible snapping points
    sp_list = snappoints.find_all_within_list(tip, ext_dist)
    sp_list += snappoints_extra.find_all_within_list(tip, ext_dist)
    if len(sp_list) == 0:
        return None, None, None

    assert base != tip
    dist = dist2d(base, tip)
    x_delta = (tip.x - base.x) / dist
    y_delta = (tip.y - base.y) / dist
    min_dist = snap_dist
    min_ext_dist = ext_dist
    result = None

    # go through all possible snapping points
    for sp in sp_list:
        p = sp[0]
        if p == tip:
            # self, skip
            continue
        tip_to_p = dist2d(tip, p)
        if tip_to_p >= ext_dist:
            # distance to candidate longer than max snap distance, skip
            continue
        ext_point = Point(tip.x + x_delta * tip_to_p, tip.y + y_delta * tip_to_p)
        ext_point_to_p = dist2d(ext_point, p)
        if ext_point_to_p > tip_to_p:
            # if this happens the candidate is behind the tip, skip
            continue
        dist = dist2d(p, ext_point)
        if dist >= min_dist:
            continue
        # calculate deviation angle from linear extension
        s1 = dist/2
        s2 = math.sqrt(dist2dsq(base, p) - s1 * s1)
        dev_angle = math.atan(s1/s2) * 180 / math.pi
        if dev_angle >= 1.0:
            # snapping to candidate causes too large change in angle
            continue
        min_dist = dist
        min_ext_dist = tip_to_p
        result = p
    return min_ext_dist, min_dist, result

# WayDatabase
#
# Memory database used to store and merge NVDB geometry.
# The code is somewhat generic, but does expect that the input data has some specific
# properties which NVDB data has.
#
class WayDatabase:

    POINT_SNAP_DISTANCE = 0.1
    MAX_SNAP_DISTANCE = 2
    EMERGENCY_SNAP_DISTANCE = 7

    def __init__(self, reference_geometry, perform_self_testing=True):

        _log.info("Setting up way database and cleaning reference geometry...")

        self.way_db = {}
        self.point_db = {}
        self.gs = None
        self._ref_gs = GeometrySearch(GEO_FILL_LENGTH, use_dist=True, perform_self_testing=perform_self_testing)
        self._ref_way_db = {}
        self._way_db_iter = None
        self._way_db_sub_iter = None
        self._perform_self_testing = perform_self_testing

        # Expected properties of 'reference_geometry':
        #
        # - All points in a ways that should be connected are close (within SNAP_POINT_DISTANCE)
        #   from a point in the connecting way, which is an endpoint
        # - No overlaps or duplicates
        # - There may be very short segments (cleaned up)
        # - Segments with the same RLID may sometimes be disconnected
        # - There may be closed ways (start and end point the same), but no self-crossing ways
        #
        # After processing:
        # - Any points closer than SNAP_POINT_DISTANCE have been merged to a single point
        # - Segments with same RLID has been connected to as long segments as possible
        # - Store in a GeometrySearch object with distance on each point
        #

        # group segments per RLID, and register all endpoints and midpoints (=non-endpoints) for searching
        rlid_ways = {}
        endpoints = TwoDimSearch()
        point_count = 0
        last_print = 0
        _log.info("Setting up endpoint 2D search data structures...")
        for idx, way in enumerate(reference_geometry):
            last_print = print_progress(last_print, idx, len(reference_geometry),
                                        progress_text="endpoint 2D search data structures")
            for ep in (way.way[0], way.way[-1]):
                endpoints.insert(ep, way)
            point_count += len(way.way)
            if way.rlid in rlid_ways:
                rlid_ways[way.rlid].append(way)
            else:
                rlid_ways[way.rlid] = [way]
        _log.info(f"({len(endpoints)} endpoints of {point_count} total points)")

        _log.info("Snap points to nearby endpoints.")
        # Due to snapping we may introduce duplicate points in the ways, which is ok as we
        # remove them later.
        ep_count, mp_count = self._snap_points_to_nearby_endpoints(rlid_ways, endpoints)
        _log.info(f"done (snapped {ep_count} endpoints and {mp_count} midpoints)")

        # In rare cases Reflinjetillkomst has lines cut short, we try to connect those
        _log.info("Snap still unconnected endpoints to nearby points by extension...")
        ep_count = 0
        uc_count = 0
        second_pass = []
        midpoints = TwoDimSearch()
        for ways in rlid_ways.values():
            for way in ways:
                for mp in way.way[1:-1]:
                    midpoints.insert(mp, way)
        for ways in rlid_ways.values():
            for way in ways:
                if way.way[0] == way.way[-1]:
                    continue # makes no sense to extend-snap closed loops
                for way_idx in [ 0, -1 ]:
                    if len(endpoints[way.way[way_idx]]) > 1:
                        # already connected
                        continue
                    uc_count += 1
                    min_ext_dist, min_dev_dist, p = extend_and_snap(way.way, way_idx == 0, endpoints, midpoints, self.POINT_SNAP_DISTANCE, self.MAX_SNAP_DISTANCE)
                    if p is None:
                        continue
                    if min_dev_dist > 1e-5:
                        # keep very tight limit on first pass so we extend in the right order
                        second_pass.append(way)
                        continue
                    _log.info(f"extend snap ext:{min_ext_dist:g} dev:{min_dev_dist:g} for RLID {way.rlid}"
                              f" at {latlon_str(p)}")
                    endpoints.remove(way.way[way_idx], way) # must be removed before midpoint test below so we don't snap to ourself
                    if p in midpoints:
                        # for midpoints it may be better to snap to an endpoint instead
                        p = self._snap_to_nearby_point(p, endpoints, self.MAX_SNAP_DISTANCE)
                    endpoints.insert(p, way)
                    way.way[way_idx] = Point(p.x, p.y)
                    ep_count += 1

        for way in second_pass:
            for way_idx in [ 0, -1 ]:
                if len(endpoints[way.way[way_idx]]) > 1:
                    continue
                min_ext_dist, min_dev_dist, p = extend_and_snap(way.way, way_idx == 0, endpoints, midpoints, self.POINT_SNAP_DISTANCE, self.MAX_SNAP_DISTANCE)
                if p is None:
                    continue
                _log.info(f"extend snap ext:{min_ext_dist:g} dev:{min_dev_dist:g} for RLID {way.rlid} at {latlon_str(p)}")
                endpoints.remove(way.way[way_idx], way)
                if p in midpoints:
                    p = self._snap_to_nearby_point(p, endpoints, self.MAX_SNAP_DISTANCE)
                endpoints.insert(p, way)
                way.way[way_idx] = Point(p.x, p.y)
                ep_count += 1

        _log.info(f"done (snapped {ep_count} endpoints, {uc_count - ep_count} still unconnected)")
        if ep_count > 0:
            _log.warning("extend snaps typically means that there are gaps in the data source's geometry")

        if self._perform_self_testing:
            for ways in rlid_ways.values():
                for way in ways:
                    for ep in [ way.way[0], way.way[-1] ]:
                        dist, new_point, _ = endpoints.find_nearest_within(ep, self.POINT_SNAP_DISTANCE, exclude_self=True)
                        if new_point is not None:
                            _log.error(f"endpoints placed too closely together: {dist}, {ep}, {new_point}")
                            raise RuntimeError("endpoints placed too closely together")

        _log.info("Join segments with same RLID and insert to search data structure...")
        self._insert_into_reference_geometry(rlid_ways, endpoints)
        _log.info("done")

    def __iter__(self):
        self._way_db_iter = iter(self.way_db.values())
        self._way_db_sub_iter = None
        return self

    def __next__(self):
        if self._way_db_sub_iter is None:
            ways = next(self._way_db_iter) # when StopIteration is raised iteration is complete
            self._way_db_sub_iter = iter(ways)
        try:
            way = next(self._way_db_sub_iter)
            return way
        except StopIteration:
            self._way_db_sub_iter = None
            return self.__next__()


    @staticmethod
    def _snap_to_nearby_point(p, snappoints, snap_distance):
        _, snap, _ = snappoints.find_nearest_within(p, snap_distance, exclude_self=True)
        if snap is None:
            return p
        return snap

    def _snap_points_to_nearby_endpoints(self, rlid_ways, endpoints):
        ep_count = 0
        mp_count = 0
        midpoints = []
        prev_count = -1
        pass_count = 0
        while pass_count < 2 or prev_count != ep_count + mp_count:
            snapped_points = set()
            prev_count = ep_count + mp_count
            if pass_count == 0:
                # snap really close one first to make sure we don't make a unnecessarily long snap
                snap_distance = 0.001
            else:
                snap_distance = self.POINT_SNAP_DISTANCE

            for ways in rlid_ways.values():
                for way in ways:
                    for way_idx in range(0, len(way.way)):
                        is_midpoint = way_idx not in (0, len(way.way) - 1)
                        ep_list = endpoints.find_all_within_list(way.way[way_idx], snap_distance)
                        if len(ep_list) == 0:
                            # the own endpoint is expected to exist in endpoints set
                            assert is_midpoint
                            continue
                        if len(ep_list) == 1 and not is_midpoint:
                            assert ep_list[0][0] == way.way[way_idx]
                            continue

                        new_point = ep_list[0][0]
                        if pass_count == 0:
                            # first pass we can pick any point due to short snap distance
                            snapped_points.add(new_point)
                        else:
                            # prefer to snap to a point already snapped
                            for ep in ep_list:
                                if ep[0] in snapped_points:
                                    new_point = ep[0]
                                    break

                        # move all the nearby endpoints to the point we have chosen for snapping (new_point)
                        for ep in ep_list:
                            old_point = ep[0]
                            if old_point == new_point:
                                continue
                            ep_set = ep[1]
                            endpoints.remove_set(old_point)
                            for w in ep_set:
                                if w.way[0] == old_point:
                                    w.way[0] = Point(new_point.x, new_point.y)
                                if w.way[-1] == old_point:
                                    w.way[-1] = Point(new_point.x, new_point.y)
                                assert new_point in (w.way[0], w.way[-1])
                                ep_count += 1
                                endpoints.insert(new_point, w)

                        midpoints.append((way_idx, way))
                        if way.way[way_idx] != new_point:
                            assert is_midpoint
                            way.way[way_idx] = Point(new_point.x, new_point.y)
                            mp_count += 1
            _log.debug(f"snap_counts {mp_count} {ep_count}")
            pass_count += 1

        # also add connected midpoints, we need to do it here afterwards to not disturb the multiple pass endpoint snapping
        # FIXME: modifying contents and meaning of endpoints is a hard-to-follow side effect
        for mp in midpoints:
            idx = mp[0]
            way = mp[1]
            endpoints.insert(way.way[idx], way)

        return ep_count, mp_count

    def _insert_into_reference_geometry(self, rlid_ways, endpoints):
        last_print = 0
        for idx, ways in enumerate(rlid_ways.values()):
            if len(rlid_ways) > 50:
                last_print = print_progress(last_print, idx, len(rlid_ways), progress_text="Join segments")
            # make longest possible ways of RLID segments
            joined_ways = join_ways(ways)
            joined_ways = join_Reflinjetillkomst_gaps(joined_ways)
            joined_ways = remove_Reflinjetillkomst_overlaps(joined_ways, self.POINT_SNAP_DISTANCE)
            for way in joined_ways:
                # very short segments lead to problems with snapping (can cause gaps where there should not be any)
                new_way = remove_short_segments_and_redundant_points(way, self.POINT_SNAP_DISTANCE, endpoints)
                if len(new_way) < 2:
                    _log.debug(f"Skipping zero length segment for {way.rlid}")
                    continue
                assert new_way[0] == way.way[0] and new_way[-1] == way.way[-1]
                way.way = new_way
                test_self_connections(way)
                if self._perform_self_testing:
                    self._test_way_dist(way, allow_unset=True)

                self._ref_gs.insert(way)
                self._test_way_dist(self._ref_gs.find_reference_way(way.way[0], way.rlid))
                if way.rlid in self._ref_way_db:
                    self._ref_way_db[way.rlid].append(way)
                else:
                    self._ref_way_db[way.rlid] = [ way ]

    def get_reference_geometry(self):
        ref_ways = []
        for ways in self._ref_way_db.values():
            for way in ways:
                ref_ways.append(way)
        return ref_ways

    def insert_missing_reference_geometry_if_any(self, geometry_ways):
        missing_ways = {}
        for way in geometry_ways:
            if not way.rlid in self._ref_way_db:
                wc = way.make_copy_new_way(copy_way(way.way))
                if way.rlid in missing_ways:
                    missing_ways[way.rlid].append(wc)
                else:
                    missing_ways[way.rlid] = [ wc ]

        if len(missing_ways) == 0:
            return False

        # snap endpoints to self
        endpoints = TwoDimSearch()
        rlids = []
        for ways in list(missing_ways.values()):

            # this type of geometry may have overlaps, so we pre-join using NVDB tags
            ways = join_ways_using_nvdb_tags(ways, self.POINT_SNAP_DISTANCE)
            missing_ways[ways[0].rlid] = ways
            rlids.append(ways[0].rlid)
            for way in ways:
                for ep in [ way.way[0], way.way[-1] ]:
                    endpoints.insert(ep, way)
        self._snap_points_to_nearby_endpoints(missing_ways, endpoints)
        self._insert_into_reference_geometry(missing_ways, endpoints)

        # Missing segments may be missing because they have been snapped to zero and thus excluded.
        # If that is the case they won't be reinserted either, so we only log after the insertion
        # we we know if any actually got in.
        did_insert = False
        for rlid in rlids:
            if rlid in self._ref_way_db:
                _log.warning(f"RLID {rlid} was not in reference geometry, inserted it.")
                did_insert = True
        return did_insert

    def insert_rlid_node(self, node, data_src_name, do_snap=True):
        did_snap = False
        if do_snap:
            dist, p, snap_way = self._ref_gs.snap_point_into_geometry(node.way, self.POINT_SNAP_DISTANCE, self.MAX_SNAP_DISTANCE)
            if p is None:
                _log.warning(f"node with RLID {node.rlid} {latlon_str(node.way)} in {data_src_name} has no"
                             f" existing geometry within {self.MAX_SNAP_DISTANCE} meters")
            else:
                did_snap = True
                if dist > self.POINT_SNAP_DISTANCE:
                    _log.info("Node %s snap distance %s", node.rlid, dist)
                node.way.x = p[0]
                node.way.y = p[1]
        if node.way in self.point_db:
            current = self.point_db[node.way][0]
            if current.rlid != node.rlid:
                # This can happen for some data in crossings for example
                #raise RuntimeError("Node with RLID %s and position %s already exists in the database (%s, %s)" % (node.rlid, latlon_str(node.way), current, node))
                _log.warning(f"Node with RLID {node.rlid} and position {latlon_str(node.way)} already"
                                f" exists in the database ({current}, {node})")
            merge_tags(current, node.tags, data_src_name)
        else:
            self.point_db[node.way] = [ node ]

        if do_snap and snap_way is not None:
            self._add_node_into_way(snap_way.rlid, p)
        return did_snap

    def _add_node_into_way(self, rlid, point):
        segs = self.way_db.get(rlid, [])
        for seg in segs:
            for idx, p in enumerate(seg.way):
                if idx == 0:
                    continue
                is_between, _ = point_between_points(point, seg.way[idx-1], p, 1e-6)
                if is_between:
                    point.dist = seg.way[idx-1].dist + dist2d(seg.way[idx-1], point)
                    seg.way.insert(idx, point)
                    return
        _log.warning(f"node {latlon_str(point)} not found in any way segment for RLID {rlid}")

    def _split_and_merge(self, way, data_src_name):

        if len(way.way) == 1:
            # skipping (extremely short) ways that were reduced to one point
            return

        if not way.rlid in self.way_db:
            # first segment for rlid
            self.way_db[way.rlid] = [ way ]
            return

        segs = self.way_db[way.rlid]
        if way.way[-1].dist <= segs[0].way[0].dist:
            # way is before existing segments
            segs.insert(0, way)
            return

        if way.way[0].dist >= segs[-1].way[-1].dist:
            # way is after existing segments
            segs.append(way)
            return

        segs_idx = 0
        while segs_idx < len(segs): # we modify segs inside, so can't use for loop
            seg = segs[segs_idx]
            if seg.way[-1].dist <= way.way[0].dist:
                # seg is before way
                segs_idx += 1
                continue

            if seg.way[0].dist >= way.way[-1].dist:
                # seg is after way, no overlap
                segs.insert(segs_idx, way)
                #print("insert no overlap")
                break

            # way starts somewhere inside seg, scan to start of way
            #print("way         ", way)
            #print("matching seg", seg)
            seg_idx = 0
            while seg_idx < len(seg.way):
                if seg.way[seg_idx].dist >= way.way[0].dist:
                    if seg.way[seg_idx].dist > way.way[0].dist:
                        # start of way is a new point, insert
                        seg.way.insert(seg_idx, way.way[0])
                    break
                seg_idx += 1

            if seg_idx > 0:
                # split out segment which is before way
                seg_copy = seg.make_copy_new_way(seg.way[:seg_idx+1])
                segs.insert(segs_idx, seg_copy)
                segs_idx += 1
                seg.way = seg.way[seg_idx:]
                #print("split before")

            # now seg starts at same point as way
            assert seg.way[0] == way.way[0]

            # way may have new points, insert those into seg, if any
            seg_idx = 0
            way_idx = 0
            while seg_idx < len(seg.way) and way_idx < len(way.way):
                if seg.way[seg_idx].dist > way.way[way_idx].dist:
                    seg.way.insert(seg_idx, way.way[way_idx])
                seg_idx += 1
                way_idx += 1

            if seg_idx < len(seg.way):
                # split out segment which is after way
                seg_copy = seg.make_copy_new_way(seg.way[seg_idx-1:])
                segs.insert(segs_idx + 1, seg_copy)
                seg.way = seg.way[:seg_idx]

            assert seg.way[0] == way.way[0]
            next_way = None
            if len(way.way) > len(seg.way):
                # split way
                next_way = way.make_copy_new_way(way.way[len(seg.way)-1:])
                way.way = way.way[:len(seg.way)]

            # merge tags
            assert seg.way[-1] == way.way[-1]
            assert seg.way[0] == way.way[0] and seg.way[-1] == way.way[-1]
            merge_tags(seg, way.tags, data_src_name)
            #print("insert with split")
            if next_way is None:
                break
            way = next_way
            if way.way[0].dist >= segs[-1].way[-1].dist:
                # special case when next_way is last
                segs.append(way)
                break

    def insert_rlid_way(self, way, data_src_name, debug_ways=None):
        if way.rlid not in self._ref_way_db:
            _log.debug(f"Skipping RLID {way.rlid} (not in reference geometry)")
            return

        _, ways = self._adapt_way_into_reference_geometry(way, data_src_name)
        for w in ways:
            if debug_ways is not None:
                debug_ways.append(w.make_copy_new_way(copy_way(w.way)))
            self._split_and_merge(w, data_src_name)

        if self._perform_self_testing:
            if way.rlid in self.way_db:
                self._test_segment(self.way_db[way.rlid])

    def _test_segment(self, segs):
        it = iter(segs)
        prev = next(it)
        for seg in it:
            if seg.way[0].dist < prev.way[-1].dist:
                raise RuntimeError("Bad order")
            prev = seg

        for seg in segs:
            assert len(seg.way) >= 2
            ref_way = self._ref_gs.find_reference_way(seg.way[0], seg.rlid)
            ref_idx = 0
            while ref_idx < len(ref_way.way) and ref_way.way[ref_idx] != seg.way[0]:
                ref_idx += 1
            assert ref_idx < len(ref_way.way)
            prev = None
            for p in seg.way:
                if prev is not None:
                    dist = dist2d(prev, p)
                    if dist < self.POINT_SNAP_DISTANCE:
                        _log.error(f"ref.way: {ref_way.way}")
                        _log.error(f"seg.way: {seg.way}")
                        _log.error(f"ref_way: {ref_way}")
                        _log.error(f"seg    : {seg}")
                        raise RuntimeError("Point closer placed than snap distance %s" % dist)
                if ref_idx == len(ref_way.way):
                    _log.error(f"ref.way: {ref_way.way}")
                    _log.error(f"seg.way: {seg.way}")
                    _log.error(f"ref_way: {ref_way}")
                    _log.error(f"seg    : {seg}")
                    raise RuntimeError("More points in segment than in reference way")
                if p.dist != ref_way.way[ref_idx].dist:
                    _log.error(f"ref.way: {ref_way.way}")
                    _log.error(f"seg.way: {seg.way}")
                    _log.error(f"ref_way: {ref_way}")
                    _log.error(f"seg    : {seg}")
                    raise RuntimeError("Dist mismatch got %s expected %s (ref_idx %s)" % (p.dist, ref_way.way[ref_idx].dist, ref_idx))
                ref_idx += 1
                prev = p

    def _test_way_dist(self, way, allow_unset=False):
        it = iter(way.way)
        prev = next(it)
        ref_dist = way.way[0].dist
        if allow_unset and ref_dist == -1:
            ref_dist = 0
        else:
            assert ref_dist >= 0
        for p in it:
            if prev == p:
                _log.info(f"{way.way}")
                _log.info(f"{way}")
                raise RuntimeError("Duplicate point %s" % p)
            dist = dist2d(prev, p)
            if dist < self.POINT_SNAP_DISTANCE:
                _log.info(f"{way.way}")
                _log.info(f"{way}")
                raise RuntimeError("Point closer placed than snap distance at %s in ref_way %s" % (p, dist))
            ref_dist += dist
            if (not allow_unset or p.dist != -1) and abs(p.dist - ref_dist) > 1e-6:
                _log.info(f"{way.way}")
                _log.info(f"{way}")
                raise RuntimeError("Bad dist in ref_way %s (expected %s got %s)" % (p, ref_dist, p.dist))
            if p.dist != -1:
                ref_dist = p.dist
            prev = p

    def _retry_adapt_way_extending_reference_geometry(self, way):
        # will not work for closed loops, or self-crossing stuff
        new_way = []
        snapped = []
        ref_way = None
        snap_count = 0
        for way_idx, point in enumerate(way.way):
            p, rway = self._ref_gs.snap_waypoint_into_geometry(way, way_idx, self.POINT_SNAP_DISTANCE, self.MAX_SNAP_DISTANCE)
            if p is not None:
                new_way.append(p)
                snapped.append(True)
                ref_way = rway
                snap_count += 1
            else:
                # snap to other way if possible, using short snap distance
                _, p, rway = self._ref_gs.snap_point_into_geometry(point, self.POINT_SNAP_DISTANCE, self.POINT_SNAP_DISTANCE)
                if p is not None:
                    new_way.append(p)
                else:
                    new_way.append(point)
                snapped.append(False) # only count points snap to self RLID
        if ref_way is None:
            _log.info(f"Way with RLID {way.rlid} could not be snapped to reference geometry")
            return False
        assert ref_way.rlid == way.rlid

        _log.info(f"must extend reference geometry for RLID {way.rlid} (only {snap_count} of {len(way.way)} points could be snapped)")
        first_snap = 0
        for idx, is_snap in enumerate(snapped):
            if is_snap:
                first_snap = idx
                break
        last_snap = len(new_way)
        for idx in range(0, len(snapped)):
            if snapped[len(snapped) - 1 - idx]:
                last_snap = len(snapped) - 1 - idx
                break
        _log.debug(f"snapped {snapped}")
        _log.debug(f"snappoints {first_snap} {last_snap}")
        for way_idx, point in enumerate(way.way):
            if way_idx <= first_snap or way_idx >= last_snap:
                continue
            if not snapped[way_idx]:
                # this means snap failure in the middle too not just an extension problem
                _log.info(f"Way with RLID {way.rlid} could not be snapped to reference geometry")
                return False
        extend_way_start = []
        extend_way_end = []
        for idx, point in enumerate(new_way):
            if idx < first_snap:
                extend_way_start.append(point)
            if idx > last_snap:
                extend_way_end.append(point)

        current_segs = self.way_db.get(way.rlid, [])
        if len(extend_way_start) > 0:
            extend_way_start.append(new_way[first_snap])
            if not self._ref_gs.extend_geometry(ref_way, extend_way_start, current_segs):
                return False

        if len(extend_way_end) > 0:
            extend_way_end.insert(0, new_way[last_snap])
            if not self._ref_gs.extend_geometry(ref_way, extend_way_end, current_segs):
                return False
        return True

    def _adapt_way_into_reference_geometry(self, way, data_src_name, is_retry=False):
        # first snap each point of the way into the existing geometry
        way.way = remove_short_segments_and_redundant_points(way, self.POINT_SNAP_DISTANCE)
        if len(way.way) == 1:
            _log.debug(f"RLID {way.rlid} reduced to one point")
            return None, [ way ]
        new_way = []
        prev = None
        max_snap_distance = self.MAX_SNAP_DISTANCE
        for way_idx, point in enumerate(way.way):
            p, ref_way = self._ref_gs.snap_waypoint_into_geometry(way, way_idx, self.POINT_SNAP_DISTANCE, max_snap_distance, new_way)
            if p is None:
                if is_retry:
                    _log.error(f"Way with RLID {way.rlid} {latlon_str(point)} has no existing geometry within {max_snap_distance} meters")
                    self._fix_after_failed_adapt_geometry_way_insert()
                    return None, []
                success = self._retry_adapt_way_extending_reference_geometry(way)
                if success:
                    return self._adapt_way_into_reference_geometry(way, data_src_name, is_retry=True)

                if max_snap_distance < self.EMERGENCY_SNAP_DISTANCE:
                    max_snap_distance = self.EMERGENCY_SNAP_DISTANCE
                    p, ref_way = self._ref_gs.snap_waypoint_into_geometry(way, way_idx, self.POINT_SNAP_DISTANCE, max_snap_distance, new_way)
                    if p is None:
                        _log.error(f"Way with RLID {way.rlid} {latlon_str(point)} has no existing geometry within {max_snap_distance} meters")
                        self._fix_after_failed_adapt_geometry_way_insert()
                        return None, []
                else:
                    _log.error(f"Failed to adapt geometry of way with RLID {way.rlid} at {latlon_str(point)}")
                    self._fix_after_failed_adapt_geometry_way_insert()
                    return None, []

            if self._perform_self_testing:
                self._test_way_dist(ref_way)
            if p != prev:
                # sometimes close points are merged to the same position
                assert p.dist >= 0
                new_way.append(p)
            prev = p

        if max_snap_distance == self.EMERGENCY_SNAP_DISTANCE:
            _log.warning(f"had to use emergency snap distance ({max_snap_distance}m) for {way.rlid} to get it "
                            f"to match reference geometry")
        way.way = new_way
        if len(way.way) == 1:
            #_log.info("RLID %s reduced to a point" % way.rlid)
            return ref_way, [ way ]

        if ref_way.way[0] == ref_way.way[-1]:
            # closed loop special cases
            assert len(ref_way.way) > 2
            closed_loop = False
            if way.way[0] == way.way[-1]:
                assert len(way.way) > 2
                closed_loop = True
                way.way = way.way[:-1]
            elif way.way[-1] == ref_way.way[0]:
                # make sure we end at max dist rather than min dist
                way.way[-1] = ref_way.way[-1]
            elif way.way[0].dist > way.way[-1].dist:
                # the way goes past split point of ref_way, split up way
                for idx, p in enumerate(way.way):
                    if p == ref_way.way[0]:
                        way_part1 = way.way[:idx] + [ ref_way.way[-1] ]
                        way_part2 = way.way[idx:]
                        break
                    if idx > 0 and way.way[idx-1].dist > p.dist:
                        # ref_way.way[0] point doesn't exist, insert it
                        way_part1 = way.way[:idx] + [ ref_way.way[-1] ]
                        way_part2 = [ ref_way.way[0] ] + way.way[idx:]
                        break
                way2 = way.make_copy_new_way(way_part2)
                way.way = way_part1

                r1, w1 = self._adapt_way_into_reference_geometry(way, data_src_name)
                r2, w2 = self._adapt_way_into_reference_geometry(way2, data_src_name)
                assert r1 == ref_way and r2 == ref_way and len(w1) == 1 and len(w2) == 1
                return ref_way, [ w1[0], w2[0] ]

            # way could have different starting point in the closed loop, make sure they are the same
            min_idx = 0
            for idx, p in enumerate(way.way):
                if p.dist < way.way[min_idx].dist:
                    min_idx = idx
            if min_idx != 0:
                way.way = way.way[min_idx:] + way.way[:min_idx]
            if closed_loop:
                if way.way[0] != ref_way.way[0]:
                    assert len(way.way) < len(ref_way.way)
                    way.way.insert(0, ref_way.way[0])
                way.way.append(ref_way.way[-1])
                assert way.way[0] == way.way[-1]

        elif len(way.way) > 2 and way.way[-1] == ref_way.way[-1] and way.way[-1].dist < way.way[-2].dist:
            # P-shaped loop, ie endpoint attaches to midpoint on the own way.
            # Very rare (seen in Stockholm dataset), and sort of illegal
            _log.warning(f"endpoint attaches to own midpoint for RLID {way.rlid}")
            way.way[-1].dist = ref_way.way[-1].dist
            if self._perform_self_testing:
                self._test_way_dist(way)

        # if this way has fewer points that the reference geometry it snaps to (happens in
        # some cases), we need to insert missing points we can assume that:
        #  - matching ways are oriented in the same direction
        #  - matching ways have the same RLID
        #  - reference geometry has each way for RLID in its full length, ie it should cover
        #    the full length of the inserted way
        ref_it = iter(ref_way.way)
        ref_p = next(ref_it)
        while ref_p != way.way[0]:
            try:
                ref_p = next(ref_it)
            except StopIteration as stop_iteration:
                raise RuntimeError("Could not find start %s of way %s in reference geometry (does it extend reference geometry?)" % (latlon_str(way.way[0]), way.rlid)) from stop_iteration
        assert ref_p == way.way[0]
        new_way = []
        #_log.info(way.rlid)
        #_log.info("ref_way", ref_way.way)
        #_log.info("way.way", way.way)
        for p in way.way:
            while ref_p != p:
                assert p.dist >= 0
                new_way.append(ref_p)
                ref_p = next(ref_it)
            new_way.append(p)
            try:
                ref_p = next(ref_it)
            except StopIteration:
                assert ref_p == p
        if len(new_way) > len(way.way):
            #_log.info("Added points to way of RLID %s (%s => %s)" % (way.rlid, len(way.way), len(new_way)))
            way.way = new_way

        return ref_way, [ way ]

    def remove_short_sub_segments(self):
        _log.info("Removing short sub-segments...")
        # "Remove" in this context means merging with neighbor segment
        remove_count = 0
        for segs in list(self.way_db.values()):
            new_segs = []
            for idx, seg in enumerate(segs):
                length, _ = calc_way_length(seg.way)
                if length > 8.0:
                    new_segs.append(seg)
                    continue
                prev_length = 0
                next_length = 0
                if len(new_segs) > 0 and new_segs[-1].way[-1] == seg.way[0]:
                    prev_length, _ = calc_way_length(new_segs[-1].way)
                next_idx = (idx+1) % len(segs)
                if segs[next_idx].way[0] == seg.way[-1]:
                    next_length, _ = calc_way_length(segs[next_idx].way)
                if prev_length == 0 and next_length == 0:
                    # unconnected short segment (hopefully rare)
                    if len(segs) == 1:
                        _log.debug(f"RLID {seg.rlid} is an alone short segment ({length:g}), must be kept")
                    else:
                        _log.debug(f"RLID {seg.rlid} has a short unconnected segment ({length:g}), must be kept")
                    new_segs.append(seg)
                    continue
                if length > 2.0:
                    # for longer stubs, we only remove them if they are on the start/end and
                    # only if only two points. This metric is based on what is seen in NVDB
                    # data.
                    if (prev_length != 0 and next_length != 0) or len(seg.way) > 2 or keep_end_stub(seg):
                        new_segs.append(seg)
                        continue
                # we can mess up dist value of points here for closed loops, but since
                # this is run at the end we don't care
                if prev_length > next_length:
                    new_segs[-1].way += seg.way[1:]
                else:
                    segs[next_idx].way = seg.way[:-1] + segs[next_idx].way
                remove_count += 1
            if len(new_segs) < len(segs):
                if len(new_segs) == 0:
                    del self.way_db[segs[0].rlid]
                else:
                    self.way_db[segs[0].rlid] = new_segs

        _log.info(f"done ({remove_count} short sub-segments were removed)")

        self.join_segments_with_same_tags()

    def _get_way(self, rlid, point):
        segs = self.way_db.get(rlid, [])
        for seg in segs:
            for p in seg.way:
                if p == point:
                    return seg
        return None

    def _fix_after_failed_adapt_geometry_way_insert(self):
        # we may now have more points in ref geometry than in actual segments.
        # This should be called rarely, easier to add in points than to clean up reference geometry.
        for segs in self.way_db.values():
            for seg in segs:
                ref_way = self._ref_gs.find_reference_way(seg.way[0], seg.rlid)
                ref_idx = 0
                while ref_idx < len(ref_way.way) and ref_way.way[ref_idx] != seg.way[0]:
                    ref_idx += 1
                seg_idx = 0
                while seg_idx < len(seg.way):
                    if seg.way[seg_idx].dist != ref_way.way[ref_idx].dist:
                        seg.way.insert(seg_idx, ref_way.way[ref_idx])
                        _log.info("Inserting extra point in geometry to compensate failed insert")
                    ref_idx += 1
                    seg_idx += 1

    def test_segments(self):
        for segs in self.way_db.values():
            self._test_segment(segs)

    def setup_geometry_search(self):
        _log.info("Setting up search data structure for all geometry...")
        self.gs = GeometrySearch(GEO_FILL_LENGTH, use_dist=False, perform_self_testing=self._perform_self_testing)
        self.gs.insert_waydb(self.way_db)
        _log.info("done")

    def get_endpoint_map(self):
        endpoints = {}
        for segs in self.way_db.values():
            for seg in segs:
                for p in [ seg.way[0], seg.way[-1] ]:
                    if p in endpoints:
                        endpoints[p].append(seg)
                    else:
                        endpoints[p] = [ seg ]
        return endpoints

    @staticmethod
    def _join_rlid_pick_best_matching_ways(ep, endpoints):
        ways = endpoints[ep]
        if len(ways) == 1:
            # no connections
            return None, None
        max_angle = -1
        best_way = None
        for w1 in ways:
            w1_closed = w1.way[0] == w1.way[-1]
            if w1.way[0] == ep:
                p1 = w1.way[1]
                w1_start = True
            else:
                p1 = w1.way[-2]
                w1_start = False
            for w2 in ways:
                if w1 == w2 or w1.tags != w2.tags:
                    continue
                w2_closed = w2.way[0] == w2.way[-1]
                if w2.way[0] == ep:
                    p3 = w2.way[1]
                    w2_start = True
                else:
                    p3 = w2.way[-2]
                    w2_start = False
                if w1_start == w2_start and not way_may_be_reversed(w1) and not way_may_be_reversed(w2):
                    # one way must be reversed, but none can be reversed

                    # if one way is closed, we can swap start/end to recover, otherwise skip this pair
                    if w1_closed:
                        if w1_start:
                            p1 = w1.way[-2]
                        else:
                            p1 = w1.way[1]
                    elif w2_closed:
                        if w2_start:
                            p3 = w2.way[-2]
                        else:
                            p3 = w2.way[1]
                    else:
                        continue
                # calculate angle between p1 and p2
                xa = p1.x - ep.x
                ya = p1.y - ep.y
                xb = p3.x - ep.x
                yb = p3.y - ep.y
                denom = math.sqrt(xa*xa + ya*ya) * math.sqrt(xb*xb + yb*yb)
                if denom != 0:
                    q = (xa * xb + ya * yb) / denom
                    if q < -1:
                        # this can happen due to precision limitation, -1.0000000000000002 seen in tests
                        angle = 180
                    elif q > 1:
                        angle = 0
                    else:
                        angle = math.acos((xa * xb + ya * yb) / denom) * 180 / math.pi
                else:
                    angle = 0
                if angle > max_angle:
                    max_angle = angle
                    if max_angle > 30:
                        best_way = (w1, w2)
                    else:
                        _log.debug(f"Skipping extreme angle {angle} between {w1.rlid} {w2.rlid}")
        if best_way is None:
            return None, None
        _log.debug(f"Max angle {max_angle} for {best_way[0].rlid} to {best_way[1].rlid}")
        return best_way[0], best_way[1]

    def _remove_seg_before_join(self, seg, endpoints):
        segs = self.way_db[seg.rlid]
        segs.remove(seg)
        if len(segs) == 0:
            _log.debug(f"RLID {seg.rlid} completely removed when joining with other segment")
            del self.way_db[seg.rlid]
        endpoints.remove(seg.way[0], seg)
        if seg.way[-1] != seg.way[0]: # closed loop special case
            endpoints.remove(seg.way[-1], seg)

    def _join_rlid(self, seg, endpoints, directional_nodes):

        rlid_join_count = 0
        ep_idx = -1
        consecutive_fails = 0
        while consecutive_fails < 2:
            if ep_idx == -1:
                ep_idx = 0
                connecting_ep_idx = -1
            else:
                ep_idx = -1
                connecting_ep_idx = 0
            ep = seg.way[ep_idx]
            w1, w2 = self._join_rlid_pick_best_matching_ways(ep, endpoints)
            if seg not in (w1, w2):
                consecutive_fails += 1
                continue
            consecutive_fails = 0
            if w1 == seg:
                join_way = w2
            else:
                join_way = w1
            self._remove_seg_before_join(join_way, endpoints)
            self._remove_seg_before_join(seg, endpoints)
            if join_way.way[connecting_ep_idx] != ep and seg.way[0] != seg.way[-1]:
                # reversing required
                if way_may_be_reversed(seg) and way_may_be_reversed(join_way):
                    l1, _ = calc_way_length(seg.way)
                    l2, _ = calc_way_length(join_way.way)
                    reverse_join_way = l1 >= l2
                elif way_may_be_reversed(join_way):
                    reverse_join_way = True
                else:
                    reverse_join_way = False
                    assert way_may_be_reversed(seg)
                if reverse_join_way:
                    _log.debug(f"Reversing joining RLID {join_way.rlid}")
                    reverse_way(join_way, directional_nodes)
                else:
                    _log.debug(f"Reversing base RLID {seg.rlid}")
                    reverse_way(seg, directional_nodes)
                    if ep_idx == 0:
                        ep_idx = -1
                    else:
                        ep_idx = 0

            # create new RLID by joining the current, sort them to get repeatable result
            new_rlid = seg.rlid.split(';')
            new_rlid.append(join_way.rlid)
            new_rlid.sort()
            new_rlid = ";".join(new_rlid)
            rlid_join_count += 1
            if seg.way[0] == join_way.way[-1]:
                seg.way.pop(0)
                seg.way = join_way.way + seg.way
            elif seg.way[-1] == join_way.way[0]:
                join_way.way.pop(0)
                seg.way += join_way.way
            else:
                _log.error(f"{seg.rlid}, {seg.way}")
                _log.error(f"{join_way.rlid}, {join_way.way}")
                raise RuntimeError("Disconnected segments cannot be joined")
            join_way.way = None

            seg.rlid = new_rlid
            if new_rlid in self.way_db:
                self.way_db[new_rlid].append(seg)
            else:
                _log.debug(f"Inserted joined RLID {new_rlid}")
                self.way_db[new_rlid] = [ seg ]
            endpoints.insert(seg.way[0], seg)
            endpoints.insert(seg.way[-1], seg)

        return rlid_join_count

    def join_segments_with_same_tags(self, join_rlid=False):

        if join_rlid:
            _log.info("Joining segments with same tags even if different RLID...")
        else:
            _log.info("Joining RLID segments with same tags...")
        join_count = 0
        for segs in self.way_db.values():
            it = iter(segs)
            prev = next(it)
            nsegs = [prev]
            for seg in it:
                lastseg = nsegs[-1]
                if len(lastseg.way) < 2:
                    raise RuntimeError("Short way")
                if len(seg.way) < 2:
                    raise RuntimeError("Short way %s %s" % (seg, segs))
                if lastseg.way[-1] == seg.way[0] and lastseg.tags == seg.tags:
                    join_count += 1
                    seg.way.pop(0)
                    lastseg.way += seg.way
                else:
                    nsegs.append(seg)
                prev = seg
            if len(nsegs) < len(segs):
                self.way_db[segs[0].rlid] = nsegs

        if join_rlid:

            # Joining ways can be optimized in several ways, as there are crossings where more
            # than two segments join at the same point and direction of segments can be swapped
            # to either make joining possible or impossible with neighboring segment, there are
            # many different solutions to the problem.
            #
            # Here we have adopted a strategy which is more advanced than the most trivial method,
            # but still it does not attempt to reach "optimal" result (whatever that would be)
            #
            directional_nodes = get_directional_nodes(self.point_db)
            rlid_join_count = 0
            endpoints = TwoDimSearch()
            all_segs = set()
            for segs in self.way_db.values():
                for seg in segs:
                    all_segs.add(seg)
                    for ep in (seg.way[0], seg.way[-1]):
                        endpoints.insert(ep, seg)

            while True:
                _log.debug("RLID join iteration")
                prev_rlid_join_count = rlid_join_count
                for seg in all_segs:
                    if seg.way is None: # already processed
                        continue
                    join_count = self._join_rlid(seg, endpoints, directional_nodes)
                    if join_count > 0:
                        _log.debug(f"Added {join_count} segments to {seg.rlid}")
                        rlid_join_count += join_count
                if prev_rlid_join_count == rlid_join_count:
                    break
                all_segs = set()
                for segs in self.way_db.values():
                    for seg in segs:
                        assert seg.way is not None
                        all_segs.add(seg)

        if join_rlid:
            _log.info(f"done ({join_count} joined within same RLID, and {rlid_join_count} with different RLID joined)")
        else:
            _log.info(f"done ({join_count} joined)")


    def make_way_directions_tree_like(self):
        _log.info("Arrange way directions so the graph grows tree-like...")
        reverse_count = 0
        decided_count = 0
        not_oriented = set()
        oriented_endpoints = TwoDimSearch()
        directional_nodes = get_directional_nodes(self.point_db)
        for segs in self.way_db.values():
            for seg in segs:
                decide_later = False
                if way_may_be_reversed(seg):
                    start_connect_count = len(self._ref_gs.find_all_connecting_ways(seg.way[0]))
                    end_connect_count = len(self._ref_gs.find_all_connecting_ways(seg.way[-1]))
                    if end_connect_count == 1:
                        # already desired direction
                        pass
                    elif start_connect_count == 1:
                        reverse_way(seg, directional_nodes)
                        reverse_count += 1
                    else:
                        decide_later = True
                        not_oriented.add(seg)
                if not decide_later:
                    oriented_endpoints.insert(seg.way[0], seg)
                    oriented_endpoints.insert(seg.way[-1], seg)
                    decided_count += 1

        _log.debug(f"master orientation iteration ({decided_count} decided, {reverse_count} reversed)")

        last_not_oriented_len = -1
        while len(not_oriented) != last_not_oriented_len:
            _log.debug(f"orientation iteration ({len(not_oriented)} left)")
            last_not_oriented_len = len(not_oriented)
            oriented = set()
            for seg in not_oriented:
                max_rev_len = -1
                max_len = -1
                for ep_idx in (0, -1):
                    ep = seg.way[ep_idx]
                    if ep not in oriented_endpoints:
                        continue
                    ways = oriented_endpoints[ep]
                    for w in ways:
                        length, _ = calc_way_length(w.way)
                        if w.way[ep_idx] == ep:
                            if length > max_rev_len:
                                max_rev_len = length
                        elif length > max_len:
                            max_len = length
                if max_rev_len == -1 and max_len == -1:
                    # could not decide direction in this round
                    continue
                if max_rev_len > max_len:
                    reverse_way(seg, directional_nodes)
                    reverse_count += 1
                oriented_endpoints.insert(seg.way[0], seg)
                oriented_endpoints.insert(seg.way[-1], seg)
                oriented.add(seg)
            not_oriented -= oriented

        _log.debug(f"orientation iterations complete ({len(not_oriented)} not considered, connected to midpoins etc)")
        _log.info(f"done ({reverse_count} ways reversed)")

    def simplify_geometry(self):
        _log.info("Simplifying geometry...")
        old_point_count = 0
        new_point_count = 0

        connected_midpoints = set()
        for segs in self.way_db.values():
            for seg in segs:
                for p in seg.way[1:-1]:
                    # We also check if connected to self (P-shaped loops)
                    if p == seg.way[0] or p == seg.way[-1] or len(self._ref_gs.find_all_connecting_ways(p)) > 1:
                        connected_midpoints.add(p)

        for segs in self.way_db.values():
            for seg in segs:
                start = 0
                nway = []
                # This value of 0.2 is consistent what is used in the Norwegian imports.
                # It's a quite high detail level and will keep most points available in NVDB
                # geometry.
                epsilon = 0.2
                for midx, p in enumerate(seg.way[1:-1]):
                    idx = midx + 1
                    if p in self.point_db or p in connected_midpoints:
                        sub_segment = seg.way[start:idx+1] # idx+1 to include current p as last point
                        simplified = simplify_way(sub_segment, epsilon)
                        nway += simplified[:-1] # skip last p to avoid overlaps with next sub-segment
                        start = idx
                nway += simplify_way(seg.way[start:], epsilon)
                old_point_count += len(seg.way)
                new_point_count += len(nway)
                seg.way = nway
        _log.info(f"done ({old_point_count} => {new_point_count} points)")

    def remove_segments_outside_area(self, geometry):
        _log.info("Remove all segments completely outside reference area...")
        remove_count = 0
        remove_rlid = []
        for rlid, segs in self.way_db.items():
            remove_segs = []
            for seg in segs:
                if not way_is_inside_or_crossing(geometry, seg.way):
                    remove_segs.append(seg)
                    remove_count += 1
            for seg in remove_segs:
                segs.remove(seg)
            if len(segs) == 0:
                remove_rlid.append(rlid)
        for rlid in remove_rlid:
            del self.way_db[rlid]
        _log.info(f"done ({remove_count} segments removed)")
