"""MCP server core: Google Sheets tools."""
import re
import sys
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build as build_google_client
from googleapiclient.errors import HttpError
from mcp.server.fastmcp import FastMCP


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# A1 range with neither a row constraint nor a cell constraint = potentially whole-column overwrite.
# Block ranges like "Sheet1!A:Z" — require at least one row number.
WHOLE_COLUMN_PATTERN = re.compile(r"^[^!]+![A-Z]+:[A-Z]+$")


class SafetyError(RuntimeError):
    """Raised when an operation would be destructive at the whole-column level."""


def _check_safe_range(a1_range: str) -> None:
    if WHOLE_COLUMN_PATTERN.match(a1_range):
        raise SafetyError(
            f"Refused: range '{a1_range}' would overwrite entire columns. "
            f"Add row bounds, e.g., 'Sheet1!A2:Z1000'."
        )


def build_server(credentials_path: str) -> FastMCP:
    creds = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=SCOPES
    )
    sheets_service = build_google_client("sheets", "v4", credentials=creds, cache_discovery=False)
    drive_service = build_google_client("drive", "v3", credentials=creds, cache_discovery=False)

    mcp = FastMCP(
        name="google-sheets",
        instructions=(
            "Google Sheets MCP server. Tools available: list_sheets, read_range, "
            "append_row, update_range, get_metadata. Share your sheet with the "
            "service account email before use."
        ),
    )

    def audit(action: str, detail: str) -> None:
        print(f"[mcp-google-sheets] {action}: {detail[:200]}", file=sys.stderr, flush=True)

    @mcp.tool()
    def list_sheets(spreadsheet_id: str) -> list[dict[str, Any]]:
        """List all sheets (tabs) in a spreadsheet.

        Args:
            spreadsheet_id: The ID from the spreadsheet URL (the part between /d/ and /edit).

        Returns:
            One dict per sheet with: title, sheet_id, row_count, column_count.
        """
        audit("list_sheets", spreadsheet_id)
        try:
            meta = sheets_service.spreadsheets().get(
                spreadsheetId=spreadsheet_id, fields="sheets.properties"
            ).execute()
        except HttpError as e:
            return [{"error": f"Failed to fetch sheets: {e}"}]

        return [
            {
                "title": s["properties"]["title"],
                "sheet_id": s["properties"]["sheetId"],
                "row_count": s["properties"].get("gridProperties", {}).get("rowCount"),
                "column_count": s["properties"].get("gridProperties", {}).get("columnCount"),
            }
            for s in meta.get("sheets", [])
        ]

    @mcp.tool()
    def read_range(spreadsheet_id: str, range: str) -> list[list[Any]]:
        """Read a range of cells in A1 notation.

        Args:
            spreadsheet_id: The spreadsheet ID.
            range: A1 notation, e.g., "Sales!A1:L50" or "Sheet1!A:A" or "Sheet2".

        Returns:
            A nested list (rows of cells). Empty list if no data in range.
        """
        audit("read_range", f"{spreadsheet_id} {range}")
        try:
            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range,
                valueRenderOption="UNFORMATTED_VALUE",
            ).execute()
            return result.get("values", [])
        except HttpError as e:
            return [[f"Error: {e}"]]

    @mcp.tool()
    def append_row(spreadsheet_id: str, sheet: str, values: list[Any]) -> dict[str, Any]:
        """Append a single row to the bottom of a sheet (non-destructive).

        Args:
            spreadsheet_id: The spreadsheet ID.
            sheet: Sheet name (tab title), not a range.
            values: List of cell values for the new row.

        Returns:
            Dict with updated_range and updated_cells count.
        """
        audit("append_row", f"{spreadsheet_id} {sheet}")
        try:
            result = sheets_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=sheet,
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": [values]},
            ).execute()
            return {
                "updated_range": result.get("updates", {}).get("updatedRange"),
                "updated_cells": result.get("updates", {}).get("updatedCells"),
            }
        except HttpError as e:
            return {"error": f"Failed to append: {e}"}

    @mcp.tool()
    def update_range(spreadsheet_id: str, range: str, values: list[list[Any]]) -> dict[str, Any]:
        """Overwrite cells in a specific range (destructive within that range).

        Args:
            spreadsheet_id: The spreadsheet ID.
            range: A1 notation with row bounds (e.g., "Sheet1!A2:C10"). Whole-column ranges
                   like "Sheet1!A:Z" are refused for safety.
            values: 2D array matching the range shape.

        Returns:
            Dict with updated_range and updated_cells count.
        """
        _check_safe_range(range)
        audit("update_range", f"{spreadsheet_id} {range}")
        try:
            result = sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range,
                valueInputOption="USER_ENTERED",
                body={"values": values},
            ).execute()
            return {
                "updated_range": result.get("updatedRange"),
                "updated_cells": result.get("updatedCells"),
            }
        except HttpError as e:
            return {"error": f"Failed to update: {e}"}

    @mcp.tool()
    def get_metadata(spreadsheet_id: str) -> dict[str, Any]:
        """Return spreadsheet title, owner, last-modified time, and number of sheets."""
        audit("get_metadata", spreadsheet_id)
        try:
            file_meta = drive_service.files().get(
                fileId=spreadsheet_id,
                fields="name, owners, modifiedTime, webViewLink",
            ).execute()
            sheets_meta = sheets_service.spreadsheets().get(
                spreadsheetId=spreadsheet_id, fields="sheets.properties.title"
            ).execute()
            return {
                "title": file_meta.get("name"),
                "owners": [o.get("emailAddress") for o in file_meta.get("owners", [])],
                "modified_time": file_meta.get("modifiedTime"),
                "url": file_meta.get("webViewLink"),
                "sheets": [s["properties"]["title"] for s in sheets_meta.get("sheets", [])],
                "sheet_count": len(sheets_meta.get("sheets", [])),
            }
        except HttpError as e:
            return {"error": f"Failed to fetch metadata: {e}"}

    return mcp
