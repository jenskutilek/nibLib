from __future__ import division, print_function

from math import degrees, pi, radians

import vanilla
from defconAppKit.windows.baseWindow import BaseWindowController

# RoboFont-internal packages
from lib.tools.extremePoints import ExtremePointPen
from mojo.drawingTools import *
from mojo.events import addObserver, removeObserver
from mojo.roboFont import CurrentFont, CurrentGlyph, RGlyph
from mojo.UI import UpdateCurrentGlyphView

from nibLib import DEBUG, def_angle_key, def_width_key, def_height_key, def_local_key, def_guide_key, def_super_key, def_model_key, rf_guide_key
from nibLib.pens import nib_models




def NibGuideGlyphFactory(glyph, font, angle):
	pen = ExtremePointPen(vertical = True, horizontal = True)
	g = RGlyph(glyph).copy()
	g.rotateBy(degrees(-angle))
	#g.extremePoints()
	g.drawPoints(pen)
	g.clear()
	out_pen = g.getPointPen()
	pen.drawPoints(out_pen)
	g.rotateBy(degrees(angle))
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
		registerRepresentationFactory(xxrf_guide_key, NibGuideGlyphFactory)
	else:
		if rf_guide_key not in Glyph.representationFactories:
			registerRepresentationFactory(Glyph, rf_guide_key, NibGuideGlyphFactory)



def _unregisterFactory():
	from defcon import unregisterRepresentationFactory, Glyph
	try:
		unregisterRepresentationFactory(Glyph, rf_guide_key)
	except:
		pass




class JKNib(BaseWindowController):
	
	def __init__(self):
		self.model = "Superellipse"
		self.angle  = radians(30)
		self.width  = 60
		self.height = 2
		self.superness = 2.5
		self.line_join = "round" # bevel, round
		self.guide_layer = None
		self.nib_pen = nib_models[self.model]
		
		self._draw_nib_faces = False
		self._draw_in_preview_mode = False
		
		self.glyph = CurrentGlyph()
		self.font = CurrentFont()
		if self.font is None:
			self.font_layers = []
		else:
			self.font_layers = self.font.layerOrder
		
		# window dimensions
		width = 300
		height = 322
		
		self.w = vanilla.FloatingWindow((width, height), "Nib Simulator")
		
		col = 60
		y = 10
		
		self.w.model_label  = vanilla.TextBox((8, y, col-8, 20), "Model")
		self.w.model_select = vanilla.PopUpButton((col, y, -48, 20),
			nib_models.keys(),
			callback = self._model_select_callback,
		)
		
		y += 32
		self.w.angle_label  = vanilla.TextBox((8, y, col-8, 20), "Angle")
		self.w.angle_slider = vanilla.Slider((col, y, -48, 20),
			minValue = 0,
			maxValue = pi,
			value = radians(30),
			tickMarkCount = 7,
			callback = self._nib_angle_callback,
			stopOnTickMarks = False,
		)
		self.w.angle_text  = vanilla.TextBox((-40, y, -8, 20), "%i" % int(round(degrees(self.angle))))
		
		y += 24
		
		self.w.width_label  = vanilla.TextBox((8, y, col-8, 20), "Width")
		self.w.width_slider = vanilla.Slider((col, y, -48, 20),
			minValue = 0,
			maxValue = 200,
			value = self.width,
			#tickMarkCount = 7,
			callback = self._nib_width_callback,
			#stopOnTickMarks = False,
		)
		self.w.width_text  = vanilla.TextBox((-40, y, -8, 20), "%i" % self.width)
		
		y += 24
		
		self.w.height_label  = vanilla.TextBox((8, y, col-8, 20), "Height")
		self.w.height_slider = vanilla.Slider((col, y, -48, 20),
			minValue = 1,
			maxValue = 200,
			value = self.height,
			#tickMarkCount = 7,
			callback = self._nib_height_callback,
			#stopOnTickMarks = False,
		)
		self.w.height_text  = vanilla.TextBox((-40, y, -8, 20), "%i" % self.height)
		
		y += 24
		
		self.w.superness_label  = vanilla.TextBox((8, y, col-8, 20), "Super")
		self.w.superness_slider = vanilla.Slider((col, y, -48, 20),
			minValue = 1.01,
			maxValue = 15.0,
			value = self.superness,
			callback = self._nib_superness_callback,
		)
		self.w.superness_text  = vanilla.TextBox((-40, y, -8, 20), "%0.2f" % self.superness)
		
		y += 32
		self.w.guide_label  = vanilla.TextBox((8, y, col-8, 20), "Guide")
		self.w.guide_select = vanilla.PopUpButton((col, y, -48, 20),
			[]
			#callback = self._guide_select_callback,
		)
		
		y += 32
		self.w.glyph_local = vanilla.CheckBox((col, y, -40, 20),
			"Glyph Uses Local Parameters",
			callback = self._glyph_local_callback,
			value=False,
		)
		
		y += 32
		self.w.display_label  = vanilla.TextBox((8, y, col-8, 20), "Display")
		self.w.draw_space = vanilla.CheckBox((col, y, -48, 20),
			"Draw In Space Center",
			callback = self._draw_space_callback,
			value=False,
		)
		
		y += 24
		self.w.draw_preview = vanilla.CheckBox((col, y, -48, 20),
			"Draw In Preview Mode",
			callback = self._draw_preview_callback,
			value=False,
		)
		
		y += 24
		self.w.draw_faces = vanilla.CheckBox((col, y, -48, 20),
			"Draw Nib Faces In RGB",
			callback = self._draw_faces_callback,
			value=False,
		)
		
		y += 32
		self.w.trace_outline = vanilla.Button((col, y, 120, 20),
			title = "Trace Outline",
			callback = self._trace_callback
		)
		
		self.observers = [
			("_preview", "drawBackground"),
			("_preview", "drawInactive"),
			("_previewFull", "drawPreview"),
			("_glyph_changed", "currentGlyphChanged"),
			("_font_changed", "fontBecameCurrent"),
			("_font_resign", "fontResignCurrent"),
		]
		
		self.setUpBaseWindowBehavior()
		self.addObservers()
		_registerFactory()
		self.load_settings()
		#self._update_ui()
		#self.w.trace_outline.enable(False)
		self.w.open()
		UpdateCurrentGlyphView()
	
	def windowCloseCallback(self, sender):
		if self.font is not None:
			self.save_settings()
		self.removeObservers()
		_unregisterFactory()
		UpdateCurrentGlyphView()
		super(JKNib, self).windowCloseCallback(sender)
	
	def addObservers(self):
		for method, observer in self.observers:
			addObserver(self, method, observer)
	
	def removeObservers(self):
		for method, observer in self.observers:
			removeObserver(self, observer)
		if self.w.draw_space.get():
			removeObserver(self, "spaceCenterDraw")
	
	def _update_layers(self):
		if self.font is None:
			self.font_layers = []
		else:
			self.font_layers = self.font.layerOrder
		self.w.guide_select.setItems(self.font_layers)
		if self.font_layers:
			last_layer = len(self.font_layers) - 1
			self.w.guide_select.set(last_layer)
			self.guide_layer = self.font_layers[last_layer]
	
	def _update_ui(self):
		#print("_update_ui")
		i = 0
		for i, model in enumerate(self.w.model_select.getItems()):
			if model == self.model:
				break
		self.w.model_select.set(i)
		self.nib_pen = nib_models[self.model]
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
		UpdateCurrentGlyphView()
	
	def _nib_angle_callback(self, sender):
		angle = int(round(degrees(sender.get())))
		self.angle = radians(angle)
		self.w.angle_text.set("%i" % angle)
		UpdateCurrentGlyphView()
	
	def _nib_width_callback(self, sender):
		self.width = int(round(sender.get()))
		self.w.width_text.set("%i" % self.width)
		self.w.height_slider.setMaxValue(self.width)
		UpdateCurrentGlyphView()
	
	def _nib_height_callback(self, sender):
		self.height = int(round(sender.get()))
		self.w.height_text.set("%i" % self.height)
		self.w.width_slider.setMinValue(self.height)
		UpdateCurrentGlyphView()
	
	def _nib_superness_callback(self, sender):
		self.superness = sender.get()
		self.w.superness_text.set("%0.2f" % self.superness)
		UpdateCurrentGlyphView()
	
	def _glyph_local_callback(self, sender):
		value = sender.get()
		#print("Local:", value)
		self.save_to_lib(self.glyph, def_local_key, False)
		if not value:
			self.load_settings()
	
	def _draw_space_callback(self, sender):
		value = sender.get()
		if value:
			addObserver(self, "_previewFull", "spaceCenterDraw")
		else:
			removeObserver(self, "spaceCenterDraw")
	
	def _draw_preview_callback(self, sender):
		self._draw_in_preview_mode = sender.get()
		UpdateCurrentGlyphView()
	
	def _draw_faces_callback(self, sender):
		self._draw_nib_faces = sender.get()
		UpdateCurrentGlyphView()
	
	def _trace_callback(self, sender):
		if self.guide_layer is None:
			self._update_layers()
			return
		guide_glyph = CurrentGlyph().getLayer(self.guide_layer)
		glyph = guide_glyph.getRepresentation(rf_guide_key, font=guide_glyph.font, angle=self.angle)
		p = self.nib_pen(self.font, self.angle, self.width, self.height, self._draw_nib_faces, nib_superness=self.superness, trace=True)
		glyph.draw(p)
		p.trace_path(CurrentGlyph())
	
	def _setup_draw(self, preview=False):
		if preview:
			fill(0)
			stroke(0)
		else:
			fill(0.6, 0.7, 0.9, 0.5)
			stroke(0.6, 0.7, 0.9)
		#strokeWidth(self.height)
		#strokeWidth(1)
		strokeWidth(0)
		stroke(None)
		lineJoin(self.line_join)
	
	def _draw_preview(self, notification, preview=False):
		if self.guide_layer is None:
			self._update_layers()
			return
		#try:
		guide_glyph = notification["glyph"].getLayer(self.guide_layer)
		glyph = guide_glyph.getRepresentation(rf_guide_key, font=guide_glyph.font, angle=self.angle)
		save()
		self._setup_draw(preview=preview)
		# TODO: Reuse pen object. Needs modifications to the pens before possible.
		p = self.nib_pen(self.font, self.angle, self.width, self.height, self._draw_nib_faces, nib_superness=self.superness)
		glyph.draw(p)
		restore()
		#except:
		#    pass
	
	def _preview(self, notification):
		self._draw_preview(notification, False)
	
	def _previewFull(self, notification):
		if self._draw_in_preview_mode:
			self._draw_preview(notification, True)
	
	def _glyph_changed(self, notification):
		#print("Glyph changed")
		if self.glyph is not None:
			self.save_settings()
		self.glyph = notification["glyph"]
		self.font = CurrentFont()
		self.font_layers = self.font.layerOrder
		#print(self.font)
		if self.glyph is not None:
			self.load_settings()
	
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
		if font_or_glyph is None or attr is None:
			return False
		value = font_or_glyph.lib[libkey] if libkey in font_or_glyph.lib else None
		if value is not None:
			setattr(self, attr, value)
		return value
	
	def save_settings(self):
		has_local_settings = self.w.glyph_local.get()
		if has_local_settings:
			#print("Saving settings to", self.glyph)
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
			#print("Saving settings to", self.font)
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
			#print("Loading settings from glyph", self.glyph)
			self.w.glyph_local.set(True)
			self.angle = radians(self.load_from_lib(self.glyph, def_angle_key))
			for setting, attr in [
				(def_width_key, "width"),
				(def_height_key, "height"),
				(def_guide_key, "guide_layer"),
				(def_super_key, "superness"),
				(def_model_key, "model"),
			 ]:
				self.load_from_lib(self.glyph, setting, attr)
		else:
			#print("Loading settings from font", self.font)
			self.w.glyph_local.set(False)
			angle = self.load_from_lib(self.font, def_angle_key)
			if angle is not None:
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
	
	def _font_resign(self, notification=None):
		self.save_settings()
	
	def _font_changed(self, notification):
		self.font = notification["font"]
		if self.font is None:
			self.font_layers = []
		else:
			self.font_layers = self.font.layerOrder
