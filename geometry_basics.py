import math

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.node_id = -1
        self.dist = -1
    def __len__(self):
        return 2
    def __getitem__(self, i):
        if i == 0:
            return self.x
        return self.y
    def __eq__(self, other):
        return isinstance(other, Point) and self.x == other.x and self.y == other.y
    def __hash__(self):
        return hash((self.x, self.y))
    def __repr__(self):
        if self.dist >= 0:
            return "<x:%s y:%s dist:%g>" % (self.x, self.y, self.dist)
        return "<x:%s y:%s>" % (self.x, self.y)

def dist2d(p1, p2):
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    return math.sqrt(dx * dx + dy * dy)

def dist2dsq(p1, p2):
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    return dx * dx + dy * dy

def snap_to_line(point, line_p1, line_p2):
    dx = line_p2.x - line_p1.x
    dy = line_p2.y - line_p1.y
    l2 = dx * dx + dy * dy
    if l2 == 0: # line is a point
        return None

    t = ((point.x - line_p1.x) * dx + (point.y - line_p1.y) * dy) / l2
    if t < 0 or t > 1:
        return None
    lp = Point(line_p1.x + t * dx, line_p1.y + t * dy)
    return lp

# Check if lines cross.
#
# Lines that lie exactly on top of each other do not cross, so if you need to check if a line
# touches the other you need an additional check.
def lines_intersect(n1, n2, p1, p2):
    Nx1 = n1.x
    Ny1 = n1.y
    Nx2 = n2.x
    Ny2 = n2.y
    Px1 = p1.x
    Py1 = p1.y
    Px2 = p2.x
    Py2 = p2.y
    denom = ((Py2 - Py1) * (Nx2 - Nx1)) - ((Px2 - Px1) * (Ny2 - Ny1))
    if denom == 0:
        return False
    a = Ny1 - Py1
    b = Nx1 - Px1
    num1 = ((Px2 - Px1) * a) - ((Py2 - Py1) * b)
    num2 = ((Nx2 - Nx1) * a) - ((Ny2 - Ny1) * b)
    a = num1 / denom
    b = num2 / denom
    if 0 < a < 1 and 0 < b < 1:
        #return Point(Nx1 + (a * (Nx2 - Nx1)), Ny1 + (a * (Ny2 - Ny1)))
        return True
    return False

# will include tp equal to p1 or p2
def point_between_points(tp, p1, p2, tolerance):
    dxc = tp.x - p1.x
    dyc = tp.y - p1.y
    dxl = p2.x - p1.x
    dyl = p2.y - p1.y
    cross = abs(dxc * dyl - dyc * dxl)
    if cross > tolerance: # not zero
        return False, cross
    if abs(dxl) >= abs(dyl):
        if dxl > 0:
            return p1.x <= tp.x and tp.x <= p2.x, cross
        return p2.x <= tp.x and tp.x <= p1.x, cross
    if dyl > 0:
        return p1.y <= tp.y and tp.y <= p2.y, cross
    return p2.y <= tp.y and tp.y <= p1.y, cross

def rotate_90deg(np1, np2):
    p1 = Point(np1.x, np1.y)
    p2 = Point(np2.x, np2.y)

    xtemp = p1.x
    ytemp = p1.y
    p1.x = -ytemp
    p1.y = xtemp

    xtemp = p2.x
    ytemp = p2.y
    p2.x = -ytemp
    p2.y = xtemp

    return p1, p2

def calc_way_length(points):
    if not isinstance(points, list) or len(points) < 2:
        return 0, 0
    it = iter(points)
    prev = next(it)
    length = 0
    min_dist = dist2d(points[0], points[1])
    for p in it:
        dist = dist2d(prev, p)
        if dist < min_dist:
            min_dist = dist
        length += dist
        prev = p
    return length, min_dist
