import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add path to sys.path
sys.path.append(os.path.join(os.getcwd(), "newcons"))

from core.models import FeedbackEvent, OCRResult
from agent.ticket_pipeline import app_ticket_pipeline
from agent.ticket_models import SentimentAnalysis, TicketRouting

class TestTicketPipeline(unittest.TestCase):
    
    def setUp(self):
        # Prepare basic event
        self.mock_event = FeedbackEvent(
            raw_text_content="Why is my 6480 gacha currency not arrived? This is the second time!",
            structured_content="Complaint: Payment not arrived \n Count: 2 \n Tone: Angry",
            ocr_results=[OCRResult(image_name="bill.png", error_codes=["PAY_ERR_500"])]
        )
        self.mock_vs = MagicMock() 

    @patch('agent.ticket_pipeline.ChatGoogleGenerativeAI')
    @patch('agent.ticket_tools.TicketTools.trigger_alert')
    def test_pipeline_crash_to_alert(self, mock_alert, mock_llm):
        print("Testing P0 Payment Alert Flow...")
        
        # 1. Mock Sentiment Agent Output
        mock_sentiment_output = SentimentAnalysis(
            sentiment_score=5,
            intent_summary="Payment not arrived",
            similar_incident_found=False
        )
        
        # 2. Mock Routing Agent Output
        mock_routing_output = TicketRouting(
            tags=["payment", "critical_bug"],
            priority="P0",
            is_crisis=True,
            action_item="Manual intervention required"
        )
        
        # Configure Mock LLM
        mock_llm.return_value.with_structured_output.return_value.invoke.side_effect = [
            mock_sentiment_output, 
            mock_routing_output
        ]
        
        # 3. Run Pipeline
        inputs = {
            "event": self.mock_event,
            "vectorstore": self.mock_vs,
            "alert_triggered": False
        }
        
        final_state = app_ticket_pipeline.invoke(inputs)
        
        # 4. Assertions
        print(f"Priority result: {final_state['routing'].priority}")
        print(f"Sentiment result: {final_state['sentiment'].sentiment_score}")
        
        self.assertEqual(final_state['routing'].priority, "P0")
        self.assertTrue(final_state['routing'].is_crisis)
        self.assertTrue(final_state['alert_triggered'])
        
        # Verify alert tool was called
        mock_alert.assert_called_once()
        print("PASS: P0 Alert and Routing logic verified!")

if __name__ == '__main__':
    unittest.main()
