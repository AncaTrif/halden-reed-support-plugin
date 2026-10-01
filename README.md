# Halden & Reed Escalation Desk (Claude Code plugin)

A Claude Code plugin that prepares cases for Tier 2 support agents at a fictional consumer brand, Halden & Reed (about 2,000 employees, selling in Germany, the UK and the US). The agent receives a prepared case with risk tier, market rules, order facts, owner and a draft reply. A human always decides and sends.

All company, customer and order data in this repo is invented.

## Why this project exists

It is a portfolio build that shows, in one place:

- Claude Code as the build environment (CLI, GitHub, commits that tell the story)
- Skills, subagents, hooks and slash commands
- Several MCP servers working together (Slack first, a custom orders server and Zoho Desk later)
- Packaging as an installable plugin with a marketplace file
- Governance: policy changes by pull request, tested by an eval suite

## Build order

| Step | What gets built |
|---|---|
| 1 | Repo, Slack workspace and channels, Slack MCP connected, 12 seeded tickets as local files |
| 2 | Triage skill: risk tier, market and owner as a structured case file |
| 3 | `/triage-ticket` command that posts the case summary to the right Slack channel |
| 4 | Hooks: block customer-facing sends, redact personal data before posting |
| 5 | Custom orders MCP server |
| 6 | Drafter and reviewer subagents, market policy files (DE, UK, US) |
| 7 | Zoho Desk MCP replaces the local ticket files |
| 8 | Package as a plugin with a marketplace file, install in a clean directory |
| 9 | Eval harness and GitHub Action, policy changes by pull request |

## Repo layout (grows step by step)

```
tickets/        12 seeded tickets (markdown with front matter)
evals/          expected outcomes per ticket, used by the eval harness later
docs/           setup guides
CLAUDE.md       conventions Claude Code reads at session start
```

## Status

Step 1 done, pending pull request. Next: step 2, the triage skill.
