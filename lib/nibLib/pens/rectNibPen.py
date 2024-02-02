from __future__ import annotations

from math import atan2, pi
from nibLib.pens.bezier import normalize_quadrant, split_at_extrema
from nibLib.pens.nibPen import NibPen
from nibLib.typing import TPoint
from typing import Tuple


class RectNibPen(NibPen):
    def transformPoint(self, pt: TPoint, d=1) -> TPoint:
        return (
            pt[0] + self.a * d,
            pt[1] + self.b,
        )

    def transformPointHeight(self, pt: TPoint, d=1) -> TPoint:
        return (
            pt[0] + self.a * d,
            pt[1] - self.b,
        )

    def transformedRect(self, P: TPoint) -> Tuple[TPoint, TPoint, TPoint, TPoint]:
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

    def _moveTo(self, pt: TPoint) -> None:
        t = self.transform.transformPoint(pt)
        self._currentPoint = t
        self.contourStart = pt

    def _lineTo(self, pt: TPoint) -> None:
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
        if self._currentPoint is None:
            raise ValueError

        t = self.transform.transformPoint(pt)

        A1, B1, C1, D1 = self.transformedRect(self._currentPoint)
        A2, B2, C2, D2 = self.transformedRect(t)

        x1, y1 = self._currentPoint
        x2, y2 = t

        # Angle between nib and path
        rho = atan2(y2 - y1, x2 - x1)

        path = None
        Q = rho / pi

        if 0 <= Q < 0.5:
            path = ((A1,), (B1,), (B2,), (C2,), (D2,), (D1,))

        elif 0.5 <= Q <= 1:
            path = ((A1,), (B1,), (C1,), (C2,), (D2,), (A2,))

        elif -1 <= Q < -0.5:
            path = ((A2,), (B2,), (B1,), (C1,), (D1,), (D2,))

        elif -0.5 <= Q < 0:
            path = ((A2,), (B2,), (C2,), (C1,), (D1,), (A1,))

        self.addPath(path)

        self._currentPoint = t

    def _curveToOne(self, pt1, pt2, pt3):
        if self._currentPoint is None:
            raise ValueError

        # Insert extrema at angle
        segments = split_at_extrema(
            self._currentPoint, pt1, pt2, pt3, transform=self.transform
        )
        for segment in segments:
            pt0, pt1, pt2, pt3 = segment
            self._curveToOneNoExtrema(pt1, pt2, pt3)

    def _curveToOneNoExtrema(self, pt1, pt2, pt3):
        if self._currentPoint is None:
            raise ValueError

        A1, B1, C1, D1 = self.transformedRect(self._currentPoint)

        # Control points
        Ac1, Bc1, Cc1, Dc1 = self.transformedRect(pt1)
        Ac2, Bc2, Cc2, Dc2 = self.transformedRect(pt2)

        # End points
        A2, B2, C2, D2 = self.transformedRect(pt3)

        # Angle at start of curve
        x0, y0 = self._currentPoint
        x1, y1 = pt1
        rho1 = atan2(y1 - y0, x1 - x0)

        # Angle at end of curve
        x2, y2 = pt2
        x3, y3 = pt3

        rho2 = atan2(y3 - y2, x3 - x2)

        path = None

        Q1 = normalize_quadrant(rho1 / pi)
        Q2 = normalize_quadrant(rho2 / pi)

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
        if Q1 == 0:
            if Q2 == 0:
                path = ((B2,), (C2,), (Cc2, Cc1, C1), (D1,), (A1,), (Ac1, Ac2, A2))
            elif 0 < Q2 < 0.5:
                path = ((A1,), (B1,), (Bc1, Bc2, B2), (C2,), (D2,), (Dc2, Dc1, D1))
            elif 0.5 <= Q2 <= 1:
                path = ((A1,), (B1,), (Bc1, Bc2, B2), (C2,), (D2,), (Dc2, Dc1, D1))
            elif -0.5 <= Q2 < 0:
                path = ((B2,), (C2,), (Cc2, Cc1, C1), (D1,), (A1,), (Ac1, Ac2, A2))

        elif 0 < Q1 < 0.5:
            if Q2 == 0:
                path = ((A1,), (B1,), (Bc1, Bc2, B2), (C2,), (D2,), (Dc2, Dc1, D1))
            elif 0 <= Q2 < 0.5:
                path = ((A1,), (B1,), (Bc1, Bc2, B2), (C2,), (D2,), (Dc2, Dc1, D1))
            elif 0.5 <= Q2 <= 1:
                path = ((A1,), (B1,), (Bc1, Bc2, B2), (C2,), (D2,), (Dc2, Dc1, D1))
            elif -1 < Q2 < -0.5:
                pass
            elif -0.5 <= Q2 < 0:
                path = ((B2,), (C2,), (Cc2, Cc1, C1), (D1,), (A1,), (Ac1, Ac2, A2))

        elif Q1 == 0.5:
            if 0 <= Q2 < 0.5:
                path = ((A1,), (B1,), (Bc1, Bc2, B2), (C2,), (D2,), (Dc2, Dc1, D1))
            elif Q2 == 0.5:
                path = ((A1,), (B1,), (Bc1, Bc2, B2), (C2,), (D2,), (Dc2, Dc1, D1))
            elif 0.5 <= Q2 <= 1:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif Q2 == -1:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))

        elif 0.5 < Q1 < 1:
            if 0 <= Q2 < 0.5:
                path = ((A1,), (B1,), (Bc1, Bc2, B2), (C2,), (D2,), (Dc2, Dc1, D1))
            elif 0.5 <= Q2 <= 1:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif Q2 == -1:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif -1 < Q2 < -0.5:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif -0.5 <= Q2 < 0:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))

        elif Q1 == 1:
            if 0 <= Q2 < 0.5:
                path = ((A1,), (B1,), (Bc1, Bc2, B2), (C2,), (D2,), (Dc2, Dc1, D1))
            elif Q2 == 0.5:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif 0.5 < Q2 < 1:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif Q2 == 1:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif Q2 == -1:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif -1 < Q2 < -0.5:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif -0.5 <= Q2 < 0:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))

        elif Q1 == -1:
            if 0 <= Q2 < 0.5:
                path = ((A1,), (B1,), (Bc1, Bc2, B2), (C2,), (D2,), (Dc2, Dc1, D1))
            elif Q2 == 0.5:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif 0.5 < Q2 < 1:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif Q2 == 1:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif Q2 == -1:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif -1 < Q2 < -0.5:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif -0.5 <= Q2 < 0:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))

        elif -1 < Q1 < -0.5:
            if 0 <= Q2 < 0.5:
                print("Crash")
            elif 0.5 <= Q2 <= 1:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif Q2 == -1:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif -1 < Q2 < -0.5:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif -0.5 <= Q2 < 0:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))

        elif Q1 == -0.5:
            if Q2 == -1:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif -1 < Q2 < -0.5:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif Q2 == -0.5:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif -0.5 <= Q2 < 0:
                path = ((B2,), (C2,), (Cc2, Cc1, C1), (D1,), (A1,), (Ac1, Ac2, A2))
            elif Q2 == 0.0:
                path = ((B2,), (C2,), (Cc2, Cc1, C1), (D1,), (A1,), (Ac1, Ac2, A2))
            elif Q2 == 1:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))

        elif -0.5 <= Q1 < 0:
            if 0 <= Q2 < 0.5:
                path = ((B2,), (C2,), (Cc2, Cc1, C1), (D1,), (A1,), (Ac1, Ac2, A2))
            elif 0.5 <= Q2 <= 1:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif Q2 == -1:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif -1 < Q2 < -0.5:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif -0.5 <= Q2 < 0:
                path = ((B2,), (C2,), (Cc2, Cc1, C1), (D1,), (A1,), (Ac1, Ac2, A2))

        self.addPath(path)

        self._currentPoint = pt3

    def _closePath(self):
        # Glyphs calls closePath though it is not really needed there ...?
        self._lineTo(self.contourStart)
        self._currentPoint = None

    def _endPath(self):
        if self._currentPoint:
            # A1, B1, C1, D1 = self.transformedRect(self._currentPoint)
            # self.addPath(((A1,), (B1,), (C1,), (D1,)))
            pass
        self._currentPoint = None
