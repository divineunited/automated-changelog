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


## 5. Get changes per commit [ X ]
For each commit, just put the commit ID and the author, date, and message after in a way that is clean and looks almost as clean as `git log --oneline`. It should be very easy to go through them all. No LLM summary needed here.
Also, since we're tracking each commit (using the short commit ID similar to the `git log --oneline` ID), you don't need to have the commit ID after each update that is appended.

## 6. Processing and Summarization. [ ]
For each service of each monorepo (or for that repo if it's not a monorepo), utilize everything you have so far to create a nice concise summary in one paragraph of all the changes that have happened since the last update. Apply the filtering rules from the `changelog_config.yaml` to the list of commits for each module from the LLM summary. 


Now, per module, prepare the input for the LLM, call the LLM API using what we defined (LITELLM_PROXY_API_KEY, LITELLM_PROXY_API_BASE) using the prompts defined in the changelog_config.yaml. Store each summary for each repo in the CHANGELOG.md

If it's a monorepo:
Collect all the module summaries, make a second LLM call to summarize the overall activity of the entire monorepo and put it as the overall summary in the CHANGELOG.md outside of all the modules at the top. And yes, in this case, you'll need to store the state at the top.
