import json
import unittest
import urllib.error
from unittest.mock import patch

from tools.jev_client import JevError, MODEL, ask


class FakeResponse:
    def __init__(self, payload, request_id="req_test"):
        self._payload = json.dumps(payload).encode("utf-8")
        self.headers = {"x-typesafe-request-id": request_id}

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class JevClientTests(unittest.TestCase):
    def setUp(self):
        patcher = patch.dict("os.environ", {"TYPESAFE_API_KEY": "test-key"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_missing_api_key_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(JevError):
                ask({"x": 1}, {})

    def test_successful_call_returns_answers_and_request_id(self):
        payload = {"model": MODEL, "answers": {"q": {"type": "noul", "noul": 0.9}}, "usage": {}}
        with patch("tools.jev_client.urllib.request.urlopen", return_value=FakeResponse(payload)):
            result = ask({"x": 1}, {"q": {"type": "noul", "instructions": "?"}})
        self.assertEqual(result["answers"]["q"]["noul"], 0.9)
        self.assertEqual(result["_request_id"], "req_test")
        self.assertNotIn("_model_mismatch", result)

    def test_model_mismatch_is_flagged_not_hidden(self):
        payload = {"model": "jev-9.9.9", "answers": {}, "usage": {}}
        with patch("tools.jev_client.urllib.request.urlopen", return_value=FakeResponse(payload)):
            result = ask({"x": 1}, {})
        self.assertTrue(result["_model_mismatch"])

    def test_401_raises_immediately_without_retry(self):
        error = urllib.error.HTTPError("url", 401, "unauthorized", {}, None)
        error.read = lambda: b"{}"
        with patch("tools.jev_client.urllib.request.urlopen", side_effect=error):
            with self.assertRaises(JevError) as ctx:
                ask({"x": 1}, {})
        self.assertIn("401", str(ctx.exception))

    def test_429_retries_then_succeeds(self):
        error = urllib.error.HTTPError("url", 429, "rate limited", {}, None)
        error.read = lambda: b"{}"
        payload = {"model": MODEL, "answers": {}, "usage": {}}
        with patch("tools.jev_client.time.sleep"), patch(
            "tools.jev_client.urllib.request.urlopen",
            side_effect=[error, FakeResponse(payload)],
        ):
            result = ask({"x": 1}, {})
        self.assertEqual(result["model"], MODEL)

    def test_undocumented_5xx_retries_then_succeeds(self):
        # A gateway can return an undocumented status (520 was observed live) - treat any 5xx
        # as transient, not just the documented 529.
        error = urllib.error.HTTPError("url", 520, "unknown error", {}, None)
        error.read = lambda: b""
        payload = {"model": MODEL, "answers": {}, "usage": {}}
        with patch("tools.jev_client.time.sleep"), patch(
            "tools.jev_client.urllib.request.urlopen",
            side_effect=[error, FakeResponse(payload)],
        ):
            result = ask({"x": 1}, {})
        self.assertEqual(result["model"], MODEL)

    def test_read_timeout_retries_then_succeeds(self):
        # urllib raises a bare TimeoutError on a read timeout, not wrapped in URLError - a real
        # bug found via a live smoke test where this crashed the script uncaught.
        payload = {"model": MODEL, "answers": {}, "usage": {}}
        with patch("tools.jev_client.time.sleep"), patch(
            "tools.jev_client.urllib.request.urlopen",
            side_effect=[TimeoutError("timed out"), FakeResponse(payload)],
        ):
            result = ask({"x": 1}, {})
        self.assertEqual(result["model"], MODEL)


if __name__ == "__main__":
    unittest.main()
