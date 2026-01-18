#!/usr/bin/env python3
"""
Validator script for agentic work index operations.
Validates and maintains the integrity of the work index system.

This validator ensures:
- Work index structure and concurrency limits are always valid
- Automatic markdown regeneration from YAML source of truth
- Git tag synchronization with work index state
- Conflict detection and prevention for concurrent agent work
- Story assignment tracking with concurrency enforcement

The validator acts as a gatekeeper, preventing invalid states from being committed
and maintaining consistency across the multi-agent coordination system.
"""

import json
import logging
import subprocess
import sys
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent
WORK_INDEX_YAML = REPO_ROOT / "product-development" / "agentic_work_index.yaml"
WORK_INDEX_MD = REPO_ROOT / "product-development" / "agentic_work_index.md"
APP_VERSION_JSON = REPO_ROOT / "product-development" / "app_version.json"


@dataclass
class ValidationResult:
    """Result of work index validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


@dataclass
class StoryAssignment:
    """Tracks story assignment to an agent."""
    story_id: str
    agent_id: Optional[str]
    assigned_at: Optional[str]
    status: str


def load_work_index() -> Dict:
    """Load the work index YAML file."""
    if not WORK_INDEX_YAML.exists():
        logger.error(f"{WORK_INDEX_YAML} not found")
        sys.exit(1)
    
    try:
        with open(WORK_INDEX_YAML, 'r') as f:
            data = yaml.safe_load(f)
            if data is None:
                logger.error(f"{WORK_INDEX_YAML} is empty or invalid")
                sys.exit(1)
            return data
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load work index: {e}")
        sys.exit(1)


def save_work_index(data: Dict) -> None:
    """Save the work index YAML file."""
    with open(WORK_INDEX_YAML, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def validate_work_index(data: Dict) -> ValidationResult:
    """Validate work index structure and constraints."""
    errors = []
    warnings = []
    
    # Check required fields
    required_fields = ['version', 'product_version', 'concurrency', 'active_epic', 'epics', 'stories']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return ValidationResult(False, errors, warnings)
    
    # Validate concurrency limits
    concurrency = data.get('concurrency', {})
    max_agents = concurrency.get('max_agents_total', 0)
    if max_agents <= 0:
        errors.append("max_agents_total must be > 0")
    
    # Validate active epic exists in epics list
    active_epic_id = data.get('active_epic', {}).get('id')
    epic_ids = [epic.get('id') for epic in data.get('epics', [])]
    if active_epic_id and active_epic_id not in epic_ids:
        errors.append(f"Active EPIC {active_epic_id} not found in epics list")
    
    # Validate story statuses and structure
    valid_statuses = ['ready', 'blocked', 'in_progress', 'done']
    story_ids: Set[str] = set()
    for story in data.get('stories', []):
        story_id = story.get('id')
        if not story_id:
            errors.append("Story missing required 'id' field")
            continue
        
        if story_id in story_ids:
            errors.append(f"Duplicate story ID: {story_id}")
        story_ids.add(story_id)
        
        status = story.get('status')
        if not status:
            errors.append(f"Story {story_id} missing 'status' field")
        elif status not in valid_statuses:
            errors.append(f"Story {story_id} has invalid status: {status}")
        
        if not story.get('acceptance_criteria'):
            warnings.append(f"Story {story_id} has no acceptance criteria")
    
    # Check concurrency limits: count in_progress stories per EPIC
    active_epic_id = data.get('active_epic', {}).get('id')
    if active_epic_id:
        epic_agents_allowed = next(
            (epic.get('agents_allowed', 0) for epic in data.get('epics', []) 
             if epic.get('id') == active_epic_id),
            0
        )
        in_progress_count = sum(
            1 for story in data.get('stories', [])
            if story.get('status') == 'in_progress'
        )
        if in_progress_count > epic_agents_allowed:
            errors.append(
                f"Too many in_progress stories ({in_progress_count}) for EPIC {active_epic_id} "
                f"(allowed: {epic_agents_allowed})"
            )
    
    # Check global concurrency limit
    total_in_progress = sum(
        1 for story in data.get('stories', [])
        if story.get('status') == 'in_progress'
    )
    if total_in_progress > max_agents:
        errors.append(
            f"Global concurrency limit exceeded: {total_in_progress} in_progress stories "
            f"(max: {max_agents})"
        )
    
    # Validate product version format
    product_version = data.get('product_version', {})
    version_current = product_version.get('current', '')
    if version_current and not version_current.startswith('v'):
        warnings.append(f"Product version '{version_current}' should start with 'v'")
    
    return ValidationResult(len(errors) == 0, errors, warnings)


def regenerate_markdown(data: Dict) -> None:
    """Regenerate the markdown file from YAML data."""
    lines = [
        "# Agentic Work Index (Start Here)",
        "",
        "This file tells a coding agent **what to work on next** after cloning the repo.",
        "It is a **generated view** of the machine-readable work database in",
        "`product-development/agentic_work_index.yaml` and is anchored to Git-native",
        "metadata for both the active EPIC and the current product version.",
        "",
        "---",
        "",
        "## How to use this file",
        "1. **Start at the \"Active EPIC\" section** to see the current focus area.",
        "2. Pick the **highest-priority story** that is `ready` and unassigned.",
        "3. Use the story acceptance criteria as the implementation checklist.",
        "4. When a story is complete, update the status and add a short outcome note.",
        "",
        "---",
        "",
        "## Git-native anchors (source of truth)",
    ]
    
    # Git tags section
    active_epic = data.get('active_epic', {})
    product_version = data.get('product_version', {})
    epic_tag = active_epic.get('git_tag', '')
    version_tag = product_version.get('git_tag', '')
    version_current = product_version.get('current', '')
    
    lines.extend([
        f"- **Active EPIC tag:** `{epic_tag}` (check with `git tag --points-at HEAD 'epic-active/*'`)",
        f"- **Product version:** `{version_current}` (tag `{version_tag}`, check with `git describe --tags --match 'product/v*' --abbrev=0`)",
        "",
        "If the tags are missing, refer to `product-development/agentic_work_index.yaml`",
        "to see the intended values and add the tags to the current commit.",
        "",
        "The app reads its version from `product-development/app_version.json`, which",
        "should match `product_version.current` in the YAML source of truth.",
        "",
        "---",
        "",
        "## Active EPIC",
    ])
    
    # Active EPIC section
    lines.extend([
        f"- **EPIC:** {active_epic.get('id')} — {active_epic.get('name', '')}",
        f"- **Goal:** {active_epic.get('goal', '')}",
        f"- **Owner:** {active_epic.get('owner', 'Unassigned')}",
        f"- **Updated:** {active_epic.get('updated', '')}",
        f"- **Agents allowed:** {active_epic.get('agents_allowed', 0)}",
        "",
        "---",
        "",
        "## Concurrency & EPIC assignments",
    ])
    
    # Concurrency section
    concurrency = data.get('concurrency', {})
    lines.extend([
        f"- **Global agent cap:** {concurrency.get('max_agents_total', 0)} total concurrent agents",
        f"- **Multi-EPIC work:** {'Allowed' if concurrency.get('allow_multi_epic') else 'Not allowed'}",
        "",
        "| EPIC | Agents Allowed |",
        "| --- | --- |",
    ])
    
    for epic in data.get('epics', []):
        lines.append(f"| {epic.get('id')} — {epic.get('name', '')} | {epic.get('agents_allowed', 0)} |")
    
    lines.extend([
        "",
        "---",
        "",
        "## Story Execution Queue",
        "",
        "| Story ID | Title | Status | Priority | Size | Acceptance Criteria |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    
    # Stories table
    for story in data.get('stories', []):
        story_id = story.get('id', '')
        title = story.get('title', '')
        status = story.get('status', '')
        priority = story.get('priority', '')
        size = story.get('size', '')
        criteria = '; '.join(story.get('acceptance_criteria', []))
        lines.append(f"| {story_id} | {title} | {status} | {priority} | {size} | {criteria} |")
    
    lines.extend([
        "",
        "---",
        "",
        "## Status Legend",
        "- **ready:** vetted and ready for implementation",
        "- **blocked:** needs clarification or dependency",
        "- **in_progress:** actively being implemented",
        "- **done:** merged and released",
        "",
        "---",
        "",
        "## Notes",
        "- If the \"Active EPIC\" changes, update the execution queue to match.",
        "- Regenerate this file from `product-development/agentic_work_index.yaml`",
        "  whenever the underlying data changes.",
        "",
    ])
    
    WORK_INDEX_MD.write_text('\n'.join(lines))
    print(f"Regenerated {WORK_INDEX_MD}")


def update_app_version(data: Dict) -> None:
    """Update app_version.json from YAML data."""
    version = data.get('product_version', {}).get('current', '')
    if version:
        version_data = {"version": version}
        with open(APP_VERSION_JSON, 'w') as f:
            json.dump(version_data, f, indent=2)
        print(f"Updated {APP_VERSION_JSON} to version {version}")


def sync_git_tags(data: Dict, create_missing: bool = False) -> Tuple[bool, List[str]]:
    """Sync git tags with work index data.
    
    Args:
        data: Work index data
        create_missing: If True, create missing tags at HEAD
    
    Returns:
        Tuple of (success, list of messages)
    """
    messages = []
    active_epic = data.get('active_epic', {})
    product_version = data.get('product_version', {})
    
    epic_tag = active_epic.get('git_tag', '')
    version_tag = product_version.get('git_tag', '')
    
    # Check EPIC tag
    try:
        result = subprocess.run(
            ['git', 'tag', '--points-at', 'HEAD', epic_tag],
            capture_output=True,
            text=True,
            check=False,
            cwd=REPO_ROOT
        )
        if not result.stdout.strip():
            if create_missing:
                subprocess.run(
                    ['git', 'tag', epic_tag],
                    check=True,
                    cwd=REPO_ROOT,
                    capture_output=True
                )
                messages.append(f"Created EPIC tag: {epic_tag}")
            else:
                messages.append(f"EPIC tag {epic_tag} not found at HEAD. Run: git tag {epic_tag}")
    except subprocess.CalledProcessError as e:
        logger.warning(f"Could not check/create EPIC tag: {e}")
        return False, messages
    except Exception as e:
        logger.warning(f"Error checking EPIC tag: {e}")
    
    # Check version tag
    try:
        result = subprocess.run(
            ['git', 'tag', '--points-at', 'HEAD', version_tag],
            capture_output=True,
            text=True,
            check=False,
            cwd=REPO_ROOT
        )
        if not result.stdout.strip():
            if create_missing:
                subprocess.run(
                    ['git', 'tag', version_tag],
                    check=True,
                    cwd=REPO_ROOT,
                    capture_output=True
                )
                messages.append(f"Created version tag: {version_tag}")
            else:
                messages.append(f"Version tag {version_tag} not found at HEAD. Run: git tag {version_tag}")
    except subprocess.CalledProcessError as e:
        logger.warning(f"Could not check/create version tag: {e}")
        return False, messages
    except Exception as e:
        logger.warning(f"Error checking version tag: {e}")
    
    return True, messages


def get_git_diff(staged: bool = False) -> str:
    """Get git diff for work index file."""
    try:
        work_index_path = str(WORK_INDEX_YAML.relative_to(REPO_ROOT))
        cmd = ['git', 'diff']
        if staged:
            cmd.append('--cached')
        cmd.append(work_index_path)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=REPO_ROOT
        )
        return result.stdout
    except Exception as e:
        logger.warning(f"Could not get git diff: {e}")
        return ""


def check_story_conflicts(data: Dict, changed_files: List[str]) -> ValidationResult:
    """Check if story status changes would cause conflicts with concurrent work."""
    errors = []
    warnings = []
    work_index_path = str(WORK_INDEX_YAML.relative_to(REPO_ROOT))
    
    if work_index_path not in changed_files:
        return ValidationResult(True, [], [])
    
    # Get git diff to see what changed
    diff = get_git_diff(staged=True)
    if not diff:
        # If no staged diff, check unstaged
        diff = get_git_diff(staged=False)
    
    # Parse diff to find story status changes
    # Look for lines like: -    status: "ready" or +    status: "in_progress"
    import re
    status_changes = re.findall(r'[-+]\s+status:\s+"(\w+)"', diff)
    
    if len(status_changes) >= 2:
        # Check if multiple stories are being changed to in_progress
        in_progress_changes = [s for s in status_changes if s == 'in_progress']
        if len(in_progress_changes) > 1:
            warnings.append(
                f"Multiple stories being set to 'in_progress' ({len(in_progress_changes)}). "
                "Ensure concurrency limits are respected."
            )
    
    # Validate final state
    validation = validate_work_index(data)
    errors.extend(validation.errors)
    warnings.extend(validation.warnings)
    
    return ValidationResult(len(errors) == 0, errors, warnings)


def get_story_by_id(data: Dict, story_id: str) -> Optional[Dict]:
    """Get a story by its ID."""
    return next((s for s in data.get('stories', []) if s.get('id') == story_id), None)


def assign_story(data: Dict, story_id: str, agent_id: Optional[str] = None) -> Tuple[bool, str]:
    """Assign a story to an agent (set status to in_progress).
    
    Returns:
        Tuple of (success, message)
    """
    story = get_story_by_id(data, story_id)
    if not story:
        return False, f"Story {story_id} not found"
    
    current_status = story.get('status')
    if current_status == 'in_progress':
        return False, f"Story {story_id} is already in_progress"
    
    if current_status == 'done':
        return False, f"Story {story_id} is already done"
    
    # Check concurrency limits BEFORE assignment
    # Count current in_progress stories (excluding the one we're about to assign)
    current_in_progress = sum(
        1 for s in data.get('stories', [])
        if s.get('status') == 'in_progress'
    )
    
    # Check global concurrency limit
    max_agents = data.get('concurrency', {}).get('max_agents_total', 0)
    if current_in_progress >= max_agents:
        return False, (
            f"Cannot assign: global concurrency limit reached "
            f"({current_in_progress}/{max_agents}). "
            f"Wait for a story to complete before assigning more."
        )
    
    # Check per-EPIC concurrency limit
    active_epic_id = data.get('active_epic', {}).get('id')
    if active_epic_id:
        # Extract EPIC identifier from story ID (e.g., "E1-S1" -> "E1" maps to "EPIC-1")
        story_epic_prefix = story_id.split('-')[0] if '-' in story_id else None
        
        # Map story prefix to EPIC ID (e.g., "E1" -> "EPIC-1", "E2" -> "EPIC-2")
        # Story IDs like "E1-S1" have prefix "E1" which corresponds to "EPIC-1"
        story_epic_id = None
        if story_epic_prefix and story_epic_prefix.startswith('E'):
            try:
                epic_num = story_epic_prefix[1:]  # Extract number after 'E'
                story_epic_id = f"EPIC-{epic_num}"
            except (ValueError, IndexError):
                pass
        
        # Only check if this story belongs to the active EPIC
        if story_epic_id and story_epic_id == active_epic_id:
            epic_agents_allowed = next(
                (epic.get('agents_allowed', 0) for epic in data.get('epics', [])
                 if epic.get('id') == active_epic_id),
                0
            )
            
            # Count in_progress stories for this EPIC (stories with same EPIC prefix)
            epic_in_progress = sum(
                1 for s in data.get('stories', [])
                if s.get('status') == 'in_progress' and 
                s.get('id', '').split('-')[0] == story_epic_prefix
            )
            
            if epic_in_progress >= epic_agents_allowed:
                return False, (
                    f"Cannot assign: EPIC {active_epic_id} concurrency limit reached "
                    f"({epic_in_progress}/{epic_agents_allowed}). "
                    f"Wait for a story in this EPIC to complete."
                )
    
    # All checks passed - assign the story
    story['status'] = 'in_progress'
    if agent_id:
        story['assigned_to'] = agent_id
        story['assigned_at'] = datetime.now().isoformat()
    
    return True, f"Assigned story {story_id} to {agent_id or 'agent'}"


def main():
    """Main entry point for work index operations."""
    if len(sys.argv) < 2:
        print("Usage: work_index_validator.py <command> [args...]")
        print("Commands:")
        print("  validate              - Validate work index structure and constraints")
        print("  regenerate            - Regenerate markdown from YAML")
        print("  sync-tags [--create]  - Check/sync git tags (--create to create missing)")
        print("  check-conflicts <files...> - Check for conflicts in changed files")
        print("  assign <story-id> [agent-id] - Assign story to agent")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'validate':
        data = load_work_index()
        result = validate_work_index(data)
        if not result.is_valid:
            logger.error("Validation errors:")
            for error in result.errors:
                logger.error(f"  - {error}")
            sys.exit(1)
        if result.warnings:
            for warning in result.warnings:
                logger.warning(f"  - {warning}")
        logger.info("Work index validation passed")
    
    elif command == 'regenerate':
        data = load_work_index()
        # Validate before regenerating
        result = validate_work_index(data)
        if not result.is_valid:
            logger.error("Cannot regenerate: validation failed")
            for error in result.errors:
                logger.error(f"  - {error}")
            sys.exit(1)
        regenerate_markdown(data)
        update_app_version(data)
        logger.info("Regeneration complete")
    
    elif command == 'sync-tags':
        data = load_work_index()
        create_missing = '--create' in sys.argv
        success, messages = sync_git_tags(data, create_missing=create_missing)
        for msg in messages:
            logger.info(msg)
        if not success:
            sys.exit(1)
    
    elif command == 'check-conflicts':
        changed_files = sys.argv[2:] if len(sys.argv) > 2 else []
        data = load_work_index()
        result = check_story_conflicts(data, changed_files)
        if not result.is_valid:
            for error in result.errors:
                logger.error(error)
            sys.exit(1)
        if result.warnings:
            for warning in result.warnings:
                logger.warning(warning)
    
    elif command == 'assign':
        if len(sys.argv) < 3:
            logger.error("Usage: work_index_validator.py assign <story-id> [agent-id]")
            sys.exit(1)
        story_id = sys.argv[2]
        agent_id = sys.argv[3] if len(sys.argv) > 3 else None
        data = load_work_index()
        success, message = assign_story(data, story_id, agent_id)
        if success:
            save_work_index(data)
            logger.info(message)
        else:
            logger.error(message)
            sys.exit(1)
    
    else:
        logger.error(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
