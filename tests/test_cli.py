"""Tests for CLI commands."""

from click.testing import CliRunner

from automated_changelog.cli import cli


def test_cli_help():
    """Test that CLI help command works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Automated Changelog Generator" in result.output


def test_init_command():
    """Test init command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 0
    assert "Initializing configuration" in result.output


def test_generate_command():
    """Test generate command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["generate"])
    assert result.exit_code == 0
    assert "Generating changelog" in result.output


def test_generate_dry_run():
    """Test generate command with dry-run flag."""
    runner = CliRunner()
    result = runner.invoke(cli, ["generate", "--dry-run"])
    assert result.exit_code == 0
    assert "Dry run mode" in result.output
