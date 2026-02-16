import logging
from functools import cmp_to_key

from geometry_basics import *
from geometry_search import GeometrySearch, snap_to_closest_way
from twodimsearch import TwoDimSearch
from merge_tags import merge_tags, append_fixme_value
from nvdb_segment import *
from proj_xy import latlon_str
from waydb import GEO_FILL_LENGTH
from tag_translations import ALL_VEHICLES
from nseg_tools import *

_log = logging.getLogger("process")

SMALL_ROAD_RESOLVE_ALGORITHMS = ['default', 'prefer_track', 'prefer_track_static', 'prefer_service', 'prefer_service_static']
MAJOR_HIGHWAYS = [ "trunk", "motorway", "primary", "secondary", "tertiary", "trunk_link", "motorway_link", "primary_link", "secondary_link", "tertiary_link" ]
MINOR_HIGHWAYS = [ "residential", "unclassified", "service", "track" ]

NVDB_USED_KEYS = [
    "NVDB_vagnummer",
    "NVDB_lansbeteckning",
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
    "NVDB_rwc_tracks",
    "NVDB_road_role",
    "NVDB_government_funded",
    "NVDB_availability_class",
    "NVDB_funk_klass",
    "FPVKLASS",
    "GCMTYP",
    "KONTRUTION",
    "OEPNINSBAR"
]

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
        if isinstance(way.way, list) and data_src_name not in ("NVDB-Hastighetsgrans", "NVDB-Vagnummer"):
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
        if way is None:
            # this can happen near borders where roads have been cut but laybys kept
            _log.warning(f"Did not find nearby way for layby {node.rlid}, keeping position as is")
            continue
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
            if node.tags.get("NVDB_layby_side", None) == "right":
                node.way.x = snap.x - xd
                node.way.y = snap.y - yd
            else:
                node.way.x = snap.x + xd
                node.way.y = snap.y + yd
            break
    return points

# preprocess_footcycleway_crossings
#
# NVDB NVDB-GCM_passage (crossings for cycleways and footways) points are often placed a bit
# beside the actual crossings so we need scan the geometry and find which crossings they belong
# and align.
#
# NVDB-GCM_vagtyp data must be in the database for this function to work.
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
            raise RuntimeError(f"Unhandled tag name {konst}")

    # First go through under passages, and convert to tunnel if needed.
    _log.info(f"Checking {len(underways)} under-passages relation to {len(bridges)} bridge segments...")
    SHORT_BRIDGE_LENGTH = 12
    delete_bridges = set()
    convert_to_tunnels = []
    for way in underways:
        crossings = bridges_lcs.find_crossing_ways(way)
        short_bridge_count = 0
        for bridge, _ in crossings:
            if is_short_bridge(bridge, bridges, SHORT_BRIDGE_LENGTH):
                short_bridge_count += 1
        if len(crossings) == 0:
            # this sometimes happens due to poor alignment or a missing bridge, but can also be crossed by railway bridges
            # (not included in the data)
            #print("Underfart %s not crossed" % way.rlid)
            pass
        elif short_bridge_count == len(crossings):
            #print("Underfart %s crossed only by %s short bridges, converting to tunnel and removing bridges" % (way.rlid, len(crossing)))
            convert_to_tunnels.append(way)
            for bridge, _ in crossings:
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
        if len(bridges_lcs.find_crossing_ways(way, abort_at_first=True)) > 0:
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

        if len(tunnels_lcs.find_crossing_ways(way, abort_at_first=True)) > 0:
            fixme_count += 1
            tags["layer"] = -1
            tags["fixme"] = "could not resolve layer"
        else:
            # no crossing ways => no layer tag
            if len(all_lcs.find_crossing_ways(way, abort_at_first=True)) > 0:
                tags["layer"] = -1

        merge_translated_tags(way, tags)
    _log.info('done')
    if fixme_count > 0:
        _log.warning(f"{fixme_count} tunnel segments crosses other tunnel, cannot resolve layers, fixme tags added")

    return bridges + tunnels + convert_to_tunnels


# process_street_crossings()
#
# Process the NVDB point layer Korsning and geometry it affects. This includes
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
                ways = way_db.gs.find_all_connecting_ways(w.way[0]).copy()
                ways.update(way_db.gs.find_all_connecting_ways(w.way[-1]))
                for w1 in ways:
                    if w1.tags.get("junction", "") == "roundabout":
                        nrbw.add(w1)
            rbw.update(nrbw)
            if len(rbw) == last_size:
                break
            last_size = len(rbw)
        return rbw

    named_rbw = set()
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
                named_rbw.add(w)
        if "highway" in node.tags:
            del node.tags["name"]
            crossings.append(node)
    if fixme_count > 0:
        _log.warning(f"did not find any way crossing for {fixme_count} street crossings, fixme tags added")


    # OSM mandates that roundabouts should not have street names, but only be named if the roundabout has
    # a specific name, so we make a second pass and remove
    remove_roundabout_street_names = True
    if remove_roundabout_street_names:
        remove_count = 0
        for way in way_db:
            if way.tags.get("junction", None) == "roundabout":
                way.tags.pop("alt_name", None)
                if way not in named_rbw:
                    if way.tags.pop("name", None) is not None:
                        remove_count += 1
        _log.info(f"Removed {remove_count} roundabout street names")

    return crossings

# preprocess_railway_crossings()
#
def preprocess_railway_crossings(points, way_db, railways):

    _log.info("Setting up search data structure for railways (to snap railway crossings)...")
    rw_gs = GeometrySearch(1000)
    for w in railways:
        rw_gs.insert(w)
    _log.info("done")

    fixme_count = 0
    rw_crossings = []
    for node in points:
        ways = way_db.gs.find_all_nearby_ways(node.way)
        cp = []
        crossing_tag = "level_crossing"
        for w in ways:
            if w.rlid == node.rlid:
                if "NVDB_funk_klass" not in w.tags:
                    crossing_tag = "crossing"
                crossings = rw_gs.find_crossing_ways(w)
                for w_and_cp in crossings:
                    crossing_point = w_and_cp[1]
                    dist = dist2d(node.way, crossing_point)
                    cp.append((dist, crossing_point))
        cp = sorted(cp, key=lambda x: x[0])
        fixme = False
        node.tags["railway"] = crossing_tag
        if len(cp) == 0:
            fixme = True
            rw_crossings.append(node)
        else:
            # Snap to suitable crossing(s)
            track_count = node.tags.get("NVDB_rwc_tracks", 1)
            for i in range(0, track_count):
                try:
                    dist = cp[i][0]
                except IndexError:
                    _log.warning(f"More tracks than crossings {track_count} {i} {cp}")
                    dist = 500
                # as we match RLID it's low risk to get the crossing wrong, so we can use a large max dist
                # Offset errors of 150 meters have been observed (Lycksele data set)
                if dist > 200:
                    fixme = True
                    rw_crossings.append(node)
                    break
                crossing_point = cp[i][1]
                rwc = node.make_copy_new_way(crossing_point)
                rw_crossings.append(rwc)
        if fixme:
            fixme_count += 1
            merge_translated_tags(node, {"fixme": "no nearby railway crossing found"})

    if fixme_count > 0:
        _log.warning(f"did not find any actual crossing between railway and way for {fixme_count} railway crossings, fixme tags added")
    return rw_crossings

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

# resolve_vagnummer()
#
# fix road number formatting
#
def resolve_vagnummer(way):
    if "NVDB_vagnummer" not in way.tags:
        return
    refs = way.tags["NVDB_vagnummer"]
    lan = way.tags.get("NVDB_lansbeteckning", "NVDB_lansbeteckning_missing")
    if isinstance(refs, list):
        refs = [str(r).replace("NVDB_lansbeteckning", lan) for r in refs]
        refs.sort(key=cmp_to_key(compare_vagnummer))
    else:
        refs = str(refs).replace("NVDB_lansbeteckning", lan)
    way.tags["ref"] = refs

# resolve_highways()
#
# Using information from multiple layers, figure out what the highway tag should be (and some side tags)
#
def resolve_highways(way_db, small_road_resolve_algorithm):

    _log.info("Resolve highway tags...")
    fixme_count = 0
    gcm_resolve_crossings = []
    for way in way_db:

        # convert tags
        resolve_vagnummer(way)

        klass = int(way.tags.get("NVDB_funk_klass", -1))
        tags = {}
        if "GCMTYP" in way.tags:
            # Note GCM-typ values was changed by Trafikverket in November 2021. This code handles only the new values
            gcmtyp = way.tags["GCMTYP"]
            if gcmtyp in (100, "Gång- och cykelbana"):
                tags["highway"] = "cycleway"
                tags["foot"] = "yes"
            elif gcmtyp in (105, "Gång- och cykelbana, uppdelad"):
                tags["highway"] = "cycleway"
                tags["segregated"] = "yes"
                tags["foot"] = "yes"
            elif gcmtyp in (110, "Cykelbana, påbjuden"):
                tags["highway"] = "cycleway"
                tags["foot"] = "no"
            elif gcmtyp in (115, "Gångbana"):
                tags["highway"] = "footway"
            elif gcmtyp in (120, "Cykelfält"):
                tags["highway"] = "cycleway"
            elif gcmtyp in (125, "Cykelpassage och övergångsställe"):
                # TODO difference with cykelöverfart not seen. Cykelpassage = bilar har ingen väjningsplikt för cyklar
                tags["highway"] = "cycleway"
                tags["cycleway"] = "crossing"
                tags["crossing"] = "marked"
                tags["foot"] = "yes"
            elif gcmtyp in (130, "Cykelöverfart och övergångsställe"):
                tags["highway"] = "cycleway"
                tags["cycleway"] = "crossing"
                tags["crossing"] = "marked"
                tags["foot"] = "yes"
            elif gcmtyp in (135, "Cykelpassage"):
                # Defined as for cycling only, but in some places it's connected to "gång- och cykelbana" on both sides
                tags["highway"] = "cycleway"
                gcm_resolve_crossings.append(way)
            elif gcmtyp in (140, "Cykelöverfart"):
                tags["highway"] = "cycleway"
                tags["cycleway"] = "crossing"
                tags["crossing"] = "marked"
            elif gcmtyp in (145, "Övergångsställe"):
                # Defined as footway only, but unfortunately in many places in NVDB it's also used for cycleways
                tags["crossing"] = "marked"
                tags["highway"] = "path" # refined later
                gcm_resolve_crossings.append(way)
            elif gcmtyp in (150, "Gatupassage utan utmärkning"):
                # This is mostly used for unmarked footway crossings, but in some situations
                # it's also a cycleway crossing, we need to resolve that by looking at connecting ways
                tags["crossing"] = "unmarked"
                tags["highway"] = "path" # refined later
                gcm_resolve_crossings.append(way)
            elif gcmtyp in (155, "Trappa"):
                tags["highway"] = "steps"
            elif gcmtyp in (160, "Torg/Öppen yta"):
                tags["highway"] = "cycleway"
                tags["foot"] = "yes"
            elif gcmtyp in (165, "Annan cykelbar förbindelse"): # Annan cykelbar förbindelse
                # This type unfortunately has multi-uses. In larger cities it's commonly used to
                # connect disconnected cycleways, eg in places you need to pass 10 - 20 meters of
                # pavement to get on to the next section. But it's also used for longer sections
                # of unpaved tracks that make practical links for cyclists but are not really
                # maintained as cycleways (this is the official definition in NVDB).
                #
                # To differ between these we look at road surface, and if it's marked oneway
                # (happens in some cases in cities) we also upgrade it to cycleway
                #
                if "oneway" in way.tags or way.tags.get("surface", "unpaved") != "unpaved":
                    tags["highway"] = "cycleway"
                    tags["foot"] = "yes"
                else:
                    tags["highway"] = "path"
                    tags["bicycle"] = "yes"
            elif gcmtyp in (170, "Annan ej cykelbar förbindelse"):
                # These may be ridable anyway, so we don't dare to set bicycle=no
                tags["highway"] = "path"
            elif gcmtyp in (175, "Hiss"):
                tags["highway"] = "elevator"
            else:
                raise RuntimeError(f"Unknown GCM-typ {gcmtyp} for {way.rlid}")

        # NOTE: Some ways are double tagged with both
        #       Cykelvägskategorier and Gatutyp/Vägtyp.
        elif "NVDB_cykelvagkat" in way.tags \
             and "NVDB_gatutyp" not in way.tags \
             and "NVDB_funk_klass" not in way.tags:
            # value is one of "Regional cykelväg", "Huvudcykelväg", "Lokal cykelväg", we tag all the same
            tags["highway"] = "cycleway"
            tags["foot"] = "yes"
        elif "NVDB_gagata" in way.tags:
            # We ignore NVDB_gagata_side, from investigations it doesn't seem to provide any valuable information
            tags["highway"] = "pedestrian"
            if way.tags.get("width", 1000) < 3:
                # JOSM doesn't like pedestrian roads narrower than 3 meters
                tags["highway"] = "cycleway"
                tags["foot"] = "yes"
                way.tags.pop("maxspeed", None) # cycleways shouldn't have maxspeed
        elif "NVDB_gangfartsomrode" in way.tags:
            # We ignore NVDB_gangfartsomrode_side, from investigations it seems that even if
            # on only one side the speed limit is set to 5 km/h.
            tags["highway"] = "living_street"
        elif "NVDB_motorvag" in way.tags: # replaced by more detailed Gatutyp in AGGREGAT-Vagslag
            tags["highway"] = "motorway"
        elif "NVDB_motortrafikled" in way.tags: # replaced by more detailed Gatutyp in AGGREGAT-Vagslag
            tags["highway"] = "trunk"
            tags["motorroad"] = "yes"
        elif "ref" in way.tags: # road number

            # Note that even if a road has a road number (and is officially for example "Primär Länsväg") we
            # still use NVDB_funk_klass instead of road number to set primary/secondary/tertiary. It's common that
            # functional class changes even if the road number is the same (as the road gets into more rural areas,
            # functional class is often lowered)
            #
            # There is a less detailed function road class, FPVKLASS, which matches better to what is currently
            # mapped in OSM, so that is used when it results in a higher level than NVDB_funk_klass.
            #
            # A road with road number will not get worse than tertiary.
            #
            if klass == -1:
                #raise RuntimeError("NVDB_funk_klass is missing for RLID %s (ref %s)" % (way.rlid, way.tags["NVDB_vagnummer"]));
                #print("Warning: NVDB_funk_klass is missing for RLID %s (ref %s)" % (way.rlid, way.tags["NVDB_vagnummer"]));
                tags["fixme"] = "could not resolve highway tag"
            else:
                fpvklass_translations = {
                    "Nationella vägar": 0,
                    "Regionalt viktiga vägar": 1,
                    "Kompletterande regionalt viktiga vägar": 2,
                    1: 0,
                    2: 1,
                    3: 2
                }
                if way.tags.get("FPVKLASS", -1) not in fpvklass_translations:
                    fpv_level = 1000
                else:
                    fpv_level = fpvklass_translations[way.tags.get("FPVKLASS", -1)]

                klass = int(way.tags["NVDB_funk_klass"])
                if klass <= 1:
                    k_level = 0 # trunk
                elif klass <= 2:
                    k_level = 1 # primary
                elif klass <= 4:
                    k_level = 2 # secondary
                else:
                    k_level = 3 # tertiary

                k_level = min(k_level, fpv_level)

                levels = [ "trunk", "primary", "secondary", "tertiary" ]
                tags["highway"] = levels[k_level]
        elif "NVDB_gatutyp" in way.tags and way.tags["NVDB_gatutyp"] != "Övergripande länk":
            gatutyp = way.tags["NVDB_gatutyp"]
            if gatutyp == "Övergripande länk":
                raise RuntimeError() # should already be handled

            if gatutyp == "Motorväg":
                tags["highway"] = "motorway"
            elif gatutyp == "Motortrafikled":
                tags["highway"] = "trunk"
                tags["motorroad"] = "yes"
            elif gatutyp == "Mötesfri väg":
                tags["highway"] = "trunk"
            elif gatutyp == "Huvudgata":
                if klass <= 1:
                    tags["highway"] = "trunk" # 0, 1
                elif klass <= 2:
                    tags["highway"] = "primary" # 2
                elif klass <= 4:
                    tags["highway"] = "secondary" # 3, 4
                elif klass <= 5:
                    tags["highway"] = "tertiary" # 5
                else:
                    tags["highway"] = "residential"
            elif gatutyp == "Landsväg": # should already be handled through road number
                tags["highway"] = "unclassified"
            elif gatutyp == "Landsväg liten": # should already be handled through road number
                tags["highway"] = "unclassified"
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
            elif gatutyp == "Småväg enkel standard":
                tags["highway"] = "track"
            elif gatutyp == "Oklassificerad":
                tags["highway"] = "track"
            else:
                raise RuntimeError(f"Unknown gatutyp {gatutyp}")
        elif "NVDB_funk_klass" in way.tags:
            # NVDB_funk_klass (from FunkVagklass) on it's own is used here last as a fallback
            # when there is no other information to rely on. NVDB_funk_klass is a metric on how
            # important a road is, and it depends on context. NVDB_funk_klass 8 can for example
            # be used both on forestry roads in rural areas and on living and pedestrian
            # streets in a city.
            #
            # For forestry roads the official definition is: 7 huvudväg, 8 normalväg,
            # 9, nollväg. However, the distinction between 8 and 9 in the actual NVDB
            # data is not that good. From testing the least bad default seems to be
            # to map both 8 and 9 to track.
            #
            # City roads should normally already been resolved by other layers, so here
            # we apply the highway tag as best suited in rural areas. Exception:
            # The NVDB-Gatunamn which provides NVDB_road_role tag is used to differ
            # between service/unclassified and track on NVDB_funk_klass 8 and 9. (Names on forestry
            # and other private roads comes from NVDB-Ovrigt_vagnamn and doesn't have
            # role tag set)
            #
            # Special case for ferry routes (shouldn't have a highway tag)
            prefer_service = small_road_resolve_algorithm in ['prefer_service', 'prefer_service_static']
            if klass <= 1:
                tags["highway"] = "trunk" # 0, 1
            elif klass <= 2:
                tags["highway"] = "primary" # 2
            elif klass <= 4:
                tags["highway"] = "secondary" # 3, 4
            elif klass <= 6:
                tags["highway"] = "tertiary" # 5, 6
            elif klass <= 7:
                tags["highway"] = "unclassified" # 7
            elif klass <= 8:
                if way.tags.get("NVDB_government_funded", "no") == "yes" or "NVDB_road_role" in way.tags:
                    tags["highway"] = "unclassified"  # 8
                elif "NVDB_availability_class" not in way.tags and prefer_service:
                    tags["highway"] = "service" # 8
                else:
                    tags["highway"] = "track" # 8
            else:
                if way.tags.get("NVDB_government_funded", "no") == "yes" or "NVDB_road_role" in way.tags or \
                   "NVDB_availability_class" not in way.tags and prefer_service:
                    tags["highway"] = "service" # 9
                else:
                    tags["highway"] = "track" # 9

            # Special case for ferry
            if way.tags.get("route", None) == "ferry":
                tags["ferry"] = tags["highway"]
                tags.pop("highway")
                if tags["ferry"] in [ "track", "service" ]:
                    tags["ferry"] = "unclassified"
                tags["foot"] = "yes"
                tags["bicycle"] = "yes"
                tags["motor_vehicle"] = "yes"
        else:
            #print("Warning: information missing to resolve highway tag for RLID %s, adding fixme tag" % way.rlid)
            tags["fixme"] = "could not resolve highway tag"

        # check if we should make this a link
        if tags.get("highway", None) in ["motorway", "trunk", "primary", "secondary", "tertiary"] and \
           way.tags.get("NVDB_road_role", None) == 4 and way.tags.get("junction", None) != "roundabout":
            tags['highway'] += "_link"

        if "fixme" in tags:
            fixme_count += 1
        merge_translated_tags(way, tags)

    # Second pass for things we couldn't resolve in the first pass

    if len(gcm_resolve_crossings) > 0:
        # group together all crossing segments that are connected to eachother
        crossings = []
        processed_set = set()
        _log.debug(f"Resolving {len(gcm_resolve_crossings)} GCM crossing segments")
        for way in gcm_resolve_crossings:
            if way in processed_set:
                continue
            crossings.append([ way ])
            processed_set.add(way)
            # in rare occasions way is a loop, the set() trick makes sure we don't run the same endpoint twice
            for ep in set([ way.way[0], way.way[-1] ]):
                ways = way_db.gs.find_all_connecting_ways(ep)
                ways.remove(way)
                for w in ways:
                    if w in gcm_resolve_crossings and w not in processed_set:
                        crossings[-1].append(w)
                        processed_set.add(w)
        _log.debug(f"Resolving {len(crossings)} GCM crossings")

        # if the crossing has two or more cycleway connections at different endpoints, make cycleway,
        # if the crossing has only one cycleway connection but no footway connection (at a different endpoint), still make cycleway,
        # otherwise make footway
        for crossing in crossings:
            cw_count = 0
            fw_count = 0
            for way in crossing:
                for ep in set([ way.way[0], way.way[-1] ]):
                    ways = way_db.gs.find_all_connecting_ways(ep)
                    connected_to_footway = False
                    for w in ways:
                        if w.tags.get("highway", None) == "cycleway":
                            cw_count += 1
                            connected_to_footway = False # If connected to both, we only count cycleway
                            break
                        if w.tags.get("highway", None) == "footway":
                            connected_to_footway = True
                    if connected_to_footway:
                        fw_count += 1
            _log.debug(f"Crossing {crossing[0].rlid} has {cw_count} cw and {fw_count} fw")
            for way in crossing:
                if (cw_count == 1 and fw_count == 0) or cw_count > 1:
                    way.tags["highway"] = "cycleway"
                    way.tags["cycleway"] = "crossing"
                    way.tags["foot"] = "yes"
                else:
                    way.tags["highway"] = "footway"
                    way.tags["footway"] = "crossing"

    if fixme_count > 0:
        _log.warning(f"could not resolve tags for {fixme_count} highway segments, added fixme tags")

    _log.info("done")



# get_connected_roads()
#
def get_connected_roads(ways, gs, criteria_fun):
    processed = set()
    roads = []
    for way in ways:
        if way in processed or not criteria_fun(way):
            continue
        road = set()
        new_segs = { way }
        while len(new_segs) > 0:
            road.update(new_segs)
            prev_segs = new_segs
            new_segs = set()
            for w0 in prev_segs:
                for w in gs.find_all_connecting_ways([w0.way[0], w0.way[-1]]):
                    if w not in road and criteria_fun(w):
                        new_segs.add(w)
        processed.update(road)
        roads.append(road)
    return roads


# upgrade_unclassified_stumps_connected_to_residential
#
def upgrade_unclassified_stumps_connected_to_residential(way_db):

    _log.info("Upgrading short unclassified stumps to residential (if connected to residential)...")
    roads = get_connected_roads(way_db, way_db.gs, lambda way: way.tags.get("highway", None) == "unclassified")
    upgrade_count = 0
    for road in roads:
        total_length = 0
        has_connected_residential = False
        for way in road:
            length, _ = calc_way_length(way.way)
            total_length += length
            if total_length > 1000:
                break
            if not has_connected_residential:
                for w in way_db.gs.find_all_connecting_ways([way.way[0], way.way[-1]]):
                    if w not in road and w.tags.get("highway", None) == "residential":
                        has_connected_residential = True
                        break

        if total_length <= 1000 and has_connected_residential:
            for way in road:
                _log.debug(f"Upgraded {way.rlid} from unclassified to residential due to being short stump connected to residential.")
                way.tags["highway"] = "residential"
                upgrade_count += 1
    _log.info(f"done ({upgrade_count} segments upgraded from unclassified to residential)")


# guess_upgrade_tracks
#
# There's not enough information for small roads (NVDB_funk_klass (7) 8, 9) so highway tag cannot be 100%
# correctly resolved, so manual adjustment will be required. The goal of this function is to
# make guesses that minimizes the need of manual adjustment
#
# Info not used and why:
#   väghållare / road maintainer:
#     - forest companies also maintain roads that we want to tag service
#     - in many municipalities all väghållare is just the same for 8/9, "enskild" with no further
#       information
#   tillgänglighetsklass / availability class (NVDB-Tillganglighet A,B,C,D):
#     - actual value has quirky contents in forestry network, many roads at a higher class than it
#       should be
#     - however if the value exists or not is a lead, value doesn't exist on driveways, unfortunately
#       it's quite often missing also on some forestry roads and other tracks as well
#
#
# This function must be run after resolve_highways so the basic work is already done
#
def guess_upgrade_tracks(way_db):

    def get_deadend_parent_ways(way):
        ways1 = way_db.gs.find_all_connecting_ways(way.way[0])
        ways2 = way_db.gs.find_all_connecting_ways(way.way[-1])
        if len(ways1) == 1 and len(ways2) > 1:
            ways2 = ways2.copy()
            return [w for w in ways2 if w != way], way.way[-1]
        if len(ways1) > 1 and len(ways2) == 1:
            ways1 = ways1.copy()
            return [w for w in ways1 if w != way], way.way[0]
        return None, None

    def way_has_a_gate(way):
        for p in way.way:
            if p in way_db.point_db:
                nodes = way_db.point_db[p]
                for node in nodes:
                    if node.tags.get("barrier", None) == "gate":
                        return True
        return False

    def is_deadend(way):
        ways, _ = get_deadend_parent_ways(way)
        return ways is not None

    def angle_between_ways(cp, w1, w2, go_right=True):
        p1 = None
        p3 = None
        for idx, p in enumerate(w1.way):
            if p == cp:
                if go_right:
                    if idx == len(w1.way)-1:
                        p1 = w1.way[idx-1]
                    else:
                        p1 = w1.way[idx+1]
                else:
                    if idx == 0:
                        p1 = w1.way[idx+1]
                    else:
                        p1 = w1.way[idx-1]
                break
        for idx, p in enumerate(w2.way):
            if p == cp:
                if go_right:
                    if idx == len(w2.way)-1:
                        p3 = w2.way[idx-1]
                    else:
                        p3 = w2.way[idx+1]
                else:
                    if idx == 0:
                        p3 = w2.way[idx+1]
                    else:
                        p3 = w2.way[idx-1]
                break
        assert p1 is not None
        assert p3 is not None
        xa = p1.x - cp.x
        ya = p1.y - cp.y
        xb = p3.x - cp.x
        yb = p3.y - cp.y
        denom = math.sqrt(xa*xa + ya*ya) * math.sqrt(xb*xb + yb*yb)
        if denom != 0:
            q = (xa * xb + ya * yb) / denom
            if q < -1:
                # this can happen due to precision limitation, -1.0000000000000002 seen in tests
                angle = 180
            elif q > 1:
                angle = 0
            else:
                angle = math.acos((xa * xb + ya * yb) / denom) * 180 / math.pi
        else:
            angle = 0
        return angle

    def has_track_name(way):
        if not "name" in way.tags:
            return False
        strings = [
            " stick",
            " gren",
            " stv",
            " grv"
        ]
        name = way.tags["name"]
        for s in strings:
            if s in name:
                return True
        return False

    ROAD_TAGS = MAJOR_HIGHWAYS + MINOR_HIGHWAYS
    ROAD_TAGS.remove("track")
    DW_DISTANCE = 300

    _log.info("Making best guesses of upgrading highway=track to highway=unclassified or service...")

    #
    # Go through all roads and pick up all tracks that may be upgraded and put it in the "undecided" set
    #
    undecided = set()
    current_service_roads = set()
    leads_nowhere = set()
    gate_count = 0
    name_count = 0
    current_service_roads_gs = GeometrySearch(DW_DISTANCE)
    for way in way_db:
        hw = way.tags.get("highway", None)
        if hw == "track":
            # exclude all tracks that have gates, this will lead to a few false positives but not too many
            if has_track_name(way):
                name_count += 1
            elif way_has_a_gate(way):
                gate_count += 1
            else:
                if is_deadend(way):
                    leads_nowhere.add(way)
                undecided.add(way)
        elif hw == "service":
            current_service_roads.add(way)
            current_service_roads_gs.insert(way)

    orig_count = len(undecided)
    _log.info(f"  {orig_count} tracks to be considered for upgrading (skipped {gate_count} as they had gates, and {name_count} with typical forestry branch road names)")

    #
    # Collect the tracks in undecided that all lead up to a dead end (following undecided tracks) in
    # the leads_nowhere set
    #
    def leads_nowhere_iteration(newest_leads_nowhere, leads_nowhere, undecided):
        also_leads_nowhere = set()
        for way in newest_leads_nowhere:
            test_ways = set()
            for w0 in way_db.gs.find_all_connecting_ways([way.way[0], way.way[-1]]):
                if w0 not in leads_nowhere and w0 in undecided:
                    test_ways.add(w0)
            for w0 in test_ways:
                for ep in (w0.way[0], w0.way[-1]):
                    ways = way_db.gs.find_all_connecting_ways(ep)
                    deadend_for_sure = True
                    for w1 in ways:
                        if w1 != w0 and w1 not in leads_nowhere:
                            deadend_for_sure = False
                            break
                    if deadend_for_sure:
                        also_leads_nowhere.add(w0)
                        break
        return also_leads_nowhere

    also_leads_nowhere = leads_nowhere
    while len(also_leads_nowhere) > 0:
        also_leads_nowhere = leads_nowhere_iteration(also_leads_nowhere, leads_nowhere, undecided)
        leads_nowhere.update(also_leads_nowhere)



    #
    # Upgrade roads that connect larger roads to unclassified
    #
    roads = get_connected_roads(undecided, way_db.gs, \
                                lambda w : w not in leads_nowhere and w in undecided and int(w.tags.get("NVDB_funk_klass", 9)) <= 8)
    larger_road_tags = MAJOR_HIGHWAYS + MINOR_HIGHWAYS
    larger_road_tags.remove("track")
    larger_road_tags.remove("service")
    upgraded = set()
    for road in roads:
        ext_connected_eps = 0
        for w0 in road:
            for ep in (w0.way[0], w0.way[-1]):
                for w in way_db.gs.find_all_connecting_ways(ep):
                    if w not in road and w.tags.get("highway", None) in larger_road_tags:
                        ext_connected_eps += 1
                        break
        if ext_connected_eps >= 2:
            for w0 in road:
                w0.tags["highway"] = "unclassified"
            upgraded.update(road)
    undecided -= upgraded
    _log.info(f"  {len(upgraded)} tracks upgraded to unclassified as they form connecting links")

    #
    # Go through all ways that lead nowhere, and see which are quite likely driveways
    #
    processed = set()
    driveway_candidates = set()
    for way in leads_nowhere:
        if way in processed or way not in undecided:
            continue

        isolated_road = True
        road = set()
        new_segs = { way }
        while len(new_segs) > 0:
            road.update(new_segs)
            prev_segs = new_segs
            new_segs = set()
            for w0 in prev_segs:
                for w in way_db.gs.find_all_connecting_ways([w0.way[0], w0.way[-1]]):
                    if w in road:
                        continue
                    if w in leads_nowhere and w in undecided:
                        new_segs.add(w)
                    elif w in undecided or w.tags.get("highway", None) in ROAD_TAGS:
                        isolated_road = False
        processed.update(road)

        if isolated_road:
            # This road leads nowhere and the only entrance is via a decided track (or path)
            # Then it's most likely not leading to housing, so we keep it as track.
            undecided -= road
            continue

        # check which parts of the road that are candidates for likely driveways
        for w in road:
            pways, cp = get_deadend_parent_ways(w)
            if pways is None:
                # way segment not a dead end, not a driveway
                continue
            length, _ = calc_way_length(w.way)
            has_connected_midpoints = len(way_db.gs.find_all_connecting_ways(w.way[1:-1])) > 1
            if length > 150 or has_connected_midpoints:
                # a bit too long or connected for being a likely driveway
                continue
            min_angle = 180
            for pway in pways:
                min_angle = min(angle_between_ways(cp, w, pway, go_right=True), min_angle)
                min_angle = min(angle_between_ways(cp, w, pway, go_right=False), min_angle)
            if min_angle < 100:
                # connecting at a sharp angle, good driveway candidate
                driveway_candidates.add(w)

    # Filter out driveway candidates which has a nearby neighbor. At least one neighbor required to make
    # it a likely enough driveway to consider it for upgrade
    #neighbor_driveway_candidates = candidates_with_nearby_neighbor(driveway_candidates, current_service_roads, 300)
    neighbor_driveway_candidates = set()
    gs = GeometrySearch(DW_DISTANCE)
    for way in driveway_candidates:
        gs.insert(way)
    for way in driveway_candidates:
        if way in neighbor_driveway_candidates:
            continue
        ways = gs.find_all_nearby_ways([way.way[0], way.way[-1]])
        ways.update(current_service_roads_gs.find_all_nearby_ways([way.way[0], way.way[-1]]))
        if len(ways) >= 2:
            for w in ways:
                neighbor_driveway_candidates.add(w)

    directly_connected = 0
    #
    # Upgrade filtered driveway candidates directly connected to a larger road
    #
    for way in neighbor_driveway_candidates:
        if way not in undecided:
            continue
        connected_to_larger_road = False
        for w in way_db.gs.find_all_connecting_ways([way.way[0], way.way[-1]]):
            if w.tags.get("highway", None) in ROAD_TAGS:
                connected_to_larger_road = True
                break
        if not connected_to_larger_road:
            continue
        current_service_roads.add(way)
        current_service_roads_gs.insert(way)
        undecided.remove(way)
        way.tags["highway"] = "service"
        directly_connected += 1
    _log.info(f"  {directly_connected} tracks upgraded to service as likely driveways connected to larger roads")

    # Add driveway candidates *not* connected to a larger road too,
    # but only if close to a driveway that is connected
    upgraded = set()
    for way in neighbor_driveway_candidates:
        if way in undecided and len(current_service_roads_gs.find_all_nearby_ways([way.way[0], way.way[-1]])) >= 2:
            way.tags["highway"] = "service"
            upgraded.add(way)
    _log.info(f"  {len(upgraded)} tracks upgraded to service as likely driveways near others")
    for way in upgraded:
        current_service_roads.add(way)
        current_service_roads_gs.insert(way)
    undecided -= upgraded

    # Upgrade tracks with asphalt surface to service
    upgraded = set()
    for way in undecided:
        if way.tags.get("surface", "unpaved") == "asphalt":
            way.tags["highway"] = "service"
            upgraded.add(way)
    for way in upgraded:
        current_service_roads.add(way)
        current_service_roads_gs.insert(way)
    undecided -= upgraded
    _log.info(f"  {len(upgraded)} tracks upgraded to service as they have asphalt surface")

    # Upgrade tracks that form links between larger road and current service roads, but only if they
    # do so within a single segment.
    # There are cases when more segments could be followed, but they are few enough to not care,
    # the upgrade can not be 100% correct in any case.
    upgraded = set()
    for way in undecided:
        has_service_connection = [ False, False ]
        has_road_connection = [ False, False ]
        for i, ep in enumerate([way.way[0], way.way[-1]]):
            for w in way_db.gs.find_all_connecting_ways(ep):
                if w == way:
                    continue
                if w in current_service_roads:
                    has_service_connection[i] = True
                elif w.tags.get("highway", None) in ROAD_TAGS:
                    has_road_connection[i] = True
        if not has_road_connection[0] and not has_road_connection[1]:
            continue
        if has_road_connection[0] != has_road_connection[1]:
            # if not connected in both ends, don't count service connection on the same end as road connection
            if has_road_connection[0]:
                has_service_connection[0] = False
            if has_road_connection[1]:
                has_service_connection[1] = False
        has_service_connection = has_service_connection[0] or has_service_connection[1]
        if not has_service_connection:
            for w in way_db.gs.find_all_connecting_ways(way.way[1:-1]):
                if w in current_service_roads:
                    has_service_connection = True
                    break
        if has_service_connection:
            way.tags["highway"] = "service"
            upgraded.add(way)
    for way in upgraded:
        current_service_roads.add(way)
        current_service_roads_gs.insert(way)
    undecided -= upgraded

    _log.info(f"  {len(upgraded)} tracks upgraded to service as they form short links between roads and driveways")

    _log.info(f"done ({orig_count - len(undecided)} of {orig_count} tracks upgraded to service)")


# sort_multiple_road_names()
#
# Sort road/street road names for segments that have more than one name.
# The sorting try to figure out which name is more prominent by assuming the lower NVDB_funk_klass number
# (from NVDB-FunkVagklass) is more prominent, and if that is the same, the longer way is used
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
        min_klass = way.tags.get("NVDB_funk_klass", 1000)
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

                            # only consider NVDB_funk_klass if none of the other names is in this segment
                            if not any_in(names, other_names):
                                klass = int(w1.tags.get("NVDB_funk_klass", 1000))
                                min_klass = min(min_klass, klass)
                        tried_set.add(w1)
            match_set = new_match_set
        return len_sum, min_klass

    def compare_nl_item(i1, i2):
        if i1[2] != i2[2]: # sort on NVDB_funk_klass, lowest number first
            return i1[2] - i2[2]
        if i1[1] != i2[1]: # sort on length, longest length first
            if i1[1] > i2[1]:
                return -1
            return 1
        # sort on name
        if i1[0] != i2[0]:
            if str(i1[0]) > str(i2[0]):
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

# simplify_cycleway_crossings()
#
# Simplify cycleway (and footway) crossings, meaning converting from way crossings to node crossings.
# This is simplifying is optional, both ways to map is correct. The advantage of node crossings is
# that cycleways doesn't get as many splits so they are a bit easier to work with manually
#
def simplify_cycleway_crossings(way_db):
    _log.info("Converting cycleway way crossings to node crossings...")
    GCM = ["cycleway", "footway", "path" ]
    count = 0
    skipped_count = 0
    no_crossing_count = 0
    processed_set = set()
    for way in way_db:
        if way in processed_set or way.tags.get("highway", None) not in GCM or way.tags.get(way.tags["highway"], None) != "crossing":
            continue

        # tags to be used for crossing node
        crossing_tags = { "highway": "crossing" }
        if "crossing" in way.tags:
            crossing_tags["crossing"] = way.tags["crossing"]
        if way.tags["highway"] == "cycleway" or way.tags.get("bicycle", None) == "yes":
            crossing_tags["bicycle"] = "yes"

        # crossing ways may be split in several parts, get all that are connected via endpoints
        crossing_set = { way }
        start_size = 0
        hw_tag = way.tags["highway"]
        while start_size != len(crossing_set):
            start_size = len(crossing_set)
            new_set = set()
            for w0 in crossing_set:
                for ep in [ w0.way[0], w0.way[-1] ]:
                    ways = way_db.gs.find_all_connecting_ways(ep)
                    for w1 in ways:
                        if w1 not in crossing_set and ep in (w1.way[0], w1.way[-1]) and \
                           w1.tags.get("highway", None) == hw_tag and \
                           w1.tags.get(hw_tag, None) == "crossing" and \
                           w1.tags.get("crossing", None) == way.tags.get("crossing", None):
                            new_set.add(w1)
            crossing_set = crossing_set.union(new_set)

        _log.debug(f"crossing_set {crossing_set}")
        crossings = []
        has_cw_crossing = False
        for w0 in crossing_set:
            processed_set.add(w0)
            for p in w0.way:
                ways = way_db.gs.find_all_connecting_ways(p)
                for w1 in ways:
                    if w1 not in crossing_set and "highway" in w1.tags:
                        if w1.tags["highway"] not in GCM:
                            crossings.append(p)
                            break
                        has_cw_crossing = True

        for w0 in crossing_set:
            w0.tags.pop(way.tags["highway"], None)
            w0.tags.pop("crossing", None)

        if len(crossings) == 0:
            if not has_cw_crossing:
                _log.warning(f"RLID {way.rlid} is marked as crossing without crossing roads or cycleways/footways/paths")
            no_crossing_count += 1
            continue

        for p in crossings:
            has_crossing = False
            crossing_tags["RLID"] = way.rlid
            if p in way_db.point_db:
                existing_nodes = way_db.point_db[p]
                for node in existing_nodes:
                    crossing_tags["RLID"] = node.rlid
                    if node.tags.get("highway", None) == "crossing":
                        has_crossing = True
                        break
            if has_crossing:
                skipped_count += 1
                continue
            crossing_tags["geometry"] = p
            way_db.insert_rlid_node(NvdbSegment(crossing_tags), "resolved")
            count += 1

    _log.info(f"done (converted {count} crossings, skipped {skipped_count} as node crossings already existed, {no_crossing_count} had no crossing roads)")

# bridge_footway_and_cycleway_separations()
#
# separation:left/right=* often have gaps over crossings which splits
# the cycleway/footway in many segments. This function assumes that
# leaving a gap over crossings is overkill and simplifies the tagging
# by keeping the separation tag over crossings.
#
def bridge_footway_and_cycleway_separations(way_db):

    def has_same_tags(ways, exclude_tags):
        ref_tags = []
        w = ways[0]
        for k, v in list(w.tags.items()):
            if k not in exclude_tags:
                kv = f"{k} {v}"
                ref_tags.append(kv)
        for w in ways[1:]:
            match_count = 0
            for k, v in list(w.tags.items()):
                if k not in exclude_tags:
                    kv = f"{k} {v}"
                    if kv not in ref_tags:
                        return False
                    match_count += 1
            if match_count < len(ref_tags):
                return False
        return True

    _log.info("Bridge cycleway/footway separations...")
    GCM = ["cycleway", "footway", "path" ]
    MAX_GAP_LENGTH = 13
    SEPARATIONS_TO_BRIDGE = [ "separation_kerb", "solid_line" ]
    KEYL = "separation:left"
    KEYR = "separation:right"
    count = 0
    exclude_tags = set([KEYL, KEYR])
    exclude_tags.update(NVDB_GEOMETRY_TAGS)
    exclude_tags.update(NVDB_USED_KEYS)
    for way in way_db:
        if way.tags.get("highway", None) not in GCM or KEYL in way.tags or KEYR in way.tags:
            continue
        dist, _ = calc_way_length(way.way)
        if dist > MAX_GAP_LENGTH:
            continue
        candidates1 = []
        candidates2 = []
        for w in way_db.gs.find_all_connecting_ways(way.way[0]):
            if (w.tags.get(KEYL, None) in SEPARATIONS_TO_BRIDGE or w.tags.get(KEYR, None) in SEPARATIONS_TO_BRIDGE) and has_same_tags([w, way], exclude_tags):
                candidates1.append(w)
        for w in way_db.gs.find_all_connecting_ways(way.way[-1]):
            if (w.tags.get(KEYL, None) in SEPARATIONS_TO_BRIDGE or w.tags.get(KEYR, None) in SEPARATIONS_TO_BRIDGE) and has_same_tags([w, way], exclude_tags):
                candidates2.append(w)
        if len(candidates1) == 0 or len(candidates2) == 0:
            continue
        separation = None
        for c1 in candidates1:
            for c2 in candidates2:
                for tag in [KEYL, KEYR]:
                    same_direction = (c1.way[-1] == way.way[0] and c2.way[0] == way.way[-1]) or (c1.way[0] == way.way[-1] and c2.way[-1] == way.way[0])
                    if same_direction and tag in c1.tags and tag in c2.tags and c1.tags[tag] == c2.tags[tag]:
                        separation = (tag, c1.tags[tag])
                        break
                if separation is not None:
                    break
            if separation is not None:
                break
        if separation is not None:
            way.tags[separation[0]] = separation[1]
            count += 1
    _log.info(f"done (filled in {count} separation gaps)")


# remove_redundant_cycleway_names()
#
# Remove names of cycleways that are named the same as neighboring street
#
def remove_redundant_cycleway_names(way_db):
    _log.info("Removing redundant cycleway names...")
    remove_count = 0
    name2road = {}
    candidates = []
    for way in way_db:
        if "highway" in way.tags and "name" in way.tags:
            hw = way.tags["highway"]
            if (hw in MAJOR_HIGHWAYS or hw in MINOR_HIGHWAYS):
                name = way.tags["name"]
                if name in name2road:
                    name2road[name].append(way)
                else:
                    name2road[name] = [ way ]
            elif hw in ["cycleway", "footway", "path", "steps", "elevator" ]:
                candidates.append(way)

    candidates2 = []
    max_distance = 100
    gs = GeometrySearch(max_distance)
    for way in candidates:
        if way.tags["name"] in name2road:
            gs.insert(way)
            candidates2.append(way)

    for way in candidates2:
        name = way.tags["name"]
        for w1 in name2road[name]:
            for p in w1.way:
                if way in gs.find_all_nearby_ways(p):
                    del way.tags["name"]
                    _log.debug(f"removed name {name} from {way.tags['highway']} {way.rlid}")
                    break
            if "name" not in way.tags:
                remove_count += 1
                break
    _log.info(f"done (removed {remove_count} redundant names)")

def way_is_small_road_gatutyp(way):
    return way.tags.get("NVDB_gatutyp", "Småväg") in ("Småväg enkel standard", "Småväg")

# remove_redundant_speed_limits()
#
# Sweden have default maxspeed as 70 when there is no road signs, or 50 in residential areas
# NVDB sets maxspeed on all roads, however OSM tradition is to exclude unnecessary tags.
#
# Maxspeed 70 on short driveways looks a bit strange too.
#
# A quirk has been observed in NVDB data: sometimes short segments of forestry roads far from residential
# areas have maxspeed 50 instead of 70. This is assumed to be some sort of bug and not actual speed limit,
# which should be the default 70.
#
def remove_redundant_speed_limits(way_db):
    _log.info("Removing redundant speed limits...")
    total_count = 0
    remove_count = 0
    for way in way_db:
        if "maxspeed" not in way.tags:
            continue
        total_count += 1
        if "maxspeed:forward" in way.tags or "maxspeed:backward" in way.tags:
            # unidirectional speed limits, assume these are signed, keep
            continue
        maxspeed = int(way.tags["maxspeed"])
        if maxspeed not in (50, 70):
            # not any of the default speeds, keep
            continue
        if not way_is_small_road_gatutyp(way):
            # not a basic road outside residential areas, keep speed limits
            continue
        klass = int(way.tags.get("NVDB_funk_klass", "9"))
        if klass >= 7 and way.tags.get("highway", None) in ["service", "unclassified", "track"]:
            way.tags.pop("maxspeed", None)
            remove_count += 1
    _log.info(f"done (removed {remove_count} of {total_count} speed limits)")

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

# cleanup_highway_widths
#
# Remove way widths with are deemed not reliable / valuable
#
# Width on forestry roads seems to be reported only on newly made roads and includes
# basically the ditches too. As forestry roads are not maintained as much and width
# is spotty we just remove it. This removal will also include some private roads, but
# the width standard is not entirely clear there either.
#
# Then there's a second pass which removes all width except for the larger roads,
# this was added after discussion with users which don't think width is valuable
# enough to cause more road segments and harder to manually maintain.
#
def cleanup_highway_widths(way_db):
    _log.info("Cleanup highway widths...")
    remove_count = 0
    total_count = 0
    apply_second_pass = True
    for way in way_db:
        if "width" not in way.tags:
            continue
        total_count += 1
        if "highway" not in way.tags:
            continue
        highway = way.tags["highway"]
        if (highway == "unclassified" and way_is_small_road_gatutyp(way)) or highway == "track":
            # According to tests, not reliable data, so we remove it
            way.tags.pop("width", None)
            remove_count += 1
            continue

        if apply_second_pass:
            # This is good data, but to some not deemed important enough to keep
            klass = int(way.tags.get("NVDB_funk_klass", "9"))
            if klass >= 7 or highway == "residential":
                way.tags.pop("width", None)
                remove_count += 1
                continue

        # NVDB data has shown to sometimes have width values like 4.099999999999999
        width = way.tags["width"]
        new_width = round(width, 1)
        if new_width != width:
            _log.debug(f'rounding width {width} to {new_width}')
            way.tags["width"] = new_width

    _log.info(f"done (removed {remove_count} of {total_count} highway widths)")

# round_highway_widths
#
# Sometimes varying road widths lead to lots of short segments, with
# overkill precision on width. This function rounds and averages road
# widths to reduce the number of segments in the final output.
#
def round_highway_widths(way_db):
    _log.info("Rounding/averaging highway widths...")

    processed = set()

    def criteria_fun(way):
        return way not in processed and \
            way.tags.get("width", 0) >= 2 and \
            "highway" in way.tags and \
            "bridge" not in way.tags and \
            "tunnel" not in way.tags

    def get_connecting_way(selfw, wset):
        # may be more than one, but we just pick the first one matching our criteria,
        # any other will be processed later and put to a different road list
        for w in wset:
            if w != selfw and \
               criteria_fun(w) and \
               w.tags["highway"] == selfw.tags["highway"] and \
               w.tags.get("lanes", None) == selfw.tags.get("lanes", None) and \
               w.tags.get("maxspeed", None) == selfw.tags.get("maxspeed", None) and \
               (w.way[-1] == selfw.way[0] or w.way[-1] == selfw.way[-1] or w.way[0] == selfw.way[0] or w.way[0] == selfw.way[-1]):
                return w
        return None

    roads = []
    for way in way_db:
        if not criteria_fun(way):
            continue
        road = [ way ]
        while True:
            cw = get_connecting_way(road[0], way_db.gs.find_all_connecting_ways(road[0].way[0]))
            if cw is not None:
                road.insert(0, cw)
                processed.add(cw)
            else:
                cw = get_connecting_way(road[-1], way_db.gs.find_all_connecting_ways(road[-1].way[-1]))
                if cw is not None:
                    road.append(cw)
                    processed.add(cw)
                else:
                    break
        if len(road) > 1:
            roads.append(road)

    _log.info(f"Found {len(roads)} connected roads to consider for width averaging and rounding")

    def round_roads(roads):
        large_span_roads = []
        for road in roads:
            max_width = min_width = road[0].tags["width"]
            for way in road:
                width = way.tags["width"]
                max_width = max(width, max_width)
                min_width = min(width, min_width)
            if max_width == min_width:
                continue
            avg = round((max_width + min_width) / 2, 1)
            if avg / min_width > 1.15 or avg - min_width > 1.5:
                #_log.info(f"Road: {len(road)} elements, width range {min_width} to {max_width} spanning {max_width - min_width}")
                large_span_roads.append(road)
                continue
            # use whole meters if we can still keep within 15%
            if round(avg, 0) / min_width <= 1.15 and max_width / round(avg, 0) <= 1.15:
                avg = int(round(avg, 0))
            for way in road:
                way.tags["width"] = avg
            _log.info(f"Road: {len(road)} segments, width range {min_width} to {max_width} changed to width {avg} for all segments")
        return large_span_roads

    large_span_roads = round_roads(roads)
    for road in large_span_roads:
        start = 0
        while len(road) - start > 1:
            for i in range(len(road)-start):
                test_road = road[start:len(road)-i]
                if len(test_road) < 2:
                    start += 1
                    break
                lsr = round_roads([ test_road ])
                if len(lsr) == 0:
                    start = len(road)-i
                    break


# merge_nearby_same_nodes()
#
# Some nodes are multiplied in the source data in slightly different positions
# These are merged to one here
#
def merge_nearby_same_nodes(way_db, point_db):

    def find_all_connecting_ways(point):
        # geometry search is setup before point layers are merged, can't search for connected ways directly
        node_ways = []
        nearby_node_ways = way_db.gs.find_all_nearby_ways(point)
        for way in nearby_node_ways:
            for p in way.way:
                if p == point:
                    node_ways.append(way)
                    break
        return node_ways

    _log.info("Merge nearby nodes that are actually the same...")

    # setup 2D search for all nodes
    node_search = TwoDimSearch()
    for node_list in point_db.values():
        for node in node_list:
            node_search.insert(node.way, node)

    remove_set = set()
    for node_list in point_db.values():
        for node in node_list:
            # only consider node types that we know is problematic in source data
            if node.tags.get("highway", None) not in ["stop", "give_way"] or node in remove_set:
                continue
            # get all nearby nodes and filter out those that are connected to the same way and have matching tags
            nearby_list = node_search.find_all_within_list(node.way, 8)
            if len(nearby_list) <= 1:
                continue
            node_ways = find_all_connecting_ways(node.way)
            if len(node_ways) == 0:
                continue
            filtered_list = []
            for (_, node_set) in nearby_list:
                for n in node_set:
                    if n.tags.get("highway", None) != node.tags["highway"] or \
                       n.tags.get("direction", None) != node.tags.get("direction", None) or \
                       n in remove_set:
                        continue
                    n_ways = find_all_connecting_ways(n.way)
                    found = False
                    for way in n_ways:
                        if way in node_ways:
                            found = True
                            break
                    if found:
                        filtered_list.append(n)
            # remove all duplicates
            for n in filtered_list:
                if n != node:
                    remove_set.add(n)
    for node in remove_set:
        del point_db[node.way]
    _log.info(f"done ({len(remove_set)} nodes were removed)")


# simplify_oneway()
#
# Turn around oneways=-1 and remove redundant backward/forward prefixes
#
def simplify_oneway(way_db, point_db):
    _log.info("Simplify tags for oneway roads...")
    directional_nodes = get_directional_nodes(point_db)
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
            reverse_way(way, directional_nodes)
            oneway = "yes"

        if oneway != "yes":
            continue

        for k, v in list(way.tags.items()):
            #  Removing direction if it's the same as oneway, except for lanes (need for lane resolving later)
            if ":forward" in k and not "lanes:" in k:
                del way.tags[k]
                k = k.replace(":forward", "")
                way.tags[k] = v

            # Remove redundant backward vehicle restriction
            k_split = k.split(":backward")
            if len(k_split) > 1 and k_split[0] in ALL_VEHICLES and v == "no":
                del way.tags[k]
    _log.info("done")


# resolve_lanes()
#
def resolve_lanes(way_db):

    _log.info("Resolving lanes tags...")
    for way in way_db:
        spec_lane_count = 0
        for k, v in list(way.tags.items()):

            # count how many lanes that are specified (bus and or direction etc)
            if "lanes:" in k:
                if isinstance(v, int):
                    spec_lane_count += v
                else:
                    spec_lane_count += int(v.split()[0]) # if conditional, eg "1 @ ...."

        if not "lanes" in way.tags and "NVDB_guess_lanes" in way.tags:
            way.tags["lanes"] = way.tags["NVDB_guess_lanes"]

        is_oneway = way.tags.get("oneway", None) in ("yes", "-1", -1)
        if spec_lane_count > 0:
            total_count = way.tags.get("lanes", -1)
            if total_count == -1:
                append_fixme_value(way.tags, "total lane count (lanes=x) not specified")
            elif spec_lane_count > total_count:
                append_fixme_value(way.tags, "too many lanes specified")
            elif spec_lane_count < total_count:
                if not "lanes:forward" in way.tags and not "lanes:backward" in way.tags:
                    if is_oneway:
                        # oneway does not need all lanes specified, all unspecified lanes are assumed to be lanes:oneway-direction
                        pass
                    elif total_count - spec_lane_count == 2:
                        # assume one lane in each direction
                        way.tags["lanes:forward"] = 1
                        way.tags["lanes:backward"] = 1
                    else:
                        append_fixme_value(way.tags, "could not derive forward/backward lanes")
                else:
                    append_fixme_value(way.tags, "too few lanes specified")

        # remove redundant lanes direction
        if is_oneway and spec_lane_count > 0:
            if way.tags["oneway"] in (-1, "-1"):
                dirstr = ":backward"
                opposite_dirstr = ":forward"
            else:
                dirstr = ":forward"
                opposite_dirstr = ":backward"
            remove_oneway = False
            for k in way.tags.keys():
                if "lanes:" in k and opposite_dirstr in k:
                    remove_oneway = True
                    break
            if remove_oneway:
                way.tags.pop("oneway", None)
                total_count = way.tags.get("lanes", None)
                if total_count is not None and total_count > spec_lane_count:
                    way.tags["lanes" + dirstr] = total_count - spec_lane_count
            else:
                for k, v in list(way.tags.items()):
                    if "lanes:" in k and dirstr in k:
                        del way.tags[k]
                        k = k.replace(dirstr, "")
                        way.tags[k] = v

        # if all lanes are bus lanes, set access restrictions
        if way.tags.get("lanes", -1) == (way.tags.get("lanes:bus", 0) + way.tags.get("lanes:bus:forward", 0) + way.tags.get("lanes:bus:backward", 0)):
            way.tags["vehicle"] = way.tags.get("vehicle", "no")
            way.tags["bus"] = way.tags.get("bus", "yes")
            _log.debug(f"Added access restrictions to {way.rlid} due to all being bus lanes")

        # 2021-11-21: we choose to keep "redundant lanes", see https://github.com/atorger/nvdb2osm/issues/28
        # remove redundant lanes=1 or lanes=2
        #if "lanes" in way.tags:
        #    lanes = way.tags["lanes"]
        #    if (is_oneway and lanes == 1) or (not is_oneway and lanes == 2):
        #        way.tags.pop("lanes", None)

    _log.info("done")


# postprocess_miscellaneous_tags()
#
# postprocess tags that aren't dealt with in any other more specialized function
#
def postprocess_miscellaneous_tags(tags):

    # remove maxspeed for footways etc (seen in Stockholm data for example)
    if tags.get("highway", None) in [ "steps", "footway" ]:
        tags.pop("maxspeed", None)

    # remove the generic maxweight from smaller roads
    if "maxweight" in tags and not "maxweight:conditional" in tags and "highway" in tags and tags["highway"] not in MAJOR_HIGHWAYS:
        tags.pop("maxweight", None)

    # remove the generic hazmat=no from smaller roads
    if tags.get("hazmat", None) == 'no' and not "hazmat:conditional" in tags and "highway" in tags and tags["highway"] not in MAJOR_HIGHWAYS:
        tags.pop("hazmat", None)

    # add bicycle=yes to pedestrian street, unless there already is a bicycle- or vehicle-related key
    if tags.get("highway", None) == "pedestrian":
        has_bicycle = False
        for k in tags.keys():
            if "bicycle" in k or k == "vehicle":
                has_bicycle = True
                break
        if not has_bicycle:
            tags["bicycle"] = "yes"


    # oneway tag is redundant for roundabouts
    if tags.get("junction", None) == "roundabout":
        tags.pop("oneway", None)

    # building passage is a good guess 90% of the time, but if it's a bridge, it's not a tunnel...
    if tags.get("tunnel", None) == "building_passage" and "bridge" in tags:
        tags.pop("tunnel", None)
        tags["covered"] = "yes"

    # fix rounding errors in source data floating point values
    for k, v in tags.items():
        if not isinstance(v, float):
            try:
                v = float(v)
            except (ValueError, TypeError):
                continue
        if k in ["SLUTAVST", "STARTAVST", "SHAPE_LEN", "AVST"]:
            continue
        new_v = round(v, 1)
        if new_v != v:
            _log.info(f'rounding {k}={v} to {new_v}')
            tags[k] = new_v

# final_pass_postprocess_miscellaneous_tags()
#
# Lastly, make a pass over all tags to fixup stuff that isn't dealt with in more specialized functions
#
def final_pass_postprocess_miscellaneous_tags(way_db):
    for way in way_db:
        postprocess_miscellaneous_tags(way.tags)
    for p in way_db.point_db:
        nodes = way_db.point_db[p]
        for node in nodes:
            postprocess_miscellaneous_tags(node.tags)

# cleanup_used_nvdb_tags()
#
# Remove all tags that have been used when resolving various things
#
def cleanup_used_nvdb_tags(way_db_ways, in_use):
    for ways in way_db_ways.values():
        for way in ways:
            for key in NVDB_USED_KEYS:
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
        if any(char.isupper() for char in k) and k != "NVDB:RLID" and k != "NVDB_extra_nodes":
            _log.warning(f"key {k} was not parsed")
