#!/usr/bin/env bash
# install.sh - install the job-agent kit for Claude Code (job-agent-kit).
# Idempotent: run it again at any time to update the skills, agents and scripts. It never
# overwrites profile.yaml, answers.yaml, the tracker, CLAUDE.md or settings.json in ~/job-search.
#
# Usage:  bash kit/install.sh [--skip-venv] [--help]
#         PYTHON=/path/to/python3.12 bash kit/install.sh    (choose the Python for the venv)
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_HOME="${HOME}/.claude"
WS="${HOME}/job-search"
MARKER="job-agent-kit"
BACKUP_DIR="${CLAUDE_HOME}/job-agent-kit-backups/$(date +%Y%m%d-%H%M%S)"
SKIP_VENV=0

usage() { sed -n '2,7p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

for arg in "$@"; do
  case "$arg" in
    --skip-venv) SKIP_VENV=1 ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown option: %s\n' "$arg" >&2; usage >&2; exit 2 ;;
  esac
done

say()    { printf '%s\n' "$*"; }
warn()   { printf 'WARNING: %s\n' "$*" >&2; }
die()    { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
pretty() { case "$1" in "$HOME"/*) printf '~/%s' "${1#"$HOME"/}" ;; *) printf '%s' "$1" ;; esac; }

for part in skills agents scripts templates workspace; do
  [[ -d "$KIT_DIR/$part" ]] || die "$KIT_DIR/$part is missing; run the install.sh that sits inside the kit folder"
done

# A same-named skill or agent that is not from this kit is moved out of Claude's scan path
# (both ~/.claude/skills and ~/.claude/agents are scanned recursively).
backup() {
  local src="$1" rel="${1#"$CLAUDE_HOME"/}"
  mkdir -p "$(dirname "$BACKUP_DIR/$rel")"
  mv "$src" "$BACKUP_DIR/$rel"
  warn "moved your existing $(pretty "$src") to $(pretty "$BACKUP_DIR/$rel") (not part of this kit)"
}

# Kit-owned files: installed, or updated when the kit version changed.
install_file() {
  local src="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"
  if [[ -f "$dest" ]] && cmp -s "$src" "$dest"; then
    say "  current   $(pretty "$dest")"
  elif [[ -f "$dest" ]]; then
    cp "$src" "$dest"
    say "  updated   $(pretty "$dest")"
  else
    cp "$src" "$dest"
    say "  installed $(pretty "$dest")"
  fi
}

# User-owned files: created once, never overwritten.
copy_if_missing() {
  local src="$1" dest="$2"
  if [[ -e "$dest" ]]; then
    if cmp -s "$src" "$dest"; then
      say "  kept      $(pretty "$dest")"
    else
      say "  kept      $(pretty "$dest") (yours differs from the kit; compare: diff \"$(pretty "$dest")\" \"$src\")"
    fi
  else
    mkdir -p "$(dirname "$dest")"
    cp "$src" "$dest"
    say "  created   $(pretty "$dest")"
  fi
}

find_python() {
  local c
  for c in "${PYTHON:-}" python3 python3.14 python3.13 python3.12 python3.11 python3.10 python py; do
    [[ -n "$c" ]] || continue
    if command -v "$c" >/dev/null 2>&1 &&
       "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
      command -v "$c"
      return 0
    fi
  done
  return 1
}

say "Job-agent kit: $KIT_DIR"

say "Skills -> $(pretty "$CLAUDE_HOME/skills")"
for skill_dir in "$KIT_DIR"/skills/*/; do
  skill_dir="${skill_dir%/}"
  name="$(basename "$skill_dir")"
  dest="$CLAUDE_HOME/skills/$name"
  if [[ -e "$dest" ]] && ! grep -qs "$MARKER" "$dest/SKILL.md"; then
    backup "$dest"
  fi
  while IFS= read -r -d '' file; do
    install_file "$file" "$dest/${file#"$skill_dir"/}"
  done < <(find "$skill_dir" -type f ! -name '.DS_Store' -print0)
done

say "Agents -> $(pretty "$CLAUDE_HOME/agents")"
for file in "$KIT_DIR"/agents/*.md; do
  dest="$CLAUDE_HOME/agents/$(basename "$file")"
  if [[ -e "$dest" ]] && ! grep -qs "$MARKER" "$dest"; then
    backup "$dest"
  fi
  install_file "$file" "$dest"
done

say "Workspace -> $(pretty "$WS")"
for dir in profile tracker applications inbox scouting scripts .claude; do
  mkdir -p "$WS/$dir"
done
copy_if_missing "$KIT_DIR/workspace/CLAUDE.md" "$WS/CLAUDE.md"
copy_if_missing "$KIT_DIR/workspace/.claude/settings.json" "$WS/.claude/settings.json"
copy_if_missing "$KIT_DIR/workspace/.gitignore" "$WS/.gitignore"
copy_if_missing "$KIT_DIR/templates/profile.example.yaml" "$WS/profile/profile.example.yaml"
copy_if_missing "$KIT_DIR/templates/answers.example.yaml" "$WS/profile/answers.example.yaml"
if [[ -f "$WS/tracker/applications.csv" && ! -s "$WS/tracker/applications.csv" ]]; then
  cp "$KIT_DIR/templates/applications.csv" "$WS/tracker/applications.csv"
  say "  repaired  $(pretty "$WS/tracker/applications.csv") (was empty; header written)"
else
  copy_if_missing "$KIT_DIR/templates/applications.csv" "$WS/tracker/applications.csv"
fi
install_file "$KIT_DIR/scripts/tracker.py" "$WS/scripts/tracker.py"
install_file "$KIT_DIR/scripts/tailor_resume.py" "$WS/scripts/tailor_resume.py"
chmod +x "$WS/scripts/tracker.py" "$WS/scripts/tailor_resume.py"

say "Python environment -> $(pretty "$WS/.venv")"
if [[ "$SKIP_VENV" -eq 1 ]]; then
  say "  skipped   (--skip-venv)"
else
  venv_python() {
    if [[ -x "$WS/.venv/Scripts/python.exe" ]]; then printf '%s' "$WS/.venv/Scripts/python.exe"
    else printf '%s' "$WS/.venv/bin/python"; fi
  }
  VENV_PY="$(venv_python)"
  if [[ -x "$VENV_PY" ]]; then
    "$VENV_PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' ||
      die "$(pretty "$WS/.venv") uses Python older than 3.10; delete that folder and re-run"
    say "  kept      $(pretty "$WS/.venv") ($("$VENV_PY" -V 2>&1))"
  else
    PY="$(find_python)" ||
      die "Python 3.10+ not found. Install it (macOS: brew install python@3.12) or set PYTHON=/path/to/python3, then re-run."
    say "  creating  $(pretty "$WS/.venv") with $("$PY" -V 2>&1)"
    "$PY" -m venv "$WS/.venv" ||
      die "could not create the venv (Debian/Ubuntu: sudo apt install python3-venv), then re-run"
    VENV_PY="$(venv_python)"
  fi
  if "$VENV_PY" -c 'import docx, pypdf, yaml' >/dev/null 2>&1; then
    say "  current   python-docx, pypdf, pyyaml"
  else
    say "  installing python-docx, pypdf, pyyaml"
    "$VENV_PY" -m pip install --quiet --disable-pip-version-check python-docx pypdf pyyaml ||
      die "pip install failed (network?). Everything else is installed; re-run this script to finish."
  fi
fi

say "Checks"
if command -v soffice >/dev/null 2>&1 || command -v libreoffice >/dev/null 2>&1 ||
   [[ -x /Applications/LibreOffice.app/Contents/MacOS/soffice ]]; then
  say "  ok        LibreOffice"
else
  warn "LibreOffice not found. PDF export and the page check need it (macOS: brew install --cask libreoffice)."
fi
if command -v git >/dev/null 2>&1; then say "  ok        git"; else warn "git not found."; fi
if command -v claude >/dev/null 2>&1; then
  say "  ok        Claude Code CLI"
else
  warn "Claude Code CLI not found: https://code.claude.com/docs/en/quickstart"
fi

cat <<EOF

Installed. Re-run this script to update skills, agents and scripts; your profile, answers,
tracker, CLAUDE.md and settings.json are never overwritten.

Next steps:
  1. Have your master resume ready as a .docx (two pages at most).
  2. At claude.ai, connect Gmail (Settings > Connectors). In Gmail, create the labels
     Jobs/Alerts and Jobs/Recruiters.
  3. Install the Claude in Chrome extension (1.0.36 or later) and sign in to LinkedIn,
     Dice and Indeed in Chrome.
  4. cd ~/job-search && claude --chrome
  5. Run /job-setup
EOF
