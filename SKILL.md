---
name: yandex-workspace
description: "Yandex Mail via IMAP/SMTP with app password. Disk and Calendar APIs are restricted by Yandex."
version: 2.0.0
author: dr0pp3r
tags: [yandex, email, imap, smtp, mail, productivity]
---

# Yandex Workspace

Yandex Mail integration via IMAP (read) and SMTP (send). Uses app password for secure access.

## Important Limitations

⚠️ **Yandex Disk API** — NOT available through public OAuth. Yandex has restricted access.
⚠️ **Yandex Calendar API** — NOT available through public OAuth. CalDAV requires separate setup.

**What works:**
- ✅ Yandex Mail via IMAP (read emails)
- ✅ Yandex Mail via SMTP (send emails)
- ❌ Yandex Disk — API restricted
- ❌ Yandex Calendar — API restricted

## Prerequisites

1. Yandex account with 2FA enabled
2. App password for mail access (NOT your main password)

## First-Time Setup

### Step 1: Enable IMAP in Yandex Mail

1. Go to [Yandex Mail Settings](https://mail.yandex.ru/#setup/client)
2. Find "Mail clients" (Mail clients)
3. Enable **IMAP** access

### Step 2: Create App Password

1. Go to [Yandex Security Settings](https://id.yandex.ru/security/app-passwords)
2. Click "Create app password"
3. Select "Mail" as the service
4. Name it "Hermes Agent"
5. Copy the generated password

### Step 3: Save Credentials Securely

Save to `~/.hermes/yandex_client_secret.json`:
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

### Step 4: Verify Connection

```bash
# Test IMAP
python3 -c "
import imaplib, json
from pathlib import Path
creds = json.loads((Path.home() / '.hermes/yandex_client_secret.json').read_text())
mail = imaplib.IMAP4_SSL('imap.yandex.ru', 993)
mail.login('YOUR_LOGIN', creds['mail_password'])
print('IMAP: OK')
mail.logout()
"

# Test SMTP
python3 -c "
import smtplib, json, ssl
from pathlib import Path
creds = json.loads((Path.home() / '.hermes/yandex_client_secret.json').read_text())
context = ssl.create_default_context()
with smtplib.SMTP_SSL('smtp.yandex.ru', 465, context=context) as server:
    server.login('YOUR_LOGIN', creds['mail_password'])
    print('SMTP: OK')
"
```

## Usage

### Read Emails (IMAP)

```python
import imaplib, json, email
from email.header import decode_header
from pathlib import Path

creds = json.loads((Path.home() / '.hermes/yandex_client_secret.json').read_text())

mail = imaplib.IMAP4_SSL('imap.yandex.ru', 993)
mail.login('YOUR_LOGIN', creds['mail_password'])
mail.select('INBOX')

# Search for recent emails
status, messages = mail.search(None, 'ALL')
msg_ids = messages[0].split()

# Read last 5 emails
for msg_id in msg_ids[-5:]:
    status, msg_data = mail.fetch(msg_id, '(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])')
    raw = msg_data[0][1].decode('utf-8', errors='replace')
    msg = email.message_from_string(raw)
    
    subject = msg.get('Subject', '')
    if subject:
        decoded = decode_header(subject)
        subject = ''.join([s.decode(c or 'utf-8') if isinstance(s, bytes) else s for s, c in decoded])
    
    sender = msg.get('From', '')
    date = msg.get('Date', '')
    print(f'{date[:16]} | {sender[:40]} | {subject[:50]}')

mail.logout()
```

### Send Email (SMTP)

```python
import smtplib, json, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

creds = json.loads((Path.home() / '.hermes/yandex_client_secret.json').read_text())

msg = MIMEMultipart()
msg['From'] = 'YOUR_LOGIN@yandex.ru'
msg['To'] = 'recipient@example.com'
msg['Subject'] = 'Subject here'
msg.attach(MIMEText('Message body', 'plain', 'utf-8'))

context = ssl.create_default_context()
with smtplib.SMTP_SSL('smtp.yandex.ru', 465, context=context) as server:
    server.login('YOUR_LOGIN', creds['mail_password'])
    server.send_message(msg)
```

## Security Best Practices

1. **Never use your main password** — always use app passwords
2. **Set file permissions to 600** — `chmod 600 ~/.hermes/yandex_client_secret.json`
3. **Store credentials separately** — don't mix with other API keys
4. **Rotate app passwords regularly** — every 6-12 months
5. **Enable 2FA on Yandex account** — required for app passwords

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `IMAP: FAIL` | Check if IMAP is enabled in Yandex Mail settings |
| `SMTP: FAIL` | Check app password and IMAP/SMTP settings |
| `Authentication failed` | Verify app password is correct |
| `Connection timeout` | Check network/firewall settings |

## File Locations

- Credentials: `~/.hermes/yandex_client_secret.json`
- OAuth token: `~/.hermes/yandex_token.json` (for Yandex ID API only)

## Related Skills

- `google-workspace` — Full Google Workspace integration (Gmail, Calendar, Drive, Docs, Sheets)
- `himalaya` — Terminal email client (alternative approach)
