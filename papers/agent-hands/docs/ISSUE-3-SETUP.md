# Issue 3: direct provider configuration and acceptance

This branch is work in progress, not a completed or physically accepted release.

## Model availability and approval

Authenticated Models API check (2026-11-12 UTC): `gemini-2.5-flash-exp` returned 404; `gemini-2.5-flash-preview-tts` returned 200; proposed replacement `gemini-2.5-flash` returned 200. The exact TTS model also returned real PCM audio in an operator smoke test. Availability to one operator key does not guarantee access for every collaborator.

The original response ID remains the default. No automatic fallback is implemented. Issue #3 requests approval for the response replacement. Until approved, full new live response generation is blocked; no claim of model equivalence is made.

## Headset files

Package: `org.prlab.agenthands`. Build 0.2.0/versionCode3. After installing/launching once, place your own local key file using:

```sh
adb -s YOUR_SERIAL shell mkdir -p /sdcard/Android/data/org.prlab.agenthands/files
adb -s YOUR_SERIAL push /YOUR/PRIVATE/api_key.txt /sdcard/Android/data/org.prlab.agenthands/files/api_key.txt
```

Never paste a key into a command argument, Issue, PR, screenshot or recording. The contents are one API key, with optional trailing newline. This is Android app-scoped external storage, **not hardware-backed secret storage**: trusted ADB/device operators can access it. Delete the file when handing the headset to an untrusted user. Do not put credentials into source/assets or rebuild the APK with a key.

Optional `models.json` in the same directory selects explicit model IDs. Only after approval of the replacement in Issue #3, a collaborator may configure:

```json
{"responseModel":"gemini-2.5-flash","ttsModel":"gemini-2.5-flash-preview-tts","approvedReplacement":true}
```

The boolean records the user's explicit configuration; it is not an authorization service. Without it, replacement IDs are rejected. No provider key is bundled. Missing/empty/invalid files show actionable messages; provider HTTP401/403 shows rejection, HTTP404 shows model unavailable. Relaunch after editing. A missing `api_key.txt` with no `server.json` selects direct mode and shows setup instructions. An existing explicit `server.json` retains the legacy LAN backend, unless a key file selects direct mode.

In **direct mode**, WAV microphone input and the permitted object registry go over TLS to the fixed `generativelanguage.googleapis.com` origin. The key is in a request header, never the URL; redirects are disabled. Responses are parsed locally and only stripped speech is sent to TTS. Keys are not forwarded to the LAN backend, written to debug output, or logged. Exact copies of the key in provider text are redacted before display. Real-room audio sent to Google is a provider data disclosure inherent to this selected mode; use only authorized inputs. This does not upload raw recordings to public GitHub.

Controls: right A hold/release registers a spoken object label at controller position; right trigger asks; left X toggles the world-space debug panel. The native direct parser currently covers the prompted subset, not the full Python semantic-region implementation. Unsupported events raise an error; unresolved target IDs remain visible in diagnostics and are not animated.

## Reproduction and verification

Build commands remain in the paper README. Run real Unity behavioral checks separately:

```sh
AGENT_HANDS_ACCEPTANCE=/private/output/runtime-acceptance.json \
  /path/to/Unity -batchmode -quit -projectPath "$PWD/unity" \
  -buildTarget StandaloneOSX -executeMethod AgentAcceptance.Run \
  -logFile /private/output/acceptance.log
```

Run the three permitted recordings without modifying originals, with the actual remote project path:

```sh
.venv/bin/python scripts/render_replays.py /private/copied-sessions \
  --host YOUR_UNITY_HOST --project /YOUR/UNITY/PROJECT --full-timeline
```

The full timeline includes the recorded question, a disclosed held-view thinking interval, response, and a held-view idle tail. These are replay fixtures, not evidence of network latency or fresh live inference. Existing fixtures retain original Qwen/macOS-speech provenance until new approved-model inference is performed. The side-by-side debug panel shows original tagged text, active parsed events, and the heuristic current word. Camera holds are labeled.

## Physical test checklist (not satisfied by compilation)

1. Launch with missing/empty key and verify the actionable text, persistent orb and two hands. Record current APK hash and device identity.
2. Place your own key; with an approved available model, register a real object and ask a fresh question. Confirm no key in logs or debug video.
3. Show idle before the question, thinking, speech/gesture, return to idle; toggle X and capture readable raw tags/parsed active events.
4. Verify tracking and registration under head translation, rotation, look-away/return; inspect real hand interaction rather than simulating contact.
5. Quit/relaunch, verify setup/error recovery; use ordinary Wi-Fi without ADB reverse. Transport, install/launch, provider inference, spatial alignment, and interaction are separate checks.

## Recorded-replay provider selection

The existing local GPU/macOS-speech path remains explicitly available as `AGENT_HANDS_PROVIDER=local`. To use the paper's provider for fresh recorded responses, configure your own operator credential outside Git:

```sh
export AGENT_HANDS_PROVIDER=gemini
export AGENT_HANDS_API_KEY_FILE=/YOUR/PRIVATE/operator-key.txt
export AGENT_HANDS_RESPONSE_MODEL=gemini-2.5-flash-exp
export AGENT_HANDS_TTS_MODEL=gemini-2.5-flash-preview-tts
```

The exact response ID currently returns404 for the operator. **Only after replacement approval**, explicitly select `AGENT_HANDS_RESPONSE_MODEL=gemini-2.5-flash` and `AGENT_HANDS_APPROVED_REPLACEMENT=true`. Environment selection applies to `generate_replays.py`, `refine_responses.py`, dialogue generation, perception/registration and TTS. No provider/model fallback is silent. `AGENT_HANDS_API_KEY` may instead be injected securely by your credential manager; never paste its value into commands, logs or Git. Native Quest `models.json` is separate from these operator environment variables.

For interactive hand contact, the project now pins official **XR Hands1.10.0** and enables its OpenXR Hand Tracking Subsystem. Tracked palm joint positions are transformed through the same XR Origin as the camera/controller. Untracked hands return no contact, not a fabricated controller hand. Turn on the debug panel while holding controllers, then put controllers down and acquire actual hand tracking for the contact test; record its left/right availability flags. Compilation/provider configuration is not proof of physical tracking.
