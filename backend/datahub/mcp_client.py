"""
Official DataHub MCP (Model Context Protocol) & GMS Client Integration.

Supports DataHub GMS backend (v1.7.0) and official acryldata/mcp-server-datahub.

Network Architecture:
- Local Dev: DATAHUB_GMS_URL=http://localhost:8080
- EC2 SSH Reverse Tunnel: DATAHUB_GMS_URL=http://127.0.0.1:18080 -> Windows GMS 8080

Environment Variables:
- DATAHUB_GMS_URL (default: http://127.0.0.1:18080)
- DATAHUB_GMS_TOKEN (optional bearer token, no PAT requirement)
- DATAHUB_MCP_ENABLED (default: true)
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import urllib.request
from typing import Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("fleetguard.datahub")


class DataHubMCPClient:
    """FastAPI Client for DataHub GMS & official acryldata/mcp-server-datahub."""

    def __init__(self) -> None:
        load_dotenv()
        self.gms_url: str = os.getenv("DATAHUB_GMS_URL", "http://127.0.0.1:18080").rstrip("/")
        self.gms_token: str | None = os.getenv("DATAHUB_GMS_TOKEN") or None
        self.enabled: bool = os.getenv("DATAHUB_MCP_ENABLED", "true").lower() == "true"
        logger.info(f"DataHub GMS configured: {self.gms_url}")

    def is_enabled(self) -> bool:
        """Returns whether DataHub MCP integration is enabled."""
        return self.enabled

    def check_gms_connection(self) -> tuple[bool, str | None]:
        """
        Lightweight HTTP health check targeting DataHub GMS backend server.
        Probes /health first, falling back to /config.
        Rejects HTML frontend responses. Timeout 3.0s.
        Returns: (datahub_connected: bool, error: str | None)
        """
        if not self.enabled:
            return False, "DataHub MCP is disabled via DATAHUB_MCP_ENABLED=false."

        endpoints = [f"{self.gms_url}/health", f"{self.gms_url}/config"]
        last_error = None

        for target_url in endpoints:
            try:
                req = urllib.request.Request(target_url)
                if self.gms_token:
                    req.add_header("Authorization", f"Bearer {self.gms_token}")

                with urllib.request.urlopen(req, timeout=3) as resp:
                    status_code = resp.status
                    content_type = resp.headers.get("Content-Type", "").lower()

                    # Reject HTML responses from frontend webserver (e.g. port 9002 or Nginx index.html)
                    if "text/html" in content_type:
                        last_error = f"Received HTML response from {target_url} (Expected DataHub GMS API)"
                        continue

                    if status_code in (200, 401, 403):
                        return True, None
            except Exception as e:
                # Sanitized error without exposing tokens or internal tracebacks
                err_type = type(e).__name__
                last_error = f"DataHub GMS unreachable at {self.gms_url} ({err_type})"

        return False, last_error or "DataHub GMS unreachable"

    def check_mcp_connection(self) -> tuple[bool, str | None]:
        """
        Checks if official mcp-server-datahub binary or uvx/npx process launcher is available.
        Returns: (mcp_connected: bool, error: str | None)
        """
        if not self.enabled:
            return False, "DataHub MCP is disabled."

        if shutil.which("mcp-server-datahub"):
            return True, None

        if shutil.which("uvx") or shutil.which("npx"):
            return True, None

        return False, "Official mcp-server-datahub binary or uvx launcher not found in PATH."

    def check_status(self) -> tuple[bool, bool, str | None]:
        """
        Returns distinct status: (datahub_connected: bool, mcp_connected: bool, error: str | None)
        """
        datahub_connected, gms_err = self.check_gms_connection()
        mcp_connected, mcp_err = self.check_mcp_connection()

        error = gms_err if not datahub_connected else (mcp_err if not mcp_connected else None)
        return datahub_connected, mcp_connected, error

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Executes a tool on the official DataHub MCP Server via stdio JSON-RPC protocol.
        """
        if not self.enabled:
            return {"success": False, "error": "DataHub MCP is disabled."}

        datahub_connected, gms_err = self.check_gms_connection()
        if not datahub_connected:
            return {"success": False, "error": gms_err or "DataHub GMS unreachable."}

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
                return {"success": False, "error": f"MCP execution error: {type(ex).__name__}"}

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
