# Issue-driven reconstruction

Use the **Revive a research paper** Issue form. It applies `revive:ready` automatically. Requests by the configured maintainer and collaborator are eligible; public strangers are not executed. Never post private data here.

A local deterministic watcher on the maintainer computer polls every two minutes. Quiet polls use GitHub API only, not an AI model. Eligible issues start the installed Codex CLI under the existing local login in an isolated Git worktree. This is a custom launchd service, not a Codex desktop Automation or a GitHub-hosted compute worker. The computer must remain awake and connected.

The worker implements one paper folder, runs software checks and creates a PR. It does not merge automatically. Closing the issue or adding `revive:cancel` stops an active run at the next control check (normally within 30 seconds). Changing trusted issue content or trusted PR feedback permits another attempt; unchanged completed requests are deduplicated. Failures have bounded retries and private logs. Builds are not device verification. External datasets, hardware and permissions may create real blockers; these are reported, not invented successes.

Public source publication has a credential-pattern and file-type preflight, **not a guarantee that all sensitive information is detected**. Workers must use public/synthetic inputs and respect publication boundaries. Python tests are independently run by the supervisor. Large generated media require separate publication review; this initial worker does not automatically upload arbitrary video or APK binaries.

GitHub Actions runs repository tests on push/PR. It is not the local implementation executor. This initial system polls issues and trusted feedback on linked PRs; it does not respond to arbitrary new PRs or merge them.

## Local deployment

Copy a private config with `repository`, `trusted_users` (numeric IDs), `checkout`, `state_dir`, and `worktree_parent`. Run `python3 automation/revive_runner.py poll --config /private/config.json --execute` from a local scheduler. Paths, login material and execution logs are not committed. See the default engine command in the runner. Inspect private status with its `status` action.
