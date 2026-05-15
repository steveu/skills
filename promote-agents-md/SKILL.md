---
name: promote-agents-md
description: Triage AGENTS.md candidate queues populated by the SessionEnd `propose-agents-md` hook. Walks through candidates one at a time — user-scope and current-project — showing each proposed addition with its target file and section, then waits for an approve / edit / reject / defer verdict before moving on. Use when the user says "/promote-agents-md", "triage agents-md candidates", "promote candidates", or asks to apply the pending AGENTS.md suggestions.
---

# promote-agents-md

The companion to the `propose-agents-md` SessionEnd hook. The hook drops candidate AGENTS.md additions into two queue files; this skill walks the user through them, one at a time, and applies the approved ones to the right `AGENTS.md` file.

## Scope

- **Yes:** read both queues, walk the user through each pending candidate, apply approved additions to the target `AGENTS.md`, remove actioned/rejected candidates from the queue.
- **Yes:** create a target `AGENTS.md` if it doesn't exist yet, seeded from the approved candidates for that scope. Confirm first.
- **No:** rewriting or restructuring `AGENTS.md` beyond the proposed additions. The skill is additive — section reorganisation is out of scope.
- **No:** batching verdicts. Each candidate gets its own approval; applied immediately before moving on.
- **No:** generating new candidates. Proposals come from the SessionEnd hook only.

## Queue locations

- **User-scope queue:** `~/ai/.agents-md-candidates.md` (in-repo, synced to other machines via `sync-memory.sh`).
- **Project-scope queue:** `~/data/<project-name>/agents-md-candidates.md` (out-of-repo, per-machine). `<project-name>` is the basename of the current git toplevel (or cwd basename if not in a repo).

## Candidate format

The hook writes each candidate as an H2 section in the queue file:

```markdown
## 2026-05-15T14:32Z — British English in prose
- target: ~/ai/AGENTS.md, section "How to talk to me"
- scope: user
- evidence: "use British English in prose" (this session)

Proposed addition:
> - **British English** in prose I'll see. Code identifiers stay whatever the codebase uses.
```

Parse by `## ` headers. Each H2 section is one candidate; the body has the metadata + a block-quoted proposed addition.

## Process

1. **Locate both queues.** Resolve project name from git toplevel (or cwd basename). Read `~/ai/.agents-md-candidates.md` and `~/data/<project-name>/agents-md-candidates.md`. Note which exist; an empty or missing file means zero candidates for that scope.

2. **If both empty, stop and say so.** "No candidates pending — nothing to triage." Don't invent content.

3. **Show the triage summary once.** Count user-scope and project-scope candidates. Announce the walk-through order: project-scope first (more local, faster decisions), then user-scope. Within each scope, oldest-first by the timestamp in the H2 header.

4. **For each candidate, in order:**

   a. **Quote the candidate.** Show the H2 title, the target file/section, the scope, the evidence, and the proposed addition verbatim. Include the queue file path and line number for the H2 header so the user can navigate.

   b. **Lead with a recommendation.** One of:
      - **Apply as-is** — the addition is clean, sits cleanly under the target section, and doesn't duplicate existing content. This is the default when nothing looks off.
      - **Apply with edit** — the substance is right but the wording needs a tweak. State the specific change and why.
      - **Reject** — already covered by existing AGENTS.md content (cite the line), or proposal is too situational to be durable. State which.
      - **Defer** — useful signal but the wording isn't settled or the user might want to phrase it themselves. Say what would change your mind.

      Confident phrasing, one verdict, one-line why. Mirror grill-me / synthesise: "I'd apply because X" beats "you might want to consider applying".

   c. **Verify the target file exists.** Before recommending "apply", check that the target `AGENTS.md` exists. If it doesn't (e.g. project has no AGENTS.md yet), flag it and ask whether to create it. On approval, create the file with a minimal skeleton (top-level `# AGENTS.md` header + the new section) and proceed.

   d. **Wait for the user's verdict.** Accept:
      - `apply` / `yes` / `go` → apply the proposed addition to the target file, then remove the H2 section from the queue. Confirm in one line: `Applied to <target> (+N lines); removed from <queue>.`
      - `apply with edit: <text>` (or just a free-text rewrite) → apply the edited version, remove from queue, confirm.
      - `reject` / `no` / `skip` → remove from queue without applying. Confirm: `Rejected; removed from <queue>.`
      - `defer` / `come back later` → leave in queue. Confirm: `Deferred; still in <queue>.`

   e. **Apply immediately.** Write to the target `AGENTS.md` and remove from the queue *before* moving to the next candidate. Each candidate's writes land before the next one's triage begins. If the user stops the walk-through, nothing is left half-done.

5. **At the end of the walk-through**, print a short summary: applied N, rejected M, deferred K. Don't keep proposing.

## Applying an addition

- **Target section exists** — append the block-quoted line(s) to the end of that section, preserving the section's existing bullet style and tone. Strip the leading `> ` from the proposed addition before pasting (the queue stores it block-quoted; the AGENTS.md gets it as plain markdown).
- **Target section is "new"** — append a new section to the end of the file (or to a sensible position if the user specifies). Confirm placement before writing.
- **Multiple candidates target the same section in one walk-through** — apply each as it's approved. Don't try to merge or order them; the user can refactor later.

## Removing from the queue

Remove the entire H2 section, including the H2 header line itself and all body content up to (but not including) the next `## ` header or end-of-file. Preserve any non-candidate prose elsewhere in the queue file (e.g. a top-of-file header explaining what the file is). If the queue file becomes empty (no remaining H2 sections), leave the file in place but empty rather than deleting it — keeps the path stable for the SessionStart nudge.

## When to stop and ask

- Two candidates propose contradictory additions — surface and let the user pick one (or both, with a note).
- A candidate's target section doesn't exist in the target AGENTS.md and the candidate says "section: X" rather than "new" — flag the mismatch.
- The proposed addition would duplicate or substantially overlap with existing AGENTS.md content the candidate didn't catch — surface the overlap, recommend reject.
- The target file doesn't exist and the user hasn't decided whether to create it.

## Anti-patterns

- Charging through candidates without per-candidate verdicts. The walk-through is the skill's primary value.
- Apologising for "reject" or "defer" recommendations. They're first-class.
- Batching applies — writing N approved candidates to AGENTS.md in one go at the end. Each lands as approved.
- Rewriting the proposed addition silently — if you'd phrase it differently, recommend "apply with edit" and show the diff.
- Deleting the queue file outright. Leave it in place if empty.
- Restructuring AGENTS.md sections, renaming headings, or "cleaning up" beyond the proposed addition. Out of scope.
- Auto-creating a missing target AGENTS.md without asking — file creation is a meaningful decision.
