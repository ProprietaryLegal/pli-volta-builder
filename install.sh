#!/bin/bash
# install.sh [--claude] [--codex] [--both] [--force] [--dry-run] [--test]
#
# Installs the skill folder skills/pli-volta-builder as a personal skill:
#   Claude Code  ${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/pli-volta-builder/
#   Codex CLI    ${CODEX_HOME:-$HOME/.codex}/skills/pli-volta-builder/
# Both agents read the same layout: a folder named after the skill holding SKILL.md (YAML frontmatter `name` and
# `description`) and the files it loads on demand. Codex also reads agents/openai.yaml (its UI name and short
# description); Claude Code ignores that folder. So one source serves both, copied as is.
#
# Idempotent: an identical installed copy is left alone; an older copy of THIS skill (it carries the marker file
# .pli-volta-builder-install written by this script) is replaced; anything else at the destination (another skill of
# the same name, a symlink, a folder without the marker) is refused unless --force is given.
# --dry-run prints what it would do and writes nothing. --test runs the skill's CPU self-tests from the installed copy.
set -euo pipefail

NAME=pli-volta-builder
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SRC="$HERE/skills/$NAME"
[ -f "$SRC/SKILL.md" ] || { echo "REFUSED: $SRC/SKILL.md not found (run this from a clone of the repository)"; exit 9; }

want_claude=0; want_codex=0; force=0; dry=0; test=0
[ $# -gt 0 ] || { sed -n '2,15p' "$0"; exit 2; }
for a in "$@"; do
  case "$a" in
    --claude) want_claude=1 ;;
    --codex) want_codex=1 ;;
    --both) want_claude=1; want_codex=1 ;;
    --force) force=1 ;;
    --dry-run) dry=1 ;;
    --test) test=1 ;;
    *) echo "unknown option $a"; sed -n '2,15p' "$0"; exit 2 ;;
  esac
done
[ $((want_claude + want_codex)) -gt 0 ] || { echo "say --claude, --codex or --both"; exit 2; }

VERSION=$(git -C "$HERE" rev-parse --short HEAD 2>/dev/null || echo "no-git")
MARK=.pli-volta-builder-install

same_tree() {  # same_tree A B: equal files, ignoring the marker and Python caches
  diff -rq -x "$MARK" -x __pycache__ -x '*.pyc' "$1" "$2" >/dev/null 2>&1
}

install_to() {  # install_to AGENT DEST
  local agent=$1 dest=$2 parent
  parent=$(dirname "$dest")
  if [ -L "$dest" ]; then
    [ $force = 1 ] || { echo "REFUSED ($agent): $dest is a symlink to $(readlink "$dest"); use --force to replace it"; return 1; }
  elif [ -d "$dest" ]; then
    if same_tree "$SRC" "$dest"; then
      echo "UNCHANGED ($agent): $dest already holds this version"
      return 0
    fi
    if [ ! -f "$dest/$MARK" ] && [ $force = 0 ]; then
      echo "REFUSED ($agent): $dest exists and was not installed by this script (another skill of the same name?); use --force to replace it"
      return 1
    fi
  elif [ -e "$dest" ]; then
    [ $force = 1 ] || { echo "REFUSED ($agent): $dest exists and is not a folder; use --force"; return 1; }
  fi
  if [ $dry = 1 ]; then
    echo "WOULD WRITE ($agent): $dest ($(find "$SRC" -type f -not -path '*/__pycache__/*' | wc -l) files, version $VERSION)"
    return 0
  fi
  mkdir -p "$parent"
  local tmp="$parent/.$NAME.new.$$"
  rm -rf "$tmp"
  cp -R "$SRC" "$tmp"
  find "$tmp" -name __pycache__ -type d -prune -exec rm -rf {} +
  printf 'installed %s from %s version %s by install.sh\n' "$(date -u +%FT%TZ)" "$HERE" "$VERSION" >"$tmp/$MARK"
  rm -rf "$dest"
  mv "$tmp" "$dest"
  echo "WROTE ($agent): $dest"
  (cd "$dest" && find . -type f | sort | sed 's|^\./|    |')
  if [ $test = 1 ]; then
    bash "$dest/tests/run_all.sh" | tail -1
  fi
}

rc=0
if [ $want_claude = 1 ]; then
  install_to "Claude Code" "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/$NAME" || rc=1
fi
if [ $want_codex = 1 ]; then
  install_to "Codex" "${CODEX_HOME:-$HOME/.codex}/skills/$NAME" || rc=1
fi
[ $rc = 0 ] && [ $dry = 0 ] && echo "Done. Start a new Claude Code or Codex session to load the skill (Codex: invoke it as \$$NAME or let it trigger)."
exit $rc
