# Issue-driven reconstruction

Use the **Revive a research paper** Issue form. It applies `revive:ready` automatically. Requests by the configured maintainer and collaborator are eligible; public strangers are not executed. Never post private data here.

Signed GitHub events are validated and durably queued by a dedicated local receiver. Normal dispatch is immediate and event-driven. Startup and an hourly recovery sweep reconcile missed events without an idle AI model. Eligible issues start the installed Codex CLI under the existing local login in an isolated Git worktree. This is a custom launchd service, not a Codex desktop Automation or a GitHub-hosted compute worker. The computer must remain awake and connected.

The worker implements one paper folder, runs software checks and creates a PR. It does not merge automatically. Closing the issue or adding `revive:cancel` stops an active run at the next control check (normally within 30 seconds). Changing trusted issue content or trusted PR feedback permits another attempt; unchanged completed requests are deduplicated. Failures have bounded retries and private logs. Builds are not device verification. External datasets, hardware and permissions may create real blockers; these are reported, not invented successes.

Public source publication has a credential-pattern and file-type preflight, **not a guarantee that all sensitive information is detected**. Workers must use public/synthetic inputs and respect publication boundaries. Python tests are independently run by the supervisor. Large generated media require separate publication review; this initial worker does not automatically upload arbitrary video or APK binaries.

GitHub Actions runs repository tests on push/PR. It is not the local implementation executor. The receiver subscribes to Issue, Issue-comment, pull-request and review events; the worker freshly reads trusted scope and linked feedback. It does not respond to arbitrary new PRs or merge them.

## Local deployment

Copy a private config with `repository`, `trusted_users` (numeric IDs), `checkout`, `state_dir`, and `worktree_parent`. Run `python3 automation/revive_webhook.py serve --config /private/config.json` as the sole supervised dispatcher. Configure a private `webhook` block as described in [the operating guide](../automation/README.md); retire the old polling scheduler. Paths, login material and execution logs are not committed. See the default engine command in the runner. Inspect private status with its `status` action.

## Initial polling deployment — 2026-11-11 (historical)

The local Mac Studio watcher was installed and observed exiting successfully. An actual [test Issue #1](https://github.com/ryosuzuki/revive/issues/1) invoked the installed Codex CLI, which wrote a ray/box implementation, English README, result manifest and 18 synthetic tests. The supervisor independently ran the tests and created [PR #2](https://github.com/ryosuzuki/revive/pull/2), head `f6a72f18527660a9cb2c8e4671c10904e34ebb2a`. GitHub checks passed. A second poll returned `idle`, without another run.

The first attempt exposed unsupported symlinked writable roots; deployment now uses resolved real-volume paths. This proves the Issue-to-code/tests-to-PR path, not arbitrary-paper fidelity, future APK correctness or physical hardware success. The test PR is deliberately left open for inspection.

## Signed-webhook acceptance — 2026-11-11

Receiver source: `5e8ccf8f36ee8fc1d588e842fec7c8e89e8d214d`; **52 independent software tests passed**. A real [trusted follow-up comment](https://github.com/ryosuzuki/revive/issues/1#issuecomment-6799830118) was delivered by GitHub with HTTP202 and started the existing worker approximately **3.4 seconds after receipt**. It implemented a new ray/box hit-point API, passed **28 paper tests**, and updated the same [PR #2](https://github.com/ryosuzuki/revive/pull/2) to `29301d5de7d434b14630881829c53bfdc4228481`; CI passed.

GitHub redelivery of the exact delivery ID returned HTTP202 with one durable event row and one implementation attempt. Restarting only the receiver preserved the same running worker and delivery. Invalid HMAC and wrong-repository requests were rejected; only the exact webhook route is accepted. The 120-second polling service was unloaded and retired. The recovery sweep is hourly and also runs immediately at startup. These observations do not promise future event latency or physical hardware correctness.
