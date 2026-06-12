import pytest

from app.rules.roi_utils import box_center, normalize_point, point_in_polygon


def test_box_center_returns_middle_point():
    assert box_center([10, 20, 30, 60]) == (20.0, 40.0)


def test_normalize_point_uses_image_size():
    assert normalize_point(50, 25, 100, 50) == (0.5, 0.5)


def test_normalize_point_rejects_invalid_size():
    with pytest.raises(ValueError):
        normalize_point(10, 10, 0, 100)


def test_point_in_polygon_handles_inside_outside_and_boundary():
    polygon = ((0.25, 0.45), (0.95, 0.45), (0.95, 0.95), (0.25, 0.95))

    assert point_in_polygon((0.5, 0.5), polygon) is True
    assert point_in_polygon((0.1, 0.1), polygon) is False
    assert point_in_polygon((0.25, 0.6), polygon) is True
