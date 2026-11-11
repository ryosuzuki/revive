# Model service

The development implementation uses `Qwen/Qwen3-VL-8B-Instruct` through the custom `POST /generate` protocol in `scripts/gpu_model_server.py` (not an OpenAI-compatible endpoint). Model weights are downloaded separately and are not repository assets.

```sh
python3 -m venv model-venv
model-venv/bin/pip install -r scripts/requirements-gpu.txt
model-venv/bin/hf download Qwen/Qwen3-VL-8B-Instruct
model-venv/bin/python scripts/gpu_model_server.py --host 127.0.0.1 --port 18441
```

Verify compatible CUDA/PyTorch hardware and available memory before loading the model. On shared machines, follow the machine owner's admission/lease procedure; do not stop unrelated jobs. The original development workload reserved 32 GiB; this is not a guarantee for arbitrary devices or prompts.

For a remote private worker, use your verified SSH route:

```sh
ssh -N -L 18441:127.0.0.1:18441 YOUR_GPU_SSH_ALIAS
```

Set `AGENT_HANDS_MODEL_URL=http://127.0.0.1:18441` on the dialogue host. `GET /health` verifies service readiness only; verify real image-conditioned inference separately. Do not expose this unauthenticated research model service publicly or place provider credentials in the APK.
