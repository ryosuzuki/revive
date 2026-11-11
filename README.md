# Revive

**Readable, runnable reconstructions of research papers.** Each paper has its own source, explanation, media, build instructions and honest verification status. All project documentation is in English.

## Paper catalog

| Paper | Implementation | Status |
| --- | --- | --- |
| [AgentHands — CHI 2026](https://doi.org/10.1145/3772318.3790938) | [Unity Quest + Python](papers/agent-hands/) | No-gaze reconstruction; software-tested, physical Quest acceptance pending |

## Request a revival

Open an [Issue](https://github.com/ryosuzuki/revive/issues/new/choose) with the paper title/link, available code/video, desired platform, expected interaction and acceptance criteria. Do not attach private recordings, credentials or confidential conversations to this public repository. Use a separate private handoff for those inputs.

Issue intake and execution are distinct: an acknowledged request is not a completed implementation. Implementations should return source, tests, a reviewable PR, reproducible build instructions and clearly labeled media; report concrete blockers instead of silently claiming success. See [issue automation](docs/issue-automation.md) for the installed trigger and current operating limits.

## Layout

```text
papers/<paper-slug>/
  README.md          # Summary, paper links, quick start, status
  docs/              # Design, verification, provenance
  media/             # Small approved images or clearly labeled synthetic fixtures
  ...                # Editable implementation and tests
```

Large build artifacts and videos belong in [Releases](https://github.com/ryosuzuki/revive/releases), not ordinary Git history. Version each paper independently, for example `agent-hands-v0.1.0`. See [publication and assets](docs/publication-and-assets.md).

## Attribution

These are independent reconstructions, not the original authors' implementations unless a paper explicitly says otherwise. Paper, model, SDK and third-party licenses remain separate; consult each paper's provenance notes. No blanket license for third-party content is implied.

## Privacy

This is a public catalog. Use only public or synthetic inputs here. Private research recordings stay in their original private context, not in Issues or public Releases.

## Collaborator onboarding

[Detailed collaborator instructions](docs/collaborator-guide.md) · [Trigger architecture and deployment limits](docs/trigger-architecture.md)
