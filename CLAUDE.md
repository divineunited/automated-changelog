# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`automated-changelog` is a Python CLI tool that automatically generates human-readable changelogs by analyzing Git history and using LLMs to create concise summaries.

## Development Commands

### Environment Setup
```bash
# Create virtual environment and install dependencies using uv
make setup
source .venv/bin/activate
```

### Testing
```bash
# Run all tests with coverage
make test

# Run pytest directly
uv run pytest

# Run a single test file
uv run pytest tests/test_config.py

# Run a specific test function
uv run pytest tests/test_config.py::test_function_name
```

### Code Quality
```bash
# Format code with black and ruff
make format

# Run linters (ruff and mypy)
make lint
```

### Running the Tool
```bash
# Initialize configuration
make run-init
# or: uv run automated-changelog init

# Generate changelog (dry run)
make run-generate-dry
# or: uv run automated-changelog generate --dry-run

# Generate changelog (writes to file)
make run-generate
# or: uv run automated-changelog generate

# Skip LLM summarization (just list commits)
uv run automated-changelog generate --skip-llm

# Generate historical changelogs for specific date ranges
uv run automated-changelog generate --from-date 2025-10-26 --to-date 2025-10-27 --dry-run
uv run automated-changelog generate --from-date 2025-11-01  # All commits since this date
uv run automated-changelog generate --to-date 2025-10-31    # All commits until this date
```

### Building for PyPI
```bash
# Build distributions
make build

# Publish (manual)
uv run twine upload -u __token__ -p <your-pypi-api-token> dist/*
```

## Code Architecture

### Core Components

1. **cli.py** - Click-based CLI entry point with two main commands:
   - `init`: Creates `.changelog_config.yaml` configuration file
   - `generate`: Generates changelog entries from Git history

2. **config.py** - Configuration management:
   - `generate_config_template()`: Generates default configuration template
   - `load_config()`: Validates and loads YAML configuration
   - `get_repo_name()`: Gets repository name from git remote or directory

3. **git_state.py** - Git operations and state tracking:
   - `fetch_commits()`: Executes `git log` and parses commit data (hash, author, date, subject)
   - `read_last_commit_hash()`: Reads state marker from CHANGELOG.md
   - `write_changelog_entry()`: Prepends new entries and updates state marker
   - State is stored as HTML comment: `<!-- CHANGELOG_STATE: <commit_hash> -->`

4. **summarization.py** - LLM-powered summarization:
   - `filter_commits()`: Filters commits by prefixes, keywords, and paths
   - `generate_summary()`: Creates changelog summary via LLM

5. **llm.py** - LLM client interface:
   - Uses LiteLLM proxy for API calls
   - Requires `LITELLM_PROXY_API_BASE` and `LITELLM_PROXY_API_KEY` env vars
   - Supports SSL verification bypass via `SSL_VERIFY=false`

### Key Design Patterns

- **Incremental Processing**: State tracking via HTML comments in CHANGELOG.md eliminates need for separate state files
- **Date Range Mode**: Supports historical changelog generation with `--from-date` and `--to-date` flags. In this mode, state markers are NOT written to preserve incremental workflow
- **Filter-First Strategy**: Commits are filtered before LLM processing to reduce costs
- **LLM Input**: Only commit messages (hash, subject, author, date) are sent to LLM, not code diffs

### Important Implementation Details

- The tool only reads **commit messages**, not code changes or file diffs
- Filtering happens before LLM calls to minimize API costs
- State marker format: `<!-- CHANGELOG_STATE: <full-40-char-hash> -->`
- Git log format: `%H|||%h|||%an|||%ai|||%s` (parsed with `|||` delimiter)
- Date format in output: `YYYY-MM-DD HH:MM` (truncated from ISO 8601)

**Two Operating Modes:**
1. **Incremental Mode** (default): Uses state marker to track last processed commit. Fetches commits from last hash to HEAD. Updates state marker after generation.
2. **Date Range Mode** (`--from-date`/`--to-date`): Uses git log `--since`/`--until` for historical generation. Does NOT update state marker. Useful for backfilling weekly/monthly historical changelogs.

### Configuration File Location

The tool expects `.changelog_config.yaml` in the repository root with:
- `output_file`: Path to CHANGELOG.md
- `filter`: Commit filtering rules (prefixes, keywords, paths)
- `llm`: Optional LLM model and prompt customization

## Environment Variables

Required for LLM features:
- `LITELLM_PROXY_API_BASE`: Your LiteLLM proxy URL
- `LITELLM_PROXY_API_KEY` (or `LITELLM_API_KEY`): API key

Optional:
- `SSL_VERIFY=false`: Disable SSL verification for internal proxies
