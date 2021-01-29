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
        print(f"These are the RLIDs for the self-crossing ways: {self_crossing_rlids}")

    unique_id = 1
    points = {}

    with open(filename, 'w', encoding="utf-8") as stream:
        # header
        stream.write("<?xml version='1.0' encoding='UTF-8'?>")
        stream.write("<osm version='0.6' generator='nvdb2osm.py'>")

        # all nodes with tags (points)
        for seg in point_list:
            p = seg.way
            if p in points:
                raise RuntimeError(f"Duplicate node in tagged node database {seg.rlid} {latlon_str(seg.way)}")
            p.node_id = unique_id
            unique_id += 1
            points[p] = p.node_id
            lat, lon = sweref99_transformer.transform(p.y, p.x)
            stream.write(f"<node id='-{p.node_id}' version='1' lat='{lat}' lon='{lon}'>\n"
                         f"  <tag k='source' v='NVDB' />\n"
                         f"  <tag k='NVDB:RLID' v='{seg.rlid}' />\n")
            for k, v in seg.tags.items():
                stream.write(f"  <tag k='{k}' v='{tag_to_str(v)}' />\n")
            stream.write("</node>")

        # all anonymous nodes (points)
        for seg in way_list:
            for p in seg.way:
                if p not in points:
                    p.node_id = unique_id
                    unique_id += 1
                    points[p] = p.node_id
                    lat, lon = sweref99_transformer.transform(p.y, p.x)
                    stream.write(f"<node id='-{p.node_id}' version='1' lat='{lat}' lon='{lon}' />\n")
                else:
                    p.node_id = points[p]

        # debug fillpoints
        # for x, ymap in way_db.gs._fillpoints.xmap.items():
        #    for y, refs in ymap.items():
        #        lat, lon = sweref99_transformer.transform(y, x)
        #        print("<node id='-%s' version='1' lat='%s' lon='%s' />" % (unique_id, lat, lon))
        #        unique_id += 1

        # all ways
        for seg in way_list:
            ways = [seg.way]
            if seg in self_crossing:
                ways = split_self_crossing_way(seg.way)
            for way in ways:
                seg.way_id = unique_id
                unique_id += 1
                stream.write(f"<way id='-{seg.way_id}' version='1'>\n")
                for p in way:
                    stream.write(f"  <nd ref='-{p.node_id}' />\n")
                stream.write(f"  <tag k='source' v='NVDB' />\n" \
                             f"  <tag k='NVDB:RLID' v='{seg.rlid}' />\n")
                for k, v in seg.tags.items():
                    stream.write(f"  <tag k='{k}' v='{tag_to_str(v)}' />\n")
                stream.write("</way>\n")

        stream.write("</osm>\n")
