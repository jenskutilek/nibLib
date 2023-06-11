from __future__ import division, print_function
from math import degrees, pi, radians
import vanilla
from defconAppKit.windows.baseWindow import BaseWindowController

from nibLib import (
    DEBUG,
    def_angle_key,
    def_width_key,
    def_height_key,
    def_local_key,
    def_guide_key,
    def_super_key,
    def_model_key,
    rf_guide_key,
)
from nibLib.pens import nib_models


class JKNib(BaseWindowController):
    def __init__(self, glyph, font):
        self.model = "Superellipse"
        self.angle = radians(30)
        self.width = 60
        self.height = 2
        self.superness = 2.5
        self.line_join = "round"  # bevel, round
        self.guide_layer = None
        self.nib_pen = nib_models[self.model]

        self._draw_nib_faces = False
        self._draw_in_preview_mode = False

        self.glyph = glyph
        self.font = font

        # window dimensions
        width = 300
        height = 322

        self.w = vanilla.FloatingWindow((width, height), "Nib Simulator")

        col = 60
        y = 10

        self.w.model_label = vanilla.TextBox((8, y, col - 8, 20), "Model")
        self.w.model_select = vanilla.PopUpButton(
            (col, y, -48, 20),
            nib_models.keys(),
            callback=self._model_select_callback,
        )

        y += 32
        self.w.angle_label = vanilla.TextBox((8, y, col - 8, 20), "Angle")
        self.w.angle_slider = vanilla.Slider(
            (col, y, -48, 20),
            minValue=0,
            maxValue=180,
            value=30,
            tickMarkCount=7,
            callback=self._nib_angle_callback,
            stopOnTickMarks=False,
        )
        self.w.angle_text = vanilla.TextBox((-40, y, -8, 20), "%i" % int(round(degrees(self.angle))))

        y += 24

        self.w.width_label = vanilla.TextBox((8, y, col - 8, 20), "Width")
        self.w.width_slider = vanilla.Slider(
            (col, y, -48, 20),
            minValue=0,
            maxValue=200,
            value=self.width,
            # tickMarkCount=7,
            callback=self._nib_width_callback,
            # stopOnTickMarks=False,
        )
        self.w.width_text = vanilla.TextBox((-40, y, -8, 20), "%i" % self.width)

        y += 24

        self.w.height_label = vanilla.TextBox((8, y, col - 8, 20), "Height")
        self.w.height_slider = vanilla.Slider(
            (col, y, -48, 20),
            minValue=1,
            maxValue=200,
            value=self.height,
            # tickMarkCount=7,
            callback=self._nib_height_callback,
            # stopOnTickMarks=False,
        )
        self.w.height_text = vanilla.TextBox((-40, y, -8, 20), "%i" % self.height)

        y += 24

        self.w.superness_label = vanilla.TextBox((8, y, col - 8, 20), "Super")
        self.w.superness_slider = vanilla.Slider(
            (col, y, -48, 20),
            minValue=1.01,
            maxValue=15.0,
            value=self.superness,
            callback=self._nib_superness_callback,
        )
        self.w.superness_text = vanilla.TextBox((-40, y, -8, 20), "%0.2f" % self.superness)

        y += 32
        self.w.guide_label = vanilla.TextBox((8, y, col - 8, 20), "Guide")
        self.w.guide_select = vanilla.PopUpButton(
            (col, y, -48, 20),
            []
            # callback=self._guide_select_callback,
        )

        y += 32
        self.w.glyph_local = vanilla.CheckBox(
            (col, y, -40, 20),
            "Glyph Uses Local Parameters",
            callback=self._glyph_local_callback,
            value=False,
        )

        y += 32
        self.w.display_label = vanilla.TextBox((8, y, col - 8, 20), "Display")
        self.w.draw_space = vanilla.CheckBox(
            (col, y, -48, 20),
            "Draw In Space Center",
            callback=self._draw_space_callback,
            value=False,
        )

        y += 24
        self.w.draw_preview = vanilla.CheckBox(
            (col, y, -48, 20),
            "Draw In Preview Mode",
            callback=self._draw_preview_callback,
            value=False,
        )

        y += 24
        self.w.draw_faces = vanilla.CheckBox(
            (col, y, -48, 20),
            "Draw Nib Faces In RGB",
            callback=self._draw_faces_callback,
            value=False,
        )

        y += 32
        self.w.trace_outline = vanilla.Button((col, y, 120, 20), title="Trace Outline", callback=self._trace_callback)

        self.envSpecificInit()
        self._update_layers()
        # self._update_ui()
        # self.w.trace_outline.enable(False)
        self.w.open()
        self._update_current_glyph_view()

    def envSpecificInit(self):
        pass

    def windowCloseCallback(self, sender):
        if self.font is not None:
            self.save_settings()
        self.envSpecificQuit()
        super(JKNib, self).windowCloseCallback(sender)
        self._update_current_glyph_view()

    def envSpecificQuit(self):
        pass

    def _update_current_glyph_view(self):
        # Overwrite with editor-specific update call
        pass

    def _update_layers(self):
        # Override with editor-specific layer update call
        pass

    def getLayerList(self):
        return []

    def _update_ui(self):
        # print("_update_ui")
        i = 0
        for i, model in enumerate(self.w.model_select.getItems()):
            if model == self.model:
                break
        self.w.model_select.set(i)
        if self.model in nib_models:
            self.nib_pen = nib_models[self.model]
        else:
            self.nib_pen = nib_models[list(nib_models.keys())[0]]
        self.w.angle_slider.set(self.angle)
        self.w.angle_text.set("%i" % int(round(degrees(self.angle))))
        self.w.width_slider.set(self.width)
        self.w.width_text.set("%i" % self.width)
        self.w.width_slider.setMinValue(self.height + 1)
        self.w.height_slider.set(self.height)
        self.w.height_text.set("%i" % self.height)
        self.w.height_slider.set(self.height)
        self.w.superness_text.set("%0.2f" % self.superness)
        self.w.superness_slider.set(self.superness)
        if self.font is None:
            self.w.guide_select.setItems([])
        else:
            if self.guide_layer in self.font_layers:
                self.w.guide_select.setItems(self.font_layers)
                self.w.guide_select.set(self.font_layers.index(self.guide_layer))
            else:
                self._update_layers()
        self.check_secondary_ui()

    def check_secondary_ui(self):
        if self.model == "Superellipse":
            self.w.superness_slider.enable(True)
        else:
            self.w.superness_slider.enable(False)
        if self.model == "Rectangle":
            self.w.draw_faces.enable(True)
        else:
            self.w.draw_faces.enable(False)

    def _model_select_callback(self, sender):
        self.model = self.w.model_select.getItems()[sender.get()]
        self.nib_pen = nib_models[self.model]
        self.check_secondary_ui()
        self._update_current_glyph_view()

    def _nib_angle_callback(self, sender):
        angle = int(round(degrees(sender.get())))
        self.angle = radians(angle)
        self.w.angle_text.set("%i" % angle)
        self._update_current_glyph_view()

    def _nib_width_callback(self, sender):
        self.width = int(round(sender.get()))
        self.w.width_text.set("%i" % self.width)
        self.w.height_slider.setMaxValue(self.width)
        self._update_current_glyph_view()

    def _nib_height_callback(self, sender):
        self.height = int(round(sender.get()))
        self.w.height_text.set("%i" % self.height)
        self.w.width_slider.setMinValue(self.height)
        self._update_current_glyph_view()

    def _nib_superness_callback(self, sender):
        self.superness = sender.get()
        self.w.superness_text.set("%0.2f" % self.superness)
        self._update_current_glyph_view()

    def _glyph_local_callback(self, sender):
        value = sender.get()
        # print("Local:", value)
        self.save_to_lib(self.glyph, def_local_key, False)
        if not value:
            self.load_settings()

    def _draw_space_callback(self, sender):
        pass

    def _draw_preview_callback(self, sender):
        self._draw_in_preview_mode = sender.get()
        self._update_current_glyph_view()

    def _draw_faces_callback(self, sender):
        self._draw_nib_faces = sender.get()
        self._update_current_glyph_view()

    def get_guide_representation(self, glyph, font, angle):
        # TODO: Rotate, add extreme points, rotate back
        return glyph.copy()

    def _trace_callback(self, sender):
        if self.guide_layer is None:
            self._update_layers()
            return
        guide_glyph = self.glyph.getLayer(self.guide_layer)
        glyph = get_guide_representation(font=guide_glyph.font, angle=self.angle)
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

    def _setup_draw(self, preview=False):
        pass

    def _draw_preview_glyph(self, preview=False):
        raise NotImplementedError

    def save_to_lib(self, font_or_glyph, libkey, value):
        pass

    def load_from_lib(self, font_or_glyph, libkey, attr=None):
        pass

    def save_settings(self):
        has_local_settings = self.w.glyph_local.get()
        if has_local_settings:
            # print("Saving settings to", self.glyph)
            for setting, value in [
                (def_angle_key, degrees(self.angle)),
                (def_width_key, self.width),
                (def_height_key, self.height),
                (def_guide_key, self.guide_layer),
                (def_local_key, has_local_settings),
                (def_super_key, self.superness),
                (def_model_key, self.model),
            ]:
                self.save_to_lib(self.glyph, setting, value)
        else:
            for setting in [def_angle_key, def_width_key, def_height_key, def_guide_key, def_local_key]:
                self.save_to_lib(self.glyph, setting, None)
            # print("Saving settings to", self.font)
            for setting, value in [
                (def_angle_key, degrees(self.angle)),
                (def_width_key, self.width),
                (def_height_key, self.height),
                (def_guide_key, self.guide_layer),
                (def_super_key, self.superness),
                (def_model_key, self.model),
            ]:
                self.save_to_lib(self.font, setting, value)

    def load_settings(self):
        has_local_settings = self.load_from_lib(self.glyph, def_local_key)
        if has_local_settings:
            # print("Loading settings from glyph", self.glyph)
            self.w.glyph_local.set(True)
            angle = self.load_from_lib(self.glyph, def_angle_key)
            if angle is None:
                self.angle = 0
            else:
                self.angle = radians(angle)
            for setting, attr in [
                (def_width_key, "width"),
                (def_height_key, "height"),
                (def_guide_key, "guide_layer"),
                (def_super_key, "superness"),
                (def_model_key, "model"),
            ]:
                self.load_from_lib(self.glyph, setting, attr)
        else:
            # print("Loading settings from font", self.font)
            self.w.glyph_local.set(False)
            angle = self.load_from_lib(self.font, def_angle_key)
            if angle is None:
                self.angle = 0
            else:
                self.angle = radians(angle)
            for setting, attr in [
                (def_width_key, "width"),
                (def_height_key, "height"),
                (def_guide_key, "guide_layer"),
                (def_super_key, "superness"),
                (def_model_key, "model"),
            ]:
                self.load_from_lib(self.font, setting, attr)
        self._update_ui()
