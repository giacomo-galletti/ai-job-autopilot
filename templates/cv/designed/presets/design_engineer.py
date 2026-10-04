"""Design engineer / UX engineer / design technologist: design AND code, equally.

The rarest and strongest positioning - most candidates are one or the other. Lead with the
pairing itself, then prove both halves on the same feature.

Use for: Design Engineer, UX Engineer, Design Technologist, Front-End Designer, Creative
Technologist, Product Engineer at a design-led company.
"""

from content_base import *  # noqa: F401,F403
from ._shared import reorder, skills

HEADLINE = "Design Engineer · Product, UI/UX, Front-end & AI"

PROFILE = (
    "Design engineer with 10+ years designing interfaces and shipping the front-end "
    "code behind them, from Figma to production. At Example Co I lead the UI design for an AI "
    "platform and build it in Vue.js, including the scenario editor customers use to author their "
    "own AI conversations and the design-system foundations the product is built on. I work across "
    "React, TypeScript, Vue and React Native, and I integrate AI into products rather than around "
    "them. I do my best work owning a product surface end to end, design decisions and shipped "
    "code in the same pair of hands."
)

SKILLS = skills("Design", "Development", "Artificial Intelligence", "Product & Business", "Tools")

ATS_SKILLS_LEFT = [
    "UI/UX Design",
    "Design Systems in Code",
    "Figma to Production Front-end",
    "Wireframing & Prototyping",
    "Responsive & Accessible Design",
    "User Testing & Feedback",
]
ATS_SKILLS_RIGHT = [
    "React & TypeScript",
    "Vue.js, Nuxt, Next.js",
    "HTML & CSS",
    "AI Integration & LLM APIs",
    "AI-Assisted Development (Claude Code)",
    "Requirements Gathering & Scoping",
]

# Pure reorder, by index into content_base: lead with the feature he designed AND built,
# then the design leadership, the design system, and the stack last.
JOBS = reorder({"Example Co": [2, 0, 3, 1]})
