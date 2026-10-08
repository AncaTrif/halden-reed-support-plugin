# Install the Halden & Reed desk plugin (step 8)

The repo is both a plugin (`halden-reed-desk`) and a one-plugin marketplace (`halden-reed`). Nothing is published anywhere. A marketplace is a file in a git repo or a folder.

## What you need first

- Claude Code with plugin support.
- Python 3.10 or newer on the path (`python3.12`, for example). The orders MCP server needs it. The first start builds a private environment in `~/.cache/halden-reed-desk` and installs the MCP SDK, so it needs network access once.
- Your own Slack MCP server, named exactly `slack`, and your own Zoho Desk MCP server, named exactly `zoho`. The plugin cannot bundle them: they are your accounts, and the Zoho URL contains a key. See `docs/slack-setup.md` and `docs/zoho-desk.md`.
- Five Slack channels for the owners, and the tickets in Zoho Desk with the ID in the subject (`[HR-1001] ...`).

## Install

From a local folder, or from GitHub with `AncaTrif/halden-reed-support-plugin` in place of the path:

```
claude plugin marketplace add /path/to/halden-reed-support-plugin --scope local
claude plugin install halden-reed-desk@halden-reed --scope local
```

Or inside Claude Code: `/plugin marketplace add <path or repo>`, then `/plugin install halden-reed-desk@halden-reed`. Restart Claude Code afterwards. Scope `local` keeps it to the current project, `user` makes it global.

A marketplace name is global. Adding `halden-reed` from a new source (a branch, a fork, a local folder) re-points it for every project on your machine, and plugins already installed from it update from the new source. To go back, add the previous source again. For a branch, use `AncaTrif/halden-reed-support-plugin#<branch>`.

Commands and agents get the plugin name as a prefix:

| What | Name |
|---|---|
| Triage and post a summary | `/halden-reed-desk:triage-ticket HR-1001` |
| Draft and review a reply | `/halden-reed-desk:draft-reply HR-1001` |
| Subagents | `halden-reed-desk:drafter`, `halden-reed-desk:reviewer` |
| Orders tool | `mcp__plugin_halden-reed-desk_orders__get_order` |

## Do these after installing

1. **Slack channel IDs.** `hooks/slack_channels.json` holds the IDs of the author's test workspace. Replace them with your own five owner channels, or the redaction hook will block every post. A plugin update overwrites the file, so keep your own copy.
2. **Permissions.** A plugin cannot ship permission rules. Copy the `permissions` block of `.claude/settings.json` into your own project settings. The plugin's `enforce_allowlist` hook is a backstop that blocks any Slack or Zoho tool not on the allowlist, but the permission rules also add the prompt before every Slack post.
3. **Names for the customer check.** `hooks/redact_slack.py` reads customer names and emails from `tickets/*.md` (the fictional seed fixture). With real tickets only in Zoho it would need another source.

## What the plugin does not include

- The Slack and Zoho connections and their secrets.
- `CLAUDE.md`. Plugins do not load it as context, so `claude plugin validate` warns about it. The same rules are in `policy/general.md`, the agents and the hooks.
- Customer-facing sending of any kind. Drafts and internal notes only, a human sends.

## Remove

```
claude plugin uninstall halden-reed-desk@halden-reed --scope local
claude plugin marketplace remove halden-reed
rm -rf ~/.cache/halden-reed-desk
```
