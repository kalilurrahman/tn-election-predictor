# Tamil Nadu Assembly Election Predictor - System Architecture

This app follows a 5-layer architecture that can scale from prototype to production forecasting.

## Layer 1: Data Ingestion
- Election archives and candidate affidavits (ECI)
- Geo boundaries and constituency mapping assets
- News and event streams for daily issue + sentiment capture
- Survey inputs for calibration
- Social trend inputs for short-cycle momentum

Current status:
- News ingestion and candidate sync pipeline are live in backend.
- Source catalog is formalized in `backend/source_registry.py`.

## Layer 2: Feature Engineering
- Swing index by constituency and region
- Incumbency / anti-incumbency factor
- Alliance transfer and coherence proxy
- Issue salience (NEET, jobs, Cauvery, welfare, etc.)
- Sentiment velocity (weekly acceleration / deceleration)
- Incumbency fatigue index (candidate + seat competitiveness)
- Welfare saturation proxy (issue + turnout + context based)
- Demographic fractionalization proxy (heterogeneity pressure)

Current status:
- Regional swings, anti-incumbency, turnout delta, alliance cohesion, and campaign intensity are implemented in simulation controls.
- Structural feature snapshots now feed scenario simulation and toss-up prioritization.
- Next upgrade: persist daily feature snapshots into a dedicated table for drift tracking.

## Layer 3: Prediction Engine
- Baseline seat model (historical vote and margin priors)
- Bayesian updater for incremental evidence
- Tamil/English NLP sentiment score fusion
- Structural simulation adjuster (feature-conditioned seat shifts)

Current status:
- Hybrid predictor + analytics endpoints are active in FastAPI.
- New API layer now exposes methodology metadata and seat dynamics classifications.
- Next upgrade: plug in model registry with explicit model versioning and backtesting windows.

## Layer 4: Forecasting Layer
- Seat-by-seat simulation engine
- Confidence intervals and distribution ranges
- Neck-and-neck and upset/surprise detectors
- Wave detection and confidence decay

Current status:
- Strategy Lab and simulation APIs provide real-time scenario runs.
- Next upgrade: nightly 10,000-run Monte Carlo batch with persisted CI outputs.

## Layer 5: Analytics UI
- State-level projection and trend readouts
- Constituency deep-dive and candidate cards
- Interactive TN map
- Scenario simulator and opinion poll view
- In-app Methodology page (README-style architecture/model/data documentation)

Current status:
- Dashboard, Candidate Registry, Strategy Lab, and Opinion Polls pages are live.
- Statistics and Methodology pages now include advanced analytics and modeling explanation.
- View transitions are enabled globally for smoother interaction.

## Recommended Production Stack
- Data pipeline: Python + scheduler + Postgres
- NLP: Indic/XLM-R style classifier fine-tuned on Tamil political text
- ML: Regression + Bayesian update + simulation engine
- API: FastAPI with typed forecast payloads
- UI: React/Next + map/charts

## Immediate Next Milestones
1. Add persistent feature store (daily snapshots per seat).
2. Add model calibration reports and error dashboards.
3. Add poll-of-polls weighting by recency and sample quality.
4. Add confidence bands and decaying uncertainty curves in UI.
