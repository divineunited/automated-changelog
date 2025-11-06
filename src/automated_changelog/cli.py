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
from automated_changelog.summarization import (
    filter_commits,
    generate_module_summary,
    generate_overall_summary,
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
@click.option(
    "--skip-llm",
    is_flag=True,
    help="Skip LLM summarization and only list commits",
)
def generate(config, dry_run, skip_llm):
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

        # Read last commit hash from changelog
        output_file = cfg["output_file"]
        last_hash = read_last_commit_hash(output_file)

        if last_hash:
            click.echo(f"\n✓ Found last processed commit: {last_hash[:8]}")
        else:
            click.echo("\n! No previous state found, fetching all commits")

        # Fetch commits
        try:
            commits = fetch_commits(last_commit_hash=last_hash)
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
            module_prompt = llm_config.get(
                "module_summary_prompt",
                "Summarize the commits in 2-4 bullet points.",
            )
            overall_prompt = llm_config.get(
                "overall_summary_prompt",
                "Provide a high-level summary across all modules.",
            )

            # Generate summaries per module
            is_monorepo = len(cfg["modules"]) > 1
            module_summaries = {}
            overall_summary = None
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
                        click.echo("\n✓ Generating LLM summaries...")
                        for module in cfg["modules"]:
                            click.echo(f"  Summarizing {module}...")
                            module_summary = generate_module_summary(
                                module_name=module,
                                commits=filtered_commits,
                                prompt_template=module_prompt,
                                model=model,
                            )
                            module_summaries[module] = module_summary

                        # Generate overall summary if monorepo
                        if is_monorepo:
                            click.echo("  Generating overall summary...")
                            overall_summary = generate_overall_summary(
                                module_summaries=module_summaries,
                                prompt_template=overall_prompt,
                                model=model,
                            )
                except Exception as e:
                    click.echo(f"\n⚠ LLM summarization failed: {e}", err=True)
                    click.echo("  Falling back to commit list only...\n")
                    use_llm = False
                    module_summaries = {}
                    overall_summary = None

            # Build changelog entry
            timestamp = datetime.now().strftime("%Y-%m-%d")
            summary = f"## [{timestamp}]\n"
            summary += f"<!-- LATEST_COMMIT: {latest_hash} -->\n\n"

            # Add overall summary if monorepo and LLM was used
            if use_llm and overall_summary:
                summary += f"### Summary\n\n"
                summary += f"{overall_summary}\n\n"

            # Add module summaries
            summary += f"### Changes by Module\n\n"
            for module in cfg["modules"]:
                summary += f"**{module}** ({len(commits)} commits)\n\n"

                # Add LLM summary if available
                if use_llm and module in module_summaries:
                    summary += f"{module_summaries[module]}\n\n"

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
                write_changelog_entry(output_file, latest_hash, summary)
                click.echo(f"\n✓ Changelog updated: {output_file}")
                click.echo(f"  Latest commit: {latest_hash[:8]}")
            else:
                click.echo("\n--- Generated Summary (Dry Run) ---")
                click.echo(summary)
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
