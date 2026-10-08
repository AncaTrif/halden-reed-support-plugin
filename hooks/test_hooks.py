#!/usr/bin/env python3
"""Feed sample hook inputs to the two hooks. Run: python3 hooks/test_hooks.py"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIER2 = "C0C6SJ57FH6"
CLEAN = (
    "*HR-1007* | DE | standard | owner: tier2-queue\nOrder: HR-DE-77602\n"
    "Deadline: 2026-09-21 (customer asks for a refund within two working days)\n"
    "Flags: high-value-customer, needs-order-check\nCase file: cases/HR-1007.md"
)


def run(script, payload):
    p = subprocess.run(
        [sys.executable, str(HERE / script)],
        input=json.dumps(payload), capture_output=True, text=True,
    )
    return p.returncode, p.stderr


def slack(message, channel=TIER2):
    return {"tool_name": "mcp__slack__slack_send_message",
            "tool_input": {"channel_id": channel, "message": message}}


CASES = [
    ("send blocks gmail send_message", "block_customer_send.py", {"tool_name": "mcp__claude_ai_Gmail__send_message"}, 2),
    ("send blocks gmail reply", "block_customer_send.py", {"tool_name": "mcp__claude_ai_Gmail__reply"}, 2),
    ("send blocks gmail forward", "block_customer_send.py", {"tool_name": "mcp__claude_ai_Gmail__forward"}, 2),
    ("send blocks zoho sendReply", "block_customer_send.py", {"tool_name": "mcp__zoho__ZohoDesk_sendReply"}, 2),
    ("send allows zoho getTicket", "block_customer_send.py", {"tool_name": "mcp__zoho__ZohoDesk_getTicket"}, 0),
    ("send allows gmail create_draft", "block_customer_send.py", {"tool_name": "mcp__claude_ai_Gmail__create_draft"}, 0),
    ("send allows gmail search", "block_customer_send.py", {"tool_name": "mcp__claude_ai_Gmail__search_threads"}, 0),
    ("allowlist passes slack read_channel", "enforce_allowlist.py", {"tool_name": "mcp__slack__slack_read_channel"}, 0),
    ("allowlist passes slack send_message", "enforce_allowlist.py", {"tool_name": "mcp__slack__slack_send_message"}, 0),
    ("allowlist blocks slack draft tool", "enforce_allowlist.py", {"tool_name": "mcp__slack__slack_send_message_draft"}, 2),
    ("allowlist blocks slack canvas tool", "enforce_allowlist.py", {"tool_name": "mcp__slack__slack_create_canvas"}, 2),
    ("allowlist blocks claude.ai slack connector extras", "enforce_allowlist.py", {"tool_name": "mcp__claude_ai_Slack__slack_schedule_message"}, 2),
    ("allowlist passes zoho getTicket", "enforce_allowlist.py", {"tool_name": "mcp__zoho__ZohoDesk_getTicket"}, 0),
    ("allowlist blocks zoho updateTicket", "enforce_allowlist.py", {"tool_name": "mcp__zoho__ZohoDesk_updateTicket"}, 2),
    ("allowlist blocks zoho sendReply", "enforce_allowlist.py", {"tool_name": "mcp__zoho__ZohoDesk_sendReply"}, 2),
    ("allowlist ignores plugin orders server", "enforce_allowlist.py", {"tool_name": "mcp__plugin_halden-reed-desk_orders__get_order"}, 0),
    ("allowlist ignores orders server", "enforce_allowlist.py", {"tool_name": "mcp__orders__get_order"}, 0),
    ("allowlist ignores non-mcp tools", "enforce_allowlist.py", {"tool_name": "Read"}, 0),
    ("allowlist fails closed on bad input", "enforce_allowlist.py", None, 2),
    ("redact passes clean message", "redact_slack.py", slack(CLEAN), 0),
    ("redact blocks full name", "redact_slack.py", slack(CLEAN + "\nCustomer: Annika Brandt"), 2),
    ("redact blocks surname only", "redact_slack.py", slack(CLEAN + "\nask Brandt"), 2),
    ("redact blocks ticket email", "redact_slack.py", slack(CLEAN + "\nannika.brandt@example.org"), 2),
    ("redact blocks any email", "redact_slack.py", slack(CLEAN + "\nsomeone@example.com"), 2),
    ("redact blocks phone", "redact_slack.py", slack(CLEAN + "\ncall +44 20 7946 0958"), 2),
    ("redact blocks street", "redact_slack.py", slack(CLEAN + "\nship to 14 Mill Lane"), 2),
    ("redact blocks other channel", "redact_slack.py", slack(CLEAN, channel="C000000000"), 2),
    ("redact blocks DM user id", "redact_slack.py", slack(CLEAN, channel="U0BKW3QEBMJ"), 2),
    ("redact fails closed on bad input", "redact_slack.py", None, 2),
]

bad = 0
for name, script, payload, want in CASES:
    code, err = run(script, payload) if payload is not None else (
        subprocess.run([sys.executable, str(HERE / script)], input="not json",
                       capture_output=True, text=True).returncode, "")
    ok = code == want
    bad += not ok
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f" (exit {code}, wanted {want})"))
# The reason must not echo the personal data it found.
_, err = run("redact_slack.py", slack(CLEAN + "\nCustomer: Annika Brandt"))
leak = "Annika" in err or "Brandt" in err
bad += leak
print(("FAIL " if leak else "PASS ") + "redact reason does not echo the name")
print("problems:", bad)
sys.exit(1 if bad else 0)
