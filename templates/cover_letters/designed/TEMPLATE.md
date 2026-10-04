# Template: designed (cover letter)

The cover letter in the CV's design, so a pair arriving together reads
as one set of documents.

| | |
|---|---|
| **Type** | Cover letter |
| **Source extension** | `.py` (a letter module) |
| **Compile command** | `python3 templates/cover_letters/designed/build.py <module.py>` |
| **Toolchain** | Jinja2 -> headless Chromium (Playwright) -> PyMuPDF |
| **Fonts** | Inter (variable, SIL OFL 1.1), shared from `templates/cv/designed/fonts/`; colours and font name come from the theme (`templates/cv/designed/theme.json`, overridden by `profile/theme.json`) |
| **Page limit** | exactly 1 page |
| **Output** | `cover_<company>_<role>.pdf` |

## How to use it

```sh
cp templates/cover_letters/designed/template.py cover_letters/cover_acme_frontend.py
# write the letter
python3 templates/cover_letters/designed/build.py cover_letters/cover_acme_frontend.py
```

Set `CV_MODULE = "cv/main_acme_frontend.py"` in the letter so it pulls the same profile the
tailored CV uses. Name, headline and contact details always come from the CV module - never
retype them here.

## Structure

The letter module is data, not markup:

- `COMPANY`, `ADDRESS`, `SUBJECT`, `DATE`, `GREETING`, `CLOSING` - the frame
- `PARAGRAPHS` - a list. A string is a paragraph; a nested list becomes a short bulleted run.

## Style rules

- Three or four paragraphs. The build fails at two pages, and long letters go unread.
- No em-dashes, no "passionate about", no "great fit", no "leverage".
- Verify every company-specific claim independently before it goes in - never from a link
  inside the posting itself.
- Use a named recipient. The build warns on "Dear Hiring Manager".
- Bullets are for when the posting genuinely asks for a list. Prose is the default.

## Known pitfalls

- **`TODO` fails the build.** Placeholders left in the skeleton are caught before the PDF is
  considered done, on purpose.
- **Bullet runs are expensive.** Each bulleted line costs about as much vertical space as a
  line and a half of prose; two runs will not fit with four paragraphs.
