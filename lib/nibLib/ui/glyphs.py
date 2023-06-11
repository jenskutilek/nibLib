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
