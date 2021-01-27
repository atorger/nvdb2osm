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
    return not LineString(points).is_simple

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
