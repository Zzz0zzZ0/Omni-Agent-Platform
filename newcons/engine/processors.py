import re
import os
from typing import List, Optional
from docling.document_converter import DocumentConverter
from paddleocr import PaddleOCR
from core.models import OCRResult

class DoclingProcessor:
    """Use Docling for document structure analysis"""
    def __init__(self):
        self.converter = DocumentConverter()

    def process(self, source: str) -> str:
        """Parse local file or URL, return Markdown content"""
        try:
            result = self.converter.convert(source)
            return result.document.export_to_markdown()
        except Exception as e:
            print(f"[Docling] Conversion failed: {e}")
            return ""

class PaddleOCRProcessor:
    """Use PaddleOCR to extract features from images"""
    def __init__(self, lang='ch'):
        # 首次初始化会下载模型
        self.ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
        
        # 预编译正则表达式
        self.re_uid = re.compile(r'\b\d{9}\b') # 9位数字 UID
        self.re_gacha = re.compile(r'(?:已抽|累计|抽数|次数)[:：]?\s*(\d+)') 
        self.re_error = re.compile(r'\b[A-Za-z0-9]{3,}_[0-9]+\b') # 错误码模式如 1001_1 或 ERROR_404

    def process(self, image_path: str) -> OCRResult:
        """Full image scanning and feature extraction"""
        if not os.path.exists(image_path):
            return OCRResult(image_name=os.path.basename(image_path))

        try:
            result = self.ocr.ocr(image_path, cls=True)
        except Exception as e:
            print(f"[OCR] Error processing image {image_path}: {e}")
            result = None
        
        all_text = ""
        if result and result[0]:
            all_text = " ".join([line[1][0] for line in result[0]])

        # Match UID
        uids = self.re_uid.findall(all_text)
        uid = uids[0] if uids else None

        # Match Gacha Count
        gachas = self.re_gacha.findall(all_text)
        gacha_count = int(gachas[0]) if gachas else None

        # Match Error Codes
        error_codes = list(set(self.re_error.findall(all_text)))

        return OCRResult(
            image_name=os.path.basename(image_path),
            uid=uid,
            gacha_count=gacha_count,
            error_codes=error_codes,
            raw_text=all_text
        )
