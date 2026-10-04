---
name: source-command-job-alerts
description: >
  Thin Codex pointer to the slash command /job-alerts, whose canonical text is .claude/commands/job-alerts.md.
---

# /job-alerts (pointer)

Use this skill when the user asks to run `/job-alerts`. The single source of truth is
`.claude/commands/job-alerts.md`: read it and follow it exactly. Read `profile/` first; if it is missing,
run `/onboard`. If the command names a Claude-only tool, use the closest available tool and state
any verification gap.
