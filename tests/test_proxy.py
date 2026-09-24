"""Proxy tests against a fake Vertex AI: no Google account, no network, no cost."""

import base64
import importlib
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "proxy"))

KEY = "test-key-123"


class FakeResponse:
    def __init__(self, status, data):
        self.status_code = status
        self._data = data
        self.text = str(data)
        self.headers = {"Content-Type": "application/json"}

    def json(self):
        return self._data

    def iter_content(self, chunk_size=None):
        yield b"data: {}\n\n"


@pytest.fixture
def proxy(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "demo-project")
    monkeypatch.setenv("PROXY_API_KEYS", f"other,{KEY}")
    monkeypatch.setenv("MAX_RETRIES", "2")
    import app as module

    module = importlib.reload(module)
    module.calls = []
    module.replies = []
    monkeypatch.setattr(module.time, "sleep", lambda s: None)

    def fake_post(url, body, stream=False):
        module.calls.append((url, body))
        return module.replies.pop(0)

    monkeypatch.setattr(module, "http_post", fake_post)
    return module


@pytest.fixture
def client(proxy):
    return proxy.app.test_client()


H = {"X-API-Key": KEY}


def test_health_needs_no_key(client):
    assert client.get("/health").json == {"status": "ok", "project_configured": True}


def test_rejects_missing_and_wrong_key(client):
    assert client.get("/v1/models").status_code == 401
    assert client.get("/v1/models", headers={"X-API-Key": "nope"}).status_code == 401


def test_accepts_bearer_key(client):
    r = client.get("/v1/models", headers={"Authorization": f"Bearer {KEY}"})
    assert r.status_code == 200
    assert any(m["id"] == "gemini-3.8-flash" for m in r.json["data"])


def test_refuses_to_run_without_keys(monkeypatch, proxy):
    monkeypatch.setattr(proxy, "API_KEYS", [])
    assert proxy.app.test_client().get("/v1/models").status_code == 500


def test_gemini_passthrough_uses_global_and_adds_role(proxy, client):
    proxy.replies.append(FakeResponse(200, {"candidates": [{"content": {"parts": [{"text": "OK"}]}}]}))
    r = client.post("/v1/gemini/gemini-3.8-flash", json={"contents": [{"parts": [{"text": "hi"}]}]}, headers=H)
    assert r.status_code == 200
    url, body = proxy.calls[0]
    assert url == (
        "https://aiplatform.googleapis.com/v1/projects/demo-project/locations/global"
        "/publishers/google/models/gemini-3.8-flash:generateContent"
    )
    assert body["contents"][0]["role"] == "user"


def test_retries_on_429_then_succeeds(proxy, client):
    proxy.replies += [FakeResponse(429, {"error": {}}), FakeResponse(200, {"ok": True})]
    r = client.post("/v1/gemini/gemini-3.8-flash", json={"contents": []}, headers=H)
    assert r.status_code == 200 and len(proxy.calls) == 2


def test_gives_up_after_max_retries(proxy, client):
    proxy.replies += [FakeResponse(429, {"error": {"code": 429}}) for _ in range(3)]
    r = client.post("/v1/gemini/gemini-3.8-flash", json={"contents": []}, headers=H)
    assert r.status_code == 429 and len(proxy.calls) == 3


def test_chat_completions_prefixes_google(proxy, client):
    proxy.replies.append(FakeResponse(200, {"choices": [{"message": {"content": "OK"}}]}))
    r = client.post("/v1/chat/completions", json={"model": "gemini-3.8-flash", "messages": []}, headers=H)
    assert r.status_code == 200
    url, body = proxy.calls[0]
    assert url.endswith("/locations/global/endpoints/openapi/chat/completions")
    assert body["model"] == "google/gemini-3.8-flash"


def test_image_gemini_reads_inline_data_both_spellings(proxy, client):
    png = base64.b64encode(b"PNGDATA").decode()
    for key in ("inlineData", "inline_data"):
        proxy.replies.append(
            FakeResponse(200, {"candidates": [{"content": {"parts": [{key: {"mimeType": "image/png", "data": png}}]}}]})
        )
        r = client.post("/v1/image", json={"prompt": "a cat"}, headers=H)
        assert r.status_code == 200 and r.json["data"] == png


def test_image_binary_mode(proxy, client):
    png = base64.b64encode(b"PNGDATA").decode()
    proxy.replies.append(
        FakeResponse(200, {"candidates": [{"content": {"parts": [{"inlineData": {"mimeType": "image/png", "data": png}}]}}]})
    )
    r = client.post("/v1/image?binary=1", json={"prompt": "a cat"}, headers=H)
    assert r.data == b"PNGDATA" and r.mimetype == "image/png"


def test_image_200_without_image_is_422(proxy, client):
    proxy.replies.append(FakeResponse(200, {"candidates": [{"finishReason": "SAFETY"}]}))
    r = client.post("/v1/image", json={"prompt": "x"}, headers=H)
    assert r.status_code == 422 and r.json["error"]["finish_reason"] == "SAFETY"


def test_imagen_goes_regional_predict(proxy, client):
    proxy.replies.append(FakeResponse(200, {"predictions": [{"bytesBase64Encoded": "QQ==", "mimeType": "image/png"}]}))
    r = client.post("/v1/image", json={"prompt": "x", "model": "imagen-4.0-fast-generate-001"}, headers=H)
    assert r.status_code == 200
    assert "us-central1-aiplatform.googleapis.com" in proxy.calls[0][0] and proxy.calls[0][0].endswith(":predict")


def test_tts_wraps_pcm_in_wav(proxy, client):
    pcm = base64.b64encode(b"\x00\x00" * 100).decode()
    proxy.replies.append(
        FakeResponse(
            200, {"candidates": [{"content": {"parts": [{"inlineData": {"mimeType": "audio/L16;codec=pcm;rate=24000", "data": pcm}}]}}]}
        )
    )
    r = client.post("/v1/tts?binary=1", json={"text": "Hello"}, headers=H)
    assert r.status_code == 200 and r.data[:4] == b"RIFF" and r.mimetype == "audio/wav"
    assert "us-central1" in proxy.calls[0][0]


def test_required_fields(client):
    for path in ("/v1/image", "/v1/tts", "/v1/video"):
        assert client.post(path, json={}, headers=H).status_code == 400


def test_video_start_and_status(proxy, client):
    op = "projects/demo-project/locations/us-central1/publishers/google/models/veo-3.1-lite-generate-001/operations/abc"
    proxy.replies.append(FakeResponse(200, {"name": op}))
    r = client.post("/v1/video", json={"prompt": "a drone shot", "duration_seconds": 4}, headers=H)
    assert r.status_code == 202 and r.json["operation"] == op
    assert proxy.calls[0][0].endswith("veo-3.1-lite-generate-001:predictLongRunning")
    assert proxy.calls[0][1]["parameters"]["durationSeconds"] == 4

    proxy.replies.append(
        FakeResponse(200, {"name": op, "done": True, "response": {"videos": [{"bytesBase64Encoded": "TVA0", "mimeType": "video/mp4"}]}})
    )
    r = client.post("/v1/video/status", json={"operation": op}, headers=H)
    assert r.json["done"] is True and r.json["videos"][0]["data"] == "TVA0"
    assert proxy.calls[1][0].endswith("veo-3.1-lite-generate-001:fetchPredictOperation")


def test_video_wait_polls_until_done(proxy, client):
    op = "projects/demo-project/locations/us-central1/publishers/google/models/veo-3.1-fast-generate-001/operations/x"
    proxy.replies += [
        FakeResponse(200, {"name": op}),
        FakeResponse(200, {"name": op, "done": False}),
        FakeResponse(200, {"name": op, "done": True, "response": {"videos": [{"gcsUri": "gs://b/v.mp4"}]}}),
    ]
    r = client.post("/v1/video", json={"prompt": "x", "model": "veo-3.1-fast-generate-001", "wait": True}, headers=H)
    assert r.status_code == 200 and r.json["videos"][0]["gcs_uri"] == "gs://b/v.mp4"


def test_video_status_rejects_unknown_operation(client):
    assert client.post("/v1/video/status", json={"operation": "nope"}, headers=H).status_code == 400
