---
name: add-recipe
description: Save a fully-developed recipe from the current conversation to the personal Obsidian vault by calling the brain-mcp `add_recipe` tool, which writes to `vault/Recipes/<title>.md`. Use when the user says "save this recipe", "save this recipe to brain", "add this recipe to brain", "save recipe to brain", or similar. Only fires when there is a clear, complete recipe in the conversation — refuses partial drafts and asks for the missing pieces.
---

# Add recipe

Save a complete recipe to the personal Obsidian vault by calling the **brain-mcp `add_recipe` tool**. The tool takes `title: string` and `body: string`, writes verbatim to `vault/Recipes/<title>.md`, and refuses to overwrite an existing recipe with the same title.

The tool only writes the file. **The skill is responsible for composing a body that already matches the shape below** — frontmatter, sections, units, voice. There is no second pass.

## Scope

Use this skill only when:

- A complete recipe has been developed in the current conversation (ingredients with quantities, method, serves, time).
- The user explicitly asks to save it: `"save this recipe"`, `"save this recipe to brain"`, `"add this recipe to brain"`, `"save recipe to brain"`, or close variants.

Do NOT use this skill for:

- Partial drafts where ingredients, method, serves, or time are missing — stop and ask for the missing pieces before saving.
- Saving a link to an external recipe — the vault wants the full text, not a pointer.
- Anything that isn't recipe-shaped — redirect to `capture` if it's a thought about food rather than a recipe.

## Recipe shape

The vault's recipe convention is anchored on `Recipes/Lemon, Greens & Sausage Pasta.md`. New recipes match this shape exactly.

### Frontmatter

Closed sets — if a recipe doesn't fit, stop and ask the user rather than inventing a value.

```yaml
---
type: batch-lunch | family-meal
source: <Claude conversation | URL | person | cookbook>
health: light | balanced | indulgent
---
```

- **`type`** — closed set, exactly two values. If the recipe is plainly neither (a snack, a drink, a dessert that fits neither category), stop and ask the user. Adding a third value is a deliberate edit to this skill, not an on-the-fly choice.
- **`source`** — fill in when obvious. The conversation usually makes this clear: `Claude conversation` if the recipe was developed in chat, a URL if cited, a person's name if attributed (`from Cheryl`), a cookbook name if quoted. Prompt the user when ambiguous.
- **`health`** — closed set, three values. `light` = vegetable-led, lean protein, minimal added fat or sugar. `balanced` = standard cooked meal, nothing extreme. `indulgent` = butter, cream, frying, sugar, or refined carbs as a primary feature. Stop and ask if you can't confidently pick.

### Body

Mirror the existing recipe layout precisely:

```markdown
**Serves:** 4  
**Time:** ~25 minutes  

---

## Ingredients

- 300g pasta
- 6 sausages
- ...

---

## Method

### 1. Cook the pasta
- Bring a large pan of salted water to the boil
- ...

---

### 2. Cook the sausage
- ...

---

## Reheating

- Microwave from chilled: 2–3 minutes, stir halfway
- ...
```

- **Inline header**: `**Serves:** N  ` and `**Time:** ~X  ` (two-space hard breaks at end of line), followed by a `---` divider before `## Ingredients`.
- **`## Ingredients`** — flat bullet list. Sub-group with `### Component` headings only if the recipe genuinely has distinct components (e.g. sauce + base + topping).
- **`## Method`** — numbered `### N. Step name` subsections, each a short bullet list. `---` divider between steps.
- **`## Reheating`** — included only when `type: batch-lunch`. Omitted entirely for `family-meal`.
- **Trailing sections** (`## Tips`, `## Notes on …`) — include only when there is genuine content. Don't pad.

### Content rules

These are non-negotiable:

- **Metric only** — grams, ml, °C. No ounces, no Fahrenheit.
- **No cups** — convert to grams (dry) or ml (liquid).
- **No decimals from conversion** — round to whole numbers. `1 cup flour` → `125g`, not `124.5g`. `1 tsp` and `1 tbsp` are fine; they're already metric-friendly.
- **British English** — courgette (not zucchini), coriander (not cilantro), aubergine (not eggplant), prawns (not shrimp), rocket (not arugula).
- **Light imperative cookbook voice** — `"Bring a large pan of salted water to the boil"`, not `"You'll want to start by bringing a pan of water…"`. Don't mimic the user's conversational phrasing.
- **Two-space hard breaks** at end-of-line within bullet lists — match the existing recipe's spacing.

### Title

- **Title Case With Spaces**, punctuation fine. `Lemon, Greens & Sausage Pasta` is the anchor.
- Used verbatim as the filename — the tool preserves case, spaces, and punctuation (it strips only `\`, `/`, and null bytes).
- Derive a concise title that names the dish. Avoid generic prefixes (`Quick & Easy …`, `The Best …`).

## Process

1. **Check completeness.** Confirm the conversation contains: ingredients with quantities, method, serves, time. If anything is missing, stop and ask.
2. **Pick the type.** `batch-lunch` or `family-meal`. If neither fits, stop and ask.
3. **Pick the health grade.** `light` / `balanced` / `indulgent`. If unsure, stop and ask.
4. **Resolve the source.** If obvious from the conversation, fill it in. If not, ask in one line: "Source for this recipe?"
5. **Compose the body.** Frontmatter, header, `## Ingredients`, `## Method`, `## Reheating` (batch-lunch only), optional trailing sections. Apply the content rules — metric, no cups, whole numbers, British English, cookbook voice.
6. **Derive the title.** Title Case, names the dish.
7. **Call `add_recipe(title, body)`.**
8. **Confirm to the user in one line**, echoing the tool's reply (e.g. `Saved — Recipes/Lemon, Greens & Sausage Pasta.md`).

## When to stop and ask

- The recipe is incomplete (missing ingredients, method, serves, or time).
- The recipe is plainly neither `batch-lunch` nor `family-meal`.
- You can't confidently pick a `health` grade.
- The `source` is ambiguous and not derivable from the conversation.
- The tool returns an overwrite error — surface it; do not invent a new title to dodge the conflict, ask the user how they want to proceed.
- The brain-mcp tool is unavailable or returns an error — surface plainly; do not fall back to writing the file via another mechanism.

## Anti-patterns

- Inventing frontmatter fields the shape doesn't define (tags, dietary flags, date added, prep/cook split, cuisine, calories).
- Adding a new `type` or `health` value because the recipe "doesn't quite fit".
- Mimicking the user's personal phrasing — voice is light cookbook imperative, regardless of how the conversation read.
- Including imperial units alongside metric "for convenience".
- Quoting decimal conversions (`124.5g`) — round.
- Including a `## Reheating` section for a `family-meal`, or omitting it for a `batch-lunch`.
- Padding with empty `## Tips` / `## Notes` sections — omit when there's nothing to say.
- Trying a different title to bypass an overwrite error — surface and ask.
- Using the GitHub connector or any file tool other than `add_recipe`.
