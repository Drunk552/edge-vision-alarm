"""检测器抽象接口。"""

from typing import Protocol


class BaseDetector(Protocol):
    """目标检测器统一接口。"""

    @property
    def model_loaded(self) -> bool:
        """模型是否已加载。"""

    def detect(self, image_path: str) -> list[dict]:
        """检测图片中的目标。"""


class EmptyDetector:
    """空检测器，用于未配置模型时保持上传链路可用。"""

    @property
    def model_loaded(self) -> bool:
        """空检测器不加载模型。"""

        return False

    def detect(self, image_path: str) -> list[dict]:
        """返回空检测结果。"""

        return []
