"""vertex-proxy: one small HTTP server that turns Google Cloud credits into AI endpoints.

Text (Gemini), images (Gemini image / Imagen), voice (Gemini TTS) and video (Veo),
all billed to your Google Cloud project, so the $300 free-trial credit pays for them.

Callers (n8n, apps, scripts) send a proxy key. Only this server holds Google credentials.
"""

from __future__ import annotations

import base64
import hmac
import io
import os
import re
import threading
import time
import wave

import google.auth
import google.auth.transport.requests
import requests
from flask import Flask, Response, jsonify, request

# ---------------------------------------------------------------------------
# Configuration (environment variables, see .env.example)
# ---------------------------------------------------------------------------

PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip()
API_KEYS = [k.strip() for k in os.environ.get("PROXY_API_KEYS", "").split(",") if k.strip()]

# Gemini 3.x text and image models only answer on the "global" location.
TEXT_LOCATION = os.environ.get("TEXT_LOCATION", "global")
# Veo, Imagen and TTS models live in regional locations.
MEDIA_LOCATION = os.environ.get("MEDIA_LOCATION", "us-central1")

DEFAULT_TEXT_MODEL = os.environ.get("DEFAULT_TEXT_MODEL", "gemini-3.8-flash")
DEFAULT_IMAGE_MODEL = os.environ.get("DEFAULT_IMAGE_MODEL", "gemini-3.1-flash-image")
DEFAULT_TTS_MODEL = os.environ.get("DEFAULT_TTS_MODEL", "gemini-2.5-flash-tts")
DEFAULT_VIDEO_MODEL = os.environ.get("DEFAULT_VIDEO_MODEL", "veo-3.1-lite-generate-001")

MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))
VIDEO_WAIT_SECONDS = int(os.environ.get("VIDEO_WAIT_SECONDS", "300"))
HTTP_TIMEOUT = int(os.environ.get("HTTP_TIMEOUT", "300"))

# Listed by GET /v1/models so OpenAI-style clients can discover something useful.
KNOWN_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.1-pro-preview",
    "gemini-3.1-flash-image",
    "gemini-3.1-flash-lite-image",
    "imagen-4.0-generate-001",
    "imagen-4.0-fast-generate-001",
    "gemini-2.5-flash-tts",
    "gemini-3.1-flash-tts-preview",
    "veo-3.1-lite-generate-001",
    "veo-3.1-fast-generate-001",
    "veo-3.1-generate-001",
]

SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Google credentials: a service-account key (GOOGLE_APPLICATION_CREDENTIALS)
# or Application Default Credentials (gcloud login, Cloud Run, a VM...).
# ---------------------------------------------------------------------------

_creds = None
_creds_lock = threading.Lock()


def google_token() -> str:
    global _creds, PROJECT
    with _creds_lock:
        if _creds is None:
            _creds, detected = google.auth.default(scopes=SCOPES)
            if not PROJECT and detected:
                PROJECT = detected
        if not _creds.valid:
            _creds.refresh(google.auth.transport.requests.Request())
        return _creds.token


def location_for(model: str) -> str:
    if "tts" in model or model.startswith(("veo", "imagen", "lyria")):
        return MEDIA_LOCATION
    return TEXT_LOCATION


def base_url(location: str) -> str:
    host = "aiplatform.googleapis.com" if location == "global" else f"{location}-aiplatform.googleapis.com"
    return f"https://{host}/v1/projects/{PROJECT}/locations/{location}"


def model_url(model: str, method: str) -> str:
    return f"{base_url(location_for(model))}/publishers/google/models/{model}:{method}"


def http_post(url: str, body: dict, stream: bool = False) -> requests.Response:
    """POST to Vertex AI. Kept as one function so tests can replace it."""
    return requests.post(
        url,
        json=body,
        headers={"Authorization": f"Bearer {google_token()}"},
        timeout=HTTP_TIMEOUT,
        stream=stream,
    )


def vertex(url: str, body: dict) -> tuple[int, dict]:
    """Call Vertex AI, retrying on 429 (quota) and 5xx with exponential backoff."""
    resp = None
    for attempt in range(MAX_RETRIES + 1):
        resp = http_post(url, body)
        if resp.status_code != 429 and resp.status_code < 500:
            break
        if attempt < MAX_RETRIES:
            time.sleep(2 ** (attempt + 1))
    try:
        data = resp.json()
    except ValueError:
        data = {"error": {"message": resp.text[:500]}}
    return resp.status_code, data


def error(status: int, message: str, **extra):
    return jsonify({"error": {"code": status, "message": message, **extra}}), status


def wants_binary() -> bool:
    return request.args.get("binary", "").lower() in ("1", "true", "yes")


# ---------------------------------------------------------------------------
# Caller authentication
# ---------------------------------------------------------------------------


@app.before_request
def check_api_key():
    if request.path == "/health":
        return None
    if not API_KEYS:
        return error(500, "PROXY_API_KEYS is empty: set at least one key before exposing the proxy.")
    given = request.headers.get("X-API-Key", "")
    auth = request.headers.get("Authorization", "")
    if not given and auth.lower().startswith("bearer "):
        given = auth[7:].strip()
    if not given or not any(hmac.compare_digest(given, k) for k in API_KEYS):
        return error(401, "Missing or invalid proxy key (X-API-Key or Authorization: Bearer).")
    return None


@app.get("/health")
def health():
    return jsonify({"status": "ok", "project_configured": bool(PROJECT)})


@app.get("/v1/models")
def list_models():
    return jsonify({"object": "list", "data": [{"id": m, "object": "model", "owned_by": "google"} for m in KNOWN_MODELS]})


# ---------------------------------------------------------------------------
# Text: raw Gemini passthrough + OpenAI-compatible chat
# ---------------------------------------------------------------------------


@app.post("/v1/gemini/<model>")
def gemini(model: str):
    """Send any Gemini generateContent body; get Vertex's answer back untouched."""
    body = request.get_json(silent=True) or {}
    for content in body.get("contents", []):
        content.setdefault("role", "user")
    status, data = vertex(model_url(model, "generateContent"), body)
    return jsonify(data), status


@app.post("/v1/chat/completions")
def chat_completions():
    """OpenAI-compatible chat, so any OpenAI SDK or tool can use Gemini."""
    body = request.get_json(silent=True) or {}
    model = body.get("model") or DEFAULT_TEXT_MODEL
    body["model"] = model if "/" in model else f"google/{model}"
    url = f"{base_url(TEXT_LOCATION)}/endpoints/openapi/chat/completions"
    if body.get("stream"):
        upstream = http_post(url, body, stream=True)
        return Response(
            upstream.iter_content(chunk_size=None),
            status=upstream.status_code,
            content_type=upstream.headers.get("Content-Type", "text/event-stream"),
        )
    status, data = vertex(url, body)
    return jsonify(data), status


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------


def first_inline_blob(data: dict):
    for cand in data.get("candidates", []):
        for part in (cand.get("content") or {}).get("parts", []):
            # Vertex answers with inlineData, some SDK paths with inline_data: read both.
            blob = part.get("inlineData") or part.get("inline_data")
            if blob and blob.get("data"):
                return blob.get("mimeType") or blob.get("mime_type") or "image/png", blob["data"]
    return None


@app.post("/v1/image")
def image():
    body = request.get_json(silent=True) or {}
    prompt = (body.get("prompt") or "").strip()
    if not prompt:
        return error(400, "Field 'prompt' is required.")
    model = body.get("model") or DEFAULT_IMAGE_MODEL
    aspect = body.get("aspect_ratio", "1:1")

    if model.startswith("imagen"):
        status, data = vertex(
            model_url(model, "predict"),
            {"instances": [{"prompt": prompt}], "parameters": {"sampleCount": 1, "aspectRatio": aspect}},
        )
        if status != 200:
            return jsonify(data), status
        preds = data.get("predictions") or []
        if not preds or not preds[0].get("bytesBase64Encoded"):
            return error(422, "No image returned (the prompt was probably filtered).")
        mime, b64 = preds[0].get("mimeType", "image/png"), preds[0]["bytesBase64Encoded"]
    else:
        status, data = vertex(
            model_url(model, "generateContent"),
            {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"responseModalities": ["TEXT", "IMAGE"], "imageConfig": {"aspectRatio": aspect}},
            },
        )
        if status != 200:
            return jsonify(data), status
        found = first_inline_blob(data)
        if not found:
            reason = next((c.get("finishReason") for c in data.get("candidates", [])), None)
            # A 200 with no image usually means a safety block: rephrase the prompt.
            return error(422, "No image returned. Rephrase the prompt.", finish_reason=reason)
        mime, b64 = found

    if wants_binary():
        return Response(base64.b64decode(b64), mimetype=mime)
    return jsonify({"model": model, "mime_type": mime, "data": b64})


# ---------------------------------------------------------------------------
# Voice (text to speech)
# ---------------------------------------------------------------------------


def pcm_to_wav(pcm: bytes, rate: int = 24000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
    return buf.getvalue()


@app.post("/v1/tts")
def tts():
    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").strip()
    if not text:
        return error(400, "Field 'text' is required.")
    model = body.get("model") or DEFAULT_TTS_MODEL
    voice = body.get("voice", "Kore")
    style = (body.get("style") or "").strip()
    spoken = f"{style}: {text}" if style else text

    status, data = vertex(
        model_url(model, "generateContent"),
        {
            "contents": [{"role": "user", "parts": [{"text": spoken}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
            },
        },
    )
    if status != 200:
        return jsonify(data), status
    found = first_inline_blob(data)
    if not found:
        return error(422, "No audio returned.")
    mime, b64 = found
    rate = int(m.group(1)) if (m := re.search(r"rate=(\d+)", mime)) else 24000
    wav = pcm_to_wav(base64.b64decode(b64), rate) if "L16" in mime or "pcm" in mime else base64.b64decode(b64)

    if wants_binary():
        return Response(wav, mimetype="audio/wav")
    return jsonify({"model": model, "voice": voice, "mime_type": "audio/wav", "data": base64.b64encode(wav).decode()})


# ---------------------------------------------------------------------------
# Video (Veo): long-running operations
# ---------------------------------------------------------------------------

OPERATION_RE = re.compile(r"projects/[^/]+/locations/([^/]+)/publishers/google/models/([^/]+)/operations/[^/]+$")


def video_result(op: dict) -> dict:
    out = {"operation": op.get("name"), "done": bool(op.get("done"))}
    if op.get("error"):
        out["error"] = op["error"]
    resp = op.get("response") or {}
    videos = []
    for v in resp.get("videos", []):
        item = {"mime_type": v.get("mimeType", "video/mp4")}
        if v.get("gcsUri"):
            item["gcs_uri"] = v["gcsUri"]
        if v.get("bytesBase64Encoded"):
            item["data"] = v["bytesBase64Encoded"]
        videos.append(item)
    if videos:
        out["videos"] = videos
    if resp.get("raiMediaFilteredCount"):
        out["filtered"] = resp["raiMediaFilteredCount"]
        out["filtered_reasons"] = resp.get("raiMediaFilteredReasons", [])
    return out


def poll_video(operation: str) -> tuple[int, dict]:
    match = OPERATION_RE.search(operation)
    if not match:
        return 400, {"error": {"message": "Unknown operation name."}}
    location, model = match.groups()
    url = f"{base_url(location)}/publishers/google/models/{model}:fetchPredictOperation"
    return vertex(url, {"operationName": operation})


@app.post("/v1/video")
def video():
    body = request.get_json(silent=True) or {}
    prompt = (body.get("prompt") or "").strip()
    if not prompt:
        return error(400, "Field 'prompt' is required.")
    model = body.get("model") or DEFAULT_VIDEO_MODEL

    instance = {"prompt": prompt}
    if body.get("image"):  # optional first frame, base64
        instance["image"] = {"bytesBase64Encoded": body["image"], "mimeType": body.get("image_mime_type", "image/png")}
    params = {
        "sampleCount": 1,
        "durationSeconds": int(body.get("duration_seconds", 8)),
        "aspectRatio": body.get("aspect_ratio", "16:9"),
        "resolution": body.get("resolution", "720p"),
        "generateAudio": bool(body.get("generate_audio", True)),
    }
    if body.get("negative_prompt"):
        params["negativePrompt"] = body["negative_prompt"]
    if body.get("storage_uri"):  # gs://bucket/folder/ : Veo writes the mp4 there instead of returning bytes
        params["storageUri"] = body["storage_uri"]

    status, data = vertex(model_url(model, "predictLongRunning"), {"instances": [instance], "parameters": params})
    if status != 200:
        return jsonify(data), status
    operation = data.get("name", "")

    if not body.get("wait"):
        return jsonify({"operation": operation, "done": False}), 202

    deadline = time.time() + VIDEO_WAIT_SECONDS
    while time.time() < deadline:
        time.sleep(10)
        status, op = poll_video(operation)
        if status != 200:
            return jsonify(op), status
        if op.get("done"):
            return jsonify(video_result(op))
    return jsonify({"operation": operation, "done": False, "hint": "Still rendering: poll /v1/video/status."}), 202


@app.post("/v1/video/status")
def video_status():
    body = request.get_json(silent=True) or {}
    operation = body.get("operation") or ""
    status, op = poll_video(operation)
    if status != 200:
        return jsonify(op), status
    return jsonify(video_result(op))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
