"""Tests for config module."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from automated_changelog.config import (
    ConfigError,
    generate_config_template,
    get_repo_name,
    load_config,
)


class TestGenerateConfigTemplate:
    """Tests for generate_config_template function."""

    def test_generate_config_template_single_repo(self):
        """Test config template generation for single repo."""
        template = generate_config_template(repo_name="my-app")

        assert 'output_file: "CHANGELOG.md"' in template
        assert "filter:" in template
        assert "ignore_prefixes:" in template
        assert "chore:" in template
        assert "docs:" in template
        assert "ignore_keywords:" in template
        assert "typo" in template
        assert "ignore_paths_only:" in template
        assert "*.md" in template
        assert "llm:" in template
        assert "model:" in template

    def test_generate_config_template_contains_all_required_fields(self):
        """Test that template contains all required configuration fields."""
        template = generate_config_template(repo_name="test")

        required_fields = [
            "output_file:",
            "filter:",
            "ignore_prefixes:",
            "ignore_keywords:",
            "ignore_paths_only:",
            "llm:",
            "model:",
            "summary_prompt:",
        ]

        for field in required_fields:
            assert field in template, f"Missing required field: {field}"


class TestGetRepoName:
    """Tests for get_repo_name function."""

    @patch("automated_changelog.config.subprocess.run")
    def test_get_repo_name_from_git_remote(self, mock_run):
        """Test extracting repo name from git remote URL."""
        mock_run.return_value.stdout = "https://github.com/user/my-awesome-repo.git\n"
        mock_run.return_value.returncode = 0

        name = get_repo_name()

        assert name == "my-awesome-repo"

    @patch("automated_changelog.config.subprocess.run")
    def test_get_repo_name_from_git_remote_ssh(self, mock_run):
        """Test extracting repo name from SSH git remote URL."""
        mock_run.return_value.stdout = "git@github.com:user/another-repo.git\n"
        mock_run.return_value.returncode = 0

        name = get_repo_name()

        assert name == "another-repo"

    @patch("automated_changelog.config.subprocess.run")
    def test_get_repo_name_fallback_to_directory(self, mock_run):
        """Test fallback to directory name when git command fails."""
        mock_run.side_effect = Exception("git not found")

        name = get_repo_name()

        # Should return current directory name
        assert name == Path.cwd().name


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_success(self, tmp_path):
        """Test successfully loading a valid config file."""
        config_file = tmp_path / "test_config.yaml"
        config_content = {
            "output_file": "CHANGELOG.md",
            "filter": {
                "ignore_prefixes": ["chore:", "docs:"],
                "ignore_keywords": ["typo"],
                "ignore_paths_only": ["*.md"],
            },
        }
        config_file.write_text(yaml.dump(config_content))

        config = load_config(config_file)

        assert config["output_file"] == "CHANGELOG.md"
        assert "filter" in config
        assert config["filter"]["ignore_prefixes"] == ["chore:", "docs:"]

    def test_load_config_file_not_found(self, tmp_path):
        """Test error when config file doesn't exist."""
        config_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(ConfigError) as exc_info:
            load_config(config_file)

        assert "Configuration file not found" in str(exc_info.value)
        assert "automated-changelog init" in str(exc_info.value)

    def test_load_config_invalid_yaml(self, tmp_path):
        """Test error when config file contains invalid YAML."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content: [\n  unclosed")

        with pytest.raises(ConfigError) as exc_info:
            load_config(config_file)

        assert "Invalid YAML" in str(exc_info.value)

    def test_load_config_empty_file(self, tmp_path):
        """Test error when config file is empty."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        with pytest.raises(ConfigError) as exc_info:
            load_config(config_file)

        assert "Configuration file is empty" in str(exc_info.value)

    def test_load_config_missing_required_fields(self, tmp_path):
        """Test error when config is missing required fields."""
        config_file = tmp_path / "incomplete.yaml"
        config_content = {"output_file": "CHANGELOG.md"}  # Missing filter
        config_file.write_text(yaml.dump(config_content))

        with pytest.raises(ConfigError) as exc_info:
            load_config(config_file)

        assert "Missing required configuration fields" in str(exc_info.value)
        assert "filter" in str(exc_info.value)

    def test_load_config_with_llm_section(self, tmp_path):
        """Test loading config with optional LLM section."""
        config_file = tmp_path / "config_with_llm.yaml"
        config_content = {
            "output_file": "CHANGELOG.md",
            "filter": {"ignore_prefixes": ["chore:"]},
            "llm": {"model": "gpt-4o-mini", "summary_prompt": "Test prompt"},
        }
        config_file.write_text(yaml.dump(config_content))

        config = load_config(config_file)

        assert "llm" in config
        assert config["llm"]["model"] == "gpt-4o-mini"
