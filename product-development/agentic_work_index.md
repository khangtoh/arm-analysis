# Agentic Work Index (Start Here)

This file tells a coding agent **what to work on next** after cloning the repo.
It is a **generated view** of the machine-readable work database in
`product-development/agentic_work_index.yaml` and is anchored to Git-native
metadata for both the active EPIC and the current product version.

---

## How to use this file
1. **Start at the "Active EPIC" section** to see the current focus area.
2. Pick the **highest-priority story** that is `ready` and unassigned.
3. Use the story acceptance criteria as the implementation checklist.
4. When a story is complete, update the status and add a short outcome note.

---

## Git-native anchors (source of truth)
- **Active EPIC tag:** `epic-active/EPIC-1` (check with `git tag --points-at HEAD 'epic-active/*'`)
- **Product version:** `v0.1.0` (tag `product/v0.1.0`, check with `git describe --tags --match 'product/v*' --abbrev=0`)

If the tags are missing, refer to `product-development/agentic_work_index.yaml`
to see the intended values and add the tags to the current commit.

The app reads its version from `product-development/app_version.json`, which
should match `product_version.current` in the YAML source of truth.

---

## Active EPIC
- **EPIC:** EPIC 1 — Event Intelligence & Curation
- **Goal:** Enable users to maintain milestone events inside the app with evidence links.
- **Owner:** Unassigned
- **Updated:** 2024-01-01
- **Agents allowed:** 2

---

## Concurrency & EPIC assignments
- **Global agent cap:** 4 total concurrent agents
- **Multi-EPIC work:** Allowed

| EPIC | Agents Allowed |
| --- | --- |
| EPIC 1 — Event Intelligence & Curation | 2 |
| EPIC 2 — Comparative & Benchmarking Views | 1 |

---

## Story Execution Queue

| Story ID | Title | Status | Priority | Size | Acceptance Criteria |
| --- | --- | --- | --- | --- | --- |
| E1-S1 | In-app event editor | ready | P0 | M | Users can add/edit/delete events in the UI, with validation for date and label. |
| E1-S2 | Event CSV import/export | ready | P0 | S | Users can download current events as CSV and upload to replace/add events. |
| E1-S3 | Event taxonomy tags | ready | P1 | S | Events can be tagged by type (earnings, product, regulation, partnership). |
| E1-S4 | Evidence links per event | ready | P1 | S | Each event supports 1+ URLs and shows them in the UI. |
| E1-S5 | Filter by event type | ready | P1 | M | Timeline overlay can be filtered to selected event tags. |

---

## Status Legend
- **ready:** vetted and ready for implementation
- **blocked:** needs clarification or dependency
- **in_progress:** actively being implemented
- **done:** merged and released

---

## Notes
- If the "Active EPIC" changes, update the execution queue to match.
- Regenerate this file from `product-development/agentic_work_index.yaml`
  whenever the underlying data changes.
