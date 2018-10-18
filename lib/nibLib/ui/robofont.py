from __future__ import division, print_function

# RoboFont-internal packages
from lib.tools.extremePoints import ExtremePointPen
from mojo.drawingTools import *
from mojo.events import addObserver, removeObserver
from mojo.roboFont import CurrentFont, CurrentGlyph, RGlyph
from mojo.UI import UpdateCurrentGlyphView

from nibLib.ui import JKNib
from nibLib import DEBUG, rf_guide_key



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




class JKNibRoboFont(JKNib):
	
	def __init__(self):
		super(JKNibRoboFont, self).__init__(CurrentGlyph(), CurrentFont())

	def envSpecificInit(self):
		self.setUpBaseWindowBehavior()
		self.addObservers()
		_registerFactory()
		UpdateCurrentGlyphView()
	
	def envSpecificQuit(self):
		self.removeObservers()
		_unregisterFactory()
		UpdateCurrentGlyphView()
	
	def addObservers(self):
		for method, observer in self.observers:
			addObserver(self, method, observer)
	
	def removeObservers(self):
		for method, observer in self.observers:
			removeObserver(self, observer)
		if self.w.draw_space.get():
			removeObserver(self, "spaceCenterDraw")
	
	def getLayerList(self):
		return self.font.layerOrder
	
	def _draw_space_callback(self, sender):
		# RF-specific: Draw in space center
		value = sender.get()
		if value:
			addObserver(self, "_previewFull", "spaceCenterDraw")
		else:
			removeObserver(self, "spaceCenterDraw")

	def get_guide_representation(self, glyph, font, angle):
		return self.glyph.getLayer(
			self.guide_layer
		).getRepresentation(
			rf_guide_key, font=font, angle=angle
		)
	
	def _trace_callback(self, sender):
		if self.guide_layer is None:
			self._update_layers()
			return
		guide_glyph = self.glyph.getLayer(self.guide_layer)
		glyph = get_guide_representation(font=guide_glyph.font, angle=self.angle)
		p = self.nib_pen(self.font, self.angle, self.width, self.height, self._draw_nib_faces, nib_superness=self.superness, trace=True)
		glyph.draw(p)
		p.trace_path(self.glyph)

	def _draw_preview(self, notification, preview=False):
		self._draw_preview_glyph(preview=preview)
	
	def _preview(self, notification):
		self._draw_preview_glyph(False)
	
	def _previewFull(self, notification):
		if self._draw_in_preview_mode:
			self._draw_preview_glyph(True)
	
	def _glyph_changed(self, notification):
		#print("Glyph changed")
		if self.glyph is not None:
			self.save_settings()
		self.glyph = notification["glyph"]
		self.font = CurrentFont()
		self.font_layers = self.self.getLayerList()
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
	
	def _font_resign(self, notification=None):
		self.save_settings()
	
	def _font_changed(self, notification):
		self.font = notification["font"]
		if self.font is None:
			self.font_layers = []
		else:
			self.font_layers = self.self.getLayerList()
