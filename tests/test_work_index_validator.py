#!/usr/bin/env python3
"""
Tests for work_index_validator.py

Run with: pytest tests/test_work_index_validator.py -v
"""

import json
import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module (adjust path as needed)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from work_index_validator import (
    load_work_index,
    save_work_index,
    validate_work_index,
    regenerate_markdown,
    update_app_version,
    sync_git_tags,
    check_story_conflicts,
    assign_story,
    get_story_by_id,
    ValidationResult,
)


@pytest.fixture
def temp_repo(tmp_path):
    """Create a temporary repository structure."""
    repo = tmp_path / "repo"
    repo.mkdir()
    
    product_dev = repo / "product-development"
    product_dev.mkdir()
    
    scripts = repo / "scripts"
    scripts.mkdir()
    
    return repo


@pytest.fixture
def valid_work_index_data():
    """Sample valid work index data."""
    return {
        "version": 1,
        "product_version": {
            "current": "v0.1.0",
            "git_tag": "product/v0.1.0"
        },
        "concurrency": {
            "max_agents_total": 4,
            "allow_multi_epic": True
        },
        "active_epic": {
            "id": "EPIC-1",
            "name": "Event Intelligence & Curation",
            "goal": "Enable users to maintain milestone events",
            "owner": "Unassigned",
            "updated": "2024-01-01",
            "git_tag": "epic-active/EPIC-1",
            "agents_allowed": 2
        },
        "epics": [
            {
                "id": "EPIC-1",
                "name": "Event Intelligence & Curation",
                "agents_allowed": 2
            },
            {
                "id": "EPIC-2",
                "name": "Comparative & Benchmarking Views",
                "agents_allowed": 1
            }
        ],
        "stories": [
            {
                "id": "E1-S1",
                "title": "In-app event editor",
                "status": "ready",
                "priority": "P0",
                "size": "M",
                "acceptance_criteria": ["Users can add/edit/delete events"]
            },
            {
                "id": "E1-S2",
                "title": "Event CSV import/export",
                "status": "ready",
                "priority": "P0",
                "size": "S",
                "acceptance_criteria": ["Users can download/upload CSV"]
            },
            {
                "id": "E1-S3",
                "title": "Event taxonomy tags",
                "status": "ready",
                "priority": "P1",
                "size": "S",
                "acceptance_criteria": ["Events can be tagged by type"]
            }
        ]
    }


@pytest.fixture
def work_index_file(temp_repo, valid_work_index_data):
    """Create a work index YAML file."""
    yaml_file = temp_repo / "product-development" / "agentic_work_index.yaml"
    yaml_file.parent.mkdir(parents=True)
    
    with open(yaml_file, 'w') as f:
        yaml.dump(valid_work_index_data, f)
    
    return yaml_file


class TestLoadWorkIndex:
    """Tests for load_work_index function."""
    
    def test_load_valid_yaml(self, temp_repo, valid_work_index_data):
        """Test loading a valid YAML file."""
        yaml_file = temp_repo / "work_index.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(valid_work_index_data, f)
        
        # Mock REPO_ROOT
        with patch('work_index_validator.REPO_ROOT', temp_repo):
            with patch('work_index_validator.WORK_INDEX_YAML', yaml_file):
                data = load_work_index()
                assert data['version'] == 1
                assert data['active_epic']['id'] == "EPIC-1"
    
    def test_load_missing_file(self, temp_repo):
        """Test loading a missing file."""
        yaml_file = temp_repo / "nonexistent.yaml"
        
        with patch('work_index_validator.REPO_ROOT', temp_repo):
            with patch('work_index_validator.WORK_INDEX_YAML', yaml_file):
                with pytest.raises(SystemExit):
                    load_work_index()
    
    def test_load_invalid_yaml(self, temp_repo):
        """Test loading invalid YAML."""
        yaml_file = temp_repo / "invalid.yaml"
        yaml_file.write_text("invalid: yaml: content: [")
        
        with patch('work_index_validator.REPO_ROOT', temp_repo):
            with patch('work_index_validator.WORK_INDEX_YAML', yaml_file):
                with pytest.raises(SystemExit):
                    load_work_index()


class TestValidateWorkIndex:
    """Tests for validate_work_index function."""
    
    def test_validate_valid_data(self, valid_work_index_data):
        """Test validation of valid data."""
        result = validate_work_index(valid_work_index_data)
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_missing_required_field(self, valid_work_index_data):
        """Test validation with missing required field."""
        del valid_work_index_data['version']
        result = validate_work_index(valid_work_index_data)
        assert result.is_valid is False
        assert any('version' in error for error in result.errors)
    
    def test_validate_invalid_concurrency(self, valid_work_index_data):
        """Test validation with invalid concurrency limit."""
        valid_work_index_data['concurrency']['max_agents_total'] = 0
        result = validate_work_index(valid_work_index_data)
        assert result.is_valid is False
        assert any('max_agents_total' in error for error in result.errors)
    
    def test_validate_active_epic_not_in_list(self, valid_work_index_data):
        """Test validation when active EPIC not in epics list."""
        valid_work_index_data['active_epic']['id'] = "EPIC-99"
        result = validate_work_index(valid_work_index_data)
        assert result.is_valid is False
        assert any('EPIC-99' in error for error in result.errors)
    
    def test_validate_invalid_story_status(self, valid_work_index_data):
        """Test validation with invalid story status."""
        valid_work_index_data['stories'][0]['status'] = "invalid_status"
        result = validate_work_index(valid_work_index_data)
        assert result.is_valid is False
        assert any('invalid status' in error.lower() for error in result.errors)
    
    def test_validate_duplicate_story_id(self, valid_work_index_data):
        """Test validation with duplicate story IDs."""
        valid_work_index_data['stories'].append({
            "id": "E1-S1",  # Duplicate
            "title": "Duplicate",
            "status": "ready"
        })
        result = validate_work_index(valid_work_index_data)
        assert result.is_valid is False
        assert any('Duplicate' in error for error in result.errors)
    
    def test_validate_concurrency_limit_exceeded(self, valid_work_index_data):
        """Test validation when concurrency limit is exceeded."""
        # Set 3 stories to in_progress, but EPIC-1 only allows 2
        valid_work_index_data['stories'][0]['status'] = "in_progress"
        valid_work_index_data['stories'][1]['status'] = "in_progress"
        valid_work_index_data['stories'].append({
            "id": "E1-S3",
            "title": "Third story",
            "status": "in_progress",
            "priority": "P0",
            "size": "S",
            "acceptance_criteria": []
        })
        
        result = validate_work_index(valid_work_index_data)
        assert result.is_valid is False
        assert any('Too many in_progress' in error for error in result.errors)
    
    def test_validate_global_concurrency_limit(self, valid_work_index_data):
        """Test validation of global concurrency limit."""
        # Set max_agents_total to 2, but have 3 in_progress
        valid_work_index_data['concurrency']['max_agents_total'] = 2
        valid_work_index_data['stories'][0]['status'] = "in_progress"
        valid_work_index_data['stories'][1]['status'] = "in_progress"
        valid_work_index_data['stories'].append({
            "id": "E1-S3",
            "title": "Third story",
            "status": "in_progress",
            "priority": "P0",
            "size": "S",
            "acceptance_criteria": []
        })
        
        result = validate_work_index(valid_work_index_data)
        assert result.is_valid is False
        assert any('Global concurrency limit' in error for error in result.errors)
    
    def test_validate_warning_no_acceptance_criteria(self, valid_work_index_data):
        """Test validation warning for missing acceptance criteria."""
        valid_work_index_data['stories'][0]['acceptance_criteria'] = []
        result = validate_work_index(valid_work_index_data)
        assert result.is_valid is True  # Warning, not error
        assert len(result.warnings) > 0
        assert any('acceptance criteria' in warning.lower() for warning in result.warnings)


class TestRegenerateMarkdown:
    """Tests for regenerate_markdown function."""
    
    def test_regenerate_markdown(self, temp_repo, valid_work_index_data):
        """Test markdown regeneration."""
        md_file = temp_repo / "work_index.md"
        
        with patch('work_index_validator.REPO_ROOT', temp_repo):
            with patch('work_index_validator.WORK_INDEX_MD', md_file):
                regenerate_markdown(valid_work_index_data)
                
                assert md_file.exists()
                content = md_file.read_text()
                assert "# Agentic Work Index" in content
                assert "EPIC-1" in content
                assert "E1-S1" in content
                assert "ready" in content


class TestUpdateAppVersion:
    """Tests for update_app_version function."""
    
    def test_update_app_version(self, temp_repo, valid_work_index_data):
        """Test app version update."""
        version_file = temp_repo / "app_version.json"
        
        with patch('work_index_validator.REPO_ROOT', temp_repo):
            with patch('work_index_validator.APP_VERSION_JSON', version_file):
                update_app_version(valid_work_index_data)
                
                assert version_file.exists()
                data = json.loads(version_file.read_text())
                assert data['version'] == "v0.1.0"


class TestAssignStory:
    """Tests for assign_story function."""
    
    def test_assign_ready_story(self, valid_work_index_data):
        """Test assigning a ready story."""
        success, message = assign_story(valid_work_index_data, "E1-S1", "agent-1")
        assert success is True
        assert "agent-1" in message
        
        story = get_story_by_id(valid_work_index_data, "E1-S1")
        assert story['status'] == "in_progress"
        assert story.get('assigned_to') == "agent-1"
    
    def test_assign_already_in_progress(self, valid_work_index_data):
        """Test assigning a story that's already in_progress."""
        valid_work_index_data['stories'][0]['status'] = "in_progress"
        success, message = assign_story(valid_work_index_data, "E1-S1", "agent-1")
        assert success is False
        assert "already in_progress" in message
    
    def test_assign_done_story(self, valid_work_index_data):
        """Test assigning a done story."""
        valid_work_index_data['stories'][0]['status'] = "done"
        success, message = assign_story(valid_work_index_data, "E1-S1", "agent-1")
        assert success is False
        assert "already done" in message
    
    def test_assign_nonexistent_story(self, valid_work_index_data):
        """Test assigning a story that doesn't exist."""
        success, message = assign_story(valid_work_index_data, "E1-S99", "agent-1")
        assert success is False
        assert "not found" in message
    
    def test_assign_enforces_global_concurrency_when_valid(self, valid_work_index_data):
        """Test that assign_story enforces concurrency limits even when current state is valid.
        
        This test verifies the bug fix: concurrency checks should always run,
        not only when validation fails.
        """
        # Set max_agents_total to 2
        valid_work_index_data['concurrency']['max_agents_total'] = 2
        
        # Set 2 stories to in_progress (at the limit, but still valid)
        valid_work_index_data['stories'][0]['status'] = "in_progress"
        valid_work_index_data['stories'][1]['status'] = "in_progress"
        
        # Try to assign a third story - should fail even though current state is valid
        success, message = assign_story(valid_work_index_data, "E1-S3", "agent-1")
        assert success is False
        assert "global concurrency limit" in message.lower()
        assert "2" in message  # Should mention the limit
    
    def test_assign_enforces_epic_concurrency_when_valid(self, valid_work_index_data):
        """Test that assign_story enforces EPIC concurrency limits even when current state is valid."""
        # EPIC-1 allows 2 agents
        # Set 2 stories to in_progress (at the limit)
        valid_work_index_data['stories'][0]['status'] = "in_progress"
        valid_work_index_data['stories'][1]['status'] = "in_progress"
        
        # Try to assign a third story in EPIC-1 - should fail
        success, message = assign_story(valid_work_index_data, "E1-S3", "agent-1")
        assert success is False
        assert "EPIC" in message or "concurrency limit" in message.lower()
    
    def test_assign_succeeds_when_under_limit(self, valid_work_index_data):
        """Test that assign_story succeeds when under concurrency limits."""
        # Set max_agents_total to 4, currently 0 in_progress
        valid_work_index_data['concurrency']['max_agents_total'] = 4
        
        # Assign first story - should succeed
        success, message = assign_story(valid_work_index_data, "E1-S1", "agent-1")
        assert success is True
        assert "Assigned" in message
        
        # Verify story was actually assigned
        story = get_story_by_id(valid_work_index_data, "E1-S1")
        assert story['status'] == "in_progress"
        assert story.get('assigned_to') == "agent-1"


class TestGetStoryById:
    """Tests for get_story_by_id function."""
    
    def test_get_existing_story(self, valid_work_index_data):
        """Test getting an existing story."""
        story = get_story_by_id(valid_work_index_data, "E1-S1")
        assert story is not None
        assert story['id'] == "E1-S1"
        assert story['title'] == "In-app event editor"
    
    def test_get_nonexistent_story(self, valid_work_index_data):
        """Test getting a story that doesn't exist."""
        story = get_story_by_id(valid_work_index_data, "E1-S99")
        assert story is None


class TestSyncGitTags:
    """Tests for sync_git_tags function."""
    
    @patch('work_index_validator.subprocess.run')
    def test_sync_tags_existing(self, mock_run, valid_work_index_data):
        """Test syncing when tags already exist."""
        # Mock git tag command returning existing tag
        mock_run.return_value = MagicMock(
            stdout="epic-active/EPIC-1\n",
            returncode=0
        )
        
        success, messages = sync_git_tags(valid_work_index_data, create_missing=False)
        assert success is True
    
    @patch('work_index_validator.subprocess.run')
    def test_sync_tags_missing(self, mock_run, valid_work_index_data):
        """Test syncing when tags are missing."""
        # Mock git tag command returning empty (tag missing)
        def mock_run_side_effect(cmd, **kwargs):
            if '--points-at' in cmd:
                return MagicMock(stdout="", returncode=0)
            return MagicMock(returncode=0)
        
        mock_run.side_effect = mock_run_side_effect
        
        success, messages = sync_git_tags(valid_work_index_data, create_missing=False)
        assert success is True
        assert len(messages) > 0
        assert any('not found' in msg for msg in messages)


class TestCheckStoryConflicts:
    """Tests for check_story_conflicts function."""
    
    def test_check_conflicts_no_changes(self, valid_work_index_data):
        """Test conflict check when work index not changed."""
        result = check_story_conflicts(valid_work_index_data, ["other_file.py"])
        assert result.is_valid is True
    
    def test_check_conflicts_with_changes(self, valid_work_index_data):
        """Test conflict check when work index is changed."""
        with patch('work_index_validator.get_git_diff', return_value=""):
            result = check_story_conflicts(
                valid_work_index_data,
                ["product-development/agentic_work_index.yaml"]
            )
            # Should validate the final state
            assert isinstance(result, ValidationResult)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
