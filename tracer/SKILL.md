---
name: tracer
description: Turn a feature or refactor idea into a tracked GitHub issue tree — a value-first parent issue plus AFK-grabbable vertical-slice sub-issues, linked via native GitHub sub-issues. Use when the user wants to decompose a plan, idea, or feature into actionable issues. Not for atomic bug reports.
---

# Tracer

Convert a feature or refactor idea into a tracked work tree on GitHub: one parent issue (value-first, human-readable) and a set of vertical-slice sub-issues (technical, AFK-grabbable), linked via native sub-issues.

## Scope

Tracer creates trees for **features** and **refactors** only. Bugs are usually atomic — for those, use the bug template directly. If a bug genuinely warrants decomposition, run a separate decomposition flow against the existing bug.

## Process

### 1. Synthesise the idea

Work from what's already in the conversation context. Do **not** interview the user — that's `/grill-me`'s job. If context is thin, ask the user for more or suggest `/grill-me` first.

### 2. Is this actually a tree?

Before sketching architecture, sanity-check that decomposition is warranted. If the work is one cohesive end-to-end change that fits in a single PR, **stop**. Don't use tracer — surface this to the user and recommend creating a single `feature.md` or `refactor.md` issue directly via `gh issue create`.

Tracer is for work that genuinely benefits from being split into independently-grabbable, dependency-ordered slices. Single-PR work doesn't.

**Heuristics for "actually a tree":**
- Touches 3+ modules with non-trivial work in each
- Has natural sequencing (slice B can't start until slice A merges)
- Some slices can run in parallel by different agents
- The full thing is too big to review in one PR

**Heuristics for "actually one issue":**
- Single module, single PR
- No internal sequencing — it all lands together or not at all
- A reviewer would read it in one sitting

When in doubt, lean toward one issue. Over-decomposition creates ceremony; under-decomposition creates work the user can always split later if needed.

### 3. Sketch the architecture

Before drafting tickets, sketch the major modules involved:

- Which modules need to be built or modified?
- Are there opportunities to extract **deep modules** — a lot of functionality behind a thin, stable interface, testable in isolation?
- What are the module boundaries and contracts?

Surface tradeoffs that affect decomposition. Sketch, not spec — keep it short.

### 4. HITL: confirm module shape

Present the architecture sketch and ask:

- Does this module breakdown match expectations?
- Are the deep-module candidates the right ones?
- Which modules need tests, and what's the prior art (similar tests in the codebase to mimic)?

Iterate until the user approves. **Don't draft tickets until the architecture lands** — wrong-shape tickets waste both your time and theirs.

### 5. Draft the parent issue

If `.github/ISSUE_TEMPLATE/feature.md` or `refactor.md` exists in the current repo, follow its style. Otherwise, default to:

- **Title:** value-first, no prefix. The capability gained or pain relieved — not the mechanism.
  - ❌ "Add ranker module"
  - ✅ "Surface kid-relevant videos first on home screen"
- **Body:** one or two sentences of summary, then the type's required section (Acceptance for feature; Pain today / After for refactor).
- **Out of scope:** explicit list at the bottom — bounds the tree, prevents agent over-reach in children.

Don't bury the architecture sketch in the parent. It belongs in the children's "where to look" pointers, or as a comment on the parent if it's substantial.

### 6. Draft the vertical-slice children

Break the work into **tracer-bullet** sub-issues. Each is a thin vertical slice cutting through ALL integration layers end-to-end (schema → API → UI → tests).

<vertical-slice-rules>
- Each slice delivers a narrow but COMPLETE path through every layer
- A completed slice is demoable or verifiable on its own
- Prefer many thin slices over few thick ones
- Slices are **AFK** (implementable and mergeable without human interaction) or **HITL** (requires architectural decision, design review, or judgment). Prefer AFK.
</vertical-slice-rules>

For each child:

- **Title:** descriptive and technical — these are work units, not human-scannable summaries
- **What to build:** end-to-end behaviour, not layer-by-layer implementation
- **Acceptance criteria:** behavioural checkbox list. Specific enough that an agent (or future-you) can verify completion without re-asking.
- **Where to look:** `file_path:line` references for entry points and patterns to mimic. Stale-but-pointing-near-the-right-place beats no pointer.
- **Tests:** which prior art to follow (e.g., "follow the pattern in `src/modules/foo/foo.test.ts`")
- **Blocked by:** which siblings must complete first
- **AFK / HITL:** tag, with one-line reason if HITL

### 7. HITL: confirm the tickets

Present the breakdown as a numbered list. For each child show: title, AFK/HITL, blocked-by, one-line summary.

Ask:

- Is the granularity right (too coarse / too fine)?
- Are the dependencies correct?
- Should any slices be merged or split?
- Are AFK / HITL tags right?

Iterate until approved.

### 8. Create the issues and link them

Create in dependency order: parent first, then children topologically so blocker references resolve to real numbers.

```bash
gh issue create --title "..." --body "..." --label feature
```

Apply the appropriate label: `feature` or `refactor` for the parent. Children inherit the parent's type label unless instructed otherwise.

After each child is created, **attach it to the parent as a native sub-issue**:

```bash
gh api -X POST repos/{owner}/{repo}/issues/{parent_number}/sub_issues \
  -f sub_issue_id={child_internal_id}
```

**Important:** `sub_issue_id` is the issue's internal `id` (from the API response), **not** the issue number. Get it from the `id` field of the create response, or via `gh api repos/{owner}/{repo}/issues/{number}` if needed.

Keep `## Parent #N` and `## Blocked by #N` text references in the body as redundant human cues — the native link is structural, the text is for readers.

## Sub-issue body template

<issue-template>
## Parent

#<parent-issue-number>

## What to build

A concise description of this vertical slice. End-to-end behaviour, not layer-by-layer implementation.

## Acceptance

- [ ] Criterion 1 (behavioural, verifiable)
- [ ] Criterion 2
- [ ] Criterion 3

## Where to look

- `path/to/module/index.ts:42` — entry point
- `path/to/related.ts` — pattern to mimic

## Tests

Follow the pattern in `path/to/similar.test.ts`. Test external behaviour, not implementation details.

## Blocked by

- #<issue-number>

(Or "None — can start immediately.")

## AFK / HITL

AFK | HITL — one-line reason if HITL.
</issue-template>

## Notes

- Don't close or modify the parent once children are attached.
- If the user invokes tracer with an existing parent issue (number or URL), skip Step 5 — use that issue as the parent and proceed from Step 6.
- If sub-issues API returns an error, fall back to text-only `## Parent #N` references and surface the failure to the user.
