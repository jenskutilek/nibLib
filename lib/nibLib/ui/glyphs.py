from __future__ import annotations

from GlyphsApp import Glyphs, GSBackgroundLayer

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
        return ["nib", "background"]

    def _update_current_glyph_view(self) -> None:
        # Make sure the current view gets redrawn
        if not Glyphs.font:
            # No font, no redraw
            return

        currentTabView = Glyphs.font.currentTab
        if currentTabView:
            currentTabView.graphicView().setNeedsDisplay_(True)

    def _set_guide_layer(self, name: str) -> None:
        """
        Set self.guide_layer to the actual layer object.
        """
        if name == "background":
            # Use the current background
            if isinstance(self.glyph, GSBackgroundLayer):
                # print("Using the layer itself as it seems to be a background layer")
                self.guide_layer = self.glyph
            else:
                # print("Using the background of the current layer")
                self.guide_layer = self.glyph.background
            return

        mid = self.glyph.master.id
        found = False
        for layer in self.glyph.parent.layers:
            if name == layer.name and layer.associatedMasterId == mid:
                self.guide_layer = layer
                found = True
                break
        if not found:
            self.guide_layer = None

    def draw_preview_glyph(self, preview=False, scale=1.0) -> None:
        if self.guide_layer is None:
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

        try:
            self.guide_layer.draw(p)
        except AttributeError:
            print("AttributeError", self.guide_layer)
            pass
        # restore()

    def _trace_callback(self, sender) -> None:
        if self.guide_layer is None:
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

        try:
            self.guide_layer.draw(p)
            p.trace_path(self.glyph)
        except AttributeError:
            pass
