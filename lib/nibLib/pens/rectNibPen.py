from __future__ import division, print_function

from math import atan2, cos, pi, sin

try:
    from mojo.drawingTools import *
except ImportError:
    from GlyphsApp.drawingTools import *

from AppKit import NSBezierPath, NSColor


from nibLib.pens.nibPen import NibPen


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
        subpath.moveTo_(path[0])
        for p in path[1:]:
            subpath.lineTo_(p)
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
        self.__currentPoint = pt3
        return

        A1, B1, C1, D1 = self.transformedRect(self.__currentPoint)

        # Control points
        Ac1, Bc1, Cc1, Dc1 = self.transformedRect(pt1)
        Ac2, Bc2, Cc2, Dc2 = self.transformedRect(pt2)

        # End points
        A2, B2, C2, D2 = self.transformedRect(pt3)

        # Angle at start of curve
        x0, y0 = self.__currentPoint
        x1, y1 = pt1
        rho = self.angle - atan2(y1 - y0, x1 - x0)
        print(rho)

        # Angle at end of curve
        x2, y2 = pt2
        x3, y3 = pt3
        rho1 = self.angle - atan2(y3 - y2, x3 - x2)
        print(rho1)

        path = None

        pi_05 = 0.5 * pi
        pi_15 = 1.5 * pi

        if rho == 0:
            path = (A1, B2, C2, D1)
            #elif 0 > rho > -pi_05 or rho > pi_15:
            #path = (A1, B1, B2, C2, D2, D1)
        elif rho == -pi_05 or rho == pi_15:
            path = (A1, B1, B2, A2)
        elif -pi_05 > rho > -pi or pi_15 > rho > pi:
            path = (A1, B1, C1, C2, D2, A2)
        elif rho == -pi or rho == pi:
            path = (A2, B1, C1, D2)
        elif pi > rho > pi_05 or -pi > rho > -pi_15:
            path = (A2, B2, B1, C1, D1, D2)
        elif rho == pi_05 or rho == -pi_15:
            path = (A2, B2, C1, D1)
        elif pi_05 > rho > 0 or rho < -pi_15:
            path = (A2, B2, C2, (Cc2, Cc1, C1), D1, A1)
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
