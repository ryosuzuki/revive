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
| Embodiment, §3.3 / Fig.1 | Procedural articulated blue hands and small emissive orb. Original paper meshes/particles are unavailable here; procedural geometry and emission are approximations, not an exact mesh/material reproduction. | New runtime tests verify orb plus two hands before a plan. Three recorded timelines generated; question/thinking/response/idle states visually inspected. Public paper-vs-synthetic comparison sheet added. |
| Idle and conversation, §4.4 | Both hands remain visible, relaxed pose with subtle sinusoidal motion. Listening/thinking state, orb pulse and exponential root/finger-pose blending; transitions are authored approximations. | New Unity tests check thinking, active response, unused-hand visibility, idle return and bounded transition. On-headset acceptance pending; initial install succeeded, first startup exposed a field-initializer error and was corrected, with a new lifecycle regression. |
| Object registration, §4.1 / Fig.3 | Replay uses existing calibrated VLM/mesh path. Native spoken-label/controller-point registration uses assumed 15cm box, not paper VLM-estimated dimensions or eye-confirmed selection. | Existing numerical software tests; independent physical accuracy not measured. |
| Spatial targeting, §4.1 / Appendix | Python semantic-grid/axes pipeline retained. Direct Quest parser supports six-face axis-aligned semantic grids; named semantic parts and inferred object rotation are not provided by spoken-label registration. | Unknown target diagnostics, canonical native grids and invalid-region rejection tested; rotated semantic-grid equivalence for direct mode not claimed. |
| Gaze/input, §4.1/§4.5 | Gaze intentionally omitted. Controller selection instead of gaze; microphone WAV sent to provider in direct mode instead of Android SpeechRecognizer. | Input substitution explicit; no eye-tracking equivalence claim. |
| Gesture coverage, §3.2.3 / Appendix | Existing procedural primitives/effects/interactions retained. Direct parser prompts a bounded subset. Not original authored animations, particles or full gesture taxonomy fidelity. | Parser and scheduler tests; complete visual taxonomy acceptance pending. |
| Animation/arbitration, §4.4.3 | Shared runtime schedules left/right/both events, retains idle hands, blends root motion and finger-joint poses. Native direct parser now uses oldest-hand arbitration and atomic double-hand interruption. Idle body follows the view with smoothing; active gesture targets remain in world coordinates. | Unity runtime tests and Python arbitration tests; native parity remains partial. |
| Speech alignment, §4.4.1–2 | Weighted-word/audio-energy heuristic in Python; weighted-word heuristic in native direct mode. Debug word highlight is approximate, not forced alignment or provider word timestamps. | Timing bounds tests; phoneme/sample-level synchronization not claimed. |
| Interactive gestures, §4.4 | Recorded/live hand root proximity with timeouts; high-five/hold/shake behavior. Idle hands must not trigger contact for the active hand. | Existing contact/timeout software tests; physical user contact pending. |
| Response/TTS models, §4.5 | Original response ID unavailable to operator (404). Exact TTS ID available and returned real audio. Replacement proposed for approval, not enabled silently. Legacy replay fixtures remain Qwen/macOS speech. | Authenticated Models API and real TTS smoke test. New approved-model conversation/replays pending approval. |
| Runtime architecture, §4.5 | Quest/OpenXR instead of paper Samsung Galaxy XR. Shared Python replay/LAN path plus project-added direct HTTPS Quest provider client. | Initial Android build succeeds; direct-client build/physical acceptance tracked separately. |
| Debug panel, project addition | Raw tagged output retained separately from parsed active events; approximate current word and unresolved-target diagnostics; X toggles world-space text. | Unity raw-preservation/invalid-target tests. Readable headset and full replay inspection pending. |
| API-key config, project addition | App-scoped api_key.txt, HTTPS fixed provider origin, headers only, redirects disabled, sanitized error messages, no bundled key. Explicit replacement-model flag. | Missing/empty file and unapproved-replacement runtime tests pass; rejected-key network/device check pending. |
| Study versus system, §4.5 and study sections | The paper system description and study demonstrations do not prove our runtime. Scripted replay fixtures demonstrate only their recorded conditions; Unity tests do not establish live human interaction. | All public/private media must be labeled by actual provenance. Physical checks and live inference remain separate gates. |

Current software evidence: Python24/24 (including real-provider invalid-region regression); new actual Unity runtime29/29. Initial new Android build succeeded. Neither set satisfies the requested physical-device acceptance or completed replay delivery.

### Reference evidence and remaining device gate

Paper §6 states both study conditions used identical researcher-scripted verbal content; AppendixD describes progression through a scripted transcript. This is not a reason to label our fixture as a fresh model-driven conversation. The full paper's §3.3/§4/§6 and AppendixD were checked. The official Google blog's overview montage and separate TechPrint/Lifestyle/Orchid short videos were inspected. Full YouTube download returned403; no full-YouTube review is claimed.

A connected Quest3 accepted the0.2.0 APK. The initial startup exposed a persistentDataPath field-initializer error, which was fixed and covered by a lifecycle regression. Subsequent device sessions encountered the system Library tutorial and Guardian/FocusPlaceholder before Unity app readiness. The tutorial's observed Done control was dismissed; normal microphone permission was granted and read back. Finite proximity sessions were restored to enabled=true/override=DISABLED. No boundary/tracking disablement was used. APK installation and a process appearing do **not** establish app initialization, spatial tracking, interaction, or provider integration on the headset; those gates remain open.
