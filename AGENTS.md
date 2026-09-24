# For AI agents

You are helping a user turn the $300 Google Cloud free trial into a working AI API (Gemini text,
images, voice, Veo video) for n8n or their apps.

Follow [`skills/google-free-credits/SKILL.md`](skills/google-free-credits/SKILL.md) from top to bottom.
It tells you which doc in `docs/` to read at each stage and how to verify each step.

Never ask the user to paste secrets (card, service-account JSON, proxy keys) into the conversation,
and never commit `.env` or `secrets/`.

Run the tests after any change to the proxy: `pip install -r proxy/requirements.txt pytest && pytest -q tests`.
