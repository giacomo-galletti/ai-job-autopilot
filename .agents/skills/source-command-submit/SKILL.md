---
name: source-command-submit
description: >
  Thin Codex pointer to the slash command /submit, whose canonical text is .claude/commands/submit.md.
---

# /submit (pointer)

Use this skill when the user asks to run `/submit`. The single source of truth is
`.claude/commands/submit.md`: read it and follow it exactly. Read `profile/` first; if it is missing,
run `/onboard`. If the command names a Claude-only tool, use the closest available tool and state
any verification gap.
