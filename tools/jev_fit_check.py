"""Use Jev (typed-judgement API) as a second opinion on job fit and CV preset selection.

This never replaces the fit evaluation in 04-job-evaluation.md - it is a decomposed, narrow
cross-check on top of it, per the reference's own guidance (Section 7: one judgment per
question; Section 10: confidence is not permission to act). Jev cannot generate text, so it
never writes CV or cover-letter copy - only scores fit and picks which preset the CV should
lead with. The human (or the assistant's own manual read) still owns the final call, especially
in the 0.4-0.6 "uncertain" band this tool reports rather than resolves.

Usage:
    python3 tools/jev_fit_check.py --posting path/to/posting.txt --profile path/to/profile_summary.txt

Reads TYPESAFE_API_KEY from the environment (see .env). Never call this against a job posting
without the profile summary alongside it - Jev evaluates fit as a comparison, not from the
posting alone.
"""

import argparse
import json
import sys
from pathlib import Path

from jev_client import JevError, ask

PRESETS = {
    "product_designer": "Leads with UI/UX design, Figma, design systems, product design strategy.",
    "product_frontend": "Leads with full-stack product engineering: Vue/React/Next.js, TypeScript, shipped products end to end.",
    "ai_product": "Leads with AI/LLM integration: agentic workflows, prompt engineering, AI features built into products.",
    "design_engineer": "Leads with design-plus-code: designs in Figma and ships the front end personally, the design/dev hybrid.",
}

FIT_LEVELS = [
    "The candidate's core skills and experience have essentially no overlap with the posting's core requirements.",
    "The candidate has minor tangential overlap, but is missing most of the named core requirements.",
    "The candidate has partial overlap: some core requirements are met, others are clear gaps.",
    "The candidate meets most core requirements, with one or two notable gaps.",
    "The candidate's skills and experience are a strong match for the posting's core requirements.",
]


def build_questions():
    return {
        "core_skill_fit": {
            "type": "score",
            "instructions": (
                "Compare `candidate.profile_summary` against `posting.text`. How well does the "
                "candidate's actual skill set and experience match the posting's core (not "
                "nice-to-have) technical requirements?"
            ),
            "criteria": FIT_LEVELS,
        },
        "best_preset": {
            "type": "choice",
            "instructions": (
                "Given `posting.text`, which CV framing in `candidate.available_presets` should "
                "lead - i.e. which angle on the candidate's background is most relevant to this "
                "specific posting?"
            ),
            "criteria": {**PRESETS, "other": "None of the listed presets fits the posting well."},
        },
        "gap_named_explicitly": {
            "type": "noul",
            "instructions": (
                "Does `posting.text` state at least one specific, named core requirement that "
                "`candidate.profile_summary` does not support (e.g. a specific tool, years of "
                "experience, or domain)?"
            ),
            "criteria": {
                "true": "At least one specific named core requirement is unmet.",
                "false": "No specific unmet core requirement is identifiable, or the posting is too vague to tell.",
            },
        },
    }


def check(posting_text, profile_summary):
    state = {
        "posting": {"text": posting_text},
        "candidate": {
            "profile_summary": profile_summary,
            "available_presets": PRESETS,
        },
    }
    response = ask(state, build_questions())
    return response


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--posting", required=True, help="Path to a text file with the job posting")
    ap.add_argument("--profile", required=True, help="Path to a text file with the candidate profile summary")
    args = ap.parse_args()

    posting_text = Path(args.posting).read_text(encoding="utf-8")
    profile_summary = Path(args.profile).read_text(encoding="utf-8")

    try:
        response = check(posting_text, profile_summary)
    except JevError as e:
        sys.exit(f"Jev call failed: {e}")

    if response.get("_model_mismatch"):
        print(f"WARNING: requested {response.get('model')!r} but a different version answered", file=sys.stderr)

    answers = response["answers"]
    fit = answers["core_skill_fit"]
    preset = answers["best_preset"]
    gap = answers["gap_named_explicitly"]

    print(f"model: {response.get('model')}  request_id: {response.get('_request_id')}")
    print(f"core_skill_fit: score={fit['score']:.2f}  confidence={fit['confidence']:.2f}")
    print(f"  probabilities: {json.dumps(fit['probabilities'])}")
    print(f"best_preset: {preset['choice']}  confidence={preset['confidence']:.2f}")
    print(f"  probabilities: {json.dumps(preset['probabilities'])}")
    print(f"gap_named_explicitly: noul={gap['noul']:.2f}")
    print(f"usage: {response.get('usage')}")


if __name__ == "__main__":
    main()
