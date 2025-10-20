"""CLI entry point for automated-changelog."""

from pathlib import Path

import click

from automated_changelog.config import generate_config_template, get_repo_name


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
    click.echo(f"Generating changelog using {config}...")
    if dry_run:
        click.echo("(Dry run mode)")
    # TODO: Implement generate logic
    click.echo("Not yet implemented")


if __name__ == "__main__":
    cli()
