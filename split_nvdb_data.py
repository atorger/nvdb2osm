#!/usr/bin/env python3

# Example:
# python3 split_nvdb_data.py --lanskod_filter 25 Norrbottens_län_Shape.zip output

import argparse
import hashlib
import pathlib
import shutil
import logging
import zipfile
import os
import glob
import sys
import geopandas
import pandas
import fiona

_log = logging.getLogger("split_nvdb_data")

def print_progress(last_print, idx, data_len, progress_text="work"):
    if data_len <= 1:
        return last_print
    progress = int(100 * idx / (data_len-1))
    if progress % 10 == 0 and progress != last_print:
        last_print = progress
        _log.info(f"{progress_text}: {progress}%")
    return last_print

def is_gpkg_file(filename):
    if zipfile.is_zipfile(filename):
        zf = zipfile.ZipFile(filename)
        files = [fn for fn in zf.namelist() if fn.endswith(".gpkg")]
        return len(files) > 0
    return str(filename).endswith(".gpkg")

def get_gpkg_layer_list(filename):
    if zipfile.is_zipfile(filename):
        zf = zipfile.ZipFile(filename)
        files = [fn for fn in zf.namelist() if fn.endswith(".gpkg")]
        if len(files) > 0:
            filename = "zip://" + str(filename) + "!" + files[0]

    _log.info(f"Reading layer list from {filename}")
    return fiona.listlayers(filename)

def make_gpkg_layer_map(files, layer_names):
    layer_map = {}
    for layer_name in layer_names:
        name = layer_name
        split_name = name.split('*')
        if len(split_name) == 1:
            prefix = ""
        else:
            prefix = split_name[0]
            name = split_name[1]
        matching_files = [fn for fn in files if prefix in fn and fn.endswith(name)]
        if len(matching_files) > 0:
            layer_map[layer_name] = matching_files[0]
            _log.info(f"{layer_name} matches layer {matching_files[0]}")
        else:
            _log.warning(f"no matching layer for {layer_name}")
    for layer in files:
        if layer not in layer_map.values():
            _log.info(f"unsused layer: {layer}")

    return layer_map

def read_gpkg_layer(filename, layer_name):
    if zipfile.is_zipfile(filename):
        zf = zipfile.ZipFile(filename)
        files = [fn for fn in zf.namelist() if fn.endswith(".gpkg")]
        if len(files) > 0:
            filename = "zip://" + str(filename) + "!" + files[0]
    _log.info(f"Reading layer {layer_name} from file {filename}")
    gdf = geopandas.read_file(filename, layer=layer_name)
    _log.info(f"done ({len(gdf)} segments)")
    assert gdf.crs == "epsg:3006", "Expected SWEREF 99 (epsg:3006) geometry"
    return gdf

def read_epsg_shapefile(directory_or_zip, name):
    if not os.path.exists(directory_or_zip):
        _log.error(f"{directory_or_zip} does not exist")
        return None

    split_name = name.split('*')
    if len(split_name) == 1:
        prefix = ""
    else:
        prefix = split_name[0]
        name = split_name[1]

    gdf_filename = None
    if zipfile.is_zipfile(directory_or_zip):
        zf = zipfile.ZipFile(directory_or_zip)
        files = [fn for fn in zf.namelist() if prefix in fn and fn.endswith(name + ".shp")]
        if len(files) > 0:
            filename = files[0]
            gdf_filename = "zip://" + str(directory_or_zip) + "!" + filename
    else:
        pattern = os.path.join(directory_or_zip, "*" + name + ".shp")
        files = glob.glob(pattern)
        files = [fn for fn in files if prefix in fn and fn.endswith(name + ".shp")]
        if len(files) > 0:
            filename = files[0]
            gdf_filename = files[0]

    if gdf_filename is None:
        _log.warning(f"No file name *{name}.shp in {directory_or_zip}")
        return None

    _log.info(f"Reading file {gdf_filename}")
    gdf = geopandas.read_file(gdf_filename, encoding='cp1252')
    _log.info(f"done ({len(gdf)} segments)")
    assert gdf.crs == "epsg:3006", "Expected SWEREF 99 (epsg:3006) geometry"
    return gdf

def log_version():
    def md5(fname):
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    files = [ "split_nvdb_data.py" ]
    _log.info("Checksum for each script file (to be replaced with single version number when script is stable):")
    for fname in files:
        path = os.path.join(os.path.dirname(__file__), fname)
        _log.info(f"  {fname:22} MD5: {md5(path)}")

def load_municipalities(lanskod):
    gdf = read_epsg_shapefile("data/ak_riks.zip", "ak_riks")
    municipalities = []
    for _, row in gdf.iterrows():
        if lanskod <= 0 or row.LANSKOD == lanskod:
            municipalities.append(row)
    return municipalities

def append_row_to_municipality(m_data, m, row):
    if m is None:
        kom_kod = -1
    else:
        kom_kod = m.KOM_KOD
    if kom_kod in m_data:
        m_data[kom_kod].append(row)
    else:
        m_data[kom_kod] = [ row ]

def main():

    layer_names = [
        "NVDB*FunkVagklass",
        "NVDB*Reflinjetillkomst",
        "NVDB*GCM_vagtyp",
        "NVDB*CykelVgsKat",
        "NVDB*Antal_korfalt2",
        "NVDB*Barighet",
        "NVDB*BegrAxelBoggiTryck",
        "NVDB*BegrBruttovikt",
        "NVDB*BegrFordBredd",
        "NVDB*BegrFordLangd",
        "NVDB*Bro_och_tunnel",
        "NVDB*Cirkulationsplats",
        "NVDB*Farjeled",
        "NVDB*ForbjudenFardriktning",
        "NVDB*Forbud_omkorn",
        "NVDB*ForbudTrafik",
        "NVDB*Gagata",
        "NVDB*Gangfartsomrade",
        "NVDB*Gatunamn",
        "NVDB*Gatutyp", # may be replaced with AGGREGAT*Vagslag
        "NVDB*GCM_belyst",
        "NVDB*GCM_separation",
        "NVDB*Hastighetsgrans",
        "NVDB*Huvudled",
        "NVDB*InskrTranspFarligtGods",
        "NVDB*Kollektivkorfalt",
        "NVDB*Motortrafikled", # probably obsolete, AGGREGAT*Vagslag has same info
        "NVDB*Motorvag", # probably obsolete, AGGREGAT*Vagslag has same info
        "NVDB*Ovrigt_vagnamn",
        "NVDB*RekomVagFarligtGods",
        "NVDB*Slitlager",
        "NVDB*Tillganglighet",
        "NVDB*Vagbredd",
        "NVDB*Vagnummer", # may be replaced with AGGREGAT*Vagslag
        "EVB*Driftbidrag_statligt",
        "VIS*Funktionellt_priovagnat",
        "VIS*Omkorningsforbud", # probably obsolete, may be replaced with NVDB*Forbud_omkorn
        "VIS*Slitlager",
        "NVDB*Farthinder",
        "NVDB*GCM_passage",
        "NVDB*Hojdhinder45dm",
        "NVDB*Korsning",
        "NVDB*Stopplikt",
        "NVDB*Vaghinder",
        "NVDB*Vajningsplikt",
        "VIS*Jarnvagskorsning",
        "VIS*P_ficka",
        "VIS*Rastplats",
        "AGGREGAT*Vagslag", # contains vägnummer mm, overlaps with some other layer (which may or may not be included)
        "AGGREGAT*Plankorsning_vag_jarnvag",
        "AGGREGAT*KommunLanReg",
    ]

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logging.getLogger("fiona.env").setLevel(logging.WARNING)
    logging.getLogger("fiona._env").setLevel(logging.WARNING)
    logging.getLogger("fiona._shim").setLevel(logging.WARNING)
    logging.getLogger("fiona.ogrext").setLevel(logging.WARNING)
    logging.getLogger("fiona.collection").setLevel(logging.WARNING)

    parser = argparse.ArgumentParser(description='Split NVDB-data from Trafikverket into smaller files')
    parser.add_argument('geo_file', type=pathlib.Path, help="zip/dir/gpkg with NVDB *.shp/*.gpkg")
    parser.add_argument('output_dir', type=pathlib.Path, help="directory to save output geometry files")
    parser.add_argument('--include_all_layers', help="Include all layers without name change (for debugging)", action='store_true')
    parser.add_argument('--lanskod_filter', help="Only include municipalities belonging to länskod", default="-1")
    parser.add_argument(
        '-d', '--debug',
        help="Print debugging statements",
        action="store_const", dest="loglevel", const=logging.DEBUG,
        default=logging.WARNING,
    )
    args = parser.parse_args()
    _log.info(f"args are {args}")
    geometry_file = args.geo_file
    output_dir = args.output_dir
    lanskod = int(args.lanskod_filter)
    include_all_layers = args.include_all_layers

    log_version()

    if not os.path.exists(output_dir):
        _log.error(f"Output directory {output_dir} does not exist")
        sys.exit(1)

    _log.info("Loading municipality borders")
    municipalities = load_municipalities(lanskod)
    if len(municipalities) == 0:
        _log.error("No municipalities matching länskod {lanskod}")
        sys.exit(1)
    _log.info(f"{len(municipalities)} areas used (länskod filter {lanskod})")

    is_gpkg = is_gpkg_file(geometry_file)
    if is_gpkg:
        layer_list = get_gpkg_layer_list(geometry_file)
        if include_all_layers:
            _log.info("Including all layers without changing their names")
            layer_map = {}
            layer_names = layer_list
            for layer in layer_list:
                if layer.startswith("Net_VAG"):
                    _log.info(f"skipping layer {layer} (Net_VAG layers known to not work)")
                    continue
                layer_map[layer] = layer
                _log.info(f"Layer: {layer}")
        else:
            layer_map = make_gpkg_layer_map(layer_list, layer_names)
    elif include_all_layers:
        _log.error("The include all layers flag only works with gpkg")
        sys.exit(1)

    for layer_idx, layer_name in enumerate(layer_names):
        _log.info(f"Reading layer {layer_name} ({layer_idx+1} of {len(layer_names)} layers) from {geometry_file}")
        gdf = None
        if is_gpkg:
            ln = layer_map.get(layer_name)
            if ln is not None:
                gdf = read_gpkg_layer(geometry_file, ln)
        else:
            gdf = read_epsg_shapefile(geometry_file, layer_name)
        if gdf is None:
            _log.warning(f"{layer_name} is missing in {geometry_file}")
            continue

        # go through all segments and distribute them into the right municipality
        m_data = {}
        last_print = 0
        for idx, row in gdf.iterrows():
            last_print = print_progress(last_print, idx, len(gdf), progress_text="Distributing segments into municipalities")
            contained = False
            for m_idx, m in enumerate(municipalities):
                if m.geometry.contains(row.geometry):
                    contained = True
                    append_row_to_municipality(m_data, m, row)
                    # move to front list
                    if m_idx != 0:
                        municipalities.insert(0, municipalities.pop(m_idx))
                    break
            if not contained:
                # not contained in a municipality, check which municipalities it intersects with and add to all
                for m_idx, m in enumerate(municipalities):
                    if m.geometry.intersects(row.geometry):
                        contained = True
                        append_row_to_municipality(m_data, m, row)
            if not contained:
                # this should not happen -- all geodata should be in some municipality
                if row.get('ELEMENT_ID') is not None:
                    row_id = row.get('ELEMENT_ID')
                else:
                    row_id = row.get('RLID')
                _log.info(f"geometry with id {row_id} not contained nor intersecting with any municipality. Adding to 'unknown'.")
                append_row_to_municipality(m_data, None, row)

        # write geometry files for each municipality
        cleaned_layer_name = layer_name.replace('*', '-')
        muni = [ { 'code': -1, 'name': 'unknown' }]
        for m in municipalities:
            muni.append({ 'code': m.KOM_KOD, 'name': m.KOMMUNNAMN })
        for m in muni:
            code = m['code']
            name = m['name']
            if code in m_data:
                _log.info(f"Saving {cleaned_layer_name}.gkpg for {name}")

                empty_copy = gdf.drop(gdf.index)
                mgdf = pandas.concat([empty_copy, pandas.DataFrame(m_data[code])], ignore_index=True)
                mgdf.crs = "epsg:3006"

                path = os.path.join(output_dir, name)
                if not os.path.exists(path):
                    os.mkdir(path)
                path = os.path.join(path, f"{cleaned_layer_name}.gpkg")
                geopandas.GeoDataFrame(mgdf).to_file(path)

    # Create zip archives for each municipality
    dirnames = next(os.walk(output_dir), (None, [], None))[1]
    for dirname in dirnames:
        archive = os.path.join(output_dir, dirname)
        _log.info(f"Creating archive {archive}.zip")
        shutil.make_archive(archive, "zip", archive)

if __name__ == "__main__":
    main()
