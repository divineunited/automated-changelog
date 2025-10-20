# Automated Changelog Phase 1

## 1. Set up Project Structure: [ X ]
In your automated-changelog repo, create a basic Python package structure (e.g., using src/automated_changelog or similar).
Choose a CLI framework (argparse is built-in, click or typer are popular alternatives) and set up the basic entry point (e.g., automated-changelog generate, automated-changelog init).
Add pyproject.toml for managing dependencies (like the LLM library, PyYAML) and build configuration.

## 2. Impliment `init` command [ X ] 
- Implement the automated-changelog init CLI portion
- this should create a .changelog_config.yaml file in the current working directory
- this should populate a template file that the user can then fill out further 
- It should have clear comments explaining each section (modules, filter rules, output file).
- It should ask the user if it's a monorepo, and if so, each folder will be considered it's own service, module, or library
- If it's not a monorepo, the whole repo should be considered it's own service, module, or library.
- It should also have filter rules similar to:

```
# Filtering rules for commits.
filter:
  # Commits starting with these prefixes will be ignored for summarization.
  ignore_prefixes:
    - "chore:"
    - "docs:"
    - "test:"
    - "ci:"
    - "refactor:"
  # Commits containing these keywords in the subject will be ignored.
  ignore_keywords:
    - "typo"
    - "cleanup"
    - "[skip ci]"
  # Commits ONLY touching files/paths matching these patterns will be ignored.
  ignore_paths_only:
    - "*.md"
    - "docs/"
    - "tests/"
    - ".github/"
```


## 3. Load the config file [ X ]
- the `generate` command should now load the file using a yaml parser
- it should look for the file in the current directory and if it's not there it should ask to init
- use a library like PyYaml
