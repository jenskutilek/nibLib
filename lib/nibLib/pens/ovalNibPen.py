from __future__ import division, print_function

from math import atan2, cos, degrees, sin, tan

from mojo.drawingTools import *

from nibLib import DEBUG_CENTER_POINTS, DEBUG_CURVE_POINTS
from nibLib.geometry import angleBetweenPoints, getPointsFromCurve, optimizePointPath
from nibLib.pens.rectNibPen import RectNibPen




class OvalNibPen(RectNibPen):
	
	def _get_tangent_point(self, alpha):
		
		# Calculate the point on the ellipse
		# at the given tangent angle alpha.
		# t not the angle from the ellipse center, but just a parameter.
		
		t = atan2(-self.b, (self.a * tan(alpha)))
		x = self.a * cos(t)
		y = self.b * sin(t)
		
		return x, y
	
	def _get_rotated_tangent_point(self, pt):
		x, y = pt
		x1 = x * cos(self.angle) - y * sin(self.angle)
		y1 = x * sin(self.angle) + y * cos(self.angle)
		
		return x1, y1
	
	def _draw_nib_face(self, pt):
		save()
		#fill(*self.path_fill)
		#strokeWidth(0)
		#stroke(None)
		translate(pt[0], pt[1])
		rotate(degrees(self.angle))
		oval(
			-self.a,
			-self.b,
			self.width,
			self.height
		)
		restore()
	
	def _moveTo(self, pt):
		self.__currentPoint = pt
		self.contourStart = pt
		self._draw_nib_face(pt)
	
	def _lineTo(self, pt):
		
		# angle from the previous to the current point
		
		phi = angleBetweenPoints(self.__currentPoint, pt)
		#print(u"%0.2f°: %s -> %s" % (degrees(phi), self.__currentPoint, pt))
		pt0 = self._get_tangent_point(phi - self.angle)
		x, y = self._get_rotated_tangent_point(pt0)
		
		if False: # Display point on oval nib
			save()
			strokeWidth(0)
			stroke(None)
			fill(0,0,1)
			translate(self.__currentPoint[0], self.__currentPoint[1])
			rect(x-0.5, y-0.5, 1, 1)
			#text("%i|%i %i" % (pt0[0], pt0[1], degrees(phi)), (0, 0))
			restore()
		#fill(1, 0, 0, self.alpha)
		#stroke(None)
		newPath()
		p0 = (self.__currentPoint[0] + x, self.__currentPoint[1] + y)
		p1 = (pt[0] + x, pt[1] + y)
		p2 = (pt[0] - x, pt[1] - y)
		p3 = (self.__currentPoint[0] - x, self.__currentPoint[1] - y)
		moveTo(p0)
		lineTo(p1)
		lineTo(p2)
		lineTo(p3)
		closePath()
		drawPath()
		if self.trace: self.path.append([(p0), (p1), (p2), (p3)])
		self._draw_nib_face(pt)
		self.__currentPoint = pt
		
	
	def _curveToOne(self, pt1, pt2, pt3):
		
		# Break curve into line segments
		points = getPointsFromCurve((self.__currentPoint, pt1, pt2, pt3), 5)
		
		# Draw points of center line
		if DEBUG_CENTER_POINTS:
			save()
			stroke(None)
			strokeWidth(0)
			fill(0, 0, 0, self.alpha)
			for x, y in points:
				rect(x-1, y-1, 2, 2)
			restore()
		
		# Calculate angles between points
		
		# The first angle is that of the curve start point to bcp1
		angles = [angleBetweenPoints(self.__currentPoint, pt1)]
		
		for i in range(1, len(points)):
			phi = angleBetweenPoints(points[i-1], points[i])
			angles.append(phi)
		
		# The last angle is that of bcp2 point to the curve end point
		angles.append(angleBetweenPoints(pt2, pt3))
		
		# Find points on ellipse for each angle
		inner = []
		outer = []
		
		#stroke(None)
		
		for i, p in enumerate(points):
			pt0 = self._get_tangent_point(angles[i] - self.angle)
			
			x, y = self._get_rotated_tangent_point(pt0)
			outer.append((p[0] + x, p[1] + y))
			if DEBUG_CURVE_POINTS:
				# Draw outer points in red
				save()
				fill(1, 0, 0, self.alpha)
				rect(p[0] + x - 1, p[1] + y - 1, 2, 2)
				restore()
			
			x, y = self._get_rotated_tangent_point((-pt0[0], -pt0[1]))
			inner.append((p[0] + x, p[1] + y))
			if DEBUG_CURVE_POINTS:
				# Draw inner points in green
				save()
				fill(0, 0.8, 0, self.alpha)
				rect(p[0] + x - 1, p[1] + y - 1, 2, 2)
				restore()
		
		if inner and outer:

			inner = optimizePointPath(inner, 0.3)
			outer = optimizePointPath(outer, 0.3)
			
			newPath()
			moveTo(outer[0])
			for p in outer[1:]:
				lineTo(p)
			inner.reverse()
			for p in inner:
				lineTo(p)
			lineTo(outer[0])
			closePath()
			drawPath()
			if self.trace: self.path.append(optimizePointPath(outer + inner, 1))
		
		self._draw_nib_face(pt3)
		self.__currentPoint = pt3
	
	def _closePath(self):
		self.__currentPoint = None
	
	def _endPath(self):
		self.__currentPoint = None
