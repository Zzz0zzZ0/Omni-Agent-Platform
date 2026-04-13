from typing import List, Optional
from .processors import DoclingProcessor, PaddleOCRProcessor
from core.models import FeedbackEvent, OCRResult

class IngestionPipeline:
    """多模态数据摄入管道协调器"""
    def __init__(self):
        # 延迟初始化，避免没用到时也加载大模型
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

    def run(self, 
            text_content: Optional[str] = None, 
            text_file_path: Optional[str] = None,
            image_paths: List[str] = []) -> FeedbackEvent:
        """执行端到端摄入流程"""
        
        event = FeedbackEvent()
        
        # 1. 处理文本部分
        if text_file_path:
            # 如果是 PDF 或 Word，使用 Docling 解析结构
            event.structured_content = self.docling.process(text_file_path)
            event.raw_text_content = f"Parsed from {text_file_path}"
        elif text_content:
            event.raw_text_content = text_content
            # 对于纯文本，也可以过一遍 Docling 做标准化，或者直接赋值
            event.structured_content = text_content

        # 2. 处理图片部分 (并发优化暂不在此处展开，保证逻辑清晰)
        ocr_results: List[OCRResult] = []
        for img_path in image_paths:
            print(f"[Pipeline] Processing image: {img_path}")
            res = self.paddle.process(img_path)
            ocr_results.append(res)
        
        event.ocr_results = ocr_results
        
        return event
