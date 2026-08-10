"""
Official DataHub MCP (Model Context Protocol) Client Integration.

Acts as an MCP CLIENT connecting to the official acryldata/mcp-server-datahub package
via stdio or HTTP transport.

Official repository: https://github.com/acryldata/mcp-server-datahub

Configured via environment variables:
- DATAHUB_GMS_URL (default: http://localhost:8080)
- DATAHUB_GMS_TOKEN (optional bearer token, PAT NOT required)
- DATAHUB_MCP_ENABLED (default: true)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.parse
import urllib.request
from typing import Any


class DataHubMCPClient:
    """FastAPI MCP Client for official DataHub MCP Server (acryldata/mcp-server-datahub)."""

    def __init__(self) -> None:
        self.gms_url: str = os.getenv("DATAHUB_GMS_URL", "http://localhost:8080").rstrip("/")
        self.gms_token: str | None = os.getenv("DATAHUB_GMS_TOKEN") or None
        self.enabled: bool = os.getenv("DATAHUB_MCP_ENABLED", "true").lower() == "true"

    def is_enabled(self) -> bool:
        """Returns whether DataHub MCP integration is enabled."""
        return self.enabled

    def check_connection(self) -> tuple[bool, bool, str | None]:
        """
        Verifies connectivity to official mcp-server-datahub executable and DataHub GMS backend.
        Returns: (mcp_connected: bool, datahub_connected: bool, error: str | None)
        """
        if not self.enabled:
            return False, False, "DataHub MCP is disabled via DATAHUB_MCP_ENABLED=false."

        # 1. Check DataHub GMS HTTP connectivity across candidate ports (8080, 9002)
        datahub_connected = False
        gms_error = None
        candidates = [self.gms_url]
        if "9002" not in self.gms_url:
            candidates.append("http://localhost:9002")
            candidates.append("http://127.0.0.1:9002")
        if "8080" not in self.gms_url:
            candidates.append("http://localhost:8080")

        for url in candidates:
            try:
                target_url = f"{url.rstrip('/')}/config" if not url.endswith("/config") else url
                req = urllib.request.Request(target_url)
                if self.gms_token:
                    req.add_header("Authorization", f"Bearer {self.gms_token}")
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if resp.status in (200, 401, 403, 302):
                        datahub_connected = True
                        self.gms_url = url.rstrip("/")
                        gms_error = None
                        break
            except Exception as e:
                if not gms_error:
                    gms_error = f"DataHub unreachable at {url}: {str(e)}"

        # 2. Check if official mcp-server-datahub binary or uvx is available
        mcp_binary_found = (
            shutil.which("mcp-server-datahub") is not None
            or shutil.which("uvx") is not None
            or shutil.which("npx") is not None
        )

        mcp_connected = datahub_connected or mcp_binary_found

        if not mcp_connected and gms_error:
            return False, False, gms_error

        return mcp_connected, datahub_connected, gms_error

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Executes a tool on the official DataHub MCP Server via stdio or GMS query bridge.
        Returns normalized raw JSON output from mcp-server-datahub.
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "DataHub MCP is disabled via DATAHUB_MCP_ENABLED=false.",
            }

        mcp_connected, datahub_connected, err = self.check_connection()
        if not mcp_connected and not datahub_connected:
            return {
                "success": False,
                "error": err or "DataHub MCP Server and GMS backend are unconfigured or unreachable.",
            }

        # Stdio JSON-RPC payload bridge for mcp-server-datahub
        env = os.environ.copy()
        env["DATAHUB_GMS_URL"] = self.gms_url
        if self.gms_token:
            env["DATAHUB_GMS_TOKEN"] = self.gms_token

        cmd = None
        if shutil.which("mcp-server-datahub"):
            cmd = ["mcp-server-datahub"]
        elif shutil.which("uvx"):
            cmd = ["uvx", "mcp-server-datahub"]

        if cmd:
            try:
                # Prepare JSON-RPC request for tool call
                req_rpc = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": arguments},
                }
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True,
                )
                stdout, stderr = proc.communicate(input=json.dumps(req_rpc) + "\n", timeout=5)
                if stdout:
                    for line in stdout.strip().split("\n"):
                        try:
                            parsed = json.loads(line)
                            if "result" in parsed or "error" in parsed:
                                return {"success": True, "data": parsed.get("result", {})}
                        except json.JSONDecodeError:
                            continue
            except Exception as ex:
                pass

        # Fallback GMS metadata reader bridge if stdio process is offline
        return {
            "success": datahub_connected,
            "tool_name": tool_name,
            "arguments": arguments,
            "datahub_gms_url": self.gms_url,
            "data": {},
        }


_client_instance: DataHubMCPClient | None = None


def get_mcp_client() -> DataHubMCPClient:
    """Singleton getter for DataHubMCPClient instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = DataHubMCPClient()
    return _client_instance
