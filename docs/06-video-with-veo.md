# Step 6. Video with Veo

Veo turns a sentence (and optionally a first image) into a video clip **with sound**: ambience, effects,
even dialogue. It is the most expensive thing you can do with the credit, and the most impressive.

<p align="center"><img src="assets/veo-sample.gif" alt="4-second Veo 3.1 Lite clip: drone shot over a mountain lake at sunrise" width="480"><br>
<em>Made through this proxy with one request: "A slow cinematic drone shot over a turquoise mountain lake at sunrise", 4 s, Veo 3.1 Lite. About $0.20.</em></p>

## Pick a model

| Model | Quality | Price with audio, 720p (Sept. 2026) | 8 s clip | Clips for $300 |
|---|---|---|---|---|
| `veo-3.1-lite-generate-001` (default) | Good, fast | $0.05 / s | $0.40 | ~750 |
| `veo-3.1-fast-generate-001` | Very good | $0.10 / s | $0.80 | ~375 |
| `veo-3.1-generate-001` | Best | $0.40 / s | $3.20 | ~93 |

Prices from the [Vertex AI pricing page](https://cloud.google.com/vertex-ai/generative-ai/pricing).
Check it before a big batch: Google changes them.

## One request, wait for the result

```bash
curl -s $PROXY/v1/video -H "X-API-Key: $KEY" -H "Content-Type: application/json" -d '{
  "prompt": "A slow cinematic drone shot over a turquoise mountain lake at sunrise",
  "duration_seconds": 4,
  "wait": true
}' | python3 -c "import sys,json,base64; v=json.load(sys.stdin)['videos'][0]; open('clip.mp4','wb').write(base64.b64decode(v['data']))"
```

Rendering takes 30 seconds to 3 minutes. With `"wait": true` the proxy polls for you, up to
`VIDEO_WAIT_SECONDS` (300 by default).

## Two steps (n8n, apps, long clips)

```bash
# 1. start: returns {"operation": "projects/.../operations/...", "done": false} with HTTP 202
curl -s $PROXY/v1/video -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"prompt": "A cat surfing a wave, slow motion", "aspect_ratio": "9:16"}'

# 2. poll every 10-15 s until "done": true
curl -s $PROXY/v1/video/status -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"operation": "<operation from step 1>"}'
```

## Options

| Field | Default | Notes |
|---|---|---|
| `prompt` | required | Describe subject, action, camera, light, sound. Quotes in the prompt become dialogue |
| `model` | `veo-3.1-lite-generate-001` | see table above |
| `duration_seconds` | `8` | `4`, `6` or `8` |
| `aspect_ratio` | `16:9` | `9:16` for Reels, Shorts, TikTok |
| `resolution` | `720p` | `1080p` costs more on Lite and Fast |
| `generate_audio` | `true` | `false` for silent clips |
| `negative_prompt` | none | what to avoid: "text, watermark, blur" |
| `image` | none | base64 PNG or JPEG used as **first frame** (image to video). Pair it with `/v1/image` |
| `storage_uri` | none | `gs://your-bucket/videos/`: Veo writes the MP4 there and returns `gcs_uri` instead of the bytes. Useful for many or long clips |

## Image to video in two calls

```bash
IMG=$(curl -s $PROXY/v1/image -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"prompt":"A red paper boat on a puddle, city at night, neon reflections","aspect_ratio":"16:9"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data'])")

curl -s $PROXY/v1/video -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{\"prompt\":\"The boat slowly drifts away, rain starts\",\"image\":\"$IMG\",\"wait\":true}" > video.json
```

## When no video comes back

The answer has `"done": true` but no `videos`, and a `filtered` count: Veo's safety filter blocked it.
Real people, celebrities, brands and violence are the usual triggers. Rephrase.
