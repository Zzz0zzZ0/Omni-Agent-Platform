"""
多模态数据摄入管道 — 重命名自 ingestion_pipeline.py。
"""
from typing import List, Optional
from engine.processors import DoclingProcessor, PaddleOCRProcessor
from domains.game_ops.schemas import FeedbackEvent, OCRResult


class IngestionPipeline:
    """多模态数据摄入管道协调器"""

    def __init__(self):
        self._docling = None
        self._paddle = None

    @property
    def docling(self):
        if self._docling is None:
            self._docling = DoclingProcessor()
        return self._docling

    @property
    def paddle(self):
        if self._paddle is None:
            self._paddle = PaddleOCRProcessor()
        return self._paddle

    def run(
        self,
        text_content: Optional[str] = None,
        text_file_path: Optional[str] = None,
        image_paths: List[str] = [],
    ) -> FeedbackEvent:
        """执行端到端摄入流程"""
        event = FeedbackEvent()

        if text_file_path:
            event.structured_content = self.docling.process(text_file_path)
            event.raw_text_content = f"Parsed from {text_file_path}"
        elif text_content:
            event.raw_text_content = text_content
            event.structured_content = text_content

        ocr_results: List[OCRResult] = []
        for img_path in image_paths:
            res = self.paddle.process(img_path)
            ocr_results.append(res)

        event.ocr_results = ocr_results
        return event
