#!/usr/bin/env python3
"""Exchange a Zoho self client grant code for a refresh token and save it to .env.

Run in your own terminal. Secrets are typed here (hidden) and written to .env
with mode 600. Nothing is printed. Usage:

  .venv/bin/python scripts/zoho_auth.py --name read    # read-only token
  .venv/bin/python scripts/zoho_auth.py --name seed    # token that can create tickets
"""
import argparse
import os
import sys
from getpass import getpass
from pathlib import Path

import httpx

from zoho_client import HOSTS, ROOT, load_env

ENV_FILE = ROOT / ".env"


def set_env(key: str, value: str) -> None:
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines() if ENV_FILE.exists() else []
    lines = [ln for ln in lines if not ln.startswith(f"{key}=")]
    lines.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(ENV_FILE, 0o600)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, choices=["read", "seed"])
    ap.add_argument("--dc", default=os.environ.get("ZOHO_DC", "eu"), choices=sorted(HOSTS))
    args = ap.parse_args()
    load_env()
    accounts, desk = HOSTS[args.dc]

    client_id = os.environ.get("ZOHO_CLIENT_ID") or input("Client ID: ").strip()
    client_secret = os.environ.get("ZOHO_CLIENT_SECRET") or getpass("Client secret (hidden): ").strip()
    code = getpass("Grant code (hidden): ").strip()

    r = httpx.post(f"{accounts}/oauth/v2/token", data={
        "grant_type": "authorization_code", "client_id": client_id,
        "client_secret": client_secret, "code": code}, timeout=20)
    body = r.json() if r.content else {}
    if "refresh_token" not in body:
        print(f"Token exchange failed: HTTP {r.status_code}, error={body.get('error', 'unknown')}")
        print("Grant codes expire after a few minutes and work once. Generate a new one and retry.")
        return 1

    set_env("ZOHO_DC", args.dc)
    set_env("ZOHO_CLIENT_ID", client_id)
    set_env("ZOHO_CLIENT_SECRET", client_secret)
    set_env(f"ZOHO_REFRESH_TOKEN_{args.name.upper()}", body["refresh_token"])

    org = httpx.get(f"{desk}/api/v1/organizations",
                    headers={"Authorization": f"Zoho-oauthtoken {body['access_token']}"}, timeout=20)
    if org.status_code == 200 and org.json().get("data"):
        set_env("ZOHO_ORG_ID", str(org.json()["data"][0]["id"]))
        print(f"Saved the {args.name} token and the organisation ID to .env (mode 600).")
    else:
        print(f"Saved the {args.name} token to .env, but could not read the organisation ID "
              f"(HTTP {org.status_code}). The scope Desk.basic.READ is needed for that.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
