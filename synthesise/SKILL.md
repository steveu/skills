---
name: synthesise
description: Pull recurring threads out of root-level daily notes in the personal Obsidian vault and merge them into topic notes under curated subfolders, leaving a `→ Synthesised into [[X]]` pointer at the top of each contributing daily. Walks through detected topics one at a time — quoting the fragments, leading with a confident recommendation (including "leave for now"), and waiting for the user's verdict before moving on. Use when the user says "synthesise the dailies", "promote daily content", "run a synthesis pass", or asks to see patterns across recent journal entries.
---

# Synthesise

Promote recurring threads from root-level daily notes (`vault/YYYY-MM-DD.md`) into topic notes, while preserving the source fragments in the dailies for historical record. The daily gets a top-of-file pointer (`→ Synthesised into [[<Topic>]] (YYYY-MM-DD).`); the topic note carries the synthesised prose. The skill makes the loop repeatable; it doesn't invent structure beyond what the loop already established.

## Scope

- **Yes:** read root-level daily notes, cluster fragments by topic, propose merges into existing topic notes, write pointers back into dailies.
- **Yes:** propose a new topic note when a thread has no home — but only after asking where it should live.
- **No:** restructuring existing topic notes (renaming sections, reordering, rewriting prose the user has already shaped).
- **No:** deleting or rewriting daily-note content. The pointer is the only change to a daily.
- **No:** synthesising into `Recipes/` or `Templates/` (closed-shape folders with their own skills).
- **No:** batching multiple topics in one invocation. One topic per pass; each gets its own approval.

## Vault config

Read `vault/AGENTS.md` first — it is the source of truth for the privacy tiers (allowlisted vs private), the directory map, and the red-line rules about what content must not cross into allowlisted folders. The skill's job is to honour those rules, not to restate them. If a fragment plausibly belongs in either tier, stop and ask. If a daily fragment mixes content from both tiers, split it before promoting.

## Process

Two phases. Phase 1 walks the user through every detected topic, one at a time, with a per-topic recommendation. Phase 2 is the synthesis flow for any topic the user says yes to — invoked inline from Phase 1, or directly when the skill is called with a topic argument (`/synthesise <topic>`).

### Phase 1 — triage walk-through

1. **Scan and cluster.** Read all root-level `vault/YYYY-MM-DD.md` files. Cluster fragments by `[[wiki-link]]` mentions and prose mentions of the same name. Build the triage list — topic, daily count, fragment count, existing target file (if any).

2. **Show the triage list once** as a compact table. Then announce the walk-through: each topic gets a recommendation, then a verdict before moving on. Don't pre-emptively pull fragments for every topic — do that inside each per-topic turn.

3. **For each topic, in priority order** (highest signal first — most fragments, clearest target, biggest delta from existing note):
   - **Quote the fragments** with `file:line` references. Short fragments inline; long fragments by reference and a one-line gist.
   - **Lead with a recommendation.** Confident phrasing, single verdict, one-line why, the main tradeoff. Mirror grill-me: "I'd X because Y; the cost is Z" beats "you might consider X". Valid recommendations:
     - **Synthesise to `<target>`** — enough signal and a clear home.
     - **Leave for now** — single fragment, low signal, or not mature enough. Say what would change your mind ("leave until at least one more fragment lands", "leave until you've used the tool for a week and have an opinion").
     - **Decide folder first** — fragments are ready but there's no home. Surface the folder options, ask the user to pick, then recommend again.
     - **Re-synthesise** — target already has a pointer from a previous pass; fresh fragments warrant another round.
     - **Out of scope** — belongs in AGENTS.md, the issue tracker, or just doing the thing. Surface and redirect.
   - **"Leave for now" is a first-class recommendation.** Don't apologise for it and don't reach for synthesis when the signal isn't there. The vault's stated mode is "collect mess then organise" — premature structure costs more than it saves.
   - **Wait for the user's verdict.** Accept any of:
     - `synthesise` / `go` / `yes` → run Phase 2 for this topic inline, **write the files**, then move on. Do not queue approved verdicts to apply in a batch later.
     - `leave` / `skip` / `no` → record and move on
     - `defer` / `come back later` → record explicitly so it doesn't quietly drop
     - `actioned <file>` (or just `actioned` if the file is unambiguous from the recommendation) → the fragment has been or will be handled outside the vault (e.g. into `AGENTS.md`, a project repo, an issue tracker). Write an `→ Actioned into <file> (<today>).` pointer to the daily — no topic-note edits, no vault content created. Confirm in one line: `Pointer added to <daily>.`
     - a free-text edit (different target, different scope, different verdict) → discuss in one turn, then re-recommend
   - **Only move to the next topic** once the current one is resolved or explicitly deferred.

4. **At the end of the walk-through**, summarise as a short list: synthesised topics, left topics, deferred topics. Don't keep proposing.

### Phase 2 — per-topic synthesis (verdict: synthesise)

a. **Gather fragments.** List every daily that mentions the topic. Quote each fragment with its `file:line` reference. Include prose mentions, not just wiki-links — the user often writes "the vault" rather than `[[Brain]]`.

b. **Locate the target.** Walk the directory map in `vault/AGENTS.md` looking for an existing `<Folder>/<Topic>.md`. If none exists, ask the user where it should go — folder placement is a privacy decision, never auto-pick.

c. **Categorise each fragment.** For each one, decide:
   - **New** — adds information not already in the target. Include in proposal.
   - **Supersedes** — refines or overturns existing target content. Include with a note: "supersedes line N of target".
   - **Already covered** — semantically present in the target. Skip and say so.
   - **Off-topic** — wiki-link matches but the surrounding sentence is about something else. Skip and say so.

d. **Compose the proposal.** Produce two artefacts in chat, no writes:
   - **Target diff** — unified-diff against the target note showing additions. Preserve the target's section structure; create new sections only when there's a category of content the target doesn't already have.
   - **Daily-note pointers** — for each contributing daily, the exact pointer line that will go at the top of the file: `→ Synthesised into [[<Topic>]] (<today>).` for whole-daily promotions, or `→ <subtopic> synthesised into [[<Topic>]] (<today>).` for partial promotions.

e. **Wait for approval.** Accept blanket approve, approve with edits, or reject. Don't write anything until explicit go-ahead.

f. **Apply immediately.** Write the target note edits and the daily-note pointers *before* returning to Phase 1. One topic's writes land before the next topic's triage begins — no end-of-walk-through batch. Confirm in one line per file edited: e.g. `Updated Work/<Topic>.md (+12 lines); pointers added to 6 dailies.`

g. **Return to Phase 1** for the next topic (when invoked via walk-through). The vault is now in a consistent, committable state — if the user stops the walk-through here, nothing is left half-done.

## Conventions to preserve

- **Pointer format** — mirror the 2026-05-12 anchor exactly. `→ Synthesised into [[<Topic>]] (YYYY-MM-DD).` at the very top of the daily, blank line below, original content unchanged. For partial promotions, prefix with the subtopic: `→ Ralph-loop idea synthesised into [[<Topic>]] (YYYY-MM-DD).`. For fragments actioned into a file outside the vault (e.g. `AGENTS.md`, a project repo), use the `Actioned` variant instead — same shape, no wiki-link, plain filename: `→ "Challenge me" note actioned into AGENTS.md (YYYY-MM-DD).`. Multiple pointers stack as separate lines if a daily contributed to more than one outcome.
- **Voice** — synthesised prose may rephrase across fragments for coherence. The target is a living doc, not a transcript. But preserve technical specifics (numbers, names, dates) verbatim and keep the user's wording where it's already crisp.
- **British English** in target-note prose. Don't change spellings the user already used.
- **Wiki-links** — preserve them when the source had them. Don't add them gratuitously to plain mentions in the target.
- **Frontmatter** — match the target note's existing frontmatter. Don't add fields the target doesn't already have.
- **Dates inline** — when a fragment is sourced from a specific daily, include the date inline (`(YYYY-MM-DD)`) in the synthesised prose so future passes can trace provenance.

## When to stop and ask

- The target note doesn't exist and you need to choose a folder.
- A fragment looks like it should split between two topics.
- A fragment is work-related and the proposed target is in an allowlisted folder.
- The target's section structure has no obvious home for new content — confirm before adding a new section.
- A fragment supersedes existing target content materially — confirm the supersession rather than silently overwriting.
- More than one topic is plausible for a synthesis run.
- A daily note already has a `→ Synthesised into [[<Topic>]]` pointer for the same topic — confirm whether this run is a re-synthesis (replace pointer's date) or whether the daily should be skipped (already promoted).

## Anti-patterns

- Charging through topics without explicit per-topic verdicts. The walk-through is the skill's primary value; respect the cadence.
- Apologising for "leave for now" recommendations or burying them. They're first-class.
- Reaching for synthesis when the signal isn't there — one fragment doesn't make a thread.
- Synthesising multiple topics in one Phase 2 pass.
- Queuing approved verdicts and writing the files in a batch at the end of the walk-through. Each approved topic's writes land before the next topic's triage starts.
- Deleting or rewriting source fragments in dailies. The pointer is the only change.
- Creating new topic notes without explicit confirmation of the folder.
- Promoting partial fragments into allowlisted folders when the surrounding daily-note content is private.
- Adding tags, sections, or frontmatter fields the target didn't already have.
- "Cleaning up" the daily-note ordering or formatting while at it. Out of scope.
- Treating the target as authoritative over the daily — the daily is the historical record, the target is the current shape. If they conflict, surface it.
- Summarising fragments to the point of losing the user's wording on a load-bearing phrase.
