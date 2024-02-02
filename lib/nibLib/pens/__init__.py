from __future__ import annotations

from nibLib.pens.ovalNibPen import OvalNibPen
from nibLib.pens.rectNibPen import RectNibPen
from nibLib.pens.superellipseNibPen import SuperellipseNibPen


nib_models = {
    "Superellipse": SuperellipseNibPen,
    "Oval": OvalNibPen,
    "Rectangle": RectNibPen,
}
