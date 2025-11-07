# automated-changelog

LLM-powered automated changelog generation for Git repositories.

## Overview

`automated-changelog` is a Python CLI tool that automatically generates human-readable changelogs by analyzing your Git history and using LLMs to create concise, meaningful summaries. It filters out noise to focus on significant changes.

## Installation

```bash
pip install automated-changelog
```

## Quick Start

1. **Set up LLM credentials** (create `.env` file in your repo):
   ```bash
   LITELLM_PROXY_API_BASE=https://your-litellm-proxy.example.com
   LITELLM_PROXY_API_KEY=sk-your-key-here
   ```

2. **Initialize configuration** (in your Git repo):
   ```bash
   automated-changelog init
   ```
   This creates `.changelog_config.yaml` with default settings.

3. **Generate your changelog**:
   ```bash
   # Preview without writing
   automated-changelog generate --dry-run

   # Generate and write to CHANGELOG.md
   automated-changelog generate

   # Skip LLM summarization (just list commits)
   automated-changelog generate --skip-llm
   ```

## CLI Commands

### `automated-changelog init [--config PATH]`

Creates a `.changelog_config.yaml` configuration file in your repository with sensible defaults for commit filtering and LLM summarization.

**Example:**
```bash
cd /path/to/your/repo
automated-changelog init
```

### `automated-changelog generate [OPTIONS]`

Generates changelog entries from Git history since the last run.

**Options:**

* `--dry-run` - Preview the changelog without writing to file
* `--skip-llm` - Skip LLM summarization and only list commits
* `--config PATH` - Use custom config file (default: `.changelog_config.yaml`)
* `--from-date DATE` - Start date for commits (YYYY-MM-DD) for historical generation
* `--to-date DATE` - End date for commits (YYYY-MM-DD) for historical generation

**Examples:**
```bash
# Preview before generating
automated-changelog generate --dry-run

# Generate with LLM summaries
automated-changelog generate

# Just list commits without LLM
automated-changelog generate --skip-llm

# Generate historical changelog for specific date range
automated-changelog generate --from-date 2024-01-01 --to-date 2024-01-07

# Generate changelog for all commits since a date
automated-changelog generate --from-date 2024-01-01

# Generate changelog for all commits until a date
automated-changelog generate --to-date 2024-12-31
```

### Environment Variables

* `LITELLM_PROXY_API_BASE` - Your LiteLLM proxy URL
* `LITELLM_PROXY_API_KEY` - Your LiteLLM API key

## Core Functionality

1.  **Commit Analysis:** Processes `git log` history, focusing on commits since the last time the tool was run (tracked via metadata within the `CHANGELOG.md`).
2.  **Intelligent Filtering:** Filters out minor commits (e.g., chores, docs, tests, typos) based on customizable rules (commit message prefixes, keywords, file paths) defined in the configuration.
3.  **LLM-Powered Summarization:** Generates concise, bulleted summaries of significant changes by analyzing commit messages.
4.  **Markdown Output:** Formats the summaries and commit lists into a well-structured Markdown section.
5.  **Incremental Updates:** Reads the existing changelog file (e.g., `CHANGELOG.md`) and automatically **prepends** the newly generated section, maintaining a running history.
6.  **Historical Generation:** Generate changelogs for specific date ranges using `--from-date` and `--to-date` flags. Perfect for backfilling weekly or monthly changelog entries for repositories with extensive history.

**How it Works:**

* **Configuration:** Uses a `.changelog_config.yaml` file (checked into your repo) to define filtering rules, the output changelog file path, and optionally customize LLM prompts. An `init` command helps generate this file.
* **Execution:** Run the `generate` command from within your repository. It uses the Git CLI and interacts with a configured LLM to produce the summaries.
* **State Management:** Stores the hash of the last processed commit **within a comment or metadata block inside the `CHANGELOG.md` file**. This ensures the tool only includes new changes in subsequent runs without requiring a separate state file.

## What Gets Summarized

**Important:** The tool analyzes **commit messages only**, not code diffs or file changes.

For each commit since the last run, the tool extracts:
- Commit hash (full and short)
- Author name
- Commit date
- Commit subject (the first line of the commit message)

### LLM Context

The LLM receives **filtered commit messages** in this format:
```
- abc1234 Add user authentication (John Doe, 2025-11-05 14:30)
- def5678 Fix login redirect bug (Jane Smith, 2025-11-04 10:15)
- ghi9012 Update password validation (John Doe, 2025-11-03 09:45)
```

The LLM does **not** see:
- Actual code changes or diffs
- File paths or file lists
- Commit bodies (only the subject line)

This design keeps API costs low and focuses on what developers already wrote in their commit messages.

## How LLM Summarization Works

1. **Filter commits** based on rules in `.changelog_config.yaml`:
   - Ignore commits with certain prefixes (`chore:`, `docs:`, `test:`, etc.)
   - Ignore commits with certain keywords (`typo`, `cleanup`, etc.)

2. **Send filtered commits to LLM** with:
   - List of commit messages (hash, subject, author, date)
   - Custom prompt from config (e.g., "Summarize in 2-4 bullet points")

3. **LLM generates** a concise summary focusing on features, fixes, and breaking changes

### Output Format

The final changelog entry includes:
- **Summary** - LLM-generated bullet points highlighting significant changes
- **All commits** (collapsible) - Full commit list for reference

**Example:**
```markdown
## [2025-11-05]

### Summary

- Added OAuth2 authentication support with Google and GitHub providers
- Implemented password reset functionality via email
- Fixed session timeout bug causing unexpected logouts

### Changes (5 commits)

<details>
<summary>All commits</summary>

- abc1234 Add OAuth2 authentication (John Doe, 2025-11-05 14:30)
- def5678 Implement password reset (Jane Smith, 2025-11-04 10:15)
- ghi9012 Fix session timeout bug (John Doe, 2025-11-03 09:45)
...
</details>
```

**Goal:**

To save developer time and improve project visibility by automating the creation of consistent, informative, and easy-to-read changelogs.
