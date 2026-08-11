from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


class WorkspaceTests(unittest.TestCase):
    def test_initialize_and_audit_empty_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "cycle"
            created = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "init_application_workspace.py"),
                    "--destination",
                    str(workspace),
                    "--cycle",
                    "2027",
                    "--timezone",
                    "Asia/Shanghai",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("Created application workspace", created.stdout)
            profile = json.loads((workspace / "profile.json").read_text(encoding="utf-8"))
            self.assertEqual(profile["cycle"], "2027")
            self.assertEqual(profile["home_timezone"], "Asia/Shanghai")
            self.assertTrue((workspace / "notes" / "offer-decision.md").exists())

            repeated = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "init_application_workspace.py"),
                    "--destination",
                    str(workspace),
                    "--cycle",
                    "2027",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(repeated.returncode, 2)

            audit = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "audit_application_workspace.py"),
                    str(workspace),
                    "--today",
                    "2026-08-12",
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            report = json.loads(audit.stdout)
            self.assertEqual(report["counts"]["errors"], 0)

    def test_audit_finds_duplicate_and_unverified_programs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "cycle"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "init_application_workspace.py"),
                    "--destination",
                    str(workspace),
                    "--cycle",
                    "2027",
                ],
                check=True,
                capture_output=True,
            )
            programs_path = workspace / "data" / "programs.csv"
            with programs_path.open(newline="", encoding="utf-8") as handle:
                fields = next(csv.reader(handle))
            rows = []
            for institution in ("Sample A", "Sample B"):
                row = {field: "" for field in fields}
                row.update(
                    {
                        "program_id": "duplicate",
                        "institution": institution,
                        "program": "CS PhD",
                        "official_url": "not-a-url",
                        "deadline_date": "2026-08-20",
                        "deadline_timezone": "Mars/Olympus",
                        "status": "researching",
                        "last_checked": "2026-01-01",
                    }
                )
                rows.append(row)
            with programs_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)

            audit = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "audit_application_workspace.py"),
                    str(workspace),
                    "--today",
                    "2026-08-12",
                    "--json",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(audit.returncode, 1)
            messages = [finding["message"] for finding in json.loads(audit.stdout)["findings"]]
            self.assertIn("Duplicate program_id", messages)
            self.assertIn("Missing verification status", messages)
            self.assertIn("Unknown IANA time zone: Mars/Olympus", messages)


if __name__ == "__main__":
    unittest.main()
