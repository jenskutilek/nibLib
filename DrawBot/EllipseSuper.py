from __future__ import division
import cmath

#a = 300
#b = 200

#phi = radians(45)
#alpha = 30

#nib_angle = 5

Variable([
    dict(name="a", ui="Slider",
        args=dict(
            value=300,
            minValue=0,
            maxValue=500)),
    dict(name="b", ui="Slider",
        args=dict(
            value=200,
            minValue=0,
            maxValue=500)),
    dict(name="n", ui="Slider",
        args=dict(
            value=2.5,
            minValue=2,
            maxValue=10)),
    dict(name="phi", ui="Slider",
        args=dict(
            value=45,
            minValue=0,
            maxValue=360)),
    dict(name="alpha", ui="Slider",
        args=dict(
            value=45,
            minValue=0,
            maxValue=360)),
    dict(name="nib_angle", ui="Slider",
        args=dict(
            value=0,
            minValue=-90,
            maxValue=90)),
    ], globals())

alpha = radians(alpha)
nib_angle = radians(nib_angle)
phi = radians(phi)


# Path optimization tools

def distanceBetweenPoints(p0, p1, doRound=False):
    # Calculate the distance between two points
    d = sqrt((p0[0] - p1[0]) ** 2 + (p0[1] - p1[1]) ** 2)
    if doRound:
        return int(round(d))
    else:
        return d


class Triangle(object):
    def __init__(self, A, B, C):
        self.A = A
        self.B = B
        self.C = C
    
    def sides(self):
        self.a = distanceBetweenPoints(self.B, self.C)
        self.b = distanceBetweenPoints(self.A, self.C)
        self.c = distanceBetweenPoints(self.A, self.B)
        return self.a, self.b, self.c
    
    def height_a(self):
        a, b, c = self.sides()
        s = (a + b + c) / 2
        h = 2 * sqrt(s * (s-a) * (s-b) * (s-c)) / a
        return h


def optimizePointPath(p, dist=0.49):
    print "Input number of points:", len(p)
    num_points = len(p)
    p0 = p[0]
    optimized = [p0]
    i = 0
    j = 1
    while i < num_points -2:
        p1 = p[i+1]
        p2 = p[i+2]
        t = Triangle(p0, p2, p1)
        h = t.height_a()
        #print i, h
        if t.height_a() > dist:
            optimized.extend([p1])
            p0 = p[i]
        else:
            pass
            #print "Skip:", i+1, p1
        i += 1
        j += 1
        #if j > 13:
        #    break
    optimized.extend([p[-1]])
    print "Optimized number of points:", len(optimized)
    return optimized


def get_superellipse_points(a, b, n, alpha=0, steps=100):
    points = []
    for i in range(0, steps + 1):
        t = i * 0.5 * pi / steps
        points.append((
            a * cos(t) ** (2 / n) * cos(alpha) - b * sin(t) ** (2 / n) * sin(alpha),
            a * cos(t) ** (2 / n) * sin(alpha) + b * sin(t) ** (2 / n) * cos(alpha),
        ))
    try:
        points = optimizePointPath(points, 1)
    except:
        print "oops"
        pass
    points.extend([(-p[0], p[1]) for p in reversed(points)])
    points.extend([(-p[0], -p[1]) for p in reversed(points)])
    return points
    

def superellipse(a, b, n, alpha, steps=100):
    points = get_superellipse_points(a, b, n, 0, steps)
    save()
    rotate(degrees(alpha))
    newPath()
    moveTo(points[0])
    for p in points[1:]:
        lineTo(p)
    closePath()
    drawPath()
    restore()

#def _get_point_on_ellipse_at_tangent_angle(a, b, alpha):
#    
#    phi = atan2(
#        - b,
#        a * tan(alpha)
#    )
#    
#    x = a * cos(phi)
#    y = b * sin(phi)
#    
#    return x, y   


def _get_point_on_superellipse_at_tangent_angle(a, b, n, alpha):
    
    print "a =", a
    print "b =", b
    
    exp = 1 / (2 - 2 / n) + 0j
    print "Exponent:", exp
    
    
    factor1 = (-b / a) ** -exp
    factor2 = cmath.tan(alpha) ** exp
    print "factor1 =", factor1
    print "factor2 =", factor2
    phi = atan2(
        1,
        (factor1 * factor2).real,
    )
    
    print "phi =", degrees(phi)
    
    
    return _get_point_on_superellipse_at_angle_from_center(a, b, n, phi)


def _get_point_on_superellipse_at_angle_from_center(a, b, n, phi):
    
    x = a * cos(phi) ** (2 / n + 0j)
    y = b * sin(phi) ** (2 / n + 0j)
    
    print x, y
    
    return x.real, y.real


def draw_arrowhead(size=10, x=0, y=0):
    line((x-size, y+size), (x, y))
    line((x, y), (x-size, y-size))

def draw_cross(size=10, x=0, y=0, phi=45):
    save()
    rotate(phi)
    line((x-size, y+size), (x+size, y-size))
    line((x+size, y+size), (x-size, y-size))
    restore()

print "Superellipse with n = %0.2f" % n

newDrawing()
size(1000, 1000)
fill(None)
stroke(0)
strokeWidth(0.25)

translate(500, 500)
save()
rotate(degrees(nib_angle))
stroke(1, 0, 0)
line((-500, 0), (500, 0))
line((0, 500), (0, -500))
stroke(1, 1, 0)
oval(-a, -b, 2*a, 2*b)
rotate(degrees(-nib_angle))
stroke(0)
strokeWidth(1)
superellipse(a, b, n, nib_angle)
restore()

save()
rotate(degrees(nib_angle))
stroke(0, 1, 0)
x, y = _get_point_on_superellipse_at_angle_from_center(a, b, n, phi)
line((0, 0), (x, y))
rect(x-1, y-1, 2, 2)
restore()

stroke(0, 0, 1)
x, y = _get_point_on_superellipse_at_tangent_angle(a, b, n, alpha - nib_angle)
print x, y
save()
stroke(0,1,0)
rotate(degrees(nib_angle))
line((0, 0), (x, y))
rect(x-1, y-1, 2, 2)
restore()
#print "Nib angle:", degrees(nib_angle)

# Calculate the un-transformed point coordinates
xnew = x * cos(nib_angle) - y * sin(nib_angle)
ynew = x * sin(nib_angle) + y * cos(nib_angle)
#print xnew, ynew

line((0, 0), (xnew, ynew))
rect(xnew-1, ynew-1, 2, 2)
translate(xnew, ynew)

save()
rotate(degrees(alpha))

line((-300, 0), (300, 0))
draw_cross(5, phi = degrees(-alpha))
draw_arrowhead(5, -300)
draw_arrowhead(5, 300)

# draw the center angle arc

rotate(degrees(-alpha))
stroke(1, 0, 1, 0.2)
strokeWidth(1)
line((0, 0), (100, 0))

newPath()
arc((0, 0), 80, 0, degrees(alpha), False)
drawPath()
strokeWidth(0)
fill(1, 0, 1, 0.5)
fontSize(12)
font("Times-Italic")
text("𝛼 = %0.1f°" % degrees(alpha), (20, 10))

restore()