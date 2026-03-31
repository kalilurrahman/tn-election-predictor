# Phase 2: Data and Calibration Workflow

## Reality check

Using free Hugging Face models for inference is straightforward.

Fine-tuning compute is different:

- model inference can be free or low-cost depending on the model and rate limits
- actual training on Hugging Face usually needs paid compute
- the cheapest practical next step is often to build a labeled headline dataset first, then calibrate your Bayesian weights locally

## What is included

- [training/build_labeling_dataset.py](C:/Users/HP/OneDrive/Documents/Playground/tn-predictor-final/training/build_labeling_dataset.py)
  - scrapes headlines and exports a JSONL labeling set
- [training/calibrate_predictor.py](C:/Users/HP/OneDrive/Documents/Playground/tn-predictor-final/training/calibrate_predictor.py)
  - finds a better sentiment scale and bias from labeled data

## Suggested workflow

1. Export a labeling set:

```bash
python training/build_labeling_dataset.py --limit 40
```

2. Label these fields for each row:

- `human_sentiment_label`
- `alliance_impact`
- `notes`

3. Save the completed JSONL as `training/headline_training_rows.jsonl`

4. Run calibration:

```bash
python training/calibrate_predictor.py --input training/headline_training_rows.jsonl
```

5. Use the resulting scale and bias to replace today’s heuristic constants in the predictor path.

## Best next upgrade after the Space is live

After you test the Space end to end, I’d recommend:

1. publish a labeled dataset to the Hub
2. fine-tune a small multilingual classifier on that dataset
3. swap the current generic sentiment model for your TN-election-specific one

If you want, I can wire the calibration output back into `backend/predictor.py` next, or generate a Hugging Face dataset card and upload flow after you log in.
