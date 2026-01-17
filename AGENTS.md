# AGENTS.md — Why this repo exists + how to use it

## Purpose (why this code exists)
This repository exists to produce a **replicable, evidence-based overlay** between:
1) **ARM (Arm Holdings) historical stock prices** and  
2) **major AI/GPU narrative milestones**

The goal is to replace vague “AI hype” discussions with:
- an event-anchored price chart (exact daily closes)
- a table of event-window returns (pre/post impact)
- a repeatable workflow that can be updated as new milestones occur

This is primarily used for **3–6 month tactical analysis**:
- identifying narrative-driven reratings vs earnings-driven moves
- quantifying how durable (or fragile) the AI/GPU storyline is in price action
- producing artifacts (charts/CSVs) suitable for exec/investment discussion

## What the repo contains
- `scripts/arm_ai_timeline_overlay.py`
  - Downloads historical OHLCV for a ticker (default: `ARM`)
  - Overlays milestone dates as vertical markers on the close-price chart
  - Computes event-window returns (default window: ±5 trading days)
  - Writes outputs to disk (PNG + CSV)

- `requirements.txt`
  - Python dependencies for the script

- `outputs/`
  - Intended directory for generated artifacts
  - Default outputs:
    - `outputs/arm_ai_timeline_overlay.png`
    - `outputs/arm_ai_event_returns.csv`

- `README.md`
  - Human-facing usage instructions

## How to run (agent instructions)
### 1) Install deps
```bash
pip install -r requirements.txt
