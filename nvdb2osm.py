#!/usr/bin/python3

import zipfile
import glob
import os
import sys
import geopandas
from sortedcontainers import SortedDict

from geometry_basics import *
from process_and_resolve import *
from tag_translations import TAG_TRANSLATIONS, process_tag_translations
from nvdb_segment import NvdbSegment, NVDB_GEOMETRY_TAGS
from shapely_utils import shapely_linestring_to_way
from waydb import WayDatabase, print_progress
from osmxml import waydb2osmxml, write_osmxml
from nvdb_ti import time_interval_strings

# FIXME replace ' ' with '=' in translation table

# read_nvdb_shapefile()
#
# Read a NVDB shapefile and apply tag translations.
#
def read_nvdb_shapefile(directory_or_zip, name, tag_translations):
    if zipfile.is_zipfile(directory_or_zip):
        zf = zipfile.ZipFile(directory_or_zip)
        files = [fn for fn in zf.namelist() if fn.endswith(name + ".shp")]
        if len(files) == 0:
            raise RuntimeError(f"No file name *{name}.shp in {directory_or_zip}")
        filename = files[0]
        gdf_filename = "zip://" + directory_or_zip + "!" + filename
    else:
        pattern = os.path.join(directory_or_zip, "*" + name + ".shp")
        files = glob.glob(pattern)
        filename = files[0]
        gdf_filename = files[0]
    print("Reading file %s..." % filename, end='', flush=True)
    gdf = geopandas.read_file(gdf_filename, encoding='cp1252')
    print("done (%s segments)" % len(gdf), flush=True)
    assert gdf.crs == "epsg:3006", "Expected SWEREF 99 (epsg:3006) geometry"
    ways = []
    print("Parsing %s segments..." % len(gdf), end='', flush=True)
    skip_count = 0
    last_print = 0
    for index, row in gdf.iterrows():
        if len(gdf) > 50:
            last_print = print_progress(last_print, index, len(gdf))
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
            print("Skipping segment without geometry RLID %s" % way["RLID"])
            skip_count += 1
            continue

        process_tag_translations(way, tag_translations)

        if geometry.type == "Point":
            points = Point(geometry.x, geometry.y)
        else:
            points = shapely_linestring_to_way(geometry)
            if len(points) == 1:
                print("Skipping geometry (reduced) to one point %s" % way)
                skip_count += 1
                continue

        way["geometry"] = points
        way.update(restore_set)
        nvdbseg = NvdbSegment(way)
        nvdbseg.way_id = index
        ways.append(nvdbseg)
    if skip_count == 0:
        print("done", flush=True)
    else:
        print("done (%s segments kept, %s skipped)" % (len(ways), skip_count), flush=True)
    return ways

# insert_rlid_elements()
#
# Wrapper to insert a read NVDB layer into the database, logging progress.
#
def insert_rlid_elements(way_db, ways, data_src_name, debug_ways=None):
    print("Merging %s segments..." % len(ways), end='', flush=True)
    last_print = 0
    for idx, way in enumerate(ways):
        if len(ways) > 50:
            last_print = print_progress(last_print, idx, len(ways))
        if isinstance(way.way, list):
            way_db.insert_rlid_way(way, data_src_name, debug_ways)
        else:
            did_snap = way_db.insert_rlid_node(way, data_src_name)
            if not did_snap:
                append_fixme_value(way.tags, "no nearby reference geometry to snap to")
    print("done", flush=True)

# main()
#
# The main function, entry point of the program.
#
def main():

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
        "VIS_DKOmkorningsforbud"
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

    if len(sys.argv) != 3:
        print("Usage: %s <zip or dir with NVDB *.shp files> <filename of OSM XML output>" % sys.argv[0])
        sys.exit(1)

    debug_dump_layers = False
    directory = sys.argv[1]
    output_filename = sys.argv[2]

    # First setup a complete master geometry and refine it so we have a good geometry to merge the rest of the data with
    name = master_geometry_name
    ref_ways = read_nvdb_shapefile(directory, name, TAG_TRANSLATIONS[name])
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
        ways = read_nvdb_shapefile(directory, name, TAG_TRANSLATIONS[name])
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
        print("Merged %s of %s line geometry layers" % (layer_idx, layer_count))

    way_db.setup_geometry_search()

    layer_count = len(point_names)
    layer_idx = 0
    for name in point_names:
        if name is None:
            break
        points = read_nvdb_shapefile(directory, name, TAG_TRANSLATIONS[name])
        points = find_overlapping_and_remove_duplicates(name, points)

        if name == "NVDB_DKGCM_passage":
            points = preprocess_footcycleway_crossings(points, way_db)
        elif name == "NVDB_DKKorsning":
            points = process_street_crossings(points, way_db, name)

        insert_rlid_elements(way_db, points, name)
        layer_idx += 1
        print("Merged %s of %s point layers" % (layer_idx, layer_count))

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
    print("Time intervals used:")
    for str1 in time_interval_strings:
        print("  '%s'" % str1)

    way_db.join_segments_with_same_tags()

    way_db.simplify_geometry(way_to_simplify_epsilon)
    print("Writing output to %s..." % output_filename, end='', flush=True)
    waydb2osmxml(way_db, output_filename)
    print("done", flush=True)

    print("Conversion is complete. NVDB data is not 100% perfect/complete: remember\n"
          "to validate the OSM file (JOSM validator) and check any fixme tags.\n"
          "Merge responsibly!")

if __name__ == "__main__":
    main()
