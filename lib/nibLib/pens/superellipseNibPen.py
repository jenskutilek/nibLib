from __future__ import division, print_function

from math import cos, degrees, pi, sin
import operator

try:
    from mojo.drawingTools import *
except ImportError:
    from GlyphsApp.drawingTools import *

from nibLib.geometry import optimizePointPath
from nibLib.pens.ovalNibPen import OvalNibPen


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
        self.nib_face_path_transformed = points[:]
        self.cache_angle = 0

    def _get_rotated_point(self, pt, phi):
        x, y = pt
        cp = cos(phi)
        sp = sin(phi)
        x1 = x * cp - y * sp
        y1 = x * sp + y * cp

        return x1, y1

    def transform_nib_path(self, alpha):

        self.nib_face_path_transformed = [
            self._get_rotated_point(pt, alpha) for pt in self.nib_face_path
        ]
        self.cache_angle = alpha

    def _get_tangent_point(self, alpha):

        # Calculate the point on the superellipse
        # at the given tangent angle alpha.

        # For now, we do this the pedestrian way, until I can figure out
        # how to calculate the tangent point directly.

        omega = alpha + self.angle  # Line angle
        if self.cache_angle != alpha:
            self.transform_nib_path(self.angle - omega)

        x, y = max(self.nib_face_path_transformed, key=operator.itemgetter(1))
        x, y = self._get_rotated_point(
            (x, y), omega - self.angle
        )  # Or just omega if you don't rotate

        return x, y

    # def _get_rotated_tangent_point(self, pt):
    #     return pt

    def _draw_nib_face(self, pt):
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

        if self.trace:
            self.path.append(
                [
                    (pt[0] + p[0], pt[1] + p[1])
                    for p in [
                        self._get_rotated_point(pp, self.angle)
                        for pp in self.nib_face_path
                    ]
                ]
            )
