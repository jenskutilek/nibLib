from __future__ import annotations

from GlyphsApp import Glyphs
from GlyphsApp.drawingTools import *
from nibLib.ui import JKNib
from typing import Any, List


class JKNibGlyphs(JKNib):
    user_data_attr = "userData"

    def envSpecificInit(self) -> None:
        pass

    def envSpecificQuit(self) -> None:
        pass

    def getLayerList(self) -> List[str]:
        return [layer.name for layer in self.glyph.parent.layers]

    def save_to_lib(self, font_or_glyph, libkey, value) -> None:
        if value is None:
            if font_or_glyph.userData and libkey in font_or_glyph.userData:
                del font_or_glyph.userData[libkey]
        else:
            if font_or_glyph.userData and libkey in font_or_glyph.userData:
                if font_or_glyph.userData[libkey] != value:
                    font_or_glyph.userData[libkey] = value
            else:
                font_or_glyph.userData[libkey] = value

    def load_from_lib(self, font_or_glyph, libkey, attr=None) -> Any:
        if font_or_glyph is None:
            return False
        value = font_or_glyph.userData.get(libkey, None)
        if attr is not None:
            if value is not None:
                setattr(self, attr, value)
        return value

    def update_current_view(self) -> None:
        currentTabView = Glyphs.font.currentTab
        if currentTabView:
            currentTabView.graphicView().setNeedsDisplay_(True)

    def _setup_draw(self, preview=False) -> None:
        if preview:
            fill(1, 0, 0)
            stroke(0)
        else:
            fill(0.6, 0.7, 0.9, 0.5)
            stroke(0.6, 0.7, 0.9)
        # strokeWidth(self.height)
        # strokeWidth(1)
        strokeWidth(0)
        stroke(None)
        lineJoin(self.line_join)

    def draw_preview_glyph(self, preview=False) -> None:
        if self.guide_layer is None:
            self._update_layers()
            return
        save()
        self._setup_draw(preview=preview)
        # TODO: Reuse pen object.
        # Needs modifications to the pens before possible.
        p = self.nib_pen(
            self.font,
            self.angle,
            self.width,
            self.height,
            self._draw_nib_faces,
            nib_superness=self.superness,
        )
        self.guide_layer.draw(p)
        restore()
