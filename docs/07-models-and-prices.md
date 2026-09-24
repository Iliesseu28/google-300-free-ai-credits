# What $300 buys

Prices from Google's official pages, checked on **September 24, 2026**:
[Vertex AI generative pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing) and
[Text-to-Speech pricing](https://cloud.google.com/text-to-speech/pricing). They change: check before a big run.

Every model below was called successfully through this proxy on a free-trial project the same day.

## Text

| Model | Good for | Input / output per 1M tokens | $300 is about |
|---|---|---|---|
| `gemini-3.8-flash` (default) | Almost everything: chat, agents, extraction, code | $0.75 / $3.75 (promo price until Dec 31, 2026, then $1.50 / $7.50) | 80M output tokens, or tens of thousands of chats |
| `gemini-3.7-flash` | Same family, previous version | see pricing page | |
| `gemini-3.1-flash-lite` | Huge volumes, classification, tagging | cheapest | |
| `gemini-3.1-pro-preview` | Hard reasoning, long documents | $2.00 / $12.00 (up to 200K context) | 25M output tokens |

A token is about 3/4 of an English word. A typical n8n step (1,000 tokens in, 300 out) costs about $0.002
with Gemini 3.8 Flash: **the credit covers more than 100,000 runs**.

## Images

| Model | Price per image (1K) | $300 is about |
|---|---|---|
| `gemini-3.1-flash-image` (default, "Nano Banana 2") | $0.067 | 4,400 images |
| `gemini-3.1-flash-lite-image` ("Nano Banana 2 Lite") | $0.034 | 8,800 images |
| `imagen-4.0-generate-001` | $0.04 | 7,500 images |
| `imagen-4.0-fast-generate-001` | $0.02 | 15,000 images |

Gemini image models follow instructions and edit well (text in images, keeping a character consistent).
Imagen is a pure text-to-image model, cheaper per image.

## Voice

| Model | Price | $300 is about |
|---|---|---|
| `gemini-2.5-flash-tts` (default) | $0.50 per 1M text tokens + $10 per 1M audio tokens (25 audio tokens = 1 s) | 300+ hours of speech |
| `gemini-3.1-flash-tts-preview` | $1 + $20 per 1M | 160+ hours |

## Video (with audio, 720p)

| Model | Per second | 8 s clip | $300 is about |
|---|---|---|---|
| `veo-3.1-lite-generate-001` (default) | $0.05 | $0.40 | 100 minutes of video |
| `veo-3.1-fast-generate-001` | $0.10 | $0.80 | 50 minutes |
| `veo-3.1-generate-001` | $0.40 | $3.20 | 12 minutes |

## A realistic month

| Use | Volume | Cost |
|---|---|---|
| n8n automations on Gemini 3.8 Flash | 20,000 runs | ~$40 |
| Blog and social images | 600 images | ~$40 |
| Voice-overs | 5 hours | ~$5 |
| Short videos for Reels / Shorts | 150 clips of 8 s on Lite | ~$60 |
| **Total** | | **~$145**, and $155 left |

## Models you cannot pay with the credit

Partner models sold as managed APIs in Model Garden (Anthropic Claude, Meta Llama API, Mistral...) are
excluded from the free trial credit. Everything in the tables above is a Google model and is covered.
