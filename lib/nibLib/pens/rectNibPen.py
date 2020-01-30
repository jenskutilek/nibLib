from __future__ import division, print_function

from math import cos, pi, sin

try:
    from mojo.drawingTools import *
except ImportError:
    from GlyphsApp.drawingTools import *

from nibLib.pens.nibPen import NibPen


class RectNibPen(NibPen):

    def transformPoint(self, pt, d=1):
        return(
            pt[0] + self.a * d * cos(self.angle) + self.b * cos(pi/2 + self.angle),
            pt[1] + self.a * d * sin(self.angle) + self.b * sin(pi/2 + self.angle)
        )

    def transformPointHeight(self, pt, d=1):
        return (
            pt[0] + self.a * d * cos(self.angle) - self.b * cos(pi/2 + self.angle),
            pt[1] + self.a * d * sin(self.angle) - self.b * sin(pi/2 + self.angle)
        )

    def _moveTo(self, pt):
        # moveTo(pt)
        self.__currentPoint = pt
        self.contourStart = pt

    def _lineTo(self, pt):

        b1 = self.transformPoint(self.__currentPoint, -1)
        b2 = self.transformPoint(pt, -1)
        b3 = self.transformPoint(pt)
        b4 = self.transformPoint(self.__currentPoint)

        r1 = self.transformPointHeight(self.__currentPoint, -1)
        r2 = self.transformPointHeight(pt, -1)
        r3 = self.transformPointHeight(pt)
        r4 = self.transformPointHeight(self.__currentPoint)

        if self.color and not self.trace:
            save()
            fill(0, 0, 1, self.alpha)
        newPath()
        moveTo(b1)
        lineTo(b2)
        lineTo(b3)
        lineTo(b4)
        closePath()
        if not self.trace:
            drawPath()

        if self.trace:
            self.path.append([(b1), (b2), (b3), (b4)])
        elif self.color:
            fill(1, 0, 0, self.alpha)

        newPath()
        moveTo(r1)
        lineTo(r2)
        lineTo(r3)
        lineTo(r4)
        closePath()
        if not self.trace:
            drawPath()

        if self.trace:
            self.path.append([(r1), (r2), (r3), (r4)])
        elif self.color:
            fill(0, 1, 0, self.alpha)

        newPath()
        moveTo(r1)
        lineTo(r2)
        lineTo(b2)
        lineTo(b1)
        closePath()
        if not self.trace:
            drawPath()

        if self.trace:
            self.path.append([(r1), (r2), (b2), (b1)])
        elif self.color:
            fill(1, 1, 0, self.alpha)

        newPath()
        moveTo(b4)
        lineTo(r4)
        lineTo(r3)
        lineTo(b3)
        closePath()
        if not self.trace:
            drawPath()

        if self.trace:
            self.path.append([(b4), (r4), (r3), (b3)])
        elif self.color:
            if self.highlight_nib_faces:
                fill(1, 1, 0, self.alpha)
                stroke(0)
                strokeWidth(0.5)

        newPath()
        moveTo(b1)
        lineTo(r1)
        lineTo(r4)
        lineTo(b4)
        closePath()
        if not self.trace:
            drawPath()

        if self.trace:
            self.path.append([(b1), (r1), (r4), (b4)])
        elif self.color:
            restore()

        self.__currentPoint = pt

    def _curveToOne(self, pt1, pt2, pt3):

        b1 = self.transformPoint(self.__currentPoint, -1)
        b2 = self.transformPoint(pt3, -1)
        b3 = self.transformPoint(pt3)
        b4 = self.transformPoint(self.__currentPoint)

        bc1 = self.transformPoint(pt1, -1)
        bc2 = self.transformPoint(pt2, -1)

        r1 = self.transformPointHeight(self.__currentPoint, -1)
        r2 = self.transformPointHeight(pt3, -1)
        r3 = self.transformPointHeight(pt3)
        r4 = self.transformPointHeight(self.__currentPoint)

        rc1 = self.transformPointHeight(pt1, -1)
        rc2 = self.transformPointHeight(pt2, -1)

        if self.color and not self.trace:
            save()
            fill(0, 0, 1, self.alpha)

        tpt1 = self.transformPoint(pt1)
        tpt2 = self.transformPoint(pt2)

        # if not self.trace:
        #     text("b1", b1)
        #     text("b2", b2)
        #     text("b3", b3)
        #     text("b4", b4)

        #     text("bc1", bc1)
        #     text("bc2", bc2)

        #     text("tpt1", tpt1)
        #     text("tpt2", tpt2)

        #     text("r1", r1)
        #     text("r2", r2)
        #     text("r3", r3)
        #     text("r4", r4)

        newPath()
        moveTo(b1)
        curveTo(bc1, bc2, b2)
        lineTo(b3)
        curveTo(
            tpt2,
            tpt1,
            b4,
        )
        closePath()
        if not self.trace:
            drawPath()

        if self.trace:
            self.path.append([(b1), (bc1, bc2, b2), (b3), (tpt2, tpt1, b4)])
        elif self.color:
            fill(1, 0, 0, self.alpha)

        tpth1 = self.transformPointHeight(pt1)
        tpth2 = self.transformPointHeight(pt2)

        newPath()
        moveTo(r1)
        curveTo(rc1, rc2, r2)
        lineTo(r3)
        curveTo(
            tpth2,
            tpth1,
            r4,
        )
        closePath()
        if not self.trace:
            drawPath()

        if self.trace:
            self.path.append([(r1), (rc1, rc2, r2), (r3), (tpth2, tpth1, r4)])
        elif self.color:
            fill(0, 1, 0, self.alpha)

        newPath()
        moveTo(r1)
        curveTo(rc1, rc2, r2)
        lineTo(b2)
        curveTo(bc2, bc1, b1)
        closePath()
        if not self.trace:
            drawPath()

        if self.trace:
            self.path.append([(r1), (rc1, rc2, r2), (b2), (bc2, bc1, b1)])
        elif self.color:
            fill(1, 1, 0, self.alpha)
            stroke(0)
            strokeWidth(0.5)

        newPath()
        moveTo(r4)
        curveTo(tpth1, tpth2, r3)
        lineTo(b3)
        curveTo(tpt2, tpt1, b4)
        closePath()
        if not self.trace:
            drawPath()

        if self.trace:
            self.path.append([(r4), (tpth1, tpth2, r3), (b3), (tpt2, tpt1, b4)])
        elif self.color:
            fill(1, 1, 0, self.alpha)
            if self.highlight_nib_faces:
                stroke(0)
                strokeWidth(0.5)

        # Draw the nib face

        newPath()
        moveTo(b1)
        lineTo(r1)
        lineTo(r4)
        lineTo(b4)
        closePath()
        if not self.trace:
            drawPath()

        if self.trace:
            self.path.append([(b1), (r1), (r4), (b4)])
        elif self.color:
            restore()

        self.__currentPoint = pt3

    def _closePath(self):

        b1 = self.transformPoint(self.__currentPoint, -1)
        b2 = self.transformPoint(self.contourStart, -1)
        b3 = self.transformPoint(self.contourStart)
        b4 = self.transformPoint(self.__currentPoint)

        r1 = self.transformPointHeight(self.__currentPoint, -1)
        r2 = self.transformPointHeight(self.contourStart, -1)
        r3 = self.transformPointHeight(self.contourStart)
        r4 = self.transformPointHeight(self.__currentPoint)

        if self.color and not self.trace:
            save()
            fill(0, 0, 1, self.alpha)
        newPath()
        moveTo(b1)
        lineTo(b2)
        lineTo(b3)
        lineTo(b4)
        closePath()
        if not self.trace:
            drawPath()

        if self.trace:
            self.path.append([(b1), (b2), (b3), (b4)])
        elif self.color:
            fill(1, 0, 0, self.alpha)

        newPath()
        moveTo(r1)
        lineTo(r2)
        lineTo(r3)
        lineTo(r4)
        closePath()
        if not self.trace:
            drawPath()

        if self.trace:
            self.path.append([(r1), (r2), (r3), (r4)])
        elif self.color:
            fill(0, 1, 0, self.alpha)

        newPath()
        moveTo(r1)
        lineTo(r2)
        lineTo(b2)
        lineTo(b1)
        closePath()
        if not self.trace:
            drawPath()

        if self.trace:
            self.path.append([(r1), (r2), (b2), (b1)])
        elif self.color:
            fill(1, 1, 0, self.alpha)

        newPath()
        moveTo(b4)
        lineTo(r4)
        lineTo(r3)
        lineTo(b3)
        closePath()
        if not self.trace:
            drawPath()

        if self.trace:
            self.path.append([(b4), (r4), (r3), (b3)])
        elif self.color:
            if self.highlight_nib_faces:
                fill(1, 1, 0, self.alpha)
                stroke(0)
                strokeWidth(0.5)

        newPath()
        moveTo(b1)
        lineTo(r1)
        lineTo(r4)
        lineTo(b4)
        closePath()
        if not self.trace:
            drawPath()

        if self.trace:
            self.path.append([(b1), (r1), (r4), (b4)])
        elif self.color:
            restore()

        self.__currentPoint = None

    def _endPath(self):

        b1 = self.transformPoint(self.__currentPoint, -1)
        b4 = self.transformPoint(self.__currentPoint)

        r1 = self.transformPointHeight(self.__currentPoint, -1)
        r4 = self.transformPointHeight(self.__currentPoint)

        if self.color and not self.trace:
            save()
            fill(1, 1, 0, self.alpha)
            if self.highlight_nib_faces:
                stroke(0)
                strokeWidth(0.5)
        newPath()
        moveTo(b1)
        lineTo(r1)
        lineTo(r4)
        lineTo(b4)
        closePath()
        if not self.trace:
            drawPath()

        if self.trace:
            self.path.append([(b1), (r1), (r4), (b4)])
        elif self.color:
            restore()
        self.__currentPoint = None
