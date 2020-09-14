# RoboFont-internal packages
# from lib.tools.extremePoints import ExtremePointPen
# from math import degrees
from mojo.drawingTools import fill, lineJoin, restore, save, strokeWidth, stroke
from mojo.events import addObserver, removeObserver
from mojo.roboFont import CurrentFont, CurrentGlyph, RGlyph
from mojo.UI import UpdateCurrentGlyphView

from math import atan2, degrees, pi, radians
import vanilla
from defconAppKit.windows.baseWindow import BaseWindowController

from nibLib import DEBUG, def_angle_key, def_width_key, def_height_key, \
    def_local_key, def_guide_key, def_super_key, def_model_key, \
    rf_guide_key



from mojo.drawingTools import *
from AppKit import NSBezierPath, NSColor


from nibLib.pens.nibPen import NibPen
from collections import namedtuple

from fontTools.misc.bezierTools import (
    calcCubicParameters,
    solveQuadratic,
    splitCubicAtT,
    epsilon,
)
from fontTools.misc.transform import Transform


Root = namedtuple("Root", ["t", "direction"])


def split_at_extrema(pt1, pt2, pt3, pt4, transform=Transform()):
    """
    Add extrema to a cubic curve, after applying a transformation.
    Example ::

        >>> # A segment in which no extrema will be added.
        >>> split_at_extrema((297, 52), (406, 52), (496, 142), (496, 251))
        [(((297, 52), (406, 52), (496, 142), (496, 251)), None)]
        >>> from fontTools.misc.transform import Transform
        >>> split_at_extrema((297, 52), (406, 52), (496, 142), (496, 251), Transform().rotate(-27))
        [(((297.0, 52.0), (84.48072108963274, -212.56513799170233), (15.572491694678519, -361.3686192413668), (15.572491694678547, -445.87035970621713)), 'h'), (((15.572491694678547, -445.8703597062171), (15.572491694678554, -506.84825401175414), (51.4551516055374, -534.3422304091257), (95.14950889754756, -547.6893014808263)), False)]
    """
    # Transform the points for extrema calculation;
    # transform is expected to rotate the points by - nib angle.
    t2, t3, t4 = transform.transformPoints([pt2, pt3, pt4])
    # When pt1 is the current point of the path,  it is already transformed, so
    # we keep it like it is.
    t1 = pt1

    (ax, ay), (bx, by), c, d = calcCubicParameters(t1, t2, t3, t4)
    ax *= 3.0
    ay *= 3.0
    bx *= 2.0
    by *= 2.0

    # vertical
    roots = [
        Root(t=t, direction="v")
        for t in solveQuadratic(ay, by, c[1])
        if 0 < t < 1
    ]

    # horizontal
    roots += [
        Root(t=t, direction="h")
        for t in solveQuadratic(ax, bx, c[0])
        if 0 < t < 1
    ]

    # Use only unique roots and sort them
    # They should be unique before, or can a root be duplicated (in h and v?)
    roots = sorted(set(roots))

    if not roots:
        return [((t1, t2, t3, t4), None)]

    # print("Roots:", roots)
    # Split transformed segment at roots (remove annotation first)
    split_segments = splitCubicAtT(t1, t2, t3, t4, *[r.t for r in roots])
    # print("Split:", split_segments)

    # Annotate the list of segments with extremum type again
    split_segments_annotated = [
        *[(s, roots[i][1]) for i, s in enumerate(split_segments[:-1])],
        (split_segments[-1], False),
    ]
    # print(split_segments_annotated)
    return split_segments_annotated



class RectNibPen(NibPen):
    def addPath(self, path=[]):
        """
        Add a path to the nib path.
        """
        if path:
            path = [
                self.transform_reverse.transformPoints(pts) for pts in path
            ]
            if self.trace:
                self.path.append(path)
            else:
                self.drawPath(path)

    def drawPath(self, path=[]):
        """
        Draw the points from path to a NSBezierPath.
        """
        subpath = NSBezierPath.alloc().init()
        subpath.moveToPoint_(path[0][0])
        for p in path[1:]:
            if len(p) == 3:
                # curve
                A, B, C = p
                subpath.curveToPoint_controlPoint1_controlPoint2_(C, A, B)
            else:
                subpath.lineToPoint_(p[0])

        subpath.closePath()
        NSColor.colorWithCalibratedRed_green_blue_alpha_(
            0, 0, 1, self.alpha
        ).set()
        subpath.stroke()

    def transformPoint(self, pt, d=1):
        return (
            pt[0] + self.a * d,
            pt[1] + self.b,
        )

    def transformPointHeight(self, pt, d=1):
        return (
            pt[0] + self.a * d,
            pt[1] - self.b,
        )

    def transformedRect(self, P):
        """
        Transform a point to a rect describing the four points of the nib face.

          D-------------------------C
          |            P            |
          A-------------------------B
        """
        A = self.transformPointHeight(P, -1)
        B = self.transformPointHeight(P)
        C = self.transformPoint(P)
        D = self.transformPoint(P, -1)
        return A, B, C, D

    def _moveTo(self, pt):
        t = self.transform.transformPoint(pt)
        self.__currentPoint = t
        self.contourStart = pt

    def _lineTo(self, pt):
        """
        Points of the nib face:

        D1                           C1     D2                           C2
          X-------------------------X         X-------------------------X
          |            X            | ------> |            X            |
          X-------------------------X         X-------------------------X
        A1                           B1     A2                           B2

        The points A2, B2, C2, D2 are the points of the nib face translated to
        the end of the current stroke.
        """
        t = self.transform.transformPoint(pt)

        A1, B1, C1, D1 = self.transformedRect(self.__currentPoint)
        A2, B2, C2, D2 = self.transformedRect(t)

        x1, y1 = self.__currentPoint
        x2, y2 = t

        # Angle between nib and path
        rho = atan2(y2 - y1, x2 - x1)

        path = None
        Q = rho / pi

        if 0 <= Q < 0.5:
            path = ((A1,), (B1,), (B2,), (C2,), (D2,), (D1,))

        elif 0.5 <= Q <= 1:
            path = ((A1,), (B1,), (C1,), (C2,), (D2,), (A2,))

        elif -1 <= Q < -0.5:
            path = ((A2,), (B2,), (B1,), (C1,), (D1,), (D2,))

        elif -0.5 <= Q < 0:
            path = ((A2,), (B2,), (C2,), (C1,), (D1,), (A1,))

        self.addPath(path)

        self.__currentPoint = t

    def _curveToOne(self, pt1, pt2, pt3):
        # Insert extrema at angle
        segments = split_at_extrema(
            self.__currentPoint, pt1, pt2, pt3, transform=self.transform
        )
        prev_direction = False
        for segment, direction in segments:
            pt0, pt1, pt2, pt3 = segment
            self._curveToOneNoExtrema(pt1, pt2, pt3, prev_direction, direction)
            prev_direction = direction

    def _curveToOneNoExtrema(self, pt1, pt2, pt3, direction_left=False, direction_right=False):
        print("_curveToOneNoExtrema", pt1, pt2, pt3, direction_left, direction_right)

        A1, B1, C1, D1 = self.transformedRect(self.__currentPoint)

        # Control points
        Ac1, Bc1, Cc1, Dc1 = self.transformedRect(pt1)
        Ac2, Bc2, Cc2, Dc2 = self.transformedRect(pt2)

        # End points
        A2, B2, C2, D2 = self.transformedRect(pt3)

        # Angle at start of curve
        x0, y0 = self.__currentPoint
        x1, y1 = pt1
        rho1 = atan2(y1 - y0, x1 - x0)

        # Angle at end of curve
        x2, y2 = pt2
        x3, y3 = pt3

        rho2 = atan2(y3 - y2, x3 - x2)

        path = None

        def normalize_quadrant(q):
            r = 2 * q
            nearest_integer = round(r)
            e = abs(nearest_integer - r)
            if e > epsilon:
                return q
            rounded = nearest_integer * 0.5
            # if rounded == -1:
            #     return 1
            return rounded

        Q1 = (rho1 / pi)
        Q2 = (rho2 / pi)
        print(f"       Q1: {Q1}, Q2: {Q2}")
        Q1 = normalize_quadrant(rho1 / pi)
        Q2 = normalize_quadrant(rho2 / pi)
        print(f"    -> Q1: {Q1}, Q2: {Q2}")

        """
        Points of the nib face:

        D1                           C1     D2                           C2
          X-------------------------X         X-------------------------X
          |            X            | ------> |            X            |
          X-------------------------X         X-------------------------X
        A1                           B1     A2                           B2

        The points A2, B2, C2, D2 are the points of the nib face translated to
        the end of the current stroke.
        """
        if Q1 == 0:
            if Q2 == 0:
                path = ((A1,), (B1,), (Bc1, Bc2, B2), (C2,), (D2,), (Dc2, Dc1, D1))
            elif 0 < Q2 < 0.5:
                path = ((B2,), (C2,), (Cc2, Cc1, C1), (D1,), (A1,), (Ac1, Ac2, A2))
            elif 0.5 <= Q2 <= 1:
                path = ((A1,), (B1,), (Bc1, Bc2, B2), (C2,), (D2,), (Dc2, Dc1, D1))
            elif -1 < Q2 < -0.5:
                pass
            elif -0.5 <= Q2 < 0:
                path = ((B2,), (C2,), (Cc2, Cc1, C1), (D1,), (A1,), (Ac1, Ac2, A2))

        elif 0 < Q1 < 0.5:
            if Q2 == 0:
                path = ((A1,), (B1,), (Bc1, Bc2, B2), (C2,), (D2,), (Dc2, Dc1, D1))
            elif 0 <= Q2 < 0.5:
                path = ((A1,), (B1,), (Bc1, Bc2, B2), (C2,), (D2,), (Dc2, Dc1, D1))
            elif 0.5 <= Q2 <= 1:
                path = ((A1,), (B1,), (Bc1, Bc2, B2), (C2,), (D2,), (Dc2, Dc1, D1))
            elif -1 < Q2 < -0.5:
                pass
            elif -0.5 <= Q2 < 0:
                path = ((B2,), (C2,), (Cc2, Cc1, C1), (D1,), (A1,), (Ac1, Ac2, A2))
        
        elif Q1 == 0.5:
            if 0 <= Q2 < 0.5:
                path = ((A1,), (B1,), (Bc1, Bc2, B2), (C2,), (D2,), (Dc2, Dc1, D1))
            elif Q2 == 0.5:
                path = ((A1,), (B1,), (Bc1, Bc2, B2), (C2,), (D2,), (Dc2, Dc1, D1))
            elif 0.5 <= Q2 <= 1:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif Q2 == -1:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))

        elif 0.5 < Q1 < 1:
            if 0 <= Q2 < 0.5:
                path = ((A1,), (B1,), (Bc1, Bc2, B2), (C2,), (D2,), (Dc2, Dc1, D1))
            elif 0.5 <= Q2 <= 1:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif Q2 == -1:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif -1 < Q2 < -0.5:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif -0.5 <= Q2 < 0:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))

        elif Q1 == 1:
            if 0 <= Q2 < 0.5:
                path = ((A1,), (B1,), (Bc1, Bc2, B2), (C2,), (D2,), (Dc2, Dc1, D1))
            elif Q2 == 0.5:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif 0.5 < Q2 < 1:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif Q2 == 1:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif Q2 == -1:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif -1 < Q2 < -0.5:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif -0.5 <= Q2 < 0:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))

        elif Q1 == -1:
            if 0 <= Q2 < 0.5:
                path = ((A1,), (B1,), (Bc1, Bc2, B2), (C2,), (D2,), (Dc2, Dc1, D1))
            elif Q2 == 0.5:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif 0.5 < Q2 < 1:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif Q2 == 1:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif Q2 == -1:
                path = ((B1,), (C1,), (Cc1, Cc2, C2), (D2,), (A2,), (Ac2, Ac1, A1))
            elif -1 < Q2 < -0.5:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif -0.5 <= Q2 < 0:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
        
        elif -1 < Q1 < -0.5:
            if 0 <= Q2 < 0.5:
                print("Crash")
            elif 0.5 <= Q2 <= 1:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif Q2 == -1:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif -1 < Q2 < -0.5:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif -0.5 <= Q2 < 0:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))

        elif Q1 == -0.5:
            if Q2 == -1:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif -1 < Q2 < -0.5:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif Q2 == -0.5:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif -0.5 <= Q2 < 0:
                path = ((B2,), (C2,), (Cc2, Cc1, C1), (D1,), (A1,), (Ac1, Ac2, A2))
            elif Q2 == 0.0:
                path = ((B2,), (C2,), (Cc2, Cc1, C1), (D1,), (A1,), (Ac1, Ac2, A2))
            elif Q2 == 1:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))

        elif -0.5 <= Q1 < 0:
            if 0 <= Q2 < 0.5:
                path = ((B2,), (C2,), (Cc2, Cc1, C1), (D1,), (A1,), (Ac1, Ac2, A2))
            elif 0.5 <= Q2 <= 1:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif Q2 == -1:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif -1 < Q2 < -0.5:
                path = ((A2,), (B2,), (Bc2, Bc1, B1), (C1,), (D1,), (Dc1, Dc2, D2))
            elif -0.5 <= Q2 < 0:
                path = ((B2,), (C2,), (Cc2, Cc1, C1), (D1,), (A1,), (Ac1, Ac2, A2))


        self.addPath(path)

        self.__currentPoint = pt3

    def _closePath(self):
        # Glyphs calls closePath though it is not really needed there ...?
        self._lineTo(self.contourStart)
        self.__currentPoint = None

    def _endPath(self):
        if self.__currentPoint:
            # A1, B1, C1, D1 = self.transformedRect(self.__currentPoint)
            # self.addPath(((A1,), (B1,), (C1,), (D1,)))
            self.__currentPoint = None


nib_models = {
    "Rectangle"   : RectNibPen,
}













class JKNib(BaseWindowController):

    def __init__(self, glyph, font):
        self.model = "Rectangle"
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
