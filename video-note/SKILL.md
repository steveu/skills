---
name: video-note
description: Turn a YouTube URL into a durable, linked note in the personal Obsidian vault by driving the brain-mcp `fetch_transcript` and `save_video_note` tools. Synthesises a one-line gist plus timestamped key points from the English transcript, greps the vault for related notes and proposes forward-only wikilinks, then files one re-mineable note into the private `Sources/` staging tier — gating the title, the worth-a-note call, and the links before any write. Use when the user says "video-note", "make a note from this video", "synthesise this YouTube video", or pastes a YouTube URL to capture into the vault.
---

# Video note

Turn a YouTube video into one durable, linked note in the Obsidian vault. Given a URL, fetch the transcript, synthesise a structured note, find and propose links to related existing notes, and write the page — gating the title, the worth-a-note call, and the links rather than auto-filing.

The synthesis is the easy part. This skill earns its keep through **linking** (so the note isn't an orphan) and **curation** (so the vault doesn't fill with low-signal AI summaries). A tidy summary is trivial to produce; the discipline is deciding whether the video deserves a note at all, and wiring it into what's already there.

Sibling to the other ingestion skills (`capture`, `add-recipe`, `synthesise`). Architecture is recorded in `~/brain/docs/adr/0004-sources-staging-tier-for-ingested-content.md` — read it if anything below is unclear; the rules here implement it.

## Why this drives brain-mcp tools

One skill, one path. The transcript fetch and the file write both run server-side via brain-mcp, so the same SKILL.md works from Claude Code on the M4 and from claude.ai. The skill is the adapter and the gate; the engine lives in brain-mcp.

ADR 0004 is amended: `Sources/` stays a private staging tier, but `save_video_note` is **write-only** — brain-mcp never reads `Sources/` back to a caller, so the ADR 0003 read boundary is preserved. The dedupe check happens inside the tool, not via a vault grep.

## Scope

- **Yes:** fetch an English transcript for a YouTube URL, synthesise a gist + timestamped key points, grep the vault for related notes, propose forward-only wikilinks, and write one note to `Sources/` after approval.
- **Yes:** downgrade a thin video — recommend a one-line capture into today's daily (or skip) when there isn't enough signal for a note. Curation is the point.
- **No:** editing any existing note. Linking is forward-only — the new note links *out*; Obsidian's backlinks pane covers discovery. Promoting ideas into `People/` / `Projects/` / `Work/` is the synthesis workflow's job, under human judgement.
- **No:** auto-filing. The title, the worth-a-note call, and the proposed links are all gated.
- **No:** overwriting an existing source note for the same URL (protects hand-written `## My takeaways`). Re-running re-mines; see below.
- **No:** non-English transcripts / translation; storing the raw transcript; bulk ingestion of many URLs at once.

## Vault config

Read `~/brain/AGENTS.md` first — the source of truth for the privacy tiers and directory map. `Sources/` is a **private staging tier**: never allowlisted for read, never served back by brain-mcp. The `save_video_note` tool is a deliberate write-only carve-out — it can file into `Sources/` but never reads it back to any caller. You don't choose the path; the tool derives the filename from the title.

## Transcript fetch

Call the brain-mcp **`fetch_transcript`** tool with the URL. It runs the bgutil-aware yt-dlp invocation server-side, prefers manual English subtitles over auto-captions, and returns one JSON object with a `status` field. Branch on it:

- **`ok`** — read `transcript` (inline `[mm:ss] line` body) and synthesise from it. Also use `id`, `title`, `channel`, `durationHuman`, `webpageUrl`, `captionKind`.
- **`no-transcript`** — no usable English captions. Do **not** write a note. Surface the reason and offer a one-line downgrade to the daily (with the title + URL) or skip. Expected for music/visual-heavy videos.
- **`error`** — the fetch failed (unavailable, private, bot-detection, bad URL). Relay the `reason` plainly. Don't retry blindly or write anything. Persistent bot-detection on an otherwise-public video usually means the server's PO-token stack needs attention — say so rather than guessing.

The transcript only lives in the response — it's never persisted on disk. To re-mine a video later, re-run the skill on the URL.

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

- **Frontmatter** is a closed set — exactly `source`, `channel`, `captured`. Don't add `tags`, `type`, `duration`, or anything else; extending it is a deliberate edit to this skill, not an on-the-fly choice. `captured` is today's date in Europe/London — set by the tool, not the model.
- **Gist** — one line, the durable anchor. Names what the video is and why it's worth re-mining. Not a generic "this video discusses…".
- **`## Key points`** — the synthesised substance. Pass each as `{text, seconds}`; the tool renders `- <text> — [[mm:ss]](https://youtu.be/<id>?t=<seconds>)`. `seconds` is the integer second offset of the source `[mm:ss]` marker in the transcript. Preserve technical specifics (names, numbers, claims) verbatim; British English in the connective prose. Number of points follows the content — don't pad a thin video to look substantial.
- **`## My takeaways`** — the user's own layer, kept across re-mines. At save, optionally ask **one** question ("Anything you want to note before I save?"); pass the answer as the `takeaways` argument, or omit it and the tool writes the scaffold line so the section exists for later. Never invent takeaways on the user's behalf.
- **`## Source`** — title link back to the video plus channel and duration.
- **Filename** — `Sources/<Title>.md`, Title Case from the video title, stripped of clutter (` | TED`, `(Official Video)`, `[4K]`) — done by the tool. Pass the raw video title; the tool sanitises.

## Process

1. **Get the URL.** From the user's message or ask for it.
2. **Fetch.** Call `fetch_transcript(url)`. Branch on `status` (see above). On `no-transcript` / `error`, stop here — offer downgrade or relay the error; write nothing.
3. **Synthesise.** From the inline `transcript`, draft the gist and key points. For each point, capture the integer `seconds` derived from the `[mm:ss]` (or `[h:mm:ss]`) marker at the start of the source line. Form an honest view of the signal: is this worth a standing note, or is it thin?
4. **Find links.** Extract the entities the note is about (people, projects, topics, tools). Use the brain-mcp **`grep`** tool to search the vault — only allowlisted folders are reachable, which is the point — for existing notes that match. Build a forward-only link proposal: which entity maps to which existing note. Don't propose links to notes that don't exist, and don't plan any edit to those notes.
5. **Gate — propose and wait.** In one turn, show: the proposed **title**, the **gist**, a **recommendation**, and the **proposed wikilinks** (entity → existing note). Lead with the recommendation in `synthesise`'s voice:
   - **Write the note** — enough signal and a clear shape.
   - **Downgrade to a one-line daily capture** — thin, or near-useless transcript (a music video's lyrics, a vlog with no durable ideas). Say what it'd capture.
   - **Skip** — nothing worth keeping. Don't apologise for this; it's the curation working.
   Then wait for the verdict. Accept approve / approve-with-edits (different title, different links, different verdict) / reject. **Write nothing before explicit go-ahead.**
6. **Save.** Once approved, call `save_video_note` with `url`, `title`, `channel`, `durationHuman`, `gist`, `key_points: [{text, seconds}, ...]`, optional `takeaways`. The tool refuses to overwrite an existing note for the same video — if it returns `{status: "exists", path}`, surface that path to the user and ask how to proceed; never improvise a different title to dodge it. On `{status: "ok", relativePath}`, confirm in one line: `Saved — <relativePath> (N key points, M links).`

## When to stop and ask

- The transcript fetch returns `no-transcript` or `error` — offer downgrade / relay the reason; don't improvise a note.
- `save_video_note` returns `{status: "exists"}` — surface the existing file and ask how to proceed (keep the existing note, or delete it manually to force a fresh write). Never rename the title to bypass the check.
- An entity is ambiguous (could match more than one existing note, or you're unsure a ghost link is wanted) — propose, don't assume.
- The video's content is plainly Hublsoft / work-sensitive — stop. The red line in `~/.claude/CLAUDE.md` applies; Hublsoft content doesn't belong in any vault folder outside `Work/`, and `save_video_note` only writes to `Sources/`.
- The user pastes several URLs — do one at a time; bulk ingestion is a curation risk and out of scope.

## Anti-patterns

- Writing a note before the gate is approved, or auto-filing without showing the title and links.
- Editing an existing note to add a backlink. Linking is forward-only — Obsidian's backlinks pane handles discovery.
- Writing a note for a video with no usable transcript "anyway" — that's exactly the junk the skill exists to prevent.
- Picking a different title to bypass `save_video_note`'s `exists` response — surface the existing note instead.
- Padding key points to make a thin video look substantial, or burying the gist under AI filler.
- Inventing frontmatter fields, or inventing the user's takeaways.
- Keeping the raw transcript — in the chat or anywhere on disk. It's transient; re-mine by re-running.
- Hand-rolling a `yt-dlp` invocation or any local transcript fetch — the only path is `fetch_transcript`.
- Reaching for a note when a one-line daily capture (or nothing) is the honest call.
