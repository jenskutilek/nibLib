from __future__ import annotations

# RoboFont-internal packages
# from lib.tools.extremePoints import ExtremePointPen
# from math import degrees
from mojo.drawingTools import fill, lineJoin, restore, save, strokeWidth, stroke
from mojo.events import addObserver, removeObserver
from mojo.roboFont import CurrentFont, CurrentGlyph, RGlyph
from mojo.UI import UpdateCurrentGlyphView

from nibLib.ui import JKNib
from nibLib import DEBUG, rf_guide_key


def NibGuideGlyphFactory(glyph, font, angle):
    # pen = ExtremePointPen(vertical=True, horizontal=True)
    g = RGlyph(glyph).copy()
    # g.rotateBy(degrees(-angle))
    # # g.extremePoints()
    # g.drawPoints(pen)
    # g.clear()
    # out_pen = g.getPointPen()
    # pen.drawPoints(out_pen)
    # g.rotateBy(degrees(angle))
    return g


def _registerFactory():
    # From https://github.com/typesupply/glyph-nanny/blob/master/Glyph%20Nanny.roboFontExt/lib/glyphNanny.py
    # always register if debugging
    # otherwise only register if it isn't registered
    from defcon import registerRepresentationFactory, Glyph

    if DEBUG:
        if rf_guide_key in Glyph.representationFactories:
            for font in AllFonts():
                for glyph in font:
                    glyph.naked().destroyAllRepresentations()
        registerRepresentationFactory(rf_guide_key, NibGuideGlyphFactory)
    else:
        if rf_guide_key not in Glyph.representationFactories:
            registerRepresentationFactory(Glyph, rf_guide_key, NibGuideGlyphFactory)


def _unregisterFactory():
    from defcon import unregisterRepresentationFactory, Glyph

    try:
        unregisterRepresentationFactory(Glyph, rf_guide_key)
    except:
        pass


class JKNibRoboFont(JKNib):
    observers = (
        ("_preview", "drawBackground"),
        ("_preview", "drawInactive"),
        ("_previewFull", "drawPreview"),
        ("_glyph_changed", "currentGlyphChanged"),
        ("_font_changed", "fontBecameCurrent"),
        ("_font_resign", "fontResignCurrent"),
    )

    def __init__(self):
        super(JKNibRoboFont, self).__init__(CurrentGlyph(), CurrentFont())

    def envSpecificInit(self):
        self.setUpBaseWindowBehavior()
        self.addObservers()
        _registerFactory()
        self.load_settings()

    def envSpecificQuit(self):
        self.removeObservers()
        _unregisterFactory()

    def addObservers(self):
        for method, observer in self.observers:
            addObserver(self, method, observer)

    def removeObservers(self):
        for method, observer in self.observers:
            removeObserver(self, observer)
        if self.w.draw_space.get():
            removeObserver(self, "spaceCenterDraw")

    def getLayerList(self):
        return ["foreground"] + self.font.layerOrder

    def _update_current_glyph_view(self):
        UpdateCurrentGlyphView()

    def _draw_space_callback(self, sender):
        # RF-specific: Draw in space center
        value = sender.get()
        if value:
            addObserver(self, "_previewFull", "spaceCenterDraw")
        else:
            removeObserver(self, "spaceCenterDraw")

    def get_guide_representation(self, glyph, font, angle):
        return glyph.getLayer(self.guide_layer).getRepresentation(
            rf_guide_key, font=font, angle=angle
        )

    def _trace_callback(self, sender):
        if self.guide_layer is None:
            self._update_layers()
            return
        guide_glyph = self.glyph.getLayer(self.guide_layer)
        glyph = self.get_guide_representation(
            glyph=guide_glyph, font=guide_glyph.font, angle=self.angle
        )
        p = self.nib_pen(
            self.font,
            self.angle,
            self.width,
            self.height,
            self._draw_nib_faces,
            nib_superness=self.superness,
            trace=True,
        )
        glyph.draw(p)
        p.trace_path(self.glyph)

    def _draw_preview(self, notification, preview=False):
        self.draw_preview_glyph(preview=preview)

    def _preview(self, notification):
        self.draw_preview_glyph(False)

    def _previewFull(self, notification):
        if self._draw_in_preview_mode:
            self.draw_preview_glyph(True)

    def _glyph_changed(self, notification):
        if self.glyph is not None:
            self.save_settings()
        self.glyph = notification["glyph"]
        self.font = CurrentFont()
        self.font_layers = self.getLayerList()
        if self.glyph is not None:
            self.load_settings()

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

    def draw_preview_glyph(self, preview=False):
        if self.guide_layer is None:
            self._update_layers()
            return
        guide_glyph = self.glyph.getLayer(self.guide_layer)
        glyph = self.get_guide_representation(
            glyph=guide_glyph, font=guide_glyph.font, angle=self.angle
        )
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
        glyph.draw(p)
        restore()

    def save_to_lib(self, font_or_glyph, libkey, value):
        if value is None:
            if libkey in font_or_glyph.lib:
                del font_or_glyph.lib[libkey]
        else:
            if libkey in font_or_glyph.lib:
                if font_or_glyph.lib[libkey] != value:
                    font_or_glyph.lib[libkey] = value
            else:
                font_or_glyph.lib[libkey] = value

    def load_from_lib(self, font_or_glyph, libkey, attr=None):
        if font_or_glyph is None:
            return False
        value = font_or_glyph.lib.get(libkey, None)
        if value is None:
            return False
        if attr is not None:
            setattr(self, attr, value)
        return value

    def _font_resign(self, notification=None):
        self.save_settings()

    def _font_changed(self, notification):
        self.font = notification["font"]
        if self.font is None:
            self.font_layers = []
        else:
            self.font_layers = self.getLayerList()

    def _update_layers(self):
        if self.font is None:
            self.font_layers = []
        else:
            self.font_layers = self.getLayerList()
        self.w.guide_select.setItems(self.font_layers)
        if self.font_layers:
            last_layer = len(self.font_layers) - 1
            self.w.guide_select.set(last_layer)
            self.guide_layer = self.font_layers[last_layer]
