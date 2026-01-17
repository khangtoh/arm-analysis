# ARM AI / GPU Stock Analysis

This repo contains a replicable analysis of **Arm Holdings (ARM)** showing how
AI / GPU narratives correlate with exact historical stock prices.

## What this does
- Pulls **exact daily ARM prices** via Yahoo Finance
- Overlays **AI / GPU strategic milestones**
- Computes **event-window returns**
- Outputs a **publication-ready chart + CSV**

## Setup
```bash
pip install -r requirements.txt
```

## Run the script
```bash
python scripts/arm_ai_timeline_overlay.py --ticker ARM --start 2023-09-01 --end 2026-01-17 --window 5
```

## Run the Streamlit app
```bash
streamlit run streamlit_app.py
```

## Use in Streamlit (Cloud) environments
When deploying to Streamlit Community Cloud (or similar hosted Streamlit environments):
1. Set **App file** to `streamlit_app.py`.
2. Set **Python version** to 3.11+ (matches the dependencies listed in `requirements.txt`).
3. Ensure the repo root is the working directory (so imports like `from scripts...` resolve).
4. Deploy. The app will download prices at runtime using Yahoo Finance.

### Using an existing Streamlit app setup
If you already have a Streamlit app configured, point it at this repo and ensure:
- Your app entrypoint is `streamlit_app.py`.
- The working directory is the repo root (required for `scripts/` imports).
- Dependencies are installed from `requirements.txt`.

If you use a custom Streamlit environment (self-hosted), install dependencies and run:
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```
