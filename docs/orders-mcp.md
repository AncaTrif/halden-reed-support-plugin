# Orders MCP server (step 5)

A small read-only MCP server that stands in for the order system, payment provider and carrier tracking. All data is fictional.

## What it does

One tool, `get_order(order_id)`. It returns status, items, totals, shipment and tracking, proof of delivery, payments (captures, refunds, chargebacks) and whether the delivery address can still be changed. If the order does not exist it returns `found: false`, and nothing should be assumed about it.

It holds no customer names, emails or addresses. Order IDs and facts only, so case files and Slack posts stay free of personal data.

## Files

- `mcp_servers/orders/server.py`: the server (Python, official `mcp` SDK, stdio).
- `mcp_servers/orders/orders.json`: 11 fictional orders, one for each ticket that has an order ID. HR-1005 has none.
- `mcp_servers/orders/test_orders.py`: checks the data against the tickets and calls the server through a real MCP client.
- `.mcp.json`: registers the server for this project.
- `.claude/settings.json`: `mcp__orders__get_order` is allowed. It is read-only.

## Set up

The MCP SDK needs Python 3.10 or newer. The system Python on this Mac is 3.9, so use Python 3.12 from Homebrew:

```
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python mcp_servers/orders/test_orders.py
```

Start Claude Code in this folder and approve the project server when asked. Run `/mcp` to confirm `orders` is connected.

## Decisions

- Read-only on purpose. No tool changes an order, a payment or a shipment. A human decides.
- One tool, not several. The case file already holds the order ID, so there is no ticket lookup. That would also have meant reading ticket files that contain personal data.
- In real life this would wrap the shop platform, payment provider and carrier APIs with read-only credentials. The tool name and answer shape would stay the same.
- The data was written to match the tickets. For example HR-DE-77602 shows two captures, and HR-UK-55877 has an open chargeback with proof of delivery. These facts answer some open questions in the case files, and that is deliberate.
