from shapely.geometry import LineString
from geometry_basics import *

# shapely_linestring_to_way
#
# Convert shapely linestring object to list of Point()
#
def shapely_linestring_to_way(geometry):
    assert (geometry.type == "LineString"), "Unexpected geometry type"
    xl, yl = geometry.xy
    way = []
    for x, y in zip(xl, yl):
        p = Point(x, y)
        if len(way) > 0 and p == way[-1]:
            # skip duplicate points (quite common in NVDB data)
            continue
        way.append(p)
    return way

# simplify_way()
#
# Remove excess amount of points from geometry using Douglas-Peucker algorithm,
# here imported from Shapely
#
def simplify_way(points, epsilon):
    if len(points) <= 2:
        return points
    ls = LineString(points).simplify(epsilon, preserve_topology=False)
    return shapely_linestring_to_way(ls)

def way_is_self_crossing(points):
    if len(points) <= 2:
        return False
    ls = LineString(points)
    if ls.is_simple:
        return False

    # Shapely considers P-shaped loops to not be simple, but these are okay according to OSM
    # so we say that those are not self-crossing.
    idx = None
    for p in points[1:-1]:
        if p == points[0]:
            if idx is not None:
                return True
            idx = 0
        elif p == points[-1]:
            if idx is not None:
                return True
            idx = -1
    if idx is None:
        return True
    if idx == 0:
        return not LineString(points[1:]).is_simple
    return not LineString(points[:-1]).is_simple

def split_self_crossing_way(points):
    # very inefficient, but okay since it's used rarely
    way = points.copy()
    new_ways = []
    while len(way) > 1:
        nl = len(way)
        while way_is_self_crossing(way[:nl]):
            nl -= 1
        new_ways.append(way[:nl])
        way = way[nl-1:]
    return new_ways

def way_is_inside_or_crossing(polygon, points):
    ls = LineString(points)
    return polygon.contains(ls) or polygon.intersects(ls)
