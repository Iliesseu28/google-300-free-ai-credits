# Troubleshooting

Every entry below happened to us in production, with the fix that worked.

| Symptom | Cause | Fix |
|---|---|---|
| **404** `Publisher model ... was not found` | Wrong location. Gemini 3.x text and image models only exist on `global`. Veo, Imagen and TTS live in regions (`us-central1`) | Keep the defaults: `TEXT_LOCATION=global`, `MEDIA_LOCATION=us-central1`. The proxy routes each model for you |
| **404** on a model name you read somewhere | The name does not exist (preview names change, `-preview` suffixes disappear) | Test names with the curl in [step 2](02-google-cloud-setup.md#test-before-going-further). Don't guess: the list in [prices](07-models-and-prices.md) was tested |
| **403** `aiplatform.endpoints.predict` denied | Missing role, API not enabled, or gcloud logged in with another Google account | Check the service account has **Vertex AI User** on the right project. On your computer: `gcloud config get-value account` |
| **401 / 403 right after creating a key** | IAM changes take up to a minute to spread | Wait 60 s, retry |
| **403** `billing` / `BILLING_DISABLED` | Project not linked to the billing account with the credit | Console, Billing, link the project |
| **429** `RESOURCE_EXHAUSTED` | Free-trial quotas are low, especially for images (a few per minute) | The proxy retries 3 times with backoff. For batches: one request at a time, 20 s between images, never two batches in parallel on the same project |
| **429 that never stops** | Quota for the day or the minute is spent in that location | Switch model (`gemini-3.1-flash-lite-image` has its own quota) or wait. Quota increase requests are blocked during the trial |
| Image request returns **422**, `finish_reason: SAFETY` or no reason | Google answered 200 but without an image: the prompt was filtered. Surprising trigger: writing "no watermark" in the prompt | Rephrase. Describe what you want, not what you don't want |
| JSON output has **random key names** | No `responseSchema` given | Always send a `responseSchema`. No `$ref`, `oneOf`, `additionalProperties`: Vertex rejects them |
| Replies are **slow** | Gemini 3 thinks before answering | `"thinkingConfig": {"thinkingLevel": "low"}` for simple tasks |
| TTS returns **500** on `global` | TTS preview models are regional | Keep `MEDIA_LOCATION=us-central1` |
| Veo: `done: true` but **no video** | Safety filter (`filtered` count in the answer) | Avoid real people, brands, violence. Rephrase |
| n8n: **ECONNREFUSED** / `fetch failed` | n8n cannot reach the proxy | Same Docker network and `http://vertex-proxy:8080`, or `host.docker.internal`. From a container, `localhost` is the container itself |
| Proxy key rejected (**401**) | Key typo, or `PROXY_API_KEYS` changed without restart | Restart the container after editing `.env` |
| Worked yesterday, **403** today | Free trial ended (90 days or $300 spent) | See [When the credit runs out](09-when-credits-run-out.md) |

## Security checklist

- The service-account JSON key is a password. It lives in `secrets/`, which is git-ignored. If it ever leaks:
  Console, IAM, Service Accounts, Keys, **delete** it, create a new one.
- One proxy key per app or workflow. Revoke one by removing it from `PROXY_API_KEYS` and restarting.
- Never put the proxy key in a mobile app or a website's JavaScript. Call the proxy from a backend.
- Expose the proxy only behind HTTPS, or not at all (same Docker network as n8n).
- Set a **budget alert** (Billing, Budgets & alerts) even during the trial: it tells you how fast you burn
  the credit.
