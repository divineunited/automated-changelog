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


def generate_module_summary(
    module_name: str,
    commits: list[dict[str, str]],
    prompt_template: str,
    model: str = "claude-sonnet-4-5",
) -> str:
    """
    Generate LLM summary for a module's commits.

    Args:
        module_name: Name of the module
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

Module: {module_name}

Commits:
{commits_text}

Provide a concise summary in 2-4 bullet points."""

    # Call LLM
    summary = call_llm(prompt=prompt, model=model)
    return summary.strip()


def generate_overall_summary(
    module_summaries: dict[str, str],
    prompt_template: str,
    model: str = "claude-sonnet-4-5",
) -> str:
    """
    Generate overall summary for monorepo from module summaries.

    Args:
        module_summaries: Dict mapping module names to their summaries
        prompt_template: System prompt template from config
        model: LLM model to use

    Returns:
        Generated overall summary text
    """
    if not module_summaries:
        return "No significant changes across modules."

    # Build module summaries text
    summary_lines = []
    for module_name, summary in module_summaries.items():
        summary_lines.append(f"**{module_name}**:\n{summary}")

    summaries_text = "\n\n".join(summary_lines)

    # Build the prompt
    prompt = f"""{prompt_template}

Module Summaries:
{summaries_text}

Provide a high-level summary (3-4 sentences) of the key activities across all modules."""

    # Call LLM
    summary = call_llm(prompt=prompt, model=model)
    return summary.strip()
