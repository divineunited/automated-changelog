# Automated Changelog Phase 2 - Git Interaction and State

## 4. Manage state and Fetch Commits [ X ]

Implement a function to read the latest commit hash from the CHANGELOG.md. Handle the case where the file or hash doesn't exist (return None or a default behavior).
Implement a function to write the latest processed commit hash to CHANGELOG.md in a structured way.

Fetch Commits and write to CHANGELOG.md:
Use `subprocess` to run `git log`.
Determine the commit range:
- If a hash was read from the state file: `git log <last_hash>..HEAD ...`
- If no hash (first run): `git log --since="1 week ago" ...` (or another default)
Use `--pretty=format:"%H ||| %s"` (or similar) to get the hash and subject easily parsable. Split the output into individual commits.
Note: Ensure the script is run from within the target Git repository, or use `git -C <repo_path> log ...`
Write some fake summary for now but track the latest commit hash.
