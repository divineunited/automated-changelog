"""Tests for config module."""

from pathlib import Path
from unittest.mock import patch

from automated_changelog.config import (
    generate_config_template,
    get_monorepo_modules,
    get_repo_name,
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
