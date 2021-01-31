import logging

from nvdb_segment import *
from geometry_basics import calc_way_length

_log = logging.getLogger("tags")


def merge_tags(seg, src, data_src_name):
    way = seg.way
    dst = seg.tags
    src_date = src.get("FRAN_DATUM", 0)
    fixmes = []
    for k, v in src.items():
        if k in NVDB_GEOMETRY_TAGS or k == "FRAN_DATUM":
            # ignore special tags
            continue
        if not k in dst:
            # new value
            dst[k] = v
            seg.tag_src[k] = (data_src_name, src_date)
            continue

        ov = dst[k]
        if isinstance(ov, list):
            match = False
            for item in ov:
                if item == v:
                    match = True
                    break
            if match:
                continue
        elif ov == v:
            if seg.tag_src[k][1] < src_date:
                seg.tag_src[k] = (data_src_name, src_date)
            continue

        if k == "fixme":
            append_tag_value(dst, k, v)
            continue

        resolved = False
        fixme = False
        solution = "resolve solution not specified"

        # go through tags that can become lists first
        if not resolved:
            if data_src_name == "NVDB_DKVagnummer":
                if k == "NVDB_vagnummer":
                    append_tag_value(dst, k, v)
                    solution = "list"
                    resolved = True
            elif data_src_name in [ "NVDB_DKGatunamn", "NVDB_DKOvrigt_vagnamn", "NVDB_DKKorsning" ]:
                if k == "name":
                    if v is None:
                        # unusual, but 'None' have been observed
                        solution = "ignoring 'None'"
                    else:
                        # this is normal for roundabouts (names of streets passing through)
                        append_tag_value(dst, "alt_name", v)
                        solution = "list"
                    resolved = True

        if not resolved and isinstance(dst[k], list):
            fixme = True
            resolved = True
            fixmes.append("Could not resolve key %s, alt value %s" % (k, v))


        # go through things we want to resolve before we look at the date
        if not resolved:
            if data_src_name == "VIS_DKSlitlager" and seg.tag_src[k][0] == "NVDB_DKSlitlager":
                dst[k] = v
                seg.tag_src[k] = (data_src_name, src_date)
                solution = "prioritized layer"
                resolved = True
            elif seg.tag_src[k][0] == "VIS_DKSlitlager" and data_src_name == "NVDB_DKSlitlager":
                solution = "prioritized layer"
                resolved = True

        # resolve by date, if possible
        if not resolved:
            if seg.tag_src[k][1] != src_date:
                if seg.tag_src[k][1] < src_date:
                    dst[k] = v
                    seg.tag_src[k] = (data_src_name, src_date)
                solution = "date"
                resolved = True

        # look at specific data sources and keys
        if not resolved:
            if data_src_name == "NVDB_DKGatutyp":
                if k == "NVDB_gatutyp":
                    # if same date, just keep current, not too important and Gatutyp is a bit messy data
                    solution = "not deemed important, current value kept"
                    resolved = True
            elif data_src_name == "NVDB_DKHastighetsgrans":
                if k in ("maxspeed", "maxspeed:forward", "maxspeed:backward"):
                    if ov > v:
                        dst[k] = v # keep smaller value
                    solution = "kept smaller value"
                    resolved = True
            elif data_src_name in [ "NVDB_DKInskrTranspFarligtGods", "NVDB_DKRekomVagFarligtGods" ]:
                # We've seen overlaps of these two layers (Malmö dataset), but as DKRekomVagFarligtGods is more
                # specific we trust that layer more
                if k == "hazmat":
                    if ov != "designated" and v == "designated":
                        dst[k] = v
                    solution = "kept designated"
                    resolved = True
            elif data_src_name == "NVDB_DKVagbredd":
                if k == "width":
                    if ov > v:
                        dst[k] = v
                    solution = "kept smaller value"
                    resolved = True
            elif data_src_name == "NVDB_DKGagata":
                if k == "NVDB_gagata_side":
                    if (ov == "left" and v == "right") or (ov == "right" and v == "left"):
                        dst[k] = "both"
                        solution = "merged to 'both'"
                        resolved = True
            elif data_src_name == "NVDB_DKGCM_vagtyp":
                if k == "GCMTYP":
                    gcm_resolve = [
                        (11, 17, 17), # gångbana 11 => trappa 17
                        (1, 3, 3), # cykelbana 1 => cykelpassage 3
                        (1, 4, 4), # cykelbana 1 => övergångsställe 4
                        (12, 5, 5), # trottoar 12 => gatupassage utan märkning 5
                        (12, 4, 4), # trottoar 12 => övergångsställe 4
                    ]
                    for gcm in gcm_resolve:
                        if (ov == gcm[0] and v) == gcm[1] or (ov == gcm[1] and v == gcm[0]):
                            dst[k] = gcm[2]
                            solution = "used GCM resolve table"
                            resolved = True
                            break
            elif data_src_name == "NVDB_DKFarthinder":
                if k == "traffic_calming":
                    if ov == "yes" and v != "yes":
                        dst[k] = v
                        solution = "used more specific"
                        resolved = True
                    elif ov == "choker" and v != "choker" and v != "yes":
                        dst[k] = v
                        solution = "prefer other value over choker"
                        resolved = True

        if not resolved and isinstance(way, list):
            dist, _ = calc_way_length(way)
            if dist < 1.0:
                # short segment, we don't care
                solution = "short segment (%g), keeping old value" % dist
                resolved = True

        if not resolved:
            fixme = True
            resolved = True
            fixmes.append("Could not resolve key %s, alt value %s" % (k, v))

        if fixme:
            res_str = "Warning: not resolved, added fixme tag"
        else:
            res_str = "Resolved, using %s (%s)" % (dst[k], solution)
        if fixme or solution not in ("list", "prioritized layer"):
            _log.warning(f"Conflicting value for key '{k}' ('{v}' and '{ov}', RLID {seg.rlid}). {res_str}")

        if dst[k] == v and seg.tag_src[k][1] < src_date:
            seg.tag_src[k] = (data_src_name, src_date)

    for v in fixmes:
        append_fixme_value(dst, v)


def append_fixme_value(tags, fixme_value):
    if "fixme" not in tags:
        fixme_value = "NVDB import: " + fixme_value
    append_tag_value(tags, "fixme", fixme_value)


def append_tag_value(tags, k, v):
    if k not in tags:
        tags[k] = v
        return
    current = tags[k]
    if isinstance(current, list):
        if not v in current:
            current.append(v)
    elif current != v:
        tags[k] = [ current, v ]
