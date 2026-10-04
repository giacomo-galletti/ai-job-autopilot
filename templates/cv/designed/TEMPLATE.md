# Template: designed (CV)

A designed CV and ATS resume built from code, so every application can have its own
tailored version.

| | |
|---|---|
| **Type** | CV |
| **Source extension** | `.py` (a content module, not markup) |
| **Compile command** | `python3 templates/cv/designed/build.py <module.py>` |
| **Toolchain** | Jinja2 -> headless Chromium (Playwright) -> PyMuPDF |
| **Fonts** | Inter (variable, SIL OFL), bundled at `templates/cv/designed/fonts/` |
| **Page limit** | ATS: at most 2 pages. Designed variant: exactly 1 page |
| **Outputs** | `main_<company>_<role>.pdf` (**ATS resume - the default, send this**) and `main_<company>_<role>_designed.pdf` (two-column, for a person) |

## Which variant is the default

**The ATS resume.** `main_<company>_<role>.pdf` is single column, Times, no images, reading
order identical to visual order. Application wording is intentionally tailored from your
profile content.

The designed variant exists for the case where the application reaches a person directly -
emailing a hiring manager, a founder, a referral. Attach it alongside, or instead, when there
is a named human on the other end. Everywhere else, a parser reads the CV before a person
does, and a two-column layout with a photo is a risk taken for no gain.

## Why the designed variant is built from code

A CV exported from a design tool often draws its text as **Type 3 outlines**, so a parser
reads garbled words and phone numbers. This template reproduces a two-column layout from data,
so the designed CV carries a real text layer.

- Page A4 595x842pt, margins 40pt, main column 350pt, sidebar 133pt starting at x=422
- Type: name 24pt/700, headline 10pt, section labels 7pt uppercase tracked, body 7.25pt/10pt

## Content and theme

| What | Where |
|---|---|
| Your CV content | `profile/cv_content.py` (gitignored). Copy `content_example.py` there and replace every value |
| Fallback content | `content_example.py`, a fictional candidate ("Alex Example"), used when the profile file is missing |
| Colours and font | `theme.json` (defaults), overridden key by key by `profile/theme.json`. Keys: `ink`, `body`, `muted`, `accent`, `accent_bar`, `rule`, `paper` (CSS colours) and `font_family` (a font name; Inter is bundled) |
| Photo and card images | `assets/photo.jpg`, and `assets/<file>` named by a project card's `"image"` key (gitignored, optional) |

`JOB_KIT_EXAMPLE_CONTENT=1` forces the example content even when `profile/cv_content.py`
exists (used by the tests). The cover letter reads the same content and theme.

Fonts: Inter (variable, SIL OFL 1.1; licence in `fonts/OFL-Inter.txt`). To use another font,
install it and set `font_family`; for PDFs you share, bundle the file and add an `@font-face`.

## How to use it

```sh
cp templates/cv/designed/template.py cv/main_acme_frontend.py
# 1. pick the preset on the import line   2. override what this posting needs
python3 templates/cv/designed/build.py cv/main_acme_frontend.py
```

A tailored CV stays a readable diff rather than a second copy of the master, because the
positioning can start from one of four role-family presets (written for the example content, see `presets/__init__.py`; with your own content use them as a pattern):

| Preset | For | Positioning |
|---|---|---|
| `product_frontend` | Frontend Engineer, Product Engineer, Software Engineer (Frontend), UI Engineer | Engineering leads; design is the differentiator that follows |
| `design_engineer` | Design Engineer, UX Engineer, Design Technologist, Creative Technologist | Design *and* code, equally - the rarest and strongest claim |
| `product_designer` | Product Designer, UI/UX Designer, Design Systems Designer | Design leads, with process language; code is supporting evidence |
| `ai_product` | AI Engineer, AI Product Engineer, Applied AI, Forward Deployed Engineer | LLM products and agentic work lead; not ML research |

Each preset re-imports `content_base.py` and overrides only the positioning layer: headline,
profile, skills order, ATS keyword lists and the order of sentences inside each job. **No
preset adds a fact.** Pick by what the posting *is*, not by what it pays - a design-led CV
sent to a React role reads as a designer who codes a bit, which is weaker than either true
positioning.

Other entry points:

```sh
python3 templates/cv/designed/build.py --master                # rebuild the untailored pair
python3 templates/cv/designed/build.py <module> --formats ats  # just the ATS resume
```

## Which file to send

| File | Send it when |
|---|---|
| `main_<company>_<role>.pdf` | **default.** Any portal, ATS, online form, or recruiter - single column, standard fonts, clean reading order |
| `main_<company>_<role>_designed.pdf` | emailing a named person: hiring manager, founder, referral |

## Style rules

- **Keyword coverage is the ATS lever.** `ATS_SKILLS_LEFT` / `ATS_SKILLS_RIGHT` are the list a
  parser scores against, so tailoring them to the posting's own vocabulary matters more than
  the designed CV's sidebar order. Only ever use a term the profile genuinely supports; a
  genuine gap stays visible and is never stuffed.
- **Two pages, ATS.** The build fails at three. Cut the profile paragraph or a job's last
  sentence first.
- **One page, designed.** The build fails at two; never shrink the type below `cv.css`.
- **Rewrite substantially, never invent.** Tailor the headline, summary, skill lists, experience bullets and project selection to the posting; presets are only a starting point. Every claim must
  already exist in your profile content (`profile/`).
- **The skills sidebar is the cheapest lever.** Putting the posting's own category first costs
  nothing and is the first thing a reader's eye lands on.
- **Two project cards, no more.** The grid is two columns; a third card breaks the page.

## Known pitfalls

- **Card images.** A card whose `"image"` file is missing from `assets/` renders text-only. A card for a
  project without an image looks unbalanced next to one with an image -
  swap both cards or neither.
- **Long company names.** The date sits on the same row as the company and does not wrap.
  A company name over ~28 characters pushes the date off; shorten the location instead.
- **Personal assets are gitignored.** `assets/photo.jpg` and card screenshots match the
  repo's `*.jpg` privacy rule. They are not committed - a fresh clone renders without them,
  and the layout still holds.
