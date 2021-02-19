# way_to_simplify_epsilon()
#
# Return the precision (in meters) we want to keep when geometry is simplified.
#
def way_to_simplify_epsilon(way):
    # This value of 0.2 is consistent what is used in the Norweigian imports.
    # It's a quite high detail level and will keep most points available in NVDB
    # geometry.
    return 0.2

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


# get_directional_nodes()
#
# get a dictionary of all nodes that depend on the direction of the way it is tied to.
#
def get_directional_nodes(point_db):
    directional_nodes = {}
    for nodes in point_db.values():
        for node in nodes:
            if "direction" in node.tags:
                directional_nodes[node.way] = node
    return directional_nodes

# reverse_way()
#
# Reverse way, changing tags if necessary
#
def reverse_way(way, directional_nodes):

    way.way = list(reversed(way.way))

    for p in way.way:
        if p in directional_nodes:
            node = directional_nodes[p]
            if node.tags["direction"] == "backward":
                node.tags["direction"] = "forward"
            elif node.tags["direction"] == "forward":
                node.tags["direction"] = "backward"

    new_tags = {}
    for k, v in way.tags.items():
        if k == "oneway":
            if v == "yes":
                v = -1
            elif v == -1:
                v = "yes"
            else:
                raise RuntimeError("Cannot reverse oneway")
        elif k == "direction":
            # direction normally used on points only, but here also check for ways to be sure
            if v == "forward":
                v = "backward"
            elif v == "backward":
                v = "forward"
        elif ":forward" in k:
            k = k.replace(":forward", ":backward")
        elif ":backward" in k:
            k = k.replace(":backward", ":forward")
        elif ":left" in k:
            k = k.replace(":left", ":right")
        elif ":right" in k:
            k = k.replace(":right", ":left")
        new_tags[k] = v
    way.tags = new_tags
