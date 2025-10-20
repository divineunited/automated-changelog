"""Configuration template and utilities for automated-changelog."""

import subprocess
from pathlib import Path


def get_monorepo_modules(root_dir: Path) -> list[str]:
    """Detect top-level directories as potential modules in a monorepo.

    Args:
        root_dir: Root directory of the repository

    Returns:
        List of directory names that could be modules
    """
    modules = []

    # Common directories to exclude
    exclude_dirs = {"venv", "node_modules", "__pycache__", "dist", "build", "htmlcov"}

    for item in root_dir.iterdir():
        if (
            item.is_dir()
            and item.name not in exclude_dirs
            and not item.name.startswith(".")
        ):
            modules.append(item.name)

    return sorted(modules)


def generate_config_template(is_monorepo: bool, repo_name: str) -> str:
    """Generate a configuration template based on repo type.

    Args:
        is_monorepo: Whether this is a monorepo
        repo_name: Name of the repository or single module

    Returns:
        YAML configuration template as string
    """

    if is_monorepo:
        # Detect modules from current directory
        cwd = Path.cwd()
        detected_modules = get_monorepo_modules(cwd)

        if detected_modules:
            modules_yaml = "\n".join(f"  - {module}" for module in detected_modules)
        else:
            modules_yaml = "  - service-a\n  - service-b\n  - shared-library"
    else:
        modules_yaml = f"  - {repo_name}"

    template = f"""# Automated Changelog Configuration
# This file defines how the changelog generator analyzes your repository.

# Output file where the changelog will be written.
# The tool will prepend new entries to this file.
output_file: "CHANGELOG.md"

# List of modules/packages/services in your repository.
# For monorepos: Each top-level directory is typically a module.
# For single repos: Just list the repo name as a single module.
modules:
{modules_yaml}

# Filtering rules for commits.
# These help focus the changelog on significant changes by excluding noise.
filter:
  # Commits starting with these prefixes will be ignored for summarization.
  ignore_prefixes:
    - "chore:"
    - "docs:"
    - "test:"
    - "ci:"
    - "refactor:"
    - "style:"
    - "build:"

  # Commits containing these keywords in the subject will be ignored.
  ignore_keywords:
    - "typo"
    - "cleanup"
    - "formatting"
    - "[skip ci]"
    - "merge branch"
    - "merge pull request"

  # Commits ONLY touching files/paths matching these patterns will be ignored.
  # Use glob patterns. If a commit touches ANY file outside these patterns, it won't be filtered.
  ignore_paths_only:
    - "*.md"
    - "docs/"
    - "tests/"
    - ".github/"
    - "*.txt"

# LLM Configuration (optional customization)
# The tool uses these prompts to generate summaries.
llm:
  # Model to use for summarization (default: claude-sonnet-4-5)
  model: "claude-sonnet-4-5"

  # System prompt for module-level summaries
  module_summary_prompt: |
    You are a technical writer creating changelog entries.
    Summarize the significant changes for this module in 2-4 concise bullet points.
    Focus on features, fixes, and breaking changes. Ignore minor updates.
    Use clear, user-facing language.

  # System prompt for overall repository summary
  overall_summary_prompt: |
    You are a technical writer creating changelog entries.
    Provide a high-level summary (3-4 sentences) of the key activities across all modules.
    Highlight the most important changes or themes for this release period.
"""

    return template


def get_repo_name() -> str:
    """Get the repository name from git or current directory.

    Returns:
        Repository name as string
    """
    try:
        # Try to get from git remote
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        url = result.stdout.strip()
        # Extract repo name from URL
        # e.g., https://github.com/user/repo.git -> repo
        name = url.split("/")[-1].replace(".git", "")
        return name
    except Exception:
        # Fallback to current directory name
        return Path.cwd().name
