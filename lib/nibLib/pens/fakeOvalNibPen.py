from __future__ import division, print_function

from math import atan2, pi


try:
    from mojo.drawingTools import *
except ImportError:
    try:
        from GlyphsApp.drawingTools import *
    except ImportError:
        pass


from AppKit import NSBezierPath, NSColor


from nibLib.geometry import halfPoint as half
from nibLib.pens.rectNibPen import RectNibPen
from nibLib.pens.bezier import normalize_quadrant, split_at_extrema


class FakeOvalNibPen(RectNibPen):
    def addPath(self, path=[]):
        """
        Add a path to the nib path.
        """
        if path:
            path = [
                self.transform_reverse.transformPoints(pts) for pts in path
            ]
            if self.trace:
                self.path.append(path)
            else:
                self.drawPath(path)

    def drawPath(self, path=[]):
        """
        Draw the points from path to a NSBezierPath.
        """
        subpath = NSBezierPath.alloc().init()
        subpath.moveToPoint_(path[0][0])
        for p in path[1:]:
            if len(p) == 3:
                # curve
                A, B, C = p
                subpath.curveToPoint_controlPoint1_controlPoint2_(C, A, B)
            else:
                subpath.lineToPoint_(p[0])

        subpath.closePath()
        NSColor.colorWithCalibratedRed_green_blue_alpha_(
            0, 0, 1, self.alpha
        ).set()
        subpath.stroke()

    def transformPoint(self, pt, d=1):
        return (
            pt[0] + self.a * d,
            pt[1] + self.b,
        )

    def transformPointHeight(self, pt, d=1):
        return (
            pt[0] + self.a * d,
            pt[1] - self.b,
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
        t = self.transform.transformPoint(pt)
        self.__currentPoint = t
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
        t = self.transform.transformPoint(pt)

        A1, B1, C1, D1 = self.transformedRect(self.__currentPoint)
        A2, B2, C2, D2 = self.transformedRect(t)

        AB1 = half(A1, B1)
        BC1 = half(B1, C1)
        CD1 = half(C1, D1)
        DA1 = half(D1, A1)

        AB2 = half(A2, B2)
        BC2 = half(B2, C2)
        CD2 = half(C2, D2)
        DA2 = half(D2, A2)

        x1, y1 = self.__currentPoint
        x2, y2 = t

        # Angle between nib and path
        rho = atan2(y2 - y1, x2 - x1)

        path = None
        Q = rho / pi

        if Q == 0:
            path = ([AB1], [AB2], [BC2], [CD2], [CD1], [DA1])
        elif 0 < Q < 0.5:
            path = ([half(A1, B1)], (half(B1, C1),), (B2,), (C2,), (D2,), (D1,))

        elif 0.5 <= Q <= 1:
            path = ([A1], [B1], [C1], [C2], [D2], [A2])

        elif -1 <= Q < -0.5:
            path = ([A2], [B2], [B1], [C1], [D1], [D2])

        elif -0.5 <= Q < 0:
            path = ([AB2], [BC2], [CD2], [CD1], [DA1], [AB1])

        self.addPath(path)

        self.__currentPoint = t

    def _curveToOne(self, pt1, pt2, pt3):
        # Insert extrema at angle
        segments = split_at_extrema(
            self.__currentPoint, pt1, pt2, pt3, transform=self.transform
        )
        for segment in segments:
            pt0, pt1, pt2, pt3 = segment
            self._curveToOneNoExtrema(pt1, pt2, pt3)

    def _curveToOneNoExtrema(self, pt1, pt2, pt3):
        print("_curveToOneNoExtrema", pt1, pt2, pt3)

        A1, B1, C1, D1 = self.transformedRect(self.__currentPoint)

        # Control points
        Ac1, Bc1, Cc1, Dc1 = self.transformedRect(pt1)
        Ac2, Bc2, Cc2, Dc2 = self.transformedRect(pt2)

        # End points
        A2, B2, C2, D2 = self.transformedRect(pt3)

        # Angle at start of curve
        x0, y0 = self.__currentPoint
        x1, y1 = pt1
        rho1 = atan2(y1 - y0, x1 - x0)

        # Angle at end of curve
        x2, y2 = pt2
        x3, y3 = pt3

        rho2 = atan2(y3 - y2, x3 - x2)

        path = None

        Q1 = (rho1 / pi)
        Q2 = (rho2 / pi)
        print(f"       Q1: {Q1}, Q2: {Q2}")
        Q1 = normalize_quadrant(rho1 / pi)
        Q2 = normalize_quadrant(rho2 / pi)
        print(f"    -> Q1: {Q1}, Q2: {Q2}")

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
        seq0 = ((B2,), (C2,), (Cc2, Cc1, C1,), (A1,), (Ac1, Ac2, A2))
        seq1 = ((half(A1, D1),), (half(A1, B1),), (Bc1, Bc2, half(B2, C2)), (half(C2, D2),), (half(D2, A2),), (Dc2, Dc1, half(C1, D1),))
        seq2 = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
        seq3 = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
        if Q1 == 0:
            if Q2 == 0:
                path = seq0
            elif 0 < Q2 < 0.5:
                path = seq1
            elif 0.5 <= Q2 <= 1:
                path = seq1
            elif -0.5 <= Q2 < 0:
                path = seq0

        elif 0 < Q1 < 0.5:
            if Q2 == 0:
                path = seq1
            elif 0 <= Q2 < 0.5:
                path = seq1
            elif 0.5 <= Q2 <= 1:
                path = seq1
            elif -1 < Q2 < -0.5:
                pass
            elif -0.5 <= Q2 < 0:
                path = seq0

        elif Q1 == 0.5:
            if 0 <= Q2 < 0.5:
                path = seq1
            elif Q2 == 0.5:
                path = seq1
            elif 0.5 <= Q2 <= 1:
                path = seq2
            elif Q2 == -1:
                path = seq2

        elif 0.5 < Q1 < 1:
            if 0 <= Q2 < 0.5:
                path = seq1
            elif 0.5 <= Q2 <= 1:
                path = seq2
            elif Q2 == -1:
                path = seq2
            elif -1 < Q2 < -0.5:
                path = seq3
            elif -0.5 <= Q2 < 0:
                path = seq3

        elif Q1 == 1:
            if 0 <= Q2 < 0.5:
                path = seq1
            elif Q2 == 0.5:
                path = seq2
            elif 0.5 < Q2 < 1:
                path = seq2
            elif Q2 == 1:
                path = seq2
            elif Q2 == -1:
                path = seq2
            elif -1 < Q2 < -0.5:
                path = seq3
            elif -0.5 <= Q2 < 0:
                path = seq3

        elif Q1 == -1:
            if 0 <= Q2 < 0.5:
                path = seq1
            elif Q2 == 0.5:
                path = seq2
            elif 0.5 < Q2 < 1:
                path = seq2
            elif Q2 == 1:
                path = seq2
            elif Q2 == -1:
                path = seq2
            elif -1 < Q2 < -0.5:
                path = seq3
            elif -0.5 <= Q2 < 0:
                path = seq3

        elif -1 < Q1 < -0.5:
            if 0 <= Q2 < 0.5:
                print("Crash")
            elif 0.5 <= Q2 <= 1:
                path = seq3
            elif Q2 == -1:
                path = seq3
            elif -1 < Q2 < -0.5:
                path = seq3
            elif -0.5 <= Q2 < 0:
                path = seq3

        elif Q1 == -0.5:
            if Q2 == -1:
                path = seq3
            elif -1 < Q2 < -0.5:
                path = seq3
            elif Q2 == -0.5:
                path = seq3
            elif -0.5 <= Q2 < 0:
                path = seq0
            elif Q2 == 0.0:
                path = seq0
            elif Q2 == 1:
                path = seq3

        elif -0.5 <= Q1 < 0:
            if 0 <= Q2 < 0.5:
                path = seq0
            elif 0.5 <= Q2 <= 1:
                path = seq3
            elif Q2 == -1:
                path = seq3
            elif -1 < Q2 < -0.5:
                path = seq3
            elif -0.5 <= Q2 < 0:
                path = seq0

        self.addPath(path)

        self.__currentPoint = pt3

    def _closePath(self):
        # Glyphs calls closePath though it is not really needed there ...?
        self._lineTo(self.contourStart)
        self.__currentPoint = None

    def _endPath(self):
        if self.__currentPoint:
            # A1, B1, C1, D1 = self.transformedRect(self.__currentPoint)
            # self.addPath(((A1,), (B1,), (C1,), (D1,)))
            self.__currentPoint = None
