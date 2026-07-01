# Yandex Workspace Configuration

Create `~/.hermes/yandex_config.json` with your settings:

```json
{
  "login": "your_yandex_login",
  "imap_server": "imap.yandex.ru",
  "imap_port": 993,
  "smtp_server": "smtp.yandex.ru",
  "smtp_port": 465
}
```

## Security Notes

- `yandex_client_secret.json` — contains OAuth credentials and mail password (chmod 600)
- `yandex_token.json` — OAuth token for Yandex ID API (chmod 600)
- `yandex_config.json` — configuration file (chmod 600)

## File Permissions

```bash
chmod 600 ~/.hermes/yandex_client_secret.json
chmod 600 ~/.hermes/yandex_token.json
chmod 600 ~/.hermes/yandex_config.json
```
