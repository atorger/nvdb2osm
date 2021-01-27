from pyproj import Transformer

sweref99_transformer = Transformer.from_crs("epsg:3006", "epsg:4326")

def latlon_str(xy):
    lat, lon = sweref99_transformer.transform(xy[1], xy[0])
    return "<lat:%s lon:%s>" % (lat, lon)
