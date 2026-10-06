#!/usr/bin/env python3
"""Tests for the orders MCP server. Run: .venv/bin/python mcp_servers/orders/test_orders.py"""
import asyncio
import json
import re
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SERVER = HERE / "server.py"
failures = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f" ({detail})"))
    if not ok:
        failures.append(name)


def ticket_fields():
    for f in sorted((ROOT / "tickets").glob("HR-*.md")):
        head = f.read_text(encoding="utf-8").split("---")[1]
        yield dict(m.groups() for m in re.finditer(r"^(\w+):\s*(.*)$", head, re.MULTILINE))


def static_checks():
    raw = (HERE / "orders.json").read_text(encoding="utf-8")
    orders = {k: v for k, v in json.loads(raw).items() if not k.startswith("_")}
    tickets = list(ticket_fields())
    ticket_orders = {t["order_id"] for t in tickets if t["order_id"] != "none"}
    check("every ticket order ID has an order record", ticket_orders <= set(orders),
          f"missing {sorted(ticket_orders - set(orders))}")
    check("no order record without a ticket", set(orders) <= ticket_orders,
          f"extra {sorted(set(orders) - ticket_orders)}")
    for oid, o in orders.items():
        calc = round(sum(i["qty"] * i["unit_price"] for i in o["items"]) + o["shipping_cost"], 2)
        check(f"{oid} total matches items", abs(calc - o["total"]) < 0.005, f"{calc} vs {o['total']}")
        check(f"{oid} market matches ID", oid.split("-")[1] == o["market"])
    leaks = []
    for t in tickets:
        name = re.sub(r"\(.*?\)", "", t["customer"])
        tokens = [w for w in re.split(r"[\s.,]+", name) if len(w) >= 3 and w.lower() not in {"dr", "mr", "mrs", "ms"}]
        if t["customer_email"].lower() in raw.lower():
            leaks.append(f"email {t['id']}")
        leaks += [f"name {t['id']}" for w in tokens if re.search(rf"\b{re.escape(w)}\b", raw)]
    check("no customer names or emails in order data", not leaks, ", ".join(sorted(set(leaks))))
    check("no email address pattern in order data", not re.search(r"[\w.+-]+@[\w-]+\.\w+", raw))


def parse(result):
    return json.loads(result.content[0].text)


async def protocol_checks():
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            check("server exposes exactly one tool, get_order", [t.name for t in tools] == ["get_order"],
                  str([t.name for t in tools]))
            ann = tools[0].annotations
            check("get_order is annotated read-only", bool(ann and ann.readOnlyHint))

            dbl = parse(await session.call_tool("get_order", {"order_id": "HR-DE-77602"}))
            caps = [p for p in dbl.get("payments", []) if p["type"] == "capture"]
            check("HR-DE-77602 shows two captures (double charge)", dbl["found"] and len(caps) == 2)

            cb = parse(await session.call_tool("get_order", {"order_id": "HR-UK-55877"}))
            types = [p["type"] for p in cb["payments"]]
            check("HR-UK-55877 has an open chargeback and proof of delivery",
                  "chargeback" in types and cb["shipment"]["proof_of_delivery"]["available"])

            ship = parse(await session.call_tool("get_order", {"order_id": "HR-UK-55921"}))
            check("HR-UK-55921 is unshipped and address can change",
                  ship["shipment"]["shipped_at"] is None and ship["address_change_allowed"])

            low = parse(await session.call_tool("get_order", {"order_id": " hr-de-77602 "}))
            check("order ID is normalised", low["found"])

            missing = parse(await session.call_tool("get_order", {"order_id": "HR-DE-99999"}))
            check("unknown order returns found false", missing["found"] is False)

            bad = parse(await session.call_tool("get_order", {"order_id": "../etc/passwd"}))
            check("invalid ID returns found false", bad["found"] is False)


static_checks()
asyncio.run(protocol_checks())
print("problems:", len(failures))
sys.exit(1 if failures else 0)
