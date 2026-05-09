#!/usr/bin/env zsh
# Build dist/<skill>.zip for each skill directory, with `${VAR}` placeholders
# in SKILL.md substituted from the values in `.env` at the repo root.
#
# `.env` and `dist/` are both gitignored — secrets stay local while the
# committed SKILL.md keeps placeholders. Generated zips are intended for
# manual upload to claude.ai.
set -euo pipefail

repo_root="${0:A:h:h}"
cd "$repo_root"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

mkdir -p dist
tmp_root="$(mktemp -d)"
trap 'rm -rf "$tmp_root"' EXIT

# Substitute ${NAME} occurrences using current environment.
# Unknown vars are left untouched (visible in the resulting zip — easy to spot).
substitute() {
  perl -pe 's/\$\{(\w+)\}/exists $ENV{$1} ? $ENV{$1} : $&/eg'
}

built=0
for dir in */; do
  name="${dir%/}"
  [[ "$name" == "dist" || "$name" == "bin" ]] && continue
  [[ -f "$name/SKILL.md" ]] || continue

  staging="$tmp_root/$name"
  mkdir -p "$staging"
  # Copy contents of the skill dir into the staging dir, preserving structure.
  (cd "$name" && tar -cf - .) | (cd "$staging" && tar -xf -)
  substitute < "$name/SKILL.md" > "$staging/SKILL.md"

  rm -f "dist/$name.zip"
  (cd "$tmp_root" && zip -rq "$repo_root/dist/$name.zip" "$name" \
    -x "*.DS_Store" "*/__MACOSX/*")

  # Also mirror the substituted staging tree into dist/<name>/ so a symlink
  # at ~/.claude/skills/<name> -> dist/<name>/ picks up the built copy in
  # local Claude Code (placeholders resolved). dist/ is gitignored.
  rm -rf "dist/$name"
  mkdir -p "dist/$name"
  (cd "$staging" && tar -cf - --exclude=.DS_Store .) | (cd "dist/$name" && tar -xf -)

  echo "dist/$name.zip"
  built=$((built + 1))
done

echo "built $built skill zip(s)"
