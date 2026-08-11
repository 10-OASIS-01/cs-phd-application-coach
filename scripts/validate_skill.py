#!/usr/bin/env python3
"""Validate the portable Skill package without third-party dependencies."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REQUIRED = [
    "SKILL.md",
    "agents/openai.yaml",
    "assets/dashboard/index.html",
    "assets/dashboard/app.js",
    "assets/dashboard/styles.css",
    "assets/workspace/profile.json",
    "assets/workspace/data/programs.csv",
    "assets/workspace/notes/research-narrative.md",
    "assets/workspace/notes/offer-decision.md",
    "assets/workspace/notes/wellbeing-plan.md",
    "scripts/init_application_workspace.py",
    "scripts/audit_application_workspace.py",
    "scripts/serve_application_dashboard.py",
]


def main() -> int:
    errors: list[str] = []
    skill_path = ROOT / "SKILL.md"
    text = skill_path.read_text(encoding="utf-8")
    frontmatter = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not frontmatter:
        errors.append("SKILL.md must begin with YAML frontmatter")
    else:
        lines = [line for line in frontmatter.group(1).splitlines() if line.strip()]
        keys = [line.split(":", 1)[0].strip() for line in lines if ":" in line]
        if keys != ["name", "description"]:
            errors.append("SKILL.md frontmatter must contain only name and description")
        if "name: cs-phd-application-coach" not in frontmatter.group(1):
            errors.append("Skill name must be cs-phd-application-coach")

    for relative in REQUIRED:
        if not (ROOT / relative).exists():
            errors.append(f"Missing required path: {relative}")

    for relative in re.findall(r"\]\((references/[^)]+)\)", text):
        if not (ROOT / relative).is_file():
            errors.append(f"Broken reference from SKILL.md: {relative}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Skill package is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
