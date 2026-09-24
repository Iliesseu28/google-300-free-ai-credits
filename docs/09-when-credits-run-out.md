# When the credit runs out

The free trial ends at whichever comes first: **$300 spent** or **90 days** after sign-up.

## What happens

- Nothing is charged. Google does not switch you to paid by itself.
- Calls through the proxy start failing (403 on billing).
- Your resources are kept for **30 days** of grace, then deleted if you don't upgrade.

## Your two options

**1. Upgrade to a paid account** (Billing, **Activate full account**)

- Any credit left is kept, but must still be used before the original 90-day date.
- After that, you pay Vertex AI prices normally. For light personal use (text only) that is often a
  few dollars a month.
- Before upgrading, **create a budget with alerts** (Billing, Budgets & alerts), for example $10 per
  month with alerts at 50%, 90% and 100%. Note: a budget alerts you, it does not stop spending by itself.
- Nothing to change in the proxy: same project, same service account.

**2. Stop there**

Remove the proxy keys from your apps and shut the container down. Nothing else to do.

## About creating a new account every 90 days

The trial is for new customers only: Google's terms say you are eligible if you have *never* been a paying
customer and *never* had the free trial. Opening accounts in a loop to get more credit breaks those terms
and can get accounts closed. This repo does not help with that. If the proxy is useful to you after 90
days, upgrading and setting a budget is the clean path.

## Other Google programs worth knowing

- **Google for Startups Cloud Program**: much larger credits for eligible startups.
- **Gemini API free tier** on Google AI Studio: a small free quota for text, separate from the $300,
  with different data terms (free-tier prompts may be used to improve Google products).

Check the current conditions on Google's pages: they change often.
