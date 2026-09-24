# Step 1. Claim the $300 free trial

Time: 5 minutes. Cost: $0.

## What you get

| | |
|---|---|
| Credit | **$300**, usable on most Google Cloud products, including Vertex AI (Gemini, Imagen, Veo, TTS) |
| Duration | **90 days** from sign-up, or until the $300 is spent, whichever comes first |
| Who | Anyone who has **never** been a paying customer of Google Cloud, Google Maps Platform or Firebase, and never had the free trial before |
| Surprise bills | None. During the trial Google **does not charge you**. When the credit or the 90 days run out, the trial simply stops |

Official page: <https://cloud.google.com/free/docs/free-cloud-features>

## Sign up

1. Open **<https://console.cloud.google.com/freetrial>** with the Google account you want to use.
   Tip: use a dedicated Gmail address for this, it keeps billing and access separate from your personal account.
2. Choose your country, accept the terms.
3. **Add a payment method** (credit or debit card). It is mandatory, even though you will not be charged.
   - Google places a **temporary authorization** of $0 to $1 on the card to check it is real.
     It is not a charge. It disappears after 1 to 14 business days depending on your bank.
   - In some countries Google also asks you to verify your bank account.
   - Virtual or prepaid cards are sometimes refused. Use a regular card if that happens.

   > **Heads-up: you may be asked for a small prepayment.** Some accounts are asked to add about
   > **$10 / 10 EUR** to the billing account before the trial activates (it happened to us). It is not in
   > Google's official terms, so not everyone sees it. If you do, it is a prepayment credited to your account,
   > not a fee.
4. Click **Start free**. The $300 is valid for **90 days** from this moment. You land in the Google Cloud Console with a **Billing account** that holds
   your $300 credit, and usually a first project called "My First Project".

## Check it worked

Console, menu **Billing** then **Credits**: you should see the Free Trial credit with about $300 remaining
and the expiry date. Write that date down.

## Good to know before you start

- **The credit pays for Vertex AI, not for Google AI Studio.** Google says it plainly: *"The $300 credit
  can't pay for Gemini API in AI Studio costs."* An API key from aistudio.google.com draws on a separate
  quota and billing. That is exactly why this repo goes through **Vertex AI**.
- **Third-party models are excluded.** Claude, Llama, Mistral and other partner models sold on Vertex's
  Model Garden as managed APIs cannot be paid with the credit. Google's own models (Gemini, Imagen, Veo,
  Gemini TTS, Chirp) can.
- **Trial limits:** no GPUs on virtual machines, no quota increase requests. The default quotas are enough
  for personal projects and automations, but image generation is limited to a few images per minute.
  See [troubleshooting](08-troubleshooting.md) for how the proxy deals with it.
- **Upgrading to a paid account is optional.** If you upgrade, the remaining credit stays usable until the
  original 90-day date, and after that you pay normally. See [When the credit runs out](09-when-credits-run-out.md).

Next: [Step 2. Set up Vertex AI](02-google-cloud-setup.md)
