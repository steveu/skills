---
name: footy
description: Create a match note in the personal Obsidian vault for the user's son's football teams (Fulford FC, Fulford School) by calling the brain-mcp `create_match` tool. Use when the user says "/footy", "log a match", "new match note", "match note for [team]", "after the [Fulford] game", "post-match note", or asks to file a record of a specific football match against an opposition. NOT for capturing general thoughts about football (use capture for that).
---

# Footy

Create a match note in the Obsidian vault by calling the **brain-mcp `create_match` tool**. The tool reads `vault/Templates/Match.md`, fills the date / opposition / team fields and any optional pre-match fields the user front-loaded, and writes the result to `vault/Matches/<date> — <team> vs <opposition>.md`. The skill's job is to collect the arguments — required ones via Q&A, optional ones by extracting from the user's prompt — and call the tool. Nothing else.

## Scope

This skill is for **one match note per invocation**. It is not for:

- Season summaries, league tables, or aggregate analysis (those run over existing match notes — not new files).
- Capturing a general football thought (use `capture` — it goes in the daily note).
- Any sport that isn't the user's son's football. If asked for rugby, cricket, etc., stop and surface — there's no template for those.

## Q&A flow

Extract whatever's in the user's prompt. Ask only for what's missing-and-important. Don't batch — ask one question at a time.

1. **Opposition** — required. If not in the prompt, **ask**. Lightly title-case the answer (`heslington` → `Heslington`).
2. **Team** — `Fulford FC` or `Fulford School`. If the user's request mentions "school" or "club", infer without asking. If the request gives no signal, default to `Fulford FC` — don't ask.
3. **Focus area** — pre-match focus for the player ("using your eyes", "first touch"). If not in the prompt, **ask**: "what's the focus this week?" Fills both `focus_area:` frontmatter and the body's `## Focus from this match` section. If the user shrugs or says "nothing in particular", omit and move on.
4. **Date** — optional. If the user gave a relative phrase ("today", "tomorrow", "this Thursday", "last Saturday"), convert to `YYYY-MM-DD` (Europe/London) and pass it. If the user did not mention a date, **omit the argument** — the tool defaults to today (Europe/London). Only ask if the date signal is genuinely ambiguous (e.g. "the match" mid-week with no other hint).

**Never ask** about the other optional pre-match fields (`pitch_type`, `pitch_condition`, `importance`, `notes`) — only fill them when the user front-loads them. **Never ask** about post-match fields (result, minutes played, position, self-rating, event tallies) — the user fills those in directly after the match.

## Other optional pre-match fields

Extract these from the user's prompt when present. **Never ask for them** — if the user didn't front-load them, omit the argument and the template default stands.

- **`pitch_type`** — surface type, e.g. `grass`, `3G`, `astroturf`. Template defaults to `grass`. Pass only if the user names a non-default surface; if they say "grass" explicitly, omit (it's the default — passing it is redundant).
- **`pitch_condition`** — pre-match condition if known, e.g. `wet`, `frozen`, `muddy`. Usually omitted — conditions are normally observed on the day.
- **`importance`** — one of `league` (default), `cup`, `cup-final`, `friendly`, `tournament`. **Inference rules:**
    - "cup final" / "final" of a named cup → `cup-final`
    - "cup" without "final", or a named cup match that isn't a final → `cup`
    - "friendly" → `friendly`
    - "tournament", "festival", "one-day" → `tournament`
    - Anything else, or no signal → omit (template default `league` stands)
- **`notes`** — free-form spillover for context that doesn't fit a frontmatter field: competition name, age group, stage, venue notes, anything else the user provided. Lands in the body `## Context` section. Don't editorialise — keep it close to what the user said. If the user gave nothing extra, omit.

## Calling the tool

Once opposition and team are known, call `create_match` with:

- `opposition`: cleaned string (no slashes or null bytes; trimmed; lightly title-cased).
- `team`: `"Fulford FC"` or `"Fulford School"` (verbatim, including the space and capitalisation).
- `date`: `YYYY-MM-DD` if the user specified one, otherwise omit.
- `pitch_type`, `pitch_condition`, `focus_area`, `importance`, `notes`: as extracted above. Omit any the user did not signal.

The tool returns a confirmation like `created Matches/2026-05-09 — Fulford FC vs Heslington.md`. Echo that back in one short line, then on the next line print the **pitchside URL** so the user can tap stats during the match (see below). Do not embellish.

## Pitchside URL

After `create_match` returns, derive the slug from the filename stem (everything before `.md`) and print:

```
${PITCHSIDE_HOST}/m/<slug>
```

**Slug rule** — lower-case the stem, collapse runs of non-`[a-z0-9]` characters into a single hyphen, trim leading/trailing hyphens. The em-dash, spaces, and any other punctuation all become hyphens.

Example: `2026-05-09 — Fulford FC vs Heslington` → `2026-05-09-fulford-fc-vs-heslington` → `${PITCHSIDE_HOST}/m/2026-05-09-fulford-fc-vs-heslington`.

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
- Asking the user to fill in optional pre-match fields they didn't mention. Extract only what they front-loaded; omit the rest.
- Inventing an `importance` value not in the enum. If the user's signal doesn't map to one of the five values, omit and let `league` stand — don't try to be clever.
- Cramming everything spare into `notes`. If the prompt only had what the frontmatter consumed, omit `notes`. The `## Context` section should be empty when there's nothing to say.
