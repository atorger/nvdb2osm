from proj_xy import latlon_str

NVDB_GEOMETRY_TAGS = [ "STARTAVST", "SLUTAVST", "SHAPE_LEN", "AVST", "FRAN_DATUM" ]

class NvdbSegment:
    def __init__(self, *args):
        # python doesn't support multiple constructors, so we use a hack with dynamic args
        if len(args) == 1:
            shapely_dict = args[0]

            assert ("RLID" in shapely_dict), "Missing RLID"
            self.rlid = shapely_dict["RLID"]

            if "FRAN_DATUM" not in shapely_dict:
                shapely_dict["FRAN_DATUM"] = 18990101
            date = shapely_dict["FRAN_DATUM"]

            tags = shapely_dict.copy()
            self.way = shapely_dict["geometry"]

            tags.pop("RLID", None)
            tags.pop("TILL_DATUM", None)
            tags.pop("geometry", None)
            self.tags = {}
            self.tag_src = {}
            for k, v in tags.items():
                self.tags[k] = v
                self.tag_src[k] = ("", date)
        else:
            self.rlid = ""
            self.way = []
            self.tags = {}
            self.tag_src = {}
        self.way_id = -1

    def make_copy_new_way(self, way):
        copy = type(self)()
        copy.rlid = self.rlid
        copy.way_id = self.way_id
        copy.tags = self.tags.copy()
        copy.tag_src = self.tag_src.copy()
        copy.way = way
        return copy

    def __eq__(self, other):
        return id(self) == id(other)

    def __hash__(self):
        return hash(id(self))

    def __repr__(self):
        if isinstance(self.way, list):
            return "<rlid:%s %g..%g>" % (self.rlid, self.way[0].dist, self.way[-1].dist)
        return "<rlid:%s %s>" % (self.rlid, latlon_str(self.way))
