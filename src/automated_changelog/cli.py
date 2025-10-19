"""CLI entry point for automated-changelog."""

import click


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
    click.echo(f"Initializing configuration at {config}...")
    # TODO: Implement init logic
    click.echo("Not yet implemented")


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
