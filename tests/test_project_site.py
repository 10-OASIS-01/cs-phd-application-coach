import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
PROJECT_URL = "https://10-oasis-01.github.io/cs-phd-application-coach/"


class ProjectSiteTests(unittest.TestCase):
    def setUp(self):
        self.html = (SITE / "index.html").read_text(encoding="utf-8")

    def test_project_metadata_targets_repository_pages_site(self):
        self.assertIn(f'<link rel="canonical" href="{PROJECT_URL}"', self.html)
        self.assertIn(f'<meta property="og:url" content="{PROJECT_URL}"', self.html)
        self.assertIn(f'{PROJECT_URL}assets/cs-phd-application-coach-card.png', self.html)
        self.assertNotIn("/skills/cs-phd-application-coach/", self.html)

        match = re.search(
            r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>',
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        structured_data = json.loads(match.group(1))
        self.assertEqual(structured_data["@type"], "SoftwareSourceCode")
        self.assertEqual(structured_data["url"], PROJECT_URL)
        self.assertEqual(
            structured_data["codeRepository"],
            "https://github.com/10-OASIS-01/cs-phd-application-coach",
        )

    def test_site_contains_required_assets_and_actions(self):
        for relative_path in [
            "styles.css",
            "app.js",
            ".nojekyll",
            "robots.txt",
            "sitemap.xml",
            "assets/cs-phd-application-coach-card.png",
        ]:
            self.assertTrue((SITE / relative_path).is_file(), relative_path)

        self.assertIn("ghbtns.com/github-btn.html", self.html)
        self.assertIn("~/.agents/skills/cs-phd-application-coach", self.html)
        self.assertIn("~/.claude/skills/cs-phd-application-coach", self.html)


if __name__ == "__main__":
    unittest.main()
