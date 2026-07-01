#!/usr/bin/env python3
"""
Yandex Workspace Setup - OAuth2 setup for Yandex services.

Usage:
  setup.py --check          # Check if auth is valid
  setup.py --auth-url       # Get OAuth URL
  setup.py --auth-code CODE # Exchange code for token
  setup.py --revoke         # Revoke token
  setup.py --test-mail      # Test mail connection
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import secrets
import urllib.request
import urllib.parse
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERMES_HOME = Path.home() / ".hermes"
TOKEN_PATH = HERMES_HOME / "yandex_token.json"
CLIENT_SECRET_PATH = HERMES_HOME / "yandex_client_secret.json"
PENDING_AUTH_PATH = HERMES_HOME / "yandex_oauth_pending.json"

REDIRECT_URI = "http://localhost:8085"

AUTH_URL = "https://oauth.yandex.com/authorize"
TOKEN_URL = "https://oauth.yandex.com/token"
INFO_URL = "https://login.yandex.ru/info"

SCOPES = ["login:info"]


def load_client_secret() -> dict:
    if not CLIENT_SECRET_PATH.exists():
        print(f"ERROR: Client secret not found at {CLIENT_SECRET_PATH}")
        sys.exit(1)
    try:
        data = json.loads(CLIENT_SECRET_PATH.read_text())
        if "client_id" not in data or "client_secret" not in data:
            print("ERROR: Must contain client_id and client_secret")
            sys.exit(1)
        return data
    except json.JSONDecodeError:
        print("ERROR: File is not valid JSON")
        sys.exit(1)


def check_auth(quiet=False) -> bool:
    if not TOKEN_PATH.exists():
        if not quiet:
            print(f"NOT_AUTHENTICATED: No token at {TOKEN_PATH}")
        return False
    data = json.loads(TOKEN_PATH.read_text())
    if "access_token" not in data:
        if not quiet:
            print("TOKEN_INVALID")
        return False
    expires_at = data.get("expires_at", 0)
    if expires_at and time.time() > expires_at:
        if "refresh_token" in data:
            return _refresh_token(data, quiet)
        if not quiet:
            print("TOKEN_EXPIRED")
        return False
    if not quiet:
        print(f"AUTHENTICATED: Token valid at {TOKEN_PATH}")
    return True


def _refresh_token(data, quiet=False) -> bool:
    client = load_client_secret()
    params = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": data["refresh_token"],
        "client_id": client["client_id"],
        "client_secret": client["client_secret"]
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=params,
                                headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
    except Exception as e:
        if not quiet:
            print(f"REFRESH_FAILED: {e}")
        return False
    new_data = {
        "access_token": result["access_token"],
        "refresh_token": result.get("refresh_token", data["refresh_token"]),
        "expires_at": time.time() + result.get("expires_in", 3600),
        "token_type": result.get("token_type", "bearer"),
        "scope": result.get("scope", data.get("scope", ""))
    }
    TOKEN_PATH.write_text(json.dumps(new_data, indent=2))
    if not quiet:
        print(f"AUTHENTICATED: Token refreshed at {TOKEN_PATH}")
    return True


def get_auth_url():
    state = secrets.token_urlsafe(16)
    PENDING_AUTH_PATH.write_text(json.dumps({
        "state": state, "redirect_uri": REDIRECT_URI
    }, indent=2))
    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": load_client_secret()["client_id"],
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "state": state,
        "force_confirm": "yes"
    })
    print(f"{AUTH_URL}?{params}")


def exchange_auth_code(code_or_url):
    if not PENDING_AUTH_PATH.exists():
        print("ERROR: Run --auth-url first")
        sys.exit(1)
    pending = json.loads(PENDING_AUTH_PATH.read_text())
    if code_or_url.startswith("http"):
        parsed = urlparse(code_or_url)
        p = parse_qs(parsed.query)
        if "code" not in p:
            print("ERROR: No code in URL")
            sys.exit(1)
        code = p["code"][0]
        returned_state = p.get("state", [None])[0]
        if returned_state and returned_state != pending["state"]:
            print("ERROR: State mismatch")
            sys.exit(1)
    else:
        code = code_or_url
    client = load_client_secret()
    params = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client["client_id"],
        "client_secret": client["client_secret"],
        "redirect_uri": pending.get("redirect_uri", REDIRECT_URI)
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=params,
                                headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
    except Exception as e:
        print(f"ERROR: Token exchange failed: {e}")
        sys.exit(1)
    token_data = {
        "access_token": result["access_token"],
        "refresh_token": result.get("refresh_token"),
        "expires_at": time.time() + result.get("expires_in", 3600),
        "token_type": result.get("token_type", "bearer"),
        "scope": result.get("scope", " ".join(SCOPES))
    }
    TOKEN_PATH.write_text(json.dumps(token_data, indent=2))
    PENDING_AUTH_PATH.unlink(missing_ok=True)
    print(f"OK: Authenticated. Token saved to {TOKEN_PATH}")


def revoke():
    if not TOKEN_PATH.exists():
        print("No token to revoke.")
        return
    TOKEN_PATH.unlink(missing_ok=True)
    PENDING_AUTH_PATH.unlink(missing_ok=True)
    print(f"Deleted {TOKEN_PATH}")


def test_mail():
    """Test mail connection."""
    import imaplib
    import smtplib
    import ssl
    
    creds = load_client_secret()
    mail_password = creds.get("mail_password")
    
    if not mail_password:
        print("ERROR: No mail_password in credentials")
        sys.exit(1)
    
    # Get login from config or token
    config_path = HERMES_HOME / "yandex_config.json"
    if config_path.exists():
        config = json.loads(config_path.read_text())
        login = config.get("login", "")
    else:
        login = ""  # Must be set in config
    
    print("Testing IMAP...")
    try:
        mail = imaplib.IMAP4_SSL("imap.yandex.ru", 993)
        mail.login(login, mail_password)
        print("✅ IMAP: OK")
        mail.logout()
    except Exception as e:
        print(f"❌ IMAP: {e}")
    
    print("Testing SMTP...")
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.yandex.ru", 465, context=context) as server:
            server.login(login, mail_password)
            print("✅ SMTP: OK")
    except Exception as e:
        print(f"❌ SMTP: {e}")


def main():
    parser = argparse.ArgumentParser(description="Yandex Workspace Setup")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--auth-url", action="store_true")
    group.add_argument("--auth-code", metavar="CODE")
    group.add_argument("--revoke", action="store_true")
    group.add_argument("--test-mail", action="store_true")
    
    args = parser.parse_args()
    
    if args.check:
        sys.exit(0 if check_auth() else 1)
    elif args.auth_url:
        get_auth_url()
    elif args.auth_code:
        exchange_auth_code(args.auth_code)
    elif args.revoke:
        revoke()
    elif args.test_mail:
        test_mail()


if __name__ == "__main__":
    main()
