#!/usr/bin/env zsh
set -euo pipefail

repo_root="${0:A:h:h}"
cd "$repo_root"
mkdir -p dist

built=0
for dir in */; do
  name="${dir%/}"
  [[ "$name" == "dist" || "$name" == "bin" ]] && continue
  [[ -f "$name/SKILL.md" ]] || continue
  rm -f "dist/$name.zip"
  zip -rq "dist/$name.zip" "$name" -x "*.DS_Store" "*/__MACOSX/*"
  echo "dist/$name.zip"
  built=$((built + 1))
done

echo "built $built skill zip(s)"
