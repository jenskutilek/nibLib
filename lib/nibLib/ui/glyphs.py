from __future__ import annotations

from GlyphsApp import Glyphs

# from GlyphsApp.drawingTools import *
from nibLib.ui import JKNib
from typing import List


class JKNibGlyphs(JKNib):
    settings_attr = "userData"

    def envSpecificInit(self) -> None:
        self.w.draw_space.enable(False)
        self.w.draw_preview.enable(False)
        self.w.draw_faces.enable(False)

    def envSpecificQuit(self) -> None:
        pass

    def getLayerList(self) -> List[str]:
        if self.font is None:
            return []

        master_id = self.glyph.master.id
        return [
            layer.name
            for layer in self.glyph.parent.layers
            if layer.associatedMasterId == master_id
        ]

    def _update_current_glyph_view(self) -> None:
        # Make sure the current view gets redrawn
        currentTabView = Glyphs.font.currentTab
        if currentTabView:
            currentTabView.graphicView().setNeedsDisplay_(True)

    def _set_guide_layer(self, name: str) -> None:
        """
        Set self.guide_layer to the actual layer object.
        """
        print(f"  _set_guide_layer: {name}")
        mid = self.glyph.master.id
        print(f"    Looking in master: {self.glyph.master}")
        for layer in self.glyph.parent.layers:
            if name == layer.name and layer.associatedMasterId == mid:
                self.guide_layer = layer
                break

    def draw_preview_glyph(self, preview=False, scale=1.0) -> None:
        if self.guide_layer_name is None:
            self._update_layers()
            return
        # save()
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
        p._scale = scale
        self.guide_layer.draw(p)
        # restore()

    def _trace_callback(self, sender) -> None:
        if self.guide_layer_name is None:
            self._update_layers()
            return
        p = self.nib_pen(
            self.font,
            self.angle,
            self.width,
            self.height,
            self._draw_nib_faces,
            nib_superness=self.superness,
            trace=True,
        )
        self.guide_layer.draw(p)
        p.trace_path(self.glyph)
