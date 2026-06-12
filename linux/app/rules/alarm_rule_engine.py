"""告警规则引擎模块。"""

import time
from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock

from app.core.config import settings
from app.rules.roi_utils import box_center, normalize_point, point_in_polygon


@dataclass
class DeviceRuleState:
    """单设备规则状态。"""

    hit_count: int = 0
    last_alarm_at: float | None = None


class AlarmRuleEngine:
    """根据检测目标计算告警状态。"""

    _states: dict[str, DeviceRuleState] = {}
    _lock = Lock()

    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        self.clock = clock or time.monotonic

    @classmethod
    def reset_states(cls) -> None:
        """清空规则状态，主要用于测试。"""

        with cls._lock:
            cls._states.clear()

    def evaluate(self, device_id: str, targets: list[dict]) -> dict:
        """评估本次检测是否触发告警。"""

        matched_targets = []
        for target in targets:
            if target["class"] != "person":
                continue
            if target["confidence"] < settings.confidence_threshold:
                continue
            if self._target_in_danger_zone(target):
                target["in_danger_zone"] = True
                matched_targets.append(target)
            else:
                target["in_danger_zone"] = False

        with self._lock:
            state = self._states.setdefault(device_id, DeviceRuleState())
            if matched_targets:
                state.hit_count += 1
                return self._danger_zone_decision(state)

            state.hit_count = 0

        return {
            "alarm": False,
            "alarm_level": "normal",
            "alarm_action": "none",
            "alarm_status": "normal",
            "event_type": "upload",
        }

    def _danger_zone_decision(self, state: DeviceRuleState) -> dict:
        if state.hit_count < settings.alarm_trigger_count:
            return {
                "alarm": False,
                "alarm_level": "medium",
                "alarm_action": "none",
                "alarm_status": "suspected",
                "event_type": "danger_zone_intrusion",
            }

        now = self.clock()
        if self._is_suppressed(state, now):
            return {
                "alarm": False,
                "alarm_level": "high",
                "alarm_action": "none",
                "alarm_status": "suppressed",
                "event_type": "danger_zone_intrusion",
            }

        state.last_alarm_at = now
        return {
            "alarm": True,
            "alarm_level": "high",
            "alarm_action": "beep_led",
            "alarm_status": "alarm",
            "event_type": "danger_zone_intrusion",
        }

    def _is_suppressed(self, state: DeviceRuleState, now: float) -> bool:
        if state.last_alarm_at is None:
            return False
        return now - state.last_alarm_at < settings.alarm_suppress_seconds

    def _target_in_danger_zone(self, target: dict) -> bool:
        if not settings.danger_zone_enabled:
            return True
        if len(settings.danger_zone_roi) < 3:
            return False

        box = target.get("box") or []
        width = target.get("image_width")
        height = target.get("image_height")
        if len(box) != 4 or not width or not height:
            return False

        center_x, center_y = box_center(box)
        point = normalize_point(center_x, center_y, int(width), int(height))
        return point_in_polygon(point, settings.danger_zone_roi)
