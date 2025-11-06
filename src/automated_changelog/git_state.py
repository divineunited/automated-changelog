"""Git operations and state management for automated-changelog."""

import re
import subprocess
from pathlib import Path
from typing import Optional

STATE_MARKER_START = "<!-- CHANGELOG_STATE:"
STATE_MARKER_END = "-->"


def read_last_commit_hash(changelog_path: str | Path) -> Optional[str]:
    """
    Read the last processed commit hash from the CHANGELOG.md file.

    The hash is stored in a HTML comment at the top of the file:
    <!-- CHANGELOG_STATE: <commit_hash> -->

    Args:
        changelog_path: Path to the changelog file

    Returns:
        The last processed commit hash, or None if not found
    """
    changelog_file = Path(changelog_path)

    if not changelog_file.exists():
        return None

    try:
        content = changelog_file.read_text(encoding="utf-8")

        # Look for the state marker in the first few lines
        start = re.escape(STATE_MARKER_START)
        end = re.escape(STATE_MARKER_END)
        pattern = rf"{start}\s*([a-f0-9]{{40}})\s*{end}"
        match = re.search(pattern, content)

        if match:
            return match.group(1)

        return None

    except Exception:
        return None


def write_changelog_entry(
    changelog_path: str | Path,
    latest_commit_hash: Optional[str],
    summary: str,
) -> None:
    """
    Write a new changelog entry and optionally update the state marker.

    This function prepends the new summary to the changelog file and
    updates the state marker with the latest commit hash (if provided).

    Args:
        changelog_path: Path to the changelog file
        latest_commit_hash: Hash of the latest processed commit. If None,
            no state marker will be written (useful for historical generation).
        summary: The changelog summary to prepend
    """
    changelog_file = Path(changelog_path)

    # Read existing content if file exists
    existing_content = ""
    if changelog_file.exists():
        existing_content = changelog_file.read_text(encoding="utf-8")

        # Remove old state marker if it exists (only when updating state)
        if latest_commit_hash:
            marker_start = re.escape(STATE_MARKER_START)
            marker_end = re.escape(STATE_MARKER_END)
            pattern = rf"{marker_start}.*?{marker_end}\n?"
            existing_content = re.sub(pattern, "", existing_content, count=1)

    # Create new content with optional state marker and summary
    if latest_commit_hash:
        state_marker = f"{STATE_MARKER_START} {latest_commit_hash} {STATE_MARKER_END}\n"
        new_content = state_marker + "\n" + summary + "\n\n" + existing_content
    else:
        new_content = summary + "\n\n" + existing_content

    # Write to file
    changelog_file.write_text(new_content, encoding="utf-8")


def fetch_commits(
    last_commit_hash: Optional[str] = None,
    repo_path: str | Path = ".",
    since_date: Optional[str] = None,
    until_date: Optional[str] = None,
) -> list[dict[str, str]]:
    """
    Fetch commits from git log.

    Args:
        last_commit_hash: The last processed commit hash. If provided,
            fetches commits from this hash to HEAD. Ignored if date range is specified.
        repo_path: Path to the git repository (default: current directory)
        since_date: Start date for commits (format: YYYY-MM-DD). If provided,
            date range takes precedence over commit hash range.
        until_date: End date for commits (format: YYYY-MM-DD). If provided,
            date range takes precedence over commit hash range.

    Returns:
        List of commit dictionaries with keys:
        - hash: full commit hash
        - short_hash: abbreviated commit hash
        - author: author name
        - date: author date (ISO 8601-like format: YYYY-MM-DD HH:MM:SS)
        - subject: commit subject/message

    Raises:
        subprocess.CalledProcessError: If git command fails
        FileNotFoundError: If git is not found
    """
    repo = Path(repo_path)

    # Build git log command
    cmd = ["git", "-C", str(repo), "log"]

    # Determine commit range - date range takes precedence
    if since_date or until_date:
        # Use date-based filtering
        if since_date:
            cmd.append(f"--since={since_date}")
        if until_date:
            cmd.append(f"--until={until_date}")
    elif last_commit_hash:
        # Use commit hash range (original behavior)
        cmd.append(f"{last_commit_hash}..HEAD")

    # Format: hash ||| short_hash ||| author ||| date ||| subject
    cmd.extend(["--pretty=format:%H|||%h|||%an|||%ai|||%s"])

    # Execute git log
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
    )

    # Parse output
    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue

        parts = line.split("|||", 4)
        if len(parts) == 5:
            # Trim date to just YYYY-MM-DD HH:MM (remove seconds and timezone)
            date_str = parts[3].strip()
            if len(date_str) >= 16:
                date_str = date_str[:16]  # "2025-10-27 14:32"

            commit = {
                "hash": parts[0].strip(),
                "short_hash": parts[1].strip(),
                "author": parts[2].strip(),
                "date": date_str,
                "subject": parts[4].strip(),
            }
            commits.append(commit)

    return commits
