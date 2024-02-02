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

    # @objc.python_method
    # def conditionalContextMenus(self):

    #     # Empty list of context menu items
    #     contextMenus = []

    #     # Execute only if layers are actually selected
    #     if Glyphs.font.selectedLayers:
    #         layer = Glyphs.font.selectedLayers[0]

    #         # Exactly one object is selected and it’s an anchor
    #         if len(layer.selection) == 1 and type(layer.selection[0]) == GSAnchor:

    #             # Add context menu item
    #             contextMenus.append(
    #                 {
    #                     "name": Glyphs.localize(
    #                         {
    #                             "en": "Do something else",
    #                             "de": "Tu etwas anderes",
    #                             "fr": "Faire aute chose",
    #                             "es": "Hacer algo más",
    #                             "pt": "Faça outra coisa",
    #                         }
    #                     ),
    #                     "action": self.doSomethingElse_,
    #                 }
    #             )

    #     # Return list of context menu items
    #     return contextMenus

    # def doSomethingElse_(self, sender):
    #     print("Just did something else")

    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__
