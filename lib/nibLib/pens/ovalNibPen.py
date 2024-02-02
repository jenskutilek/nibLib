from __future__ import annotations

from math import atan2, cos, degrees, sin, tan
from nibLib.typing import TPoint


# from nibLib import DEBUG_CENTER_POINTS, DEBUG_CURVE_POINTS
from nibLib.geometry import (
    angleBetweenPoints,
    getPointsFromCurve,
    optimizePointPath,
)
from nibLib.pens.rectNibPen import RectNibPen


class OvalNibPen(RectNibPen):
    def _get_tangent_point(self, alpha: float) -> TPoint:
        """Return the point on the ellipse at the given angle alpha.

        Args:
            alpha (float): The angle in radians.

        Returns:
            TPoint: The tangent point.
        """

        # Calculate the point on the ellipse
        # at the given tangent angle alpha.
        # t not the angle from the ellipse center, but just a parameter.

        t = atan2(-self.b, (self.a * tan(alpha)))
        x = self.a * cos(t)
        y = self.b * sin(t)

        return x, y

    def _get_rotated_tangent_point(self, pt: TPoint) -> TPoint:
        x, y = pt
        x1 = x * cos(self.angle) - y * sin(self.angle)
        y1 = x * sin(self.angle) + y * cos(self.angle)

        return x1, y1

    def _draw_nib_face(self, pt: TPoint) -> None:
        return
        save()
        # fill(*self.path_fill)
        # strokeWidth(0)
        # stroke(None)
        translate(pt[0], pt[1])
        rotate(degrees(self.angle))
        oval(-self.a, -self.b, self.width, self.height)
        restore()

    def _moveTo(self, pt: TPoint) -> None:
        self._currentPoint = pt
        self.contourStart = pt
        if not self.trace:
            self._draw_nib_face(pt)

    def _lineTo(self, pt: TPoint) -> None:
        if self._currentPoint is None:
            raise ValueError

        # angle from the previous to the current point
        phi = angleBetweenPoints(self._currentPoint, pt)
        # print(u"%0.2f°: %s -> %s" % (degrees(phi), self._currentPoint, pt))
        pt0 = self._get_tangent_point(phi - self.angle)
        x, y = self._get_rotated_tangent_point(pt0)
        px, py = pt
        cx, cy = self._currentPoint

        self.addPath(
            [
                ((cx + x, cy + y),),  # move
                ((px + x, py + y),),  # line
                ((px - x, py - y),),  # line
                ((cx - x, cy - y),),  # line
            ]
        )

        if not self.trace:
            self._draw_nib_face(pt)

        self._currentPoint = pt

    def _curveToOne(self, pt1: TPoint, pt2: TPoint, pt3: TPoint) -> None:
        if self._currentPoint is None:
            raise ValueError

        # Break curve into line segments
        points = getPointsFromCurve((self._currentPoint, pt1, pt2, pt3), 5)

        # Draw points of center line
        # if DEBUG_CENTER_POINTS:
        #     save()
        #     stroke(None)
        #     strokeWidth(0)
        #     fill(0, 0, 0, self.alpha)
        #     for x, y in points:
        #         rect(x - 1, y - 1, 2, 2)
        #     restore()

        # Calculate angles between points

        # The first angle is that of the curve start point to bcp1
        angles = [angleBetweenPoints(self._currentPoint, pt1)]

        for i in range(1, len(points)):
            phi = angleBetweenPoints(points[i - 1], points[i])
            angles.append(phi)

        # The last angle is that of bcp2 point to the curve end point
        angles.append(angleBetweenPoints(pt2, pt3))

        # Find points on ellipse for each angle
        inner = []
        outer = []

        # stroke(None)

        for i, p in enumerate(points):
            pt0 = self._get_tangent_point(angles[i] - self.angle)

            x, y = self._get_rotated_tangent_point(pt0)
            outer.append((p[0] + x, p[1] + y))
            # if DEBUG_CURVE_POINTS:
            #     # Draw outer points in red
            #     save()
            #     fill(1, 0, 0, self.alpha)
            #     rect(p[0] + x - 1, p[1] + y - 1, 2, 2)
            #     restore()

            x, y = self._get_rotated_tangent_point((-pt0[0], -pt0[1]))
            inner.append((p[0] + x, p[1] + y))
            # if DEBUG_CURVE_POINTS:
            #     # Draw inner points in green
            #     save()
            #     fill(0, 0.8, 0, self.alpha)
            #     rect(p[0] + x - 1, p[1] + y - 1, 2, 2)
            #     restore()

        if inner and outer:

            inner = optimizePointPath(inner, 0.3)
            outer = optimizePointPath(outer, 0.3)

            path = []
            path.append((outer[0],))  # move
            for p in outer[1:]:
                path.append((p,))  # line
            inner.reverse()
            for p in inner:
                path.append((p,))  # line
            path.append((outer[0],))  # line
            self.addPath(path)

            if not self.trace:
                self._draw_nib_face(pt3)

        self._currentPoint = pt3

    def _closePath(self) -> None:
        self._currentPoint = None

    def _endPath(self) -> None:
        self._currentPoint = None
