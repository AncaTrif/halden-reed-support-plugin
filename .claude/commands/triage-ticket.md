---
description: Triage one ticket and post a PII-free case summary to the owner's Slack channel. Add --dry-run to print the message without posting.
argument-hint: HR-xxxx [--dry-run]
---

Triage ticket `$ARGUMENTS`.

The first word is the ticket ID (`HR-1001` to `HR-1012`). If `--dry-run` is present, never call a Slack tool that sends. Nothing customer-facing is ever sent. This command posts internal summaries only, and a human approves every post.

## Steps

1. Check that `tickets/<ID>.md` exists. If not, stop and say so.
2. If `cases/<ID>.md` does not exist, run the `triage` skill for that ticket. If it exists, read it and use it as is. Do not re-triage unless the user asks.
3. Build the Slack summary from the case file front matter and the Constraints section, using this template:

   ```
   *<ID>* | <market> | <risk_tier> | owner: <owner>
   Order: <order_id>
   Deadline: <deadline> (<deadline_basis>)
   Flags: <flags>
   Linked: <linked_tickets>
   Reply must not: <one line summarising the main constraints>
   Case file: cases/<ID>.md
   ```

   Use `none` for empty fields. Use ticket IDs and order IDs only.

4. Personal data check (a hook in `hooks/redact_slack.py` also blocks the post if this check misses something). Read the `customer` and `customer_email` lines from the ticket front matter. The message must not contain the email, the customer's name or any part of it, or any address from the ticket body. If it does, remove it and check again. If you cannot remove it, stop and report.
5. Pick the channel by owner:

   | owner | channel |
   |---|---|
   | product-quality | `#hr-product-quality` |
   | legal-gdpr | `#hr-legal-gdpr` |
   | finance | `#hr-finance` |
   | comms | `#hr-comms` |
   | tier2-queue | `#hr-tier2-queue` |

   Routine and standard tickets owned by `tier2-queue` are posted too, so Tier 2 has one place to see everything. Find the channel ID with `slack_search_channels`.
6. If `secondary_owner` is not `none`, prepare a second, shorter message for that owner's channel:

   ```
   FYI *<ID>* | <risk_tier> | secondary owner: <secondary_owner>
   Primary owner: <owner> (#hr-<owner channel>)
   Deadline: <deadline>
   Why you are copied: <one line>
   ```

7. Show the user each message with its channel, exactly as it would be posted. In dry-run mode, stop here.
8. Otherwise post each message with `slack_send_message`. The permission prompt is the human approval, so do not try to get around it. If the user denies a post, do not retry it. Report which messages were posted and which were not.
9. Finish with one line: the ID, tier, owner, and which channels received a post.

## Never

- Never post names, emails, addresses or ticket text.
- Never post to a channel that is not in the table above.
- Never use any Slack tool other than `slack_search_channels` and `slack_send_message`. The others are denied in `.claude/settings.json`.
