# skills

Personal Claude Code skills, shared across machines.

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

`tdd` and `improve-codebase-architecture` are adapted from
[Matt Pocock's skills](https://github.com/mattpocock/skills) (MIT, see
`LICENSE-pocock`).
