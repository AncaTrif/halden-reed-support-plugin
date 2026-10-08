#!/usr/bin/env python3
"""PreToolUse hook: deny by default for Slack and Zoho Desk tools.

A plugin cannot ship permission deny lists, so this hook carries the same rule:
any tool from a server whose name contains "slack" or "zoho" must be on the
allowlist below, otherwise the call is blocked (exit 2). Other servers, such as
the orders server, are not touched. Fails closed if the input cannot be read.
"""
import json
import sys

ALLOWED = {
    "slack": {"slack_search_channels", "slack_send_message", "slack_read_channel", "slack_read_thread"},
    "zoho": {"ZohoDesk_getTicket", "ZohoDesk_getTickets", "ZohoDesk_searchTickets",
             "ZohoDesk_getTicketConversations", "ZohoDesk_getContact"},
}


def decide(tool_name: str):
    """Return a reason string if the call must be blocked, else None."""
    parts = tool_name.split("__", 2)
    if len(parts) != 3 or parts[0] != "mcp":
        return None
    server, tool = parts[1].lower(), parts[2]
    for key, allowed in ALLOWED.items():
        if key in server and tool not in allowed:
            return (f"{tool_name} is not on the allowlist for {key}. This desk only reads and "
                    f"drafts. Allowed {key} tools: {', '.join(sorted(allowed))}.")
    return None


def main() -> int:
    try:
        name = json.load(sys.stdin).get("tool_name", "")
    except Exception:
        print("Blocked: could not read hook input, failing closed.", file=sys.stderr)
        return 2
    reason = decide(name)
    if reason:
        print("Blocked: " + reason, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
