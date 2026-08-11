#!/usr/bin/env python3
"""Audit a portable PhD application workspace for common planning risks."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass
class Finding:
    severity: str
    file: str
    row: str
    message: str


EXPECTED_FIELDS = {
    "programs.csv": {
        "program_id",
        "institution",
        "program",
        "official_url",
        "deadline_date",
        "deadline_timezone",
        "verification_status",
        "last_checked",
        "status",
    },
    "faculty.csv": {
        "faculty_id",
        "program_id",
        "faculty_name",
        "profile_url",
        "authoritative_url",
        "last_checked",
    },
    "materials.csv": {
        "material_id",
        "program_id",
        "document_type",
        "authoritative_url",
        "last_checked",
        "status",
        "deadline_date",
    },
    "recommenders.csv": {
        "recommender_id",
        "recommender_name",
        "strong_letter_confirmed",
        "next_reminder_date",
        "status",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit a PhD application workspace.")
    parser.add_argument("workspace", type=Path)
    parser.add_argument(
        "--today",
        type=date.fromisoformat,
        default=date.today(),
        help="Audit date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--stale-days",
        type=int,
        default=45,
        help="Warn when a changing fact has not been checked within this many days",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser.parse_args()


def read_csv(path: Path, findings: list[Finding]) -> list[dict[str, str]]:
    if not path.exists():
        findings.append(Finding("error", path.name, "-", "Required file is missing"))
        return []
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or [])
            missing = EXPECTED_FIELDS.get(path.name, set()) - fields
            if missing:
                findings.append(
                    Finding("error", path.name, "header", f"Missing fields: {', '.join(sorted(missing))}")
                )
            return [{key: (value or "").strip() for key, value in row.items()} for row in reader]
    except (OSError, csv.Error) as exc:
        findings.append(Finding("error", path.name, "-", f"Could not read CSV: {exc}"))
        return []


def valid_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def parse_optional_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def check_source(
    findings: list[Finding], file_name: str, row_id: str, row: dict[str, str], today: date, stale_days: int
) -> None:
    source = row.get("authoritative_url") or row.get("official_url") or ""
    if not source:
        findings.append(Finding("warning", file_name, row_id, "Missing authoritative URL"))
    elif not valid_http_url(source):
        findings.append(Finding("error", file_name, row_id, f"Invalid authoritative URL: {source}"))

    checked_raw = row.get("last_checked", "")
    checked = parse_optional_date(checked_raw)
    if not checked_raw:
        findings.append(Finding("warning", file_name, row_id, "Missing last_checked date"))
    elif checked is None:
        findings.append(Finding("error", file_name, row_id, "last_checked must use YYYY-MM-DD"))
    elif checked > today:
        findings.append(Finding("error", file_name, row_id, "last_checked is in the future"))
    elif (today - checked).days > stale_days:
        findings.append(
            Finding("warning", file_name, row_id, f"Source check is {(today - checked).days} days old")
        )


def check_deadline(
    findings: list[Finding], file_name: str, row_id: str, row: dict[str, str], today: date
) -> date | None:
    raw = row.get("deadline_date", "")
    if not raw:
        findings.append(Finding("warning", file_name, row_id, "Missing deadline date"))
        return None
    deadline = parse_optional_date(raw)
    if deadline is None:
        findings.append(Finding("error", file_name, row_id, "deadline_date must use YYYY-MM-DD"))
        return None

    timezone_name = row.get("deadline_timezone", "")
    if not timezone_name:
        findings.append(Finding("warning", file_name, row_id, "Missing deadline time zone"))
    else:
        try:
            ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            findings.append(Finding("error", file_name, row_id, f"Unknown IANA time zone: {timezone_name}"))

    days = (deadline - today).days
    status = row.get("status", "").lower()
    if days < 0 and status not in {"submitted", "complete", "withdrawn", "declined"}:
        findings.append(Finding("warning", file_name, row_id, f"Deadline passed {abs(days)} days ago"))
    elif 0 <= days <= 14 and status not in {"submitted", "complete", "withdrawn", "declined"}:
        findings.append(Finding("warning", file_name, row_id, f"Deadline is in {days} days"))
    return deadline


def main() -> int:
    args = parse_args()
    workspace = args.workspace.expanduser().resolve()
    findings: list[Finding] = []

    if not workspace.is_dir():
        print(f"ERROR: workspace is not a directory: {workspace}", file=sys.stderr)
        return 2

    profile_path = workspace / "profile.json"
    if not profile_path.exists():
        findings.append(Finding("error", "profile.json", "-", "Required file is missing"))
    else:
        try:
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            if not profile.get("cycle"):
                findings.append(Finding("warning", "profile.json", "cycle", "Target cycle is empty"))
            zone = profile.get("home_timezone", "")
            if zone:
                try:
                    ZoneInfo(zone)
                except ZoneInfoNotFoundError:
                    findings.append(Finding("error", "profile.json", "home_timezone", "Unknown IANA time zone"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append(Finding("error", "profile.json", "-", f"Invalid JSON: {exc}"))

    data_dir = workspace / "data"
    programs = read_csv(data_dir / "programs.csv", findings)
    program_ids: set[str] = set()
    program_deadlines: dict[str, date] = {}
    for index, row in enumerate(programs, start=2):
        row_id = row.get("program_id") or f"line {index}"
        if not row.get("program_id"):
            findings.append(Finding("error", "programs.csv", row_id, "program_id is required"))
        elif row["program_id"] in program_ids:
            findings.append(Finding("error", "programs.csv", row_id, "Duplicate program_id"))
        else:
            program_ids.add(row["program_id"])
        if not row.get("institution") or not row.get("program"):
            findings.append(Finding("error", "programs.csv", row_id, "Institution and program are required"))
        if not row.get("verification_status"):
            findings.append(Finding("warning", "programs.csv", row_id, "Missing verification status"))
        check_source(findings, "programs.csv", row_id, row, args.today, args.stale_days)
        deadline = check_deadline(findings, "programs.csv", row_id, row, args.today)
        if deadline and row.get("program_id"):
            program_deadlines[row["program_id"]] = deadline

    faculty = read_csv(data_dir / "faculty.csv", findings)
    faculty_per_program: dict[str, int] = {}
    for index, row in enumerate(faculty, start=2):
        row_id = row.get("faculty_id") or f"line {index}"
        program_id = row.get("program_id", "")
        if program_id and program_id not in program_ids:
            findings.append(Finding("error", "faculty.csv", row_id, f"Unknown program_id: {program_id}"))
        if program_id:
            faculty_per_program[program_id] = faculty_per_program.get(program_id, 0) + 1
        if not row.get("faculty_name"):
            findings.append(Finding("error", "faculty.csv", row_id, "faculty_name is required"))
        check_source(findings, "faculty.csv", row_id, row, args.today, args.stale_days)

    for program_id in sorted(program_ids):
        count = faculty_per_program.get(program_id, 0)
        if count < 2:
            findings.append(
                Finding(
                    "warning",
                    "faculty.csv",
                    program_id,
                    f"Only {count} plausible faculty match(es); verify rotations, co-advising, or single-advisor risk",
                )
            )

    materials = read_csv(data_dir / "materials.csv", findings)
    for index, row in enumerate(materials, start=2):
        row_id = row.get("material_id") or f"line {index}"
        program_id = row.get("program_id", "")
        if program_id and program_id not in program_ids:
            findings.append(Finding("error", "materials.csv", row_id, f"Unknown program_id: {program_id}"))
        if not row.get("document_type"):
            findings.append(Finding("error", "materials.csv", row_id, "document_type is required"))
        check_source(findings, "materials.csv", row_id, row, args.today, args.stale_days)
        deadline = check_deadline(findings, "materials.csv", row_id, row, args.today)
        if deadline and 0 <= (deadline - args.today).days <= 14 and row.get("status", "").lower() not in {
            "final",
            "submitted",
            "complete",
        }:
            findings.append(Finding("warning", "materials.csv", row_id, "Material is not final near deadline"))

    recommenders = read_csv(data_dir / "recommenders.csv", findings)
    for index, row in enumerate(recommenders, start=2):
        row_id = row.get("recommender_id") or f"line {index}"
        strong = row.get("strong_letter_confirmed", "").lower()
        if strong not in {"yes", "true", "confirmed"}:
            findings.append(Finding("warning", "recommenders.csv", row_id, "Strong letter is not confirmed"))
        reminder_raw = row.get("next_reminder_date", "")
        reminder = parse_optional_date(reminder_raw)
        if reminder_raw and reminder is None:
            findings.append(Finding("error", "recommenders.csv", row_id, "next_reminder_date must use YYYY-MM-DD"))
        elif reminder and reminder < args.today and row.get("status", "").lower() not in {"submitted", "complete"}:
            findings.append(Finding("warning", "recommenders.csv", row_id, "Letter reminder is overdue"))

    counts = {
        "programs": len(programs),
        "faculty": len(faculty),
        "materials": len(materials),
        "recommenders": len(recommenders),
        "errors": sum(item.severity == "error" for item in findings),
        "warnings": sum(item.severity == "warning" for item in findings),
    }

    if args.json:
        print(json.dumps({"workspace": str(workspace), "today": str(args.today), "counts": counts, "findings": [asdict(item) for item in findings]}, indent=2))
    else:
        print(f"Application workspace audit: {workspace}")
        print(
            f"Programs {counts['programs']} | Faculty {counts['faculty']} | "
            f"Materials {counts['materials']} | Recommenders {counts['recommenders']}"
        )
        if findings:
            for item in findings:
                print(f"{item.severity.upper():7} {item.file}:{item.row} — {item.message}")
        else:
            print("No audit findings.")
        print(f"Summary: {counts['errors']} error(s), {counts['warnings']} warning(s)")

    return 1 if counts["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
