"""
Outpost — the remote station where assistants can query for drift.

This is an MCP (Model Context Protocol) server that exposes drift
detection as tools. Point Claude Code or Codex at this server and
they can scan any repo for honesty.

Run with:
    python -m outpost.server
    # or
    drift serve
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add parent to path so imports work when run as module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from the_dig.strata import excavate
from the_dig.fieldnotes import FieldNotes
from lenses import ALL_LENSES
from cartography.drift_map import DriftMap
from cartography.timeline import DriftTimeline


def scan_directory(path: str, output_format: str = "markdown") -> str:
    """
    Full drift scan of a directory.

    Args:
        path: Path to the directory to scan
        output_format: "markdown" or "json"

    Returns:
        The drift report as a string
    """
    root = Path(path).resolve()
    if not root.is_dir():
        return f"Error: {path} is not a directory"

    # Excavate
    strata = list(excavate(root))

    # Prepare field notes
    notes = FieldNotes(
        files_scanned=len(set(s.path for s in strata)),
        strata_examined=len(strata),
    )

    # Apply all lenses
    for lens_cls in ALL_LENSES:
        lens = lens_cls()
        artifacts = lens.examine(strata, root)
        notes.record_many(artifacts)

    # Render
    drift_map = DriftMap(notes)
    if output_format == "json":
        return drift_map.render_json()
    return drift_map.render_markdown()


def scan_file(path: str) -> str:
    """
    Scan a single file for drift signals (comments, docstrings, TODOs).

    Args:
        path: Path to the file to scan

    Returns:
        Report of drift found in this file
    """
    file_path = Path(path).resolve()
    if not file_path.is_file():
        return f"Error: {path} is not a file"

    root = file_path.parent

    from the_dig.strata import Stratum
    content = file_path.read_text(encoding="utf-8", errors="replace")
    stratum = Stratum(
        path=file_path.relative_to(root),
        content=content,
        layer="code",
    )

    notes = FieldNotes(files_scanned=1, strata_examined=1)

    for lens_cls in ALL_LENSES:
        lens = lens_cls()
        if lens.applies_to(stratum):
            artifacts = lens.examine([stratum], root)
            notes.record_many(artifacts)

    drift_map = DriftMap(notes)
    return drift_map.render_markdown(title=f"Drift: {file_path.name}")


def get_staleness_report(path: str) -> str:
    """
    Temporal analysis: how old is the drift?

    Args:
        path: Path to the directory to analyze

    Returns:
        ASCII histogram and staleness score
    """
    root = Path(path).resolve()
    if not root.is_dir():
        return f"Error: {path} is not a directory"

    strata = list(excavate(root))
    notes = FieldNotes(
        files_scanned=len(set(s.path for s in strata)),
        strata_examined=len(strata),
    )

    for lens_cls in ALL_LENSES:
        lens = lens_cls()
        artifacts = lens.examine(strata, root)
        notes.record_many(artifacts)

    timeline = DriftTimeline(notes)
    histogram = timeline.render_ascii_histogram()
    score = timeline.staleness_score()

    return f"{histogram}\nStaleness score: {score:.2f} (0=fresh, 1=ancient)\n"


# --- MCP Server Protocol ---

TOOLS = [
    {
        "name": "drift_scan",
        "description": (
            "Scan a directory for drift — places where the codebase lies about itself. "
            "Compares READMEs vs reality, comments vs code, test names vs assertions, "
            "docstrings vs signatures, and finds abandoned TODOs."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path to scan"},
                "format": {"type": "string", "enum": ["markdown", "json"], "default": "markdown"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "drift_scan_file",
        "description": "Scan a single file for drift signals (stale comments, wrong docstrings, theater tests).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to scan"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "drift_staleness",
        "description": "Temporal analysis of drift: how old are the lies? Uses git blame to age each finding.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path to analyze"},
            },
            "required": ["path"],
        },
    },
]


def handle_tool_call(name: str, arguments: dict) -> str:
    """Route MCP tool calls to the right function."""
    if name == "drift_scan":
        return scan_directory(arguments["path"], arguments.get("format", "markdown"))
    elif name == "drift_scan_file":
        return scan_file(arguments["path"])
    elif name == "drift_staleness":
        return get_staleness_report(arguments["path"])
    else:
        return f"Unknown tool: {name}"


def run_stdio_server():
    """
    Simple MCP stdio server loop.
    Reads JSON-RPC from stdin, writes responses to stdout.
    """
    import select

    sys.stderr.write("🏕️ Drift outpost online. Listening for MCP requests...\n")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = request.get("method", "")
        req_id = request.get("id")

        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "drift", "version": "0.1.0"},
                },
            }
        elif method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": TOOLS},
            }
        elif method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            result_text = handle_tool_call(tool_name, arguments)
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": result_text}],
                },
            }
        elif method == "notifications/initialized":
            continue  # Notification, no response needed
        else:
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "scan":
        # Quick CLI mode: drift scan <path>
        target = sys.argv[2] if len(sys.argv) > 2 else "."
        fmt = sys.argv[3] if len(sys.argv) > 3 else "markdown"
        print(scan_directory(target, fmt))
    elif len(sys.argv) > 1 and sys.argv[1] == "file":
        target = sys.argv[2] if len(sys.argv) > 2 else ""
        print(scan_file(target))
    else:
        run_stdio_server()
