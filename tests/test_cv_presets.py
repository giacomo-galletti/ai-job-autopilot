"""reorder() in the CV presets: a per-application override must build on the preset.

template.py teaches "The preset already ordered each job's sentences. Override a single
job", so a module that imports a preset and overrides one job keeps every other job as
the preset left it. reorder() used to rebuild from content_base alone, which silently put
the master wording back (a tailored CV regained a line the designer preset drops).
"""
import os
import sys
import unittest
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / "templates/cv/designed"
sys.path.insert(0, str(TEMPLATE))
# The presets are written for the example content; ignore any profile/cv_content.py.
os.environ["JOB_KIT_EXAMPLE_CONTENT"] = "1"

DEVELOPER_LINE = "It's the project that turned me into a developer."


def application_module(body):
    """Run `body` the way build.py runs a per-application content module."""
    namespace = {"__name__": "cv_application_fixture"}
    exec(body, namespace)
    return {job["company"]: job["sentences"] for job in namespace["JOBS"]}


class ReorderBuildsOnThePreset(unittest.TestCase):
    def test_overriding_one_job_keeps_the_presets_other_jobs(self):
        jobs = application_module(
            "from presets.product_designer import *\n"
            "from presets._shared import reorder\n"
            "JOBS = reorder(Freelance=['Rewritten freelance sentence.', 2])\n"
        )
        # The overridden job: the string as given, the int resolved against content_base.
        self.assertEqual(jobs["Freelance"], [
            "Rewritten freelance sentence.",
            "Manage each project from first call to launch, handling scoping, pricing, timelines and client "
            "communication, with significant engagements typically running six months.",
        ])
        # Jobs the module didn't name keep the product_designer preset's version.
        self.assertEqual(jobs["Sample Marketplace"][0],
                         "Designed a two-sided digital marketplace and ran it, owning every product decision.")
        self.assertNotIn(DEVELOPER_LINE, jobs["Sample Marketplace"])
        self.assertEqual(jobs["Example Co"][-1],
                         "Develop the front end in Vue.js across the conversation player, scenario "
                         "editor and dashboards, so the designs ship as built.")

    def test_successive_overrides_accumulate(self):
        jobs = application_module(
            "from presets.product_designer import *\n"
            "from presets._shared import reorder\n"
            "JOBS = reorder(Freelance=['First override.'])\n"
            "JOBS = reorder({'Sample Marketplace': ['Second override.']})\n"
        )
        self.assertEqual(jobs["Freelance"], ["First override."])
        self.assertEqual(jobs["Sample Marketplace"], ["Second override."])

    def test_a_preset_still_builds_from_content_base(self):
        import presets.design_engineer as design_engineer
        jobs = {job["company"]: job["sentences"] for job in design_engineer.JOBS}
        # design_engineer reorders Example Co as [2, 0, 3, 1] of the master list.
        self.assertTrue(jobs["Example Co"][0].startswith("Design and build key features"))
        self.assertEqual(jobs["Sample Marketplace"][-1], DEVELOPER_LINE)


if __name__ == "__main__":
    unittest.main()
