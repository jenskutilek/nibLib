from __future__ import annotations

from fontTools.misc.transform import Transform
from fontTools.pens.basePen import BasePen
from math import pi

try:
    from mojo.drawingTools import stroke, strokeWidth
except ImportError:
    from GlyphsApp.drawingTools import stroke, strokeWidth


class NibPen(BasePen):
    def __init__(
        self,
        glyphSet,
        angle,
        width,
        height,
        show_nib_faces=False,
        alpha=0.2,
        nib_superness=2.5,
        trace=False,
        round_coords=False,
    ):
        BasePen.__init__(self, glyphSet)
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
        self.a = 0.5 * width
        self.b = 0.5 * height
        self.color = show_nib_faces
        self.highlight_nib_faces = False
        self.alpha = alpha
        self.nib_superness = nib_superness
        self.trace = trace
        self.round_coords = round_coords

        # Initialize the nib face path
        # This is only needed for more complex shapes
        self.setup_nib()

        self.path = []

        self.__currentPoint = None
        if self.color:
            stroke(0, 0, 0, 0.5)
            strokeWidth(0.1)

    def round_pt(self, pt):
        # Round a point based on self.round_coords
        if not self.round_coords:
            return pt
        x, y = pt
        return round(x), round(y)

    def setup_nib(self):
        pass

    def addComponent(self, baseName, transformation):
        pass

    # unused
    # def draw(self):
    #     drawPath()

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
