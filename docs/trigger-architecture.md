# Trigger architecture review — 2026-11-11

This is a targeted review of official documentation and deployed configuration, not a latency benchmark or an exhaustive deep-research claim.

## Findings

- Previous custom launchd interval: 120 seconds (retired after webhook acceptance). Quiet checks call GitHub APIs, not an LLM. Normally 720 scheduler opportunities/day; API request count can exceed that because feedback scans paginate. Detection is delayed up to the interval plus scheduling/network delay. Working, but not optimal for immediate dispatch.
- GitHub recommends webhooks instead of polling. Verify raw-body HMAC, repository and immutable sender IDs; record delivery IDs durably, acknowledge quickly and enqueue work. Reconcile missed deliveries after outages. Webhook delivery alone does not mean implementation completion.
- OpenClaw offers authenticated `/hooks/agent` and `/hooks/wake`, disabled by default, plus supervised stream-command schedules. Its native condition watchers still poll; moving the same 120-second check into an Automation does not make it event-driven. A stream also needs a genuine event source; wrapping an API polling loop in it does not eliminate polling.
- GitHub cannot directly authenticate to the standard OpenClaw bearer hook just by setting its webhook secret: GitHub sends an HMAC signature. Use a validating adapter, or a trusted GitHub Actions bridge with a separately stored hook token. Preserve durable dispatch state in the existing worker.
- GitHub Actions can react to `issues`, `issue_comment`, and review events on GitHub-hosted runners, then notify a private worker. It needs an authenticated route to the Mac (narrow HTTPS ingress or private-network bridge) and new credential provisioning. It is not magically connected by adding an event stanza.
- Self-hosted Actions runners can execute on a Mac, but persistent runners on public repositories expose a substantially larger execution surface. They are not selected as a shortcut for the privileged operator Mac. A restricted disposable executor is a separate deployment decision.

## Recommendation

Use events as the primary trigger and a low-frequency reconciliation sweep for recovery. Retain immutable author checks, one active claim, request-fingerprint fencing, cancellation, checkpoint reuse, independent tests and media/device gates. The deployed implementation now uses a dedicated HMAC receiver and narrow HTTPS ingress, not a public Gateway endpoint or self-hosted Actions runner. Actual GitHub delivery, duplicate redelivery and receiver-restart continuity were verified. Cancellation/source-fencing and retry/outage retention have software regression coverage; do not relabel those tests as a fresh physical-device test. The former two-minute scheduler is retired; startup and hourly reconciliation remain for missed events.

## Official sources inspected

- [GitHub REST best practices: avoid polling](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api#avoid-polling)
- [GitHub webhook best practices](https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks)
- [GitHub Actions events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
- [Self-hosted runners](https://docs.github.com/en/actions/concepts/runners/self-hosted-runners)
- [OpenClaw inbound webhooks](https://docs.openclaw.ai/automation/cron-jobs/webhooks)
- [OpenClaw stream and condition schedules](https://docs.openclaw.ai/automation/cron-jobs/schedules)

Local installed OpenClaw docs at the same `automation/cron-jobs/` paths were also inspected. No repository webhook or self-hosted Actions runner was registered at the time of the check. That inspection does not establish the state of unrelated repositories or gateways.

Deployment and exact acceptance evidence: [Issue automation](issue-automation.md#signed-webhook-acceptance--2026-11-11).
