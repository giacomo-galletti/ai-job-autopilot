# /reset - Reset Candidate Profile Data

You are resetting the user's private data so they can start fresh with `/onboard`.

**This command is destructive.** Nothing is deleted until the user types the confirmation word.
Follow these steps in order. It works the same in Claude Code and Codex.

Scopes:

- `profile` - deletes everything inside `profile/` (the gitignored private folder). Tracked files,
  templates, `profile.example/` and all framework files are never touched.
- `documents` - deletes the files the user dropped into `documents/` subfolders.
- `all` - both.

---

## Step 0: Parse scope

Check `$ARGUMENTS` for `profile`, `documents` or `all`. If none is present, ask which one and wait.
Describe each scope in one sentence, as above.

---

## Step 1: Show exactly what will be deleted

Before doing anything, verify `profile/` is gitignored (`git check-ignore profile/` prints `profile/`);
if not, say so and stop, because something is wrong with the checkout.

### If scope includes `profile`:
List every file under `profile/` (use `find profile -type f`). Show the list, grouped, and say whether
`profile/` is already empty. Expect: `profile.md`, `behavioral.md`, `deal-breakers.md`, `forms.md`,
`portals.md`, `search-queries.md`, `cv_content.py`, `theme.json` and anything else the user added.

```
## Profile reset will delete:
- profile/<file> ...  (N files)

NOT touched: profile.example/, templates/, .claude/, .agents/, tools/, tests/.
Generated outputs elsewhere (cv/, cover_letters/, the application tracker, job_scraper/ state, .env)
are not part of this scope and may still contain personal data; they are listed below if present.
```

Then list any of `cv/`, `cover_letters/`, `job_scraper/`, `job_alerts/` and tracker files that exist
and contain user data, so the user can decide to remove them by hand.

### If scope includes `documents`:
List the files in `documents/cv/`, `documents/linkedin/`, `documents/diplomas/`,
`documents/references/`, `documents/projects/`, `documents/postings/` and
`documents/applications/` (subfolders and files). `documents/README.md` is never deleted.

---

## Step 2: Require explicit confirmation

> **This cannot be undone.** Type **`RESET`** (all caps) to confirm, or anything else to cancel.

Only the exact word `RESET` proceeds. Anything else: reply "Reset cancelled. Nothing was changed." and stop.

---

## Step 3: Execute

### Profile reset
```bash
find profile -mindepth 1 -delete
```
Keep the `profile/` folder itself. If it does not exist, create it with `mkdir -p profile`.

### Documents reset
```bash
rm -f documents/cv/*
rm -f documents/linkedin/*
rm -f documents/diplomas/*
rm -f documents/references/*
rm -f documents/projects/*
rm -f documents/postings/*
rm -rf documents/applications/*/
```
Do not delete the folders or `documents/README.md`.

---

## Step 4: Report

```
## Reset complete
### Cleared
[what was deleted]
### Unchanged
[what was already empty or intentionally kept]
```

Next steps:

- Profile reset: "`profile/` is now empty. Run `/onboard` to rebuild it."
- Documents reset: "`documents/` is now empty. Add new documents and run `/onboard`."
- Both: "Everything personal is cleared. Add documents or use the CV-import / interview path, then run `/onboard`."
