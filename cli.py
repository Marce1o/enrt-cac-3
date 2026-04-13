"""
drift — the CLI entry point.

Usage:
    drift scan [path] [--format=markdown|json]
    drift file <path>
    drift staleness [path]
    drift serve
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure the project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    parser = argparse.ArgumentParser(
        prog="drift",
        description="Find where your codebase lies about itself.",
    )
    sub = parser.add_subparsers(dest="command")

    # scan
    scan_p = sub.add_parser("scan", help="Full drift scan of a directory")
    scan_p.add_argument("path", nargs="?", default=".", help="Directory to scan")
    scan_p.add_argument("--format", choices=["markdown", "json"], default="markdown")

    # file
    file_p = sub.add_parser("file", help="Scan a single file")
    file_p.add_argument("path", help="File to scan")

    # staleness
    stale_p = sub.add_parser("staleness", help="Temporal drift analysis")
    stale_p.add_argument("path", nargs="?", default=".", help="Directory to analyze")

    # serve
    sub.add_parser("serve", help="Start MCP server for assistant integration")

    args = parser.parse_args()

    if args.command == "scan":
        from outpost.server import scan_directory
        print(scan_directory(args.path, args.format))

    elif args.command == "file":
        from outpost.server import scan_file
        print(scan_file(args.path))

    elif args.command == "staleness":
        from outpost.server import get_staleness_report
        print(get_staleness_report(args.path))

    elif args.command == "serve":
        from outpost.server import run_stdio_server
        run_stdio_server()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
