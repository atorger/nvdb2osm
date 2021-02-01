# way_to_simplify_epsilon()
#
# Depending on type of way return the precision (in meters) we want to keep when
# geometry is simplified.
#
def way_to_simplify_epsilon(way):
    if way.tags.get("junction", "") == "roundabout":
        return 0.25
    if way.tags.get("highway", "") in [ "trunk","primary", "secondary", "tertiary", "unclassified", "track" ]:
        return 1.5
    if way.tags.get("highway", "") in [ "footway", "cycleway" ]:
        return 0.75
    return 1.0

# keep_end_stub()
#
# For short end stubs, return True if we want to keep them anyway depending on type
#
def keep_end_stub(way):
    # in Stockholm dataset a number of steps in stub ends have been observed
    return way.tags.get("highway", None) == "steps"

# way_may_be_reversed()
#
# Return True if the tags allow that the way is reversed, otherwise False
#
def way_may_be_reversed(way):
    return "oneway" not in way.tags

# reverse_way()
#
# Reverse way, changing tags if necessary
#
def reverse_way(way):
    way.way = list(reversed(way.way))
    new_tags = {}
    for k, v in way.tags.items():
        if k == "oneway":
            if v == "yes":
                v = -1
            elif v == -1:
                v = "yes"
            else:
                raise RuntimeError("Cannot reverse oneway")
        elif ":forward" in k:
            k = k.replace(":forward", ":backward")
        elif ":backward" in k:
            k = k.replace(":backward", ":forward")
        new_tags[k] = v
    way.tags = new_tags
