---
name: video-note
description: Turn a YouTube URL into a durable, linked note in the personal Obsidian vault. Fetches the English transcript via a bundled yt-dlp helper, synthesises a one-line gist plus timestamped key points, greps the vault for related notes and proposes forward-only wikilinks, then writes one re-mineable note to the private `Sources/` staging tier — gating the title, the worth-a-note call, and the links before any write. Use when the user says "video-note", "make a note from this video", "synthesise this YouTube video", or pastes a YouTube URL to capture into the vault. M4-only (filesystem skill); not for claude.ai.
---

# Video note

Turn a YouTube video into one durable, linked note in the Obsidian vault. Given a URL, fetch the transcript, synthesise a structured note, find and propose links to related existing notes, and write the page — gating the title, the worth-a-note call, and the links rather than auto-filing.

The synthesis is the easy part. This skill earns its keep through **linking** (so the note isn't an orphan) and **curation** (so the vault doesn't fill with low-signal AI summaries). A tidy summary is trivial to produce; the discipline is deciding whether the video deserves a note at all, and wiring it into what's already there.

Sibling to the other ingestion skills (`capture`, `add-recipe`, `synthesise`). Architecture is recorded in `~/brain/docs/adr/0004-sources-staging-tier-for-ingested-content.md` — read it if anything below is unclear; the rules here implement it.

## Scope

- **Yes:** fetch an English transcript for a YouTube URL, synthesise a gist + timestamped key points, grep the vault for related notes, propose forward-only wikilinks, and write one note to `Sources/` after approval.
- **Yes:** downgrade a thin video — recommend a one-line capture into today's daily (or skip) when there isn't enough signal for a note. Curation is the point.
- **No:** editing any existing note. Linking is forward-only — the new note links *out*; Obsidian's backlinks pane covers discovery. Promoting ideas into `People/` / `Projects/` / `Work/` is the synthesis workflow's job, under human judgement.
- **No:** auto-filing. The title, the worth-a-note call, and the proposed links are all gated.
- **No:** overwriting an existing source note for the same URL (protects hand-written `## My takeaways`). Re-running re-mines; see below.
- **No:** non-English transcripts / translation; storing the raw transcript; bulk ingestion of many URLs at once.
- **No:** a claude.ai path. This is a local filesystem skill on the M4 — `Sources/` is private and can't be served by brain-mcp (private takeaways; see ADR 0004).

## Vault config

Read `~/brain/AGENTS.md` first — the source of truth for the privacy tiers and directory map. `Sources/` is a **private staging tier** (same as daily notes): never allowlisted, never served to claude.ai. Don't write vault content into allowlisted folders, and don't link a `Sources/` note's private content into one.

## Transcript fetch

Use the bundled helper — don't hand-roll `yt-dlp` parsing:

```sh
node ~/.claude/skills/video-note/fetch-transcript.mjs "<youtube-url>"
```

It mirrors Eddy's proven path (`--dump-json` → English caption track → json3) but preserves each line's start time for deep-links, and prefers manual subtitles over auto-captions. It prints one JSON object and, on success, writes the timestamped transcript to a temp file rather than to stdout.

Branch on the `status` field:

- **`ok`** — read `transcriptFile` (lines are `[mm:ss] text`) and synthesise from it. Also use `id`, `title`, `channel`, `durationHuman`, `webpageUrl`, `captionKind`.
- **`no-transcript`** — no usable English captions. Do **not** write a note. Surface the reason and offer a one-line downgrade to the daily (with the title + URL) or skip. This is the expected outcome for music/visual-heavy videos.
- **`error`** — yt-dlp failed (unavailable, private, bot-detection, bad URL). Relay the `reason` plainly. Don't retry blindly or write anything. Persistent bot-detection on an otherwise-public video is the one case that may need Eddy's PO-token stack running — say so rather than guessing.

The transcript file is **transient** — discard it after synthesis (`rm` it once the note is written). To re-mine a video later, re-run the skill on the URL; the raw transcript is never kept in the vault.

## Note shape

One note per video under `Sources/`. The gist is the re-mineable asset; key points scale with the video's substance — a meaty talk earns many, a thin one earns few (and may not earn a note at all).

```markdown
---
source: https://www.youtube.com/watch?v=<id>
channel: <Channel name>
captured: YYYY-MM-DD
---

<One-line gist — what this video is and why it's worth keeping. Plain prose, not a label.>

## Key points

- <Point in the user's-vault voice, specifics preserved> — [[12:05]](https://youtu.be/<id>?t=725)
- <Next point> — [[18:40]](https://youtu.be/<id>?t=1120)

## My takeaways

<Either the user's answer to the one save-time prompt, or this scaffold line:>
*(What did this change for you? — fill in on a later pass.)*

## Source

[<Video title>](https://www.youtube.com/watch?v=<id>) — <Channel name>, <durationHuman>
```

- **Frontmatter** is a closed set — exactly `source`, `channel`, `captured`. Don't add `tags`, `type`, `duration`, or anything else; extending it is a deliberate edit to this skill, not an on-the-fly choice. `captured` is today's date (Europe/London).
- **Gist** — one line, the durable anchor. Names what the video is and why it's worth re-mining. Not a generic "this video discusses…".
- **`## Key points`** — the synthesised substance. Each bullet ends with a clickable deep-link: `[[mm:ss]](https://youtu.be/<id>?t=<seconds>)`, seconds = the integer offset of the `[mm:ss]` marker from the transcript. Preserve technical specifics (names, numbers, claims) verbatim; British English in the connective prose. Number of points follows the content — don't pad a thin video to look substantial.
- **`## My takeaways`** — the user's own layer, kept across re-mines. At save, optionally ask **one** question ("Anything you want to note before I save?"); if they pass, write the scaffold line so the section exists for later. Never invent takeaways on the user's behalf.
- **`## Source`** — title link back to the video plus channel and duration.
- **Filename** — `Sources/<Title>.md`, Title Case from the video title, stripped of clutter (` | TED`, `(Official Video)`, `[4K]`). Keep it recognisable.

## Process

1. **Get the URL.** From the user's message or ask for it.
2. **Fetch.** Run the helper. Branch on `status` (see above). On `no-transcript` / `error`, stop here — offer downgrade or relay the error; write nothing.
3. **Synthesise.** Read the transcript file. Draft the gist and key points. Form an honest view of the signal: is this worth a standing note, or is it thin?
4. **Find links.** Extract the entities the note is about (people, projects, topics, tools). Grep the vault — **titles first, then content** — for existing notes that match. Build a forward-only link proposal: which entity maps to which existing note. Don't propose links to notes that don't exist, and don't plan any edit to those notes.
5. **Gate — propose and wait.** In one turn, show: the proposed **title**, the **gist**, a **recommendation**, and the **proposed wikilinks** (entity → existing note). Lead with the recommendation in `synthesise`'s voice:
   - **Write the note** — enough signal and a clear shape.
   - **Downgrade to a one-line daily capture** — thin, or near-useless transcript (a music video's lyrics, a vlog with no durable ideas). Say what it'd capture.
   - **Skip** — nothing worth keeping. Don't apologise for this; it's the curation working.
   Then wait for the verdict. Accept approve / approve-with-edits (different title, different links, different verdict) / reject. **Write nothing before explicit go-ahead.**
6. **Check for a prior note.** Before writing, grep `Sources/*.md` frontmatter for the same `source:` URL. If one exists, **refuse to overwrite** — surface the existing note and ask how to proceed (re-mine into a fresh-named note, or stop). This protects hand-written takeaways.
7. **Write.** `mkdir -p ~/brain/vault/Sources` (first run only), then write `Sources/<Title>.md`. Optionally ask the one takeaways question; otherwise scaffold. Confirm in one line: `Saved — Sources/<Title>.md (N key points, M links).`
8. **Clean up.** `rm` the transcript temp file.

## When to stop and ask

- The transcript fetch returns `no-transcript` or `error` — offer downgrade / relay the reason; don't improvise a note.
- A source note with the same URL already exists — never overwrite; surface and ask.
- An entity is ambiguous (could match more than one existing note, or you're unsure a ghost link is wanted) — propose, don't assume.
- The video's content is plainly Hublsoft / work-sensitive and a proposed link points into an allowlisted folder — stop; the red line in `~/.claude/CLAUDE.md` applies.
- The user pastes several URLs — do one at a time; bulk ingestion is a curation risk and out of scope.

## Anti-patterns

- Writing a note before the gate is approved, or auto-filing without showing the title and links.
- Editing an existing note to add a backlink. Linking is forward-only — Obsidian's backlinks pane handles discovery.
- Writing a note for a video with no usable transcript "anyway" — that's exactly the junk the skill exists to prevent.
- Overwriting a source note for a re-run, silently destroying `## My takeaways`.
- Padding key points to make a thin video look substantial, or burying the gist under AI filler.
- Inventing frontmatter fields, or inventing the user's takeaways.
- Keeping the raw transcript — in the vault or the chat. It's transient; re-mine by re-running.
- Hand-rolling `yt-dlp` invocation instead of using the bundled helper.
- Reaching for a note when a one-line daily capture (or nothing) is the honest call.
