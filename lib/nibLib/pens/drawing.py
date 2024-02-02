from AppKit import NSBezierPath


from nibLib.typing import TPoint
from typing import Sequence


def draw_path(path: Sequence[Sequence[TPoint]] | None) -> None:
    """
    Build a NSBezierPath from `path`. The NSBezierPath is then drawn in the current
    context.
    """

    if not path:
        return

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
    subpath.stroke()
