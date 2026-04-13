from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class OCRResult(BaseModel):
    """单张图片的 OCR 提取结果"""
    image_name: str
    uid: Optional[str] = None
    gacha_count: Optional[int] = None
    error_codes: List[str] = []
    raw_text: str = ""

class FeedbackEvent(BaseModel):
    """统一的反馈事件模型"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    raw_text_content: str = ""
    structured_content: str = "" # Docling 处理后的 Markdown
    ocr_results: List[OCRResult] = []
    
    def get_enriched_text(self) -> str:
        """生成用于向量化增强的文本"""
        metadata_str = ""
        uids = {r.uid for r in self.ocr_results if r.uid}
        error_codes = {ec for r in self.ocr_results for ec in r.error_codes}
        
        if uids:
            metadata_str += f" [UID: {', '.join(uids)}]"
        if error_codes:
            metadata_str += f" [ErrorCodes: {', '.join(error_codes)}]"
            
        return f"{metadata_str} {self.structured_content or self.raw_text_content}".strip()
