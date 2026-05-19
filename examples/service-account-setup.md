# Service Account Setup (step-by-step)

If you're new to Google Cloud, this is the path of least resistance.

## 1. Create or pick a Google Cloud project

Go to https://console.cloud.google.com — top bar → "Select a project" → "New Project".

Name it something memorable like `claude-mcp-tools`. Create.

## 2. Enable the Google Sheets API

Left sidebar → "APIs & Services" → "Library" → search "Google Sheets API" → click it → "Enable".

Repeat for "Google Drive API" (needed for `get_metadata` tool).

## 3. Create a service account

Left sidebar → "APIs & Services" → "Credentials" → "Create credentials" → "Service account".

- Service account name: `claude-sheets` (or similar)
- Description: `MCP server access to my sheets`
- Click "Create and Continue"
- **Skip** the optional steps (Grant access, Grant user access) — click "Done"

## 4. Generate a JSON key

You'll see your new service account in the list. Click it.

Top tabs → "Keys" → "Add key" → "Create new key" → JSON → Create.

A file downloads automatically. **This is your credential.** Store it securely (do NOT commit to git).

Suggested path:
- macOS/Linux: `~/.config/mcp-google-sheets/credentials.json`
- Windows: `%USERPROFILE%\.config\mcp-google-sheets\credentials.json`

## 5. Share your spreadsheet with the service account

The service account has its own email address — looks like:
```
claude-sheets@your-project-id.iam.gserviceaccount.com
```

You can find it in the JSON file under `client_email`.

In your Google Sheet:
1. Click "Share" (top right)
2. Paste the service account email
3. Choose role:
   - **Viewer** = read-only access (recommended for analytics use cases)
   - **Editor** = full read/write (needed for `append_row`, `update_range`)
4. Uncheck "Notify people"
5. Share

The service account now has access. Claude (through this MCP server) can operate on the sheet.

## 6. Wire into Claude Desktop

See `examples/claude_desktop_config.json`. Replace the placeholder path with your JSON key file's actual location.

Restart Claude Desktop. The tools should appear.

## Security notes

- Treat the JSON key like a password. Anyone who has it can access every sheet shared with that service account.
- If the key leaks, immediately revoke it in Google Cloud Console: APIs & Services → Credentials → click the service account → Keys → delete the leaked key → generate a new one.
- Use **separate service accounts** for separate scopes of trust. Don't share the "claude-sheets" service account email with sheets containing sensitive data unless you trust Claude with that data.
- Free tier quota: 60 read requests/min, 60 write requests/min. Plenty for personal use.
