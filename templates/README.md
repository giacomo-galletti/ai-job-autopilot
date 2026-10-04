# Custom Templates

This folder holds user-registered templates (LaTeX, Typst, or any other toolchain with a declared compile command), managed by the `/add-template` command. The framework works out of the box with its stock templates (moderncv for CVs, `cover.cls` for cover letters) — this folder only gets content when you register your own.

## Layout

```
templates/
├── cv/
│   └── <template-name>/
│       ├── template.<ext>  # Profile-agnostic skeleton ([PLACEHOLDER] tokens), e.g. template.tex or template.typ
│       ├── TEMPLATE.md      # Manifest: source extension, compile command, fonts, page limit, style rules, pitfalls
│       ├── *.cls / *.sty    # Custom class/style files, or Typst packages (if the template needs them)
│       └── fonts/           # Bundled font files (if not using system fonts)
└── cover_letters/
    └── <template-name>/
        └── (same layout)
```

## How it works

- `/add-template` interviews you for the template's instructions (source extension, compile command, fonts, style rules, page limit), stores the files here, and runs a mandatory test compile before registering anything.
- Activating a template adds a managed block to `05-cv-templates.md` or `06-cover-letter-templates.md`, which is what `/apply` reads when drafting and compiling — no other wiring needed.
- `/add-template --list` shows registered templates; `/add-template --use <name>` switches; `/add-template --use default` reverts to the stock templates.

Templates are stored with `[PLACEHOLDER]` tokens instead of personal data, so they are safe to commit and share.

## Bundled template: `designed`

`templates/cv/designed/` (CV and ATS resume) and `templates/cover_letters/designed/` (matching letter) are the default, working out of the box with fictional example content. They are Python/HTML/CSS templates rendered with Jinja2, Playwright's Chromium and PyMuPDF.

- Your content: `profile/cv_content.py` (gitignored). Without it the example candidate renders.
- Your look: `profile/theme.json` overrides the defaults in `templates/cv/designed/theme.json` (colours and `font_family`).
- Fonts: Inter (SIL OFL 1.1), licence in `templates/cv/designed/fonts/OFL-Inter.txt`.
- Build: `python3 templates/cv/designed/build.py --master` and `python3 templates/cover_letters/designed/build.py <letter module>`.
