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

## Issue #3 work in progress — 2026-11-12 UTC

This section supersedes old renderer/key/model descriptions only for the Issue3 branch. It does not declare the Issue complete. [Setup and acceptance procedure](ISSUE-3-SETUP.md).

| Component / paper reference | Current implementation and differences | Evidence / unresolved gate |
| --- | --- | --- |
| Embodiment, §3.3 / Fig.1 | Procedural articulated blue hands and small emissive orb. Original paper meshes/particles are unavailable here; procedural geometry and emission are approximations, not an exact mesh/material reproduction. | New runtime tests verify orb plus two hands before a plan. Comparison images/recorded visual acceptance pending. |
| Idle and conversation, §4.4 | Both hands remain visible, relaxed pose with subtle sinusoidal motion. Listening/thinking state, orb pulse and exponential root-pose blending; transitions are authored approximations. | New Unity tests check thinking, active response, unused-hand visibility, idle return and bounded transition. On-headset acceptance pending. |
| Object registration, §4.1 / Fig.3 | Replay uses existing calibrated VLM/mesh path. Native spoken-label/controller-point registration uses assumed 15cm box, not paper VLM-estimated dimensions or eye-confirmed selection. | Existing numerical software tests; independent physical accuracy not measured. |
| Spatial targeting, §4.1 / Appendix | Python semantic-grid/axes pipeline retained. Direct Quest parser supports prompted event/object subset, not all semantic-grid attributes. | Unknown target diagnostics tested; rotated semantic-grid equivalence for direct mode not claimed. |
| Gaze/input, §4.1/§4.5 | Gaze intentionally omitted. Controller selection instead of gaze; microphone WAV sent to provider in direct mode instead of Android SpeechRecognizer. | Input substitution explicit; no eye-tracking equivalence claim. |
| Gesture coverage, §3.2.3 / Appendix | Existing procedural primitives/effects/interactions retained. Direct parser prompts a bounded subset. Not original authored animations, particles or full gesture taxonomy fidelity. | Parser and scheduler tests; complete visual taxonomy acceptance pending. |
| Animation/arbitration, §4.4.3 | Shared runtime schedules left/right/both events, retains idle hands, blends root motion. Native direct parser currently chooses right for single-hand events rather than full oldest-transition arbitration. | Unity runtime tests and Python arbitration tests; native parity remains partial. |
| Speech alignment, §4.4.1–2 | Weighted-word/audio-energy heuristic in Python; character-position heuristic in native direct mode. Debug word highlight is approximate, not forced alignment or provider word timestamps. | Timing bounds tests; phoneme/sample-level synchronization not claimed. |
| Interactive gestures, §4.4 | Recorded/live hand root proximity with timeouts; high-five/hold/shake behavior. Idle hands must not trigger contact for the active hand. | Existing contact/timeout software tests; physical user contact pending. |
| Response/TTS models, §4.5 | Original response ID unavailable to operator (404). Exact TTS ID available and returned real audio. Replacement proposed for approval, not enabled silently. Legacy replay fixtures remain Qwen/macOS speech. | Authenticated Models API and real TTS smoke test. New approved-model conversation/replays pending approval. |
| Runtime architecture, §4.5 | Quest/OpenXR instead of paper Samsung Galaxy XR. Shared Python replay/LAN path plus project-added direct HTTPS Quest provider client. | Initial Android build succeeds; direct-client build/physical acceptance tracked separately. |
| Debug panel, project addition | Raw tagged output retained separately from parsed active events; approximate current word and unresolved-target diagnostics; X toggles world-space text. | Unity raw-preservation/invalid-target tests. Readable headset and full replay inspection pending. |
| API-key config, project addition | App-scoped api_key.txt, HTTPS fixed provider origin, headers only, redirects disabled, sanitized error messages, no bundled key. Explicit replacement-model flag. | Missing/empty file and unapproved-replacement runtime tests pass; rejected-key network/device check pending. |
| Study versus system, §4.5 and study sections | The paper system description and study demonstrations do not prove our runtime. Scripted replay fixtures demonstrate only their recorded conditions; Unity tests do not establish live human interaction. | All public/private media must be labeled by actual provenance. Physical checks and live inference remain separate gates. |

Current software evidence: original Python20/20; new actual Unity runtime15/15. Initial new Android build succeeded. Neither set satisfies the requested physical-device acceptance or completed replay delivery.
