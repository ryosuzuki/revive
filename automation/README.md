# Issue-driven Revive execution

This is a **local deterministic watcher + Codex CLI worker**, not a GitHub-hosted agent and not a native desktop-app scheduled task. GitHub Actions runs software checks on pushes/PRs; it does not hold lab credentials or execute public issue text on lab machines.

## Requester experience

1. Open **Issues → New issue → Revive a research paper**.
2. Fill in paper slug, DOI/URL, requested behavior, public inputs, and acceptance tests. Submit.
3. The form applies `revive:ready`. An immutable numeric-ID allowlist accepts Ryo or Ada; unknown authors do not start execution.
4. The local watcher detects the request (recommended interval: 120 seconds), claims one issue, and starts an isolated Git worktree and actual Codex implementation run.
5. Codex implements, builds/tests, inspects outputs, and iterates. The supervisor independently runs the paper's Python regression checks, audits owned source paths/public artifacts, and publishes a **PR for review**, not an automatic merge.
6. Trusted issue comments and PR review/comments become follow-up context. A fresh trusted-content fingerprint can initiate another isolated iteration. Closing the original issue or adding `revive:cancel` stops a running worker at its next 30-second check and prevents later publication checks. Remove `revive:ready` to pause.

No DM is required. A public Issue is public: private recordings and credentials must never be attached. A request requiring private input stops with an explicit external gate instead of silently publishing it.

## Installation

Keep runtime config, prompts, logs, state and model sessions **outside this public checkout**. Use `config.example.json` as a schema, replacing paths with absolute private paths. Do not copy authentication files. The worker unsets inherited `CODEX_HOME` and uses the normal operator's already authenticated CLI; run its `login status` first. A configured model is not forced: the installed CLI's current default is used.

```sh
python3 automation/revive_runner.py poll --config /private/runtime/config.json
python3 automation/revive_runner.py poll --config /private/runtime/config.json --execute
python3 automation/revive_runner.py status --config /private/runtime/config.json
```

The first command is a read-only dispatch preview (it can persist crash reconciliation locally). `--execute` launches one worker in the background; empty polls use no model. Schedule only this deterministic command, e.g. a user LaunchAgent `StartInterval=120`. Do not also install a second app Automation or cron watcher for the same queue. The scheduler must explicitly set PATH for `gh`, `git`, Python and the CLI; it requires the authenticated Mac to remain available. Parent/operator owns scheduler deployment and the real end-to-end acceptance test.

Each worker receives issue context through a private prompt file/stdin, never shell interpolation. It may write only its `papers/<slug>/` path. The wrapper requires `REVIVE_RESULT.json` with meaningful passed test evidence plus actual independently runnable `tests/test_*.py`; it does not accept prose "done" as completion. The path/secret/media audit is an additional guard, not proof of all possible data privacy. Human review of public research artifacts remains required.

## Execution and failure semantics

- File locks serialize claim updates and enforce one live worker globally.
- The state records process identity, attempt, fingerprint and worktree. Live claims are not duplicated. A vanished worker becomes failed, never successful.
- Each failed attempt retains its worktree/logs; up to three attempts run per request revision with bounded backoff. Blocked results require new trusted issue content to resume.
- Status comments use stable markers to deduplicate sends. A PR-creation/readback failure is reconciled against the prior branch before another execution attempt.
- Cancellation is rechecked before push and PR creation. A closed Issue cannot undo a previously published PR; the recorded endpoint is reported honestly.
- `succeeded` means **verified PR created**, not merged, not physical-device tested, and not a complete paper replication. Incomplete device acceptance remains explicitly documented.
- Runtime raw errors/logs remain private; public status comments contain only generic execution state and reviewed links.
- New source work never changes the dispatcher or expands its own authority. Public source ZIPs/releases require separate publication review; the default runner refuses media/binary source commits.

## Testing

```sh
python3 -m unittest discover -s tests -v
```

The automated cases cover author authorization, cancellation, traversal/injection-shaped slug rejection, quoted task data, quiet polls, active dedupe, no repeat after success, stale claim recovery, publication audits and failure state. These are software tests; the deployment record must separately provide the actual trusted Issue → Codex edits/tests → GitHub PR evidence. A mocked subprocess is not that acceptance test.
