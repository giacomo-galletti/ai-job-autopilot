"""Product / front-end engineering roles. Closest to the master content.

Engineering leads, design is the differentiator that follows it. This is the preset for the
large middle of the market: "Frontend Engineer", "Software Engineer (Frontend)", "Product
Engineer", "Full-Stack Engineer" with a front-end lean.

Use for: Frontend Engineer, Front-End Developer, Product Engineer, Software Engineer
(Frontend), UI Engineer, Web Developer.
"""

from content_base import *  # noqa: F401,F403
from ._shared import reorder, skills

HEADLINE = "Product Engineer · Front-end, UI/UX & AI Integration"

PROFILE = (
    "Product engineer with 10+ years building websites, web apps and mobile apps, from "
    "Figma to production. At Example Co I develop the front end of an AI platform in Vue.js "
    "across the conversation player, scenario editor and dashboards, and I built the design-system "
    "foundations the product is built on. I work across Vue, Nuxt, React, Next.js, TypeScript, "
    "React Native and Flutter. I implement AI into products rather than around them: LLM APIs, "
    "agentic workflows and automations, shipped in two products of my own as well as at work. "
    "Because I design as well as build, I can take a requirement to a shipped interface without a "
    "handoff in the middle."
)

SKILLS = skills("Development", "Design", "Artificial Intelligence", "Product & Business", "Tools")

ATS_SKILLS_LEFT = [
    "Front-end Development",
    "JavaScript & TypeScript",
    "Vue.js, Nuxt, React, Next.js",
    "React Native, Expo, Flutter",
    "HTML, CSS, Tailwind",
    "Web & Mobile App Development",
    "Bug Investigation & Root Cause Analysis",
]
ATS_SKILLS_RIGHT = [
    "Design Systems & Component Libraries",
    "UI/UX Design (Figma)",
    "Responsive & Accessible Design",
    "AI Integration & LLM APIs",
    "Workflow Automation & Agentic Workflows",
    "Requirements Gathering & Scoping",
    "Cross-Functional Collaboration",
]

# Pure reorder, by index into content_base.
JOBS = reorder(
    {"Example Co": [1, 2, 3, 0]},
    Freelance=[0, 1, 3, 2],
)
