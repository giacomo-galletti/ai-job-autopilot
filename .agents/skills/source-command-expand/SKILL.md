---
name: source-command-expand
description: >
  Thin Codex pointer to the slash command /expand, whose canonical text is .claude/commands/expand.md.
---

# /expand (pointer)

Use this skill when the user asks to run `/expand`. The single source of truth is
`.claude/commands/expand.md`: read it and follow it exactly. Read `profile/` first; if it is missing,
run `/onboard`. If the command names a Claude-only tool, use the closest available tool and state
any verification gap.
