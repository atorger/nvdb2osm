import logging
from functools import cmp_to_key

from geometry_basics import *
from geometry_search import GeometrySearch, snap_to_closest_way
from merge_tags import merge_tags, append_fixme_value
from nvdb_segment import *
from proj_xy import latlon_str
from waydb import GEO_FILL_LENGTH
from tag_translations import ALL_VEHICLES
from nseg_tools import *


_log = logging.getLogger("process")


# merge_translated_tags()
#
# Help function to merge tags with special case for fix me tag.
#
def merge_translated_tags(way, tags):
    for k, v in tags.items():
        if k == "fixme":
            append_fixme_value(way.tags, v)
        else:
            way.tags[k] = v

# find_overlapping_and_remove_duplicates()
#
# Go through a freshly read NVDB layer and log any overlaps and remove any duplicates.
#
def find_overlapping_and_remove_duplicates(data_src_name, ways):

    class NvdbSegmentDup:
        def __init__(self, nvdb_seg):
            self.way = nvdb_seg.way
            self.tags = nvdb_seg.tags
            self.rlid = nvdb_seg.rlid
        def __eq__(self, other):
            if not isinstance(other, NvdbSegmentDup):
                return False
            return self.way == other.way and self.rlid == other.rlid and self.tags == other.tags
        def __hash__(self):
            return hash(self.rlid)

    pointpairs = {}
    waysd = {}
    new_ways = []
    overlap = False

    for way in ways:
        wd = NvdbSegmentDup(way)
        if wd not in waysd:
            waysd[wd] = way
        else:
            #way2 = waysd[wd]

            # duplicates are so normal and common, so we don't care to log them any longer
            #if isinstance(way.way, list):
            #    print("Duplicate ways:")
            #    print("  Way 1: %s tags=%s (%s points, index %s)" % (way, way.tags, len(way.way), way.way_id))
            #    print("  Way 2: %s tags=%s (%s points, index %s)" % (way2, way2.tags, len(way2.way), way2.way_id))
            #else:
            #    print("Duplicate nodes:")
            #    print("  Node 1: %s tags=%s (%s, index %s)" % (way, way.tags, way.way, way.way_id))
            #    print("  Node 2: %s tags=%s (%s, index %s)" % (way2, way2.tags, way2.way, way2.way_id))
            continue

        # overlapping segments are quite normal, but may be interesting to print, except for some
        # data layers when there's always lots of overlaps (it must be for some layers, for directional speed limits
        # for example)
        if isinstance(way.way, list) and data_src_name not in ("NVDB_DKHastighetsgrans", "NVDB_DKVagnummer"):
            it = iter(way.way)
            prev = next(it)
            for p in it:
                pp = (p, prev)
                prev = p
                if pp not in pointpairs:
                    pointpairs[pp] = way
                else:
                    way2 = pointpairs[pp]
                    _log.info(f"Self-overlapping segment between {latlon_str(pp[0])}-{latlon_str(pp[1])}:")
                    _log.info(f"  Segment 1: {way} tags={way.tags} ({len(way.way)} points, index {way.way_id})")
                    _log.info(f"  Segment 2: {way2} tags={way2.tags} ({len(way2.way)} points, index {way2.way_id})")
                    overlap = True
                    break
        new_ways.append(way)

    if len(new_ways) < len(ways):
        _log.info(f"{data_src_name} has duplicate elements. Only one copy of each was kept")

    if overlap:
        _log.info(f"{data_src_name} has overlapping segments.")

    return new_ways

# preprocess_laybys
#
# OSM tradition is to map layby parkings as unattached nodes beside the road rather than on it,
# (even if that makes routing difficult).
#
# Here we move the layby nodes parallel to the road
#
def preprocess_laybys(points, way_db):

    LAYBY_OFFSET = 7

    for node in points:
        ways = way_db.gs.find_all_nearby_ways(node.way)
        _, snap, way = snap_to_closest_way(ways, node.way)
        for idx, p in enumerate(way.way):
            if idx == 0:
                continue
            prev = way.way[idx-1]
            is_between, _ = point_between_points(snap, prev, p, 1e-6)
            if not is_between:
                continue
            prev, p = rotate_90deg(prev, p)
            oldlen = dist2d(prev, p)
            xd = (p.x - prev.x) / oldlen * LAYBY_OFFSET
            yd = (p.y - prev.y) / oldlen * LAYBY_OFFSET
            if node.tags["NVDB_layby_side"] == "right":
                node.way.x = snap.x - xd
                node.way.y = snap.y - yd
            else:
                node.way.x = snap.x + xd
                node.way.y = snap.y + yd
            break
    return points

# preprocess_footcycleway_crossings
#
# NVDB NVDB_DKGCM_passage (crossings for cycleways and footways) points are often placed a bit
# beside the actual crossings so we need scan the geometry and find which crossings they belong
# and align.
#
# NVDB_DKGCM_vagtyp data must be in the database for this function to work.
#
def preprocess_footcycleway_crossings(points, way_db):

    def has_value_tags(tags):
        for k in tags.keys():
            if k not in NVDB_GEOMETRY_TAGS:
                return True
        return False

    _log.info("Preprocess footway/cycleway crossings...")
    crossings = []
    unconnected_count = 0
    connected_count = 0
    for node in points:
        if not has_value_tags(node.tags):
            # empty, exclude this node
            continue
        cp = way_db.gs.find_crossing_points_within(node.way, 5)
        if len(cp) == 0:
            # This can happen normally in newly built areas where roads are not complete, or
            # where crossings are mapped but not related footway
            unconnected_count += 1
        else:
            # Snap to suitable crossing
            min_dist = None
            min_p = None
            for pl in cp:
                dist = dist2d(node.way, pl[0])
                has_other = False
                has_gcm = False
                for way in pl[1]:
                    if "GCMTYP" in way.tags:
                        has_gcm = True
                    else:
                        has_other = True
                if has_gcm and has_other and (min_dist is None or dist < min_dist):
                    min_dist = dist
                    min_p = pl[0]
            if min_p is None:
                unconnected_count += 1
            else:
                node.way = min_p
                connected_count += 1
        crossings.append(node)
    _log.info(f"done ({connected_count} attached to a way crossing, {unconnected_count} without)")
    return crossings

# preprocess_bridges_and_tunnels()
#
# Convert NVDB bridges and tunnels into OSM tags.
#
#  - The NVDB bridge/tunnel data has a considerable amount of errors
#      - Missing bridges, especially for cycleway
#      - Sometimes incorrect tags (bridge that should be under passage etc)
#      - Some alignment errors of under passages missing the bridge above
#      - Sometimes bridges are off by ~100 meters (rare?).
#      - Errors are more prominent in city areas like Stockholm with many long bridges and tunnels,
#        in rural areas the data is often mostly correct
#
#  - It's not possible to resolve the "layer" tag for OSM data. If the NVDB data would be 100%
#    correct it would be possible to make good educated guesses with an advanced algorithm. However
#    as the data is not that good and multi-layer bridges are rare, we've not made an algoritm for
#    that, a fix me tag is added instead when crossing bridges and tunnels are detected.
#
#  - OSM mapping tradition is to map a cycleway/footway that passes under a street as a tunnel,
#    even when the construction is technically a short bridge. In NVDB this is mapped as överfart
#    on the street and underfart on the cycleway. This is resolved here, converting to the OSM
#    mapping tradition.
#
def preprocess_bridges_and_tunnels(ways, way_db):

    def is_short_bridge(bridge, bridges, short_bridge):
        dist, _ = calc_way_length(bridge.way)
        if dist > short_bridge:
            return False
        measured_bridges = { bridge }
        for b in bridges:
            if b in measured_bridges:
                continue
            if dist2d(b.way[0], bridge.way[0]) < 0.05 or dist2d(b.way[0], bridge.way[-1]) < 0.05:
                dist2, _ = calc_way_length(b.way)
                dist += dist2
                if dist > short_bridge:
                    return False
                measured_bridges.add(b)
                bridge = b

        return True

    # Here (before being merged with other layers) bridges/tunnels are in the original lengths
    # ways may still be broken into parts

    bridges = []
    underways = []
    tunnels = []
    bridges_lcs = GeometrySearch(GEO_FILL_LENGTH)
    tunnels_lcs = GeometrySearch(GEO_FILL_LENGTH)
    for way in ways:
        konst = way.tags["KONTRUTION"]
        # Due to incorrect tagging of "överfart" vs "överfart och underfart" and that
        # "överfart och underfart" is very rare, we handle them the same as "överfart"
        if konst in ("överfart", "överfart och underfart"):
            bridges.append(way)
            bridges_lcs.insert(way)
        elif konst == "underfart":
            underways.append(way)
        elif konst == "tunnel":
            tunnels.append(way)
            tunnels_lcs.insert(way)
        else:
            raise RuntimeError("Unhandled tag name %s" % konst)

    # First go through under passages, and convert to tunnel if needed.
    _log.info(f"Checking {len(underways)} under-passages relation to {len(bridges)} bridge segments...")
    SHORT_BRIDGE_LENGTH = 12
    delete_bridges = set()
    convert_to_tunnels = []
    for way in underways:
        crossing = bridges_lcs.find_crossing_ways(way)
        short_bridge_count = 0
        for bridge in crossing:
            if is_short_bridge(bridge, bridges, SHORT_BRIDGE_LENGTH):
                short_bridge_count += 1
        if len(crossing) == 0:
            # this sometimes happens due to poor alignment or a missing bridge, but can also be crossed by railway bridges
            # (not included in the data)
            #print("Underfart %s not crossed" % way.rlid)
            pass
        elif short_bridge_count == len(crossing):
            #print("Underfart %s crossed only by %s short bridges, converting to tunnel and removing bridges" % (way.rlid, len(crossing)))
            convert_to_tunnels.append(way)
            for bridge in crossing:
                delete_bridges.add(bridge)

    for way in convert_to_tunnels:
        way.tags["tunnel"] = "yes"
        way.tags["layer"] = -1

    nbridges = []
    bridges_lcs = GeometrySearch(GEO_FILL_LENGTH)
    for way in bridges:
        if not way in delete_bridges:
            bridges_lcs.insert(way)
            nbridges.append(way)
    bridges = nbridges

    _log.info('done')
    if len(convert_to_tunnels) > 0:
        _log.info(f"{len(convert_to_tunnels)} under-passages was converted to tunnel and the related {len(delete_bridges)} short bridges were removed")

    _log.info(f"Processing {len(bridges)} bridge segments...")
    fixme_count = 0
    for way in bridges:
        tags = {}
        tags["bridge"] = "yes"
        tags["layer"] = 1
        crossing = bridges_lcs.find_crossing_ways(way, abort_at_first=True)
        if len(crossing) > 0:
            # in theory we could do a better job if we looked at "överfart och underfart" separately
            # and analyzed the connecting road network, but as the data is often not fully correct and
            # these situations are rare, we just add a FIXME in these situations.
            tags["fixme"] = "could not resolve layer"
            fixme_count += 1
        merge_translated_tags(way, tags)
    _log.info('done')
    if fixme_count > 0:
        _log.warning(f"{fixme_count} bridge segments crosses other bridges, cannot resolve layers, fixme tags added")

    if len(tunnels) > 0:
        _log.info("Setting up search datastructure for crossing lines...")
        all_lcs = GeometrySearch(GEO_FILL_LENGTH)
        all_lcs.insert_waydb(way_db.way_db)
        _log.info("done")
    _log.info(f"Processing {len(tunnels)} tunnel segments...")
    fixme_count = 0
    for way in tunnels:
        tags = {}
        tags["tunnel"] = "yes"

        if tunnels_lcs.find_crossing_ways(way, abort_at_first=True):
            fixme_count += 1
            tags["layer"] = -1
            tags["fixme"] = "could not resolve layer"
        else:
            # no crossing ways => no layer tag
            crossing = all_lcs.find_crossing_ways(way, abort_at_first=True)
            if len(crossing) > 0:
                tags["layer"] = -1

        merge_translated_tags(way, tags)
    _log.info('done')
    if fixme_count > 0:
        _log.warning(f"{fixme_count} tunnel segments crosses other tunnel, cannot resolve layers, fixme tags added")

    return bridges + tunnels + convert_to_tunnels


# process_street_crossings()
#
# Process the NVDB point layer DKKorsning and geometry it affects. This includes
# setting names on roundabouts and snapping the points to actual crossings in the
# line geometry.
#
def process_street_crossings(points, way_db, data_src_name):
    def get_roundabout_ways(point_on_roundabout, way_db):
        ways = way_db.gs.find_all_connecting_ways(point_on_roundabout)
        rbw = set()
        for w in ways:
            if w.tags.get("junction", "") == "roundabout":
                rbw.add(w)
        last_size = len(rbw)
        while True:
            nrbw = set()
            for w in rbw:
                ways = way_db.gs.find_all_connecting_ways(w.way[0])
                ways.update(way_db.gs.find_all_connecting_ways(w.way[-1]))
                for w1 in ways:
                    if w1.tags.get("junction", "") == "roundabout":
                        nrbw.add(w1)
            rbw.update(nrbw)
            if len(rbw) == last_size:
                break
            last_size = len(rbw)
        return rbw

    crossings = []
    fixme_count = 0
    for node in points:
        if not "highway" in node.tags and node.tags["NVDB_generaliseringstyp"] != "cirkulationsplats":
            # no useful info, skip this crossing
            continue
        cp = way_db.gs.find_crossing_points_within(node.way, 2)
        fixme = False
        if len(cp) == 0:
            fixme = True
        else:
            # Snap to suitable crossing
            min_dist = None
            min_p = None
            for pl in cp:
                dist = dist2d(node.way, pl[0])
                if (min_dist is None or dist < min_dist):
                    min_dist = dist
                    min_p = pl[0]
            if min_p is None:
                fixme = True
            else:
                node.way = min_p
        if fixme:
            if not "highway" in node.tags:
                # ignore
                continue
            fixme_count += 1
            merge_translated_tags(node, {"fixme": "no suitable street crossing found"})
        if node.tags["NVDB_generaliseringstyp"] == "cirkulationsplats" and node.tags.get("name", None) is not None:
            rbw = get_roundabout_ways(node.way, way_db)
            # if there are already names on the roads, we put roundabout name as the main one
            for w in rbw:
                if "name" in w.tags:
                    merge_name = w.tags["name"]
                    w.tags["name"] = node.tags["name"]
                else:
                    merge_name = node.tags["name"]
                merge_tags(w, {"name": merge_name}, data_src_name)
        if "highway" in node.tags:
            del node.tags["name"]
            crossings.append(node)
    if fixme_count > 0:
        _log.warning(f"did not find any way crossing for {fixme_count} street crossings, fixme tags added")
    return crossings


# parse_road_number()
#
# Split text road numbers into components
#
def parse_road_number(rn):
    rn = str(rn)
    if rn[0].isalpha():
        rns = rn.split(' ')
        prefix = rns[0]
        rest = rns[1]
    else:
        prefix = ""
        rest = rn
    rns = rest.split('.')
    main_nr = int(rns[0])
    if len(rns) > 1:
        sub_nr = int(rns[1])
    else:
        sub_nr = 0
    # E is also "Östergötlands län"
    is_e_road = prefix == 'E' and main_nr < 500
    return prefix, main_nr, sub_nr, is_e_road


# compare_vagnummer()
#
# Sort function for road numbers, used when there is more than one road number on the same road segment.
#
def compare_vagnummer(r1, r2):
    p1, n1, u1, r1_is_e = parse_road_number(r1)
    p2, n2, u2, r2_is_e = parse_road_number(r2)

    # E roads get sorted first
    if r1_is_e != r2_is_e:
        if r1_is_e:
            return -1
        return 1

    # Sort on länsbokstav
    if p1 > p2:
        return 1
    if p1 < p2:
        return -1

    # Sort on main number
    if n1 != n2:
        return n1 - n2

    # Sort on under number
    return u1 - u2

# resolve_highways()
#
# Using information from multiple layers, figure out what the highway tag should be (and some side tags)
#
def resolve_highways(way_db):

    _log.info("Resolve highway tags...")
    fixme_count = 0
    gcm_resolve_crossings = []
    for way in way_db:

        # convert tags
        if "NVDB_vagnummer" in way.tags:
            refs = way.tags["NVDB_vagnummer"]
            if isinstance(refs, list):
                refs.sort(key=cmp_to_key(compare_vagnummer))
            way.tags["ref"] = refs

        tags = {}
        if "GCMTYP" in way.tags:
            gcmtyp = way.tags["GCMTYP"]

            if gcmtyp == 1: # Cykelbana (C)
                tags["highway"] = "cycleway"
            elif gcmtyp == 2: # Cykelfält (C)
                tags["highway"] = "cycleway"
            elif gcmtyp == 3: # Cykelpassage (C)
                tags["highway"] = "cycleway"
                tags["cycleway"] = "crossing"
                tags["crossing"] = "marked"
            elif gcmtyp == 4: # Övergångsställe (C+G)
                # note: may in some cases be marked only with traffic sign,
                # OSM "marked" actually refers to marking on road surface
                tags["crossing"] = "marked"
                tags["highway"] = "path" # refined later
                gcm_resolve_crossings.append(way)
            elif gcmtyp == 5: # Gatupassage utan märkning (C+G)
                tags["crossing"] = "unmarked"
                tags["highway"] = "path" # refined later
                gcm_resolve_crossings.append(way)
            # elif gcmtyp == 6: not used by NVDB
            # elif gcmtyp == 7: not used by NVDB
            elif gcmtyp == 8: # Koppling till annat nät (C+G)
                tags["highway"] = "path" # refined later
                gcm_resolve_crossings.append(way)
            elif gcmtyp == 9: # Annan cykelbar förbindelse (C)
                tags["highway"] = "path"
                tags["bicycle"] = "yes"
            elif gcmtyp == 10: # Annan ej cykelbar förbindelse (C+G)
                tags["highway"] = "path"
            elif gcmtyp == 11: # Gångbana (G)
                tags["highway"] = "footway"
            elif gcmtyp == 12: # Trottoar (G)
                tags["highway"] = "footway"
                tags["footway"] = "sidewalk"
            elif gcmtyp == 13: # Fortsättning i nätet (C+G)
                # generally a logical continuation of a sidewalk broken up by a parking lot
                tags["highway"] = "path" # refined later
                gcm_resolve_crossings.append(way)
            elif gcmtyp == 14: # Passage genom byggnad (G)
                tags["highway"] = "footway"
                tags["tunnel"] = "building_passage"
            elif gcmtyp == 15: # Ramp (G)
                tags["highway"] = "footway"
                tags["incline"] = "up"
                tags["wheelchair"] = "yes"
                tags["fixme"] = "could not resolve incline"
            elif gcmtyp == 16: # Perrong (G)
                tags["highway"] = "platform"
                tags["public_transport"] = "platform"
                tags["railway"] = "platform"
            elif gcmtyp == 17: # Trappa (C+G)
                tags["highway"] = "steps"
            elif gcmtyp == 18: # Rulltrappa (G)
                tags["highway"] = "steps"
                tags["conveying"] = "yes"
            elif gcmtyp == 19: # Rullande trottoar (G)
                tags["highway"] = "footway"
                tags["footway"] = "sidewalk"
                tags["conveying"] = "yes"
            elif gcmtyp == 20: # Hiss (G)
                tags["highway"] = "elevator"
            elif gcmtyp == 21: # Snedbanehiss (G)
                tags["highway"] = "elevator"
            elif gcmtyp == 22: # Linbana (G)
                tags["aerialway"] = "cablecar"
            elif gcmtyp == 23: # Bergbana (G)
                tags["railway"] = "funicular"
            elif gcmtyp == 24: # Torg (C+G)
                tags["highway"] = "footway"
            elif gcmtyp == 25: # Kaj (C+G)
                tags["highway"] = "footway"
            elif gcmtyp == 26: # Öppen yta (C+G)
                tags["highway"] = "path" # refined later
                gcm_resolve_crossings.append(way)
            elif gcmtyp == 27: # Färja (C+G)
                tags["route"] = "ferry"
            elif gcmtyp == 28: # Cykelpassage och övergångsställe (C+G)
                tags["highway"] = "cycleway"
                tags["cycleway"] = "crossing"
                tags["crossing"] = "marked"
            elif gcmtyp == 29: # Cykelbana ej lämplig för gång (C)
                tags["highway"] = "cycleway"
                tags["foot"] = "no"
            else:
                raise RuntimeError("Unknown GCM-typ %s" % gcmtyp)

        elif "NVDB_cykelvagkat" in way.tags:
            # value is one of "Regional cykelväg", "Huvudcykelväg", "Lokal cykelväg", we tag all the same
            tags["highway"] = "cycleway"
        elif "NVDB_gagata" in way.tags:
            # We ignore NVDB_gagata_side, from investigations it doesn't seem to provide any valuable information
            tags["highway"] = "pedestrian"
            if way.tags.get("width", 1000) < 3:
                # JOSM doesn't like pedestrian roads narrower than 3 meters
                tags["highway"] = "cycleway"
                way.tags.pop("maxspeed", None) # cycleways shouldn't have maxspeed
        elif "NVDB_gangfartsomrode" in way.tags:
            # We ignore NVDB_gangfartsomrode_side, from investigations it seems that even if
            # on only one side the speed limit is set to 5 km/h.
            tags["highway"] = "living_street"
        elif "NVDB_motorvag" in way.tags:
            tags["highway"] = "motorway"
        elif "NVDB_motortrafikled" in way.tags:
            tags["highway"] = "trunk"
            tags["motorroad"] = "yes"
        elif "NVDB_gatutyp" in way.tags and way.tags["NVDB_gatutyp"] != "Övergripande länk":
            gatutyp = way.tags["NVDB_gatutyp"]
            if gatutyp == "Övergripande länk":
                raise RuntimeError() # should already be handled
            if gatutyp == "Huvudgata":
                tags["highway"] = "residential"
            elif gatutyp == "Lokalgata stor":
                tags["highway"] = "residential"
            elif gatutyp == "Lokalgata liten":
                tags["highway"] = "residential"
            elif gatutyp == "Kvartersväg":
                tags["highway"] = "service"
            elif gatutyp == "Parkeringsområdesväg":
                tags["highway"] = "service"
                tags["service"] = "parking_aisle"
            elif gatutyp == "Infartsväg/Utfartsväg":
                tags["highway"] = "service"
            elif gatutyp == "Leveransväg":
                tags["highway"] = "unclassified"
            elif gatutyp == "Småväg":
                tags["highway"] = "unclassified"
            else:
                raise RuntimeError("Unknown gatutyp %s" % gatutyp)
        elif "ref" in way.tags: # road number

            # Note that even if a road has a road number (and is officially for example "Primär Länsväg") we
            # still use KLASS instead of road number to set primary/secondary/tertiary. It's common that
            # functional class changes even if the road number is the same (as the road gets into more rural areas,
            # functional class is often lowered)
            #
            # There is a less detailed function road class, FPVKLASS, which matches better to what is currently
            # mapped in OSM, so that is used when it results in a higher level than KLASS.
            #
            # A road with road number will not get worse than tertiary.
            #
            if not "KLASS" in way.tags:
                #raise RuntimeError("KLASS is missing for RLID %s (ref %s)" % (way.rlid, way.tags["NVDB_vagnummer"]));
                #print("Warning: KLASS is missing for RLID %s (ref %s)" % (way.rlid, way.tags["NVDB_vagnummer"]));
                tags["fixme"] = "could not resolve highway tag"
            else:
                fpvklass = int(way.tags.get("FPVKLASS", -1))
                if fpvklass in (1,2,3):
                    # secondary, primary or trunk.
                    fpv_level = fpvklass - 1
                else:
                    fpv_level = 1000

                klass = int(way.tags["KLASS"])
                if klass <= 1:
                    k_level = 0 # trunk
                elif klass <= 2:
                    k_level = 1 # primary
                elif klass <= 4:
                    k_level = 2 # secondary
                else:
                    k_level = 3 # tertiary

                if fpv_level < k_level:
                    k_level = fpv_level

                levels = [ "trunk", "primary", "secondary", "tertiary" ]
                tags["highway"] = levels[k_level]
        elif "KLASS" in way.tags:
            # KLASS (from DKFunkVagklass) on it's own is used here last as a fallback
            # when there is no other information to rely on. KLASS is a metric on how
            # important a road is, and it depends on context. KLASS 8 can for example
            # be used both on forestry roads in rural areas and on living and pedestrian
            # streets in a city.
            #
            # City roads should normally already been resolved by other layers, so here
            # we apply the highway tag as best suited in rural areas.
            #
            klass = int(way.tags["KLASS"])
            if way.tags.get("route", "") == "ferry":
                # Special case for ferry routes (shouldn't have a highway tag, but is
                # in NVDB classified with importance and thus have a KLASS tag, so we
                # need to ignore it)
                pass
            elif klass <= 1:
                tags["highway"] = "trunk"
            elif klass <= 2:
                tags["highway"] = "primary"
            elif klass <= 4:
                tags["highway"] = "secondary"
            elif klass <= 6:
                tags["highway"] = "tertiary"
            elif klass <= 8:
                tags["highway"] = "unclassified"
            else:
                tags["highway"] = "track"
        else:
            #print("Warning: information missing to resolve highway tag for RLID %s, adding fixme tag" % way.rlid)
            tags["fixme"] = "could not resolve highway tag"

        if "fixme" in tags:
            fixme_count += 1
        merge_translated_tags(way, tags)

    # Second pass for things we couldn't resolve in the first pass
    if len(gcm_resolve_crossings) > 0:
        # Rules for marking road/street crossings:
        #  if cycleway on both ends: make cycleway
        #  else if footway on both ends: make footway
        #  else if footway in one and and cycleway in the other: make footway
        #  else: make path
        endpoints = way_db.get_endpoint_map()
        tag_single_sided_as_cycleway = False
        tag_unconnected_as_footway = False
        while len(gcm_resolve_crossings) > 0:
            unconnected = []
            match = False
            has_single_sided = False
            for way in gcm_resolve_crossings:
                connecting_ways = ([], [])
                for idx, ep in enumerate([ way.way[0], way.way[-1] ]):
                    ways = endpoints.get(ep, []).copy()
                    ways.remove(way)
                    for w in ways:
                        hval = w.tags.get("highway", "")
                        if hval in ("cycleway", "footway"):
                            connecting_ways[idx].append(hval)

                tags = {}
                if len(connecting_ways[0]) == 0:
                    connecting_ways = tuple(reversed(connecting_ways))
                if len(connecting_ways[0]) == 0:
                    # not connected to cycleway/footway (usually middle segment in a crossing split in three or more segments
                    if tag_unconnected_as_footway:
                        tags["highway"] = "footway"
                    else:
                        unconnected.append(way)
                        continue
                if len(connecting_ways[1]) == 0:
                    # connected only on one side, usually due to crossing split in two or more segments
                    if "footway" in connecting_ways[0]:
                        tags["highway"] = "footway"
                    elif tag_single_sided_as_cycleway:
                        tags["highway"] = "cycleway"
                    else:
                        # could be joined by footway on other end, so we don't know yet how to tag
                        unconnected.append(way)
                        has_single_sided = True
                        continue
                else:
                    # connected on both sides, single-segment crossing
                    if "cycleway" in connecting_ways[0] and "cycleway" in connecting_ways[1]:
                        tags["highway"] = "cycleway"
                    else:
                        tags["highway"] = "footway"
                if way.tags.get("crossing", None) is not None:
                    tags[tags["highway"]] = "crossing"
                way.tags.pop("highway", None)
                assert "highway" in tags
                merge_translated_tags(way, tags)
                match = True

            if not match:
                if has_single_sided:
                    tag_single_sided_as_cycleway = True
                    gcm_resolve_crossings = unconnected
                elif len(unconnected) > 0:
                    tag_unconnected_as_footway = True

            gcm_resolve_crossings = unconnected

            if len(unconnected) > 0:
                _log.info(f"{len(unconnected)} unconnected crossings, making an additional pass")
        _log.info("all crossings resolved")

    if fixme_count > 0:
        _log.warning(f"could not resolve tags for {fixme_count} highway segments, added fixme tags")

    _log.info("done")

# sort_multiple_road_names()
#
# Sort road/street road names for segments that have more than one name.
# The sorting try to figure out which name is more prominent by assuming the lower KLASS number
# (from NVDB_DKFunkVagklass) is more prominent, and if that is the same, the longer way is used
#
# For roundabouts it is assumed that the main name is correct (as we set that before this is called),
# and then only the alt_name list is sorted
#
def sort_multiple_road_names(way_db):

    def get_all_names(way):
        name = way.tags.get("name", None)
        if name is None:
            return []
        alt_names = way.tags.get("alt_name", None)
        if alt_names is None:
            return [ name ]
        if not isinstance(alt_names, list):
            alt_names = [ alt_names ]
        return [ name ] + alt_names

    def any_in(list1, list2):
        for item in list1:
            if item in list2:
                return True
        return False

    def follow_road_name(way_db, way, name, other_names):
        len_sum, _ = calc_way_length(way.way)
        min_klass = way.tags.get("KLASS", 1000)
        if any_in(other_names, get_all_names(way)):
            min_klass = 1000
        match_set = set({ way })
        tried_set = set({ way })
        while len(match_set) > 0:
            new_match_set = set()
            for w in match_set:
                for ep in (w.way[0], w.way[-1]):
                    ways = way_db.gs.find_all_connecting_ways(ep)
                    for w1 in ways:
                        if w1 in tried_set:
                            continue
                        names = get_all_names(w1)
                        if name in names:
                            length, _ = calc_way_length(w1.way)
                            len_sum += length
                            new_match_set.add(w1)

                            # only consider KLASS if none of the other names is in this segment
                            if not any_in(names, other_names):
                                klass = int(w1.tags.get("KLASS", 1000))
                                if klass < min_klass:
                                    min_klass = klass
                        tried_set.add(w1)
            match_set = new_match_set
        return len_sum, min_klass

    def compare_nl_item(i1, i2):
        if i1[2] != i2[2]: # sort on KLASS, lowest number first
            return i1[2] - i2[2]
        if i1[1] != i2[1]: # sort on length, longest length first
            if i1[1] > i2[1]:
                return -1
            return 1
        # sort on name
        if i1[0] != i2[0]:
            if i1[0] > i2[0]:
                return 1
            return -1
        return 0

    _log.info("Sorting road/street names for those with multiple names...")
    sorted_names = []
    for way in way_db:
        names = get_all_names(way)
        if len(names) <= 1:
            continue
        orig_first_name = names[0]
        name_list = []
        for name in names:
            len_sum, min_klass = follow_road_name(way_db, way, name, [n for n in names if n != name])
            name_list.append((name, len_sum, min_klass))
        name_list.sort(key=cmp_to_key(compare_nl_item))
        sorted_names = [item[0] for item in name_list]
        if way.tags.get("junction", "") == "roundabout":
            # exemption for roundabouts, the main name should already be set for those
            sorted_names = [ orig_first_name ] + [n for n in sorted_names if n != orig_first_name]
        if names == sorted_names:
            continue
        way.tags["name"] = sorted_names[0]
        if len(sorted_names) > 2:
            way.tags["alt_name"] = sorted_names[1:]
        else:
            way.tags["alt_name"] = sorted_names[1]

    _log.info("done")

# simplify_speed_limits()
#
# Speed limits in NVDB often has direction. Here we merge such that if we have forward/backward
# with the same speed we remove the direction. Note however that there are real cases when
# maxspeed indeed is different backward vs forward.
#
def simplify_speed_limits(way_db):

    _log.info("Simplify speed limits...")
    for way in way_db:
        ms_f = way.tags.get("maxspeed:forward", None)
        ms_b = way.tags.get("maxspeed:backward", None)
        ms = way.tags.get("maxspeed", None)
        if ms is None and ms_f is None and ms_b is None:
            continue
        same_speeds = True
        speed = None
        speed_tags = [ms_f, ms_b, ms]
        for tag in speed_tags:
            if tag is not None:
                if speed is None:
                    speed = tag
                elif tag != speed:
                    same_speeds = False
                break
        if same_speeds:
            way.tags.pop("maxspeed:forward", None)
            way.tags.pop("maxspeed:backward", None)
            way.tags["maxspeed"] = speed
        elif ms_f is not None and ms_b is not None and ms is not None:
            merge_translated_tags(way, {"fixme": "too many maxspeeds"})
        elif ms is not None:
            if ms_b is not None:
                way.tags["maxspeed:forward"] = ms
            else:
                way.tags["maxspeed:backward"] = ms
            way.tags.pop("maxspeed", None)

    _log.info("done")


# simplify_oneway()
#
# Turn around oneways=-1 and remove redundant backward/forward prefixes
#
def simplify_oneway(way_db):
    _log.info("Simplify tags for oneway roads...")
    for way in way_db:

        # merge :backward/:forward into one key when applicable
        for k, v in list(way.tags.items()):
            if ":forward" in k and not "lanes:" in k:
                bw_key = k.replace(":forward", ":backward")
                plain_key = k.replace(":forward", "")
                if bw_key in way.tags and way.tags[bw_key] == v and way.tags.get(plain_key, v) == v:
                    del way.tags[k]
                    del way.tags[bw_key]
                    way.tags[plain_key] = v

        if not "oneway" in way.tags:
            continue

        # reverse oneway if necessary to avoid oneway=-1 tag which JOSM doesn't like
        oneway = way.tags["oneway"]
        if oneway == -1:
            reverse_way(way)
            oneway = "yes"

        if oneway != "yes":
            continue

        for k, v in list(way.tags.items()):
            #  Removing direction if it's the same as oneway, except for lanes
            if ":forward" in k and not "lanes:" in k:
                del way.tags[k]
                k = k.replace(":forward", "")
                way.tags[k] = v

            # Remove redundant backward vehicle restriction
            k_split = k.split(":backward")
            if len(k_split) > 1 and k_split[0] in ALL_VEHICLES and v == "no":
                del way.tags[k]
    _log.info("done")


# postprocess_miscellaneous_tags()
#
# postprocess tags that aren't dealt with in any other more specialized function
#
def postprocess_miscellaneous_tags(tags):
    spec_lane_count = 0
    for k, v in list(tags.items()):

        # count how many lanes that are specified
        if "lanes:" in k:
            if isinstance(v, int):
                spec_lane_count += v
            else:
                spec_lane_count += int(v.split()[0]) # if conditional, eg "1 @ ...."

    if not "lanes" in tags and "NVDB_guess_lanes" in tags:
        tags["lanes"] = tags["NVDB_guess_lanes"]

    if spec_lane_count > 0:
        total_count = tags.get("lanes", -1)
        if total_count == -1:
            append_fixme_value(tags, "total lane count (lanes=x) not specified")
        elif spec_lane_count > total_count:
            append_fixme_value(tags, "too many lanes specified")
        elif spec_lane_count < total_count:
            if not "lanes:forward" in tags and not "lanes:backward" in tags:
                if tags.get("oneway", "") == "yes":
                    tags["lanes:forward"] = total_count - spec_lane_count
                elif total_count - spec_lane_count == 2:
                    tags["lanes:forward"] = 1
                    tags["lanes:backward"] = 1
                else:
                    append_fixme_value(tags, "could not derive forward/backward lanes")
            else:
                append_fixme_value(tags, "too few lanes specified")

    # remove maxspeed for footways etc (seen in Stockholm data for example)
    if tags.get("highway", None) in [ "steps", "footway" ]:
        tags.pop("maxspeed", None)

# cleanup_used_nvdb_tags()
#
# Remove all tags that have been used when resolving various things
#
def cleanup_used_nvdb_tags(way_db_ways, in_use):
    used_keys = [
        "NVDB_vagnummer",
        "NVDB_gagata",
        "NVDB_gangfartsomrode",
        "NVDB_gangfartsomrode_side",
        "NVDB_gatutyp",
        "NVDB_motorvag",
        "NVDB_motortrafikled",
        "NVDB_generaliseringstyp",
        "NVDB_cykelvagkat",
        "NVDB_guess_lanes",
        "NVDB_gagata_side",
        "NVDB_layby_side",
        "KLASS",
        "FPVKLASS",
        "GCMTYP",
        "KONTRUTION",
        "OEPNINSBAR"
    ]
    for ways in way_db_ways.values():
        for way in ways:
            for key in used_keys:
                way.tags.pop(key, None)
            for key in NVDB_GEOMETRY_TAGS:
                way.tags.pop(key, None)
            for key in way.tags.keys():
                if not key in in_use:
                    in_use[key] = 1
                else:
                    in_use[key] += 1
    return in_use

# log_used_and_leftover_keys()
#
# Log all the keys we have used, and warn if there are keys left that haven't been translated.
#
def log_used_and_leftover_keys(in_use):
    _log.info("Current keys in use:")
    for k, v in in_use.items():
        _log.info(f"  '{k}': {v}")
        if k[0].isupper() and k != "NVDB:RLID" and k != "NVDB_extra_nodes":
            _log.warning(f"key {k} was not parsed")
