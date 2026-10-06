#!/usr/bin/env python3
"""PreToolUse hook: block tools that send mail to a customer.

Reads the hook JSON from stdin. Exit 2 blocks the call and shows stderr to
Claude. Drafting stays allowed. Fails closed if the input cannot be read.
"""
import json
import sys

SEND_TOOLS = {
    "mcp__claude_ai_Gmail__send_message",
    "mcp__claude_ai_Gmail__reply",
    "mcp__claude_ai_Gmail__forward",
}


def main() -> int:
    try:
        tool = json.load(sys.stdin).get("tool_name", "")
    except Exception:
        print("Blocked: could not read hook input, failing closed.", file=sys.stderr)
        return 2
    if tool in SEND_TOOLS:
        print(
            f"Blocked: {tool} would send mail to a customer. Nothing customer-facing "
            "is sent automatically. Create a draft or an internal note and let a human send it.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
