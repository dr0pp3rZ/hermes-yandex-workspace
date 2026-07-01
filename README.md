# Yandex Workspace — Hermes Agent Skill

[![Hermes Agent](https://img.shields.io/badge/Hermes-Agent-blue)](https://hermes-agent.nousresearch.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Security: Safe](https://img.shields.io/badge/Security-Safe-brightgreen)](#security)

Yandex Mail integration for [Hermes Agent](https://hermes-agent.nousresearch.com) via IMAP (read) and SMTP (send). Secure, simple, and production-ready.

## ⚠️ Important Limitations

| Service | Status | Reason |
|---------|--------|--------|
| 📧 **Yandex Mail** | ✅ Works | IMAP/SMTP with app password |
| 💾 **Yandex Disk** | ❌ Not available | API restricted by Yandex |
| 📅 **Yandex Calendar** | ❌ Not available | API restricted by Yandex |

> **Note:** For full cloud workspace integration (Calendar, Drive, Docs, Sheets), use the [`google-workspace`](https://github.com/NousResearch/hermes-agent/tree/main/skills/productivity/google-workspace) skill instead.

## Installation

```bash
hermes skills install dr0pp3rZ/hermes-yandex-workspace
```

Or install from local path:
```bash
hermes skills install /path/to/yandex-workspace
```

## Quick Start

### 1. Enable IMAP in Yandex Mail

1. Go to [Yandex Mail Settings](https://mail.yandex.ru/#setup/client)
2. Find **"Mail clients"** (Mail clients)
3. Enable **IMAP** access

### 2. Create App Password

1. Go to [Yandex Security Settings](https://id.yandex.ru/security/app-passwords)
2. Click **"Create app password"**
3. Select **"Mail"** as the service
4. Name it `Hermes Agent`
5. Copy the generated password

### 3. Save Credentials

Create `~/.hermes/yandex_client_secret.json`:

```json
{
  "client_id": "your_yandex_oauth_client_id",
  "client_secret": "your_yandex_oauth_client_secret",
  "mail_password": "your_app_password_here"
}
```

Set secure permissions:
```bash
chmod 600 ~/.hermes/yandex_client_secret.json
```

### 4. Create Config File

Create `~/.hermes/yandex_config.json`:

```json
{
  "login": "your_yandex_login",
  "imap_server": "imap.yandex.ru",
  "imap_port": 993,
  "smtp_server": "smtp.yandex.ru",
  "smtp_port": 465
}
```

Set secure permissions:
```bash
chmod 600 ~/.hermes/yandex_config.json
```

### 5. Verify Connection

```bash
# Test IMAP and SMTP
python3 ~/.hermes/skills/productivity/yandex-workspace/scripts/setup.py --test-mail
```

## Usage

### CLI Commands

```bash
# Set shortcuts
YAPI="python3 ~/.hermes/skills/productivity/yandex-workspace/scripts/yandex_api.py"
YSETUP="python3 ~/.hermes/skills/productivity/yandex-workspace/scripts/setup.py"

# List emails
$YAPI mail list --max 10

# List folders
$YAPI mail folders

# Get specific email
$YAPI mail get MESSAGE_ID

# Send email
$YAPI mail send --to recipient@example.com --subject "Hello" --body "Message text"

# Reply to email
$YAPI mail reply MESSAGE_ID --body "Thanks for your message!"

# Search emails
$YAPI mail search "meeting" --max 5

# Check connection
$YSETUP --test-mail
```

### Python API

```python
import imaplib
import json
from pathlib import Path

# Load credentials
creds = json.loads((Path.home() / '.hermes/yandex_client_secret.json').read_text())

# Connect to IMAP
mail = imaplib.IMAP4_SSL('imap.yandex.ru', 993)
mail.login('your_login', creds['mail_password'])

# List emails
mail.select('INBOX')
status, messages = mail.search(None, 'ALL')
msg_ids = messages[0].split()

# Read last 5 emails
for msg_id in msg_ids[-5:]:
    status, msg_data = mail.fetch(msg_id, '(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])')
    print(msg_data[0][1].decode())

mail.logout()
```

### Sending Email

```python
import smtplib
import json
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

creds = json.loads((Path.home() / '.hermes/yandex_client_secret.json').read_text())

msg = MIMEMultipart()
msg['From'] = 'your_login@yandex.ru'
msg['To'] = 'recipient@example.com'
msg['Subject'] = 'Subject here'
msg.attach(MIMEText('Message body', 'plain', 'utf-8'))

context = ssl.create_default_context()
with smtplib.SMTP_SSL('smtp.yandex.ru', 465, context=context) as server:
    server.login('your_login', creds['mail_password'])
    server.send_message(msg)
```

## File Structure

```
~/.hermes/
├── yandex_client_secret.json    # OAuth credentials + mail password (chmod 600)
├── yandex_token.json            # OAuth token for Yandex ID API (chmod 600)
└── yandex_config.json           # Configuration (chmod 600)
```

## Security

### Built-in Protections

- ✅ **No hardcoded credentials** — all secrets loaded from files
- ✅ **Secure file permissions** — all credential files use `chmod 600`
- ✅ **SSL/TLS encryption** — all connections use SSL
- ✅ **Input validation** — login and credentials are validated before use
- ✅ **No credential leaks** — passwords never printed to stdout/stderr
- ✅ **Separate config files** — credentials isolated from code

### Best Practices

1. **Never use your main password** — always use app passwords
2. **Set file permissions to 600** — `chmod 600 ~/.hermes/yandex_*.json`
3. **Rotate app passwords regularly** — every 6-12 months
4. **Enable 2FA on Yandex account** — required for app passwords
5. **Don't commit credentials** — `.gitignore` excludes `*.json` files

### Security Audit

This skill passed the Hermes Skills Guard security scan:

```
Scan: yandex-workspace (self/community)  Verdict: SAFE
Decision: ALLOWED — Allowed (community source, safe verdict)
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `IMAP: FAIL` | Check if IMAP is enabled in Yandex Mail settings |
| `SMTP: FAIL` | Check app password and IMAP/SMTP settings |
| `Authentication failed` | Verify app password is correct |
| `Connection timeout` | Check network/firewall settings |
| `No 'login' configured` | Set login in `~/.hermes/yandex_config.json` |

## IMAP Search Syntax

| Command | Description |
|---------|-------------|
| `SEARCH FROM "sender@example.com"` | Emails from specific sender |
| `SEARCH SUBJECT "meeting"` | Emails with subject containing "meeting" |
| `SEARCH UNSEEN` | Unread emails |
| `SEARCH SINCE "01-Jan-2026"` | Emails after date |
| `SEARCH LARGER 1000000` | Emails larger than 1MB |

See [references/yandex-mail-search.md](references/yandex-mail-search.md) for full syntax.

## Related Skills

| Skill | Description |
|-------|-------------|
| [`google-workspace`](https://github.com/NousResearch/hermes-agent/tree/main/skills/productivity/google-workspace) | Full Google Workspace (Gmail, Calendar, Drive, Docs, Sheets) |
| [`himalaya`](https://github.com/NousResearch/hermes-agent/tree/main/skills/email/himalaya) | Terminal email client via IMAP/SMTP |

## Requirements

- Python 3.8+
- Yandex account with 2FA enabled
- App password for mail access

## License

MIT License — see [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run security scan: `hermes skills publish . --to github --repo your/repo`
5. Submit a pull request

## Support

- 📖 [Hermes Agent Documentation](https://hermes-agent.nousresearch.com/docs/)
- 🐛 [Report Issues](https://github.com/dr0pp3rZ/hermes-yandex-workspace/issues)
- 💬 [Hermes Community](https://hermes-agent.nousresearch.com/community/)

