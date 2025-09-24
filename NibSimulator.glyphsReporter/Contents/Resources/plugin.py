from __future__ import annotations

import objc
from AppKit import NSClassFromString
from GlyphsApp import Glyphs
from GlyphsApp.plugins import ReporterPlugin
from GlyphsApp.drawingTools import *

from nibLib.ui.glyphs import JKNibGlyphs


class NibSimulator(ReporterPlugin):
    @objc.python_method
    def settings(self):
        self.menuName = Glyphs.localize(
            {
                "en": "Nib Simulator",
                "de": "Schreibfedersimulator",
            }
        )
        self.generalContextMenus = [
            {
                "name": Glyphs.localize(
                    {
                        "en": "Nib Settings...",
                        "de": "Schreibfedereinstellungen ...",
                    }
                ),
                "action": self.openSettingsWindow_,
            }
        ]
        self.w = None

    @objc.python_method
    def background(self, layer):
        if self.w is None:
            return

        # If the layer has changed, we need a new guide layer
        if layer != self.w.glyph:
            self.w.glyph = layer

        currentController = self.controller.view().window().windowController()
        if currentController:
            tool = currentController.toolDrawDelegate()
            if not (
                tool.isKindOfClass_(NSClassFromString("GlyphsToolText"))
                or tool.isKindOfClass_(NSClassFromString("GlyphsToolHand"))
                or tool.isKindOfClass_(
                    NSClassFromString("GlyphsToolTrueTypeInstructor")
                )
            ):
                self.w.draw_preview_glyph(scale=self.getScale())

    @objc.python_method
    def window_will_close(self):
        self.w = None

    def openSettingsWindow_(self, sender):
        font = Glyphs.font
        layer = None
        master = None
        if font is not None:
            sel = font.selectedLayers
            layer = None if sel is None else sel[0]
            if layer is not None:
                master = layer.master

        self.w = JKNibGlyphs(layer, master, self)

    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__
