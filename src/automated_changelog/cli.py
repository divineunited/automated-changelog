"""CLI entry point for automated-changelog."""

from pathlib import Path

import click

from automated_changelog.config import (
    ConfigError,
    generate_config_template,
    get_repo_name,
    load_config,
)


@click.group()
@click.version_option()
def cli():
    """Automated Changelog Generator for Git Monorepos."""
    pass


@cli.command()
@click.option(
    "--config",
    "-c",
    default=".changelog_config.yaml",
    help="Path to configuration file",
)
def init(config):
    """Initialize changelog configuration file."""
    config_path = Path(config)

    # Check if config already exists
    if config_path.exists():
        if not click.confirm(
            f"Configuration file '{config}' already exists. Overwrite?", default=False
        ):
            click.echo("Initialization cancelled.")
            return

    # Ask if this is a monorepo
    is_monorepo = click.confirm(
        "Is this a monorepo with multiple services/modules?", default=False
    )

    # Get repo name for single repo case
    repo_name = get_repo_name()

    # Generate template
    template = generate_config_template(is_monorepo, repo_name)

    # Write config file
    try:
        config_path.write_text(template)
        click.echo(f"✓ Created configuration file: {config}")
        click.echo("\nNext steps:")
        click.echo(f"  1. Review and customize {config}")
        click.echo("  2. Run 'automated-changelog generate' to create your changelog")
    except Exception as e:
        click.echo(f"✗ Error writing configuration file: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option(
    "--config",
    "-c",
    default=".changelog_config.yaml",
    help="Path to configuration file",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be generated without writing to file",
)
def generate(config, dry_run):
    """Generate changelog from git history."""
    # Load configuration
    try:
        cfg = load_config(config)
        click.echo(f"✓ Loaded configuration from {config}")

        # Display config summary
        click.echo(f"  Output file: {cfg['output_file']}")
        click.echo(f"  Modules: {', '.join(cfg['modules'])}")

        if dry_run:
            click.echo("\n(Dry run mode - no files will be written)")

        # TODO: Implement changelog generation logic
        click.echo("\nChangelog generation not yet implemented")

    except ConfigError as e:
        click.echo(f"✗ {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()
