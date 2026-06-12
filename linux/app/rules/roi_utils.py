"""危险区域 ROI 几何工具。"""


def box_center(box: list[int] | tuple[int, int, int, int]) -> tuple[float, float]:
    """计算检测框中心点。"""

    if len(box) != 4:
        raise ValueError("box must contain four coordinates")

    x1, y1, x2, y2 = box
    return ((float(x1) + float(x2)) / 2.0, (float(y1) + float(y2)) / 2.0)


def normalize_point(
    x: float, y: float, width: int, height: int
) -> tuple[float, float]:
    """将像素坐标转换为归一化坐标。"""

    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")

    return (x / float(width), y / float(height))


def point_in_polygon(
    point: tuple[float, float], polygon: list[list[float]] | tuple[tuple[float, float], ...]
) -> bool:
    """判断点是否位于 ROI 多边形内，边界点按区域内处理。"""

    if len(polygon) < 3:
        return False

    x, y = point
    inside = False
    previous = polygon[-1]

    for current in polygon:
        x1, y1 = float(previous[0]), float(previous[1])
        x2, y2 = float(current[0]), float(current[1])

        if _point_on_segment(x, y, x1, y1, x2, y2):
            return True

        crosses = (y1 > y) != (y2 > y)
        if crosses:
            x_intersection = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x_intersection >= x:
                inside = not inside

        previous = current

    return inside


def _point_on_segment(
    px: float, py: float, x1: float, y1: float, x2: float, y2: float
) -> bool:
    cross = (px - x1) * (y2 - y1) - (py - y1) * (x2 - x1)
    if abs(cross) > 1e-9:
        return False

    return min(x1, x2) - 1e-9 <= px <= max(x1, x2) + 1e-9 and min(
        y1, y2
    ) - 1e-9 <= py <= max(y1, y2) + 1e-9
