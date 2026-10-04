"""AI engineer / AI product roles: building products on top of LLM APIs.

Not ML research. This preset is for postings that want someone **implementing AI** - shipping
LLM features into a product, wiring up agentic workflows, automating work that used to be
manual - not someone training models. If a posting requires a PhD, publications, or training
from scratch, it is the wrong posting, not the wrong preset.

It covers two shapes of the same capability, because the evidence is the same either way:

  - **AI product engineering** - building the AI features of someone's product
  - **AI solutions / integration** - implementing AI inside a business: automations,
    integrations, internal tooling. This is the shape most contract work takes, and the
    freelance AI-automation line plus n8n/Make/Zapier is what backs it.

Use for: AI Engineer, AI Product Engineer, Applied AI Engineer, AI Solutions Engineer,
Forward Deployed Engineer, Automation Engineer, Full-Stack Engineer on an AI product.
"""

from content_base import *  # noqa: F401,F403
from ._shared import reorder, skills

HEADLINE = "AI Engineer · LLM Integration, Automation & Product"

PROFILE = (
    "Product engineer with 10+ years shipping web and mobile products, now implementing AI into "
    "them. At Example Co I design and build features for an AI platform: AI-assisted writing, "
    "voice controls, and the editor customers use to author their own AI conversations. I "
    "have shipped two AI products of my own, benchmarking several models against "
    "real sold listings before choosing one, and I build AI automations that take repetitive work "
    "out of a business. I build the interface as well as the integration, so an AI feature arrives "
    "as something people can actually use."
)

SKILLS = skills("Artificial Intelligence", "Automation", "Development", "Design", "Tools")

ATS_SKILLS_LEFT = [
    "AI Integration & LLM APIs",
    "Prompt Engineering",
    "Agentic Workflows",
    "AI-Assisted Development (Claude Code, Cursor)",
    "Workflow Automation (n8n, Make, Zapier)",
    "Local LLMs (Ollama)",
    "API Integration",
]
ATS_SKILLS_RIGHT = [
    "JavaScript & TypeScript",
    "Vue.js, Nuxt, React, Next.js",
    "React Native, Expo, SwiftUI",
    "Python",
    "UI/UX Design & Design Systems",
    "Product Design & Strategy",
    "Requirements Gathering & Scoping",
]

JOBS = reorder(
    {"Example Co": [
        "Design and build AI features for a platform where people practise high-stakes workplace "
        "conversations through realistic simulations: AI-assisted writing, voice controls, and the "
        "step-by-step editor customers use to create their own AI conversations.",
        1,
        "Lead UI design for the platform, and build the design-system foundations connected to "
        "Figma along with the Nuxt marketing site in three languages.",
    ]},
    Freelance=[3, 0, 1, 2],
)
