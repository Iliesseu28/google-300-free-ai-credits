# Step 2. Set up Vertex AI and a service account

Time: 10 minutes. Two ways to do the same thing: **clicks in the Console** or **5 commands with gcloud**.
Pick one.

What you create:

```
Billing account ($300 credit)
   └── Project  (e.g. my-ai-credits-123456)
         ├── Vertex AI API  (aiplatform.googleapis.com), enabled
         └── Service account  vertex-proxy@<project>.iam.gserviceaccount.com
               └── role "Vertex AI User"  (roles/aiplatform.user)
               └── JSON key  (only if the proxy runs outside Google Cloud)
```

A **service account** is a robot identity. The proxy logs in to Google with it, so you never put your
personal Google login on a server. The **Vertex AI User** role lets it call models and nothing else:
it cannot delete your project, read your files or change billing.

## Option A. In the Console (no install)

1. **Create a project.** Top bar, project picker, **New project**. Name it `my-ai-credits`.
   Note the **Project ID** Google shows under the name (for example `my-ai-credits-123456`).
   You need the ID, not the name.
2. **Link billing.** Menu **Billing**, **Link a billing account**, choose the one with the Free Trial.
   (New projects are often linked automatically. Check anyway: without billing, every call fails.)
3. **Enable the Vertex AI API.** Open
   <https://console.cloud.google.com/apis/library/aiplatform.googleapis.com>, check the project name in
   the top bar, click **Enable**. Wait about 1 minute.
4. **Create the service account.** Menu **IAM & Admin**, **Service Accounts**, **Create service account**.
   - Name: `vertex-proxy`
   - Role: search **Vertex AI User**, select it, **Continue**, **Done**.
5. **Create a key** (skip if you deploy on Cloud Run, see below). Click the new service account,
   tab **Keys**, **Add key**, **Create new key**, **JSON**. A file downloads.
   - Rename it `service-account.json` and put it in a `secrets/` folder next to this repo.
   - Treat it like a password. Never commit it, never paste it in a chat or a public place.
     The repo's `.gitignore` already excludes `secrets/`.

Some organizations block key creation (policy `iam.disableServiceAccountKeyCreation`). A personal free-trial
account normally does not. If you hit it, use Option C.

## Option B. With gcloud (5 commands)

Install the Google Cloud CLI: <https://cloud.google.com/sdk/docs/install>. Then:

```bash
gcloud auth login
gcloud billing accounts list                # note the ACCOUNT_ID of the Free Trial billing account

export PROJECT=my-ai-credits-$RANDOM
gcloud projects create $PROJECT --name="My AI credits"
gcloud billing projects link $PROJECT --billing-account=<ACCOUNT_ID>
gcloud services enable aiplatform.googleapis.com --project=$PROJECT

gcloud iam service-accounts create vertex-proxy --display-name="Vertex proxy" --project=$PROJECT
gcloud projects add-iam-policy-binding $PROJECT \
  --member="serviceAccount:vertex-proxy@$PROJECT.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user" --condition=None

mkdir -p secrets
gcloud iam service-accounts keys create secrets/service-account.json \
  --iam-account=vertex-proxy@$PROJECT.iam.gserviceaccount.com
echo "Your project id: $PROJECT"
```

## Option C. No key at all

Keys are the easiest path, but you can skip them:

- **On your own computer:** `gcloud auth application-default login`. The proxy picks up your login
  automatically (Application Default Credentials).
- **On Cloud Run:** deploy with `--service-account vertex-proxy@$PROJECT.iam.gserviceaccount.com`.
  Google injects the identity, no file to manage. See [Step 3](03-run-the-proxy.md#option-3-google-cloud-run).

## Test before going further

With gcloud installed, one call proves the whole chain (billing, API, permissions):

```bash
export PROJECT=<your-project-id>   # already set if you followed Option B
curl -s -X POST \
  "https://aiplatform.googleapis.com/v1/projects/$PROJECT/locations/global/publishers/google/models/gemini-3.8-flash:generateContent" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"role":"user","parts":[{"text":"Say OK"}]}]}'
```

A JSON answer with `"text": "OK"` means you are ready. An error? See [troubleshooting](08-troubleshooting.md).

Note: a brand new key or role can take about a minute to work. A 401 or 403 in the first minute is normal.

Next: [Step 3. Run the proxy](03-run-the-proxy.md)
