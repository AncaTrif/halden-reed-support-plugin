"""Small Zoho Desk API client: OAuth refresh tokens, EU by default.

Secrets come from the environment or from .env in the project root (git
ignores it). Nothing here prints or logs a token or secret.
"""
import os
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
HOSTS = {  # data center -> (accounts host, desk host)
    "eu": ("https://accounts.zoho.eu", "https://desk.zoho.eu"),
    "com": ("https://accounts.zoho.com", "https://desk.zoho.com"),
    "in": ("https://accounts.zoho.in", "https://desk.zoho.in"),
    "au": ("https://accounts.zoho.com.au", "https://desk.zoho.com.au"),
}


class ZohoError(RuntimeError):
    pass


def load_env() -> None:
    """Load KEY=VALUE lines from .env without overriding real environment."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


class ZohoDesk:
    def __init__(self, token_var: str = "ZOHO_REFRESH_TOKEN_READ"):
        load_env()
        self.dc = os.environ.get("ZOHO_DC", "eu")
        if self.dc not in HOSTS:
            raise ZohoError(f"Unknown ZOHO_DC {self.dc!r}")
        self.accounts, self.desk = HOSTS[self.dc]
        try:
            self._client_id = os.environ["ZOHO_CLIENT_ID"]
            self._client_secret = os.environ["ZOHO_CLIENT_SECRET"]
            self._refresh = os.environ[token_var]
        except KeyError as exc:
            raise ZohoError(f"Missing setting {exc.args[0]}. Run scripts/zoho_auth.py.") from None
        self.org_id = os.environ.get("ZOHO_ORG_ID", "")
        self._token = ""
        self._expires = 0.0

    def _access_token(self) -> str:
        if self._token and time.time() < self._expires - 60:
            return self._token
        r = httpx.post(
            f"{self.accounts}/oauth/v2/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": self._refresh,
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
            timeout=20,
        )
        body = r.json() if r.content else {}
        if r.status_code != 200 or "access_token" not in body:
            raise ZohoError(f"Token refresh failed: HTTP {r.status_code}, {body.get('error', 'no error field')}")
        self._token = body["access_token"]
        self._expires = time.time() + int(body.get("expires_in_sec", body.get("expires_in", 3600)))
        return self._token

    def request(self, method: str, path: str, *, params=None, json=None):
        headers = {"Authorization": f"Zoho-oauthtoken {self._access_token()}"}
        if self.org_id:
            headers["orgId"] = self.org_id
        r = httpx.request(method, f"{self.desk}/api/v1{path}", params=params, json=json,
                          headers=headers, timeout=30)
        if r.status_code == 204:
            return {}
        if r.status_code >= 400:
            raise ZohoError(f"Zoho Desk {method} {path}: HTTP {r.status_code} {r.text[:300]}")
        return r.json()
