from __future__ import division, print_function

from fontTools.pens.basePen import BasePen

try:
    from mojo.drawingTools import stroke, strokeWidth
except ImportError:
    from GlyphsApp.drawingTools import stroke, strokeWidth


class NibPen(BasePen):
    def __init__(
        self, glyphSet, angle, width, height, show_nib_faces=False, alpha=0.2,
        nib_superness=2.5, trace=False
    ):
        BasePen.__init__(self, glyphSet)
        self.angle = angle
        self.width = width
        self.height = height
        self.a = 0.5 * width
        self.b = 0.5 * height
        self.color = show_nib_faces
        self.highlight_nib_faces = False
        self.alpha = alpha
        self.nib_superness = nib_superness
        self.trace = trace

        # Initialize the nib face path
        # This is only needed for more complex shapes
        self.setup_nib()

        self.path = []

        self.__currentPoint = None
        if self.color:
            stroke(0, 0, 0, 0.5)
            strokeWidth(0.1)

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
                # tmp.correctDirection()
                out_glyph.appendGlyph(tmp)
                tmp.clear()
            p.moveTo((
                int(round(path[0][0])),
                int(round(path[0][1]))
            ))
            for segment in path[1:]:
                if len(segment) == 2:
                    p.lineTo((
                        int(round(segment[0])),
                        int(round(segment[1]))
                    ))
                elif len(segment) == 3:
                    p.curveTo(
                        (
                            int(round(segment[0][0])),
                            int(round(segment[0][1]))
                        ),
                        (
                            int(round(segment[1][0])),
                            int(round(segment[1][1]))
                        ),
                        (
                            int(round(segment[2][0])),
                            int(round(segment[2][1]))
                        ),
                    )

                else:
                    print("Unknown segment type:", segment)
        p.closePath()
        # tmp.correctDirection()
        out_glyph.appendGlyph(tmp)
        # out_glyph.removeOverlap()
        # out_glyph.removeOverlap()
        out_glyph.update()
