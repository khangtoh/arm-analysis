# Git Hooks Mechanism for Agentic Work Index

This document explains how git hooks integrate with the agentic work index system to enable automated validation, conflict prevention, and state synchronization for multi-agent coordination.

## Overview

The git hooks mechanism provides **automated enforcement** of work index rules and **conflict prevention** when multiple agents work concurrently. It ensures:

1. **Validation**: Work index structure and concurrency limits are always valid
2. **Conflict Prevention**: Detects when multiple agents try to claim the same story
3. **State Synchronization**: Auto-regenerates markdown and syncs git tags
4. **Audit Trail**: All changes are tracked through git commits

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Git Hooks Layer                          │
├─────────────────────────────────────────────────────────────┤
│  pre-commit  │  post-commit  │  post-merge  │  pre-push    │
└──────┬──────────────┬──────────────┬──────────────┬─────────┘
       │              │              │              │
       └──────────────┴──────────────┴──────────────┘
                      │
              ┌───────▼────────┐
              │ work_index_    │
              │ validator.py    │  ← Validates work index integrity
              └───────┬────────┘
                      │
       ┌──────────────┼──────────────┐
       │              │              │
┌──────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
│  Validate   │ │ Regenerate  │ │ Sync Tags  │
│  Structure  │ │  Markdown   │ │            │
│  & Limits   │ │             │ │            │
└─────────────┘ └─────────────┘ └─────────────┘
```

## Components

### 1. `work_index_validator.py`

The validator script that validates and maintains work index integrity. It acts as a gatekeeper,
ensuring the work index never enters an invalid state and enforcing all concurrency rules.

**Validator Commands:**
- **`validate`**: Validates YAML structure, concurrency limits, story statuses
- **`regenerate`**: Generates markdown from YAML source of truth
- **`sync-tags`**: Checks/syncs git tags with work index state
- **`check-conflicts`**: Detects potential conflicts in concurrent changes
- **`assign`**: Assigns a story to an agent (with strict concurrency enforcement)

### 2. Git Hooks

#### Pre-Commit Hook

**Purpose**: Validate changes before they're committed

**Triggers**: `git commit`

**Actions**:
1. Check if `agentic_work_index.yaml` is being modified
2. Validate the new state (structure, concurrency limits)
3. Check for conflicts (multiple stories being claimed)
4. Reject commit if validation fails

**Example Output**:
```
ERROR: Validation errors:
  - Too many in_progress stories (3) for EPIC EPIC-1 (allowed: 2)
```

#### Post-Commit Hook

**Purpose**: Auto-regenerate markdown and sync state after commit

**Triggers**: `git commit` (after commit succeeds)

**Actions**:
1. Regenerate `agentic_work_index.md` from YAML
2. Update `app_version.json` with current version
3. Check git tags (warn if missing, optionally create)

**Example Output**:
```
INFO: Regenerated product-development/agentic_work_index.md
INFO: Updated product-development/app_version.json to version v0.1.0
INFO: EPIC tag epic-active/EPIC-1 not found at HEAD. Run: git tag epic-active/EPIC-1
```

#### Post-Merge Hook

**Purpose**: Sync state after pulling changes from remote

**Triggers**: `git merge`, `git pull`

**Actions**:
1. Regenerate markdown (in case remote had YAML changes)
2. Validate merged state
3. Warn about any concurrency limit violations

**Why needed**: When multiple agents push changes, the merge might create invalid states that need detection.

#### Pre-Push Hook

**Purpose**: Final validation before pushing to remote

**Triggers**: `git push`

**Actions**:
1. Validate work index one final time
2. Check concurrency limits
3. Reject push if validation fails

**Why needed**: Prevents pushing invalid states that could break other agents' workflows.

## Workflow Examples

### Agent Starting Work

```bash
# 1. Agent reads work index
cat product-development/agentic_work_index.md

# 2. Agent picks a story (e.g., E1-S1)
# 3. Agent updates YAML: status: "ready" -> "in_progress"
vim product-development/agentic_work_index.yaml

# 4. Agent commits
git add product-development/agentic_work_index.yaml
git commit -m "Assign E1-S1 to agent-1"

# Pre-commit hook runs:
#   - Validates structure ✓
#   - Checks concurrency limits ✓
#   - Detects no conflicts ✓
#   - Commit succeeds

# Post-commit hook runs:
#   - Regenerates markdown ✓
#   - Updates app_version.json ✓
#   - Checks git tags ✓
```

### Conflict Detection

```bash
# Agent 1 and Agent 2 both try to claim E1-S1

# Agent 1 commits first:
git commit -m "Assign E1-S1"
# ✓ Pre-commit passes
# ✓ Commit succeeds

# Agent 2 tries to commit:
git commit -m "Assign E1-S1"
# ✗ Pre-commit detects:
#   - Story E1-S1 already in_progress
#   - Commit rejected
```

### Concurrency Limit Enforcement

```bash
# EPIC-1 allows 2 agents, but 3 try to start work

# Agent 1: E1-S1 -> in_progress ✓
# Agent 2: E1-S2 -> in_progress ✓
# Agent 3: E1-S3 -> in_progress ✗

# Pre-commit hook detects:
# ERROR: Too many in_progress stories (3) for EPIC EPIC-1 (allowed: 2)
# Commit rejected
```

## Validation Rules

### Structure Validation

- All required fields present (`version`, `product_version`, `concurrency`, `active_epic`, `epics`, `stories`)
- Active EPIC exists in epics list
- All stories have valid IDs (no duplicates)
- All stories have valid statuses (`ready`, `blocked`, `in_progress`, `done`)

### Concurrency Validation

- **Global limit**: Total `in_progress` stories ≤ `max_agents_total`
- **Per-EPIC limit**: `in_progress` stories for active EPIC ≤ `agents_allowed` for that EPIC
- **Multi-EPIC**: If `allow_multi_epic: false`, only active EPIC stories can be `in_progress`

### Story Assignment Validation

- Cannot assign `done` stories
- Cannot assign already `in_progress` stories
- Assignment must respect concurrency limits

## Git Tags Integration

The work index uses git tags as **anchors** for versioning:

- **EPIC tag**: `epic-active/EPIC-1` - Points to commit where EPIC-1 is active
- **Version tag**: `product/v0.1.0` - Points to commit with product version

**Checking tags**:
```bash
# Check active EPIC
git tag --points-at HEAD 'epic-active/*'

# Check product version
git describe --tags --match 'product/v*' --abbrev=0
```

**Creating tags** (if missing):
```bash
# Manual
git tag epic-active/EPIC-1
git tag product/v0.1.0

# Automatic (via helper)
./scripts/work_index_validator.py sync-tags --create
```

## Conflict Resolution

When conflicts occur (e.g., merge conflicts in YAML):

1. **Resolve merge conflict** in `agentic_work_index.yaml`
2. **Validate resolved state**:
   ```bash
   ./scripts/work_index_validator.py validate
   ```
3. **Regenerate markdown**:
   ```bash
   ./scripts/work_index_validator.py regenerate
   ```
4. **Complete merge**:
   ```bash
   git add product-development/agentic_work_index.yaml
   git commit
   ```

## Best Practices

### For Agents

1. **Always validate before committing**:
   ```bash
   ./scripts/work_index_validator.py validate
   ```

2. **Use explicit assignment** (optional but recommended):
   ```bash
   ./scripts/work_index_validator.py assign E1-S1 agent-1
   ```

3. **Check concurrency before starting**:
   - Read the markdown to see current `in_progress` count
   - Ensure you're within limits

4. **Pull before starting work**:
   ```bash
   git pull  # Post-merge hook will sync state
   ```

### For Maintainers

1. **Keep YAML as source of truth**: Never edit markdown directly
2. **Regenerate after manual YAML edits**:
   ```bash
   ./scripts/work_index_validator.py regenerate
   ```
3. **Monitor concurrency**: Check `in_progress` counts regularly
4. **Tag releases**: Create git tags when EPICs or versions change

## Troubleshooting

### Hook Not Running

```bash
# Check if hooks are executable
ls -la .git/hooks/pre-commit

# Make executable
chmod +x .git/hooks/pre-commit
```

### Validation Failing

```bash
# Get detailed errors
./scripts/work_index_validator.py validate

# Check specific story
grep -A 10 "E1-S1" product-development/agentic_work_index.yaml
```

### Tags Out of Sync

```bash
# Check current tags
git tag --points-at HEAD

# Sync tags
./scripts/work_index_validator.py sync-tags --create
```

### Merge Conflicts

```bash
# After resolving conflict, validate
./scripts/work_index_validator.py validate

# Regenerate
./scripts/work_index_validator.py regenerate

# Commit
git add product-development/agentic_work_index.yaml
git commit
```

## Comparison with Gas Town

| Feature | Agentic Work Index | Gas Town |
|---------|-------------------|----------|
| **State Management** | Git commits + YAML | Git worktrees (hooks) |
| **Conflict Detection** | Pre-commit validation | Git merge conflicts |
| **Isolation** | Git branches | Separate worktrees |
| **Coordination** | YAML status tracking | Convoys + Mayor |
| **Persistence** | Git history | Persistent worktrees |

**Key Difference**: Our approach uses **git-native** validation and coordination, while Gas Town uses **separate worktrees** for isolation. Both are valid; ours is simpler but requires more discipline around git workflows.

## Future Enhancements

Potential improvements:

1. **Agent assignment tracking**: Add `assigned_to` and `assigned_at` fields
2. **Lock mechanism**: Use git notes or separate lock file for story claims
3. **Webhook integration**: Notify external systems on status changes
4. **Dashboard**: Real-time view of work index state
5. **Automated conflict resolution**: Smart merge strategies for common conflicts
