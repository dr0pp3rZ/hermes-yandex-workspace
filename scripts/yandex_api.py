#!/usr/bin/env python3
"""
Yandex Workspace API - Mail operations via IMAP/SMTP.

Usage:
  yandex_api.py mail list [--max N] [--folder FOLDER]
  yandex_api.py mail get MESSAGE_ID
  yandex_api.py mail send --to EMAIL --subject SUBJECT --body BODY [--html]
  yandex_api.py mail reply MESSAGE_ID --body BODY
  yandex_api.py mail folders
  yandex_api.py mail search QUERY [--max N] [--folder FOLDER]
"""

from __future__ import annotations

import argparse
import imaplib
import json
import smtplib
import ssl
import sys
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

HERMES_HOME = Path.home() / ".hermes"
CRED_PATH = HERMES_HOME / "yandex_client_secret.json"
CONFIG_PATH = HERMES_HOME / "yandex_config.json"

# Default config
DEFAULT_CONFIG = {
    "imap_server": "imap.yandex.ru",
    "imap_port": 993,
    "smtp_server": "smtp.yandex.ru",
    "smtp_port": 465,
    "login": ""  # MUST be set in yandex_config.json
}


def load_config() -> dict:
    """Load configuration from file or use defaults."""
    if CONFIG_PATH.exists():
        try:
            config = json.loads(CONFIG_PATH.read_text())
            return validate_config({**DEFAULT_CONFIG, **config})
        except Exception:
            pass
    return validate_config(DEFAULT_CONFIG.copy())


def validate_config(config: dict) -> dict:
    """Validate configuration and set defaults."""
    if not config.get("login"):
        # Try to load from yandex_client_secret.json
        if CRED_PATH.exists():
            try:
                creds = json.loads(CRED_PATH.read_text())
                if creds.get("login"):
                    config["login"] = creds["login"]
            except Exception:
                pass
    
    if not config.get("login"):
        print("ERROR: No 'login' configured. Set it in ~/.hermes/yandex_config.json")
        print('Example: {"login": "your_yandex_login", ...}')
        sys.exit(1)
    
    return config


def load_credentials() -> dict:
    """Load credentials from secure file."""
    if not CRED_PATH.exists():
        print(f"ERROR: Credentials not found at {CRED_PATH}")
        print("Create it with: {\"mail_password\": \"your_app_password\"}")
        sys.exit(1)
    
    try:
        return json.loads(CRED_PATH.read_text())
    except Exception as e:
        print(f"ERROR: Failed to read credentials: {e}")
        sys.exit(1)


def get_imap_connection():
    """Create IMAP connection."""
    config = load_config()
    creds = load_credentials()
    
    try:
        mail = imaplib.IMAP4_SSL(config["imap_server"], config["imap_port"])
        mail.login(config["login"], creds["mail_password"])
        return mail
    except Exception as e:
        print(f"ERROR: IMAP connection failed: {e}")
        sys.exit(1)


def get_smtp_connection():
    """Create SMTP connection."""
    config = load_config()
    creds = load_credentials()
    
    try:
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"], context=context)
        server.login(config["login"], creds["mail_password"])
        return server
    except Exception as e:
        print(f"ERROR: SMTP connection failed: {e}")
        sys.exit(1)


def decode_mime_header(header: str) -> str:
    """Decode MIME encoded header."""
    if not header:
        return ""
    
    decoded_parts = decode_header(header)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or 'utf-8', errors='replace'))
        else:
            result.append(part)
    return ''.join(result)


def list_folders():
    """List all mail folders."""
    mail = get_imap_connection()
    
    try:
        status, folders = mail.list()
        result = []
        for folder in folders:
            if isinstance(folder, bytes):
                folder = folder.decode('utf-8', errors='replace')
            # Parse folder name
            parts = folder.split('"')
            if len(parts) >= 3:
                name = parts[-2] if parts[-2] else parts[-1]
            else:
                name = folder
            result.append(name)
        
        return {"folders": result}
    finally:
        mail.logout()


def list_emails(folder: str = "INBOX", max_count: int = 10):
    """List emails in folder."""
    mail = get_imap_connection()
    
    try:
        status, _ = mail.select(folder, readonly=True)
        if status != 'OK':
            return {"error": f"Failed to select folder: {folder}"}
        
        status, messages = mail.search(None, 'ALL')
        if status != 'OK':
            return {"error": "Failed to search messages"}
        
        msg_ids = messages[0].split()
        if not msg_ids:
            return {"emails": [], "total": 0}
        
        # Get last N messages
        recent_ids = msg_ids[-max_count:]
        emails = []
        
        for msg_id in reversed(recent_ids):
            status, msg_data = mail.fetch(msg_id, '(BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE)])')
            if status != 'OK':
                continue
            
            raw = msg_data[0][1].decode('utf-8', errors='replace')
            msg = email.message_from_string(raw)
            
            emails.append({
                "id": msg_id.decode(),
                "from": decode_mime_header(msg.get('From', '')),
                "to": decode_mime_header(msg.get('To', '')),
                "subject": decode_mime_header(msg.get('Subject', '')),
                "date": msg.get('Date', ''),
            })
        
        return {
            "emails": emails,
            "total": len(msg_ids),
            "folder": folder
        }
    finally:
        mail.logout()


def get_email(message_id: str, folder: str = "INBOX"):
    """Get full email content."""
    mail = get_imap_connection()
    
    try:
        status, _ = mail.select(folder, readonly=True)
        if status != 'OK':
            return {"error": f"Failed to select folder: {folder}"}
        
        status, msg_data = mail.fetch(message_id.encode(), '(RFC822)')
        if status != 'OK':
            return {"error": f"Failed to fetch message: {message_id}"}
        
        raw = msg_data[0][1].decode('utf-8', errors='replace')
        msg = email.message_from_string(raw)
        
        # Extract body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                    break
                elif content_type == 'text/html' and not body:
                    body = part.get_payload(decode=True).decode('utf-8', errors='replace')
        else:
            body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
        
        return {
            "id": message_id,
            "from": decode_mime_header(msg.get('From', '')),
            "to": decode_mime_header(msg.get('To', '')),
            "subject": decode_mime_header(msg.get('Subject', '')),
            "date": msg.get('Date', ''),
            "body": body,
            "content_type": msg.get_content_type()
        }
    finally:
        mail.logout()


def send_email(to: str, subject: str, body: str, html: bool = False):
    """Send email via SMTP."""
    config = load_config()
    
    msg = MIMEMultipart()
    msg['From'] = f"{config['login']}@yandex.ru"
    msg['To'] = to
    msg['Subject'] = subject
    
    content_type = 'html' if html else 'plain'
    msg.attach(MIMEText(body, content_type, 'utf-8'))
    
    server = get_smtp_connection()
    try:
        server.send_message(msg)
        return {
            "status": "sent",
            "from": msg['From'],
            "to": to,
            "subject": subject
        }
    finally:
        server.quit()


def reply_to_email(message_id: str, body: str, folder: str = "INBOX"):
    """Reply to an email."""
    # First get the original email
    original = get_email(message_id, folder)
    if "error" in original:
        return original
    
    # Create reply
    config = load_config()
    
    msg = MIMEMultipart()
    msg['From'] = f"{config['login']}@yandex.ru"
    msg['To'] = original['from']
    msg['Subject'] = f"Re: {original['subject']}"
    msg['In-Reply-To'] = message_id
    msg['References'] = message_id
    
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    server = get_smtp_connection()
    try:
        server.send_message(msg)
        return {
            "status": "sent",
            "from": msg['From'],
            "to": original['from'],
            "subject": msg['Subject'],
            "in_reply_to": message_id
        }
    finally:
        server.quit()


def search_emails(query: str, folder: str = "INBOX", max_count: int = 10):
    """Search emails."""
    mail = get_imap_connection()
    
    try:
        status, _ = mail.select(folder, readonly=True)
        if status != 'OK':
            return {"error": f"Failed to select folder: {folder}"}
        
        # IMAP search
        status, messages = mail.search(None, f'(OR SUBJECT "{query}" FROM "{query}")')
        if status != 'OK':
            return {"error": "Search failed"}
        
        msg_ids = messages[0].split()
        if not msg_ids:
            return {"emails": [], "total": 0, "query": query}
        
        # Get last N messages
        recent_ids = msg_ids[-max_count:]
        emails = []
        
        for msg_id in reversed(recent_ids):
            status, msg_data = mail.fetch(msg_id, '(BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE)])')
            if status != 'OK':
                continue
            
            raw = msg_data[0][1].decode('utf-8', errors='replace')
            msg = email.message_from_string(raw)
            
            emails.append({
                "id": msg_id.decode(),
                "from": decode_mime_header(msg.get('From', '')),
                "to": decode_mime_header(msg.get('To', '')),
                "subject": decode_mime_header(msg.get('Subject', '')),
                "date": msg.get('Date', ''),
            })
        
        return {
            "emails": emails,
            "total": len(msg_ids),
            "query": query,
            "folder": folder
        }
    finally:
        mail.logout()


def main():
    parser = argparse.ArgumentParser(description="Yandex Workspace API")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Mail commands
    mail_parser = subparsers.add_parser("mail", help="Mail operations")
    mail_subparsers = mail_parser.add_subparsers(dest="subcommand")
    
    # List folders
    mail_subparsers.add_parser("folders", help="List mail folders")
    
    # List emails
    list_parser = mail_subparsers.add_parser("list", help="List emails")
    list_parser.add_argument("--max", type=int, default=10, help="Max emails to show")
    list_parser.add_argument("--folder", default="INBOX", help="Mail folder")
    
    # Get email
    get_parser = mail_subparsers.add_parser("get", help="Get email content")
    get_parser.add_argument("message_id", help="Message ID")
    get_parser.add_argument("--folder", default="INBOX", help="Mail folder")
    
    # Send email
    send_parser = mail_subparsers.add_parser("send", help="Send email")
    send_parser.add_argument("--to", required=True, help="Recipient email")
    send_parser.add_argument("--subject", required=True, help="Email subject")
    send_parser.add_argument("--body", required=True, help="Email body")
    send_parser.add_argument("--html", action="store_true", help="Send as HTML")
    
    # Reply to email
    reply_parser = mail_subparsers.add_parser("reply", help="Reply to email")
    reply_parser.add_argument("message_id", help="Message ID to reply to")
    reply_parser.add_argument("--body", required=True, help="Reply body")
    reply_parser.add_argument("--folder", default="INBOX", help="Mail folder")
    
    # Search emails
    search_parser = mail_subparsers.add_parser("search", help="Search emails")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--max", type=int, default=10, help="Max results")
    search_parser.add_argument("--folder", default="INBOX", help="Mail folder")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "mail":
        if args.subcommand == "folders":
            result = list_folders()
        elif args.subcommand == "list":
            result = list_emails(args.folder, args.max)
        elif args.subcommand == "get":
            result = get_email(args.message_id, args.folder)
        elif args.subcommand == "send":
            result = send_email(args.to, args.subject, args.body, args.html)
        elif args.subcommand == "reply":
            result = reply_to_email(args.message_id, args.body, args.folder)
        elif args.subcommand == "search":
            result = search_emails(args.query, args.folder, args.max)
        else:
            mail_parser.print_help()
            sys.exit(1)
        
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
