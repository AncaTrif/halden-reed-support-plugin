#!/usr/bin/env python3
"""Create the 12 fictional tickets in Zoho Desk (one-time seeding).

Dry run by default. The free plan has no custom fields, so the ticket ID goes in
the subject ([HR-1001] ...) and the metadata goes in a header block at the top of
the description (Market, Language, Order, Received). Tickets already in Zoho are
skipped, which needs the read token. Usage:

  .venv/bin/python scripts/zoho_seed.py                    # show the plan
  .venv/bin/python scripts/zoho_seed.py --apply --only HR-1011   # create one
  .venv/bin/python scripts/zoho_seed.py --apply            # create all missing
"""
import argparse
import re
import sys
from pathlib import Path

from zoho_client import ROOT, ZohoDesk, ZohoError

CHANNEL = {"email": "Email", "web form": "Web", "chat": "Chat", "phone transcript": "Phone"}


def parse(path: Path) -> dict:
    head, body = path.read_text(encoding="utf-8").split("---", 2)[1:]
    meta = dict(m.groups() for m in re.finditer(r"^(\w+):\s*(.*)$", head, re.MULTILINE))
    meta["body"] = body.strip()
    return meta


def contact(meta: dict) -> dict:
    name = re.sub(r"\(.*?\)", "", meta["customer"]).strip()
    first, _, last = name.rpartition(" ")
    return {"firstName": first, "lastName": last or name, "email": meta["customer_email"]}


def payload(meta: dict, department_id: str) -> dict:
    channel = next((v for k, v in CHANNEL.items() if meta["channel"].lower().startswith(k)), "Web")
    header = (f"Market: {meta['market']}\nLanguage: {meta['language']}\n"
              f"Order: {meta['order_id']}\nReceived: {meta['received']}\n"
              f"Source channel: {meta['channel']}\n\n")
    return {"subject": f"[{meta['id']}] {meta['subject']}", "departmentId": department_id,
            "contact": contact(meta), "channel": channel, "description": header + meta["body"]}


def existing_ids(read: ZohoDesk) -> set:
    found, start = set(), 0
    while True:
        data = read.request("GET", "/tickets", params={"from": start, "limit": 100}).get("data", [])
        found |= {m.group(1) for t in data if (m := re.match(r"\[(HR-\d{4})\]", t.get("subject", "")))}
        if len(data) < 100:
            return found
        start += 100


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only", help="seed a single ticket, e.g. HR-1011")
    args = ap.parse_args()

    tickets = [parse(p) for p in sorted((ROOT / "tickets").glob("HR-*.md"))]
    if args.only:
        tickets = [t for t in tickets if t["id"] == args.only]
        if not tickets:
            print(f"No ticket {args.only} in tickets/.")
            return 1

    if not args.apply:
        print(f"Dry run. Would create up to {len(tickets)} tickets in Zoho Desk:")
        for t in tickets:
            print(f"  [{t['id']}] {t['subject']}  (market {t['market']}, language {t['language']})")
        print("Nothing was sent. Add --apply to create them.")
        return 0

    try:
        done = existing_ids(ZohoDesk("ZOHO_REFRESH_TOKEN_READ"))
        seed = ZohoDesk("ZOHO_REFRESH_TOKEN_SEED")
        depts = seed.request("GET", "/departments").get("data", [])
        if not depts:
            print("No department found in Zoho Desk.")
            return 1
        dept = depts[0]["id"]
        for t in tickets:
            if t["id"] in done:
                print(f"skip   {t['id']} (already in Zoho)")
                continue
            created = seed.request("POST", "/tickets", json=payload(t, dept))
            print(f"created {t['id']} as Zoho ticket number {created.get('ticketNumber', '?')}")
    except ZohoError as exc:
        print(f"Stopped: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
