## OpenClaw Media Gen

Generate images and videos using the AIsa API:

- **Gemini Image**: `gemini-3-pro-image-preview` (`/v1/models/{model}:generateContent`)
- **Wan 2.6 Video**: `wan2.6-t2v` (`/apis/v1/services/aigc/...` async task + polling)

API documentation index: [`https://docs.aisa.one/reference/`](https://docs.aisa.one/reference/)

### Quick Start

```bash
export AISA_API_KEY="your-key"
```

### Generate Image

```bash
python scripts/media_gen_client.py image \
  --prompt "A cute red panda, cinematic lighting" \
  --out out.png
```

### Generate Video (Create Task + Polling)

```bash
python scripts/media_gen_client.py video-create \
  --prompt "cinematic close-up, slow push-in" \
  --img-url "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/320px-Cat03.jpg" \
  --duration 5

python scripts/media_gen_client.py video-wait \
  --task-id <task_id> \
  --poll 10 \
  --timeout 600
```

### Auto-download Generated Video (mp4)

```bash
python scripts/media_gen_client.py video-wait \
  --task-id <task_id> \
  --download \
  --out out.mp4
```
