#!/usr/bin/env python3

import argparse
import logging
import pathlib
import zipfile
import glob
import os
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


# read_nvdb_shapefile()
#
# Read a NVDB shapefile and apply tag translations.
#
def read_nvdb_shapefile(directory_or_zip, name, tag_translations):
    _log = logging.getLogger("nvdb2osm")
    if zipfile.is_zipfile(directory_or_zip):
        zf = zipfile.ZipFile(directory_or_zip)
        files = [fn for fn in zf.namelist() if fn.endswith(name + ".shp")]
        if len(files) == 0:
            raise RuntimeError(f"No file name *{name}.shp in {directory_or_zip}")
        filename = files[0]
        gdf_filename = "zip://" + str(directory_or_zip) + "!" + filename
    else:
        pattern = os.path.join(directory_or_zip, "*" + name + ".shp")
        files = glob.glob(pattern)
        filename = files[0]
        gdf_filename = files[0]
    _log.info(f"Reading file {filename}")
    gdf = geopandas.read_file(gdf_filename, encoding='cp1252')
    _log.info(f"done ({len(gdf)} segments)")
    assert gdf.crs == "epsg:3006", "Expected SWEREF 99 (epsg:3006) geometry"
    ways = []
    _log.info(f"Parsing {len(gdf)} segments...")
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


# insert_rlid_elements()
#
# Wrapper to insert a read NVDB layer into the database, logging progress.
#
def insert_rlid_elements(way_db, ways, data_src_name, debug_ways=None):
    _log.info(f"Merging {len(ways)} segments...")
    last_print = 0
    for idx, way in enumerate(ways):
        if len(ways) > 50:
            last_print = print_progress(last_print, idx, len(ways), progress_text=f"Merging {len(ways)} segments")
        if isinstance(way.way, list):
            way_db.insert_rlid_way(way, data_src_name, debug_ways)
        else:
            did_snap = way_db.insert_rlid_node(way, data_src_name)
            if not did_snap:
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
        "NVDB_DKMiljozon",
        "NVDB_DKMotortrafikled",
        "NVDB_DKMotorvag",
        "NVDB_DKOvrigt_vagnamn",
        "NVDB_DKRekomVagFarligtGods",
        "NVDB_DKSlitlager",
        "NVDB_DKVagbredd",
        "NVDB_DKVagnummer",
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
        "NVDB_DKVandmojlighet",
        "VIS_DKP_ficka",
        "VIS_DKRastplats",
    ]
    parser = argparse.ArgumentParser(description='Convert NVDB-data from Trafikverket to OpenStreetMap XML')
    parser.add_argument('--dump_layers', action='store_true')
    parser.add_argument(
        '-d', '--debug',
        help="Print lots of debugging statements",
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

    debug_dump_layers = args.dump_layers
    directory_or_zip = args.shape_file
    output_filename = args.osm_file

    # First setup a complete master geometry and refine it so we have a good geometry to merge the rest of the data with
    name = master_geometry_name
    ref_ways = read_nvdb_shapefile(directory_or_zip, name, TAG_TRANSLATIONS[name])
    if debug_dump_layers:
        write_osmxml(ref_ways, [], "raw_reference_geometry.osm")
    ref_ways = find_overlapping_and_remove_duplicates(name, ref_ways)
    way_db = WayDatabase(ref_ways)

    if debug_dump_layers:
        write_osmxml(way_db.get_reference_geometry(), [], "reference_geometry.osm")

    all_line_names = line_names
    layer_count = len(all_line_names)
    layer_idx = 0
    for name in all_line_names:
        if name is None:
            break
        ways = read_nvdb_shapefile(directory_or_zip, name, TAG_TRANSLATIONS[name])
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

        insert_rlid_elements(way_db, ways, name, debug_ways)
        way_db.test_segments()
        if debug_ways is not None:
            write_osmxml(debug_ways, [], name + "-adapted.osm")
        layer_idx += 1
        _log.info(f"Merged {layer_idx} of {layer_count} line geometry layers")

    way_db.setup_geometry_search()

    layer_count = len(point_names)
    layer_idx = 0
    for name in point_names:
        if name is None:
            break
        points = read_nvdb_shapefile(directory_or_zip, name, TAG_TRANSLATIONS[name])
        points = find_overlapping_and_remove_duplicates(name, points)

        if name == "NVDB_DKGCM_passage":
            points = preprocess_footcycleway_crossings(points, way_db)
        elif name == "NVDB_DKKorsning":
            points = process_street_crossings(points, way_db, name)

        insert_rlid_elements(way_db, points, name)
        layer_idx += 1
        _log.debug(f"Merged {layer_idx} of {layer_count} point layers")

    if debug_dump_layers:
        waydb2osmxml(way_db, "pre-resolve.osm")

    way_db.join_segments_with_same_tags()
    way_db.remove_short_sub_segments(keep_end_stub)

    resolve_highways(way_db)
    simplify_speed_limits(way_db)

    # Note: simplify_oneway() may reverse some ways, causing functions depending on that ways
    # with the same RLID is oriented in the same direction to not work
    simplify_oneway(way_db)

    for way in way_db:
        postprocess_miscellaneous_tags(way.tags)

    used_keys = SortedDict()
    cleanup_used_nvdb_tags(way_db.way_db, used_keys)
    cleanup_used_nvdb_tags(way_db.point_db, used_keys)

    log_used_and_leftover_keys(used_keys)
    _log.info("Time intervals used:")
    for str1 in time_interval_strings:
        _log.info(f"  '{str1}'")

    way_db.join_segments_with_same_tags()

    way_db.simplify_geometry(way_to_simplify_epsilon)
    _log.info(f"Writing output to {output_filename}")
    waydb2osmxml(way_db, output_filename)
    _log.info("done writing output")

    print("Conversion is complete. NVDB data is not 100% perfect/complete: remember\n"
          "to validate the OSM file (JOSM validator) and check any fixme tags.\n"
          "Merge responsibly!")

if __name__ == "__main__":
    main()
