#!/usr/bin/env bash
# Calls every route of the proxy once. Total cost: about $0.30 (mostly the 4-second video).
# Usage: PROXY=http://localhost:8080 KEY=<your-proxy-key> ./examples/curl.sh
set -euo pipefail
: "${PROXY:?set PROXY, e.g. http://localhost:8080}" "${KEY:?set KEY to your proxy key}"
mkdir -p out
H=(-H "X-API-Key: $KEY" -H "Content-Type: application/json")

echo "1/5 health";  curl -fsS "$PROXY/health"; echo

echo "2/5 chat"
curl -fsS "$PROXY/v1/chat/completions" "${H[@]}" \
  -d '{"model":"gemini-3.8-flash","messages":[{"role":"user","content":"Say hello in five words"}]}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"

echo "3/5 image -> out/image.png"
curl -fsS "$PROXY/v1/image?binary=1" "${H[@]}" \
  -d '{"prompt":"Flat illustration of a small robot holding a gold coin","aspect_ratio":"1:1"}' -o out/image.png

echo "4/5 voice -> out/voice.wav"
curl -fsS "$PROXY/v1/tts?binary=1" "${H[@]}" \
  -d '{"text":"Your three hundred dollars are ready.","voice":"Kore"}' -o out/voice.wav

echo "5/5 video (30 s to 3 min) -> out/video.mp4"
curl -fsS "$PROXY/v1/video" "${H[@]}" --max-time 600 \
  -d '{"prompt":"A slow cinematic drone shot over a turquoise mountain lake at sunrise","duration_seconds":4,"wait":true}' \
  | python3 -c "import sys,json,base64; v=json.load(sys.stdin)['videos'][0]; open('out/video.mp4','wb').write(base64.b64decode(v['data']))"

echo "Done. Open the out/ folder."
