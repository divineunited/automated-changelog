"""Tests for config module."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from automated_changelog.config import (
    ConfigError,
    generate_config_template,
    get_monorepo_modules,
    get_repo_name,
    load_config,
)


class TestGetMonorepoModules:
    """Tests for get_monorepo_modules function."""

    def test_get_monorepo_modules_excludes_common_dirs(self, tmp_path):
        """Test that common directories are excluded from modules."""
        # Create some directories
        (tmp_path / "service-a").mkdir()
        (tmp_path / "service-b").mkdir()
        (tmp_path / ".git").mkdir()
        (tmp_path / ".venv").mkdir()
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "__pycache__").mkdir()

        modules = get_monorepo_modules(tmp_path)

        assert "service-a" in modules
        assert "service-b" in modules
        assert ".git" not in modules
        assert ".venv" not in modules
        assert "node_modules" not in modules
        assert "__pycache__" not in modules

    def test_get_monorepo_modules_sorted(self, tmp_path):
        """Test that modules are returned in sorted order."""
        (tmp_path / "zebra").mkdir()
        (tmp_path / "alpha").mkdir()
        (tmp_path / "beta").mkdir()

        modules = get_monorepo_modules(tmp_path)

        assert modules == ["alpha", "beta", "zebra"]

    def test_get_monorepo_modules_ignores_files(self, tmp_path):
        """Test that files are ignored, only directories are returned."""
        (tmp_path / "service-a").mkdir()
        (tmp_path / "README.md").touch()
        (tmp_path / "setup.py").touch()

        modules = get_monorepo_modules(tmp_path)

        assert modules == ["service-a"]

    def test_get_monorepo_modules_empty_directory(self, tmp_path):
        """Test that empty directory returns empty list."""
        modules = get_monorepo_modules(tmp_path)
        assert modules == []


class TestGenerateConfigTemplate:
    """Tests for generate_config_template function."""

    def test_generate_config_template_single_repo(self):
        """Test config template generation for single repo."""
        template = generate_config_template(is_monorepo=False, repo_name="my-app")

        assert 'output_file: "CHANGELOG.md"' in template
        assert "modules:" in template
        assert "  - my-app" in template
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

    @patch("automated_changelog.config.get_monorepo_modules")
    def test_generate_config_template_monorepo_with_detected_modules(
        self, mock_get_modules
    ):
        """Test config template generation for monorepo with detected modules."""
        mock_get_modules.return_value = ["api", "frontend", "shared"]

        template = generate_config_template(is_monorepo=True, repo_name="my-repo")

        assert "  - api" in template
        assert "  - frontend" in template
        assert "  - shared" in template

    @patch("automated_changelog.config.get_monorepo_modules")
    def test_generate_config_template_monorepo_no_detected_modules(
        self, mock_get_modules
    ):
        """Test config template generation for monorepo with no detected modules."""
        mock_get_modules.return_value = []

        template = generate_config_template(is_monorepo=True, repo_name="my-repo")

        # Should fall back to example modules
        assert "service-a" in template
        assert "service-b" in template
        assert "shared-library" in template

    def test_generate_config_template_contains_all_required_fields(self):
        """Test that template contains all required configuration fields."""
        template = generate_config_template(is_monorepo=False, repo_name="test")

        required_fields = [
            "output_file:",
            "modules:",
            "filter:",
            "ignore_prefixes:",
            "ignore_keywords:",
            "ignore_paths_only:",
            "llm:",
            "model:",
            "module_summary_prompt:",
            "overall_summary_prompt:",
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
            "modules": ["api", "frontend"],
            "filter": {
                "ignore_prefixes": ["chore:", "docs:"],
                "ignore_keywords": ["typo"],
                "ignore_paths_only": ["*.md"],
            },
        }
        config_file.write_text(yaml.dump(config_content))

        config = load_config(config_file)

        assert config["output_file"] == "CHANGELOG.md"
        assert config["modules"] == ["api", "frontend"]
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
        config_content = {"output_file": "CHANGELOG.md"}  # Missing modules and filter
        config_file.write_text(yaml.dump(config_content))

        with pytest.raises(ConfigError) as exc_info:
            load_config(config_file)

        assert "Missing required configuration fields" in str(exc_info.value)
        assert "modules" in str(exc_info.value)
        assert "filter" in str(exc_info.value)

    def test_load_config_with_llm_section(self, tmp_path):
        """Test loading config with optional LLM section."""
        config_file = tmp_path / "config_with_llm.yaml"
        config_content = {
            "output_file": "CHANGELOG.md",
            "modules": ["service"],
            "filter": {"ignore_prefixes": ["chore:"]},
            "llm": {"model": "gpt-4o-mini", "module_summary_prompt": "Test prompt"},
        }
        config_file.write_text(yaml.dump(config_content))

        config = load_config(config_file)

        assert "llm" in config
        assert config["llm"]["model"] == "gpt-4o-mini"
