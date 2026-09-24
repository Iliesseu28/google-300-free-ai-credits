# Step 4. Use it from anything

Every route except `/health` needs the proxy key, in `X-API-Key: <key>` or `Authorization: Bearer <key>`.

| Route | Does | Returns |
|---|---|---|
| `GET /health` | Is it alive? | `{"status":"ok","project_configured":true}` |
| `GET /v1/models` | Suggested models | OpenAI-style list |
| `POST /v1/chat/completions` | **OpenAI-compatible chat** with Gemini | OpenAI format, streaming supported |
| `POST /v1/gemini/<model>` | Raw Gemini `generateContent`: JSON mode, tools, images in input, everything | Vertex's JSON, untouched |
| `POST /v1/image` | Image from a prompt | `{mime_type, data}` (base64), or the PNG with `?binary=1` |
| `POST /v1/tts` | Voice from a text | `{mime_type, data}` (base64 WAV), or the WAV with `?binary=1` |
| `POST /v1/video` | Veo video from a prompt | `{operation}` (202), or the video with `"wait": true` |
| `POST /v1/video/status` | Poll a video | `{done, videos: [{data or gcs_uri}]}` |

Quota errors (429) and Google hiccups (5xx) are retried automatically with backoff (2 s, 4 s, 8 s).

## Chat: drop-in for OpenAI tools

Anything that speaks the OpenAI API works: set the **base URL** to `<proxy>/v1`, the **API key** to your
proxy key, the **model** to a Gemini name.

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8080/v1", api_key="<your-proxy-key>")
reply = client.chat.completions.create(
    model="gemini-3.8-flash",
    messages=[{"role": "user", "content": "Three name ideas for a coffee shop"}],
)
print(reply.choices[0].message.content)
```

That includes LangChain, LlamaIndex, Open WebUI, Continue, Cursor custom models, the n8n OpenAI node,
and most "bring your own OpenAI key" apps.

## Raw Gemini: structured JSON output

```bash
curl -s $PROXY/v1/gemini/gemini-3.8-flash -H "X-API-Key: $KEY" -H "Content-Type: application/json" -d '{
  "contents": [{"parts": [{"text": "Extract name and city: Maria lives in Lisbon"}]}],
  "generationConfig": {
    "responseMimeType": "application/json",
    "responseSchema": {"type": "OBJECT", "properties": {"name": {"type": "STRING"}, "city": {"type": "STRING"}}},
    "thinkingConfig": {"thinkingLevel": "low"}
  }
}'
```

Two tips that save money and bugs:

- **Always give a `responseSchema`** when you want JSON. Without it, the model invents key names now and then.
  Vertex accepts a subset of JSON Schema: no `$ref`, `oneOf` or `additionalProperties`.
- **`"thinkingLevel": "low"`** for simple tasks (extraction, classification, rewriting). Faster, fewer tokens.

## Image

```bash
curl -s "$PROXY/v1/image?binary=1" -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"prompt":"Flat illustration of a robot holding a gold coin","aspect_ratio":"1:1"}' -o robot.png
```

| Field | Default | Notes |
|---|---|---|
| `prompt` | required | |
| `model` | `gemini-3.1-flash-image` | or `gemini-3.1-flash-lite-image` (cheaper), `imagen-4.0-generate-001`, `imagen-4.0-fast-generate-001` |
| `aspect_ratio` | `1:1` | `16:9`, `9:16`, `4:3`, `3:4` |

A `422` means Google returned no image, almost always a safety filter. Rephrase the prompt.

## Voice

```bash
curl -s "$PROXY/v1/tts?binary=1" -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"text":"Welcome back! Here is your daily summary.","voice":"Kore","style":"Say cheerfully"}' -o hello.wav
```

| Field | Default | Notes |
|---|---|---|
| `text` | required | |
| `voice` | `Kore` | 30 prebuilt voices: `Puck`, `Charon`, `Fenrir`, `Aoede`, `Leda`, `Orus`, `Zephyr`, ... ([list](https://cloud.google.com/text-to-speech/docs/gemini-tts)) |
| `style` | none | plain-language direction: "Whisper", "Say it like a sports commentator" |
| `model` | `gemini-2.5-flash-tts` | or `gemini-3.1-flash-tts-preview` |

It speaks the language of the text, no setting needed.

## Video

See [Step 6. Video with Veo](06-video-with-veo.md).

## From code

- JavaScript (Node 18+, browser-free): [`examples/node_example.mjs`](../examples/node_example.mjs)
- Python: [`examples/python_example.py`](../examples/python_example.py)
- Shell, all routes: [`examples/curl.sh`](../examples/curl.sh)

**Mobile or web apps:** never ship the proxy key inside the app, anyone can extract it. Call the proxy
from your backend (a Cloud Function, an API route, an Edge Function), or give each user a short-lived
token of your own.

Next: [Step 5. Connect n8n](05-n8n.md)
