---
name: source-command-mail-cleanup
description: >
  Thin Codex pointer to the slash command /mail-cleanup, whose canonical text is .claude/commands/mail-cleanup.md.
---

# /mail-cleanup (pointer)

Use this skill when the user asks to run `/mail-cleanup`. The single source of truth is
`.claude/commands/mail-cleanup.md`: read it and follow it exactly. Read `profile/` first; if it is missing,
run `/onboard`. If the command names a Claude-only tool, use the closest available tool and state
any verification gap.
