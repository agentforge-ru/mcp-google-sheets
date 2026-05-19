# mcp-google-sheets

A **focused MCP server for Google Sheets** — read/write tools for Claude to operate on your spreadsheets without copy-pasting cells back and forth.

> If you've ever asked Claude "look at this Google Sheet and tell me X" and then pasted 200 rows of data into the chat — this is for you.

## Why this exists

Claude is great at analyzing tabular data. But getting that data into the chat reliably is painful:
- Copy-paste loses formulas and formatting
- CSV exports drop column types
- Re-asking for the same data 5 times in a session is annoying

This MCP server gives Claude direct, structured access to your sheets:
- ✅ List all sheets in a spreadsheet
- ✅ Read any range with type-preserving values
- ✅ Append rows
- ✅ Update specific cells / ranges
- ✅ Get metadata (titles, IDs, dimensions)

## Tools exposed to the LLM

| Tool | Purpose |
|---|---|
| `list_sheets(spreadsheet_id)` | All sheet names + their IDs + dimensions |
| `read_range(spreadsheet_id, range)` | Read an A1-notation range. Returns nested list of values. |
| `append_row(spreadsheet_id, sheet, values)` | Append a single row to the bottom of a sheet |
| `update_range(spreadsheet_id, range, values)` | Overwrite specific cells with new values |
| `get_metadata(spreadsheet_id)` | Title, owner, last-modified, number of sheets |

## Installation

```bash
git clone https://github.com/agentforge-ru/mcp-google-sheets
cd mcp-google-sheets
pip install -e .
```

## Authentication

This server uses a **Google Cloud service account** — the cleanest auth model for headless tools.

1. Go to [Google Cloud Console](https://console.cloud.google.com) → new project (or pick existing)
2. APIs & Services → Library → enable **Google Sheets API**
3. APIs & Services → Credentials → Create credentials → **Service account**
4. Fill in name (e.g., `claude-sheets`), Create → Done
5. Click on the new service account → Keys → Add key → JSON → download
6. Save the file securely (e.g., `~/.config/mcp-google-sheets/credentials.json`)
7. **Share your sheet** with the service account's email (looks like `claude-sheets@your-project.iam.gserviceaccount.com`) — Viewer for read-only, Editor for write access

## Wiring into Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sheets": {
      "command": "python",
      "args": ["-m", "mcp_google_sheets"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/absolute/path/to/credentials.json"
      }
    }
  }
}
```

Restart Claude Desktop. Tools appear in the model's context.

## Usage examples (in Claude Desktop chat)

```
You: What sheets are in spreadsheet 1aBcDeFgHi...XyZ?
Claude: [calls list_sheets] You have 3 sheets:
  - "Sales" (1247 rows × 12 cols)
  - "Customers" (843 rows × 8 cols)
  - "Pipeline" (156 rows × 6 cols)

You: Read the top 50 rows of Sales.
Claude: [calls read_range(range="Sales!A1:L50")] Returns header + 49 rows.

You: Add a new lead: name "ACME Corp", email "ops@acme.example", source "referral".
Claude: [calls append_row(sheet="Pipeline", values=["ACME Corp", "ops@acme.example", "referral", "..."])]
```

## Architecture

```
[ Claude Desktop / Claude Code / Cursor ]
              ↓ MCP protocol (stdio)
        [ mcp-google-sheets ]
              ↓ google-api-python-client
        [ Google Sheets API ]
              ↓
        [ Your spreadsheets ]
```

Auth happens once at startup via the service account JSON key. The server keeps a single API client instance for the session.

## Safety model

- **No DELETE_SHEET / DELETE_RANGE tools exposed.** Even with editor access, the server won't delete entire sheets — to remove rows, you use `update_range` to clear cells. This is intentional: easier to recover from "blanked column" than "deleted sheet".
- **Append-only by default for new data.** `append_row` is non-destructive (always adds to end).
- **`update_range` is destructive** but scoped to specific A1 ranges. The server won't accept "Sheet!A:Z" without a row constraint to prevent accidental whole-column overwrites.

## Limitations (honest)

- **Service account auth only.** No OAuth user flow yet. If you need a sheet you can't share with a service account (e.g., locked-down enterprise), this won't help.
- **No formula evaluation.** Returns raw cell values. If a cell contains `=A1+B1`, you get the computed result, not the formula — unless you use `valueRenderOption=FORMULA` which I haven't wired through yet.
- **No charts / formatting / pivot-table manipulation.** Pure values only.
- **Rate limits apply.** Google Sheets API caps you at 60 reads/min and 60 writes/min on free quota. For higher volume, request a quota increase.

## License

MIT — see `LICENSE`. Use it, fork it, send PRs.

## Author

Built by [agentforge_ru](https://github.com/agentforge-ru) — custom Claude Code subagents, MCP servers, and Telegram bots with AI logic.

Need a custom MCP server tailored to your data source? [Open an issue](https://github.com/agentforge-ru/mcp-google-sheets/issues) or reach via Kwork.
