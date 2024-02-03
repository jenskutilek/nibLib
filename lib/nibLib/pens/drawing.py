from AppKit import NSBezierPath, NSColor


from nibLib.typing import TPoint
from typing import Sequence


def draw_path(path: Sequence[Sequence[TPoint]] | None, width=1.0) -> None:
    """
    Build a NSBezierPath from `path`. The NSBezierPath is then drawn in the current
    context.
    """

    if not path:
        return

    subpath = NSBezierPath.alloc().init()
    subpath.setLineWidth_(width)
    # subpath.setStrokeColor_(NSColor())
    subpath.moveToPoint_(path[0][0])
    for p in path[1:]:
        if len(p) == 3:
            # curve
            A, B, C = p
            subpath.curveToPoint_controlPoint1_controlPoint2_(C, A, B)
        else:
            subpath.lineToPoint_(p[0])

    subpath.closePath()
    NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0.2, 1, 0.5).set()
    subpath.stroke()
