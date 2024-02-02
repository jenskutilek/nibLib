from __future__ import annotations

from math import atan2, pi
from nibLib.typing import CCurve, TPoint
from typing import List, Sequence, Tuple


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
        if self.__currentPoint is None:
            raise ValueError

        t = self.transform.transformPoint(pt)

        A1, B1, C1, D1 = self.transformedRect(self.__currentPoint)
        A2, B2, C2, D2 = self.transformedRect(t)

        AB1 = half(A1, B1)
        # BC1 = half(B1, C1)
        CD1 = half(C1, D1)
        DA1 = half(D1, A1)

        AB2 = half(A2, B2)
        BC2 = half(B2, C2)
        CD2 = half(C2, D2)
        # DA2 = half(D2, A2)

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

    def _curveToOneNoExtrema(self, pt1, pt2, pt3):
        if self.__currentPoint is None:
            raise ValueError

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

        Q1 = rho1 / pi
        Q2 = rho2 / pi
        # print(f"       Q1: {Q1}, Q2: {Q2}")
        Q1 = normalize_quadrant(rho1 / pi)
        Q2 = normalize_quadrant(rho2 / pi)
        # print(f"    -> Q1: {Q1}, Q2: {Q2}")

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
        seq0 = ((B2,), (C2,), (Cc2, Cc1, C1), (A1,), (Ac1, Ac2, A2))
        seq1 = (
            (half(A1, D1),),
            (half(A1, B1),),
            (Bc1, Bc2, half(B2, C2)),
            (half(C2, D2),),
            (half(D2, A2),),
            (Dc2, Dc1, half(C1, D1)),
        )
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
