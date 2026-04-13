import os
import sys
from unittest.mock import MagicMock, patch

# Add path to sys.path
sys.path.append(os.path.join(os.getcwd(), "newcons"))

from core.models import FeedbackEvent, OCRResult
from engine.processors import DoclingProcessor, PaddleOCRProcessor
from engine.ingestion_pipeline import IngestionPipeline

def test_multimodal_alignment():
    print("Starting verification of multimodal alignment logic...")
    
    # 1. Mock OCR result
    mock_ocr_res = OCRResult(
        image_name="screenshot_1.png",
        uid="123456789",
        gacha_count=80,
        error_codes=["1001_1"],
        raw_text="UID: 123456789, pulled 80 times, error 1001_1"
    )
    
    # 2. Mock building FeedbackEvent
    event = FeedbackEvent(
        raw_text_content="Player feedback: Game crashed with error.",
        structured_content="Player feedback: Game crashed with error.",
        ocr_results=[mock_ocr_res]
    )
    
    # 3. Verify text enrichment logic
    enriched = event.get_enriched_text()
    print(f"Generated Enriched Text: {enriched}")
    
    expected_parts = ["[UID: 123456789]", "[ErrorCodes: 1001_1]"]
    for part in expected_parts:
        if part in enriched:
            print(f"PASS: Found expected part: {part}")
        else:
            print(f"FAIL: Missing expected part: {part}")
            return False

    # 4. Mock Pipeline Run
    with patch('engine.processors.DocumentConverter'), \
         patch('engine.processors.PaddleOCR'), \
         patch.object(DoclingProcessor, 'process', return_value="# Structured Feedback"), \
         patch.object(PaddleOCRProcessor, 'process', return_value=mock_ocr_res):
            
            pipeline = IngestionPipeline()
            
            result_event = pipeline.run(
                text_content="Help me!",
                image_paths=["dummy.png"]
            )
            
            print(f"Pipeline Run Result Event ID: {result_event.event_id}")
            print(f"OCR Results Count: {len(result_event.ocr_results)}")
            
            if len(result_event.ocr_results) == 1 and result_event.ocr_results[0].uid == "123456789":
                print("PASS: Pipeline alignment check")
            else:
                print("FAIL: Pipeline alignment check")
                return False

    return True

if __name__ == "__main__":
    success = test_multimodal_alignment()
    if success:
        print("\nAll multimodal ingestion logic verified!")
        sys.exit(0)
    else:
        print("\nErrors found during verification.")
        sys.exit(1)
