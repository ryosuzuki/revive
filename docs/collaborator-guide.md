# Revive collaborator guide

## Submit a request (Ada)

1. Sign into GitHub as your configured collaborator account and open [New issue](https://github.com/ryosuzuki/revive/issues/new/choose).
2. Choose **Revive a research paper**. Supply a lowercase paper slug, title/DOI, public source links, target platform, desired behaviors and concrete acceptance scenarios.
3. Select **apk**, **video**, and **physical-device** when required. Describe the camera view, original question, generated response and expected spatial behavior. A simple synthetic animation is not a substitute for a requested recorded-context demonstration.
4. Submit. The form adds `revive:ready`. Signed GitHub Webhooks now notify the local implementation queue immediately. No recurring two-minute poll or idle AI model is used. The real acceptance test dispatched in about 3.4 seconds after receipt; this is an observation, not a latency guarantee.
5. Watch the Issue for progress/checkpoints and its linked PR. Add corrections to the original Issue or linked PR; the implementation continues on the existing branch. Remove `revive:ready` to pause; add `revive:cancel` or close the Issue to cancel. Control checks normally occur within 30 seconds during execution.
6. Review the code, actual demo and limitations separately. PR creation is **ready for review**, not a declaration of paper equivalence, merged code, published media or successful hardware testing.

Keep private recordings, room scans, network addresses and credentials OUT of public Issues. Use the approved lab-private data location supplied privately. The public worker deliberately does not ingest that location automatically; private-data processing and lab delivery require the owning operator's separate private lane. Merely naming a file in an Issue does not grant publication rights.

## What executes

GitHub Webhook → raw-body HMAC and repository verification → durable delivery queue → numeric-ID authorization → one serialized local worker → isolated Git worktree → Codex CLI implementation → independently rerun tests and acceptance receipts → source/publication preflight → PR. Trusted follow-up content can resume the preserved checkpoint. Failed revisions retry up to three times with backoff; exhausted retries and missing hardware become explicit attention/blocked states, not fabricated completion. Mac availability, login and network connectivity are required.

The orchestrator runs on the operator Mac Studio. Unity builds/rendering can use an available approved lab Mac Studio; GPU inference requires a compatible approved CUDA worker. This is not a guarantee that every Issue can automatically reserve hardware. Shared storage is not a compute scheduler. Public assets are versioned in GitHub Releases; source stays under `papers/<slug>/`. Private originals and derivatives remain outside public Git history.

## AgentHands: install and reproduce

See [paper README](../papers/agent-hands/README.md) for exact backend, model, Unity, APK and replay commands, and [model setup](../papers/agent-hands/docs/GPU.md).

- Requirements: Python, ffmpeg, Unity 6000.4.5f1 plus Android support for builds; approved CUDA/PyTorch hardware for Qwen3-VL. Backend speech currently uses macOS `say`.
- Create a venv and install the paper package. Run its tests before processing data.
- Start the private model service and dialogue backend. Configure the headset's `server.json` to a reachable private backend; the public APK has no built-in lab address. Install with ADB, grant microphone permission, hold **A** to label/register at the controller position, and use the right trigger for questions.
- For an authorized recording ZIP, run `import_captures.py`, `transcribe.py`, `generate_replays.py`, `refine_responses.py`, `render_replays.py --host YOUR_UNITY_SSH_HOST`, then `package_demos.py`. Commands are in the paper README. Configure the remote Unity staging path explicitly.
- Validate full MP4 decoding, inspect registration/hand visibility and spoken answers, and retain hashes and provenance. Replay is not a live headset test.

The public Release contains **synthetic runtime fixtures**, not private captured-room footage. Recorded-context demos are delivered through the authorized lab-private channel. Physical Quest installation/alignment remains independently unverified. Do not describe a source download as one-click full reproduction without the separate models, hardware and permitted recording inputs.

## Trigger architecture and present status

The verified deployment is a dedicated signed-webhook receiver plus the existing Codex CLI worker, supervised locally by launchd. GitHub Actions runs CI only. A real GitHub comment event continued Issue #1 and updated the same PR #2 with 28 passing tests. Actual GitHub redelivery did not start a second attempt. Restarting the receiver preserved the same running worker and queued delivery. This validates the software lane, not arbitrary future papers or physical-device success.

Normal triggering is now event-driven. Startup immediately reconciles missed events; an hourly non-model sweep is retained for outage recovery. Accepted work remains durably pending while a worker is busy or waiting to retry. The old two-minute polling LaunchAgent is retired. The public ingress exposes only the dedicated HMAC receiver, not the OpenClaw Gateway or administrator API. See [trigger comparison and deployment evidence](trigger-architecture.md).
