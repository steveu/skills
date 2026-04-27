---
name: grill-me
description: Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me".
---

Interview the user relentlessly about every aspect of this plan until shared understanding lands. Walk down each branch of the decision tree, resolving dependencies between decisions one at a time.

## Rules

- Ask one question at a time.
- If a question can be answered by exploring the codebase or reading existing docs, explore instead of asking.
- For each question, lead with a recommended answer — don't just pose the question. Format: **answer + one-line why + the main tradeoff**. Be confident: "I'd do X because Y; the cost is Z" beats "you might want to consider X".
- Skip questions that aren't load-bearing. If a decision doesn't change behaviour, scope, or what gets built, don't ask it.

## Stop when

- Every branch is either **resolved** (a call has been made) or **explicitly deferred** (the user has said "decide later" — record the deferral so it doesn't quietly drop).
- No new questions are surfacing from the answers given.

On stop, summarise as a short list: resolved calls, then deferrals. Don't keep grilling once the tree is exhausted.
