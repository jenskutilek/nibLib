from __future__ import annotations

from beziers.path import BezierPath as SCBezierPath
from beziers.point import Point as SCPoint
from fontPens.penTools import getCubicPoint
from fontTools.misc.bezierTools import calcCubicArcLength
from functools import cached_property
from math import atan2, sqrt
from nibLib.typing import CCurve, TPoint
from typing import List, Sequence, Tuple


def getPointsFromCurve(p: CCurve, div=0.75) -> List[TPoint]:
    """Return a list of points for the given cubic curve segment.

    Args:
        p (CCurve): The cubic curve segment as four control points.
        div (float, optional): The dividend to be used to split the curve. Defaults to 0.75.

    Returns:
        List[TPoint]: The list of points.
    """
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


def getPathFromPoints(points: Sequence[TPoint]) -> List[Tuple[TPoint, ...]]:
    """Return a path with lines and curves from a sequence of points.

    Args:
        points (Sequence[TPoint]): The list of points.

    Returns:
        List[Tuple[TPoint, ...]]: The path.
    """
    curve_points = SCBezierPath().fromPoints(
        [SCPoint(x, y) for x, y in points],
        error=1.0,
        cornerTolerance=1.0,
        maxSegments=10000,
    )

    # Reconvert Simon's BezierPath segments to our segment type
    curves: List[Tuple[TPoint, ...]] = []
    first = True
    for segment in curve_points.asSegments():
        if first:
            # For the first segment, add the move point
            p = segment[0]
            curves.append(((p.x, p.y),))
            first = False
        # Do we have to check the length of the tuples? Or are they always cubic curves
        # with 3 points?
        curves.append(tuple([(p.x, p.y) for p in segment[1:]]))
    return curves


def angleBetweenPoints(p0: TPoint, p1: TPoint) -> float:
    """Return the angle between two points.

    Args:
        p0 (TPoint): The first point.
        p1 (TPoint): The second point.

    Returns:
        float: The angle in radians.
    """
    return atan2(p1[1] - p0[1], p1[0] - p0[0])


def distanceBetweenPoints(p0: TPoint, p1: TPoint, doRound=False) -> float | int:
    """Return the distance between two points.

    Args:
        p0 (TPoint): The first point.
        p1 (TPoint): The second point.
        doRound (bool, optional): Whether to round the distance. Defaults to False.

    Returns:
        float | int: The distance.
    """
    d = sqrt((p0[0] - p1[0]) ** 2 + (p0[1] - p1[1]) ** 2)
    if doRound:
        return round(d)
    else:
        return d


def halfPoint(p0: TPoint, p1: TPoint, doRound=False) -> TPoint:
    """Return a point halfway between two points.

    Args:
        p0 (TPoint): The first point.
        p1 (TPoint): The second point.
        doRound (bool, optional): Whether to round the coordinates of the halfway point. Defaults to False.

    Returns:
        TPoint: The halfway point.
    """
    x0, y0 = p0
    x1, y1 = p1
    xh = 0.5 * (x0 + x1)
    yh = 0.5 * (y0 + y1)
    if doRound:
        return round(xh), round(yh)
    return xh, yh


class Triangle(object):
    """
    A triangle with points A, B, C; sides a, b, c; angles α, β, γ.

         C
        . γ  ..
     b .         ..  a
      .               ..
     . α                 β..
    A . . . . . . . . . . . . . B
                  c
    """

    def __init__(self, A: TPoint, B: TPoint, C: TPoint) -> None:
        """Initialize the triangle with three points A, B, C.

        Args:
            A (TPoint): The point A.
            B (TPoint): The point B.
            C (TPoint): The point C.
        """
        self.A = A
        self.B = B
        self.C = C

    @cached_property
    def sides(self) -> Tuple[float, float, float]:
        """Return the lengths of the three sides of the triangle.

        Returns:
            Tuple[float, float, float]: The lengths of the sides a, b, c.
        """
        self.a = distanceBetweenPoints(self.B, self.C)
        self.b = distanceBetweenPoints(self.A, self.C)
        self.c = distanceBetweenPoints(self.A, self.B)
        return self.a, self.b, self.c

    @cached_property
    def height_a(self) -> float:
        """Return the height over side a.

        Returns:
            float: The height.
        """
        a, b, c = self.sides
        s = (a + b + c) / 2
        h = 2 * sqrt(s * (s - a) * (s - b) * (s - c)) / a
        return h


def optimizePointPath(p: Sequence[TPoint], dist=0.49) -> List[TPoint]:
    """Return an optimized version of a list of points. A points will be skipped unless
    its distance from the line formed by its previous to its next point is greater than
    `dist`.

    Args:
        p (Sequence[TPoint]): The path as a sequence of points.
        dist (float, optional): The maximum distance. Defaults to 0.49.

    Returns:
        Sequence[TPoint]: The optimized sequence of points.
    """
    num_points = len(p)
    p0 = p[0]
    optimized = [p0]  # Keep the first point of the original path
    i = 0
    while i < num_points - 2:
        p1 = p[i + 1]
        p2 = p[i + 2]
        t = Triangle(p0, p2, p1)
        if t.height_a > dist:
            optimized.append(p1)
            p0 = p[i]
        else:
            pass
        i += 1
    optimized.append(p[-1])  # Keep the last point of the original path
    return optimized
