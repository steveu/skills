---
name: capture
description: Append a thought, observation, or idea to the personal Obsidian vault at ~/brain/vault/. Use when the user says "capture this", "save this thought", "save to brain", "remember this in brain", or otherwise asks to file something into their personal notes. NOT for code TODOs, bug tickets, or project work tracking — only personal vault content.
---

# Capture

File a thought into the Obsidian vault at `~/brain/vault/`. Default destination is today's daily note. Match the vault's existing conventions — do not impose Zettelkasten structure, atomic-note IDs, or templates the vault is not already using.

## Scope

Capture is for personal notes only — daily entries, project updates, ideas, observations about people, places, or activities. It is not for:

- Code TODOs or bugs (use the issue tracker or a code comment).
- Hublsoft work content (day-job — never goes in `~/brain/`).
- Anything the user is actively drafting in another app or PR — capture is for fast, low-friction filing, not authoring long documents.

If the request looks like one of the above, push back and suggest a better home before writing anything.

## Where it goes

Pick one:

1. **Today's daily note** (default). Path: `~/brain/vault/YYYY-MM-DD.md` for today's date in the user's local time. Create the file if it does not exist. Append the thought as a new paragraph at the end, separated from prior content by a blank line.
2. **An existing topic note** — only when the thought is plainly an extension of one (a project update, adding to a person note, another step in a recipe). Append under the relevant `##` section, or at the end of the body if no section fits.
3. **A new topic note** — rare. Always ask the user first. If confirmed, mirror the frontmatter and structure of the closest existing note of that kind (project, person, recipe).

If torn between (1) and (2), default to (1). A misfiled daily-note bullet is forgiving; a misfiled topic note is harder to find later.

## Conventions to match

Read a recent daily note and any topic note you might be editing **before** writing — do not guess the style.

- **British English** in prose.
- **`[[Wiki-links]]`** for people, projects, places, and recurring activities. Run `ls ~/brain/vault ~/brain/vault/People` first so you know what already exists. It is fine to wiki-link a target that does not yet have a note (Obsidian shows these as ghost links) — but do **not** auto-create the target note. If the user clearly wants a new person/project page, ask.
- **Terse, paragraph-style** in daily notes — not bulleted with `-`. One thought per paragraph, blank line between. Match the existing length of recent entries.
- **Frontmatter** only on typed notes (project, person, recipe). Daily notes have no frontmatter — do not add any.
- **Voice**: preserve the user's wording. Do not summarise, expand, or "improve" the thought. Light copy-edit for grammar only if obviously needed.

## Process

1. Identify what the user wants captured. If it is a long passage of conversation, distil to the essential thought and confirm the wording with the user before writing.
2. Decide the destination using the rules above. State it in one line before editing (e.g. "Appending to `~/brain/vault/2026-05-07.md`").
3. Read the destination file (or list the relevant vault dir to confirm wiki-link targets) before editing.
4. Append. Never reorder or rewrite existing content in the same edit.
5. Do not commit — `~/brain/` has its own sync that handles git.

## When to stop and ask

- Creating a new top-level note, or any new file under `Work/`, `People/`, `Recipes/`, `Templates/`.
- Editing an existing note's frontmatter or restructuring its sections.
- The thought introduces PII for a person not already named in the vault — `~/brain/` is treated as sensitive; confirm before adding new people.
- The user said "capture this" but the content is plainly code-shaped (TODOs, bug reports, project tickets) — surface and redirect.

## Anti-patterns

- Inventing Zettelkasten IDs, "see also" footers, or atomic-note structures the vault does not already use.
- Adding tags the user did not ask for.
- Editing or quitting Obsidian, running sync scripts, or committing on the user's behalf.
- Pasting captured content into other projects' prompts or logs — vault content is sensitive by default.
