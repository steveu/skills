---
name: grill-me
description: Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Sharpens domain language inline and captures durable decisions as ADRs / CONTEXT.md entries when warranted. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me".
---

Interview the user relentlessly about every aspect of this plan until shared understanding lands. Walk down each branch of the decision tree, resolving dependencies between decisions one at a time.

## Rules

- Ask one question at a time.
- If a question can be answered by exploring the codebase or reading existing docs, explore instead of asking.
- For each question, lead with a recommended answer — don't just pose the question. Format: **answer + one-line why + the main tradeoff**. Be confident: "I'd do X because Y; the cost is Z" beats "you might want to consider X".
- Skip questions that aren't load-bearing. If a decision doesn't change behaviour, scope, or what gets built, don't ask it.

## Sharpen language as you go

- **Challenge fuzzy or overloaded terms.** When the user says "account", "user", "request", etc., propose a precise canonical name. "You're saying 'account' — do you mean the Customer or the User? Those are different things."
- **Stress-test with concrete scenarios.** When relationships between concepts are being discussed, invent edge cases that force the user to be precise about boundaries.
- **Cross-reference with code.** When the user states how something works, check whether the code agrees. Surface contradictions: "Your code cancels entire Orders, but you just said partial cancellation is possible — which is right?"

## Capture durable decisions

At the start of grilling, look for existing documentation:

- `CONTEXT.md` at repo root → single-context repo with a glossary
- `CONTEXT-MAP.md` at repo root → multiple bounded contexts; the map points to where each `CONTEXT.md` lives
- `docs/adr/` (root or per-context) → existing decision records, sequentially numbered

If none of these exist, that's fine — create them lazily, only when there's something worth writing.

### CONTEXT.md (glossary) — update inline

When a term gets resolved during grilling, update `CONTEXT.md` immediately. Don't batch. Format: [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).

- Only domain terms — not general programming concepts (timeouts, error types, utilities).
- If a user's term conflicts with the existing glossary, call it out: "Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"
- If multiple contexts exist, infer which one the topic belongs to. If unclear, ask.

### ADRs — offer sparingly

Only offer to create an ADR when **all three** are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If any is missing, skip it. Format and qualifying examples: [ADR-FORMAT.md](./ADR-FORMAT.md). Create `docs/adr/` lazily when the first ADR is needed.

## Stop when

- Every branch is either **resolved** (a call has been made) or **explicitly deferred** (the user has said "decide later" — record the deferral so it doesn't quietly drop).
- No new questions are surfacing from the answers given.

On stop, summarise as a short list: resolved calls, then deferrals, then any new ADRs / CONTEXT.md entries written during the session. Don't keep grilling once the tree is exhausted.
