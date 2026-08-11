#!/usr/bin/env python3
"""Create a portable PhD application workspace from bundled templates."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a local Markdown/CSV/JSON PhD application workspace."
    )
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--cycle", required=True, help="Target intake year or cycle label")
    parser.add_argument("--name", default="", help="Applicant name; optional")
    parser.add_argument(
        "--timezone",
        default="",
        help="Applicant IANA time zone, for example Asia/Shanghai",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow bundled template files to replace files with the same names",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    skill_root = Path(__file__).resolve().parent.parent
    template_dir = skill_root / "assets" / "workspace"
    destination = args.destination.expanduser().resolve()

    if not template_dir.is_dir():
        print(f"ERROR: bundled workspace templates not found: {template_dir}", file=sys.stderr)
        return 2

    if destination.exists() and any(destination.iterdir()) and not args.force:
        print(
            f"ERROR: destination is not empty: {destination}\n"
            "Choose an empty directory or pass --force after reviewing existing files.",
            file=sys.stderr,
        )
        return 2

    destination.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    replaced: list[str] = []

    for source in sorted(template_dir.iterdir()):
        target = destination / source.name
        existed = target.exists()
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=args.force)
        else:
            if existed and not args.force:
                print(f"ERROR: refusing to overwrite {target}", file=sys.stderr)
                return 2
            shutil.copy2(source, target)
        (replaced if existed else created).append(source.name)

    profile_path = destination / "profile.json"
    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: could not read generated profile: {exc}", file=sys.stderr)
        return 2

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    profile.update(
        {
            "applicant_name": args.name,
            "cycle": str(args.cycle),
            "home_timezone": args.timezone,
            "created_at": profile.get("created_at") or now,
            "updated_at": now,
        }
    )
    profile_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Created application workspace: {destination}")
    print(f"Cycle: {args.cycle}")
    print(f"New files: {', '.join(created) if created else 'none'}")
    if replaced:
        print(f"Replaced files: {', '.join(replaced)}")
    print("Next: complete profile.json, add programs, then run audit_application_workspace.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
