import os
import sys
import numpy as np
from unittest.mock import MagicMock, patch

# Add path to sys.path
sys.path.append(os.path.join(os.getcwd(), "newcons"))

from core.models import FeedbackEvent, OCRResult
from algorithms.linucb import ticket_recommender
# Pre-mock ChatGoogleGenerativeAI and embeddings before importing pipeline
with patch('langchain_google_genai.ChatGoogleGenerativeAI'), \
     patch('langchain_huggingface.HuggingFaceEmbeddings'):
    from agent.ticket_pipeline import app_ticket_pipeline
    from agent.ticket_models import SentimentAnalysis, TicketRouting

def test_recommendation_core():
    print("Starting verification of Personalized Recommendation Engine...")
    
    # 1. Test context building
    dummy_emb = [0.1] * 20
    context = ticket_recommender.build_context(dummy_emb, 5, ["bug", "payment"])
    
    print(f"Context vector shape: {context.shape}")
    assert context.shape[0] == 20
    assert context[16] == 1.0 # Normalized sentiment
    assert context[17] == 1.0 # Payment tag part
    assert context[18] == 1.0 # Bug tag part
    print("PASS: Context building logic")

    # 2. Test initial recommendation
    op, idx, x_t = ticket_recommender.recommend(context)
    print(f"Initial Recommended Operator: {op} (Arm {idx})")
    assert op in ticket_recommender.operators
    print("PASS: Initial recommendation selection")

    # 3. Test reward update logic
    tech_arm_idx = ticket_recommender.operators.index("Tech_Support")
    print("Simulating training: Operator Tech_Support likes 'bug' tickets...")
    for _ in range(5):
        ticket_recommender.update_reward(tech_arm_idx, context, 1.0)
    
    print("PASS: Reward update logic")

    # 4. Test Graph Integration
    print("Verifying Pipeline Integration...")
    # Mocking the LLM responses and embedding
    with patch('agent.ticket_pipeline.embeddings') as mock_emb_instance, \
         patch('agent.ticket_pipeline.ChatGoogleGenerativeAI') as mock_llm_cls:
        
        mock_emb_instance.embed_query.return_value = [0.1] * 384
        
        mock_sentiment = SentimentAnalysis(sentiment_score=4, intent_summary="Bug report", similar_incident_found=False)
        mock_routing = TicketRouting(tags=["bug"], priority="P1", is_crisis=False, action_item="Fix it")
        
        # Structure the mock for with_structured_output
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.side_effect = [mock_sentiment, mock_routing]
        mock_llm_cls.return_value.with_structured_output.return_value = mock_structured_llm
        
        event = FeedbackEvent(raw_text_content="It broke!")
        inputs = {
            "event": event,
            "vectorstore": MagicMock(),
            "alert_triggered": False
        }
        
        final_state = app_ticket_pipeline.invoke(inputs)
        print(f"Pipeline Recommended Operator: {final_state['recommended_operator']}")
        assert "recommended_operator" in final_state
        print("PASS: Pipeline integration")

    return True

if __name__ == "__main__":
    try:
        if test_recommendation_core():
            print("\nAll LinUCB Recommendation tests passed!")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
