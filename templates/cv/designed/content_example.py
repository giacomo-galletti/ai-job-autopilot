"""Example CV content: a fictional candidate, so the template renders out of the box.

Nothing here is real. `content_base.py` uses this file only when `profile/cv_content.py`
(your own content, gitignored) does not exist. Copy this file to `profile/cv_content.py`
and replace every value with your own; keep the names and structure.

The designed CV joins each job's sentences into a paragraph; the ATS resume shows them as
bullets. A per-application module (cv/main_<company>_<role>.py) imports * from content_base
and overrides only what the role needs - see template.py for the skeleton.
"""

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

NAME = "Alex Example"
HEADLINE = "Product Engineer · Front-end, UI/UX & AI"

CONTACT = {
    "location": "Example City, Country",
    "availability": "Open to remote work",  # optional: leave the key out when you have nothing to say
    "phone": "+00 000 000 000",
    "email": "alex@example.com",
    "website": "example.com",
    "linkedin": "linkedin.com/in/alex-example",
    "github": "github.com/alex-example",
}

PROFILE = (
    "Product engineer with 10+ years of experience designing and building websites, web apps and mobile apps, "
    "from Figma to production. Proven track record of turning complex requirements into clear, usable interfaces, "
    "building them in Vue and React, and integrating AI features and automations that take repetitive work off "
    "people's hands. Experienced collaborating with clients, product teams and developers, and owning products "
    "from scoping to launch. Skilled in UI/UX design, design systems, front-end development and AI integration."
)

# Order matters: the designed CV renders these top to bottom in the sidebar.
SKILLS = [
    ("Artificial Intelligence", ["AI Integration", "LLM APIs", "Prompt Engineering", "AI-Assisted Development", "Agentic Workflows"]),
    ("Automation", ["Workflow Automation", "API Integration", "n8n", "Make", "Zapier"]),
    ("Design", ["UI/UX Design", "Design Systems", "Wireframing & Prototyping", "Responsive & Accessible Design", "User Testing & Feedback"]),
    (
        "Development",
        ["Web & Mobile App Development", "JavaScript", "TypeScript", "Vue.js", "Nuxt", "React", "Next.js", "React Native", "Python", "Tailwind"],
    ),
    (
        "Product & Business",
        ["Product Design & Strategy", "Requirements Gathering & Scoping", "Bug Investigation & Root Cause Analysis", "Client Communication", "Cross-Functional Collaboration"],
    ),
    ("Tools", ["Figma", "Sketch", "Photoshop", "Claude Code", "Cursor"]),
]

# The ATS CV shows a short two-column list instead of the categories above.
ATS_SKILLS_LEFT = [
    "Product Design & Strategy",
    "Requirements Gathering & Scoping",
    "User Testing & Feedback",
    "Bug Investigation & Root Cause Analysis",
    "AI Integration & Workflow Automation",
    "Client Communication",
    "Cross-Functional Collaboration",
]
ATS_SKILLS_RIGHT = [
    "UI/UX Design",
    "Design Systems",
    "Wireframing & Prototyping",
    "Responsive & Accessible Design",
    "Web App Development",
    "Mobile App Development",
    "AI-Assisted Development (Claude Code, Cursor)",
]

LANGUAGES = [("English", "Native"), ("Italian", "Conversational")]

# Contact details are shared only on request, with the referee's permission.
REFERENCES = [
    {"name": "Sam Referee", "role": "Engineering Manager, Example Co"},
    {"name": "Jordan Sample", "role": "Founder, Sample Marketplace"},
]
REFERENCES_NOTE = "Contact details available upon request."

# Dates. start/end are optional and accept every form below, so an unknown month never has to
# be invented:
#   (2021, 3)  month and year  -> "03/2021" (ATS), "Mar 2021" (designed)
#   (2021,)    year only; 2021 and (2021, None) mean the same
#   leave "start" out (or None) when the whole date is unknown; with an "end" only, the entry
#   shows just that year
# An "end" of None (or no "end") means Present. "company" is optional too: leave it out when the
# employer is unknown or private and the role (plus location) is shown on its own; never put the
# string "None" or a placeholder there. The same date rules apply to EDUCATION.
JOBS = [
    {
        "company": "Example Co",
        "role": "Product Designer & Front-end Developer",
        "start": (2021, 3),
        "end": None,
        "location": "Example City, Country",
        "remote": True,
        "sentences": [
            "Lead UI design for an AI platform where people practise high-stakes workplace conversations through realistic simulations.",
            "Develop the front end in Vue.js across the conversation player, scenario editor and dashboards.",
            "Design and build key features, from the step-by-step editor customers use to create their own AI "
            "conversations to AI-assisted writing, voice controls and a redesigned results screen.",
            "Build the design-system foundations, connected to Figma, used across a dev team of five to six, plus "
            "the Nuxt marketing site in three languages.",
        ],
    },
    {
        "company": "Freelance",
        "role": "Web Designer / Developer",
        "start": (2014, 7),
        "end": None,
        "location": None,
        "remote": True,
        "sentences": [
            "Design and build websites, web apps and mobile apps for clients, from UI/UX in Figma to production in Vue, "
            "Nuxt, React, Next.js and React Native.",
            "Deliver complete products, from B2B platforms with a web dashboard and mobile app to marketplaces with seller "
            "tools, licensing and payments.",
            "Manage each project from first call to launch, handling scoping, pricing, timelines and client "
            "communication, with significant engagements typically running six months.",
            "Build AI automations that take the repetitive work out of the process, from finding new clients to generating demo sites.",
        ],
    },
    {
        "company": "Sample Marketplace",
        "role": "Founder & Designer / Developer",
        "start": (2016, 1),
        "end": (2020, 4),
        "location": None,
        "remote": True,
        "sentences": [
            "Founded and ran a two-sided digital marketplace, owning every product decision.",
            "Designed the platform and hired developers for the first version, then learned to build it myself, rebuilding "
            "the front end in Vue.js with a friend handling the back end.",
            "Ran the business day to day: recruiting and onboarding sellers, setting pricing and licensing terms, "
            "integrating Stripe and PayPal payments and handling customer support.",
            "It's the project that turned me into a developer.",
        ],
    },
    {
        "company": "Example Studio",
        "role": "Graphic Designer (Internship)",
        "start": (2013, 9),
        "end": (2013, 10),
        "location": "Example City, Country",
        "remote": False,
        "sentences": ["Designed magazines and flyers and edited photos during a school internship."],
    },
]

# Optional sections: an empty PROJECTS, REFERENCES (with an empty REFERENCES_NOTE) or
# CERTIFICATIONS list is simply not drawn - no empty heading in either CV.

# `card` is what the designed CV shows (title after the dash, description, stack); None = ATS only.
# An optional card["image"] names a file in the template's assets/ folder.
PROJECTS = [
    {
        "name": "Example App One",
        "descriptor": "Product design & development - desktop workflow automation app",
        "bullets": [
            "Built a desktop app in SwiftUI and Python that coordinates multi-step content workflows, from media discovery "
            "and editing to AI-assisted audio and video.",
            "Designed the full interface and integrated several LLM and media APIs.",
        ],
        "card": {
            "title": "workflow automation app",
            "description": "Desktop app coordinating multi-step content workflows, from media discovery and editing to AI-assisted audio and video.",
            "stack": ["SwiftUI", "Python", "LLM & media APIs"],
        },
    },
    {
        "name": "Example App Two",
        "descriptor": "Product design & development - mobile app for iOS and Android",
        "bullets": [
            "Designed and built an app in React Native and Expo that estimates what a second-hand item is worth from a "
            "single photo, combining AI with live marketplace prices.",
            "Compared several AI models against real sold listings to choose the most accurate one, launching the app in 8 languages.",
        ],
        "card": {
            "title": "iOS & Android app",
            "description": "Estimates what a second-hand item is worth from a single photo, combining AI with live marketplace prices.",
            "stack": ["React Native", "Expo", "Vision models", "Marketplace APIs"],
        },
    },
    {
        "name": "Example Client Platform",
        "descriptor": "Client project - B2B travel platform, web dashboard and mobile app",
        "bullets": [
            "Designed the manager dashboard and mobile app for a B2B travel platform agencies use to manage bookings, "
            "collections and operations across offices.",
            "Built the front end of the web app in React and the mobile app in React Native.",
        ],
        "card": None,
    },
    {
        "name": "Example Client Marketplace",
        "descriptor": "Client project - multi-vendor marketplace, web and mobile app",
        "bullets": [
            "Designed a marketplace and management dashboard for buying and selling digital products on web and mobile.",
            "Designed and built the full payment flow, including seller commissions and payouts.",
            "Built the web app in Vue.js and the mobile app in Flutter, working with another developer who handled the back end.",
        ],
        "card": None,
    },
]

# school, degree, dates, location and sentences are all optional; leave out what is unknown
# (with no school, the degree is shown as the entry title).
EDUCATION = [
    {
        "school": "Example Technical Institute",
        "degree": "Graphic Design Diploma",
        "start": (2009, 9),
        "end": (2014, 6),
        "location": "Example City, Country",
        "sentences": ["Studied layout, typography and design software."],
    },
    {
        "school": "Example High School",
        "degree": "Exchange Semester",
        "start": (2013, 1),
        "end": (2013, 6),
        "location": "Example Town, USA",
        "sentences": ["Completed a semester at an American high school as an exchange student."],
    },
]

# Optional. name is required; issuer and year are optional. Shown compactly in the designed
# sidebar and after Education in the ATS resume; an empty list draws nothing.
# CERTIFICATIONS = [
#     {"name": "Example Cloud Practitioner", "issuer": "Example Cert Body", "year": 2022},
#     {"name": "Example Scrum Master"},
# ]
CERTIFICATIONS = []

# Document properties for the PDFs. Only skills the CV itself states - this is visible, standard
# metadata, not a place to stuff extra keywords.
METADATA = {
    "title": f"{NAME} - {HEADLINE}",
    "author": NAME,
    "subject": f"CV of {NAME}, product engineer working across UI/UX design, front-end development and AI integration",
    "keywords": ", ".join([
        "Product Engineer", "UI/UX Design", "Front-end Development", "Design Systems", "Figma",
        "Vue.js", "Nuxt", "React", "Next.js", "React Native", "TypeScript", "JavaScript",
        "Python", "AI Integration", "LLM APIs", "Workflow Automation", "Remote",
    ]),
}
