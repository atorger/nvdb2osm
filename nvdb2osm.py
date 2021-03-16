#!/usr/bin/env python3

import argparse
import hashlib
import logging
import pathlib
import zipfile
import glob
import os
import sys
import geopandas
from sortedcontainers import SortedDict

from process_and_resolve import *
from tag_translations import TAG_TRANSLATIONS, process_tag_translations
from nvdb_segment import NvdbSegment, NVDB_GEOMETRY_TAGS
from shapely_utils import shapely_linestring_to_way
from waydb import WayDatabase, print_progress
from osmxml import waydb2osmxml, write_osmxml
from nvdb_ti import time_interval_strings

_log = logging.getLogger("nvdb2osm")

# read_epsg_shapefile()
#
#
def read_epsg_shapefile(directory_or_zip, name):
    if zipfile.is_zipfile(directory_or_zip):
        zf = zipfile.ZipFile(directory_or_zip)
        files = [fn for fn in zf.namelist() if fn.endswith(name + ".shp")]
        if len(files) > 0:
            filename = files[0]
            gdf_filename = "zip://" + str(directory_or_zip) + "!" + filename
    else:
        pattern = os.path.join(directory_or_zip, "*" + name + ".shp")
        files = glob.glob(pattern)
        if len(files) > 0:
            filename = files[0]
            gdf_filename = files[0]

    if len(files) == 0:
        _log.warning(f"No file name *{name}.shp in {directory_or_zip}")
        return None

    _log.info(f"Reading file {filename}")
    gdf = geopandas.read_file(gdf_filename, encoding='cp1252')
    _log.info(f"done ({len(gdf)} segments)")
    assert gdf.crs == "epsg:3006", "Expected SWEREF 99 (epsg:3006) geometry"
    return gdf

# read_nvdb_shapefile()
#
# Read a NVDB shapefile and apply tag translations.
#
def read_nvdb_shapefile(directory_or_zip, name, tag_translations, nvdb_total_bounds):
    gdf = read_epsg_shapefile(directory_or_zip, name)
    if gdf is None:
        return []
    _log.info(f"Parsing {len(gdf)} segments...")

    # update global bounding box
    bounds = gdf.total_bounds
    if bounds[0] < nvdb_total_bounds[0]:
        nvdb_total_bounds[0] = bounds[0]
    if bounds[1] < nvdb_total_bounds[1]:
        nvdb_total_bounds[1] = bounds[1]
    if bounds[2] > nvdb_total_bounds[2]:
        nvdb_total_bounds[2] = bounds[2]
    if bounds[3] > nvdb_total_bounds[3]:
        nvdb_total_bounds[3] = bounds[3]

    ways = []
    skip_count = 0
    last_print = 0
    for index, row in gdf.iterrows():
        if len(gdf) > 50:
            last_print = print_progress(last_print, index, len(gdf), progress_text=f"Parsing {len(gdf)} segments")
        way = row.to_dict()

        way.pop("TILL_DATUM", None)
        restore_set = {}
        for k in NVDB_GEOMETRY_TAGS:
            if k in way:
                restore_set[k] = way[k]
                del way[k]
        geometry = way["geometry"]
        del way["geometry"]

        if geometry is None:
            _log.info(f"Skipping segment without geometry RLID {way['RLID']}")
            skip_count += 1
            continue

        process_tag_translations(way, tag_translations)

        if geometry.type == "Point":
            points = Point(geometry.x, geometry.y)
        else:
            points = shapely_linestring_to_way(geometry)
            if len(points) == 1:
                _log.info(f"Skipping geometry (reduced) to one point {way}")
                skip_count += 1
                continue

        way["geometry"] = points
        way.update(restore_set)
        nvdbseg = NvdbSegment(way)
        nvdbseg.way_id = index
        ways.append(nvdbseg)
    if skip_count == 0:
        _log.info("done")
    else:
        _log.info(f"done ({len(ways)} segments kept, {skip_count} skipped)")
    return ways

# log_version()
#
# Log a unique hash for the code used
#
def log_version():

    def md5(fname):
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    files = [ "geometry_basics.py", "merge_tags.py", "nvdb2osm.py", "nvdb_ti.py", "process_and_resolve.py", "shapely_utils.py", "twodimsearch.py",
              "geometry_search.py", "nseg_tools.py", "nvdb_segment.py", "osmxml.py", "proj_xy.py", "tag_translations.py", "waydb.py"
             ]
    _log.info("Checksum for each script file (to be replaced with single version number when script is stable):")
    for fname in files:
        path = os.path.join(os.path.dirname(__file__), fname)
        _log.info(f"  {fname:22} MD5: {md5(path)}")


# insert_rlid_elements()
#
# Wrapper to insert a read NVDB layer into the database, logging progress.
#
def insert_rlid_elements(way_db, ways, data_src_name, debug_ways=None, do_snap=True):
    _log.info(f"Merging {len(ways)} segments...")
    last_print = 0
    for idx, way in enumerate(ways):
        if len(ways) > 50:
            last_print = print_progress(last_print, idx, len(ways), progress_text=f"Merging {len(ways)} segments")
        if isinstance(way.way, list):
            way_db.insert_rlid_way(way, data_src_name, debug_ways)
        else:
            did_snap = way_db.insert_rlid_node(way, data_src_name, do_snap)
            if not did_snap and do_snap:
                append_fixme_value(way.tags, "no nearby reference geometry to snap to")
    _log.info("done merging")


def main():
    """The main function, entry point of the program."""
    master_geometry_name = "NVDB_DKReflinjetillkomst"

    # Note the order how the layers are merged is in part important, see comments
    # So be careful if you re-order
    line_names = [
        # We always do FunkVagklass and GCM_vagtyp/DKCykVgKatier first, as experience tells us
        # that if there is a problem with the reference geometry these layers will trigger it.
        "NVDB_DKFunkVagklass", # all streets/roads
        "NVDB_DKGCM_vagtyp",   # all footways/cycleways
        "NVDB_DKCykVgKatier",  # most often redundant, otherwise complements DKGCM_vagtyp

        # just alphabetical order
        "NVDB_DKAntal_korfalt2",
        "NVDB_DKBarighet",
        "NVDB_DKBegrAxelBoggiTryck",
        "NVDB_DKBegrBruttovikt",
        "NVDB_DKBegrFordBredd",
        "NVDB_DKBegrFordLangd",
        "NVDB_DKBro_och_tunnel",
        "NVDB_DKCirkulationsplats",
        "NVDB_DKFarjeled",
        "NVDB_DKForbjudenFardriktning",
        "NVDB_DKForbudTrafik",
        "NVDB_DKGagata",
        "NVDB_DKGangfartsomrade",
        "NVDB_DKGatunamn",
        "NVDB_DKGatutyp",
        "NVDB_DKGCM_belyst",
        "NVDB_DKGCM_separation",
        "NVDB_DKHastighetsgrans",
        "NVDB_DKHuvudled",
        "NVDB_DKInskrTranspFarligtGods",
        "NVDB_DKKollektivkorfalt",
        # "NVDB_DKMiljozon", experimental tags, excluding them for now
        "NVDB_DKMotortrafikled",
        "NVDB_DKMotorvag",
        "NVDB_DKOvrigt_vagnamn",
        "NVDB_DKRekomVagFarligtGods",
        "NVDB_DKSlitlager",
        "NVDB_DKVagbredd",
        "NVDB_DKVagnummer",
        "TRV_EVB_DKDriftbidrag_statligt",
        "VIS_DKFunktionellt_priovagnat",
        "VIS_DKOmkorningsforbud",
        "VIS_DKSlitlager"
    ]

    point_names = [
        "NVDB_DKFarthinder",
        "NVDB_DKGCM_passage",
        "NVDB_DKHojdhinder45dm",
        "NVDB_DKKorsning",
        "NVDB_DKStopplikt",
        "NVDB_DKVaghinder",
        "NVDB_DKVajningsplikt",
        "VIS_DKJarnvagskorsning",
        "VIS_DKP_ficka",
        "VIS_DKRastplats",
    ]
    parser = argparse.ArgumentParser(description='Convert NVDB-data from Trafikverket to OpenStreetMap XML')
    parser.add_argument('--dump_layers', help="Write an OSM XML file for each layer", action='store_true')
    parser.add_argument('--skip_railway', help="Don't require railway geometry (leads to worse railway crossing handling)", action='store_true')
    parser.add_argument('--railway_file', type=pathlib.Path, help="Path to zip or dir with national railway network *.shp (usually Järnvägsnät_grundegenskaper.zip)")
    parser.add_argument('--rlid', help="Include RLID in output", action='store_true')
    parser.add_argument('--skip_self_test', help="Skip self tests", action='store_true')
    parser.add_argument(
        '-d', '--debug',
        help="Print debugging statements",
        action="store_const", dest="loglevel", const=logging.DEBUG,
        default=logging.WARNING,
    )
    parser.add_argument(
        '-v', '--verbose',
        help="Be verbose",
        action="store_const", dest="loglevel", const=logging.INFO,
    )
    parser.add_argument('shape_file', type=pathlib.Path,
                        help="zip or dir with NVDB *.shp files")
    parser.add_argument('osm_file', type=pathlib.Path,
                        help="filename of OSM XML output")
    args = parser.parse_args()
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=args.loglevel)
    _log = logging.getLogger("nvdb2osm")
    # When we turn on logging fiona gets a bit talkative
    logging.getLogger("fiona.env").setLevel(logging.WARNING)
    logging.getLogger("fiona._env").setLevel(logging.WARNING)
    logging.getLogger("fiona._shim").setLevel(logging.WARNING)
    logging.getLogger("fiona.ogrext").setLevel(logging.WARNING)
    logging.getLogger("fiona.collection").setLevel(logging.WARNING)
    _log.debug(f"args are {args}")

    log_version()

    write_rlid = args.rlid
    debug_dump_layers = args.dump_layers
    skip_railway = args.skip_railway
    directory_or_zip = args.shape_file
    output_filename = args.osm_file
    railway_filename = args.railway_file
    perform_self_testing = not args.skip_self_test

    if railway_filename is None and not skip_railway:
        _log.error("File with national railway geometry not provided (use --railway_file). Can be skipped by adding --skip_railway parameter, but then railway crossings will be somewhat misaligned")
        sys.exit(1)

    nvdb_total_bounds = [10000000, 10000000, 0, 0] # init to outside max range of SWEREF99
    # First setup a complete master geometry and refine it so we have a good geometry to merge the rest of the data with
    name = master_geometry_name
    ref_ways = read_nvdb_shapefile(directory_or_zip, name, TAG_TRANSLATIONS[name], nvdb_total_bounds)
    if debug_dump_layers:
        write_osmxml(ref_ways, [], "raw_reference_geometry.osm")
    ref_ways = find_overlapping_and_remove_duplicates(name, ref_ways)
    way_db = WayDatabase(ref_ways, perform_self_testing)

    if debug_dump_layers:
        write_osmxml(way_db.get_reference_geometry(), [], "reference_geometry.osm")

    all_line_names = line_names
    layer_count = len(all_line_names)
    layer_idx = 0
    for name in all_line_names:
        if name is None:
            break
        ways = read_nvdb_shapefile(directory_or_zip, name, TAG_TRANSLATIONS[name], nvdb_total_bounds)
        ways = find_overlapping_and_remove_duplicates(name, ways)
        did_insert_new_ref_geometry = way_db.insert_missing_reference_geometry_if_any(ways)

        if debug_dump_layers:
            if did_insert_new_ref_geometry:
                write_osmxml(way_db.get_reference_geometry(), [], "reference_geometry.osm")
            write_osmxml(ways, [], name + ".osm")

        debug_ways = None
        if name == "NVDB_DKBro_och_tunnel":
            ways = preprocess_bridges_and_tunnels(ways, way_db)
            if debug_dump_layers:
                write_osmxml(ways, [], name + "-preproc.osm")
                debug_ways = []

        insert_rlid_elements(way_db, ways, name, debug_ways=debug_ways)
        if perform_self_testing:
            way_db.test_segments()
        if debug_ways is not None:
            write_osmxml(debug_ways, [], name + "-adapted.osm")
        layer_idx += 1
        _log.info(f"Merged {layer_idx} of {layer_count} line geometry layers")

    way_db.join_segments_with_same_tags()
    way_db.remove_short_sub_segments()

    way_db.setup_geometry_search()

    layer_count = len(point_names)
    layer_idx = 0
    for name in point_names:
        if name is None:
            break
        points = read_nvdb_shapefile(directory_or_zip, name, TAG_TRANSLATIONS[name], nvdb_total_bounds)
        points = find_overlapping_and_remove_duplicates(name, points)

        do_snap = True
        if name == "NVDB_DKGCM_passage":
            points = preprocess_footcycleway_crossings(points, way_db)
        elif name == "NVDB_DKKorsning":
            points = process_street_crossings(points, way_db, name)
        elif name == "VIS_DKJarnvagskorsning":
            if len(points) > 0:
                railways = []
                if not skip_railway:
                    _log.info(f"There are {len(points)} railway crossings, reading railway geometry to have something to snap them to")
                    gdf = read_epsg_shapefile(railway_filename, "Järnvägsnät_med_grundegenskaper")
                    if gdf is None:
                        raise RuntimeError("Railway geometry missing")
                    _log.info(f"Filtering out railway segments for bounding box {nvdb_total_bounds}...")
                    for index, row in gdf.iterrows():
                        if bounds_intersect(row.geometry.bounds, nvdb_total_bounds):
                            seg = NvdbSegment({ "geometry": shapely_linestring_to_way(row.geometry),
                                                "RLID": "RW-%s" % index
                                               })
                            railways.append(seg)
                    _log.info(f"Done ({len(railways)} of {len(gdf)} segments kept)")
                    if debug_dump_layers:
                        write_osmxml(railways, [], "local-railway.osm")
                points = preprocess_railway_crossings(points, way_db, railways)
        elif name == "VIS_DKP_ficka":
            points = preprocess_laybys(points, way_db)
            do_snap = False

        insert_rlid_elements(way_db, points, name, do_snap=do_snap)
        layer_idx += 1
        _log.debug(f"Merged {layer_idx} of {layer_count} point layers")

    if debug_dump_layers:
        waydb2osmxml(way_db, "pre-resolve.osm")

    sort_multiple_road_names(way_db)
    resolve_highways(way_db)

    # converts cycleway way crossings to node crossing, which is optional, both ways to map are correct
    simplify_cycleway_crossings(way_db)

    simplify_speed_limits(way_db)
    remove_redundant_speed_limits(way_db)
    cleanup_highway_widths(way_db)

    # Note: simplify_oneway() may reverse some ways, causing functions depending on that ways
    # with the same RLID is oriented in the same direction to not work
    simplify_oneway(way_db, way_db.point_db)

    resolve_lanes(way_db)
    final_pass_postprocess_miscellaneous_tags(way_db)

    used_keys = SortedDict()
    cleanup_used_nvdb_tags(way_db.way_db, used_keys)
    cleanup_used_nvdb_tags(way_db.point_db, used_keys)

    log_used_and_leftover_keys(used_keys)
    _log.info("Time intervals used:")
    for str1 in time_interval_strings:
        _log.info(f"  '{str1}'")

    if debug_dump_layers:
        waydb2osmxml(way_db, "pre-join.osm")

    way_db.join_segments_with_same_tags(join_rlid=True)

    if debug_dump_layers:
        waydb2osmxml(way_db, "pre-treelike.osm")

    way_db.make_way_directions_tree_like()

    if debug_dump_layers:
        waydb2osmxml(way_db, "pre-simplify.osm")

    way_db.simplify_geometry()
    _log.info(f"Writing output to {output_filename}")
    waydb2osmxml(way_db, output_filename, write_rlid=write_rlid)
    _log.info("done writing output")

    _log.info("Conversion is complete. Don't expect NVDB data to be perfect or complete.")
    _log.info("Remember to validate the OSM file (JOSM validator) and check any fixme tags.")
    _log.info("Have fun and merge responsibly!")

if __name__ == "__main__":
    main()
