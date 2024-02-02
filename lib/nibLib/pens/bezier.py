from __future__ import annotations

from fontTools.misc.bezierTools import (
    calcCubicParameters,
    solveQuadratic,
    splitCubicAtT,
    epsilon,
)
from fontTools.misc.transform import Transform


def normalize_quadrant(q):
    r = 2 * q
    nearest = round(r)
    e = abs(nearest - r)
    if e > epsilon:
        return q
    rounded = nearest * 0.5
    return rounded


def split_at_extrema(pt1, pt2, pt3, pt4, transform=Transform()):
    """
    Add extrema to a cubic curve, after applying a transformation.
    Example ::

        >>> # A segment in which no extrema will be added.
        >>> split_at_extrema((297, 52), (406, 52), (496, 142), (496, 251))
        [((297, 52), (406, 52), (496, 142), (496, 251))]
        >>> from fontTools.misc.transform import Transform
        >>> split_at_extrema((297, 52), (406, 52), (496, 142), (496, 251), Transform().rotate(-27))
        [((297.0, 52.0), (84.48072108963274, -212.56513799170233), (15.572491694678519, -361.3686192413668), (15.572491694678547, -445.87035970621713)), ((15.572491694678547, -445.8703597062171), (15.572491694678554, -506.84825401175414), (51.4551516055374, -534.3422304091257), (95.14950889754756, -547.6893014808263))]
    """
    # Transform the points for extrema calculation;
    # transform is expected to rotate the points by - nib angle.
    t2, t3, t4 = transform.transformPoints([pt2, pt3, pt4])
    # When pt1 is the current point of the path,  it is already transformed, so
    # we keep it like it is.
    t1 = pt1

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
    # They should be unique before, or can a root be duplicated (in h and v?)
    roots = sorted(set(roots))

    if not roots:
        return [(t1, t2, t3, t4)]

    return splitCubicAtT(t1, t2, t3, t4, *roots)


if __name__ == "__main__":
    import sys
    import doctest

    sys.exit(doctest.testmod().failed)
