# Add Work Index Validator with Git Hooks Mechanism

## Summary

This PR introduces a comprehensive validation and enforcement system for the agentic work index, enabling safe multi-agent coordination through git hooks integration.

## What's Changed

### Core Components

1. **`scripts/work_index_validator.py`** - Main validator script that:
   - Validates work index YAML structure and concurrency limits
   - Enforces strict concurrency rules (global and per-EPIC)
   - Regenerates markdown from YAML source of truth
   - Synchronizes git tags with work index state
   - Detects conflicts in concurrent agent work
   - Manages story assignments with concurrency enforcement

2. **`tests/test_work_index_validator.py`** - Comprehensive test suite covering:
   - Validation logic (structure, concurrency, statuses)
   - Story assignment with concurrency enforcement
   - Markdown regeneration
   - Git tag synchronization
   - Conflict detection

3. **`product-development/GIT_HOOKS_MECHANISM.md`** - Complete documentation explaining:
   - How git hooks integrate with work index
   - Pre-commit, post-commit, post-merge, and pre-push workflows
   - Validation rules and concurrency enforcement
   - Conflict resolution strategies
   - Best practices for agents and maintainers

## Key Features

### Validation & Enforcement
- ✅ Validates work index structure (required fields, story IDs, statuses)
- ✅ Enforces global concurrency limits (`max_agents_total`)
- ✅ Enforces per-EPIC concurrency limits (`agents_allowed`)
- ✅ Prevents invalid story assignments
- ✅ Detects duplicate story IDs

### State Management
- ✅ Auto-regenerates markdown from YAML source
- ✅ Syncs `app_version.json` with product version
- ✅ Validates git tag alignment with work index state
- ✅ Tracks story assignments with timestamps

### Bug Fixes
- 🐛 **Fixed**: `assign_story` now properly enforces concurrency limits even when current state is valid
- 🐛 **Fixed**: EPIC ID mapping for story assignment (E1 → EPIC-1)
- 🐛 **Fixed**: `validate_work_index` and `assign_story` now use consistent limit checks (>= instead of >)
- 🐛 **Fixed**: `allow_multi_epic` constraint now enforced in both validation and assignment
- 🐛 **Fixed**: `check_story_conflicts` only counts added lines for in_progress stories
- 🐛 **Fixed**: `sync_git_tags` now checks both tags independently
- 🐛 **Fixed**: Per-EPIC concurrency check now properly filters by active EPIC ID
- 🐛 **Fixed**: `assign_story` now returns value and sets `assigned_to` field correctly
- 🐛 **Fixed**: Restored streamlit and plotly dependencies

## Testing

Run tests with:
```bash
pytest tests/test_work_index_validator.py -v
```

All tests pass, including:
- Validation of valid and invalid work index states
- Concurrency limit enforcement
- Story assignment workflows
- Markdown regeneration
- Git tag synchronization

## Usage

### Validate work index
```bash
./scripts/work_index_validator.py validate
```

### Assign story to agent
```bash
./scripts/work_index_validator.py assign E1-S1 agent-1
```

### Regenerate markdown
```bash
./scripts/work_index_validator.py regenerate
```

### Sync git tags
```bash
./scripts/work_index_validator.py sync-tags --create
```

## Git Hooks Integration

The validator is designed to be used with git hooks:

- **pre-commit**: Validates changes before commit
- **post-commit**: Auto-regenerates markdown and syncs state
- **post-merge**: Syncs state after pulling changes
- **pre-push**: Final validation before pushing

See `product-development/GIT_HOOKS_MECHANISM.md` for detailed hook implementation examples.

## Dependencies

- `pyyaml>=6.0` - YAML parsing
- `pytest>=7.0` - Testing framework

## Documentation

- `product-development/GIT_HOOKS_MECHANISM.md` - Complete git hooks mechanism documentation
- `NAME_SUGGESTIONS.md` - Naming rationale (can be removed if desired)

## Breaking Changes

None - this is a new feature addition.

## Next Steps

1. Implement actual git hooks (pre-commit, post-commit, etc.) using the validator
2. Add agent assignment tracking fields to YAML schema
3. Consider adding a webhook/dashboard for real-time work index monitoring

## Related Issues

N/A - New feature
