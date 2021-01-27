import sys
import html

from geometry_basics import *
from proj_xy import sweref99_transformer, latlon_str
from shapely_utils import way_is_self_crossing, split_self_crossing_way

def waydb2osmxml(way_db, filename):
    ways = []
    points = []
    for segs in way_db.way_db.values():
        ways += segs
    for segs in way_db.point_db.values():
        points += segs
    write_osmxml(ways, points, filename)

def write_osmxml(way_list, point_list, filename):

    def tag_to_str(tag):
        if isinstance(tag, list):
            it = iter(tag)
            v = str(next(it))
            for t in it:
                v += ";" + str(t)
            return html.escape(v)
        return html.escape(str(tag))

    self_crossing = set()
    self_crossing_rlids = set()
    for seg in way_list:
        if way_is_self_crossing(seg.way):
            self_crossing.add(seg)
            self_crossing_rlids.add(seg.rlid)
    if len(self_crossing) > 0:
        print("Warning: data contains self-crossing ways, these will be split to support OSM XML format")
        print("These are the RLIDs for the self-crossing ways: %s" % self_crossing_rlids)

    unique_id = 1
    points = {}

    original_stdout = sys.stdout
    with open(filename, 'w') as stream:
        sys.stdout = stream
        # header
        print("<?xml version='1.0' encoding='UTF-8'?>")
        print("<osm version='0.6' generator='nvdb2osm.py'>")

        # all nodes with tags (points)
        for seg in point_list:
            p = seg.way
            if p in points:
                raise RuntimeError("Duplicate node in tagged node database %s %s" % (seg.rlid, latlon_str(seg.way)))
            p.node_id = unique_id
            unique_id += 1
            points[p] = p.node_id
            lat, lon = sweref99_transformer.transform(p.y, p.x)
            print("<node id='-%s' version='1' lat='%s' lon='%s'>" % (p.node_id, lat, lon))
            print("  <tag k='source' v='NVDB' />")
            print("  <tag k='NVDB:RLID' v='%s' />" % seg.rlid)
            for k, v in seg.tags.items():
                print("  <tag k='%s' v='%s' />" % (k, tag_to_str(v)))
            print("</node>")

        # all anonymous nodes (points)
        for seg in way_list:
            for p in seg.way:
                if not p in points:
                    p.node_id = unique_id
                    unique_id += 1
                    points[p] = p.node_id
                    lat, lon = sweref99_transformer.transform(p.y, p.x)
                    print("<node id='-%s' version='1' lat='%s' lon='%s' />" % (p.node_id, lat, lon))
                else:
                    p.node_id = points[p]

        # debug fillpoints
        #for x, ymap in way_db.gs._fillpoints.xmap.items():
        #    for y, refs in ymap.items():
        #        lat, lon = sweref99_transformer.transform(y, x)
        #        print("<node id='-%s' version='1' lat='%s' lon='%s' />" % (unique_id, lat, lon))
        #        unique_id += 1

        # all ways
        for seg in way_list:
            ways = [ seg.way ]
            if seg in self_crossing:
                ways = split_self_crossing_way(seg.way)
            for way in ways:
                seg.way_id = unique_id
                unique_id += 1
                print("<way id='-%s' version='1'>" % seg.way_id)
                for p in way:
                    print("  <nd ref='-%s' />" % p.node_id)
                print("  <tag k='source' v='NVDB' />")
                print("  <tag k='NVDB:RLID' v='%s' />" % seg.rlid)
                for k, v in seg.tags.items():
                    print("  <tag k='%s' v='%s' />" % (k, tag_to_str(v)))
                print("</way>")

        print("</osm>")

        sys.stdout = original_stdout
