---
name: footy
description: Create a match note in the personal Obsidian vault for the user's son's football teams (Fulford FC, Fulford School) by calling the brain-mcp `create_match` tool. Use when the user says "/footy", "log a match", "new match note", "match note for [team]", "after the [Fulford] game", "post-match note", or asks to file a record of a specific football match against an opposition. NOT for capturing general thoughts about football (use capture for that).
---

# Footy

Create a match note in the Obsidian vault by calling the **brain-mcp `create_match` tool**. The tool takes `opposition`, `team`, and an optional `date` (YYYY-MM-DD). It reads `vault/Templates/Match.md`, substitutes the date / opposition / team fields and the H1 placeholders, and writes the result to `vault/Matches/<date> — <team> vs <opposition>.md`. The skill's job is to collect the three arguments and call the tool — nothing else.

## Scope

This skill is for **one match note per invocation**. It is not for:

- Season summaries, league tables, or aggregate analysis (those run over existing match notes — not new files).
- Capturing a general football thought (use `capture` — it goes in the daily note).
- Any sport that isn't the user's son's football. If asked for rugby, cricket, etc., stop and surface — there's no template for those.

## Q&A flow

Ask only what's needed. Skip questions whose answer is already in the user's request.

1. **Opposition** — required, freeform. Lightly title-case (`heslington` → `Heslington`). If the user already gave it in their message, don't re-ask.
2. **Team** — `Fulford FC` or `Fulford School`. If the user's request mentions "school" or "club", infer without asking. If the request gives no signal, default to `Fulford FC`.
3. **Date** — optional. If the user gave a relative phrase ("today", "tomorrow", "this Thursday", "last Saturday"), convert to `YYYY-MM-DD` (Europe/London) and pass it. If the user did not mention a date, **omit the argument** — the tool defaults to the next Saturday on or after today.

**Do not ask** about: result, minutes played, position, pitch condition, focus area, self-rating, importance, or event tallies. The template's existing defaults handle these (`importance: standard`, `minutes: full`, `position: CM`); the rest are filled in after the match by the user directly. The skill's job is the skeleton.

## Calling the tool

Once opposition and team are known, call `create_match` with:

- `opposition`: cleaned string (no slashes or null bytes; trimmed; lightly title-cased).
- `team`: `"Fulford FC"` or `"Fulford School"` (verbatim, including the space and capitalisation).
- `date`: `YYYY-MM-DD` if the user specified one, otherwise omit.

The tool returns a confirmation like `created Matches/2026-05-09 — Fulford FC vs Heslington.md`. Echo that back in one short line. Do not embellish.

## Errors

- `match already exists: Matches/...` — the tool refuses to overwrite. Tell the user a note for that exact team / opposition / date is already in the vault; ask whether they meant to edit the existing one or whether the date / opposition is wrong.
- `template not found at Templates/Match.md` — the template is missing from the vault. Surface this; do not retry.
- Any other error — surface verbatim. Don't guess at the cause.

## Conventions

- **British English** in any prose you write (e.g. when echoing the confirmation, or when surfacing errors).
- **Pluralising / abbreviating team names is wrong** — `FC` stays `FC`, `Fulford School` is not `FS`.
- **No `[[wiki-links]]`** in the arguments — opposition names are plain strings, not Obsidian links. The MCP tool writes them as-is.

## Anti-patterns

- Calling `create_match` with a guessed opposition because the user said "log the match" without naming one. Ask first.
- Filling in `date` with `today` or `next saturday` literally — the tool wants `YYYY-MM-DD` or omitted.
- Calling `create_match` more than once for the same prompt (e.g. "logging both Fulford FC and Fulford School matches") without explicitly confirming the team-by-team plan with the user first. The skill is one match per invocation.
- Using `capture` for a match note, or `create_match` for a non-match thought.
