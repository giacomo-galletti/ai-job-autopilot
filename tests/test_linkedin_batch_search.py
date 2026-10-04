import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.linkedin_batch_search import run_batch


class LinkedInBatchSearchTests(unittest.TestCase):
    def test_deduplicates_same_job_across_queries_and_locations(self):
        payload = '{"results":[{"id":"1","title":"Frontend Engineer","company":"Acme","date":"2026-09-24","url":"https://www.linkedin.com/jobs/view/1"}]}'

        class Result:
            returncode = 0
            stdout = payload
            stderr = ""

        with tempfile.TemporaryDirectory() as temp, patch("tools.linkedin_batch_search.subprocess.run", return_value=Result()) as run:
            result = run_batch(Path(temp), days=30, pages=1, per_page=10)
        # 4 queries x (Remote, EU remote+hybrid, United States remote+hybrid, United Kingdom remote) x 1 page
        self.assertEqual(result["calls"], 24)
        self.assertEqual(result["raw_unique_results"], 1)
        self.assertEqual(len(result["results"][0]["discovered_queries"]), 4)
        self.assertEqual(result["results"][0]["discovered_locations"],
                         ["European Union", "Remote", "United Kingdom", "United States"])
        # The UK pass is remote-only.
        uk_modes = {call.args[0][call.args[0].index("--remote") + 1] for call in run.call_args_list
                    if "United Kingdom" in call.args[0]}
        self.assertEqual(uk_modes, {"remote"})

    def test_searches_prompt_engineer_and_conversation_designer_roles(self):
        # The fourth family covers conversational-AI titles.
        class Result:
            returncode = 0
            stdout = '{"results":[]}'
            stderr = ""

        with tempfile.TemporaryDirectory() as temp, patch("tools.linkedin_batch_search.subprocess.run", return_value=Result()) as run:
            run_batch(Path(temp), days=14, pages=1, per_page=10)
        queries = {call.args[0][call.args[0].index("--query") + 1] for call in run.call_args_list}
        self.assertTrue(any("prompt engineer" in query and "conversation designer" in query for query in queries))

    def test_drops_low_cost_market_postings_before_they_reach_the_pool(self):
        payload = ('{"results":['
                   '{"id":"1","title":"Prompt Engineer","company":"Acme","location":"Bengaluru, Karnataka, India"},'
                   '{"id":"2","title":"Conversation Designer","company":"Beta","location":"Austin, Texas, United States"},'
                   '{"id":"3","title":"Designer","company":"Gamma","location":"Greater Coimbatore Area"}]}')

        class Result:
            returncode = 0
            stdout = payload
            stderr = ""

        with tempfile.TemporaryDirectory() as temp, patch("tools.linkedin_batch_search.subprocess.run", return_value=Result()):
            result = run_batch(Path(temp), days=14, pages=1, per_page=10)
        self.assertEqual([job["id"] for job in result["results"]], ["2"])
        self.assertEqual(result["raw_unique_results"], 1)
        # Dropped postings stay visible in the report, once each, with the market that excluded them.
        self.assertEqual(sorted((job["id"], job["market"]) for job in result["dropped_low_cost"]),
                         [("1", "India"), ("3", "India")])


if __name__ == "__main__":
    unittest.main()
