"""Commit filtering and summarization logic."""

from typing import Any

from automated_changelog.llm import call_llm


def filter_commits(
    commits: list[dict[str, str]],
    filter_config: dict[str, Any],
) -> list[dict[str, str]]:
    """
    Filter commits based on configuration rules.

    Args:
        commits: List of commit dictionaries
        filter_config: Filter configuration from changelog_config.yaml

    Returns:
        Filtered list of commits
    """
    if not filter_config:
        return commits

    filtered = []
    ignore_prefixes = filter_config.get("ignore_prefixes", [])
    ignore_keywords = filter_config.get("ignore_keywords", [])

    for commit in commits:
        subject = commit["subject"]

        # Check ignore_prefixes
        if any(subject.startswith(prefix) for prefix in ignore_prefixes):
            continue

        # Check ignore_keywords (case-insensitive)
        subject_lower = subject.lower()
        if any(keyword.lower() in subject_lower for keyword in ignore_keywords):
            continue

        # Passed all filters
        filtered.append(commit)

    return filtered


def generate_summary(
    commits: list[dict[str, str]],
    prompt_template: str,
    model: str = "claude-sonnet-4-5",
) -> str:
    """
    Generate LLM summary for commits.

    Args:
        commits: List of filtered commit dictionaries
        prompt_template: System prompt template from config
        model: LLM model to use

    Returns:
        Generated summary text
    """
    if not commits:
        return "No significant changes."

    # Build commit list for the prompt
    commit_lines = []
    for commit in commits:
        commit_lines.append(
            f"- {commit['short_hash']} {commit['subject']} "
            f"({commit['author']}, {commit['date']})"
        )

    commits_text = "\n".join(commit_lines)

    # Build the prompt
    prompt = f"""{prompt_template}

Commits:
{commits_text}

Provide a concise summary in 2-4 bullet points."""

    # Call LLM
    summary = call_llm(prompt=prompt, model=model)
    return summary.strip()
