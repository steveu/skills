---
name: codex-review
description: Run one round of `codex review` against an existing GitHub PR by invoking `~/ai/bin/codex-pr-review.sh`. The review is posted to the PR as a `gh pr review` comment, and the skill reports verdict + finding count + URL back in chat. Use when the user wants a codex pass on a PR they (or another agent) already opened — not for full ship-feature loops, which iterate with auto-fix.
---

# codex-review

Runs one round of `codex review` against a GitHub PR via the shared script at `~/ai/bin/codex-pr-review.sh`, then reports the verdict in chat. The review body goes on the PR as the audit trail; chat gets a one-line summary.

## Scope

- **Single round.** No fix-and-iterate loop. After the review posts, the user (or the calling Claude) decides what to do with the findings.
- **Existing PRs only.** This skill does not create, branch, or push. If there is no PR yet, stop and tell the user.
- **The codex output belongs on the PR, not the terminal.** Don't paraphrase or dump the review body back into chat.

For the full build-and-iterate flow, use the `ship-feature` agent instead.

## Process

### 1. Resolve the PR

Two paths:

- **Explicit arg.** If the skill was invoked with a PR number (`42`) or URL (`https://github.com/owner/repo/pull/42`), use that. No confirmation needed — typing it is the confirmation.
- **Context scan.** Otherwise, look at recent conversation context for the most-obvious PR. Signals, in priority order:
  1. A PR URL mentioned in the last few turns (`https://github.com/.../pull/N`)
  2. An explicit `#N` reference where N is clearly a PR (e.g. just-opened PR, recent `gh pr view`/`gh pr create` output)
  3. The current branch's open PR — check with `gh pr view --json number,title,baseRefName,headRefName,url` (no PR-number arg uses the current branch)

  If one PR is clearly the obvious candidate, propose it with a single-question confirm: e.g. *"Run codex review on PR #42 — \"Add foo to bar\"?"* If nothing obvious surfaces, stop and ask the user for a PR number or URL.

Once resolved, capture:

```
PR_N=<number>
BASE=$(gh pr view "$PR_N" --json baseRefName -q .baseRefName)
PR_URL=$(gh pr view "$PR_N" --json url -q .url)
PR_HEAD=$(gh pr view "$PR_N" --json headRefName -q .headRefName)
```

### 2. Check branch state

Get the current branch:

```bash
CURRENT=$(git rev-parse --abbrev-ref HEAD)
```

If `CURRENT` != `PR_HEAD`, the codex prompt's tool-use ("you may use `git`, `rg`, file reads to inspect surrounding code") will read the wrong tree and may produce false positives where the PR introduces new symbols. Surface this and offer to switch:

> *"You're on `<CURRENT>` but the PR is on `<PR_HEAD>`. Codex's local file reads will see the wrong tree. Run `gh pr checkout <PR_N>` first?"*

- If the user agrees: `gh pr checkout "$PR_N"` and proceed.
- If the user declines: proceed and include a one-line warning in the chat report.

### 3. Run the review

```bash
VERDICT=$(~/ai/bin/codex-pr-review.sh "$PR_N" "$BASE" 1)
```

The script posts the review to the PR via `gh pr review` (falling back to `gh pr comment` on self-PRs) and writes the full review to `/tmp/codex-pr${PR_N}-r1.md`. Stdout is one of: `approved`, `changes-requested`, `missing`, `error`.

**Round header caveat.** The script labels the posted review "round 1/3" because it's shared with the `ship-feature` agent's bounded loop. For a standalone re-run on the same PR, that header is misleading but harmless — the review body is what matters, and the PR's review history shows the true sequence. Don't try to work around it from here.

### 4. Count findings

Parse the saved review file for findings count. Findings are bulleted items in the codex review body. A robust enough heuristic:

```bash
COUNT=$(grep -cE '^[-*] ' "/tmp/codex-pr${PR_N}-r1.md" || echo 0)
```

If the count looks wrong (e.g. the review is prose-only), fall back to reporting "findings posted on PR" without a number.

### 5. Report back

A single line in chat:

```
<verdict> — <COUNT> findings — <PR_URL>
```

Examples:

- `approved — 0 findings — https://github.com/owner/repo/pull/42`
- `changes-requested — 4 findings — https://github.com/owner/repo/pull/42`
- `missing — 2 findings — https://github.com/owner/repo/pull/42` (codex didn't emit a verdict tag; treat as changes-requested)
- `error — see PR for codex output — https://github.com/owner/repo/pull/42`

If the user declined to checkout the PR's branch in step 2, append a second line: *"(reviewed from `<CURRENT>` — codex's local reads may be off-tree)"*.

Do **not** dump the review body, finding bullets, or any prose from the review into chat. The user reads it on the PR.

## Rules

- **Never merge the PR.** This skill reviews; it doesn't merge. No `gh pr merge`, ever.
- **No destructive git.** No `git push --force`, `git reset --hard`, `git clean -f`, `git branch -D`, `git checkout --` / `git restore .`. The only git mutation this skill ever performs is the optional `gh pr checkout` in step 2, with explicit user confirmation.
- **No fix loop.** If the verdict is `changes-requested`, stop. The calling Claude or the user decides what to do next.
- **Don't paraphrase the review.** The PR has the audit trail; chat gets only the one-line summary.
- **British English** in any prose (commit messages, comments) — but this skill should rarely produce any prose other than the one-line report.
- **If `codex-pr-review.sh` is missing or non-executable**, stop and tell the user. Don't try to reconstruct the review flow inline.
