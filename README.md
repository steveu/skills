# skills

Personal Claude Code and Codex skills, shared across machines.

## Install

Each top-level directory is a skill (containing a `SKILL.md` and any
supporting files). Claude Code loads skills from `~/.claude/skills/`.

Clone the whole set:

```sh
git clone https://github.com/steveu/skills.git ~/.claude/skills
```

Or, if `~/.claude/skills` already exists, symlink individual skills:

```sh
git clone https://github.com/steveu/skills.git ~/src/skills
ln -s ~/src/skills/tracer ~/.claude/skills/tracer
```

Restart Claude Code (or start a new session) to pick up new skills.

Codex loads skills from `~/.codex/skills/`. Symlink the same source
directories there, excluding `dist/`:

```sh
for d in ~/skills/*(/); do
  name=${d:t}
  [[ $name == dist || $name == bin ]] && continue
  [[ -f "$d/SKILL.md" ]] || continue
  ln -sfn "$d" "$HOME/.codex/skills/$name"
done
```

Restart Codex to pick up new or changed skills.

## Skills

- **tracer** — Decompose a feature or refactor idea into a tracked GitHub
  issue tree: a value-first parent issue plus AFK-grabbable vertical-slice
  sub-issues, linked via native GitHub sub-issues.
- **grill-me** — Interview relentlessly about a plan or design until every
  branch of the decision tree is resolved or explicitly deferred. Each
  question arrives with a recommended answer and tradeoff.
- **tdd** — Test-driven development with a red-green-refactor loop, vertical
  slices, behaviour-not-implementation testing.
- **improve-codebase-architecture** — Surface deepening opportunities and
  architectural friction; consolidate shallow modules into deep ones.
- **capture** — Append a thought to the personal Obsidian vault at
  `~/brain/vault/`. Defaults to today's daily note; matches existing
  vault conventions rather than imposing Zettelkasten structure.
- **capture-cloud** — Same shape as `capture`, but calls the brain-mcp
  `capture` tool for use in Claude.ai (web/mobile) where there is no
  local filesystem. Upload as a skill in Claude.ai settings.
- **add-recipe** — Save a fully-developed recipe from the current
  conversation to `~/brain/vault/Recipes/<title>.md` via the brain-mcp
  `add_recipe` tool. Closed-set frontmatter (`type`, `source`, `health`),
  metric units only, body matches the existing recipe convention.
- **codex-review** — Run one round of `codex review` against an existing
  GitHub PR via `~/ai/bin/codex-pr-review.sh`. Detects the obvious PR from
  conversation context (or accepts an explicit PR ref), offers to check out
  the PR's branch if you're elsewhere, posts the review to the PR, and
  reports verdict + finding count + URL back in chat.
- **footy** — Create a match note for the user's son's football teams
  (Fulford FC, Fulford School) by calling the brain-mcp `create_match`
  tool. Asks for opposition / date / team with sensible defaults; the
  tool reads `vault/Templates/Match.md` and writes to
  `vault/Matches/`. Body is left blank for post-match fill-in.
- **video-note** — Turn a YouTube URL into a durable, linked note in the
  brain vault. A bundled `fetch-transcript.mjs` helper shells `yt-dlp`
  (json3 captions, timestamps preserved) on the M4; the skill synthesises
  a gist + timestamped key points, greps the vault for related notes and
  proposes forward-only `[[wikilinks]]`, then writes one re-mineable note
  to the private `Sources/` staging tier — gating title, worth-a-note call,
  and links first. Curation-first: thin videos get downgraded or skipped.
- **trails** — Turn a public walk guide (or a list of landmarks) into a
  clean, followable GPX on real OSM paths. A bundled stdlib `route.py` geocodes
  named waypoints (Nominatim), routes them with BRouter, and reports
  distance/ascent/retrace plus how much of the line is on roads-with-cars vs
  paths. Emits named `<wpt>` pins (start, destination, landmarks) that map apps
  render as labelled markers, with off-route landmarks marked but not routed
  through. Renders an HTML preview (OS Outdoor if `OS_API_KEY` is set, else
  OpenTopoMap) with a route on/off toggle. Signal-vs-renderer discipline: keep
  the guide's deliberate roads, don't let routing optimise them away. Writes the
  GPX to `~/brain/vault/Travel/` (Claude Code) or returns it as a download
  (claude.ai) for offline use in OsmAnd.

`tdd` and `improve-codebase-architecture` are adapted from
[Matt Pocock's skills](https://github.com/mattpocock/skills) (MIT, see
`LICENSE-pocock`).

## Uploading to Claude.ai

Claude.ai has no API for skill management — zip the skill folder and upload
via the web UI. `dist/` is gitignored; rebuild locally before each upload:

```sh
./bin/build.sh
```

To refresh changed skill zips automatically on every commit (so `dist/` is
never stale), opt into the repo's git hooks once per clone:

```sh
git config core.hooksPath .githooks
```

## Local config (`.env`)

This repo is public, so any private values referenced by a `SKILL.md` (e.g.
a Tailscale hostname) live in a gitignored `.env` at the repo root and are
substituted into a fresh copy of `SKILL.md` at zip-build time. The committed
SKILL.md keeps `${VAR}` placeholders; the `dist/<skill>.zip` you upload to
claude.ai contains the substituted values.

Setup:

```sh
cp .env.example .env
# then edit .env to fill in real values
./bin/build.sh
```

`bin/build.sh` sources `.env`, skips skills whose existing `dist/<skill>.zip`
and `dist/<skill>/` mirror are newer than their source files, then copies each
changed skill directory to a temp staging area, runs `${NAME}` substitution
over `SKILL.md` using current env, and zips the staging copy. Unknown variables
are left as-is (visible in the resulting zip — easy to spot if you forgot to
populate `.env`).

When adding a new skill that needs a private value, keep `${YOUR_VAR}` in
the committed `SKILL.md` and add `YOUR_VAR=...` to `.env` (and document it
in `.env.example` with a placeholder).
