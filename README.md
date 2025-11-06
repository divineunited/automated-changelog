# automated-changelog

LLM-powered automated changelog generation for Git repositories and monorepos.

## Overview

`automated-changelog` is a Python CLI tool that automatically generates human-readable changelogs by analyzing your Git history and using LLMs to create concise, meaningful summaries. It works with both single repositories and monorepos, filtering out noise to focus on significant changes.

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
   This creates `.changelog_config.yaml` with auto-detected modules.

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

Creates a `.changelog_config.yaml` configuration file in your repository.

* Auto-detects monorepo modules or uses repository name for single repos
* Prompts for repository type (monorepo or single repo)

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
* `SSL_VERIFY` - Set to `false` to disable SSL verification (for internal proxies)

**Example:**
```bash
SSL_VERIFY=false automated-changelog generate --dry-run
```

## Core Functionality

1.  **Monorepo Aware:** Identifies distinct modules (packages, services, libraries) within your monorepo based on paths defined in a configuration file.
2.  **Commit Analysis:** Processes `git log` history, specifically focusing on squashed merge commits since the last time the tool was run (tracked via metadata within the `CHANGELOG.md`).
3.  **Intelligent Filtering:** Filters out minor commits (e.g., chores, docs, tests, typos) based on customizable rules (commit message prefixes, keywords, file paths) defined in the configuration.
4.  **LLM-Powered Summarization:**
    * Generates concise, bulleted summaries of the *significant* changes made within **each module**.
    * Creates a high-level **overall summary** highlighting key activities across the entire monorepo for the period.
5.  **Markdown Output:** Formats the summaries (overall and per-module with commit counts) into a Markdown section.
6.  **Incremental Updates:** Reads the existing changelog file (e.g., `CHANGELOG.md`) and automatically **prepends** the newly generated section, maintaining a running history.
7.  **Historical Generation:** Generate changelogs for specific date ranges using `--from-date` and `--to-date` flags. Perfect for backfilling weekly or monthly changelog entries for repositories with extensive history.

**How it Works:**

* **Configuration:** Uses a `.changelog_config.yaml` file (checked into your repo) to define modules, filtering rules, the output changelog file path, and optionally customize LLM prompts. An `init` command helps generate this file.
* **Execution:** Run the `generate` command from within your monorepo. It uses the Git CLI and interacts with a configured LLM to produce the summaries.
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

The summarization happens in two stages:

### Stage 1: Module-Level Summaries

For each module in your repository:

1. **Filter commits** based on rules in `.changelog_config.yaml`:
   - Ignore commits with certain prefixes (`chore:`, `docs:`, `test:`, etc.)
   - Ignore commits with certain keywords (`typo`, `cleanup`, etc.)

2. **Send filtered commits to LLM** with:
   - Module name
   - List of commit messages (hash, subject, author, date)
   - Custom prompt from config (e.g., "Summarize in 2-4 bullet points")

3. **LLM generates** a concise summary focusing on features, fixes, and breaking changes

### Stage 2: Overall Summary (Monorepos Only)

If you have multiple modules:

1. **Collect all module summaries** from Stage 1

2. **Send module summaries to LLM** with:
   - All module names and their summaries
   - Custom overall summary prompt from config

3. **LLM generates** a high-level summary highlighting key themes across all modules

### Output Format

The final changelog entry includes:
- **Overall summary** (for monorepos) - High-level themes
- **Module summaries** - LLM-generated bullet points per module
- **All commits** (collapsible) - Full commit list for reference

**Example:**
```markdown
## [2025-11-05]

### Summary
This release focuses on authentication improvements and bug fixes across
the platform, with significant updates to the user service and API layer.

### Changes by Module

**user-service** (5 commits)

- Added OAuth2 authentication support with Google and GitHub providers
- Implemented password reset functionality via email
- Fixed session timeout bug causing unexpected logouts

<details>
<summary>All commits</summary>

- abc1234 Add OAuth2 authentication (John Doe, 2025-11-05 14:30)
- def5678 Implement password reset (Jane Smith, 2025-11-04 10:15)
- ghi9012 Fix session timeout bug (John Doe, 2025-11-03 09:45)
...
</details>
```

**Goal:**

To save developer time and improve project visibility by automating the creation of consistent, informative, and easy-to-read changelogs specifically tailored for the complexities of a monorepo structure.
