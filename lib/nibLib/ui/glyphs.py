from __future__ import annotations

from GlyphsApp import Glyphs
from nibLib.ui import JKNib


class JKNibGlyphs(JKNib):

    user_data_attr = "userData"

    def __init__(self, layer, font):
        super(JKNibGlyphs, self).__init__(layer, font)

    def envSpecificInit(self):
        pass

    def envSpecificQuit(self):
        pass

    def getLayerList(self):
        return [layer.name for layer in self.glyph.parent.layers]

    def save_to_lib(self, font_or_glyph, libkey, value):
        if value is None:
            if font_or_glyph.userData and libkey in font_or_glyph.userData:
                del font_or_glyph.userData[libkey]
        else:
            if font_or_glyph.userData and libkey in font_or_glyph.userData:
                if font_or_glyph.userData[libkey] != value:
                    font_or_glyph.userData[libkey] = value
            else:
                font_or_glyph.userData[libkey] = value

    def load_from_lib(self, font_or_glyph, libkey, attr=None):
        if font_or_glyph is None:
            return False
        value = font_or_glyph.userData.get(libkey, None)
        if attr is not None:
            if value is not None:
                setattr(self, attr, value)
        return value

    def update_current_view(self):
        currentTabView = Glyphs.font.currentTab
        if currentTabView:
            currentTabView.graphicView().setNeedsDisplay_(True)

    def _setup_draw(self, preview=False):
        if preview:
            fill(0)
            stroke(0)
        else:
            fill(0.6, 0.7, 0.9, 0.5)
            stroke(0.6, 0.7, 0.9)
        # strokeWidth(self.height)
        # strokeWidth(1)
        strokeWidth(0)
        stroke(None)
        lineJoin(self.line_join)

    def _draw_preview_glyph(self, preview=False):
        if self.guide_layer is None:
            self._update_layers()
            return
        glyph = get_guide_representation(font=guide_glyph.font, angle=self.angle)
        save()
        self._setup_draw(preview=preview)
        # TODO: Reuse pen object.
        # Needs modifications to the pens before possible.
        p = self.nib_pen(
            self.font, self.angle, self.width, self.height, self._draw_nib_faces, nib_superness=self.superness
        )
        glyph.draw(p)
        restore()
