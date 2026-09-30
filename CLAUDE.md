# Project conventions for Claude Code

This repo builds the Halden & Reed Escalation Desk plugin. Read README.md for the build order.

## Ground rules

- All data is fictional. Never add real customer names, emails, addresses or order numbers. Use the example domains `example.com` and `example.org`.
- Nothing customer-facing is ever sent automatically. Drafts and internal notes only. A human presses send.
- Personal data stays out of logs and Slack posts. Use ticket IDs and order IDs, not names, in escalation messages.
- Policy text lives in `policy/` (added in step 6) and is changed by pull request only.
- One build step per branch and per pull request. Commit messages say what was found or decided, not only what changed.

## Style

- Plain text files, markdown with YAML front matter for tickets and skills.
- No em dashes in written text.
- Tickets may be in German, English or both. Keep the customer's original language in the ticket body.

## Markets and owners

- Markets: DE, UK, US
- Owners (Slack channels): Product Quality, Legal and GDPR, Finance, Comms, Tier 2 Queue

## Ticket IDs

`HR-1001` to `HR-1012`. Expected outcomes live in `evals/expected.yaml`.
