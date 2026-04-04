from transformers import pipeline
from typing import List, Dict, Any, Tuple

class ElectionPredictor:
    def __init__(self, model_name: str = "facebook/bart-large-mnli"):
        self.model_name = model_name
        print(f"Loading prediction model: {self.model_name}...")
        try:
            self.classifier = pipeline(
                "zero-shot-classification",
                model=self.model_name,
                tokenizer=self.model_name,
                device=-1
            )
            print("Prediction model loaded successfully.")
        except Exception as e:
            print(f"Error loading prediction model {self.model_name}: {e}")
            self.classifier = None
            raise

    def predict(self, text_input: str, candidate_or_party_names: List[str], num_predictions: int = 5) -> List[Tuple[str, float]]:
        if not self.classifier:
            return [("Error", 0.0)]
        if not text_input or not text_input.strip():
            return [("Input required", 0.0)]
        if not candidate_or_party_names:
            return [("No candidates/parties provided", 0.0)]

        try:
            results = self.classifier(
                text_input,
                candidate_labels=candidate_or_party_names,
                hypothesis_template="This text is about {}.",
                multi_label=False
            )
            predictions = []
            if results and 'labels' in results and 'scores' in results:
                scored_labels = list(zip(results['labels'], results['scores']))
                scored_labels.sort(key=lambda item: item[1], reverse=True)
                predictions = scored_labels[:num_predictions]

            if not predictions:
                return [("No specific prediction", 0.0)]

            return predictions
        except Exception as e:
            print(f"Error during prediction: {e}")
            return [("Prediction Error", 0.0)]
