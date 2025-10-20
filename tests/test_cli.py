"""Tests for CLI commands."""

from pathlib import Path

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
