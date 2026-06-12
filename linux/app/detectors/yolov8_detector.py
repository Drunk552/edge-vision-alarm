"""YOLOv8 检测器适配模块。"""

from pathlib import Path

from app.core.config import settings


class Yolov8Detector:
    """基于 Ultralytics YOLOv8 的检测器。"""

    def __init__(
        self, model_path: Path | None = None, confidence: float | None = None
    ) -> None:
        self.model_path = model_path or settings.model_path
        self.confidence = confidence or settings.confidence_threshold
        self._model = None

    @property
    def model_loaded(self) -> bool:
        """模型是否已加载。"""

        return self._model is not None

    def load_model(self) -> None:
        """加载 YOLOv8 模型。"""

        if self._model is not None:
            return
        if not self.model_path.exists():
            raise FileNotFoundError(f"model file not found: {self.model_path}")

        from ultralytics import YOLO

        self._model = YOLO(str(self.model_path))

    def detect(self, image_path: str) -> list[dict]:
        """执行目标检测并返回统一目标结构。"""

        self.load_model()
        results = self._model.predict(
            source=image_path, conf=self.confidence, verbose=False
        )
        targets: list[dict] = []
        for result in results:
            names = result.names
            image_height, image_width = result.orig_shape
            for box in result.boxes:
                xyxy = box.xyxy[0].tolist()
                class_id = int(box.cls[0].item())
                targets.append(
                    {
                        "class": names[class_id],
                        "confidence": float(box.conf[0].item()),
                        "box": [int(value) for value in xyxy],
                        "image_width": int(image_width),
                        "image_height": int(image_height),
                    }
                )
        return targets
