from __future__ import division, print_function

from math import atan2, sqrt

from fontPens.penTools import getCubicPoint
from fontTools.misc.bezierTools import calcCubicArcLength


def getPointsFromCurve(p, div=0.75):
    points = []
    length = calcCubicArcLength(p[0], p[1], p[2], p[3])
    t = 0
    step = div / length
    # print("Length:", d, "Steps:", step)
    while t < 1:
        points.append(getCubicPoint(t, p[0], p[1], p[2], p[3]))
        t += step
    points.append(p[3])
    return points


def angleBetweenPoints(p0, p1):
    return atan2(p1[1] - p0[1], p1[0] - p0[0])


def distanceBetweenPoints(p0, p1, doRound=False):
    # Calculate the distance between two points
    d = sqrt((p0[0] - p1[0]) ** 2 + (p0[1] - p1[1]) ** 2)
    if doRound:
        return int(round(d))
    else:
        return d


def halfPoint(p0, p1, doRound=False):
    x0, y0 = p0
    x1, y1 = p1
    xh = .5 * (x0 + x1)
    yh = .5 * (y0 + y1)
    if doRound:
        return int(round(xh)), int(round(yh))
    return xh, yh


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
        h = 2 * sqrt(s * (s - a) * (s - b) * (s - c)) / a
        return h


def optimizePointPath(p, dist=0.49):
    # print("Input number of points:", len(p))
    num_points = len(p)
    p0 = p[0]
    optimized = [p0]
    i = 0
    j = 1
    while i < num_points - 2:
        p1 = p[i + 1]
        p2 = p[i + 2]
        t = Triangle(p0, p2, p1)
        # h = t.height_a()
        # print(i, h)
        if t.height_a() > dist:
            optimized.extend([p1])
            p0 = p[i]
        else:
            pass
            # print("Skip:", i+1, p1)
        i += 1
        j += 1
        # if j > 13:
        #    break
    optimized.extend([p[-1]])
    # print("Optimized number of points:", len(optimized))
    return optimized
