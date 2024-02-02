from __future__ import annotations

import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
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
    def foreground(self, layer):
        if self.w is None:
            return
        save()
        p = self.w.nib_pen(
            self.w.font,
            self.w.angle,
            self.w.width,
            self.w.height,
            self.w._draw_nib_faces,
            nib_superness=self.w.superness,
        )
        if hasattr(layer.background, "draw"):
            layer.background.draw(p)
        else:
            layer.draw(p)
        restore()

    # @objc.python_method
    # def inactiveLayerForeground(self, layer):
    #     NSColor.selectedTextColor().set()
    #     if layer.paths:
    #         layer.bezierPath.fill()
    #     if layer.components:
    #         NSColor.findHighlightColor().set()
    #         for component in layer.components:
    #             component.bezierPath.fill()

    # @objc.python_method
    # def preview(self, layer):
    #     NSColor.textColor().set()
    #     if layer.paths:
    #         layer.bezierPath.fill()
    #     if layer.components:
    #         NSColor.highlightColor().set()
    #         for component in layer.components:
    #             component.bezierPath.fill()

    def openSettingsWindow_(self, sender):
        self.w = JKNibGlyphs(None, None)

    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__
