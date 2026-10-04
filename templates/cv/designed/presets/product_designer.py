"""Product / UI-UX designer roles. Design-led; the code is supporting evidence.

So: the summary leads with design, the design-process language that is genuinely true
(wireframing, prototyping, user testing and feedback, design systems) is pulled to the front,
each job leads with the design decision rather than the stack, and the two ATS columns are
split design | technical so a recruiter can see the separation in one glance.

Use for: Product Designer, UI/UX Designer, Senior Product Designer, Digital Product Designer,
Design Systems Designer.
"""

from content_base import *  # noqa: F401,F403
from ._shared import reorder, skills

HEADLINE = "Product Designer · UI/UX, Design Systems & AI Products"

# The portfolio link is not repeated here: it already sits in the header line of both CVs,
# and a sentence about it costs a line.
PROFILE = (
    "Product designer with 10+ years designing interfaces for web and mobile, from wireframes and "
    "prototypes through user feedback to a shipped product. At Example Co I lead the UI design "
    "for an AI platform where people practise high-stakes workplace conversations, including the "
    "editor customers use to build their own conversations and the design-system "
    "foundations connected to Figma. I design AI products specifically: what an LLM feature should "
    "feel like, and what to show when it is thinking, wrong or unsure. Because I also build the "
    "front end, my designs arrive as working interfaces rather than handoffs."
)

# Design leads the sidebar. Development stays - it is the differentiator - but second.
SKILLS = skills("Design", "Artificial Intelligence", "Product & Business", "Development", "Tools")

# Left column is design, right column is technical: the separation the review asked for.
ATS_SKILLS_LEFT = [
    "UI/UX Design",
    "Design Systems",
    "Wireframing & Prototyping",
    "User Testing & Feedback",
    "Responsive & Accessible Design",
    "Product Design & Strategy",
    "Requirements Gathering & Scoping",
]
ATS_SKILLS_RIGHT = [
    "Figma (Sketch, Photoshop)",
    "Designing AI & LLM Product Features",
    "Design-to-Code / Figma to Production",
    "HTML, CSS, JavaScript, TypeScript",
    "Vue.js, Nuxt, React, Next.js",
    "React Native, Expo, Flutter",
    "Client Communication",
]

JOBS = reorder(
    {
        # Lead with design leadership, then the feature, then the design system (which carries
        # the team size). The stack sentence stays, rephrased so it reads as design reaching
        # production.
        "Example Co": [
            0,
            2,
            3,
            "Develop the front end in Vue.js across the conversation player, scenario "
            "editor and dashboards, so the designs ship as built.",
        ],
        # Design framing, and without the closing "turned me into a developer" line, which
        # points the wrong way for a design-led CV.
        "Sample Marketplace": [
            "Designed a two-sided digital marketplace and ran it, owning every product decision.",
            1,
            2,
        ],
    },
    Freelance=[
        "Design websites, web apps and mobile apps for clients, from UI/UX in Figma through "
        "wireframes and prototypes to the built product.",
        "Design complete products end to end, from B2B platforms with a web dashboard and mobile "
        "app to marketplaces with seller tools, licensing and payments.",
        "Build the front end myself in Vue, Nuxt, React, Next.js and React Native, which "
        "keeps the shipped interface faithful to the design.",
        2,
    ],
)
