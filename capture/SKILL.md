---
name: capture
description: Append a thought, observation, or idea to the personal Obsidian vault by calling the brain-mcp `capture` tool, which writes to today's daily note. Use when the user says "capture this", "save this thought", "save to brain", "remember this in brain", or otherwise asks to file something into their personal notes. NOT for code TODOs, bug tickets, or project work tracking — only personal vault content.
---

# Capture

File a thought into the personal Obsidian vault by calling the **brain-mcp `capture` tool**. The tool takes a single `thought: string` and appends it to today's daily note (`vault/YYYY-MM-DD.md`, date computed in Europe/London), creating the file if it does not exist. There is no parameter to override the destination in v1 — if the thought belongs in a topic note rather than the daily note, stop and ask.

Match the vault's existing conventions — do not impose Zettelkasten structure, atomic-note IDs, or templates the vault is not already using.

## Scope

Capture is for personal notes only — daily entries, project updates, ideas, observations about people, places, or activities. It is not for:

- Code TODOs or bugs (use the issue tracker or a code comment).
- Hublsoft work content (day-job — never goes in the brain vault).
- Anything the user is actively drafting in another app or PR — capture is for fast, low-friction filing, not authoring long documents.

If the request looks like one of the above, push back and suggest a better home before writing anything.

## Where it goes

The brain-mcp `capture` tool only writes to today's daily note. So:

- **Today's daily note** — the only destination v1 supports. The thought is appended as a new paragraph at the end of the file.
- **A topic note** (project, person, recipe) — not supported by the tool yet. If the thought plainly belongs in one, stop and ask the user how they want to proceed.

If torn between the two, default to the daily note — a misfiled daily-note entry is forgiving; a misfiled topic note is harder to find later.

## Conventions to match

Shape the thought to fit the vault's style before passing it to `capture`:

- **British English** in prose.
- **`[[Wiki-links]]`** for people, projects, places, and recurring activities. It is fine to wiki-link a target that may not yet have a note (Obsidian shows these as ghost links) — but do **not** try to create the target note. If the user clearly wants a new person/project page, ask.
- **Scan recent conversation turns** for vault entities just created or referenced (a recipe saved via `add_recipe`, a note just edited, a person just added) and convert plain-prose mentions in the thought to `[[wiki-links]]` before calling `capture`. Same rules as above — ghost links are fine, do not try to create the target.
- **Terse, paragraph-style** in daily notes — not bulleted with `-`. One thought per paragraph.
- **Frontmatter** never goes in daily notes — do not add any.
- **Voice**: preserve the user's wording. Do not summarise, expand, or "improve" the thought. Light copy-edit for grammar only if obviously needed.

## Process

1. Identify what the user wants captured. If it is a long passage of conversation, distil to the essential thought and confirm the wording with the user before calling the tool.
2. Confirm the destination is today's daily note (the only option in v1). If the thought belongs in a topic note instead, stop and ask.
3. Call `capture(thought)`.
4. Confirm to the user in one line, echoing the tool's reply (e.g. "Captured — appended to `2026-05-07.md`").

## When to stop and ask

- The thought plainly belongs in a topic note rather than the daily note — v1 has no tool for that yet.
- Creating a new top-level note, or any new file under `Work/`, `People/`, `Recipes/`, `Templates/` — not supported by the tool.
- Editing an existing note's frontmatter or restructuring its sections — not supported by the tool.
- The thought introduces PII for a person not already named in the vault — the brain vault is treated as sensitive; confirm before adding new people.
- The user said "capture this" but the content is plainly code-shaped (TODOs, bug reports, project tickets) — surface and redirect.
- The brain-mcp tool is unavailable or returns an error — surface plainly; do not attempt a workaround that bypasses the tool.

## Anti-patterns

- Inventing Zettelkasten IDs, "see also" footers, or atomic-note structures the vault does not already use.
- Adding tags the user did not ask for.
- Pasting captured content into other projects' prompts or logs — vault content is sensitive by default.
