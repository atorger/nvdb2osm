
# AGGREGATLevkval_DoU_2017       o not relevant (leveranskvalitetsklass)
# AGGREGATVagkategori            o redundant (aggregate road types, government roads only)
# ATKATK_Matplats                o not relevant (measurement place, not food place)
# BATMAN_*                       o redundant (bridges and tunnels, doesn't add relevat info over NVDB-Bro_och_tunnel)
# Miljö_Landskap*                o not relevant
# Net                            o redundant
# TFR-Tjalrestriktion            o not relevant (temporary information of road damage)
# TRAFIK-Trafik                  o not relevant (traffic statistics)
# EVB-Driftbidrag_statligt       - for resolving highway (figuring out difference between track/unclassified on small roads)
# VIS-Brunn___Slamsugning        o not translated
# VIS-Bullerskydd_vag            o not translated (noise barrier, but incomplete and geometry on road rather than wall)
# VIS-Driftomrade                o not relevant
# VIS-Driftvandplats             o not relevant (operating turning point can be routed in road network)
# VIS-FPV_*                      o not relevant (prioritized roads for certain uses)
# VIS-Funktionellt_priovagnat    - for resolving highway (a less detailed NVDB-FunkVagklass)
# VIS-Hallplatslage              o not translated (suitably used separately when mapping bus lines)
# VIS-Hallplats                  o not translated (suitably used separately when mapping bus lines)
# VIS-Jarnvagskorsning           - railway crossings (poorly aligned, railways loaded to snap alignment)
# VIS-Kalibreringsstracka        o not relevant (measurement reference)
# VIS-Kantstolpe                 o not translated (rare, and mainly for winter maintenance)
# VIS-Katastrofoverfart          o not translated (not existing OSM tags, not important for normal users)
# VIS-Mittremsa                  o not relevant (lane separation in meters)
# VIS-Omkorningsforbud           - overtaking=no
# VIS-Overledningsplats          o not translated (similar to VIS-Katastrofoverfart)
# VIS-Pendlings__och_servicevg   o not relevant
# VIS-P_ficka                    - parking=layby
# VIS-Raffla                     o not translated (rare, no existing OSM tag, not important)
# VIS-Rastplats                  - amenity=parking etc, requires manual splitting to multiple nodes/areas (fixme tag added)
# VIS-Sidoanlaggningsvag         o redundant
# VIS-Slitlager                  - detailed road surface for government managed roads (complements NVDB_Slitlager)
# VIS-Stamvag                    o redundant
# VIS-Stigningsfalt              o not translated (rare, generally covered by increase of lanes)
# VIS-Storstadsvag               o redundant
# VIS-Strateg_VN_tyngretranspo   o not relevant
# VIS-TEN_T_Vagnat               o redundant
# VIS-Vagnybyggnad_2009          o not relevant
# VIS-Vagtyp                     o redundant (government roads only)
# VIS-Viltpassage_i_plan         o not translated
# VIS-Viltstangsel               o not translated (wildlife fence, but not mapped at fence but rather on road)
# VIS-Viltuthopp                 o not translated
# VIS-Vinter2003                 o not translated (winter_service=yes, but only covering the large roads,
#                                                          ie not all roads that actually have winter service)
# VIS-VVIS                       o not relevant (weather stations)

#
# At the time of writing these are all NVDB files, and how they are used in the translation:
#
# NVDB-Antal_korfalt2            - lanes=x
# NVDB-Barighet                  - maxweight=x
# NVDB-BegrAxelBoggiTryck        - maxaxleload=x, maxbogieweight=x, maxaxleload:conditional=x
# NVDB-BegrBruttovikt            - maxweightrating=x
# NVDB-BegrFordBredd             - maxwidth=x
# NVDB-BegrFordLangd             - maxlength=x
# NVDB-Bro_och_tunnel            - bridges and tunnels
# NVDB-C_Cykelled                o not translated (named cycling routes, similar to NVDB-Turismcykelled)
# NVDB-Cirkulationsplats         - junction=roundabout
# NVDB-C_Rekbilvagcykeltrafik    o not translated (recommended road for cyclists)
# NVDB-CykelVgsKat               - used to resolve highway, often redundant (subset of GCM_vagtyp), but not everywhere
# NVDB-Farjeled                  - ferry routes
# NVDB-Farthinder                - traffic_calming=x
# NVDB-ForbjudenFardriktning     - oneway
# NVDB-ForbjudenSvang            o ? empty data in Stockholm, Göteborg and other test areas
# NVDB-ForbudTrafik              - traffic restrictions, partly translated (too specific, not enough OSM tags available)
# NVDB-FramkFordonskomb          o not translated (rare tag, possibility for trucks etc to get through)
# NVDB-FunkVagklass              - used to resolve highway
# NVDB-Gagata                    - used to resolve highway
# NVDB-Gangfartsomrade           - used to resolve highway
# NVDB-Gatunamn                  - street names
# NVDB-Gatutyp                   - used to resolve highway
# NVDB-GCM_belyst                - lit=yes
# NVDB-GCM_passage               - traffic signals for footway/cycleway
# NVDB-GCM_separation            - cycleway separation
# NVDB-GCM_vagtyp                - cycleways and footways (and some more other rare types)
# NVDB-Hastighetsgrans           - maxspeed, including time limits
# NVDB-Hojdhinder45dm            - maxheight
# NVDB-Huvudled                  - priority_road=designated
# NVDB-InskrTranspFarligtGods    - hazmat=no (hazardous goods)
# NVDB-Kollektivkorfalt          - psv:lanes=* (not enough info to know placement of lanes or if bus or psv)
# NVDB-Korsning                  - highway=traffic_signals, names for roundabouts
# NVDB-Miljozon                  - Swedish environment zones, custom tag used for now
# NVDB-Motortrafikled            - used to resolve highway
# NVDB-Motorvag                  - used to resolve highway
# NVDB-Ovrigt_vagnamn            - road names
# NVDB-Reflinjetillkomst         - used as reference geometry, no tags used
# NVDB-RekomVagFarligtGods       - hazmat=designated
# NVDB-Slitlager                 - road surface paved/gravel
# NVDB-Stopplikt                 - highway=stop
# NVDB-Svangmojlighet            o not translated (rare tag, possibility for trucks to turn in tight crossings)
# NVDB-TattbebyggtOmrade         o redundant (subset of Gatutyp)
# NVDB-Tillganglighet            o redundant (similar to FunkVagKlass)
# NVDB-Turismcykelled            o not translated (named cycling routes)
# NVDB-Vagbredd                  - street width
# NVDB-Vaghallare                o not translated (road maintainer)
# NVDB-Vaghinder                 - barrier=x
# NVDB-Vagnummer                 - ref=x and used to resolve highway
# NVDB-Vagtrafiknat              o redundant
# NVDB-Vajningsplikt             - highway=give_way
# NVDB-Vandmojlighet             o was turning_circle, but is too often wrong so no longer used

import logging
import string

from nvdb_ti import parse_time_interval_tags, parse_range_date

_log = logging.getLogger("translations")


# append_fixme_value()
#
def append_fixme_value(tags, fixme_value):
    if fixme_value is None:
        return
    if tags.get("fixme", None) is None:
        tags["fixme"] = "NVDB import: " + fixme_value
    else:
        tags["fixme"] = tags["fixme"] + "; " + fixme_value


# tag_translation_expect_unset_time_intervals()
#
def tag_translation_expect_unset_time_intervals(tags):
    time_intervals = parse_time_interval_tags(tags)
    if time_intervals == -1:
        append_fixme_value(tags, "time interval parse failure")
    elif time_intervals is not None:
        # if this happens, we probably need to implement some code to handle time intervals for that given type
        _log.warning(f"unexpected time interval (not implemented) RLID {tags['RLID']}")
        append_fixme_value(tags, "Warning: time interval handling not implemented)")


# add_extra_nodes_tag()
#
# Add key/value tags to the custom NVDB_extra_nodes tag, the purpose being to
# store tags that cannot be mapped to the single node due to conflicts.
#
def add_extra_nodes_tag(tags, extra_nodes):
    if len(extra_nodes) == 0:
        return
    kvset = set()
    for kv in extra_nodes:
        node_str = "["
        for k, v in kv.items():
            node_str += "%s=%s, " % (k, v)
        node_str = node_str[:-2] + "], "
        kvset.add(node_str)
    en_str = "".join(kvset)
    en_str = en_str[:-2]
    tags["NVDB_extra_nodes"] = en_str
    append_fixme_value(tags, "NVDB_extra_nodes need to be mapped manually")

# parse_speed_limit()
#
# Parse NVDB speed limit, taking certain NVDB peculiarities into account.
#
def parse_speed_limit(tags, key):
    speed = tags[key]
    # text "gångfart" is very rare (forgot which dataset it was seen in)
    # we use Gangfartsomrade rather than this to resolve living_street
    # This could probably be used also on pedestrian streets (gågata) which
    # is not the same as living street.
    if speed == "gångfart":
        speed = 5
    elif not isinstance(speed, int):
        _log.warning(f"unexpected speed value {key} {speed} (RLID {tags['RLID']})")
        append_fixme_value(tags, "Bad %s speed value" % key)
        speed = 5
    elif speed >= 1000: # observed to be used as undefined value in some cases
        speed = -1
    del tags[key]
    return speed

# parse_direction()
#
# Parse NVDB direction and convert to OSM :forward/:backward or nothing.
#
def parse_direction(tags):
    if not "RIKTNING" in tags or tags["RIKTNING"] == "Med och mot" or tags["RIKTNING"] is None:
        dir_str = ""
    elif tags["RIKTNING"] == "Med":
        dir_str = ":forward"
    elif tags["RIKTNING"] == "Mot":
        dir_str = ":backward"
    else:
        dir_str = ""
        _log.warning(f"invalid value of RIKTNING {tags['RIKTNING']} (RLID {tags['RLID']})")
        append_fixme_value(tags, "Bad RIKTNING value")
    tags.pop("RIKTNING", None)
    return dir_str

# parse_vehicle_types()
#
# Parse NVDB vehicle types ("fordonstyp"), and alternatively if purpose/user lists are provided
# also road users ("trafikant"
#
def parse_vehicle_types(tags, key_base, purpose_list=None, user_list=None):
    del_tags = []
    vtypes = []
    fixme_tags = { "fixme": tags.get("fixme", None) }
    for key in tags:
        if key.startswith(key_base) and tags[key] != -1:
            v = tag_translation_fordon_trafikant(tags[key], tags["RLID"])
            if v == "FIXME":
                append_fixme_value(fixme_tags, f"Unknown tag {tags[key]}")
            elif v == "IGNORE":
                pass
            elif v.startswith("PURPOSE"):
                if purpose_list is not None:
                    purpose_list.append(v.split()[1])
                else:
                    _log.warning(f"{key_base} contains conditional element (RLID {tags['RLID']})")
                    append_fixme_value(fixme_tags, f"{key_base} contains conditional element")
            elif v.startswith("USER"):
                if user_list is not None:
                    user_list.append(v.split()[1])
                else:
                    _log.warning(f"{key_base} contains conditional element (RLID {tags['RLID']})")
                    append_fixme_value(fixme_tags, f"{key_base} contains conditional element")
            else:
                vtypes.append(v)
        if key.startswith(key_base):
            del_tags.append(key)
    for k in del_tags:
        del tags[k]
    if fixme_tags.get("fixme", None) is not None:
        tags["fixme"] = fixme_tags["fixme"]
    return vtypes

# Translation table used by the tag_translation_fordon_trafikant() function
VEHICLES_AND_ROAD_USERS_TRANSLATIONS = {
    "ambulans":              "emergency",
    "anläggningens fordon":  "IGNORE",
    "arbetsfordon":          "IGNORE",
    "beskickningsfordon":    "USER diplomatic", # custom tag
    "beställd taxi":         "taxi",
    "besökare":              "PURPOSE destination",
    "bil":                   "motorcar",
    "bilägare med arrendekontrakt": "USER permit_holder",
    "bokbuss":               "bus",
    "buss":                  "bus",
    "cykel":                 "bicycle",
    "efterfordon":           "trailer",
    "fordon":                "vehicle",

    # the actual vehicle is described in an extra free-text tag as it's free text it's not
    # reasonable to make a translation tabel for it
    "fordon enligt beskrivning": "IGNORE",

    "fordon i linjetrafik":  "bus",
    "fordon i linjetrafik vid på- och avstigning":        "bus",
    "fordon med särskilt tillstånd":                      "USER permit_holder",
    "fordon eller fordonståg vars längd, lasten inräknad, överstiger 10 meter": "lhv",
    "fordon som används av rörelsehindrade med särskilt tillstånd": "USER disabled",
    "fordon som används för distribution av post":        "IGNORE",
    "fyrhjulig moped":       "atv",
    "färdtjänstfordon":      "psv",
    "godstransporter":       "hgv",
    "hästfordon":            "carriage",
    "kommunens servicefordon": "IGNORE",
    "lastbil":               "hgv",
    "lastbil vid på- och avlastning": "PURPOSE delivery",
    "2-axlig lastbil":       "hgv",
    "lätt lastbil":          "goods",
    "lätt motorcykel":       "motorcycle",
    "lätt terrängvagn":      "atv",
    "moped":                 "moped",
    "moped klass I":         "moped",
    "moped klass II":        "mofa",
    "motorcykel":            "motorcycle",
    "motordrivet fordon med tillkopplad släpvagn annat än påhängsvagn eller enaxlig släpvagn": "hgv",
    "motordrivna fordon":    "motor_vehicle",
    "motorfordon":           "motor_vehicle",
    "motorredskap":          "IGNORE",
    "motorredskap klass I":  "IGNORE",
    "motorredskap klass II": "IGNORE",
    "okänt":                 "IGNORE",
    "personbil":             "motorcar",
    "renhållningsbil":       "IGNORE",
    "taxi":                  "taxi",
    "terrängmotorfordon":    "atv",
    "terrängmotorfordon och terrängsläp": "atv",
    "terrängskoter":         "snowmobile",
    "terrängsläp":           "trailer",
    "terrängvagn":           "atv",
    "trafik":                "vehicle",
    "traktor":               "agricultural",
    "transporter":           "PURPOSE delivery",
    "trehjulig moped":       "moped",
    "truck":                 "IGNORE",
    "tung lastbil":          "hgv",
    "tung motorcykel":       "motorcycle",
    "tung terrängvagn":      "atv",
    "utryckningsfordon":     "emergency",
    "på- eller avlastning av gods": "PURPOSE delivery",
    "på- eller avstigning":  "PURPOSE embark_disembark", # custom conditional
    "påhängsvagn":           "trailer",
    "skolskjuts":            "psv",
    "släpkärra":             "trailer",
    "släpvagn":              "trailer"
}


# tag_translation_fordon_trafikant()
#
# Translate NVDB vehicles and road users into OSM tags. Note that in this case OSM tags are
# not as detailed as NVDB tags, so translation is not 100% correct. Most of those marked as
# "IGNORE" are used for exemptions, and we don't consider those as important to document.
#
def tag_translation_fordon_trafikant(tag, rlid):

    if isinstance(tag, int):
        # in some cases the tag is provided as an int instead of text
        trans_number = {
            10: "bil",
            20: "buss",
            30: "cykel",
            40: "fordon",
            50: "fordon i linjetrafik",
            70: "fordon som används av rörelsehindrade med särskilt",
            80: "hästfordon",
            90: "lastbil",
            100: "lätt lastbil",
            110: "lätt terrängvagn",
            120: "moped",
            130: "moped klass I",
            140: "moped klass II",
            150: "motorcykel",
            160: "motordrivet fordon med tillkopplad släpvagn annat",
            170: "motordrivna fordon",
            180: "motorredskap",
            190: "motorredskap klass I",
            200: "motorredskap klass II",
            210: "personbil",
            230: "terrängmotorfordon",
            240: "terrängmotorfordon och terrängsläp",
            250: "terrängskoter",
            260: "terrängvagn",
            270: "traktor",
            280: "tung lastbil",
            290: "tung terrängvagn",
            300: "utryckningsfordon",
            9999: "okänt"
        }
        tag = trans_number.get(tag, "okänt")

    if not tag in VEHICLES_AND_ROAD_USERS_TRANSLATIONS:
        _log.warning(f"unexpected NVDB fordon-trafikant tag '{tag}' (RLID {rlid})")
        return "FIXME"
    return VEHICLES_AND_ROAD_USERS_TRANSLATIONS[tag]


# tag_translation_single_value_with_time_interval()
#
# Generic function for translating NVDB tags that are a single value combined with a
# time interval
#
def tag_translation_single_value_with_time_interval(tags, key, value):
    time_intervals = parse_time_interval_tags(tags)
    if time_intervals == -1:
        append_fixme_value(tags, "time interval parse failure")
    elif time_intervals is not None:
        tags[key + ":conditional"] = "%s @ (%s)" % (value, time_intervals)
    else:
        tags[key] = value

# tag_translation_Barighet()
#
# Maxweight
#  - "Särskilda villkor" (specific conditions) not documented in NVDB so cannot be translated
#
def tag_translation_Barighet(tags):
    winter_bk = tags["BAEIGHTSOD"] is not None and tags["BAEIGHTSOD"] != tags["BAEIGHTSSS"]
    tag_translations = {
        "BAEIGHTSSS=BK 1": "maxweight=64",
        "BAEIGHTSSS=BK 2": "maxweight=51.4",
        "BAEIGHTSSS=BK 3": "maxweight=37.5",
        "BAEIGHTSSS=BK 4": "maxweight=74",
        "BAEIGHTSSS=BK 4 - Särskilda villkor": "maxweight=74",
        "BAEIGHTSOD=BK 1": "wc=64",
        "BAEIGHTSOD=BK 2": "wc=51.4",
        "BAEIGHTSOD=BK 3": "wc=37.5",
        "BAEIGHTSOD=BK 4": "wc=74",
        "BAEIGHTSOD=BK 4 - Särskilda villkor": "wc=74",
        "STATDAUMOD": None,
        "SLUDATMSOD": None,
    }
    process_tag_translations(tags, tag_translations)
    if winter_bk:
        if tags.get("STATDAUMO3", None) is None or tags.get("SLUDATMVOD", None) is None:
            _log.warning(f"Winter-specific maxweight without date range for RLID {tags['RLID']}")
        else:
            start_winter = parse_range_date(tags["STATDAUMO3"])
            stop_winter = parse_range_date(tags["SLUDATMVOD"])
            tags["maxweight:conditional"] = str(tags["wc"]) + " @ (" + start_winter + "-" + stop_winter + ")"
    _ = [tags.pop(key, None) for key in ["wc", "BAEIGHTSOD", "SLUDATMVOD", "STATDAUMO3", "BETECKNING"]]

# tag_translation_BegrAxelBoggiTryck()
#
# Maxaxleload/maxbogieweight/triple axle
#  - we skip information about organisation (Länsstyrelse) etc, and just keep the weight information
#
def tag_translation_BegrAxelBoggiTryck(tags):
    time_interval = parse_time_interval_tags(tags)
    if time_interval == -1:
        append_fixme_value(tags, "time interval parse failure")
        time_interval = None

    for i in range(1, 4): # i = 1..3
        weight = tags.get("TRYCK" + str(i), -1)
        if weight > 0 and "TYPTRYCK" + str(i) in tags:
            typ = tags["TYPTRYCK" + str(i)]
            if time_interval is None:
                if typ == "axeltryck":
                    tags["maxaxleload"] = weight
                elif typ == "boggitryck":
                    tags["maxbogieweight"] = weight
                elif typ == "trippelaxeltryck":
                    tags["maxaxleload:conditional"] = '%s @ "triple axle"' % weight
            else:
                if typ == "axeltryck":
                    tags["maxaxleload:conditional"] = "%s @ (%s)" % (weight, time_interval)
                elif typ == "boggitryck":
                    tags["maxbogieweight:conditional"] = "%s @ (%s)" % (weight, time_interval)
                elif typ == "trippelaxeltryck":
                    tags["maxaxleload:conditional"] = '%s @ (%s AND "triple axle")' % (weight, time_interval)

        tags.pop("TRYCK" + str(i), None)
        tags.pop("TYPTRYCK" + str(i), None)
    # FIXME: we should probably not ignore the new field FORDTRAF (restriction does not apply to vehicle type XYZ)
    _ = [tags.pop(key, None) for key in [ "AARTAL1", "AARTAL2", "LOEPNUMME1", "LOEPNUMME2", "MEDELADEON", "ORGNISTI1", "ORGNISTI2", "BETECKNING", "FORDTRAF" ]]

# tag_translation_BegrBruttovikt()
#
# Maxweightrating
#  - FORD_TAG=ja means "also applies to vehicle trains". OSM doesn't do that distinction, so we ignore it
#
def tag_translation_BegrBruttovikt(tags):
    key = "maxweightrating"
    value = tags["BRUTTOVIKT"]
    tags.pop("RIKTNING", None) # ignored
    tags.pop("FORD_TAG", None) # ignored
    tags.pop("BETECKNING", None) # ignored
    tags.pop("FORDTRAF", None) # ignored, FIXME probably should not be ignored
    tags.pop("BRUTTOVIKT", None)
    tag_translation_single_value_with_time_interval(tags, key, value)

# tag_translation_BegrFordBredd()
#
# Maxwidth
#
def tag_translation_BegrFordBredd(tags):
    key = "maxwidth"
    value = tags["FORD_BREDD"]
    tags.pop("FORD_BREDD", None)
    for i in range(1, 4):
        tags.pop("FORDTRAF" + str(i), None) # doesn't seem to be used
    tag_translation_single_value_with_time_interval(tags, key, value)

# tag_translation_BegrFordLangd()
#
# Maxlength
#
def tag_translation_BegrFordLangd(tags):
    key = "maxlength"
    value = tags["FORD_LGD"]
    tags.pop("FORD_LGD", None)
    for i in range(1, 4):
        tags.pop("FORDTRAF" + str(i), None) # doesn't seem to be used
    tag_translation_single_value_with_time_interval(tags, key, value)

# tag_translation_ForbudTrafik()
#
# Traffic restrictions.
#   - Quite tricky to get right.
#   - Cannot be translated 100% correct due to too few OSM tags, and some NVDB free text fields
#
def tag_translation_ForbudTrafik(tags):

    # BESKRGFART      Beskrivning (fritext, sällsynt, verkar vara samma som BSEKR_GEJ1)
    # BSEKR_GEJ1      Gäller ej.Beskrivning (fritext, exempel: "Fordon som används vid bärgningsarbete")
    # FORDTYP[1..3]   Gäller fordon
    # TOTALVIKT       Anger totalvikt på fordon över vilken förbudet gäller om det bara gäller fordon med viss totalvikt.
    # GENOMFART       Anger om trafikregeln enbart gäller genomfart eller inte (sant/falskt).
    # /               Tidsintervall
    # GE/             Gäller ej.Tidsintervall (= tidsintervall när "gäller-ej"-fordonen får köra)
    # FORDTRA1[1..10] Gäller ej.Fordon/trafikant
    # VERKSAMH1[1..7] Gäller ej.Verksamhet
    # RIKTNING        Riktning

    rlid = tags["RLID"]
    ti = parse_time_interval_tags(tags)
    if ti == -1:
        append_fixme_value(tags, "time interval parse failure")
        return

    for k, v in list(tags.items()):
        if v is None:
            del tags[k]
    _log.debug(f"ForbudTrafik input: {tags} {ti}")

    forbidden_ti = ti["/"]
    exemption_ti = ti["GE/"]

    # Seem to be a quite common error/style to specify 00:00-00:00 as in this layer (Stockholm data),
    # we assume it means 00:00-00:24 ie same as no time interval
    if forbidden_ti == "00:00-00:00":
        forbidden_ti = None
    if exemption_ti == "00:00-00:00":
        exemption_ti = None

    only_applies_to_passing_through = tags["GENOMFART"] == "sant"
    total_weight = tags["TOTALVIKT"]
    direction = parse_direction(tags)

    vtypes = parse_vehicle_types(tags, "FORDTYP")
    if len(vtypes) == 0:
        vtypes.append("vehicle")
    purpose_list = []
    user_list = []
    exemption_vtypes = parse_vehicle_types(tags, "FORDTRA1", purpose_list, user_list)

    # make sure we don't have overlap between vehicle types
    for v in vtypes:
        if v in exemption_vtypes:
            # This can happen when NVDB tag is more specific than the translated OSM tag
            # We then remove the exemption and keep the generic OSM
            _log.warning(f"vehicle overlap with exemption for restrictions ({v}) (RLID {rlid})")
            exemption_vtypes.remove(v)

    # remove duplicates
    purpose_list = list(dict.fromkeys(purpose_list))
    user_list = list(dict.fromkeys(user_list))
    if only_applies_to_passing_through and "destination" in purpose_list:
        purpose_list.remove("destination")

    if len(purpose_list) > 0 and exemption_ti is None:
        # The only valid alternative for multiple purposes seems to make multiple conditionals,
        # so we create a dummy time to be able to make conditionals
        exemption_ti = "00:00-24:00"

    base_str= ""
    cond_str = ""
    if forbidden_ti is None:
        if total_weight > 0 and only_applies_to_passing_through:
            cond_str = "destination @ (weight>%s)" % total_weight
        elif only_applies_to_passing_through:
            base_str = "destination"
        elif total_weight > 0:
            cond_str = "no @ (weight>%s)" % total_weight
        else:
            base_str = "no"
    else:
        if total_weight > 0 and only_applies_to_passing_through:
            cond_str = "no @ (weight>%s AND %s); destination @ (%s)" % (total_weight, forbidden_ti, forbidden_ti)
        elif only_applies_to_passing_through:
            base_str = "no"
            cond_str = "destination @ (%s)" % forbidden_ti
        elif total_weight > 0:
            cond_str = "no @ (weight>%s AND %s)" % (total_weight, forbidden_ti)
        else:
            cond_str = "no @ (%s)" % forbidden_ti

    for purpose in purpose_list:
        if not purpose in cond_str:
            cond_str += "; %s @ (%s)" % (purpose, exemption_ti)

    for user in user_list:
        if not user in cond_str:
            if exemption_ti is None:
                cond_str += "; yes @ (%s)" % (user)
            else:
                # mixing 'no @' and 'yes @' ond the same line  is not common, but seems to be okay with
                # the (loose) specification https://wiki.openstreetmap.org/wiki/Conditional_restrictions
                cond_str += "; yes @ (%s AND %s)" % (exemption_ti, user)
    if cond_str != "" and cond_str[0] == ';':
        cond_str = cond_str[2:]

    for v in vtypes:
        if base_str != "":
            tags[v + direction] = base_str
        if cond_str != "":
            tags[v + direction + ":conditional"] = cond_str
    for v in exemption_vtypes:
        if exemption_ti is None or exemption_ti == "00:00-24:00" or exemption_ti == forbidden_ti:
            tags[v] = "yes"
        else:
            tags[v + direction + ":conditional"] = "yes @ (%s)" % exemption_ti

    idx = 1
    while "VERKSAMH1" + str(idx) in list(tags):
        del tags["VERKSAMH1" + str(idx)]
        idx += 1
    _ = [tags.pop(key, None) for key in ["BESKRGFART", "BSEKR_GEJ1", "GENOMFART", "TOTALVIKT"]]

    _log.debug(f"ForbudTrafik output {tags}")

# tag_translation_GCM_separation()
#
# At the time of writing cycleway separation is just a proposal, but quite much use in Germany
# https://wiki.openstreetmap.org/wiki/Proposed_features/cycleway:separation
#
def tag_translation_GCM_separation(tags):
    key = None
    key2 = None
    if tags["SIDA"] == "Höger":
        key = "separation:right"
    elif tags["SIDA"] == "Vänster":
        key = "separation:left"
    elif tags["SIDA"] == "Vänster och höger": # rare, but exists
        key = "separation:left"
        key2 = "separation:right"
    elif tags["SIDA"] == "Mitt" or tags["SIDA"] is None: # rare, but exists, we ignore these
        _log.info(f"ignoring separation with SIDA {tags['SIDA']} (RLID {tags['RLID']})")
    else:
        _log.warning(f"unknown SIDA {tags['SIDA']} (RLID {tags['RLID']})")
        append_fixme_value(tags, "GCM_separation: unknown SIDA value")

    trans_separation = {
        1: "separation_kerb", # kantsten
        2: None, # skiljeremsa
        3: "railing", # räcke
        4: None, # friliggande
        5: "solid_line", # vägmarkering
        99: None, # okänt
    }
    separation = tags.pop("SEPARATION", None)
    tags.pop("SIDA", None)

    if separation not in trans_separation:
        _log.warning(f"unknown SEPARATION {separation} (RLID {tags['RLID']})")
        append_fixme_value(tags, f"GCM_separation: unknown SEPARATION value {separation}")
    elif trans_separation.get(separation, None) is not None and key is not None:
        tags[key] = trans_separation[separation]
        if key2 is not None:
            tags[key2] = trans_separation[separation]

# tag_translation_Hastighetsgrans()
#
# Maxspeed, sometimes conditional
#
def tag_translation_Hastighetsgrans(tags):
    time_interval = parse_time_interval_tags(tags)
    if time_interval == -1:
        append_fixme_value(tags, "time interval parse failure")
        return

    vtypes = parse_vehicle_types(tags, "FORDTYP1")
    direction = parse_direction(tags)
    maxspeed = parse_speed_limit(tags, "HTHAST")
    alt_maxspeed = parse_speed_limit(tags, "HAVHAST1")
    max_weight = tags.get("TOTALVIKT1", -1)

    only_applies_to_these_vehicles = tags["HAVGIE1"] == 2
    doesnt_apply_to_these_vehicles = tags["HAVGIE1"] == 1
    if len(vtypes) > 0 and tags["HAVGIE1"] == -1:
        append_fixme_value(tags, "Hastighetsgrans: got vehicles but applies-to not set")
        _log.warning(f"Hastighetsgrans: got vehicles without applies-to set RLID {tags['RLID']}")
        only_applies_to_these_vehicles = True # guess

    if (only_applies_to_these_vehicles or doesnt_apply_to_these_vehicles) and len(vtypes) == 0:
        append_fixme_value(tags, "Hastighetsgrans: got applies-to but no vehicles")
        _log.warning(f"Hastighetsgrans: got applies-to without vehicles RLID {tags['RLID']}")
        only_applies_to_these_vehicles = False
        doesnt_apply_to_these_vehicles = False

    cond_str = ""
    if time_interval:
        if max_weight > 0:
            cond_str = "(weight>%s AND %s)" % (max_weight, time_interval)
        else:
            cond_str = "(%s)" % time_interval
    else:
        if max_weight > 0:
            cond_str = "(weight>%s)" % max_weight

    if (cond_str != "" or len(vtypes) > 0) and (alt_maxspeed < 0 or alt_maxspeed == maxspeed):
        append_fixme_value(tags, "Hastighetsgrans: conditions without alternate speed")
        _log.warning(f"Hastighetsgrans: conditions without alternate speed {tags} (RLID {tags['RLID']} {vtypes} {cond_str})")
        cond_str = ""

    if only_applies_to_these_vehicles:
        tags["maxspeed" + direction] = maxspeed
        for v in vtypes:
            if cond_str != "":
                tags["maxspeed:" + v + direction + ":conditional"] = "%s @ %s" % (alt_maxspeed, cond_str)
            else:
                tags["maxspeed:" + v + direction] = alt_maxspeed
    elif doesnt_apply_to_these_vehicles:
        tags["maxspeed" + direction] = alt_maxspeed
        for v in vtypes:
            if cond_str != "":
                tags["maxspeed:" + v + direction + ":conditional"] = "%s @ %s" % (maxspeed, cond_str)
            else:
                tags["maxspeed:" + v + direction] = maxspeed
    else:
        tags["maxspeed" + direction] = maxspeed
        if cond_str != "":
            tags["maxspeed" + direction + ":conditional"] = "%s @ %s" % (alt_maxspeed, cond_str)

    tags.pop("HAVGIE1", None)
    tags.pop("TOTALVIKT1", None)

# tag_translation_InskrTranspFarligtGods()
#
# Restrictions for hazardous materials
#
def tag_translation_InskrTranspFarligtGods(tags):
    may_not = tags["FARINTE"]
    # we translate all values to hazmat=no
    if may_not not in ("föras", "stannas", "parkeras", "stannas eller parkeras"):
        _log.warning(f"unknown FARINTE value {tags} (RLID {tags['RLID']})")
        append_fixme_value(tags, "InskrTranspFarligtGods: unknown FARINTE value")

    time_intervals = parse_time_interval_tags(tags)
    if time_intervals == -1:
        append_fixme_value(tags, "time interval parse failure")
        return
    if time_intervals is None:
        tags["hazmat"] = "no"
    else:
        tags["hazmat:conditional"] = "no @ %s" % time_intervals

    del tags["FARINTE"]

    # FIXME: we don't care about these fields yet (are they ever used?)
    for i in range(1, 6):
        tags.pop("FORDTYP" + str(i), None)
    for i in range(1, 4):
        tags.pop("FORDTRAF1" + str(i), None)
    for i in range(1, 4):
        tags.pop("VERKSAMH1" + str(i), None)
    tags.pop("PLATS1", None)
    tags.pop("RIKTNING", None)

# tag_translation_Kollektivkorfalt()
#
# Bus lanes
#  - NVDB doesn't specify which lane is the bus one
#  - NVDB doesn't specify if taxi may drive there
#  - NVDB has odd way to specify time interval, sometimes only TIM12 set
#  - We do some lane tricks
#
def tag_translation_Kollektivkorfalt(tags):

    ti_tags = {
        "DAGSL1": tags.get("DAGSLAG", None),
        "STDAT1": tags.get("STARTDATUM", "1899-12-29"),
        "SLDAT1": tags.get("SLUTDATUM", "1899-12-29"),
        "STDAG1": tags.get("STARTDAG", None),
        "SLDAG1": tags.get("SLUTDAG", None),
        "STTIM11": tags.get("TIMME", -1),
        "SLTIM11": tags.get("TIM12", -1),
        "STMIN11": tags.get("MINUT", -1),
        "SLMIN11": tags.get("MIN13", -1),
        "RLID": tags["RLID"]
    }
    # case with only TIM12 set seems to be quite common, so we fix that to make a parsable time
    all_undefined = True
    for k in [ "STTIM11", "SLTIM11", "STMIN11", "SLMIN11"]:
        if ti_tags[k] != -1 and ti_tags[k] is not None:
            all_undefined = False
    if not all_undefined:
        for k in [ "STTIM11", "SLTIM11", "STMIN11", "SLMIN11"]:
            if ti_tags[k] == -1 or ti_tags[k] is None:
                ti_tags[k] = 0

    time_interval = parse_time_interval_tags(ti_tags)
    if time_interval == -1:
        append_fixme_value(tags, "time interval parse failure")
        time_interval = None

    if time_interval in ("00:00-00:00", "00:00-24:00"):
        time_interval = None

    all_lanes = tags["KOEFAETKNA"] == "Körbana"
    direction = parse_direction(tags)

    # 'NVDB_guess_lanes' is a guess for lanes, later converted to 'lanes' if not better source is available
    lane_count = 1
    if direction == "" and all_lanes:
        # assume two lanes
        lane_count = 2
        tags["NVDB_guess_lanes"] = 2
    elif all_lanes:
        tags["NVDB_guess_lanes"] = 1
    else:
        # hopefully Antal_korfalt2 has this covered
        pass

    if time_interval is not None:
        tags["lanes:bus" + direction + ":conditional"] = "%s @ (%s)" % (lane_count, time_interval)
    else:
        tags["lanes:bus" + direction] = lane_count

    _ = [tags.pop(key, None) for key in [ "MIN13", "MINUT", "TIM12", "TIMME", "DAGSLAG", "STARTDATUM", "SLUTDATUM", "STARTDAG", "SLUTDAG", "KOEFAETKNA" ]]

# tag_translation_P_ficka()
#
# Layby parkings
#
def tag_translation_P_ficka(tags):
    tags["amenity"] = "parking"
    tags["parking"] = "layby"
    if tags["SIDA"] == "Höger":
        tags["NVDB_layby_side"] = "right"
    elif tags["SIDA"] == "Vänster":
        tags["NVDB_layby_side"] = "left"
    else:
        # Note: "Mitt" has been observed in Rättvik
        _log.warning(f"unknown SIDA {tags} (RLID {tags['RLID']})")
        append_fixme_value(tags, "P_ficka: unknown SIDA value")

    # "Uppställbar längd", that is the number of meters that can be used for parking,
    # specified for about 1/3 of the laybys. There is no established OSM key for this
    # particular purpose, we use 'maxlength'here.
    length = tags.get("UPPTAELBGD", -1)
    if length > 0:
        tags["maxlength"] = length

    del_keys = [
        "PLACERING", # "Längs vägen" or "Avskild från vägen, still close enough for layby
        "UPPTAELBGD",
        "SIDA",
        "XKOORDINAT",
        "YKOORDINAT"
    ]
    for k, v in tags.items():
        if v is None or v == "Finns ej" or v == "Okänt":
            del_keys.append(k)
    for k in del_keys:
        tags.pop(k, None)

    del_keys = []
    add_tags = {}
    extra_nodes = []
    for k, v in tags.items():
        unknown_key = False

        if k == "NAMN" and v != -1: # Namn
            add_tags["name"] = v
        elif k == "TOALETT":    # Toalett
            extra_nodes.append({"amenity": "toilets"})
        elif k == "BORMEDITER": # Bord med sittplatser
            extra_nodes.append({"leisure": "picnic_table"})
        elif k == "SOPKAERL":   # Sopkärl
            extra_nodes.append({"amenity": "waste_disposal"})
        elif k == "MOLOK":      # Molok
            extra_nodes.append({"amenity": "waste_disposal"}) # not 100% sure what a Molok is...
        else:
            unknown_key = True

        if not unknown_key:
            del_keys.append(k)

    for k in del_keys:
        del tags[k]
    tags.update(add_tags)

    add_extra_nodes_tag(tags, extra_nodes)

# tag_translation_Rastplats()
#
# Highway rest areas
#   - NVDB point data, packed with tags
#   - Cannot be mapped as a single node in OSM due to the many tags
#   - As these are few (1 - 5 per kommun), we don't solve this automatically but add the
#     extra tags in a custom field and a fixme tag so these can be completed manually,
#     preferably by making the rest area parking as an area rather than a node and mapping
#     the individual parts as separate nodes
#
def tag_translation_Rastplats(tags):
    del_keys = [
        "HUVUDMAN",   # Huvudman
        "RASPLASTYP", # Rastplatstyp (rastplats, enkel rastplats)
        "AVKERNNGAT", # Avkörningspunkt X-Koordinat
        "AVKERNNG13", # Avkörningspunkt Y-Koordinat
        "ALTRNAIVAT", # Alternativ avkörningspunkt X-Koordinat
        "ALTRNAIV15", # Alternativ avkörningspunkt Y-Koordinat
        "OEVIGURUNG", # Övrig utrustning
        "SAEERHTSDD", # Säkerhetsskydd (rare tag, unclear what it means...)
        "OEVIGPRKET", # Övrig parkeringsmöjlighet
    ]

    # remove all keys with value No or Unknown or -1
    for k, v in list(tags.items()):
        if v in [None, "nej", "Nej", "okänt", "Okänt", "-1"] or (isinstance(v, (int, float)) and v == -1):
            del_keys.append(k)

    for k in del_keys:
        tags.pop(k, None)

    # Note: highway=rest_area would be more logical as main feature, but
    # amenity=parking tag is much more mature, so we use that as the main
    # tag here
    parking_capacity = 0
    tags["amenity"] = "parking"
    tags["access"] = "yes"
    del_keys = []
    add_tags = {}
    extra_nodes = []
    for k, v in tags.items():
        unknown_key = False

        if k == "RASPLASNMN": # Rastplatsnamn
            add_tags["name"] = v
        elif k == "RASPLASASS": # Rastplatsadress
            add_tags["addr:place"] = v
        elif k == "BELYSNING":  # Belysning
            add_tags["lit"] = "yes"
        elif k == "SKOTSEANIG": # Skötselansvarig
            add_tags["operator"] = v
        elif k == "LAEKADESSS": # Länkadress
            add_tags["website"] = v
        elif k == "UTPKADAETS": # Utpekad lämplig lastbilsparkeringsplats
            add_tags["hgv"] = "yes" # unofficial but in-use
        elif k == "ANTLMAKEIL": # Antal markerade parkeringsplatser för personbil
            parking_capacity += v
        elif k == "ANTLMAKEEP": # Antal markerade parkeringsplatser för personbil + släp
            parking_capacity += v
        elif k == "ANTLMAKE20": # Antal markerade parkeringsplatser för lastbil
            add_tags["hgv"] = "yes"
            parking_capacity += v
        elif k == "ANTLMAKE21": # Antal markerade parkeringsplatser för lastbil + släp
            add_tags["hgv"] = "yes"
            parking_capacity += v
        elif k == "ANTLMAKE22": # Antal markerade parkeringsplatser för husbil
            parking_capacity += v
        elif k == "ANTLMAKESS": # Antal markerade parkeringsplatser för buss
            add_tags["bus"] = "yes" # unofficial but in-use
            parking_capacity += v
        elif k == "LATINTEMNG":   # Latrintömning
            extra_nodes.append({"amenity": "sanitary_dump_station"})
        elif k == "LATINTEMNA": # Latrintömning löstagbar tunna
            extra_nodes.append({"amenity": "sanitary_dump_station"})
        elif k == "LATINTEM28": # Latrintömning fastmonterad tunna
            extra_nodes.append({"amenity": "sanitary_dump_station"})
        elif k == "HCPNPASATT": # HCP-anpassad toalett
            extra_nodes.append({ "amenity": "toilets", "wheelchair": "yes"})
        elif k == "SOPKAERL":   # Sopkärl
            extra_nodes.append({"amenity": "waste_disposal"})
        elif k == "DUSHMOJLET": # Duschmöjlighet
            extra_nodes.append({"amenity": "shower"})
        elif k == "HUNRASGARD": # Hundrastgård
            extra_nodes.append({"amenity": "dog_toilet"})
        elif k == "RESTAURANG": # Restaurang
            extra_nodes.append({"amenity": "restaurant"})
        elif k == "SERVERING":  # Servering
            extra_nodes.append({"amenity": "cafe"})
        elif k == "HAETRATGRD": # Hästrastgård
            extra_nodes.append({"amenity": "horse_exercise_area"}) # custom tag
        elif k == "INFRMAIOON": # Information
            extra_nodes.append({"information": "board"})
        elif k == "LEKTRUTNNG": # Lekutrustning
            extra_nodes.append({"leisure": "playground"})
        elif k == "BORMEDITER": # Bord med sittplatser
            extra_nodes.append({"leisure": "picnic_table"})
        else:
            unknown_key = True

        if not unknown_key:
            del_keys.append(k)

    for k in del_keys:
        del tags[k]
    tags.update(add_tags)

    if parking_capacity > 0:
        tags["capacity"] = parking_capacity

    add_extra_nodes_tag(tags, extra_nodes)

# tag_translation_Vagnummer()
#
# Road numbers, may be more than one per road. Information is refined in highway
# resolve function.
#
def tag_translation_Vagnummer(tags):
    huvudnr = tags["HUVUDNR"]
    undernr = tags.get("UNDERNR", None)
    if undernr <= 0 or undernr is None:
        undernr_str = ""
    else:
        undernr_str = "." + str(undernr)
    if tags["EUROPAVÄG"] == -1:
        # E road number with space (eg "E 4" instead of "E4") is not Swedish standard,
        # but we need to follow the standard used in OSM over Europe which is using
        # a space.
        tags["NVDB_vagnummer"] = "E " + str(huvudnr) + undernr_str
    else:
        if huvudnr > 499:
            lan_str_tab = {
                1:  "AB", # Stockholms län
                3:  "C",  # Uppsala län
                4:  "D",  # Södermanlands län
                5:  "E",  # Östergötlands län
                6:  "F",  # Jönköpings län
                7:  "G",  # Kronobergs län
                8:  "H",  # Kalmar län
                9:  "I",  # Gotlands län
                10: "K",  # Blekinge län
                11: "L",  # (f.d. Kristianstads län)
                12: "M",  # Skåne län (f.d. Malmöhus län)
                13: "N",  # Hallands län
                14: "O",  # Västra Götalands län (f.d. Götebors- och Bohus län)
                15: "P",  # (f.d. Älvsborgs län)
                16: "R",  # (f.d. Skaraborgs län)
                17: "S",  # Värmlands län
                18: "T",  # Örebro län
                19: "U",  # Västmanlands län
                20: "W",  # Dalarnas län (f.d. Kopparbergs län)
                21: "X",  # Gävleborgs län
                22: "Y",  # Västernorrlands län
                23: "Z",  # Jämtlands län
                24: "AC", # Västerbottens län
                25: "BD"  # Norrbottens län
            }
            lan_str = lan_str_tab[tags["LÄN"]] + " "
        else:
            lan_str = ""
        tags["NVDB_vagnummer"] = lan_str + str(huvudnr) + undernr_str

    _ = [tags.pop(key, None) for key in ["HUVUDNR", "UNDERNR", "EUROPAVÄG", "LÄN"]]

# tag_translation_Vaghinder()
#
# Barriers
#
def tag_translation_Vaghinder(tags):
    hindertyp = tags["HINDERTYP"]
    passbredd = tags["PASSBREDD"]
    if passbredd >= 0:
        tags["maxwidth"] = passbredd

    if hindertyp == "pollare":
        tags["barrier"] = "bollard"
    elif hindertyp == "eftergivlig grind":
        tags["barrier"] = "swing_gate"
    elif hindertyp == "ej öppningsbar grind eller cykelfålla":
        tags["barrier"] = "cycle_barrier"
    elif hindertyp == "låst grind eller bom":
        # These type of gates are often mostly open. In some cases not, but in any case
        # we choose access=permissive to be the least bad default value.
        tags["barrier"] = "gate"
        tags["access"] = "permissive"
    elif hindertyp == "betonghinder":
        tags["barrier"] = "block"
    elif hindertyp == "spårviddshinder":
        tags["barrier"] = "bus_trap"
    elif hindertyp == "övrigt":
        tags["barrier"] = "yes"
    else:
        append_fixme_value(tags, "Vaghinder: unknown hindertyp")
        _log.warning(f"unknown hindertyp {hindertyp} (RLID {tags['RLID']})")

    del tags["PASSBREDD"]
    del tags["HINDERTYP"]

# preprocess_name()
#
# NVDB has some quirks in its name (NAMN) tags sometimes, like all uppercase etc. This is
# cleaned up here.
#
def preprocess_name(name):

    if not isinstance(name, str) or name == "-1":
        # sometimes NAMN is set to None or -1
        return None

    # strip leading/trailing whitespace in name (rare, but happens)
    name = name.strip()

    # if it's an all uppercase name, capitalize it
    if name.isupper():
        name = string.capwords(name)
        # Some common strings are not names, convert the capitalized strings back to lowercase/uppercase as suited
        replace_table = {
            "Gc": "GC",
            "Mot": "mot",
            "Med": "med",
            "Grenväg": "grenväg",
            "Stickväg": "stickväg",
            "Grenvägar": "grenvägar",
            "Stickvägar": "stickvägar",
            "Stick": "stick",
            "Väg": "väg",
            "Tunnel": "tunnel",
            "Körbana": "körbana"
        }
        for k, v in replace_table.items():
            name = name.replace(k, v)

    replace_table = {
        "CPL ": "Cpl ", # cirkulationsplats
        ";": ":" # ';' not compatible with OSM, for example "G;a" instead of "G:a" as abbreviation of "Gamla" has been observed
    }
    for k, v in replace_table.items():
        name = name.replace(k, v)

    if name.startswith("Cpl ") and "rondell" in name:
        # Cpl is redundant if name contains rondell
        name = name[4:]

    return name

# process_tag_translations()
#
# Translate tags for a layer using provided matching entry from TAG_TRANSLATIONS,
# some are static translations from the table, others run matching
# tag_translation_*() function
#
def process_tag_translations(tags, tag_translations):

    if not bool(tag_translations):
        return

    if "NAMN" in tags:
        name = tags["NAMN"]
        new_name = preprocess_name(name)
        if new_name != name:
            if new_name is None:
                _log.info(f"Removed invalid name: '{name}'")
            else:
                _log.info(f"Changed name: '{name}' => '{new_name}'")
            tags["NAMN"] = new_name

    if "translator_function" in tag_translations:
        tag_translations["translator_function"](tags)
    if tag_translations.get("expect_unset_time_intervals", False):
        tag_translation_expect_unset_time_intervals(tags)
    replaced_keys = []
    new_items = {}
    if "add_keys_and_values" in tag_translations:
        all_kv = tag_translations["add_keys_and_values"]
        if not isinstance(all_kv, list):
            all_kv = [ all_kv ]
        for item in all_kv:
            kv = item.split('=')
            if len(kv) == 1:
                raise RuntimeError("Bad item in add_keys_and_values %s" % item)
            new_items[kv[0].strip()] = kv[1].strip()
    for k, v in tags.items():
        # look at k=v first as we want to support both key=value and key replacement for the same key.
        kv = "%s=%s" % (k, v)
        if kv in tag_translations:
            sub = tag_translations.get(kv)
            replaced_keys.append(k)
            if sub is not None:
                # replace specific key/value combination with new key/value combo
                if not isinstance(sub, list):
                    sub = [sub]
                for kv in sub:
                    kv = kv.split('=')
                    new_items[kv[0].strip()] = kv[1].strip()
        elif k in tag_translations:
            sub = tag_translations[k]
            # replace key with new key name (or remove it)
            replaced_keys.append(k)
            if sub is not None:
                new_items[sub] = v
    tags.update(new_items)
    for k in replaced_keys:
        del tags[k]

    # convert to int or float where approriate
    for k, v in tags.items():
        if not isinstance(v, str):
            continue
        try:
            intv = int(v)
            tags[k] = intv
        except ValueError:
            try:
                fv = float(v)
                tags[k] = fv
            except ValueError:
                pass

#
# Table for tag translations.
#
TAG_TRANSLATIONS = {
    "NVDB-Antal_korfalt2": {
        "KOEFAETSAL": "lanes",
        "KOEFAETING": None,
        "KOEFAETIN1": None,
        "RIKTNING": None
    },
    "NVDB-Barighet": {
        "translator_function": tag_translation_Barighet,
    },
    "NVDB-BegrAxelBoggiTryck": {
        "translator_function": tag_translation_BegrAxelBoggiTryck,
    },
    "NVDB-BegrBruttovikt": {
        "translator_function": tag_translation_BegrBruttovikt,
    },
    "NVDB-BegrFordBredd": {
        "translator_function": tag_translation_BegrFordBredd,
    },
    "NVDB-BegrFordLangd": {
        "translator_function": tag_translation_BegrFordLangd,
    },
    "NVDB-Bro_och_tunnel": {
        "IDENTITET": None,
        "LAENGD": None,
        "NAMN": None
    },
    "NVDB-Cirkulationsplats": {
        "add_keys_and_values": "junction=roundabout",
        "RIKTNING": None
    },
    "NVDB-CykelVgsKat": {
        "FOEBINELRI": "NVDB_cykelvagkat",
    },
    "NVDB-Farjeled": {
        "LEDSNAMN": "name",
        "add_keys_and_values": "route=ferry"
    },
    "NVDB-ForbjudenFardriktning": {
        "RIKTNING=Mot": "oneway=yes",
        "RIKTNING=Med": "oneway=-1",
        "expect_unset_time_intervals": True
    },
    "NVDB-ForbudTrafik": {
        "translator_function": tag_translation_ForbudTrafik,
    },
    "NVDB-FunkVagklass": {},
    "NVDB-Gagata": {
        "add_keys_and_values":    "NVDB_gagata=yes",
        "SIDA=Vänster":           "NVDB_gagata_side=left",
        "SIDA=Höger":             "NVDB_gagata_side=right",
        "SIDA=Vänster och höger": "NVDB_gagata_side=both",
        "SIDA=None": None
    },
    "NVDB-Gangfartsomrade": {
        "add_keys_and_values":    "NVDB_gangfartsomrode=yes",
        "SIDA=Vänster":           "NVDB_gangfartsomrode_side=left",
        "SIDA=Höger":             "NVDB_gangfartsomrode_side=right",
        "SIDA=Vänster och höger": "NVDB_gangfartsomrode_side=both",
        "SIDA=None": None
    },
    "NVDB-Gatunamn": {
        "NAMN": "name",
        "RIKTNING": None,
        "ORDNING": None,
        "LANKROLL": "NVDB_road_role",
        "SEQ_NO": None,
        "VARDVAG": None
    },
    "NVDB-Gatutyp": {
        "TYP": "NVDB_gatutyp",
        "INDSTRVAEG": None,
        "UPPAMLNDDE": None,
        "AVFRTSAEEG": None
    },
    "NVDB-GCM_belyst": {
        "add_keys_and_values": "lit=yes"
    },
    "NVDB-GCM_separation": {
        "translator_function": tag_translation_GCM_separation
    },
    "NVDB-GCM_vagtyp": { },
    "NVDB-Hastighetsgrans": {
        "translator_function": tag_translation_Hastighetsgrans,
    },
    "NVDB-Huvudled": {
        "add_keys_and_values": "priority_road=designated",
    },
    "NVDB-InskrTranspFarligtGods": {
        "translator_function": tag_translation_InskrTranspFarligtGods,
    },
    "NVDB-Kollektivkorfalt": {
        "translator_function": tag_translation_Kollektivkorfalt,
    },
    "NVDB-Miljozon": {
        "AARTA8": None,
        "AARTAL": None,
        "LOEPNUMME9": None,
        "LOEPNUMMER": None,
        "ORGNISTIO7": None,
        "ORGNISTIOD": None,
        "MEDELADEON": None,
        "MILOEZNKSS=Miljözon klass 1": "environmental_zone:sv=1", # custom tag
        "MILOEZNKSS=Miljözon klass 2": "environmental_zone:sv=2", # custom tag
        "MILOEZNKSS=Miljözon klass 3": "environmental_zone:sv=3", # custom tag
        "MILOEZNKSS=None": None
    },
    "NVDB-Motortrafikled": {
        "add_keys_and_values": "NVDB_motortrafikled=yes"
    },
    "NVDB-Motorvag": {
        "add_keys_and_values": "NVDB_motorvag=yes"
    },
    "NVDB-Ovrigt_vagnamn": {
        "NAMN": "name",
        "ORGANISAT": None
    },
    "NVDB-Reflinjetillkomst": {
        "ANSVARORG": None,
        "DIM1": None,
        "FLYGHJD1": None,
        "KOMPROC1": None,
        "MEDELFEL1": None,
        "METREFLIN1": None,
        "SKALFKT1": None,
        "SLUTDAT1": None
    },
    "NVDB-RekomVagFarligtGods": {
        "REKOMEND=rekommenderad primär väg":   "hazmat=designated",
        "REKOMEND=rekommenderad sekundär väg": "hazmat=designated"
    },
    "NVDB-Slitlager": {
        # note: surface=paved would be more correct, but asphalt is so dominant in Sweden that we use that
        "TYP=belagd": "surface=asphalt",

        # Note 1: NVDB's "grus" is more specific than it should be, "obelagd"/unpaved would be more correct as
        # grus is used for all roads that are not paved.
        "TYP=grus":   "surface=unpaved"
    },
    "NVDB-Tillganglighet": {
        "KLASS=A": "NVDB_availability_class=1",
        "KLASS=B": "NVDB_availability_class=2",
        "KLASS=C": "NVDB_availability_class=3",
        "KLASS=D": "NVDB_availability_class=4"
    },
    "NVDB-Vagbredd": {
        "BREDD": "width",
        "MÄTMETOD": None
    },
#    "NVDB-Vaghallare": {
#        "VAEHAALAMN": "NVDB_maintainer_name",
#        "VAEHAALAYP": "NVDB_maintainer_type",
#        "FOEVALNIRM": "NVDB_management_type",
#        "AVVKANEUAR": None,
#        "ORGNISTIER": None
#    },
    "NVDB-Vagnummer": {
        "translator_function": tag_translation_Vagnummer,
        "RIKTNING": None,
        "ORDNING": None,
        "LANKROLL": "NVDB_road_role",
        "SEQ_NO": None,
        "VARDVAG": None,
    },
    "EVB-Driftbidrag_statligt": {
        "add_keys_and_values": "NVDB_government_funded=yes",
        "VAGDELSN1": None,
        "VAGNR1": None,
        "SLITLAG1": None,
        "TRAFIKKL1": None,
    },
    "VIS-Funktionellt_priovagnat": {},
    "VIS-Omkorningsforbud": {
        "RIKTNING=Med":         "overtaking:forward=no",
        "RIKTNING=Mot":         "overtaking:backward=no",
        "RIKTNING=Med och mot": "overtaking=no",
    },
    "VIS-Slitlager": {
        "TYP=0": None,                  # Uppgift saknas
        "TYP=1": "surface=asphalt",     # Bituminös
        "TYP=2": "surface=asphalt",     # Oljegrus
        "TYP=3": "surface=fine_gravel", # Grus
        "TYP=4": "surface=gravel",      # Sten
        "TYP=5": "surface=concrete",    # Betong
        "TYP=6": "surface=asphalt",     # Y1G
        "TYP=7": "surface=asphalt"      # Förseglat grus
    },
    "NVDB-Farthinder": {
        # Ideally TYP=1 should be with priority=* (to differ from TYP=3) but there's no info on which
        # side the choker is unfortunately.
        "TYP=1":  "traffic_calming=choker",  # Avsmalning till ett körfält
        # Could also be "bump", but "hump" is statistically much more common
        "TYP=2":  "traffic_calming=hump",    # Gupp (cirkulärt gupp eller gupp med ramp utan gcm-passage)
        # TYP=3 is similar to TYP=1, but not as narrow choker.
        "TYP=3":  "traffic_calming=choker",  # Sidoförskjutning - avsmalning
        "TYP=4":  "traffic_calming=island",  # Sidoförskjutning - refug
        "TYP=5":  "traffic_calming=dip",     # Väghåla
        "TYP=6":  "traffic_calming=cushion", # Vägkudde
        "TYP=7":  "traffic_calming=table",   # Förhöjd genomgående GCM-passage
        "TYP=8":  "traffic_calming=table",   # Förhöjd korsning
        "TYP=9":  "traffic_calming=yes",     # Övrigt farthinder
        "TYP=10": "traffic_calming=dynamic_bump", # Dynamiskt aktivt farthinder
        "TYP=11": "traffic_calming=dynamic_bump", # Dynamiskt passivt farthinder
        "LAEGE": None
    },
    "NVDB-GCM_passage": {
        "REFGPASAGE=ja": "crossing:island=yes",
        "REFGPASAGE=nej": None,
        "REFGPASAGE=okänt": None,
        "TRAIKATTYP": None,
        "PASSAGETYP=annan ordnad passage i plan": None,
        "PASSAGETYP=planskild passage underfart": None,
        "PASSAGETYP=planskild passage överfart": None,
        "PASSAGETYP=övergångsställe och/eller cykelpassage/cykelöverfart i plan": [ "highway=crossing", "crossing=marked" ],
        "PASSAGETYP=signalreglerat övergångsställe och/eller signalreglerad cykelpassage/cykelöverfart i plan": [ "highway=crossing", "crossing=traffic_signals" ],
    },
    "NVDB-Hojdhinder45dm": {
        "FRIHOJD": "maxheight",
        "HOJDID": None,
        "TYP": None
    },
    "NVDB-Korsning": {
        "GENRALSEYP": "NVDB_generaliseringstyp",
        "SIGALRGLNG=ja":    [ "highway=traffic_signals" ],
        "SIGALRGLNG=nej":   None,
        "SIGALRGLNG=okänt": None,
        "NAMN": "name",
        "TRAIKPATER": None,
        "TPLUNDRNER": None,
        "XKOORDINAT": None,
        "YKOORDINAT": None
    },
    "NVDB-Stopplikt": {
        "add_keys_and_values":  "highway=stop",
        "RIKTNING=Med":         "direction=forward",
        "RIKTNING=Mot":         "direction=backward",
        "RIKTNING=Med och mot": None
    },
    "NVDB-Vaghinder": {
        "translator_function": tag_translation_Vaghinder
    },
    "NVDB-Vajningsplikt": {
        "add_keys_and_values":  "highway=give_way",
        "RIKTNING=Med":         "direction=forward",
        "RIKTNING=Mot":         "direction=backward",
        "RIKTNING=Med och mot": None
    },
#    "NVDB-Vandmojlighet": {
#        "add_keys_and_values": "highway=turning_circle",
#        "KLASS": None,
#        "TYP": None,
#    },
    "VIS-Jarnvagskorsning": {
        "PLAKORNIID": None,              # Plankorsnings-Id
        "JVGBANDEL": None,               # Jvg-bandel
        "JVGILOETER": None,              # Jvg-kilometer
        "JVGMETER": None,                # Jvg-meter
        "ANTALSPAAR": "NVDB_rwc_tracks", # Antal spår
        "VAEPROILEN": None,              # Vägprofil farligt vägkrön
        "VAEPROILVA": None,              # Vägprofil tvär kurva
        "VAEPROILNG": None,              # Vägprofil brant lutning
        "VAEGSKYDD=1": "crossing:barrier=full", # Helbom
        "VAEGSKYDD=2": "crossing:barrier=half",	# Halvbom
        "VAEGSKYDD=3": [ "crossing:bell=yes", "crossing:light=yes" ], # Ljus och ljudsignal
        "VAEGSKYDD=4": "crossing:light=yes",    # Ljussignal
        "VAEGSKYDD=5": "crossing:bell=yes",	# Ljudsignal
        "VAEGSKYDD=6": "crossing:saltire=yes",  # Kryssmärke
        "VAEGSKYDD=7": "crossing:barrier=no",   # Utan skydd
        "PORALHEJJD": "maxheight", # Portalhöjd
        "PORALHEJJD=0.0": None, # Portalhöjd, value for no portal
        "PORALHEJJD=9.0": None, # Portalhöjd, alt value for no portal
        "TAAGFLOEDE": None,   # Tågflöde
        "KONAKTEDNG": None,   # Contact line, in OSM set on railway, not crossing
        "KORMAGSIIN": None,   # Kort magasin
        "XKOORDINAT": None,   # X-koordinat
        "YKOORDINAT": None,   # Y-koordinat
        "SENSTANDAD": None    # Senast ändrad
    },
    "VIS-P_ficka": {
        "translator_function": tag_translation_P_ficka
    },
    "VIS-Rastplats" : {
        "translator_function": tag_translation_Rastplats,
    }
}

# _build_vehicle_list
#
# extract vehicles form the VEHICLES_AND_ROAD_USERS_TRANSLATIONS table
#
def _build_vehicle_list():
    vl = []
    for vehicle in VEHICLES_AND_ROAD_USERS_TRANSLATIONS.values():
        if vehicle.startswith("PURPOSE") or vehicle.startswith("USER") or vehicle == "IGNORE":
            continue
        vl.append(vehicle)
    return vl

ALL_VEHICLES = _build_vehicle_list()
