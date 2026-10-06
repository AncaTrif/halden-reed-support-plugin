#!/usr/bin/env python3
"""Halden & Reed orders MCP server (fictional data, read-only).

Stands in for the order system, payment provider and carrier tracking that a
support agent would otherwise open one by one. It exposes one tool, get_order.
Records hold no customer names, emails or addresses. Nothing here can change an
order, a payment or a shipment.

Run over stdio: .venv/bin/python mcp_servers/orders/server.py
"""
import json
import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

DATA_FILE = Path(__file__).resolve().parent / "orders.json"
ORDER_ID = re.compile(r"^HR-(DE|UK|US)-\d{5}$")

mcp = FastMCP("orders")


def load_orders() -> dict:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def lookup(order_id: str) -> dict:
    """Pure lookup, kept separate from the tool so tests can call it directly."""
    order_id = order_id.strip().upper()
    if not ORDER_ID.match(order_id):
        return {"found": False, "order_id": order_id,
                "message": "Not a valid order ID. Expected a format like HR-DE-77602."}
    order = load_orders().get(order_id)
    if order is None:
        return {"found": False, "order_id": order_id,
                "message": "No order with this ID. Do not assume facts about it."}
    return {"found": True, **order}


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)
)
def get_order(order_id: str) -> dict:
    """Look up the facts of one order: status, items, totals, shipment and
    tracking, proof of delivery, payments (captures, refunds, chargebacks) and
    whether the delivery address can still be changed.

    Read-only. Returns order and payment facts only, never customer names, emails
    or addresses. If the order does not exist, found is false and nothing should
    be assumed about it. order_id looks like HR-DE-77602.
    """
    return lookup(order_id)


if __name__ == "__main__":
    mcp.run()
