# RoboFont-internal packages
# from lib.tools.extremePoints import ExtremePointPen
# from math import degrees
from mojo.drawingTools import fill, lineJoin, restore, save, strokeWidth, stroke
from mojo.events import addObserver, removeObserver
from mojo.roboFont import CurrentFont, CurrentGlyph, RGlyph
from mojo.UI import UpdateCurrentGlyphView

from math import cos, degrees, pi, sin, radians
import operator

import vanilla
from defconAppKit.windows.baseWindow import BaseWindowController

from nibLib import DEBUG, def_angle_key, def_width_key, def_height_key, \
    def_local_key, def_guide_key, def_super_key, def_model_key, \
    rf_guide_key


DEBUG_CENTER_POINTS = False
DEBUG_CURVE_POINTS = False


from beziers.path import BezierPath as SCBezierPath
from beziers.point import Point as SCPoint

from mojo.drawingTools import *
from AppKit import NSBezierPath, NSColor

import beziers

from nibLib.geometry import (
    angleBetweenPoints,
    getPointsFromCurve,
    optimizePointPath,
)
from nibLib.pens.ovalNibPen import OvalNibPen

from fontTools.misc.bezierTools import (
    calcCubicParameters,
    solveQuadratic,
    splitCubicAtT,
    epsilon,
)
from fontTools.misc.transform import Transform


class SuperellipseNibPen(OvalNibPen):
    def setup_nib(self):
        steps = 100
        points = []
        # Build a quarter of the superellipse with the requested number of steps
        for i in range(0, steps + 1):
            t = i * 0.5 * pi / steps
            points.append(
                (
                    self.a * cos(t) ** (2 / self.nib_superness),
                    self.b * sin(t) ** (2 / self.nib_superness),
                )
            )
        try:
            points = optimizePointPath(points, 0.02)
        except:
            print("Error optimizing point path.")
            pass

        # Just add the remaining three quarters by transposing the existing points
        points.extend([(-p[0], p[1]) for p in reversed(points)])
        points.extend([(p[0], -p[1]) for p in reversed(points)])

        self.nib_face_path = points
        self.nib_face_path_transformed = points.copy()
        self.nib_drawing_path = self._curve_from_lines(points)
        self.nib_drawing_path_transformed = self.nib_drawing_path.copy()
        self.cache_angle = None

    def _get_rotated_point(self, pt, phi):
        x, y = pt
        cp = cos(phi)
        sp = sin(phi)
        x1 = x * cp - y * sp
        y1 = x * sp + y * cp

        return x1, y1

    def transform_nib_path(self, alpha):
        t = Transform().rotate(-alpha)
        self.nib_face_path_transformed = t.transformPoints(self.nib_face_path)
        self.cache_angle = alpha

    def _get_tangent_point(self, alpha):

        # Calculate the point on the superellipse
        # at the given tangent angle alpha.

        # For now, we do this the pedestrian way, until I can figure out
        # how to calculate the tangent point directly.

        if self.cache_angle != alpha:
            self.transform_nib_path(alpha)

        x, y = max(self.nib_face_path_transformed, key=operator.itemgetter(1))
        x, y = Transform().rotate(alpha).transformPoint((x, y)) # .rotate(-self.angle)
        return x, y

    def _moveTo(self, pt):
        t = self.transform.transformPoint(pt)
        self.__currentPoint = t
        self.contourStart = pt
        self._draw_nib_face(pt)

    def _lineTo(self, pt):
        t = self.transform.transformPoint(pt)

        # angle from the previous to the current point
        phi = angleBetweenPoints(self.__currentPoint, t)
        # print(u"%0.2f°: %s -> %s" % (degrees(phi), self.__currentPoint, pt))

        x, y = self._get_tangent_point(phi)

        p0 = (self.__currentPoint[0] + x, self.__currentPoint[1] + y)
        p1 = (t[0] + x, t[1] + y)
        p2 = (t[0] - x, t[1] - y)
        p3 = (self.__currentPoint[0] - x, self.__currentPoint[1] - y)

        self.addPath([[p0], [p3], [p2], [p1]])
        self._draw_nib_face(pt)

        self.__currentPoint = t

    def _curveToOne(self, pt1, pt2, pt3):
        if not self.trace and DEBUG_CENTER_POINTS or DEBUG_CURVE_POINTS:
            save()
        
        t1 = self.transform.transformPoint(pt1)
        t2 = self.transform.transformPoint(pt2)
        t3 = self.transform.transformPoint(pt3)

        # Break curve into line segments
        points = getPointsFromCurve((self.__currentPoint, t1, t2, t3), 5)

        # Draw points of center line
        if DEBUG_CENTER_POINTS:
            stroke(None)
            strokeWidth(0)
            fill(0, 0, 0, self.alpha)
            for p in points:
                x, y = self.transform_reverse.transformPoint(p)
                rect(x - 1, y - 1, 2, 2)

        # Calculate angles between points

        # The first angle is that of the curve start point to bcp1
        angles = [angleBetweenPoints(self.__currentPoint, t1)]

        for i in range(1, len(points)):
            phi = angleBetweenPoints(points[i - 1], points[i])
            angles.append(phi)

        # The last angle is that of bcp2 point to the curve end point
        angles.append(angleBetweenPoints(t2, t3))

        # Find points on ellipse for each angle
        inner = []
        outer = []

        # stroke(None)
        for i, p in enumerate(points):
            x, y = self._get_tangent_point(angles[i])

            pp = self._get_rotated_point((p[0] + x, p[1] + y), self.angle)
            outer.append(pp)

            if not self.trace and DEBUG_CURVE_POINTS:
                # Draw outer points in red
                fill(1, 0, 0, self.alpha)
                pr = self.transform_reverse.transformPoint((p[0] + x, p[1] + y))
                rect(pr[0] - 1, pr[1] - 1, 2, 2)

            pp = self._get_rotated_point((p[0] - x, p[1] - y), self.angle)
            inner.append(pp)
            if not self.trace and DEBUG_CURVE_POINTS:
                # Draw inner points in green
                fill(0, 0.8, 0, self.alpha)
                pr = self.transform_reverse.transformPoint((p[0] - x, p[1] - y))
                rect(pr[0] - 1, pr[1] - 1, 2, 2)

        if inner and outer:
            if self.trace:
                outer.reverse()
                outer = self._curve_from_lines(outer)
                inner = self._curve_from_lines(inner)
                self.path.append(outer + inner)
            else:
                inner = optimizePointPath(inner, 0.3)
                outer = optimizePointPath(outer, 0.3)
                outer.reverse()
                optimized = optimizePointPath(outer + inner, 1)
                self.addPath([[self.transform.transformPoint(o)] for o in optimized])
            self._draw_nib_face(pt3)

        self.__currentPoint = t3
        if not self.trace and DEBUG_CENTER_POINTS or DEBUG_CURVE_POINTS:
            restore()

    def _closePath(self):
        self.lineTo(self.contourStart)
        self.__currentPoint = None

    def _endPath(self):
        self.__currentPoint = None

    def _draw_nib_face(self, pt):
        if self.trace:
            x, y = pt
            nib = []
            t = Transform().translate(x, y).rotate(self.angle)
            for seg in self.nib_drawing_path:
                seg_path = []
                for p in seg:
                    seg_path.append(t.transformPoint(p))
                nib.append(seg_path)
            self.path.append(nib)
        else:
            save()
            translate(pt[0], pt[1])
            rotate(degrees(self.angle))
            newPath()
            moveTo(self.nib_face_path[0])
            for p in self.nib_face_path[1:]:
                lineTo(p)
            closePath()
            drawPath()
            restore()
    
    def _curve_from_lines(self, point_tuple_list: list) -> list:
        error=50.0
        cornerTolerance=20.0
        maxSegments=20
        curve_points = SCBezierPath().fromPoints(
            [SCPoint(p[0], p[1]) for p in point_tuple_list],
            error=1.0,
            cornerTolerance=1.0,
            maxSegments=10000,
        )

        # Reconvert the BezierPath segments to our segment type
        point_tuple_list = []
        first = True
        for segment in curve_points.asSegments():
            segment_tuple = []
            if first:
                # For the first segment, add the move point
                p = segment[0]
                point_tuple_list.append([(p.x, p.y)])
            for p in segment[1:]:
                segment_tuple.append((p.x, p.y))
            point_tuple_list.append(segment_tuple)
        return point_tuple_list

    def trace_path(self, out_glyph):
        from mojo.roboFont import RGlyph

        tmp = RGlyph()
        p = tmp.getPen()
        first = True
        for path in self.path:
            if first:
                first = False
            else:
                p.closePath()
                out_glyph.appendGlyph(tmp)
                tmp.clear()
            p.moveTo(self.round_pt(path[0][0]))
            for segment in path[1:]:
                if len(segment) == 1:
                    p.lineTo(self.round_pt(segment[0]))
                elif len(segment) == 3:
                    p.curveTo(
                        self.round_pt(segment[0]),
                        self.round_pt(segment[1]),
                        self.round_pt(segment[2]),
                    )

                else:
                    print("Unknown segment type:", segment)
        p.closePath()
        # tmp.correctDirection()
        out_glyph.appendGlyph(tmp)
        # out_glyph.removeOverlap()
        # out_glyph.removeOverlap()
        out_glyph.update()


nib_models = {
    "Superellipse"   : SuperellipseNibPen,
}













class JKNib(BaseWindowController):

    def __init__(self, glyph, font):
        self.model = "Superellipse"
        self.angle = radians(30)
        self.width = 60
        self.height = 2
        self.superness = 2.5
        self.line_join = "round" # bevel, round
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

        self.w.model_label  = vanilla.TextBox((8, y, col-8, 20), "Model")
        self.w.model_select = vanilla.PopUpButton(
            (col, y, -48, 20),
            nib_models.keys(),
            callback=self._model_select_callback,
        )

        y += 32
        self.w.angle_label  = vanilla.TextBox((8, y, col-8, 20), "Angle")
        self.w.angle_slider = vanilla.Slider(
            (col, y, -48, 20),
            minValue=0,
            maxValue=pi,
            value=radians(30),
            tickMarkCount=7,
            callback=self._nib_angle_callback,
            stopOnTickMarks=False,
        )
        self.w.angle_text = vanilla.TextBox((-40, y, -8, 20), "%i" % int(round(degrees(self.angle))))

        y += 24

        self.w.width_label = vanilla.TextBox((8, y, col-8, 20), "Width")
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

        self.w.height_label = vanilla.TextBox((8, y, col-8, 20), "Height")
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

        self.w.superness_label = vanilla.TextBox((8, y, col-8, 20), "Super")
        self.w.superness_slider = vanilla.Slider(
            (col, y, -48, 20),
            minValue=1.01,
            maxValue=15.0,
            value=self.superness,
            callback=self._nib_superness_callback,
        )
        self.w.superness_text = vanilla.TextBox(
            (-40, y, -8, 20),
            "%0.2f" % self.superness
        )

        y += 32
        self.w.guide_label = vanilla.TextBox((8, y, col-8, 20), "Guide")
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
        self.w.display_label = vanilla.TextBox((8, y, col-8, 20), "Display")
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
        self.w.trace_outline = vanilla.Button(
            (col, y, 120, 20),
            title="Trace Outline",
            callback=self._trace_callback
        )

        self.envSpecificInit()
        # self.check_secondary_ui()
        self._update_ui()
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
        if self.font is None:
            self.font_layers = []
        else:
            self.font_layers = self.getLayerList()
        self.w.guide_select.setItems(self.font_layers)
        if self.font_layers:
            last_layer = len(self.font_layers) - 1
            self.w.guide_select.set(last_layer)
            self.guide_layer = self.font_layers[last_layer]

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
                self.w.guide_select.set(
                    self.font_layers.index(self.guide_layer)
                )
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
        glyph = self.get_guide_representation(
            glyph=guide_glyph,
            font=guide_glyph.font,
            angle=self.angle
        )
        p = self.nib_pen(
            self.font,
            self.angle,
            self.width,
            self.height,
            self._draw_nib_faces,
            nib_superness=self.superness,
            trace=True
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
            for setting in [
                def_angle_key,
                def_width_key,
                def_height_key,
                def_guide_key,
                def_local_key
            ]:
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
            registerRepresentationFactory(
                Glyph,
                rf_guide_key,
                NibGuideGlyphFactory
            )


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
        super(JKNibRoboFont, self).__init__(
            CurrentGlyph(),
            CurrentFont()
        )

    def envSpecificInit(self):
        self.setUpBaseWindowBehavior()
        self.addObservers()
        _registerFactory()
        self._update_layers()
        self.load_settings()
        self._update_current_glyph_view()

    def envSpecificQuit(self):
        self.removeObservers()
        _unregisterFactory()
        self._update_current_glyph_view()

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
        return glyph.getLayer(
            self.guide_layer
        ).getRepresentation(
            rf_guide_key, font=font, angle=angle
        )

    def _trace_callback(self, sender):
        if self.guide_layer is None:
            self._update_layers()
            return
        guide_glyph = self.glyph.getLayer(self.guide_layer)
        glyph = self.get_guide_representation(
            glyph=guide_glyph,
            font=guide_glyph.font,
            angle=self.angle
        )
        p = self.nib_pen(
            self.font,
            self.angle,
            self.width,
            self.height,
            self._draw_nib_faces,
            nib_superness=self.superness,
            trace=True
        )
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

    def _draw_preview_glyph(self, preview=False):
        if self.guide_layer is None:
            self._update_layers()
            return
        guide_glyph = self.glyph.getLayer(self.guide_layer)
        glyph = self.get_guide_representation(
            glyph=guide_glyph,
            font=guide_glyph.font,
            angle=self.angle
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
            nib_superness=self.superness
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


OpenWindow(JKNibRoboFont)
