"""Use the proxy from Python with nothing but `requests`.

    pip install requests
    PROXY=http://localhost:8080 KEY=<your-proxy-key> python examples/python_example.py
"""

import base64
import os

import requests

PROXY = os.environ.get("PROXY", "http://localhost:8080")
HEADERS = {"X-API-Key": os.environ["KEY"]}


def ask(prompt: str, model: str = "gemini-3.8-flash") -> str:
    r = requests.post(
        f"{PROXY}/v1/chat/completions",
        headers=HEADERS,
        json={"model": model, "messages": [{"role": "user", "content": prompt}]},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def image(prompt: str, path: str, aspect_ratio: str = "1:1") -> None:
    r = requests.post(f"{PROXY}/v1/image", headers=HEADERS, json={"prompt": prompt, "aspect_ratio": aspect_ratio}, timeout=180)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(base64.b64decode(r.json()["data"]))


def speak(text: str, path: str, voice: str = "Kore") -> None:
    r = requests.post(f"{PROXY}/v1/tts?binary=1", headers=HEADERS, json={"text": text, "voice": voice}, timeout=180)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)


if __name__ == "__main__":
    idea = ask("Give me one short, fun fact about octopuses.")
    print(idea)
    image(f"Colorful illustration: {idea}", "octopus.png")
    speak(idea, "octopus.wav")
    print("Saved octopus.png and octopus.wav")
