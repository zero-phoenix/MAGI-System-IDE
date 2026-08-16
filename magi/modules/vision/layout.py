from typing import Any


class LayoutEngine:
    """
    Motor geométrico (Tesseract modo layout y cálculo matemático de teselas).
    P1.b: Tesseract Dummy y Teselador.
    """
    def __init__(self):
        pass

    def _compute_iou(self, boxA: tuple[float, float, float, float], boxB: tuple[float, float, float, float]) -> float:
        """
        Intersección sobre Unión (IoU).
        Cajas: (x1, y1, x2, y2)
        """
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0, xB - xA) * max(0, yB - yA)
        if interArea == 0:
            return 0.0

        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

        iou = interArea / float(boxAArea + boxBArea - interArea)
        return iou

    def extract_layout(self, image_data: bytes) -> dict[str, Any]:
        """
        Retorna las cajas delimitadoras y calcula IoU matemático.
        """
        # Mocking Tesseract bbox extraction
        mock_boxes = [
            {"id": 1, "box": (10, 10, 100, 50), "text": "Header"},
            {"id": 2, "box": (10, 60, 200, 100), "text": "Paragraph"}
        ]

        # Test IoU calculation against a mock VLM box
        mock_vlm_box = (12, 12, 98, 48)

        iou_val = self._compute_iou(mock_boxes[0]["box"], mock_vlm_box)

        return {
            "boxes": mock_boxes,
            "mean_iou_mock": iou_val,
            "baseline_cuts": 0
        }
