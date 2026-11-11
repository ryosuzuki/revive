# Publication and large assets

## What goes where

| Content | Destination |
| --- | --- |
| Source, build instructions, small approved figures | Per-paper directory in Git |
| APKs, videos, source ZIPs and reproducibility manifests | Paper-versioned GitHub Releases |
| Private room captures, conversations, participant data, keys | Separate private storage; never public Git or public Releases |
| Model weights and installed dependencies | External model/package distribution; do not commit caches |

Use tags such as `agent-hands-v0.1.0`, `agent-hands-v0.1.1`. New versions can have new Release assets without rewriting Git history. GitHub's asset-size and repository/LFS quotas apply independently. Use immutable versioned names and SHA256 manifests so a download can be matched to source. If an asset needs replacement, make a new release version rather than silently changing evidence under an old URL.

Git LFS is updateable, not permanently frozen, but stores each large-file version and has storage/bandwidth limits. It is optional here: ordinary source stays in Git and downloadable builds/media go in Releases. Releases are also public when the repository is public. They are not a privacy exception.

Every paper page should identify the original paper, source provenance, implemented features, substitutions, exact source revision, build procedure, tested platform and remaining limitations. Label media as synthetic, recorded replay or live physical footage. Do not infer permission to publish a room/participant recording merely because it was available for implementation.
