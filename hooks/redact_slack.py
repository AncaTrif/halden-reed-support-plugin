#!/usr/bin/env python3
"""PreToolUse hook for slack_send_message: keep personal data out of Slack.

Blocks the post (exit 2) when the message
  - goes to a channel that is not one of the five owner channels,
  - contains a customer name or email taken from tickets/*.md,
  - contains any email address, phone number or street address pattern.

It blocks instead of rewriting, so the message a human approves is the message
that gets posted. The reason names the category and ticket ID, never the value.
Fails closed if the input or the ticket files cannot be read.
"""
import json
import re
import sys
from pathlib import Path

ALLOWED_CHANNELS = {
    "C0C6SJ82C8G": "#hr-product-quality",
    "C0C5SU0TV4M": "#hr-legal-gdpr",
    "C0C5SU29HS9": "#hr-finance",
    "C0C5Y340GQJ": "#hr-comms",
    "C0C6SJ57FH6": "#hr-tier2-queue",
}
TITLES = {"dr", "mr", "mrs", "ms", "prof"}
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE = re.compile(r"\+\d[\d ()-]{7,}\d|\(\d{2,5}\)\s?\d{3,}")
STREET = re.compile(
    r"\b\d{1,5}\s+[A-Z][\w'-]*(?:\s+[A-Z][\w'-]*)*\s+"
    r"(?:Lane|Street|St|Road|Rd|Avenue|Ave|Drive|Close|Way|Strasse|Straße)\b"
)


def customers(tickets_dir: Path):
    """Yield (ticket_id, name_tokens, email) for every ticket."""
    files = sorted(tickets_dir.glob("HR-*.md"))
    if not files:
        raise RuntimeError("no tickets found")
    for f in files:
        head = f.read_text(encoding="utf-8").split("---")[1]
        fields = dict(
            m.groups() for m in re.finditer(r"^(\w+):\s*(.*)$", head, re.MULTILINE)
        )
        name = re.sub(r"\(.*?\)", "", fields["customer"])
        tokens = [
            t for t in re.split(r"[\s.,]+", name)
            if len(t) >= 3 and t.lower() not in TITLES
        ]
        yield fields["id"], tokens, fields["customer_email"].lower()


def check(tool_input: dict, tickets_dir: Path) -> list:
    problems = []
    channel = tool_input.get("channel_id", "")
    if channel not in ALLOWED_CHANNELS:
        problems.append("channel is not one of the five owner channels")
    text = tool_input.get("message", "")
    low = text.lower()
    for tid, tokens, email in customers(tickets_dir):
        if email and email in low:
            problems.append(f"customer email from {tid}")
        for t in tokens:
            if re.search(rf"\b{re.escape(t)}\b", text):
                problems.append(f"customer name from {tid}")
                break
    if EMAIL.search(text):
        problems.append("an email address")
    if PHONE.search(text):
        problems.append("a phone number")
    if STREET.search(text):
        problems.append("a street address")
    return sorted(set(problems))


def main() -> int:
    try:
        data = json.load(sys.stdin)
        tickets = Path(__file__).resolve().parent.parent / "tickets"
        problems = check(data.get("tool_input", {}), tickets)
    except Exception as exc:
        print(f"Blocked: redaction check could not run ({type(exc).__name__}), failing closed.", file=sys.stderr)
        return 2
    if problems:
        print(
            "Blocked: the Slack post contains " + "; ".join(problems) + ". "
            "Use ticket IDs and order IDs only, remove the personal data and try again.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
