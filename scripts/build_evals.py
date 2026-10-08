#!/usr/bin/env python3
"""Generate the eval suite for `claude plugin eval` from one source of truth.

Reads evals/expected.yaml and tickets/*.md and writes:
  evals/mocks/zoho/ZohoDesk_searchTickets.md   one mock, answers from the fixtures
  evals/mocks/zoho/fixtures/HR-xxxx.json       one Zoho-shaped search result per ticket
  evals/triage-HR-xxxx/                        one triage case per ticket (prompt + graders)
Run: python3 scripts/build_evals.py   (add --check to fail if the files are out of date)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
LANG = {"en": "English", "de": "German"}


def kv(block):
    return {m.group(1): m.group(2).strip() for m in re.finditer(r"^\s*(?:- )?(\w+):[ \t]*(.*)$", block, re.M)}


def expected():
    text = (EVALS / "expected.yaml").read_text(encoding="utf-8")
    return [kv(c) for c in re.split(r"\n(?=- id:)", text) if "id: HR-" in c]


def tickets():
    for f in sorted((ROOT / "tickets").glob("HR-*.md")):
        _, head, body = f.read_text(encoding="utf-8").split("---", 2)
        yield {**kv(head), "body": body.strip()}


def fixture(t):
    name = re.sub(r"\(.*?\)", "", t["customer"]).strip()
    first, _, last = name.rpartition(" ")
    desc = (f"Market: {t['market']}\nLanguage: {t['language']}\nOrder: {t['order_id']}\n"
            f"Received: {t['received']}\nSource channel: {t['channel']}\n\n{t['body']}")
    one = {"id": "2482250000" + t["id"][-4:], "ticketNumber": str(int(t["id"][-4:]) - 900),
           "subject": f"[{t['id']}] {t['subject']}", "channel": "Email", "status": "Open",
           "language": LANG[t["language"]], "contactId": "9" + t["id"][-4:],
           "contact": {"firstName": first, "lastName": last or name, "email": t["customer_email"]},
           "description": desc}
    return {"status": "success", "data": {"data": [one], "count": 1}}


def grader(name, **fm):
    lines = ["---"] + [f"{k}: {v}" for k, v in fm.items()] + ["---", ""]
    return name, "\n".join(lines)


def case(e, t):
    cid, path = e["id"], f"cases/{e['id']}.md"
    target = f"{{ source: file, path: {path} }}"
    name_words = [w for w in re.split(r"[\s.,]+", re.sub(r"\(.*?\)", "", t["customer"])) if len(w) >= 3 and w.lower() not in {"dr", "mr", "mrs", "ms"}]
    graders = [
        grader("market", type="regex", target=target, pattern=f"'^market: {e['market']}$'", flags="m"),
        grader("risk-tier", type="regex", target=target, pattern=f"'^risk_tier: {e['risk_tier']}$'", flags="m"),
        grader("owner", type="regex", target=target, pattern=f"'^owner: {e['owner']}$'", flags="m"),
        grader("escalate", type="regex", target=target, pattern=f"'^escalate: {e['escalate']}$'", flags="m"),
        grader("no-email", type="regex", target=target, pattern="'[\\w.+-]+@[\\w-]+\\.\\w+'", match="not_contains"),
        grader("no-customer-name", type="regex", target=target, pattern="'\\b(" + "|".join(name_words) + ")\\b'", match="not_contains"),
        grader("read-ticket-from-zoho", type="tool_used", tool="mcp__zoho__ZohoDesk_searchTickets", min=1),
        grader("skill-fired", type="tool_used", tool="Skill", input_match="'\"skill\"\\s*:\\s*\"(?:[\\w-]+:)?triage\"'"),
    ]
    prompt = ("---\nmax_turns: 25\ntimeout_seconds: 300\ntags: [triage]\n"
              "allowed_tools: [Read, Glob, Grep, Skill, Agent]\n---\n\n"
              f"Please triage support ticket {cid} and prepare the case file.\n")
    return cid, prompt, graders


def build():
    files = {}
    files["evals/mocks/zoho/ZohoDesk_searchTickets.md"] = "{{file:fixtures/{input.query_params.subject}.json}}\n"
    tix = {t["id"]: t for t in tickets()}
    for tid, t in tix.items():
        files[f"evals/mocks/zoho/fixtures/{tid}.json"] = json.dumps(fixture(t), indent=2, ensure_ascii=False) + "\n"
    for e in expected():
        cid, prompt, graders = case(e, tix[e["id"]])
        files[f"evals/triage-{cid}/prompt.md"] = prompt
        for name, text in graders:
            files[f"evals/triage-{cid}/graders/{name}.md"] = text
    return files


if __name__ == "__main__":
    files, stale = build(), []
    for rel, text in files.items():
        p = ROOT / rel
        if "--check" in sys.argv:
            if not p.exists() or p.read_text(encoding="utf-8") != text:
                stale.append(rel)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
    if "--check" in sys.argv:
        print("out of date:", *stale, sep="\n  ") if stale else print("eval files are up to date")
        sys.exit(1 if stale else 0)
    print(f"wrote {len(files)} files")
