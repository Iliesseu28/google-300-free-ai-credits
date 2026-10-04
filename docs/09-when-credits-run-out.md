# When the credit runs out

The free trial ends at whichever comes first: **$300 spent** or **90 days** after sign-up.

## What happens if you stayed on the trial

- Nothing is charged. Google does not upgrade you by itself: per its terms, the trial ends when you upgrade
  manually or when the trial billing account closes.
- Calls through the proxy start failing (403 on billing).
- Your resources are kept for **30 days** of grace, then deleted if you don't upgrade.

## What happens if the account was upgraded, even by accident

Then nothing stops. When the credit is used up, every call is billed to your card at normal prices.

It happened to us. The account became a paid one in the middle of the trial (one click on an **Activate**
button, while we still believed we were on the trial), the daily image workflows emptied the credit, and
Google billed about **90 EUR** over the next weeks before we noticed.

- **How to check:** **Billing**, **Overview**. A free trial account shows the trial and the days left. A paid
  account does not. The "Real bill" budget from [step 2](02-google-cloud-setup.md#set-a-budget-alert-now)
  emails you as soon as your card starts paying.
- **Stop spending at once:** unlink the project from billing (`gcloud billing projects unlink $PROJECT`, or
  Billing, **Account management**, disable billing on the project). Every call fails from then on.
- **Ask for a refund:** Billing, **Help with billing**, ask for a one-time adjustment and explain it was a
  mistake. It is a request, not a right.

## Your two options

**1. Upgrade to a paid account** (Billing, **Activate full account**)

- Any credit left is kept, but must still be used before the original 90-day date.
- After that, you pay Vertex AI prices normally. For light personal use (text only) that is often a
  few dollars a month.
- Keep the budgets from [step 2](02-google-cloud-setup.md#set-a-budget-alert-now) and raise the "Real bill"
  amount to what you accept to pay, for example $10 per month. A budget alerts you, it does not stop spending:
  when the alert comes, check the usage, and unlink billing if it is not expected.
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
