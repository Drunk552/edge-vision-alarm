"""告警规则引擎模块。"""

from app.core.config import settings


class AlarmRuleEngine:
    """根据检测目标计算告警状态。"""

    def evaluate(self, device_id: str, targets: list[dict]) -> dict:
        """评估本次检测是否触发告警。"""

        matched_targets = [
            target
            for target in targets
            if target["class"] == "person"
            and target["confidence"] >= settings.confidence_threshold
        ]
        if matched_targets:
            return {
                "alarm": True,
                "alarm_level": "high",
                "alarm_action": "beep_led",
                "alarm_status": "alarm",
                "event_type": "intrusion",
            }
        return {
            "alarm": False,
            "alarm_level": "normal",
            "alarm_action": "none",
            "alarm_status": "normal",
            "event_type": "upload",
        }
