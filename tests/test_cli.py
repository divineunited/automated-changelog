"""Tests for CLI commands."""

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from automated_changelog.cli import cli


def test_cli_help():
    """Test that CLI help command works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Automated Changelog Generator" in result.output


def test_init_command_creates_config():
    """Test init command creates configuration file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Simulate user input: answer 'n' to monorepo question
        result = runner.invoke(cli, ["init"], input="n\n")

        assert result.exit_code == 0
        assert "Created configuration file" in result.output
        assert Path(".changelog_config.yaml").exists()

        # Check file content
        config_content = Path(".changelog_config.yaml").read_text()
        assert "output_file:" in config_content
        assert "modules:" in config_content
        assert "filter:" in config_content


def test_init_command_monorepo():
    """Test init command for monorepo."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create some directories to simulate monorepo
        Path("service-a").mkdir()
        Path("service-b").mkdir()

        # Simulate user input: answer 'y' to monorepo question
        result = runner.invoke(cli, ["init"], input="y\n")

        assert result.exit_code == 0
        config_content = Path(".changelog_config.yaml").read_text()

        # Should detect the directories we created
        assert "service-a" in config_content
        assert "service-b" in config_content


def test_init_command_overwrite_existing():
    """Test init command with existing config file - user confirms overwrite."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create existing config
        Path(".changelog_config.yaml").write_text("existing content")

        # Simulate user input: 'y' to overwrite, 'n' to monorepo question
        result = runner.invoke(cli, ["init"], input="y\nn\n")

        assert result.exit_code == 0
        assert "Created configuration file" in result.output

        # File should be overwritten
        config_content = Path(".changelog_config.yaml").read_text()
        assert "existing content" not in config_content
        assert "output_file:" in config_content


def test_init_command_cancel_overwrite():
    """Test init command with existing config file - user cancels."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create existing config
        Path(".changelog_config.yaml").write_text("existing content")

        # Simulate user input: 'n' to overwrite question
        result = runner.invoke(cli, ["init"], input="n\n")

        assert result.exit_code == 0
        assert "Initialization cancelled" in result.output

        # File should not be changed
        config_content = Path(".changelog_config.yaml").read_text()
        assert config_content == "existing content"


def test_init_command_custom_config_path():
    """Test init command with custom config path."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Use custom config path
        result = runner.invoke(
            cli, ["init", "--config", "custom_config.yaml"], input="n\n"
        )

        assert result.exit_code == 0
        assert Path("custom_config.yaml").exists()
        assert not Path(".changelog_config.yaml").exists()


def test_generate_command_missing_config():
    """Test generate command when config file doesn't exist."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["generate"])

        assert result.exit_code == 1
        assert "Configuration file not found" in result.output
        assert "automated-changelog init" in result.output


@patch("automated_changelog.cli.fetch_commits")
@patch("automated_changelog.cli.read_last_commit_hash")
@patch("automated_changelog.cli.write_changelog_entry")
def test_generate_command_with_valid_config(mock_write, mock_read, mock_fetch):
    """Test generate command with valid config file."""
    # Mock git operations
    mock_read.return_value = None
    mock_fetch.return_value = [
        {
            "hash": "abc123def456789012345678901234567890abcd",
            "short_hash": "abc123d",
            "author": "Test Author",
            "date": "2025-10-27 14:32",
            "subject": "Initial commit",
        }
    ]

    runner = CliRunner()
    with runner.isolated_filesystem():
        # First create a config file
        runner.invoke(cli, ["init"], input="n\n")

        # Then run generate
        result = runner.invoke(cli, ["generate"])

        assert result.exit_code == 0
        assert "Loaded configuration" in result.output
        assert "CHANGELOG.md" in result.output
        assert "Found 1 commits to process" in result.output

        # Verify write was called
        assert mock_write.called


@patch("automated_changelog.cli.fetch_commits")
@patch("automated_changelog.cli.read_last_commit_hash")
@patch("automated_changelog.cli.write_changelog_entry")
def test_generate_dry_run(mock_write, mock_read, mock_fetch):
    """Test generate command with dry-run flag."""
    # Mock git operations
    mock_read.return_value = "abc123"
    mock_fetch.return_value = [
        {
            "hash": "def456789012345678901234567890abcdef456",
            "short_hash": "def4567",
            "author": "Test Author",
            "date": "2025-10-26 10:15",
            "subject": "New feature",
        }
    ]

    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create config first
        runner.invoke(cli, ["init"], input="n\n")

        # Run with dry-run
        result = runner.invoke(cli, ["generate", "--dry-run"])

        assert result.exit_code == 0
        assert "Dry run mode" in result.output

        # Verify write was NOT called in dry-run mode
        assert not mock_write.called


@patch("automated_changelog.cli.fetch_commits")
@patch("automated_changelog.cli.read_last_commit_hash")
@patch("automated_changelog.cli.write_changelog_entry")
def test_generate_custom_config_path(mock_write, mock_read, mock_fetch):
    """Test generate command with custom config path."""
    # Mock git operations
    mock_read.return_value = None
    mock_fetch.return_value = [
        {
            "hash": "abc123def456789012345678901234567890abcd",
            "short_hash": "abc123d",
            "author": "Test Author",
            "date": "2025-10-27 11:20",
            "subject": "Test commit",
        }
    ]

    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create config at custom path
        runner.invoke(cli, ["init", "--config", "my_config.yaml"], input="n\n")

        # Generate using custom path
        result = runner.invoke(cli, ["generate", "--config", "my_config.yaml"])

        assert result.exit_code == 0
        assert "Loaded configuration from my_config.yaml" in result.output
