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
    dict(name="alpha", ui="Slider",
        args=dict(
            value=45,
            minValue=0,
            maxValue=180)),
    dict(name="phi", ui="Slider",
        args=dict(
            value=45,
            minValue=0,
            maxValue=180)),
    dict(name="nib_angle", ui="Slider",
        args=dict(
            value=30,
            minValue=-90,
            maxValue=90)),
    ], globals())

alpha = radians(alpha)
phi = radians(phi)
nib_angle = radians(nib_angle)

def _get_point_on_ellipse_at_tangent_angle(a, b, alpha):
    
    print "Tangent angle:     %0.2f°" % degrees(alpha)
    
    t = atan2(- b , (a * tan(alpha)))
    t = atan(-b /(a * tan(alpha)))
    print "Parameter t: %0.2f" % (t + nib_angle)
    
    return _get_point_on_ellipse_at_t(a, b, t)


def _get_point_on_ellipse_at_t(a, b, t):
    
    # t is not the angle, it is just a parameter
    
    x = a * cos(t)
    y = b * sin(t)
    
    return x, y


def _get_point_on_ellipse_at_angle_from_center(a, b, phi):
    
    # This time, phi is the real center angle
    
    div = sqrt(a**2 * tan(phi) ** 2 / b ** 2 + 1)
    
    x = a / div
    y = a * tan(phi) / div
    
    return x, y


def draw_arrowhead(size=10, x=0, y=0):
    line((x-size, y+size), (x, y))
    line((x, y), (x-size, y-size))

def draw_cross(size=10, x=0, y=0, phi=45):
    save()
    rotate(phi)
    line((x-size, y+size), (x+size, y-size))
    line((x+size, y+size), (x-size, y-size))
    restore()


newDrawing()
size(1000, 1000)
fill(None)
stroke(0)
strokeWidth(0.25)

translate(500, 500)
save()
rotate(degrees(nib_angle))
line((-500, 0), (500, 0))
line((0, 500), (0, -500))
oval(-a, -b, 2*a, 2*b)
restore()

x, y = _get_point_on_ellipse_at_angle_from_center(a, b, phi)
print "Center angle: %0.2f°" % degrees(phi)
save()
stroke(1, 0, 0)
rotate(degrees(nib_angle))
line((0, 0), (x, y))
rect(x-1, y-1, 2, 2)
restore()

stroke(0, 0, 1)
x, y = _get_point_on_ellipse_at_tangent_angle(a, b, alpha - nib_angle)
print "Point on ellipse: %0.2f | %0.2f (ellipse reference system)" % (x, y)
save()
stroke(0,1,0)
rotate(degrees(nib_angle))
line((0, 0), (x, y))
rect(x-1, y-1, 2, 2)
restore()
print "Nib angle: %0.2f°" % degrees(nib_angle)

# Calculate the un-transformed point coordinates
xnew = x * cos(nib_angle) - y * sin(nib_angle)
ynew = x * sin(nib_angle) + y * cos(nib_angle)
print "Point on ellipse: %0.2f | %0.2f" % (xnew, ynew)

line((0, 0), (xnew, ynew))
rect(xnew-1, ynew-1, 2, 2)
translate(xnew, ynew)

save()
rotate(degrees(alpha))

line((-200, 0), (200, 0))
draw_cross(5, phi = degrees(-alpha))
draw_arrowhead(5, -200)
draw_arrowhead(5, 200)

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
