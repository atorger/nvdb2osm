import logging
import os
import geopandas
from shapely.geometry import Polygon

from osmxml import write_osmxml
from shapely_utils import way_is_inside_or_crossing, shortest_way_inside_or_crossing

_log = logging.getLogger("splitosm")

def sort_polygons(polygons):
    out_polygons = []
    while len(polygons) > 0:
        topmost_p = polygons[0].exterior.coords[0]
        topmost_polygon = polygons[0]
        found_one = False
        for polygon in polygons:
            if len(out_polygons) > 0:
                found_count = 0
                for p in polygon.exterior.coords:
                    if p in out_polygons[-1].exterior.coords:
                        found_count += 1
                if found_count < 2:
                    continue
            found_one = True
            for p in polygon.exterior.coords:
                if p[1] > topmost_p[1] or (p[1] == topmost_p[1] and p[0] > topmost_p[0]):
                    topmost_p = p
                    topmost_polygon = polygon
        if not found_one:
            for polygon in polygons:
                for p in polygon.exterior.coords:
                    if p[1] > topmost_p[1] or (p[1] == topmost_p[1] and p[0] > topmost_p[0]):
                        topmost_p = p
                        topmost_polygon = polygon
        out_polygons.append(topmost_polygon)
        polygons.remove(topmost_polygon)
    return out_polygons

def read_geojson_with_polygons(filename):
    gdf = geopandas.read_file(filename, encoding='utf-8')
    gdf.to_crs("epsg:3006", inplace=True)
    polygons = []
    for _, row in gdf.iterrows():
        polygons.append(Polygon(row.geometry))
    return sort_polygons(polygons)

def splitosm(way_db, split_geojson_filename, output_dir, basename, write_rlid=True):

    polygons = read_geojson_with_polygons(split_geojson_filename)
    for idx, polygon in enumerate(polygons):
        _log.info(f"Getting all ways and points that is inside or intersects area {idx+1} (of {len(polygons)})")
        ways = []
        points = []
        for segs in way_db.way_db.values():
            for seg in segs:
                w = shortest_way_inside_or_crossing(polygon, seg.way)
                if w is not None:
                    ways.append(seg.make_copy_new_way(w))
        for segs in way_db.point_db.values():
            for point in segs:
                if way_is_inside_or_crossing(polygon, point.way):
                    points.append(point)
        _log.info(f"{basename} subarea {idx+1} contains {len(ways)} ways and {len(points)} points")
        output_filename = os.path.join(output_dir, f"{basename}-subarea-{idx+1:02d}.osm")
        _log.info(f"Writing output to {output_filename}")
        write_osmxml(ways, points, output_filename, write_rlid)
        _log.info("done writing output")
