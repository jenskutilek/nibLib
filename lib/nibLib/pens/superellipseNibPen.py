from __future__ import annotations

import operator

from fontTools.misc.transform import Transform
from math import cos, degrees, pi, sin
from nibLib.typing import TPoint
from nibLib.geometry import (
    angleBetweenPoints,
    getPathFromPoints,
    getPointsFromCurve,
    optimizePointPath,
)
from nibLib.pens.ovalNibPen import OvalNibPen


# Settings for curve trace
TRACE_ERROR = 0.5
TRACE_CORNER_TOLERANCE = 1.0
TRACE_MAXIMUM_SEGMENTS = 1000


DEBUG_CENTER_POINTS = False
DEBUG_CURVE_POINTS = False


class SuperellipseNibPen(OvalNibPen):
    def setup_nib(self) -> None:
        steps = 100
        points = []
        # Build a quarter of the superellipse with the requested number of steps
        for i in range(0, steps + 1):
            t = i * 0.5 * pi / steps
            points.append(
                (
                    self.a * cos(t) ** (2 / self.nib_superness),
                    self.b * sin(t) ** (2 / self.nib_superness),
                )
            )
        try:
            points = optimizePointPath(points, 0.02)
        except:
            print("Error optimizing point path.")
            pass

        # Just add the remaining three quarters by transposing the existing points
        points.extend([(-x, y) for x, y in reversed(points)])
        points.extend([(x, -y) for x, y in reversed(points)])

        self.nib_face_path = points
        self.nib_face_path_transformed = points.copy()
        self.nib_drawing_path = getPathFromPoints(points)
        self.cache_angle = None

    def _get_rotated_point(self, pt: TPoint, phi: float) -> TPoint:
        x, y = pt
        cp = cos(phi)
        sp = sin(phi)
        x1 = x * cp - y * sp
        y1 = x * sp + y * cp

        return x1, y1

    def transform_nib_path(self, alpha: float) -> None:
        t = Transform().rotate(-alpha)
        self.nib_face_path_transformed = t.transformPoints(self.nib_face_path)
        self.cache_angle = alpha

    def _get_tangent_point(self, alpha: float) -> TPoint:

        # Calculate the point on the superellipse
        # at the given tangent angle alpha.

        # For now, we do this the pedestrian way, until I can figure out
        # how to calculate the tangent point directly.

        if self.cache_angle != alpha:
            self.transform_nib_path(alpha)

        x, y = max(self.nib_face_path_transformed, key=operator.itemgetter(1))
        x, y = Transform().rotate(alpha).transformPoint((x, y))  # .rotate(-self.angle)
        return x, y

    def _moveTo(self, pt: TPoint) -> None:
        t = self.transform.transformPoint(pt)
        self._currentPoint = t
        self.contourStart = pt
        self._draw_nib_face(pt)

    def _lineTo(self, pt: TPoint) -> None:
        if self._currentPoint is None:
            raise ValueError

        cx, cy = self._currentPoint

        t = self.transform.transformPoint(pt)
        tx, ty = t

        # angle from the previous to the current point
        phi = angleBetweenPoints(self._currentPoint, t)
        # print(u"%0.2f°: %s -> %s" % (degrees(phi), self._currentPoint, pt))

        x, y = self._get_tangent_point(phi)

        p0 = (cx + x, cy + y)
        p1 = (tx + x, ty + y)
        p2 = (tx - x, ty - y)
        p3 = (cx - x, cy - y)

        self.addPath([[p0], [p3], [p2], [p1]])
        self._draw_nib_face(pt)

        self._currentPoint = t

    def _curveToOne(self, pt1: TPoint, pt2: TPoint, pt3: TPoint) -> None:
        if self._currentPoint is None:
            raise ValueError

        # if not self.trace and DEBUG_CENTER_POINTS or DEBUG_CURVE_POINTS:
        #     save()

        t1 = self.transform.transformPoint(pt1)
        t2 = self.transform.transformPoint(pt2)
        t3 = self.transform.transformPoint(pt3)

        # Break curve into line segments
        points = getPointsFromCurve((self._currentPoint, t1, t2, t3), 5)

        # Draw points of center line
        # if DEBUG_CENTER_POINTS:
        #     stroke(None)
        #     strokeWidth(0)
        #     fill(0, 0, 0, self.alpha)
        #     for p in points:
        #         x, y = self.transform_reverse.transformPoint(p)
        #         rect(x - 1, y - 1, 2, 2)

        # Calculate angles between points

        # The first angle is that of the curve start point to bcp1
        angles = [angleBetweenPoints(self._currentPoint, t1)]

        for i in range(1, len(points)):
            phi = angleBetweenPoints(points[i - 1], points[i])
            angles.append(phi)

        # The last angle is that of bcp2 point to the curve end point
        angles.append(angleBetweenPoints(t2, t3))

        # Find points on ellipse for each angle
        inner = []
        outer = []

        # stroke(None)
        for i, p in enumerate(points):
            x, y = self._get_tangent_point(angles[i])

            pp = self._get_rotated_point((p[0] + x, p[1] + y), self.angle)
            outer.append(pp)

            if not self.trace and DEBUG_CURVE_POINTS:
                # Draw outer points in red
                fill(1, 0, 0, self.alpha)
                pr = self.transform_reverse.transformPoint((p[0] + x, p[1] + y))
                rect(pr[0] - 1, pr[1] - 1, 2, 2)

            pp = self._get_rotated_point((p[0] - x, p[1] - y), self.angle)
            inner.append(pp)
            if not self.trace and DEBUG_CURVE_POINTS:
                # Draw inner points in green
                fill(0, 0.8, 0, self.alpha)
                pr = self.transform_reverse.transformPoint((p[0] - x, p[1] - y))
                rect(pr[0] - 1, pr[1] - 1, 2, 2)

        if inner and outer:
            if self.trace:
                outer.reverse()
                outer = getPathFromPoints(outer)
                inner = getPathFromPoints(inner)
                self.path.append(outer + inner)
            else:
                inner = optimizePointPath(inner, 0.3)
                outer = optimizePointPath(outer, 0.3)
                outer.reverse()
                optimized = optimizePointPath(outer + inner, 1)
                self.addPath([[self.transform.transformPoint(o)] for o in optimized])
            self._draw_nib_face(pt3)

        self._currentPoint = t3
        # if not self.trace and DEBUG_CENTER_POINTS or DEBUG_CURVE_POINTS:
        #     restore()

    def _closePath(self) -> None:
        self.lineTo(self.contourStart)
        self._currentPoint = None

    def _endPath(self) -> None:
        self._currentPoint = None

    def _draw_nib_face(self, pt: TPoint) -> None:
        x, y = pt
        nib = []
        t = Transform().translate(x, y).rotate(self.angle)
        for seg in self.nib_drawing_path:
            seg_path = []
            for p in seg:
                seg_path.append(t.transformPoint(p))
            nib.append(seg_path)
        self.addPathRaw(nib)
