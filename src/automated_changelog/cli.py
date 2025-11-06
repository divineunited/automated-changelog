"""CLI entry point for automated-changelog."""

import subprocess
from datetime import datetime
from pathlib import Path

import click

from automated_changelog.config import (
    ConfigError,
    generate_config_template,
    get_repo_name,
    load_config,
)
from automated_changelog.git_state import (
    fetch_commits,
    read_last_commit_hash,
    write_changelog_entry,
)
from automated_changelog.summarization import filter_commits


@click.group()
@click.version_option()
def cli():
    """Automated Changelog Generator for Git repositories."""
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

    # Get repo name
    repo_name = get_repo_name()

    # Generate template
    template = generate_config_template(repo_name)

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
@click.option(
    "--skip-llm",
    is_flag=True,
    help="Skip LLM summarization and only list commits",
)
@click.option(
    "--from-date",
    help="Start date for commits (YYYY-MM-DD) for historical generation.",
)
@click.option(
    "--to-date",
    help="End date for commits (YYYY-MM-DD) for historical generation.",
)
def generate(config, dry_run, skip_llm, from_date, to_date):
    """Generate changelog from git history."""
    # Load configuration
    try:
        cfg = load_config(config)
        click.echo(f"✓ Loaded configuration from {config}")

        # Display config summary
        click.echo(f"  Output file: {cfg['output_file']}")

        if dry_run:
            click.echo("\n(Dry run mode - no files will be written)")

        # Determine mode: date range or incremental
        using_date_range = from_date or to_date
        output_file = cfg["output_file"]
        last_hash = None

        if using_date_range:
            # Date range mode - for historical generation
            click.echo("\n✓ Using date range mode")
            if from_date:
                click.echo(f"  From: {from_date}")
            if to_date:
                click.echo(f"  To: {to_date}")
        else:
            # Incremental mode - read last commit hash from changelog
            last_hash = read_last_commit_hash(output_file)

            if last_hash:
                click.echo(f"\n✓ Found last processed commit: {last_hash[:8]}")
            else:
                click.echo("\n! No previous state found, fetching all commits")

        # Fetch commits
        try:
            commits = fetch_commits(
                last_commit_hash=last_hash,
                since_date=from_date,
                until_date=to_date,
            )
            click.echo(f"✓ Found {len(commits)} commits to process")

            if not commits:
                click.echo("\n! No new commits to process")
                return

            # Display some commits for verification
            click.echo("\nRecent commits:")
            for commit in commits[:5]:
                click.echo(f"  {commit['short_hash']} - {commit['subject']}")
            if len(commits) > 5:
                click.echo(f"  ... and {len(commits) - 5} more")

            # Get the latest commit hash
            latest_hash = commits[0]["hash"]

            # Filter commits based on config
            filter_config = cfg.get("filter", {})
            filtered_commits = filter_commits(commits, filter_config)

            click.echo(
                f"  After filtering: {len(filtered_commits)} commits "
                f"(excluded {len(commits) - len(filtered_commits)})"
            )

            # Get LLM configuration
            llm_config = cfg.get("llm", {})
            model = llm_config.get("model", "claude-sonnet-4-5")
            summary_prompt = llm_config.get(
                "summary_prompt",
                "Summarize the commits in 2-4 bullet points.",
            )

            # Generate summary
            changelog_summary = None
            use_llm = not skip_llm

            if use_llm:
                try:
                    # Check for LLM credentials
                    from automated_changelog.llm import get_llm_client

                    try:
                        get_llm_client()
                    except ValueError as e:
                        click.echo(f"\n⚠ {e}", err=True)
                        click.echo(
                            "  Run with --skip-llm to generate without summarization.\n"
                        )
                        use_llm = False

                    if use_llm:
                        click.echo("\n✓ Generating LLM summary...")
                        from automated_changelog.summarization import generate_summary

                        changelog_summary = generate_summary(
                            commits=filtered_commits,
                            prompt_template=summary_prompt,
                            model=model,
                        )
                except Exception as e:
                    click.echo(f"\n⚠ LLM summarization failed: {e}", err=True)
                    click.echo("  Falling back to commit list only...\n")
                    use_llm = False
                    changelog_summary = None

            # Build changelog entry
            # Use date range for header if specified, otherwise use current date
            if using_date_range:
                if from_date and to_date:
                    timestamp = f"{from_date} to {to_date}"
                elif from_date:
                    timestamp = f"Since {from_date}"
                elif to_date:
                    timestamp = f"Until {to_date}"
            else:
                timestamp = datetime.now().strftime("%Y-%m-%d")

            summary = f"## [{timestamp}]\n"
            # Only add state marker in incremental mode (not for historical date ranges)
            if not using_date_range:
                summary += f"<!-- LATEST_COMMIT: {latest_hash} -->\n\n"
            else:
                summary += "\n"

            # Add LLM summary if available
            if use_llm and changelog_summary:
                summary += "### Summary\n\n"
                summary += f"{changelog_summary}\n\n"

            # Add commits section
            summary += f"### Changes ({len(commits)} commits)\n\n"

            # List all commits (not just filtered)
            if use_llm:
                summary += "<details>\n<summary>All commits</summary>\n\n"
            for commit in commits:
                summary += (
                    f"- `{commit['short_hash']}` {commit['subject']} "
                    f"({commit['author']}, {commit['date']})\n"
                )
            if use_llm:
                summary += "\n</details>\n\n"
            else:
                summary += "\n"

            # Write to changelog
            if not dry_run:
                # Pass None for latest_hash in date range mode to skip state update
                hash_to_write = None if using_date_range else latest_hash
                write_changelog_entry(output_file, hash_to_write, summary)
                click.echo(f"\n✓ Changelog updated: {output_file}")
                if not using_date_range:
                    click.echo(f"  Latest commit: {latest_hash[:8]}")
            else:
                click.echo("\n--- Generated Summary (Dry Run) ---")
                click.echo(summary)
                if not using_date_range:
                    click.echo(f"\nWould update state to: {latest_hash[:8]}")

        except subprocess.CalledProcessError as e:
            click.echo(f"✗ Git command failed: {e}", err=True)
            raise click.Abort()
        except FileNotFoundError:
            click.echo("✗ Git not found. Please ensure git is installed.", err=True)
            raise click.Abort()

    except ConfigError as e:
        click.echo(f"✗ {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()
