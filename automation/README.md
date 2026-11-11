# Issue-driven Revive execution

This is an **authenticated GitHub webhook + durable local queue + Codex CLI worker**, not a GitHub-hosted agent and not a native desktop-app scheduled task. GitHub Actions runs software checks on pushes/PRs; it does not hold lab credentials or execute public issue text on lab machines.

## Requester experience

1. Open **Issues → New issue → Revive a research paper**.
2. Fill in paper slug, DOI/URL, requested behavior, public inputs, and acceptance tests. Submit.
3. The form applies `revive:ready`. An immutable numeric-ID allowlist accepts Ryo or Ada; unknown authors do not start execution.
4. The authenticated GitHub webhook detects the request immediately, claims one issue, and starts an isolated Git worktree and actual Codex implementation run.
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

The first command is a read-only dispatch preview (it can persist crash reconciliation locally). `--execute` launches one worker in the background; empty polls use no model. These commands are manual diagnostics/fallback entry points. Production uses the signed-webhook service below; do not install a second polling LaunchAgent, app Automation or cron watcher for the same queue. The scheduler must explicitly set PATH for `gh`, `git`, Python and the CLI; it requires the authenticated Mac to remain available. Parent/operator owns scheduler deployment and the real end-to-end acceptance test.

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

## Continuation, publication and acceptance gates

The dispatcher is a continuing state machine: `running → verification → publishing → ready_for_review`, with `failed → retry` from the **same owned worktree/branch**, `queued` after trusted request changes, and explicit `blocked`, `cancelled` or `needs_attention` outcomes. A successful model process is only the start of independent verification. Unmerged PR feedback is applied to the same branch/PR, preserving earlier implementation rather than starting from the catalog's main branch again. Prior closed/merged PRs need an explicit integration decision instead of silently being declared successful.

- Trusted issue body/comments and trusted PR reviews/comments form a stable content fingerprint. Runner-owned marked progress comments are excluded. A changed request stops the old engine and is fenced again before push/PR publication; the next run uses current context.
- Each live process has a birth identity as well as PID. API errors, timeouts, cancellation and supervisor interruption all reach owned-process-group cleanup. A live orphan engine prevents a new dispatch; an unprovable identity is not permission to kill another process.
- REST scans paginate all Issue/comment/review pages. Empty scans use no model. Five-minute progress checkpoints and verification/blocked/cancelled/failed states are visible in the original Issue. Exhausted automatic repair retries become a visible maintainer-attention state, not a silent finished/idle claim.
- The supervisor independently discovers a **nonzero** number of paper tests and runs them. It saves a private verification receipt tied to the exact commit. PR recovery requires that receipt, matching repository/base/head, and an OPEN or MERGED endpoint; a closed unmerged PR or mismatched SHA is not a success.
- The Issue form's **Required acceptance** checkboxes add `apk`, `video`, or `physical-device`. Free-text older requests conservatively recognize those requirements in their requested-deliverables section. An APK/video cannot be satisfied merely by a Python test: `REVIVE_RESULT.json` must identify an actual file, byte count and SHA256 in the issue's private artifact directory. APK ZIP/manifest and full video decoding are independently checked. Physical-device acceptance requires a separate operator-owned evidence receipt for the exact request fingerprint.
- Source-only PR publication never publishes raw media by default. Non-text assets (including PNG/JPG/PDF) need both a per-paper `PUBLIC_ASSETS.json` entry and a hash independently approved in the private operator config. The worker cannot authorize its own asset just by writing a manifest. Review and sanitize images/metadata before approval. This mechanical audit is an additional check, not a guarantee against every possible privacy leak.
- `ready_for_review` means verified source PR, **not merged and not fully delivered public releases**. APK/video release publication remains `review-pending` until the independent publication owner checks provenance and publishes the authorized assets. Device gates remain blocked until real evidence exists.

`PUBLIC_ASSETS.json` example (per paper):

```json
{"assets":[{"path":"synthetic-demo.png","sha256":"SHA256","origin":"synthetic","source":"reproducible generator","license":"CC0"}]}
```

The operator separately adds that digest to `approved_public_asset_hashes` in the **private** config after inspection. Do not approve private room captures merely because they are present locally.

The worker may write requested build artifacts only to its issue-specific private artifact directory, supplied by `--add-dir`; it cannot write the independent operator acceptance receipt through that grant. An operator device receipt is kept outside source at `operator-device-evidence.json` in the private state directory, keyed by Issue number with `source_fingerprint`, `status: passed`, and a concrete `evidence` locator. Keep private paths/device details out of public comments.


## Webhook deployment

Preferred entrypoint: `python3 automation/revive_webhook.py serve --config /private/runtime/config.json`. Bind only `127.0.0.1:18472`; the sole POST route is `/webhooks/github`, with JSON body cap 2 MiB and a 10-second socket read timeout. An independently provisioned HTTPS reverse proxy must expose only this receiver, never the Gateway/admin port. Do not keep the old two-minute polling LaunchAgent active beside it.

Add `webhook` to private config: `host`, `port`, `path`, immutable GitHub `repository_id`, `secret_command` (trusted argv that prints the 1Password-backed HMAC secret), `busy_retry_seconds: 5`, `reconcile_seconds: 3600`. The secret is captured and cached only in receiver memory; it is never a command-line value, plaintext file, source file or log entry.

The receiver verifies HMAC-SHA256, repository identity and trusted sender IDs; it deduplicates delivery IDs and commits minimal metadata to a private SQLite FULL-synchronous durable queue before HTTP202. Event bodies are never shell commands or persisted transcripts. Own marked progress comments are ignored to prevent loops. Pending deliveries survive busy workers, failed-attempt repair backoff, API/database errors and receiver restarts; dispatch alone never consumes an event. A local source-change marker immediately triggers the existing worker's fresh-source fence.

Startup performs an immediate reconciliation for events missed while offline, followed by hourly non-model reconciliation. Normal dispatch is event-driven, not two-minute AI polling. Public GitHub delivery/redelivery history and the private `webhook-dispatch-status.json` distinguish actual delivery from local fixture tests. Database/API failures remain visible in private health receipts and are retried; they do not silently kill the dispatcher while HTTP keeps acknowledging.
