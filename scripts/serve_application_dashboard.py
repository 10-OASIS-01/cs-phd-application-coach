#!/usr/bin/env python3
"""Serve a private local dashboard backed by the application workspace files."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import tempfile
import threading
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


TABLES = {
    "programs": "programs.csv",
    "faculty": "faculty.csv",
    "materials": "materials.csv",
    "recommenders": "recommenders.csv",
    "tasks": "tasks.csv",
    "contacts": "contacts.csv",
    "interviews": "interviews.csv",
    "offers": "offers.csv",
}
NOTES = {
    "research-narrative": "research-narrative.md",
    "offer-decision": "offer-decision.md",
    "wellbeing-plan": "wellbeing-plan.md",
}
MAX_BODY_BYTES = 2 * 1024 * 1024


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a local visual dashboard for a PhD application workspace."
    )
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-open", action="store_true", help="Do not open a browser tab")
    return parser.parse_args()


def read_table(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = [{field: (row.get(field) or "") for field in fields} for row in reader]
    return fields, rows


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False, newline=""
    ) as handle:
        handle.write(content)
        temp_path = Path(handle.name)
    temp_path.replace(path)


def create_backup(workspace: Path, source: Path) -> None:
    if not source.exists():
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    relative = source.relative_to(workspace)
    target = workspace / "archive" / "dashboard-backups" / stamp / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def build_handler(workspace: Path, dashboard_dir: Path, expected_origin: str):
    class DashboardHandler(SimpleHTTPRequestHandler):
        server_version = "PhDApplicationDashboard/1.0"

        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(dashboard_dir), **kwargs)

        def log_message(self, format_string: str, *args) -> None:
            sys.stderr.write("dashboard: " + (format_string % args) + "\n")

        def end_headers(self) -> None:
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cache-Control", "no-store")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'",
            )
            super().end_headers()

        def send_json(self, payload, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def send_error_json(self, status: HTTPStatus, message: str) -> None:
            self.send_json({"error": message}, status)

        def read_json_body(self):
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                raise ValueError("Invalid Content-Length")
            if length <= 0 or length > MAX_BODY_BYTES:
                raise ValueError("Request body must be between 1 byte and 2 MiB")
            raw = self.rfile.read(length)
            try:
                return json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError(f"Invalid JSON: {exc}") from exc

        def valid_write_origin(self) -> bool:
            origin = self.headers.get("Origin")
            return origin is None or origin == expected_origin

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/api/state":
                try:
                    profile = json.loads((workspace / "profile.json").read_text(encoding="utf-8"))
                    tables = {}
                    for name, filename in TABLES.items():
                        fields, rows = read_table(workspace / "data" / filename)
                        tables[name] = {"fields": fields, "rows": rows}
                    notes = {
                        name: (workspace / "notes" / filename).read_text(encoding="utf-8")
                        for name, filename in NOTES.items()
                    }
                    self.send_json({"profile": profile, "tables": tables, "notes": notes})
                except (OSError, csv.Error, json.JSONDecodeError) as exc:
                    self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
                return
            if parsed.path == "/api/health":
                self.send_json({"ok": True, "workspace": str(workspace)})
                return
            if parsed.path == "/":
                self.path = "/index.html"
            super().do_GET()

        def do_PUT(self) -> None:
            if not self.valid_write_origin():
                self.send_error_json(HTTPStatus.FORBIDDEN, "Write origin is not the local dashboard")
                return
            parsed = urlparse(self.path)
            try:
                payload = self.read_json_body()
                if parsed.path == "/api/profile":
                    if not isinstance(payload, dict):
                        raise ValueError("Profile must be a JSON object")
                    target = workspace / "profile.json"
                    create_backup(workspace, target)
                    payload["updated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
                    atomic_write_text(target, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
                    self.send_json({"ok": True, "profile": payload})
                    return

                table_prefix = "/api/table/"
                if parsed.path.startswith(table_prefix):
                    name = parsed.path[len(table_prefix) :]
                    if name not in TABLES:
                        self.send_error_json(HTTPStatus.NOT_FOUND, "Unknown table")
                        return
                    rows = payload.get("rows") if isinstance(payload, dict) else None
                    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
                        raise ValueError("Table payload must contain a rows array of objects")
                    target = workspace / "data" / TABLES[name]
                    fields, _ = read_table(target)
                    for row in rows:
                        unknown = set(row) - set(fields)
                        if unknown:
                            raise ValueError(f"Unknown fields for {name}: {', '.join(sorted(unknown))}")
                    create_backup(workspace, target)
                    with tempfile.NamedTemporaryFile(
                        "w", encoding="utf-8", dir=target.parent, delete=False, newline=""
                    ) as handle:
                        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
                        writer.writeheader()
                        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
                        temp_path = Path(handle.name)
                    temp_path.replace(target)
                    self.send_json({"ok": True, "rows": rows})
                    return

                note_prefix = "/api/note/"
                if parsed.path.startswith(note_prefix):
                    name = parsed.path[len(note_prefix) :]
                    if name not in NOTES:
                        self.send_error_json(HTTPStatus.NOT_FOUND, "Unknown note")
                        return
                    content = payload.get("content") if isinstance(payload, dict) else None
                    if not isinstance(content, str):
                        raise ValueError("Note payload must contain string content")
                    target = workspace / "notes" / NOTES[name]
                    create_backup(workspace, target)
                    atomic_write_text(target, content)
                    self.send_json({"ok": True, "content": content})
                    return

                self.send_error_json(HTTPStatus.NOT_FOUND, "Unknown API route")
            except ValueError as exc:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
            except (OSError, csv.Error, json.JSONDecodeError) as exc:
                self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    return DashboardHandler


def main() -> int:
    args = parse_args()
    workspace = args.workspace.expanduser().resolve()
    skill_root = Path(__file__).resolve().parent.parent
    dashboard_dir = skill_root / "assets" / "dashboard"

    required = [workspace / "profile.json", workspace / "data" / "programs.csv", dashboard_dir / "index.html"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        print("ERROR: required dashboard files are missing:\n- " + "\n- ".join(missing), file=sys.stderr)
        return 2
    if not 1 <= args.port <= 65535:
        print("ERROR: port must be between 1 and 65535", file=sys.stderr)
        return 2
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        print(
            "WARNING: the dashboard contains private application data and is not bound to loopback.",
            file=sys.stderr,
        )

    display_host = "127.0.0.1" if args.host in {"localhost", "::1"} else args.host
    origin = f"http://{display_host}:{args.port}"
    server = ThreadingHTTPServer((args.host, args.port), build_handler(workspace, dashboard_dir, origin))
    print(f"Application dashboard: {origin}")
    print(f"Workspace: {workspace}")
    print("Press Ctrl-C to stop. Data stays in the workspace folder.")

    if not args.no_open:
        threading.Timer(0.4, lambda: webbrowser.open(origin)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
