---
name: repo-init
description: Apply a canonical issue-label set to a GitHub repo (six labels — bug, feature, refactor, chore, afk, hitl — with consistent colours and descriptions) and strip GitHub's OSS-community defaults. Use after creating a new repo, or to bring an existing repo's labels in line. Auto-detects the current repo, or accepts `owner/name` as an argument. Idempotent — safe to re-run.
---

# repo-init

Apply a canonical issue-label set to a GitHub repo. This file is the source of truth — edit it to evolve the scheme, then re-run on affected repos to bring them in line.

## Scope

- **Yes:** issue labels (create/update the six canonical ones, remove the seven OSS defaults).
- **No:** issue templates. Those flow automatically from the owner's `.github` repo and need no per-repo action.
- **No:** repo creation itself. Run `gh repo create` first.

## Usage

Inside a repo:

    /repo-init

Target auto-detected via `gh repo view`.

Targeting another repo:

    /repo-init owner/name

## Canonical labels

| Name       | Colour    | Description                                             |
| ---------- | --------- | ------------------------------------------------------- |
| `bug`      | `d73a4a`  | Something isn't working                                 |
| `feature`  | `a2eeef`  | A capability someone gains                              |
| `refactor` | `bfd4f2`  | Internal quality — same behaviour, better shape         |
| `chore`    | `ededed`  | Mechanical maintenance — deps, config, infra            |
| `afk`      | `0e8a16`  | Agent can ship this end-to-end without human input      |
| `hitl`     | `fbca04`  | Needs human judgement — architecture, design, or policy |

**Type vs workflow.** `bug` / `feature` / `refactor` / `chore` are mutually-exclusive types — one per issue. `afk` / `hitl` are orthogonal, tagging who can pick up the issue.

## OSS defaults to remove

GitHub ships every new repo with these. Mostly noise for small-team / agent-driven workflows:

- `documentation`
- `duplicate`
- `good first issue`
- `help wanted`
- `invalid`
- `question`
- `wontfix`

Removing a label strips it from any existing issues that have it. For a brand-new repo there won't be any.

## Process

1. **Resolve target.** If an argument was passed (`owner/name`), use it. Otherwise: `gh repo view --json nameWithOwner --jq .nameWithOwner` from the current directory.
2. **Apply canonical labels.** For each row in the table: `gh label create <name> -R <repo> --color <hex> --description "<desc>" --force`. The `--force` flag updates colour/description if the label already exists.
3. **Strip OSS defaults.** For each: `gh label delete <name> -R <repo> --yes`. Ignore not-found errors (label may already be absent).
4. **Sibling check.** Run `gh repo view <owner>/.github >/dev/null 2>&1` — if absent, flag once that the owner has no `.github` repo and issue templates won't auto-populate. Don't create it; that's a separate decision.
5. **Summary.** Print one line: target repo, count of labels set, count of labels removed.

## Reference implementation

```bash
TARGET="${1:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"
OWNER="${TARGET%%/*}"

CANONICAL=(
  "bug|d73a4a|Something isn't working"
  "feature|a2eeef|A capability someone gains"
  "refactor|bfd4f2|Internal quality — same behaviour, better shape"
  "chore|ededed|Mechanical maintenance — deps, config, infra"
  "afk|0e8a16|Agent can ship this end-to-end without human input"
  "hitl|fbca04|Needs human judgement — architecture, design, or policy"
)
DEFAULTS=(documentation duplicate "good first issue" "help wanted" invalid question wontfix)

set_count=0; rm_count=0
for line in "${CANONICAL[@]}"; do
  IFS='|' read -r name color desc <<< "$line"
  gh label create "$name" -R "$TARGET" --color "$color" --description "$desc" --force >/dev/null && ((set_count++))
done
for label in "${DEFAULTS[@]}"; do
  gh label delete "$label" -R "$TARGET" --yes >/dev/null 2>&1 && ((rm_count++))
done

gh repo view "$OWNER/.github" >/dev/null 2>&1 || \
  echo "Note: $OWNER has no .github repo — issue templates won't auto-populate."

echo "$TARGET: $set_count labels set, $rm_count removed."
```

## Notes

- Personal GitHub accounts have no org-level default-labels feature, so this skill is the only way to bootstrap them.
- Organisations *do* have native default labels (Settings → Repository defaults → Labels), but keeping the spec in this file avoids splitting it between an org-settings UI and a tracked file.
- The label scheme pairs with the AFK / HITL tag in `tracer`'s vertical-slice template — applying the label promotes that body-level judgement into a board-filterable signal.
