# Zoho Desk (step 7)

The 12 tickets live in Zoho Desk (free edition, EU data center). Triage, drafting and review read them through Zoho's own hosted MCP server. Nothing is written back to Zoho.

## How tickets are stored

The free plan has no custom fields and no CSV import, so each ticket was created through the API with:

- the ticket ID at the start of the subject: `[HR-1007] Doppelt abgebucht...`
- a header block at the top of the description, ended by a blank line: `Market`, `Language`, `Order`, `Received`, `Source channel`
- the customer's message after the blank line

Zoho sets `createdTime` itself and cannot backdate it, so the Received line is the received date. `scripts/zoho_seed.py` created the tickets and skips any that exist. It needs a Zoho API client with create scope, which was deleted after seeding. `tickets/*.md` stays as the seed fixture and as the name list for the Slack redaction hook.

## The MCP server

A server in the Zoho MCP console exposes only five read tools: `getTicket`, `getTickets`, `searchTickets`, `getTicketConversations`, `getContact`. In Claude Code they appear as `mcp__zoho__ZohoDesk_<name>`. Authorization type is "Authorization on Demand".

`.claude/settings.json` allows the five read tools and denies 25 write tools (send, update, delete, create, bulk). Zoho's catalogue has hundreds of tools, so the console selection and the deny list are two layers. The send hook also blocks `ZohoDesk_sendReply`.

## Connect it

The server URL contains a key. Keep it out of git and out of chat. Add it at local scope, from a separate terminal:

```
claude mcp add --transport http zoho "<server URL>" --scope local
```

Then run `/mcp` in Claude Code and confirm `zoho` is connected with five tools. Do not paste the output of `claude mcp list` or `claude mcp get zoho` anywhere, because they can print the URL.

## Secrets

- The server URL key is the only secret still needed. It can be regenerated on the Connect page of the Zoho MCP console, which invalidates the old URL.
- The API client secret and both refresh tokens used for seeding were deleted from `.env` afterwards. Delete the self client in the Zoho API console as well.

## Known gaps

- A vendor server returns the customer's email address, so the drafter and reviewer can see it. The Slack hook still stops it from being posted.
- The Slack hook reads customer names from `tickets/*.md`. With real tickets only in Zoho it would need another source.
- Agent and command files are loaded when Claude Code starts, so changes to them can need a restart.
- Zoho search by subject is a wildcard search. The agents pick the result whose subject starts with `[<ID>]`.
