---
name: promote-agents-md
description: Triage the proposal queues populated by the SessionEnd `propose-agents-md` hook. Each candidate is one of two kinds — an AGENTS.md rule or a memory entry. Walks through user-scope and current-project candidates one at a time, showing each proposal with its destination, then waits for an approve / edit / reject / defer verdict before moving on. Use when the user says "/promote-agents-md", "triage agents-md candidates", "promote candidates", or asks to apply the pending proposals.
---

# promote-agents-md

The companion to the `propose-agents-md` SessionEnd hook. The hook drops candidates into two queue files; this skill walks the user through them, one at a time, and applies the approved ones to the right destination — either an `AGENTS.md` file or a memory dir.

## Scope

- **Yes:** read both queues, walk the user through each pending candidate, apply approved candidates to the right destination, remove actioned/rejected candidates from the queue.
- **Yes:** create a missing target `AGENTS.md` if approved, seeded from the candidate. Confirm first.
- **No:** rewriting or restructuring `AGENTS.md` / memory files beyond the proposed content. The skill is additive — section reorganisation is out of scope.
- **No:** batching verdicts. Each candidate gets its own approval; applied immediately before moving on.
- **No:** generating new candidates. Proposals come from the SessionEnd hook only.

## Queue locations

- **User-scope queue:** `~/ai/.agents-md-candidates.md` (in-repo, synced cross-machine via `sync-memory.sh`).
- **Project-scope queue:** `~/data/<project-name>/agents-md-candidates.md` (out-of-repo, per-machine). `<project-name>` is the basename of the current git toplevel (or cwd basename if not in a repo).

The filename still says "agents-md" for muscle-memory reasons; the queue holds candidates of both kinds (`kind: agents-md` and `kind: memory`).

## Candidate kinds

Each H2 section in the queue is one candidate. The first metadata line — `- kind:` — chooses the destination.

**`kind: agents-md`** (rule, convention, preference, decision):

```markdown
## 2026-05-15T14:32Z — British English in prose
- kind: agents-md
- target: ~/ai/AGENTS.md, section "How to talk to me"
- scope: user
- evidence: "use British English in prose" (this session)

Proposed addition:
> - **British English** in prose I'll see. Code identifiers stay whatever the codebase uses.
```

**`kind: memory`** (fact, context, observation, reference):

```markdown
## 2026-05-15T14:32Z — Tailscale Funnel exposes brain-mcp
- kind: memory
- scope: project
- type: reference
- name: tailscale-funnel-brain-mcp
- description: brain-mcp is exposed externally via Tailscale Funnel; check the Grafana board for request-path issues
- evidence: "the Funnel URL is what hits brain-mcp from outside the tailnet"

Proposed memory body:
> brain-mcp is reachable from outside the tailnet via a Tailscale Funnel at `<hostname>`. Oncall watches the Grafana board at `<url>` for request-path latency.
```

Legacy candidates (written before the `kind:` field existed) have no `- kind:` line and an early `- target:` line — treat those as `kind: agents-md`.

## Process

1. **Locate both queues.** Resolve project name from git toplevel (or cwd basename). Read `~/ai/.agents-md-candidates.md` and `~/data/<project-name>/agents-md-candidates.md`. Note which exist; an empty or missing file means zero candidates for that scope.

2. **If both empty, stop and say so.** "No candidates pending — nothing to triage." Don't invent content.

3. **Show the triage summary once.** Count candidates per scope, mention kind mix (e.g. "4 project-scope: 3 agents-md, 1 memory"). Announce the walk-through order: project-scope first (more local, faster decisions), then user-scope. Within each scope, oldest-first by the timestamp in the H2 header.

4. **For each candidate, in order:**

   a. **Quote the candidate.** Show the H2 title, the kind, the target/destination, the scope, the evidence, and the proposed content verbatim. Include the queue file path and line number for the H2 header so the user can navigate.

   b. **Lead with a recommendation.** One of:
      - **Apply as-is** — the content is clean, sits cleanly at the destination, and doesn't duplicate existing content. This is the default when nothing looks off.
      - **Apply with edit** — the substance is right but the wording needs a tweak. State the specific change and why.
      - **Reject** — already covered (cite the line), or proposal is too situational to be durable. State which.
      - **Defer** — useful signal but the wording isn't settled or the user might want to phrase it themselves. Say what would change your mind.
      - **Reclassify** — kind looks wrong (e.g. a memory candidate that's really a rule, or vice versa). Say which kind it should be and why, then apply at the corrected destination on approval.

      Confident phrasing, one verdict, one-line why.

   c. **Verify the destination exists.** Before recommending "apply":
      - **`kind: agents-md`** — check the target `AGENTS.md` exists. If not (project has no `AGENTS.md` yet), flag and ask whether to create it. On approval, create with a minimal skeleton (top-level `# AGENTS.md` + the new section), then run `~/ai/bin/ensure-claude-symlink.sh <dir>` to put the sibling `CLAUDE.md` symlink in place (see "Claude Code symlink" below).
      - **`kind: memory`** — check the destination memory dir exists. For user-scope: `~/.claude/projects/-Users-steveu-ai/memory/`. For project-scope: `~/.claude/projects/<encoded-cwd>/memory/` (sibling of the project's transcript dir). These dirs are created by `link-memory.sh` at session start, so the dir should already exist — if it doesn't, flag it.

   d. **Wait for the user's verdict.** Accept:
      - `apply` / `yes` / `go` → apply per "Applying" below; remove the H2 from the queue. Confirm in one line.
      - `apply with edit: <text>` (or a free-text rewrite) → apply the edited version, remove from queue, confirm.
      - `reject` / `no` / `skip` → remove from queue without applying.
      - `defer` / `come back later` → leave in queue.
      - `reclassify as <kind>` → flip the candidate's kind and re-recommend; user re-verdicts.

   e. **Apply immediately.** Write to the destination *before* moving to the next candidate. If the user stops the walk-through, nothing is left half-done.

5. **At the end of the walk-through**, print a short summary: applied N (of which K memory, A agents-md), rejected M, deferred D. Don't keep proposing.

## Applying an AGENTS.md candidate

- **Target section exists** — append the block-quoted line(s) to the end of that section, preserving the section's bullet style and tone. Strip the leading `> ` before pasting.
- **Target section is "new"** — append a new section to the end of the file (or to a position the user specifies). Confirm placement before writing.
- **Multiple candidates target the same section in one walk-through** — apply each as it's approved. Don't merge.
- **After writing**, run `~/ai/bin/ensure-claude-symlink.sh <dir>` to keep the sibling `CLAUDE.md` symlink in place (idempotent — safe on every apply).

Confirmation line: `Applied to <target> (+N lines); ensured CLAUDE.md symlink; removed from <queue>.`

## Applying a memory candidate

The memory file format mirrors the auto-memory schema documented in `~/ai/AGENTS.md`:

```markdown
---
name: <slug-from-candidate>
description: <description-from-candidate>
metadata:
  type: <type-from-candidate>
---

<body — block-quoted text from candidate, with the leading `> ` stripped>
```

For `feedback` / `project` types, the body should already have the `**Why:**` / `**How to apply:**` structure baked in by the classifier — preserve it verbatim. If it's missing, that's an "apply with edit" moment.

Steps:

1. Resolve the destination dir:
   - `scope: user` → `~/.claude/projects/-Users-steveu-ai/memory/`
   - `scope: project` → `~/.claude/projects/<encoded-current-cwd>/memory/` (sibling of the running transcript). On macOS, this resolves through a symlink to `~/ai/memory/personal/<project>/`; on Windows, `~/ai/memory/work/<project>/`. Write through the `~/.claude/projects/...` path either way — the symlink takes you to the right place.
2. Filename: `<name>.md` where `<name>` is the kebab slug from the candidate. If a file with that name already exists, **stop and ask** — same name with different content is almost always a sign the classifier missed dedup; the user decides whether to merge, rename, or reject.
3. Write the full file (frontmatter + body) with `Write`.
4. Add an index entry to `MEMORY.md` in the same dir:
   - Format: `- [<H2 title from candidate>](<name>.md) — <description-from-candidate>`
   - Append to the end. If `MEMORY.md` doesn't exist, create it with a one-line header (`# MEMORY.md`) and the entry. Keep total file length under 200 lines (the auto-memory loader truncates beyond that) — if appending would push it over, surface and ask before adding.

Confirmation line: `Wrote memory <name>.md to <dir>; indexed in MEMORY.md; removed from <queue>.`

## Claude Code symlink (AGENTS.md only)

Claude Code reads `CLAUDE.md`, not `AGENTS.md`. Any project where you've written an `AGENTS.md` needs a sibling `CLAUDE.md` symlink pointing at it, or Claude Code won't pick the file up at session start. The pattern mirrors user-scope (`~/ai/CLAUDE.md → AGENTS.md`): same-directory **relative** symlink.

The mechanics live in `~/ai/bin/ensure-claude-symlink.sh` — call it after every write to a project-scope `AGENTS.md`. It's idempotent (no-op if the symlink is already correct), handles Windows symlink mode, and exits with a verdict so you don't need to re-check the filesystem.

```
~/ai/bin/ensure-claude-symlink.sh <dir-containing-agents-md>
```

Interpret the exit code:

- **0** — symlink in place. The stdout line says whether it was newly created or already correct. Pass it through to the user as a one-line confirmation.
- **2** — `CLAUDE.md` exists as a real file. The script refused to clobber it. Stop, surface what's there, ask the user how to resolve: merge content into AGENTS.md and re-run; delete the real CLAUDE.md and re-run; or leave both un-linked (Claude Code keeps reading the hand-written CLAUDE.md, the new AGENTS.md additions are invisible until resolved).
- **3** — `CLAUDE.md` is a symlink to something other than `AGENTS.md`. Stop and ask. Same shape of decision.
- **1** — unexpected error (missing AGENTS.md, `ln` failed, bad arg). stderr explains; surface it.

User-scope writes (to `~/ai/AGENTS.md`) don't need this — the symlinks are already in place (`~/ai/CLAUDE.md → AGENTS.md`, `~/.claude/CLAUDE.md → ~/ai/AGENTS.md`). Memory writes don't need this either — memory files are loaded via the `<encoded-project>/memory/` path directly.

## Removing from the queue

Remove the entire H2 section, including the H2 header line itself and all body content up to (but not including) the next `## ` header or end-of-file. Preserve any non-candidate prose elsewhere in the queue file (e.g. a top-of-file header explaining what the file is). If the queue file becomes empty (no remaining H2 sections), leave the file in place but empty rather than deleting it — keeps the path stable for the SessionStart nudge.

## When to stop and ask

- Two candidates propose contradictory or duplicative content — surface and let the user pick.
- An AGENTS.md candidate's target section doesn't exist in the target file and the candidate says "section: X" rather than "new" — flag the mismatch.
- The proposed content would duplicate or substantially overlap with existing AGENTS.md / MEMORY.md content the candidate didn't catch — surface the overlap, recommend reject.
- A memory candidate's `name:` collides with an existing file in the destination dir.
- The target file doesn't exist (AGENTS.md) and the user hasn't decided whether to create it.

## Anti-patterns

- Charging through candidates without per-candidate verdicts. The walk-through is the skill's primary value.
- Apologising for "reject" or "defer" recommendations. They're first-class.
- Batching applies — writing N approved candidates in one go at the end. Each lands as approved.
- Rewriting the proposed content silently — if you'd phrase it differently, recommend "apply with edit".
- Deleting the queue file outright. Leave it in place if empty.
- Restructuring AGENTS.md sections or memory files, renaming headings, or "cleaning up" beyond the proposed addition. Out of scope.
- Auto-creating a missing target AGENTS.md without asking — file creation is a meaningful decision.
- Writing to a project-scope AGENTS.md and skipping the `ensure-claude-symlink.sh` call. Without the symlink, Claude Code won't pick the file up — the whole loop is silently useless.
- Hand-rolling the symlink with raw `ln -s` from inside the skill. Use the script — it handles idempotency, the Windows symlink-mode export, and conflict detection in one place.
- Writing a memory file without adding the `MEMORY.md` index entry. The index is what gets loaded into context at session start; without it, the memory file is invisible.
- Generating memory frontmatter inconsistent with the candidate's metadata. The candidate is the source of truth for `name`, `description`, `type` — don't paraphrase or substitute.
