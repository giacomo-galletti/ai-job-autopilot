#!/usr/bin/env python3
"""Build a CV from a content module.

    python3 templates/cv/designed/build.py cv/main_acme_frontend.py
    python3 templates/cv/designed/build.py cv/main_acme_frontend.py --formats ats
    python3 templates/cv/designed/build.py --master          # rebuild both master CVs

Output goes next to the content module:

    main_acme_frontend.pdf           the ATS resume - single column, standard fonts. THE DEFAULT.
    main_acme_frontend_designed.pdf  the two-column designed CV, for emailing a person.

Both are built unless --formats says otherwise. The **ATS resume is the one to send** unless
there is a specific reason to send the designed one: it is the variant a parser reads
correctly, and a parser reads most applications before a person does.

Exit code 1 with a readable reason if a document overflows its page budget or its text layer
would not survive an ATS parser. That failure is the point: an application that looks fine in
the source and breaks in the PDF is the failure mode this replaces.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import render  # noqa: E402  (needs the sys.path line above)
import render_ats  # noqa: E402

FORMATS = ("ats", "designed")


def build(
    module_path: Path,
    formats: tuple[str, ...],
    out_dir: Path | None = None,
    stem: str | None = None,
) -> int:
    out_dir = out_dir or module_path.parent
    stem = stem or module_path.stem
    failures = 0

    if "ats" in formats:
        target = out_dir / f"{stem}.pdf"
        try:
            result = render_ats.render(module_path, target)
        except render.RenderError as exc:
            print(f"FAIL ats: {exc}", file=sys.stderr)
            failures += 1
        else:
            print(f"OK   ats (send this) -> {target} ({result.pages} pages)")
            for warning in result.warnings:
                print(f"     warning: {warning}")

    if "designed" in formats:
        target = out_dir / f"{stem}_designed.pdf"
        try:
            result = render.render(module_path, target)
        except render.RenderError as exc:
            print(f"FAIL designed: {exc}", file=sys.stderr)
            failures += 1
        else:
            print(f"OK   designed        -> {target} ({result.pages} page)")
            for warning in result.warnings:
                print(f"     warning: {warning}")

    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("module", nargs="?", help="content module, e.g. cv/main_acme_frontend.py")
    parser.add_argument(
        "--formats",
        default="ats,designed",
        help="comma list: ats, designed (default: both; ats is the one to send)",
    )
    parser.add_argument("--out-dir", help="write PDFs here instead of next to the module")
    parser.add_argument(
        "--master",
        action="store_true",
        help="rebuild the untailored master CVs (profile/cv_content.py, else the example content) into cv/main_master*.pdf",
    )
    args = parser.parse_args()

    formats = tuple(f.strip() for f in args.formats.split(",") if f.strip())
    unknown = set(formats) - set(FORMATS)
    if unknown:
        parser.error(f"unknown format(s): {', '.join(sorted(unknown))}. Choose from {', '.join(FORMATS)}.")

    if args.master:
        repo_root = HERE.parents[2]
        out_dir = Path(args.out_dir) if args.out_dir else repo_root / "cv"
        return build(HERE / "content_base.py", formats, out_dir, stem="main_master")

    if not args.module:
        parser.error("give a content module path, or --master")

    return build(Path(args.module), formats, Path(args.out_dir) if args.out_dir else None)


if __name__ == "__main__":
    raise SystemExit(main())
