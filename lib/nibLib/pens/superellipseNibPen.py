from __future__ import division, print_function

from math import cos, degrees, pi, sin
import operator

try:
    from mojo.drawingTools import *
except ImportError:
    from GlyphsApp.drawingTools import *

from fontTools.misc.transform import Transform

from beziers.path import BezierPath as SCBezierPath
from beziers.point import Point as SCPoint

from nibLib.geometry import (
    angleBetweenPoints,
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
    def setup_nib(self):
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
        points.extend([(-p[0], p[1]) for p in reversed(points)])
        points.extend([(p[0], -p[1]) for p in reversed(points)])

        self.nib_face_path = points
        self.nib_face_path_transformed = points.copy()
        self.cache_angle = None

    def _get_rotated_point(self, pt, phi):
        x, y = pt
        cp = cos(phi)
        sp = sin(phi)
        x1 = x * cp - y * sp
        y1 = x * sp + y * cp

        return x1, y1

    def transform_nib_path(self, alpha):
        t = Transform().rotate(-alpha)
        self.nib_face_path_transformed = t.transformPoints(self.nib_face_path)
        self.cache_angle = alpha

    def _get_tangent_point(self, alpha):

        # Calculate the point on the superellipse
        # at the given tangent angle alpha.

        # For now, we do this the pedestrian way, until I can figure out
        # how to calculate the tangent point directly.

        if self.cache_angle != alpha:
            self.transform_nib_path(alpha)

        x, y = max(self.nib_face_path_transformed, key=operator.itemgetter(1))
        x, y = Transform().rotate(alpha).transformPoint((x, y)) # .rotate(-self.angle)
        return x, y

    def _moveTo(self, pt):
        t = self.transform.transformPoint(pt)
        self.__currentPoint = t
        self.contourStart = pt
        self._draw_nib_face(pt)

    def _lineTo(self, pt):
        t = self.transform.transformPoint(pt)

        # angle from the previous to the current point
        phi = angleBetweenPoints(self.__currentPoint, t)
        # print(u"%0.2f°: %s -> %s" % (degrees(phi), self.__currentPoint, pt))

        x, y = self._get_tangent_point(phi)

        p0 = (self.__currentPoint[0] + x, self.__currentPoint[1] + y)
        p1 = (t[0] + x, t[1] + y)
        p2 = (t[0] - x, t[1] - y)
        p3 = (self.__currentPoint[0] - x, self.__currentPoint[1] - y)

        self.addPath([[p0], [p3], [p2], [p1]])
        self._draw_nib_face(pt)

        self.__currentPoint = t

    def _curveToOne(self, pt1, pt2, pt3):
        if not self.trace and DEBUG_CENTER_POINTS or DEBUG_CURVE_POINTS:
            save()
        
        t1 = self.transform.transformPoint(pt1)
        t2 = self.transform.transformPoint(pt2)
        t3 = self.transform.transformPoint(pt3)

        # Break curve into line segments
        points = getPointsFromCurve((self.__currentPoint, t1, t2, t3), 5)

        # Draw points of center line
        if DEBUG_CENTER_POINTS:
            stroke(None)
            strokeWidth(0)
            fill(0, 0, 0, self.alpha)
            for p in points:
                x, y = self.transform_reverse.transformPoint(p)
                rect(x - 1, y - 1, 2, 2)

        # Calculate angles between points

        # The first angle is that of the curve start point to bcp1
        angles = [angleBetweenPoints(self.__currentPoint, t1)]

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
                outer = self._curve_from_lines(outer)
                inner = self._curve_from_lines(inner)
                self.path.append(outer + inner)
            else:
                inner = optimizePointPath(inner, 0.3)
                outer = optimizePointPath(outer, 0.3)
                outer.reverse()
                optimized = optimizePointPath(outer + inner, 1)
                self.addPath([[self.transform.transformPoint(o)] for o in optimized])
            self._draw_nib_face(pt3)

        self.__currentPoint = t3
        if not self.trace and DEBUG_CENTER_POINTS or DEBUG_CURVE_POINTS:
            restore()

    def _closePath(self):
        self.lineTo(self.contourStart)
        self.__currentPoint = None

    def _endPath(self):
        self.__currentPoint = None

    def _draw_nib_face(self, pt):
        if self.trace:
            points = [
                (pt[0] + p[0], pt[1] + p[1])
                for p in [
                    self._get_rotated_point(pp, self.angle)
                    for pp in self.nib_face_path
                ]
            ]
            self.path.append(self._curve_from_lines(points))
        else:
            save()
            translate(pt[0], pt[1])
            rotate(degrees(self.angle))
            newPath()
            moveTo(self.nib_face_path[0])
            for p in self.nib_face_path[1:]:
                lineTo(p)
            closePath()
            drawPath()
            restore()
    
    def _curve_from_lines(self, point_tuple_list: list) -> list:
        curve_points = SCBezierPath().fromPoints(
            [SCPoint(p[0], p[1]) for p in point_tuple_list],
            error=TRACE_ERROR,
            cornerTolerance=TRACE_CORNER_TOLERANCE,
            maxSegments=TRACE_MAXIMUM_SEGMENTS,
        )

        # Reconvert the BezierPath segments to our segment type
        point_tuple_list = []
        first = True
        for segment in curve_points.asSegments():
            segment_tuple = []
            if first:
                # For the first segment, add the move point
                p = segment[0]
                point_tuple_list.append([(p.x, p.y)])
            for p in segment[1:]:
                segment_tuple.append((p.x, p.y))
            point_tuple_list.append(segment_tuple)
        return point_tuple_list

    def trace_path(self, out_glyph):
        from mojo.roboFont import RGlyph

        tmp = RGlyph()
        p = tmp.getPen()
        first = True
        for path in self.path:
            if first:
                first = False
            else:
                p.closePath()
                out_glyph.appendGlyph(tmp)
                tmp.clear()
            p.moveTo(self.round_pt(path[0][0]))
            for segment in path[1:]:
                if len(segment) == 1:
                    p.lineTo(self.round_pt(segment[0]))
                elif len(segment) == 3:
                    p.curveTo(
                        self.round_pt(segment[0]),
                        self.round_pt(segment[1]),
                        self.round_pt(segment[2]),
                    )

                else:
                    print("Unknown segment type:", segment)
        p.closePath()
        # tmp.correctDirection()
        out_glyph.appendGlyph(tmp)
        # out_glyph.removeOverlap()
        # out_glyph.removeOverlap()
        out_glyph.update()
