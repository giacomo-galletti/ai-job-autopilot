"""Guards for the /onboard command spec (and the /setup alias).

The command is a markdown spec, so the spec is the implementation. These tests pin the
invariants that matter: privacy (profile/ only), the portal-selection step, the file names
other workflows read, and that onboarding is runtime-neutral (Claude Code and Codex).
"""
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ONBOARD = REPO / ".claude" / "commands" / "onboard.md"
SETUP = REPO / ".claude" / "commands" / "setup.md"
AGENTS_SKILLS = REPO / ".agents" / "skills"

PROFILE_FILES = [
    "profile.md", "behavioral.md", "forms.md", "deal-breakers.md",
    "portals.md", "search-queries.md", "cv_content.py", "theme.json",
]
SECTIONS = ["identity", "experience", "behavioral", "deal-breakers", "portals",
            "search", "template", "theme", "gmail", "forms"]


def steps(text):
    return {m.group(1): m.group(2) for m in re.finditer(r"^## (Step \d+[^\n]*)\n(.*?)(?=^## |\Z)", text, re.S | re.M)}


class OnboardSpec(unittest.TestCase):
    def setUp(self):
        self.text = ONBOARD.read_text(encoding="utf-8")
        self.steps = steps(self.text)

    def test_steps_present_in_order(self):
        names = list(self.steps)
        for i, kw in enumerate(["Preflight", "Intake", "Write the profile", "Portal selection",
                                "Template and theme", "Standing rules", "Gmail", "Form-answer", "Dry-run", "Finish"], 1):
            self.assertIn(kw, names[i - 1], names)

    def test_three_intake_paths(self):
        intake = next(b for k, b in self.steps.items() if "Intake" in k)
        for p in ("Path A", "Path B", "Path C"):
            self.assertIn(p, intake)

    def test_every_profile_file_is_named(self):
        for f in PROFILE_FILES:
            self.assertIn(f"`{f}`", self.text, f)

    def test_section_mode_documents_every_section(self):
        for s in SECTIONS:
            self.assertIn(f"`{s}`", self.text, s)
        self.assertIn("--section", self.text)

    def test_privacy_rule_checks_gitignore(self):
        self.assertIn("git check-ignore profile/", self.text)

    def test_preflight_uses_requirements_file(self):
        self.assertIn("requirements.txt", self.text)
        self.assertTrue((REPO / "requirements.txt").exists())

    def test_no_claude_only_assumptions(self):
        self.assertIn("Codex", self.text)
        for banned in ("AskUserQuestion", "TodoWrite", "mcp__"):
            self.assertNotIn(banned, self.text)


class PortalSelection(unittest.TestCase):
    def setUp(self):
        self.text = ONBOARD.read_text(encoding="utf-8")
        self.portal = next(b for k, b in steps(self.text).items() if "Portal selection" in k)

    def test_covers_all_three_tiers(self):
        for kw in ("Global tier", "Country tier", "niche boards"):
            self.assertIn(kw, self.portal)

    def test_inputs_named(self):
        for kw in ("role family", "seniority", "remote", "languages"):
            self.assertIn(kw, self.portal)

    def test_robots_check_and_add_portal_handoff(self):
        self.assertIn("tools/robots_check.py", self.portal)
        self.assertIn("/add-portal", self.portal)

    def test_decision_table_present(self):
        self.assertIn("Decision table", self.portal)

    def test_writes_portals_and_search_queries(self):
        self.assertIn("profile/portals.md", self.portal)
        self.assertIn("profile/search-queries.md", self.portal)
        self.assertIn("tools/low_cost_markets.py", self.portal)

    def test_denmark_clis_not_default(self):
        self.assertRegex(self.portal, r"Denmark[^\n]*Not default")

    def test_every_bundled_cli_mentioned_exists(self):
        for name in re.findall(r"`([a-z]+-search)`", self.portal):
            self.assertTrue((AGENTS_SKILLS / name / "SKILL.md").exists(), name)


class SetupAlias(unittest.TestCase):
    def test_setup_points_to_onboard(self):
        text = SETUP.read_text(encoding="utf-8")
        self.assertIn("onboard.md", text)
        self.assertLess(len(text.splitlines()), 10)


class NoPersonalLeaks(unittest.TestCase):
    def test_command_files_are_generic(self):
        pat = re.compile("|".join(["gia"+"como", "gal"+"letti", "mad"+"real", "fer"+"rara", "/Us"+"ers/"]), re.I)
        for p in (ONBOARD, SETUP, REPO / ".claude" / "commands" / "reset.md",
                  REPO / ".claude" / "commands" / "add-portal.md"):
            self.assertIsNone(pat.search(p.read_text(encoding="utf-8")), p.name)


if __name__ == "__main__":
    unittest.main()
