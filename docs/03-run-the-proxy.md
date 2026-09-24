# Step 3. Run the proxy

The proxy is one Python file, [`proxy/app.py`](../proxy/app.py) (about 400 lines, 4 dependencies).
It holds the Google credentials. Your apps and n8n only get a **proxy key** that you choose and can
revoke at any time.

```
 n8n / your app / a script
        │  X-API-Key: <proxy key>
        ▼
   vertex-proxy  ──(service account)──►  Vertex AI  ──►  billed to your $300 credit
```

## Configure

```bash
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(32))"   # generate a proxy key
```

Edit `.env`:

| Variable | Value |
|---|---|
| `GOOGLE_CLOUD_PROJECT` | your project **ID** from step 2 |
| `PROXY_API_KEYS` | the key you just generated. Several apps? One key each, comma-separated, so you can revoke one without touching the others |

The proxy refuses every request while `PROXY_API_KEYS` is empty: it will never run open by accident.

## Option 1. On your computer (to try it)

```bash
python3 -m venv .venv
.venv/bin/pip install -r proxy/requirements.txt
export $(grep -v '^#' .env | xargs)
export GOOGLE_APPLICATION_CREDENTIALS=$PWD/secrets/service-account.json   # or: gcloud auth application-default login
.venv/bin/python proxy/app.py
```

The proxy listens on <http://localhost:8080>. Check: `curl localhost:8080/health`.

## Option 2. Docker (a VPS, a home server, next to n8n)

```bash
docker compose up -d --build
```

[`docker-compose.yml`](../docker-compose.yml) mounts `secrets/service-account.json` read-only, runs as a
non-root user, and publishes the port on `127.0.0.1` only.

**Same server as n8n?** Put both on the same Docker network and call `http://vertex-proxy:8080` from n8n:
nothing is exposed to the internet at all. This is the setup we use in production.

```yaml
# add to docker-compose.yml
networks:
  default:
    name: n8n_default     # the network of your n8n stack
    external: true
```

**Need it from the internet** (a mobile app, a site on another host)? Put a reverse proxy with HTTPS in
front (Caddy, Traefik, Coolify, nginx). Never expose plain HTTP: the proxy key would travel in clear.
Minimal Caddyfile:

```
ai.example.com {
    reverse_proxy 127.0.0.1:8080
}
```

## Option 3. Google Cloud Run

Serverless, HTTPS included, no key file (Google injects the service account). Cloud Run itself is billed
to the same credit, and a personal proxy costs cents.

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project=$PROJECT

gcloud run deploy vertex-proxy --source proxy --project=$PROJECT --region=us-central1 \
  --service-account=vertex-proxy@$PROJECT.iam.gserviceaccount.com \
  --set-env-vars=GOOGLE_CLOUD_PROJECT=$PROJECT,PROXY_API_KEYS=<your-proxy-key> \
  --timeout=600 --allow-unauthenticated
```

Several proxy keys? Commas break `--set-env-vars`: change the separator with
`--set-env-vars=^@^GOOGLE_CLOUD_PROJECT=$PROJECT@PROXY_API_KEYS=key1,key2`.

`--allow-unauthenticated` lets requests reach the proxy, which then checks the proxy key itself.
For a stricter setup, store the key in Secret Manager and pass it with `--set-secrets`.

## Smoke test

```bash
export PROXY=http://localhost:8080 KEY=<your-proxy-key>

curl -s $PROXY/v1/chat/completions -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model":"gemini-3.8-flash","messages":[{"role":"user","content":"Say OK"}]}'
```

Or run all five capabilities at once: [`examples/curl.sh`](../examples/curl.sh).

Next: [Step 4. Use it from anything](04-use-it.md)
