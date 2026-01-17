# Agentic Product Specs

This directory contains high-level, human-readable product specifications intended for
use by coding agents (including but not limited to Codex). These specs are structured
as EPICs with bullet-point stories to guide implementation work.

To ensure a new coding agent knows **which EPIC and stories to work on**, reference
the execution queue in `product-development/agentic_work_index.md`, which is generated
from the machine-readable database in `product-development/agentic_work_index.yaml`.
That source of truth lists the currently active EPIC, story priorities, owners, and
acceptance criteria for the next batch of work, plus concurrency limits for
multi-agent execution.

---

## EPIC 1 — Event Intelligence & Curation
- Allow users to add/edit/remove milestone events directly in the UI.
- Support CSV upload/download for event lists.
- Tag events by type (earnings, product launch, regulation, partnership).
- Attach evidence links (press releases, filings, transcripts, news).
- Enable filtering of timeline overlays by event type/tag.

## EPIC 2 — Comparative & Benchmarking Views
- Add peer/benchmark overlays (e.g., NVDA, AMD, SOX).
- Provide relative performance mode (alpha vs benchmark).
- Enable multi-ticker comparison within the same time window.
- Let users define custom benchmarks by ticker list.

## EPIC 3 — Deeper Analytics & Impact Metrics
- Expand event-window analysis to include longer post-event drift windows.
- Add volatility and drawdown stats around events.
- Provide an attribution table for event contributions to total returns.
- Surface statistically notable events (outliers vs typical moves).

## EPIC 4 — Workflow, Sharing & Reporting
- Save and reload analysis scenarios (ticker, range, window, events, benchmark).
- One-click export of charts and tables (PNG/PDF/CSV).
- Add a shareable report view for executive consumption.
- Version and audit event lists over time.

## EPIC 5 — UX & Interaction Enhancements
- Interactive event selection (click to highlight and isolate windows).
- Hover tooltips with event metadata and return stats.
- Side-by-side layout for chart and returns table.
- Clear empty/error states with guided prompts.

## EPIC 6 — Data Quality & Trust
- Offer multiple data providers or validation checks.
- Explicit handling of non-trading days/partial sessions.
- Show data refresh timestamp and source transparency.

## EPIC 7 — Alerts & Monitoring (Optional / Later)
- Notify users when price/volume moves exceed event norms.
- Scheduled refresh to keep overlays current.
- Configurable alert thresholds by ticker/event type.
