from unittest import TestCase

from nibLib.geometry import getPathFromPoints


class GeometryTest(TestCase):
    def test_getPathFromPoints(self):
        pts = [(0, 0), (100, 100)]
        assert getPathFromPoints(pts) == [
            ((0.0, 0.0),),
            (
                (33.333333333333336, 33.333333333333336),
                (66.66666666666667, 66.66666666666667),
                (100.0, 100.0),
            ),
        ]
