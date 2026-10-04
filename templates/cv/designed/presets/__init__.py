"""Role-family presets: the same career, positioned for a different kind of reader.

    from presets.product_designer import *   # in cv/main_<company>_<role>.py

Each preset re-imports content_base and overrides the positioning layer - headline, profile
paragraph, ATS keyword lists, sidebar order, and the order of sentences inside each job. None
of them adds a fact. Every sentence a preset uses appears in content_base.py, reordered or
rephrased to lead with what that kind of employer reads for.

    product_frontend   Front-end / product engineering roles. Closest to the master.
    design_engineer    Design engineer, UX engineer, design technologist - design AND code.
    product_designer   Product / UI-UX designer. Design-led; code is supporting evidence.
    ai_product         AI engineer, AI product engineer, applied AI, forward-deployed.

Pick by what the posting is, not by what it pays. A design-led preset sent to a React role
reads as a designer who codes a bit, which is a weaker claim than either true one.

**These presets are written for the example content** (content_example.py: Example Co,
Freelance, Sample Marketplace). They name those companies and index into those sentence lists,
and they replace PROFILE and HEADLINE with example text. With your own `profile/cv_content.py`,
do not import a preset as-is: copy one into your per-application module as a pattern and
rewrite it from your own facts. A preset never adds a fact; yours must not either.

In proportion is the operative phrase for any claim a preset carries (product engineer, AI
implementation): include it where the posting cares, and drop it where it would crowbar in
text that costs space the relevant evidence needs.
"""

PRESETS = ("product_frontend", "design_engineer", "product_designer", "ai_product")
