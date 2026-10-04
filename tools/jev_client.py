"""Minimal client for Jev (TypeSafe AI's typed-judgement API).

Native v1 only: POST https://api.typesafe.ai/v1/systemone with a `state` and a map of typed
`questions` (noul/choice/score); returns a typed `answer` per question. Jev does not generate
text - it is used here only for scoring/classification, never to write CV or cover-letter copy.

Reference: ~/Development/jev-system-one-reference/Jev_System_One_Reference.md (Section 3).
Pinned model: jev-1.13.0 (never the "-latest" alias - the reference warns an alias can move
versions silently). The response's own `model` field is checked against this pin on every call.

Credential: reads TYPESAFE_API_KEY from the environment only. Never hardcoded, never logged.
"""

import json
import os
import time
import urllib.error
import urllib.request

API_URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-1.13.0"
MAX_RETRIES = 4


class JevError(Exception):
    pass


def ask(state, questions, *, model=MODEL, timeout=30):
    """POST one Jev request. Returns the parsed response dict.

    Retries on 429, and on any 5xx (documented 529 or an undocumented gateway error like 520),
    timeouts and other transient network errors, with exponential backoff. 401/422 never retry -
    they mean the request itself is wrong, not that the server is busy.
    """
    api_key = os.environ.get("TYPESAFE_API_KEY")
    if not api_key:
        raise JevError("TYPESAFE_API_KEY is not set in the environment")

    body = json.dumps({"state": state, "model": model, "questions": questions}).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    delay = 1.0
    last_error = None
    for _attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                request_id = resp.headers.get("x-typesafe-request-id")
                data = json.loads(resp.read().decode("utf-8"))
                data["_request_id"] = request_id
                if data.get("model") != model:
                    # The reference: log this, never silently trust an alias-moved version.
                    data["_model_mismatch"] = True
                return data
        except urllib.error.HTTPError as e:
            status = e.code
            request_id = e.headers.get("x-typesafe-request-id") if e.headers else None
            body_text = e.read().decode("utf-8", errors="replace")
            if status == 401:
                raise JevError(f"401 Unauthorized (request_id={request_id}): check TYPESAFE_API_KEY")
            if status == 422:
                raise JevError(f"422 Validation error (request_id={request_id}): {body_text}")
            if status == 429 or status >= 500:
                last_error = JevError(f"{status} (request_id={request_id}), retrying")
                time.sleep(delay)
                delay *= 2
                continue
            raise JevError(f"{status} (request_id={request_id}): {body_text}")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            # Covers DNS/connection failures (URLError) and read timeouts, which urllib raises as
            # a bare TimeoutError/OSError rather than wrapping them in URLError.
            last_error = JevError(f"network error: {e}")
            time.sleep(delay)
            delay *= 2

    raise last_error or JevError("exhausted retries")
