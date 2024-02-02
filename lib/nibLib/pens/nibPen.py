from __future__ import annotations

from fontTools.misc.transform import Transform
from fontTools.pens.basePen import BasePen
from math import pi
from nibLib.pens.drawing import draw_path
from nibLib.typing import TPoint
from typing import Sequence


class NibPen(BasePen):
    def __init__(
        self,
        glyphSet,
        angle: float,  # The nib's angle in radians.
        width: float,
        height: float,
        show_nib_faces=False,
        nib_superness=2.5,
        trace=False,
        round_coords=False,
    ):
        """The base class for all nib pens.

        Args:
            glyphSet (Dict): The glyph set, used to access components.
            angle (float): The nib's angle over the horizontal in radians.
            width (float): The width of the nib.
            height (float): The height of the nib.
            show_nib_faces (bool, optional): Whether the nib face should be drawn separately. Defaults to False.
            nib_superness (float, optional): The superness of the nib shape. Only used in superelliptical nibs. Defaults to 2.5.
            trace (bool, optional): Whether the path should be traced. Defaults to False.
            round_coords (bool, optional): Whether the coordinates of the resulting path should be rounded. Defaults to False.
        """
        BasePen.__init__(self, glyphSet)

        # Reduce the angle if it is greater than 180° or smaller than -180°
        self.angle = angle
        if self.angle > pi:
            self.angle -= pi
        elif self.angle < -pi:
            self.angle += pi

        # Store a transform, used for calculating extrema in some nib models
        self.transform = Transform().rotate(-self.angle)
        self.transform_reverse = Transform().rotate(self.angle)

        self.width = width
        self.height = height

        # Cache the half width and height
        self.a = 0.5 * width
        self.b = 0.5 * height

        # Used for drawing
        self.color = show_nib_faces
        self.highlight_nib_faces = False
        self._scale = 1.0

        # Used for superelliptical nibs
        self.nib_superness = nib_superness

        # Whether to trace the path; otherwise it is just drawn for preview
        self.trace = trace

        # Should the coordinates of the nib path be rounded?
        self.round_coords = round_coords

        # Initialize the nib face path
        # This is only needed for more complex shapes
        self.setup_nib()

        self.path = []

        self._currentPoint: TPoint | None = None

    def round_pt(self, pt: TPoint) -> TPoint:
        # Round a point based on self.round_coords
        if not self.round_coords:
            return pt
        x, y = pt
        return round(x), round(y)

    def setup_nib(self) -> None:
        pass

    def addComponent(self, baseName: str, transformation: Transform) -> None:
        """Components are ignored.

        Args:
            baseName (str): The base glyph name of the component.
            transformation (Transform): The component's transformation.
        """
        pass

    def addPath(self, path: Sequence[Sequence[TPoint]] | None = None) -> None:
        """
        Add a path to the nib path.
        """
        if path is None:
            return

        tr_path = [self.transform_reverse.transformPoints(pts) for pts in path]
        if self.trace:
            self.path.append(tr_path)
        else:
            draw_path(tr_path, width=1 / self._scale)

    def addPathRaw(self, path: Sequence[Sequence[TPoint]] | None = None) -> None:
        """
        Add a path to the nib path. The path is added as is, i.e. the points must have
        been transformed by the caller.
        """
        if path is None:
            return

        if self.trace:
            self.path.append(path)
        else:
            draw_path(path, width=1 / self._scale)

    def trace_path(self, out_glyph, clear=True) -> None:
        """Trace the path into the supplied glyph.

        Args:
            out_glyph (RGlyph): The glyph to receive the traced path.
        """
        if clear:
            out_glyph.clear()
        p = out_glyph.getPen()
        first = True
        for path in self.path:
            if first:
                first = False
            else:
                p.closePath()
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
        # out_glyph.removeOverlap()
        # out_glyph.removeOverlap()
        # out_glyph.update()
