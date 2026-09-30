# Slack setup for the test workspace

Goal: a test workspace with one channel per owner, and a Slack MCP server connected to Claude Code that can read channels and post messages.

## 1. Channels

Create these public channels in your test workspace:

| Channel | Owner |
|---|---|
| `#hr-tier2-queue` | Tier 2 agents, default destination |
| `#hr-product-quality` | Safety and hygiene cases |
| `#hr-legal-gdpr` | Data requests, legal threats |
| `#hr-finance` | Chargebacks, refunds above threshold |
| `#hr-comms` | Press and social media |

## 2. Posting capability

The Slack tools visible so far in Claude sessions cover reading channels, history and users. Before building the `/triage-ticket` command (step 3), confirm that the Slack MCP server you connect to Claude Code has a tool for posting a message. If it does not:

- Option A: use a different Slack MCP server that includes posting.
- Option B: add a small posting tool to your own MCP server (you will write one in step 5 anyway).

## 3. Connect from the CLI

1. Create or choose a Slack app in your test workspace with the scopes the chosen MCP server documents (typically channel read, history, and `chat:write` for posting).
2. Install the app to the workspace and invite it to the five channels above.
3. Register the server with Claude Code, following the server's own README for the command and token. Keep the token in an environment variable or `.env`, never in the repo.
4. Start Claude Code in this repo and run `/mcp` to confirm the server shows as connected.

## 4. Check

Ask Claude Code to list the channels and read the last message in `#hr-tier2-queue`. If that works, step 1 is done on the Slack side. Posting is verified in step 3.

## Notes for the write-up

Record what you had to decide here (which server, which scopes, why). Those decisions are portfolio material.
