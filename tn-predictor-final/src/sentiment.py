from transformers import pipeline
from typing import Dict, Any

class SentimentAnalyzer:
    def __init__(self, model_name: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"):
        self.model_name = model_name
        print(f"Loading sentiment analysis model: {self.model_name}...")
        try:
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                tokenizer=self.model_name,
                device=-1
            )
            print("Sentiment analysis model loaded successfully.")
        except Exception as e:
            print(f"Error loading sentiment model {self.model_name}: {e}")
            self.sentiment_pipeline = None
            raise

    def analyze(self, text: str) -> Dict[str, Any]:
        if not self.sentiment_pipeline:
            return {"error": "Sentiment analysis model not loaded."}
        if not text or not isinstance(text, str) or not text.strip():
            return {"label": "NEUTRAL", "score": 0.0, "warning": "Empty input provided."}

        try:
            result = self.sentiment_pipeline(text)
            if result and isinstance(result, list) and len(result) > 0:
                sentiment_map = {
                    "LABEL_0": "Negative",
                    "LABEL_1": "Neutral",
                    "LABEL_2": "Positive"
                }
                sentiment_label = result[0].get('label', 'Unknown')
                score = result[0].get('score', 0.0)
                readable_label = sentiment_map.get(sentiment_label, sentiment_label)
                return {"label": readable_label, "score": float(score)}
            else:
                return {"label": "Unknown", "score": 0.0, "error": "Unexpected result format from model."}
        except Exception as e:
            print(f"Error during sentiment analysis: {e}")
            return {"label": "Error", "score": 0.0, "error": str(e)}
