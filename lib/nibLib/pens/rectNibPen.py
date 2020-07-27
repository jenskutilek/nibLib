from __future__ import division, print_function

from math import atan2, cos, pi, sin
from fontTools.misc.bezierTools import (
    calcCubicParameters,
    solveQuadratic,
    splitCubicAtT,
    epsilon,
)
from fontTools.misc.transform import Transform

try:
    from mojo.drawingTools import *
except ImportError:
    from GlyphsApp.drawingTools import *

from AppKit import NSBezierPath, NSColor


from nibLib.pens.nibPen import NibPen


def split_at_extrema(pt1, pt2, pt3, pt4, transform=Transform()):
    # Transform the points for extrema calculation;
    # transform is expected to rotate the points by - nib angle.
    t1, t2, t3, t4 = transform.transformPoints([pt1, pt2, pt3, pt4])

    (ax, ay), (bx, by), c, d = calcCubicParameters(t1, t2, t3, t4)
    ax *= 3.0
    ay *= 3.0
    bx *= 2.0
    by *= 2.0

    # vertical
    roots = [t for t in solveQuadratic(ay, by, c[1]) if 0 < t < 1]

    # horizontal
    roots += [t for t in solveQuadratic(ax, bx, c[0]) if 0 < t < 1]

    # Use only unique roots and sort them
    roots = sorted(set(roots))

    # Split segment at roots (uses original points!)
    return splitCubicAtT(pt1, pt2, pt3, pt4, *roots)


class RectNibPen(NibPen):
    def addPath(self, path=[]):
        """
        Add a path to the nib path.
        """
        if path:
            if self.trace:
                self.path.append(path)
            else:
                self.drawPath(path)

    def drawPath(self, path=[]):
        """
        Draw the points from path to a NSBezierPath.
        """
        subpath = NSBezierPath.alloc().init()
        subpath.moveToPoint_(path[0])
        for p in path[1:]:
            if len(p) == 3:
                # curve
                A, B, C = p
                subpath.curveToPoint_controlPoint1_controlPoint2_(C, A, B)
            else:
                subpath.lineToPoint_(p)

        subpath.closePath()
        NSColor.colorWithCalibratedRed_green_blue_alpha_(
            0, 0, 1, self.alpha
        ).set()
        subpath.stroke()

    def transformPoint(self, pt, d=1):
        return (
            pt[0]
            + self.a * d * cos(self.angle)
            + self.b * cos(pi / 2 + self.angle),
            pt[1]
            + self.a * d * sin(self.angle)
            + self.b * sin(pi / 2 + self.angle),
        )

    def transformPointHeight(self, pt, d=1):
        return (
            pt[0]
            + self.a * d * cos(self.angle)
            - self.b * cos(pi / 2 + self.angle),
            pt[1]
            + self.a * d * sin(self.angle)
            - self.b * sin(pi / 2 + self.angle),
        )

    def transformedRect(self, P):
        """
        Transform a point to a rect describing the four points of the nib face.

          D-------------------------C
          |            P            |
          A-------------------------B
        """
        A = self.transformPointHeight(P, -1)
        B = self.transformPointHeight(P)
        C = self.transformPoint(P)
        D = self.transformPoint(P, -1)
        return A, B, C, D

    def _moveTo(self, pt):
        self.__currentPoint = pt
        self.contourStart = pt

    def _lineTo(self, pt):
        """
        Points of the nib face:

        D1                           C1     D2                           C2
          X-------------------------X         X-------------------------X
          |            X            | ------> |            X            |
          X-------------------------X         X-------------------------X
        A1                           B1     A2                           B2

        The points A2, B2, C2, D2 are the points of the nib face translated to
        the end of the current stroke.
        """

        A1, B1, C1, D1 = self.transformedRect(self.__currentPoint)
        A2, B2, C2, D2 = self.transformedRect(pt)

        x1, y1 = self.__currentPoint
        x2, y2 = pt

        # Relative angle between nib and path
        rho = self.angle - atan2(y2 - y1, x2 - x1)

        path = None
        Q = rho / pi

        if 0 >= Q > -0.5 or Q >= 1.5:
            path = (A1, B1, B2, C2, D2, D1)
        elif -0.5 >= Q > -1 or 1.5 >= Q > 1:
            path = (A1, B1, C1, C2, D2, A2)
        elif 1 >= Q > 0.5 or -1 >= Q > -1.5:
            path = (A2, B2, B1, C1, D1, D2)
        elif 0.5 >= Q > 0 or Q <= -1.5:
            path = (A2, B2, C2, C1, D1, A1)
        self.addPath(path)

        self.__currentPoint = pt

    def _curveToOne(self, pt1, pt2, pt3):
        # Insert extrema at angle
        segments = split_at_extrema(
            self.__currentPoint, pt1, pt2, pt3, transform=self.transform
        )
        for segment in segments:
            pt0, pt1, pt2, pt3 = segment
            self._curveToOneNoExtrema(pt1, pt2, pt3)

    def _curveToOneNoExtrema(self, pt1, pt2, pt3):

        A1, B1, C1, D1 = self.transformedRect(self.__currentPoint)

        # Control points
        Ac1, Bc1, Cc1, Dc1 = self.transformedRect(pt1)
        Ac2, Bc2, Cc2, Dc2 = self.transformedRect(pt2)

        # End points
        A2, B2, C2, D2 = self.transformedRect(pt3)

        # Angle at start of curve
        x0, y0 = self.__currentPoint
        x1, y1 = pt1
        rho1 = self.angle - atan2(y1 - y0, x1 - x0)

        # Angle at end of curve
        x2, y2 = pt2
        x3, y3 = pt3

        rho2 = self.angle - atan2(y3 - y2, x3 - x2)

        path = None
        Q1 = rho1 / pi
        Q2 = rho2 / pi
        print(Q1, Q2)

        if 0 >= Q1 > -0.5 or Q1 >= 1.5:
            print("Q1-1")

            if 0 >= Q2 > -0.5 or Q2 >= 1.5:
                path = (A1, B1, (Bc1, Bc2, B2), C2, D2, (Dc2, Dc1, D1))
            elif -0.5 >= Q2 > -1 or 1.5 > Q2 > 1:
                path = (A1, B1, (Bc1, Bc2, B2), C2, D2, (Dc2, Dc1, D1))
            elif 1 >= Q2 > 0.5 or -1 >= Q2 > -1.5:
                print("  Q2-3")
                # path = (A1, B1, (Bc1, Bc2, B2), A2, (Ac2, Ac1, A1))

        elif -0.5 >= Q1 > -1 or 1.5 > Q1 > 1:
            print("Q1-2")

            if 0 >= Q2 > -0.5 or Q2 >= 1.5:
                print("  Q2-1")
                path = (A1, B1, (Bc1, Bc2, B2), C2, D2, (Dc2, Dc1, D1))
            elif -0.5 >= Q2 > -1 or 1.5 >= Q2 > 1:
                path = (B1, C1, (Cc1, Cc2, C2), D2, A2, (Ac2, Ac1, A1))
            elif 1 >= Q2 > 0.5 or -1 >= Q2 > -1.5:
                print("  Q2-3")
                path = (B1, C1, (Cc1, Cc2, C2), D2, A2, (Ac2, Ac1, A1))
                # path = (B1, C1, D1, (Dc1, Dc2, D2), D2, A2, B2, (Bc2, Bc1, B1))
            elif 0.5 >= Q2 > 0 or Q2 <= -1.5:
                path = ()

        elif 1 >= Q1 > 0.5 or -1 >= Q1 > -1.5:
            print("Q1-3")

            if 0 >= Q2 > -0.5 or Q2 >= 1.5:
                print("  Q2-1")
                # OK
                path = (C1, D1, A1, (Ac1, Ac2, A2), B2, C2, (Cc2, Cc1, C1))
            elif -0.5 >= Q2 > -1 or 1.5 >= Q2 > 1:
                print("  Q2-2")
                path = (B1, C1, (Cc1, Cc2, C2), A2, (Ac2, Ac1, A1))
            elif 1 >= Q2 > 0.5 or -1 >= Q2 > -1.5:
                print("  Q2-3")
                path = (C1, D1, (Dc1, Dc2, D2), A2, B2, (Bc2, Bc1, B1))
            elif 0.5 >= Q2 > 0 or Q2 <= -1.5:
                print("  Q2-4")
                # OK
                path = (C1, D1, (Dc1, Dc2, D2), A2, B2, (Bc2, Bc1, B1))

        elif 0.5 >= Q1 > 0 or Q1 <= -1.5:
            print("Q1-4")

            if 0 >= Q2 > -0.5 or Q2 >= 1.5:
                print("  Q2-1")
                path = (D1, A1, (Ac1, Ac2, A2), B2, C2, (Cc2, Cc1, C1))
            elif -0.5 >= Q2 > -1 or 1.5 >= Q2 > 1:
                print("  Q2-2")
                path = (A1, B1, (Bc1, Bc2, B2), C2, D2, (Dc2, Dc1, D1))
            elif 1 >= Q2 > 0.5 or -1 >= Q2 > -1.5:
                print("  Q2-3")
                path = ()
            elif 0.5 >= Q2 > 0 or Q2 <= -1.5:
                print("  Q2-4")
                path = (D1, A1, (Ac1, Ac2, A2), B2, C2, (Cc2, Cc1, C1))
        self.addPath(path)

        self.__currentPoint = pt3

    def _closePath(self):
        # Glyphs calls closePath though it is not really needed there ...?
        self._lineTo(self.contourStart)
        self.__currentPoint = None

    def _endPath(self):
        if self.__currentPoint:
            A1, B1, C1, D1 = self.transformedRect(self.__currentPoint)
            self.addPath((A1, B1, C1, D1))
