# automated-changelog
LLM Summarized and Automated Changelog for Any Repo

## **Automated Changelog Generator**

`automated-changelog` is a Python CLI tool designed to automatically generate human-readable changelogs for Git **monorepos**. It analyzes squashed merge commits since its last run (tracked within the changelog file itself), summarizes significant changes using an LLM, and prepends these summaries to a `CHANGELOG.md` file.

**Core Functionality:**

1.  **Monorepo Aware:** Identifies distinct modules (packages, services, libraries) within your monorepo based on paths defined in a configuration file.
2.  **Commit Analysis:** Processes `git log` history, specifically focusing on squashed merge commits since the last time the tool was run (tracked via metadata within the `CHANGELOG.md`).
3.  **Intelligent Filtering:** Filters out minor commits (e.g., chores, docs, tests, typos) based on customizable rules (commit message prefixes, keywords, file paths) defined in the configuration.
4.  **LLM-Powered Summarization:**
    * Generates concise, bulleted summaries of the *significant* changes made within **each module**.
    * Creates a high-level **overall summary** highlighting key activities across the entire monorepo for the period.
5.  **Markdown Output:** Formats the summaries (overall and per-module with commit counts) into a Markdown section.
6.  **Incremental Updates:** Reads the existing changelog file (e.g., `CHANGELOG.md`) and automatically **prepends** the newly generated section, maintaining a running history.

**How it Works:**

* **Configuration:** Uses a `.changelog_config.yaml` file (checked into your repo) to define modules, filtering rules, the output changelog file path, and optionally customize LLM prompts. An `init` command helps generate this file.
* **Execution:** Run the `generate` command from within your monorepo. It uses the Git CLI and interacts with a configured LLM to produce the summaries.
* **State Management:** Stores the hash of the last processed commit **within a comment or metadata block inside the `CHANGELOG.md` file**. This ensures the tool only includes new changes in subsequent runs without requiring a separate state file.

**Goal:**

To save developer time and improve project visibility by automating the creation of consistent, informative, and easy-to-read changelogs specifically tailored for the complexities of a monorepo structure.
