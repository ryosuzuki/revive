# Verification

This public snapshot separates software evidence from physical acceptance.

| Gate | Status |
| --- | --- |
| Python behavior | 20/20 pass on the public sanitized copy (2026-11-11) |
| Typed event parsing and scheduling | Implemented; software tested |
| Calibrated projection and semantic regions | Implemented; numerical tests, not measured physical accuracy |
| Articulated-hand renderer | Implemented in Unity; public synthetic fixture uses this runtime |
| Quest APK | Android source/build path included; consult the exact public release manifest for the built revision |
| On-headset install/launch/live question | Not verified |
| Physical registration/contact/occlusion accuracy | Not measured |

Gaze is intentionally absent. Native registration uses a spoken label and controller point. Replay perception and mesh registration are separate from an observed live object-selection event. Coarse room-depth occlusion is opt-in because unvalidated meshes may clip hands. Speech timing uses weighted-word and audio-energy heuristics. Network transport does not establish tracking accuracy; successful compilation does not establish physical interaction.

Private-room inputs and their media are excluded from this public repository. Public synthetic media are explicit fixtures, not evidence of live AI dialogue.
