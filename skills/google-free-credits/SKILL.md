---
name: google-free-credits
description: Take a user from zero to a working AI API paid by the $300 Google Cloud free trial. Covers the free-trial sign-up, the Vertex AI project and service account, deploying the vertex-proxy (local, Docker next to n8n, or Cloud Run), connecting n8n or an app, and generating text, images, voice and Veo video. Use when the user wants free Google AI credits, a Gemini or Veo API without an AI Studio key, a Vertex AI proxy, or to plug Gemini into n8n.
---

# Google $300 credit to a working AI API

You guide the user through five stages. The repo root (two folders above this file) contains the
proxy (`proxy/app.py`), the docs (`docs/01` to `docs/09`) and examples. Read the matching doc before
each stage: it has the exact clicks and commands.

Golden rules:

- **Never ask the user to paste a secret in the chat** (card numbers, the service-account JSON, proxy keys).
  Secrets go in files you create (`secrets/service-account.json`, `.env`), never in your messages or in git.
- **Payment and sign-up are the user's job.** You cannot and must not enter card details. Tell them what to
  click, wait for "done", then verify.
- **Verify each stage before the next one.** Each stage below ends with a check. Do not skip it.
- **Say what costs money** before running it. Text and images cost fractions of a cent; a Veo video costs
  $0.20 to $3.20.

## Stage 0. Find out where the user stands

Ask, in one message:
1. Has this Google account (or this person) ever used Google Cloud, Firebase or Google Maps billing before?
   If yes, the free trial is not available: explain it (docs/01) and offer to continue on a paid account.
2. Is `gcloud` installed? (`gcloud --version`). If not and they are fine installing it, prefer it:
   stage 2 becomes five commands. Otherwise use the Console path.
3. Where should the proxy run: this computer (to try), a server with Docker (often next to n8n), or
   Google Cloud Run?

## Stage 1. Free trial (user does it, you guide)

Read `docs/01-free-trial.md`. Give the user the link <https://console.cloud.google.com/freetrial> and the
three facts that reassure: a card is required, Google only places a $0 to $1 temporary authorization, and
nothing is charged during the trial.
Warn them that some accounts are asked for a ~$10 / 10 EUR prepayment before activation (not in
Google's official terms, but it happens), and that the credit expires 90 days after sign-up.

Check: the user sees about $300 under **Billing, Credits**. Ask them for the expiry date and remind them of it
at the end.

## Stage 2. Project, API, service account

Read `docs/02-google-cloud-setup.md`.

- With gcloud: run Option B's commands yourself, after `gcloud auth login` (the user completes the browser
  login). Pick a unique project id like `my-ai-credits-<random>`. Save the key to `secrets/service-account.json`
  inside the repo (git-ignored). Never print the key file.
- Without gcloud: walk the user through Option A one step at a time. Ask for the **project ID** (not secret)
  and ask them to move the downloaded JSON to `secrets/service-account.json` themselves.
- Cloud Run: no key needed (Option C).

Check: run the "Test before going further" curl from docs/02 (needs gcloud), or skip to the proxy
smoke test in stage 3. A 401/403 in the first minute after creating the key is normal: wait 60 s.

## Stage 3. Run the proxy

Read `docs/03-run-the-proxy.md`.

1. `cp .env.example .env`, set `GOOGLE_CLOUD_PROJECT`, generate a proxy key with
   `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` and write it to `PROXY_API_KEYS`
   directly in `.env` (do not echo it back in chat; tell the user where it is).
2. Start it the way the user chose (Option 1, 2 or 3).

Check: `curl <proxy>/health` answers `{"status":"ok","project_configured":true}`, then one chat call
through the proxy answers. Load the key from `.env` into a shell variable, do not print it.

## Stage 4. Connect what the user wants

- **n8n**: `docs/05-n8n.md`. Create the Header Auth credential (the user pastes the key into n8n themselves),
  or configure n8n's OpenAI credential with base URL `<proxy>/v1`. Offer to import `n8n/content-pipeline.json`.
- **An app or a script**: `docs/04-use-it.md` and `examples/`. For OpenAI-based code, only the base URL,
  the key and the model name change. For a mobile or web app, the proxy is called from the app's backend,
  never with the key shipped in the client.
- **Video**: `docs/06-video-with-veo.md`. Default to `veo-3.1-lite-generate-001`, 4 s, to test cheaply.

Check: one real output produced for the user's use case (a reply, a PNG, a WAV or an MP4 they can open).

## Stage 5. Wrap up

Tell the user, briefly:
- where the proxy runs and its URL, where `.env` and `secrets/` are (and that they must never be committed);
- the trial expiry date, and `docs/07-models-and-prices.md` for what the credit buys;
- to set a budget alert (Billing, Budgets & alerts);
- `docs/09-when-credits-run-out.md` for what happens after 90 days.

## When something fails

Go straight to `docs/08-troubleshooting.md`: 404 (wrong location or model name), 403 (role, API, billing,
wrong gcloud account), 429 (trial quotas, especially images), 422 on images (safety filter), empty Veo
result (safety filter). Model names are not guessable: only use names listed in docs/07, or test a name
with the curl from docs/02 before relying on it.
