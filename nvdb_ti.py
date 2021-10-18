# Tools for parsing NVDB time intervals and converting them to OSM "opening hours" format
#
# FIXME: Currently this code is very hackish. At some point it should be redesigned to
# parse to a "time interval" class and then work on that rather than just work directly on
# strings
#
import logging

from sortedcontainers import SortedDict
from scanf import scanf

_log = logging.getLogger("nvdb_ti")
time_interval_strings = set()


# parse_time_interval_tags()
#
# Parse NVDB time interval tags into OSM intervals
#
def parse_time_interval_tags(tags):
    # FIXME this parsing code became a bit convoluted, could be simplified...
    interval_keys = [
        {
            "keys": [ "STTIM", "STMIN", "SLTIM", "SLMIN" ],
            "not_used_values": [ -1, None ],
            "output_key": "hourmin_interval",
            "parser": parse_hourmin_interval,
        },
        {
            "keys": [ "STDAT", "SLDAT" ],
            "not_used_values": [ -1, None ], # most common not used == "1899-12-29" x 2, handled in parser
            "output_key": "date_interval",
            "parser": parse_date_interval
        },
        {
            "keys": [ "STDAG", "SLDAG" ],
            "not_used_values": [ None, -1 ],
            "output_key": "day_interval",
            "parser": parse_day_interval
        },
        {
            "keys": [ "DAGSL" ],
            "not_used_values": [ None, -1 ],
            "output_key": "day_type",
            "parser": parse_day_type
        }
    ]
    presuffixes = set()
    del_keys = []
    max_suffix_len = {}
    for k in tags.keys():
        for item in interval_keys:
            for key in item["keys"]:
                split = k.split(key)
                if len(split) > 1:
                    prefix = split[0] + "/"
                    suffix = split[-1]
                    if str(int(suffix)) != suffix or len(split) > 2:
                        _log.warning(f"unexpected time interval key {k} (RLID {tags['RLID']})")
                        return -1
                    if not prefix is max_suffix_len or len(suffix) > max_suffix_len[prefix]:
                        max_suffix_len[prefix] = len(suffix)
                    presuffixes.add(prefix + suffix)
                    del_keys.append(k)
                    break
    parsed_intervals = SortedDict({})
    for presuffix in presuffixes:
        prefix = presuffix.split("/")[0] + "/"
        suffix = presuffix.split("/")[1]
        key = prefix
        if len(suffix) == max_suffix_len[prefix]:
            key += suffix[:-1]
        else:
            key += suffix
        if not key in parsed_intervals:
            parsed_intervals[key] = {}
        output = parsed_intervals[key]
        for item in interval_keys:
            values = []
            not_used_count = 0
            for key in item["keys"]:
                ckey = prefix[:-1] + key + suffix
                values.append(tags.get(ckey, item["not_used_values"][0]))
                if values[-1] in item["not_used_values"]:
                    not_used_count += 1
            if 0 < not_used_count < len(values):
                if item["output_key"] == "day_interval" and values[0] is not None:
                    # exemption: day interval can be specified without SLDAG if it only specifies a single weekday
                    pass
                else:
                    _log.warning(f"mixed used and not used values in time interval keys {item['keys']}"
                                 f" (RLID {tags['RLID']})")
                    return -1
            output_key = item["output_key"]
            if len(suffix) == max_suffix_len[prefix]:
                output_key += suffix[-1]
            if not_used_count == len(values):
                output[output_key] = None
            else:
                output[output_key] = item["parser"](values)
    for k in del_keys:
        del tags[k]
    output_map = {}
    for k, v in parsed_intervals.items():
        prefix = k.split("/")[0] + "/"
        if prefix not in output_map:
            output_map[prefix] = None
        ti_str = merge_time_intervals(v, tags["RLID"])
        if ti_str == -1:
            return -1
        if ti_str is not None:
            if output_map[prefix] is None:
                output_map[prefix] = simplify_time_interval(ti_str)
            else:
                output_map[prefix] = merge_multiple_time_intervals(output_map[prefix], ti_str)
    if len(output_map) == 1 and "/" in output_map:
        return output_map["/"]
    return output_map


def merge_time_intervals(ti, rlid):
    hourmin_int1 = ti.get("hourmin_interval1", None)
    hourmin_int2 = ti.get("hourmin_interval2", None)
    if hourmin_int1 is None and hourmin_int2 is not None:
        _log.warning(f"bad hourmin interval combination (RLID {rlid})")
        return -1
    if hourmin_int1 is not None and hourmin_int2 is not None:
        hourmin_int = hourmin_int1 + "," + hourmin_int2
    else:
        hourmin_int = hourmin_int1

    day_type = ti["day_type"]
    day_interval = ti["day_interval"]
    date_interval = ti["date_interval"]
    merge_str = hourmin_int
    if merge_str is None:
        merge_str = "00:00-24:00"
    if day_type is not None:
        if day_interval is not None and day_type != "vardag":
            _log.warning(f"day_interval ({day_interval}) and day_type ({day_type}) set at the same time (RLID {rlid})")
            return -1
        if day_type in ["vardag", 1]:
            if day_interval is not None:
                # rare case (observed in InskrTranspFarligtGods Stockholm)
                merge_str = "%s %s; PH off" % (day_interval, merge_str)
                day_interval = None
            else:
                merge_str = "Mo-Sa %s; PH off" % merge_str
        elif day_type in ['vardag före sön- och helgdag', 2]:
            merge_str = "Sa %s; PH -1 day %s; PH off" % (merge_str, merge_str)
        elif day_type in ["vardag utom dag före sön- och helgdag", 3]:
            merge_str = "Mo-Fr %s; PH -1 day off; PH off" % merge_str
        elif day_type in ["sön- och helgdag", 4]:
            merge_str = "Su %s; PH %s" % (merge_str, merge_str)
        else:
            _log.warning(f"unknown day type {day_type} (RLID {rlid})")
            return -1
    if day_interval is not None:
        merge_str = day_interval + " " + merge_str
    if date_interval is not None:
        merge_str = "%s %s" % (date_interval, merge_str)
    if merge_str == "00:00-24:00":
        return None
    time_interval_strings.add(merge_str)
    return merge_str


# This is not fully generic, in only can merge time intervals
# merge_time_intervals() is expected to produce
def merge_multiple_time_intervals(dst, src):
    months = [ "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec" ]
    dst_has_date_interval = dst.split()[0] in months
    src_has_date_interval = src.split()[0] in months

    if dst_has_date_interval:
        merge_str = dst + "; " + src
    elif src_has_date_interval:
        merge_str = src + "; " + dst
    else:
        src_has_ph1 = "PH -1 day" in src
        src_has_ph = src.count("PH ") - src.count("PH -1 day") == 1
        if "; PH -1 day off" in dst and src_has_ph1:
            dst = dst.replace("; PH -1 day off", "")
        if "; PH off" in dst and src_has_ph:
            dst = dst.replace("; PH off", "")
        merge_str = dst + "; " + src

    merge_str = simplify_time_interval(merge_str)
    time_interval_strings.add("Merge time intervals: '%s' AND '%s' => '%s'" % (dst, src, merge_str))
    return merge_str

def parse_hourmin_interval(values):
    return "%02d:%02d-%02d:%02d" % (values[0], values[1], values[2], values[3])

def parse_date_interval(values):
    di = parse_range_date(values[0]) + "-" + parse_range_date(values[1])
    if di in ("Dec 29-Dec 29", "Jan 01-Dec 29"):
        return None
    return di

def parse_day_interval(values):
    day_map = { "måndag": "Mo", "tisdag": "Tu", "onsdag": "We", "torsdag": "Th", "fredag": "Fr", "lördag": "Sa", "söndag": "Su", \
                "1": "Mo", "2": "Tu", "3": "We", "4": "Th", "5": "Fr", "6": "Sa", "7": "Su" }
    if values[1] is None:
        return day_map[str(values[0])]
    return day_map[str(values[0])] + "-" + day_map[str(values[1])]

def parse_day_type(values):
    return values[0] # fix at merge

# parse_range_date()
#
# Translate NVDB range date to OSM syntax (exapmle: "1899-10-11" => "Oct 10")
#
def parse_range_date(date_str):
    date_str = date_str.split("-")
    mon = int(date_str[1])
    day = date_str[2]
    mon_str = [ "", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec" ][mon]
    return mon_str + " " + day

def simplify_time_interval_once(ti_str):
    # FIXME: support more cases

    val = scanf('Mo-Sa %2d:%2d-%2d:%2d; Su %2d:%2d-%2d:%2d; PH %2d:%2d-%2d:%2d', ti_str)
    if val is not None:
        for i in range(0, 4):
            if val[i+0] != val[i+4] or val[i+0] != val[i+8]:
                return ti_str
        return "%02d:%02d-%02d:%02d" % val[:4]

    # Mo-Fr 22:00-06:00; Sa 22:00-06:00 => Mo-Sa 22:00-06:00
    val = scanf('Mo-Fr %2d:%2d-%2d:%2d; Sa %2d:%2d-%2d:%2d%*s', ti_str)
    if val is not None:
        for i in range(0, 4):
            if val[i+0] != val[i+4]:
                return ti_str
        return "Mo-Sa %02d:%02d-%02d:%02d%s" % (val[0], val[1], val[2], val[3], ti_str[33:])
    return ti_str

def simplify_time_interval(ti_str):
    out = simplify_time_interval_once(ti_str)
    while out != ti_str:
        ti_str = out
        out = simplify_time_interval_once(ti_str)
    return out

#print(simplify_time_interval('Mo-Sa 22:00-06:00; Su 22:00-06:00; PH 22:00-06:00'))
#print(simplify_time_interval('Mo-Fr 22:00-06:00; Sa 22:00-06:00; PH 22:00-06:00'))
