---
name: capture
description: Append a thought, observation, or idea to the personal Obsidian vault by committing to the GitHub repo `steveu/brain` via the GitHub connector. Use when the user says "capture this", "save this thought", "save to brain", "remember this in brain", or otherwise asks to file something into their personal notes. NOT for code TODOs, bug tickets, or project work tracking — only personal vault content.
---

# Capture (cloud)

File a thought into the Obsidian vault hosted at `github.com/steveu/brain`. The vault content sits at `vault/` in that repo. Default destination is today's daily note. Match the vault's existing conventions — do not impose Zettelkasten structure, atomic-note IDs, or templates the vault is not already using.

This skill writes via the **GitHub connector**, not a local filesystem. Every successful capture produces a commit on `main` of `steveu/brain`. The user's Mac mini runs a sync loop every 10 minutes that pulls from GitHub and pushes to iCloud, so captures reach iOS Obsidian within that window and Mac Obsidian on the next pull.

## Scope

Capture is for personal notes only — daily entries, project updates, ideas, observations about people, places, or activities. It is not for:

- Code TODOs or bugs (use the issue tracker or a code comment).
- Hublsoft work content (day-job — never goes in the brain repo).
- Anything the user is actively drafting in another app or PR — capture is for fast, low-friction filing, not authoring long documents.

If the request looks like one of the above, push back and suggest a better home before writing anything.

## Where it goes

Pick one:

1. **Today's daily note** (default). Path in repo: `vault/YYYY-MM-DD.md` for today's date in the user's local time (Europe/London). Create the file if it does not exist. Append the thought as a new paragraph at the end, separated from prior content by a blank line.
2. **An existing topic note** — only when the thought is plainly an extension of one (a project update, adding to a person note, another step in a recipe). Append under the relevant `##` section, or at the end of the body if no section fits.
3. **A new topic note** — rare. Always ask the user first. If confirmed, mirror the frontmatter and structure of the closest existing note of that kind (project, person, recipe).

If torn between (1) and (2), default to (1). A misfiled daily-note bullet is forgiving; a misfiled topic note is harder to find later.

## Conventions to match

Read a recent daily note and any topic note you might be editing **before** writing — do not guess the style.

- **British English** in prose.
- **`[[Wiki-links]]`** for people, projects, places, and recurring activities. List `vault/` and `vault/People/` (via the GitHub connector) before writing so you know what already exists. It is fine to wiki-link a target that does not yet have a note (Obsidian shows these as ghost links) — but do **not** auto-create the target note. If the user clearly wants a new person/project page, ask.
- **Terse, paragraph-style** in daily notes — not bulleted with `-`. One thought per paragraph, blank line between. Match the existing length of recent entries.
- **Frontmatter** only on typed notes (project, person, recipe). Daily notes have no frontmatter — do not add any.
- **Voice**: preserve the user's wording. Do not summarise, expand, or "improve" the thought. Light copy-edit for grammar only if obviously needed.

## Process

1. Identify what the user wants captured. If it is a long passage of conversation, distil to the essential thought and confirm the wording with the user before writing.
2. Decide the destination using the rules above. State it in one line before editing (e.g. "Appending to `vault/2026-05-07.md` on `steveu/brain`").
3. Use the GitHub connector to read the destination file's current contents (or note that it doesn't yet exist). If you may need to wiki-link a person or project, also list `vault/People/` and the root of `vault/` in the same step.
4. Construct the new file contents in memory: existing contents + blank line + the thought + trailing newline. Never reorder or rewrite existing content.
5. Write the file back via the GitHub connector with a commit on `main`. Commit message format: `capture: <first ~60 chars of the thought, single line>` — distinct from the auto-sync commits the launchd loop produces.
6. Confirm to the user in one line which file was updated and the commit ref or message used.

## When to stop and ask

- Creating a new top-level note, or any new file under `vault/Work/`, `vault/People/`, `vault/Recipes/`, `vault/Templates/`.
- Editing an existing note's frontmatter or restructuring its sections.
- The thought introduces PII for a person not already named in the vault — the brain repo is treated as sensitive; confirm before adding new people.
- The user said "capture this" but the content is plainly code-shaped (TODOs, bug reports, project tickets) — surface and redirect.
- The GitHub connector is unavailable or returns a permission error — surface plainly; do not attempt a workaround that bypasses the connector.

## Anti-patterns

- Inventing Zettelkasten IDs, "see also" footers, or atomic-note structures the vault does not already use.
- Adding tags the user did not ask for.
- Creating a pull request, branch, or draft commit instead of a direct commit to `main`. Captures go straight to `main`; the sync loop expects that.
- Force-pushing, rewriting history, or touching anything outside `vault/`.
- Pasting captured content into other projects' prompts or logs — vault content is sensitive by default.
