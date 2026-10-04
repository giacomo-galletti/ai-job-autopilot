#!/usr/bin/env python3
"""Run a bounded, paginated LinkedIn public-job search and deduplicate results."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import date
from pathlib import Path

try:
    from tools.low_cost_markets import low_cost_market
except ModuleNotFoundError:  # run as a script: tools/ itself is on sys.path
    from low_cost_markets import low_cost_market

# Optional fourth family: conversational-AI roles. Edit QUERIES to match your own role families
# (the onboarding generates profile/search-queries.md from your profile).
QUERIES = (
    "frontend engineer OR front end developer OR product engineer",
    "design engineer OR UX engineer OR design technologist",
    "product designer OR UI UX designer OR design systems designer",
    "prompt engineer OR conversation designer OR conversational AI designer",
)
# Default search locations; edit LOCATIONS and MODES for your own country and remote preferences.
LOCATIONS = ("Remote", "European Union", "United States", "United Kingdom")
MODES = {"Remote": ("remote",), "European Union": ("remote", "hybrid"), "United States": ("remote", "hybrid"),
         "United Kingdom": ("remote",)}


def run_batch(root: Path, days: int, pages: int, per_page: int) -> dict:
    cli = root / ".agents/skills/linkedin-search/cli/src/cli.ts"
    jobs: dict[str, dict] = {}
    dropped: dict[str, dict] = {}
    errors = []
    calls = 0
    for query in QUERIES:
        for location in LOCATIONS:
            for mode in MODES[location]:
                for page in range(1, pages + 1):
                    calls += 1
                    command = ["bun", "run", str(cli), "search", "--query", query,
                           "--location", location, "--remote", mode, "--jobage", str(days), "--page", str(page),
                               "--limit", str(per_page), "--format", "json"]
                    completed = subprocess.run(command, cwd=root, capture_output=True, text=True)
                    if completed.returncode:
                        errors.append({"query": query, "location": location, "mode": mode, "page": page,
                                   "error": (completed.stderr or completed.stdout).strip()})
                        continue
                    try:
                        payload = json.loads(completed.stdout)
                    except json.JSONDecodeError as exc:
                        errors.append({"query": query, "location": location, "mode": mode, "page": page,
                                   "error": f"invalid JSON: {exc}"})
                        continue
                    for job in payload.get("results", []):
                        job_id = str(job.get("id") or job.get("url") or "").strip()
                        if not job_id:
                            continue
                        # Postings confined to India and other low-cost markets never enter the pool.
                        market = low_cost_market(job)
                        if market:
                            dropped[job_id] = {"id": job_id, "title": job.get("title"), "company": job.get("company"),
                                               "location": job.get("location"), "market": market}
                            continue
                        if job_id not in jobs:
                            jobs[job_id] = {**job, "discovered_queries": [], "discovered_locations": [], "discovered_modes": []}
                        jobs[job_id]["discovered_queries"] = sorted(set(jobs[job_id]["discovered_queries"] + [query]))
                        jobs[job_id]["discovered_locations"] = sorted(set(jobs[job_id]["discovered_locations"] + [location]))
                        jobs[job_id]["discovered_modes"] = sorted(set(jobs[job_id]["discovered_modes"] + [mode]))
    results = sorted(jobs.values(), key=lambda item: (item.get("date") or "", item.get("company") or "",
                                                       item.get("title") or ""), reverse=True)
    return {"generated_on": date.today().isoformat(), "calls": calls,
            "raw_unique_results": len(results), "errors": errors, "results": results,
            "dropped_low_cost": list(dropped.values())}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--pages", type=int, default=2)
    parser.add_argument("--per-page", type=int, default=10)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    if args.days < 1 or args.pages < 1 or args.per_page < 1:
        parser.error("--days, --pages and --per-page must be positive")
    root = args.root.resolve()
    output = (args.output or root / "reports/linkedin-batch-search.json").resolve()
    payload = run_batch(root, args.days, args.pages, args.per_page)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"calls": payload["calls"], "unique_results": payload["raw_unique_results"],
                      "dropped_low_cost": len(payload["dropped_low_cost"]),
                      "errors": len(payload["errors"]), "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
