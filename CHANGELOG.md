<!-- CHANGELOG_STATE: b17c762a4ff6a672f16f0ca775eb4a7dcef8a743 -->

## [0.3.0] - 2025-11-06

### Breaking Changes

- **Removed monorepo support**: The tool now treats each repository as a single unit, simplifying the codebase and eliminating the issue where commits spanning multiple areas were duplicated across module sections
- **Configuration schema changes**:
  - Removed `modules` field from `.changelog_config.yaml`
  - Changed LLM prompt fields from `module_summary_prompt` and `overall_summary_prompt` to a single `summary_prompt`
- **Migration required**: Existing configurations must remove the `modules` field and update LLM prompt field names

### Changed

- Simplified CLI `init` command - no longer asks about monorepo structure
- Changed from two-stage summarization (per-module + overall) to single repository summary
- Updated changelog output format from "Changes by Module" to "Changes (N commits)"
- Simplified configuration template with fewer required fields

### Removed

- `get_monorepo_modules()` function and module detection logic
- Module iteration throughout the codebase
- Per-module commit filtering and summarization

### Documentation

- Updated README to focus on single repository workflow
- Updated CLAUDE.md with simplified architecture
- Removed all monorepo references from documentation

## [0.2.0] - 2025-11-06

### Added

- **Date range support for historical changelog generation**: New `--from-date` and `--to-date` CLI options allow generating changelogs for specific time periods
- Support for backfilling weekly or monthly changelog entries for repositories with extensive history
- Two operating modes: incremental (default with state tracking) and date range (historical generation without state updates)

### Changed

- Changelog headers now show date ranges when using `--from-date`/`--to-date` (e.g., `[2024-01-01 to 2024-01-07]`)
- State markers are only written in incremental mode, preserving the incremental workflow when generating historical entries

### Documentation

- Updated README with date range examples and usage
- Updated CLAUDE.md with developer commands and architecture details
- Added comprehensive CLI help text for new date parameters

## [0.1.0] - 2025-11-05
<!-- LATEST_COMMIT: b17c762a4ff6a672f16f0ca775eb4a7dcef8a743 -->

### Changes by Module

**automated-changelog** (9 commits)

- **Git integration**: Added commit fetching and state management to automatically extract changes from git history, including commit IDs, authors, and dates
- **Configuration system**: Implemented `init` command to generate `.changelog_config.yaml` files and added YAML parsing for configuration management
- **CLI foundation**: Bootstrapped the tool with a command-line interface for managing automated changelogs

<details>
<summary>All commits</summary>

- `b17c762` Get changes per commit - and persist them along with author and date (Danny Vu, 2025-10-27 00:53)
- `0892e30` Add commit id to each appended changelog (Danny Vu, 2025-10-26 23:49)
- `1a68122` Add changelog_config file for this repo (Danny Vu, 2025-10-26 23:18)
- `092c580` Implement git state management and commit fetching (Danny Vu, 2025-10-26 23:17)
- `3692aff` Phase 1 Step 3 - Load the Config File with Yaml Parsing (Danny Vu, 2025-10-19 22:22)
- `a0dc96e` Implement init command for .changelog_config.yaml (Danny Vu, 2025-10-19 22:11)
- `7bffc5e` chore: mypy fix (Danny Vu, 2025-10-19 07:30)
- `179f970` Bootstrap Repository with CLI (Danny Vu, 2025-10-18 23:02)
- `21493d1` Initial commit (Danny Vu, 2025-10-18 14:17)

</details>



