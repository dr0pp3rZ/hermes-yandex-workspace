# Yandex Mail IMAP Search Syntax

Yandex Mail supports standard IMAP search commands. Here are the most useful ones:

## Basic Search

```
SEARCH FROM "sender@example.com"
SEARCH SUBJECT "meeting"
SEARCH TO "recipient@example.com"
SEARCH BODY "keyword"
```

## Date Search

```
SEARCH SINCE "01-Jan-2026"
SEARCH BEFORE "31-Dec-2026"
SEARCH ON "15-Jun-2026"
```

## Combined Search

```
SEARCH FROM "boss@company.com" SUBJECT "urgent"
SEARCH FROM "team@company.com" SINCE "01-Jan-2026"
SEARCH SUBJECT "report" BEFORE "31-Dec-2026"
```

## Status Search

```
SEARCH UNSEEN          # Unread emails
SEARCH SEEN            # Read emails
SEARCH FLAGGED         # Starred emails
SEARCH UNFLAGGED       # Not starred
SEARCH ANSWERED        # Replied emails
SEARCH UNANSWERED      # Not replied
```

## Size Search

```
SEARCH LARGER 1000000   # Larger than 1MB
SEARCH SMALLER 100000   # Smaller than 100KB
```

## Examples in Python

```python
import imaplib

mail = imaplib.IMAP4_SSL('imap.yandex.ru', 993)
mail.login('user', 'password')
mail.select('INBOX')

# Search for unread emails from specific sender
status, messages = mail.search(None, 'FROM "boss@company.com" UNSEEN')

# Search for emails with attachments (approximate)
status, messages = mail.search(None, 'LARGER 1000000')

# Search for recent emails
status, messages = mail.search(None, 'SINCE "01-Jan-2026"')

# Get message IDs
msg_ids = messages[0].split()
```

## Notes

- Yandex Mail uses modified UTF-7 encoding for folder names
- Search is case-insensitive for most fields
- Date format: DD-Mon-YYYY (e.g., "01-Jan-2026")
- Size is in bytes
