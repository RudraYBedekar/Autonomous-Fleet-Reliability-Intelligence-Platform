"""
DataHub GMS & MCP Connection Diagnostic Script.

Usage:
    python -m backend.datahub.check_connection

Prints concise connectivity status without exposing tokens or secrets.
"""

from __future__ import annotations

import sys
from backend.datahub.context_service import get_status


def main() -> None:
    """Executes DataHub connection health diagnostic."""
    status = get_status()
    print(f"DataHub GMS URL: {status.datahub_gms_url}")
    print(f"Connected: {str(status.datahub_connected).lower()}")
    print(f"MCP Connected: {str(status.mcp_connected).lower()}")

    if status.error:
        print(f"Error: {status.error}")

    sys.exit(0 if status.datahub_connected else 1)


if __name__ == "__main__":
    main()
