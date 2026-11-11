# Verification

This public snapshot separates software evidence from physical acceptance.

| Gate | Status |
| --- | --- |
| Python behavior | 20/20 pass on the public sanitized copy (2026-11-11) |
| Typed event parsing and scheduling | Implemented; software tested |
| Calibrated projection and semantic regions | Implemented; numerical tests, not measured physical accuracy |
| Articulated-hand renderer | Public fixture rendered 160 actual Unity frames; eight-second H.264 video fully decode-checked; four representative gesture states visually inspected |
| Quest APK | Public 0.1.1/versionCode2 build succeeded in Unity 6000.4.5f1; aapt verifies ARM64 package org.prlab.agenthands, min API32/target36; ZIP integrity passed |
| On-headset install/launch/live question | Not verified |
| Physical registration/contact/occlusion accuracy | Not measured |

Gaze is intentionally absent. Native registration uses a spoken label and controller point. Replay perception and mesh registration are separate from an observed live object-selection event. Coarse room-depth occlusion is opt-in because unvalidated meshes may clip hands. Speech timing uses weighted-word and audio-energy heuristics. Network transport does not establish tracking accuracy; successful compilation does not establish physical interaction.

Private-room inputs and their media are excluded from this public repository. Public synthetic media are explicit fixtures, not evidence of live AI dialogue.

## Public build record (2026-11-11)

- Build source: `7d5839c54d4708f24dfeaaaaa80ad94dd51c2f6c` (documentation and generated YAML whitespace may differ from the build staging copy; executable source and package versions agree).
- APK: 41,662,070 bytes; SHA256 `f7b691f3113aab8c474a2aa863977960926d7a4c1313db77ffb168fe5f088299`.
- Checked absence of the previous deployment endpoint in source and APK (ASCII/UTF16). Backend configuration is explicit; no hidden default lab host remains.
- The synthetic fixture initially lacked stable event IDs; rendering exposed a null-key error. Explicit fixture IDs fixed it, and the 160-frame render then succeeded. No production response or registration was substituted with fixture values.
- No physical Quest availability was established by this public build task; installation, tracking and interaction remain unverified.
