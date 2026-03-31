---
name: openclaw-media-gen
description: "Generate images & videos with AIsa. Gemini 3 Pro Image (image) + Qwen Wan 2.6 (video) via one API key."
homepage: https://openclaw.ai
metadata: {"openclaw":{"emoji":"🎬","requires":{"bins":["python3","curl"],"env":["AISA_API_KEY"]},"primaryEnv":"AISA_API_KEY"}}
---

# OpenClaw Media Gen 🎬

Generate **images** and **videos** with a single AIsa API key:

- **Image**: `gemini-3-pro-image-preview` (Gemini GenerateContent)
- **Video**: `wan2.6-t2v` (Qwen Wan 2.6, async task)

API documentation index: [AIsa API Reference](https://docs.aisa.one/reference/) (all pages can be found at `https://docs.aisa.one/llms.txt`).

## 🔥 What You Can Do

### Image Generation (Gemini)
```
"Generate a cyberpunk-style city nightscape with neon lights, rainy night, cinematic feel"
```

### Video Generation (Wan 2.6)
```
"Generate a 5-second shot from a reference image: slow camera push-in, wind blowing through hair, cinematic feel, shallow depth of field"
```

## Quick Start

```bash
export AISA_API_KEY="your-key"
```

---

## 🖼️ Image Generation (Gemini)

### Endpoint

- Base URL: `https://api.aisa.one/v1`
- `POST /models/{model}:generateContent`

Documentation: `google-gemini-chat` (GenerateContent) at `https://docs.aisa.one/reference/generatecontent`.

### curl Example (response contains inline_data for images)

```bash
curl -X POST "https://api.aisa.one/v1/models/gemini-3-pro-image-preview:generateContent" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents":[
      {"role":"user","parts":[{"text":"A cute red panda, ultra-detailed, cinematic lighting"}]}
    ]
  }'
```

> Note: The response from this endpoint may include `candidates[].parts[].inline_data` (typically containing base64 data and a MIME type); the client script will automatically parse and save the file.

---

## 🎞️ Video Generation (Qwen Wan 2.6 / Tongyi Wanxiang)

### Create task

- Base URL: `https://api.aisa.one/apis/v1`
- `POST /services/aigc/video-generation/video-synthesis`
- Header: `X-DashScope-Async: enable` (required, async)

Documentation: `video-generation` at `https://docs.aisa.one/reference/post_services-aigc-video-generation-video-synthesis`.

```bash
curl -X POST "https://api.aisa.one/apis/v1/services/aigc/video-generation/video-synthesis" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -H "X-DashScope-Async: enable" \
  -d '{
    "model":"wan2.6-t2v",
    "input":{
      "prompt":"cinematic close-up, slow push-in, shallow depth of field",
      "img_url":"https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/320px-Cat03.jpg"
    },
    "parameters":{
      "resolution":"720P",
      "duration":5,
      "shot_type":"single",
      "watermark":false
    }
  }'
```

### Poll task

- `GET /services/aigc/tasks?task_id=...`

Documentation: `task` at `https://docs.aisa.one/reference/get_services-aigc-tasks`.

```bash
curl "https://api.aisa.one/apis/v1/services/aigc/tasks?task_id=YOUR_TASK_ID" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

## Python Client

```bash
# Generate image (save to local file)
python3 {baseDir}/scripts/media_gen_client.py image \
  --prompt "A cute red panda, cinematic lighting" \
  --out "out.png"

# Create video task (requires img_url)
python3 {baseDir}/scripts/media_gen_client.py video-create \
  --prompt "cinematic close-up, slow push-in" \
  --img-url "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/320px-Cat03.jpg" \
  --duration 5

# Poll task status
python3 {baseDir}/scripts/media_gen_client.py video-status --task-id YOUR_TASK_ID

# Wait until success (optional: print video_url on success)
python3 {baseDir}/scripts/media_gen_client.py video-wait --task-id YOUR_TASK_ID --poll 10 --timeout 600

# Wait until success and auto-download mp4
python3 {baseDir}/scripts/media_gen_client.py video-wait --task-id YOUR_TASK_ID --download --out out.mp4
```
